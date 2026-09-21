#!/usr/bin/env python3
"""Audit an EchoSAT v2 reward replay without training."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd


EPS = 1.0e-12
CHECK_NAMES = [
    "blocked_rows_non_positive",
    "eligible_positive_exists",
    "all_v2_stage4_checks",
]
HARD_SAFETY_REASONS = [
    ("control", "v2_control_blocked", True),
    ("invalid_static_baseline", "v2_invalid_static_baseline", True),
    ("invalid_symmetry_orbit_evidence", "v2_valid_symmetry_orbit_evidence", False),
    ("missing_plain_baseline", "v2_missing_plain_baseline", True),
    ("missing_static_baseline", "v2_missing_static_baseline", True),
    ("near_cap", "v2_near_cap", True),
    ("plain_result_mismatch", "v2_plain_result_mismatch", True),
    ("plain_solved_guided_unsolved", "v2_plain_solved_guided_unsolved", True),
    ("plain_unsolved", "v2_plain_unsolved", True),
    ("static_result_mismatch", "v2_static_result_mismatch", True),
    ("static_solved_guided_unsolved", "v2_static_solved_guided_unsolved", True),
    ("static_unsolved", "v2_static_unsolved", True),
    ("weighted_risk", "v2_weighted_risk", True),
    ("hard_safety_total", "v2_hard_safety_blocked", True),
]


def _strict_eligibility(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    values = (
        frame["v2_positive_eligible"].to_numpy(dtype=object)
        if "v2_positive_eligible" in frame.columns
        else np.full(len(frame), None, dtype=object)
    )
    valid = np.fromiter(
        (isinstance(value, (bool, np.bool_)) for value in values),
        dtype=bool,
        count=len(frame),
    )
    eligible = np.fromiter(
        (bool(value) if is_valid else False for value, is_valid in zip(values, valid)),
        dtype=bool,
        count=len(frame),
    )
    return eligible, ~valid


def _strict_bool_column(
    frame: pd.DataFrame,
    column: str,
) -> tuple[np.ndarray, np.ndarray]:
    if column not in frame.columns:
        return np.zeros(len(frame), dtype=bool), np.zeros(len(frame), dtype=bool)
    values = frame[column].to_numpy(dtype=object)
    valid = np.fromiter(
        (isinstance(value, (bool, np.bool_)) for value in values),
        dtype=bool,
        count=len(frame),
    )
    parsed = np.fromiter(
        (bool(value) if is_valid else False for value, is_valid in zip(values, valid)),
        dtype=bool,
        count=len(frame),
    )
    return parsed, valid


def _markdown_table_cell(value: object) -> str:
    normalized = str(value).replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\n", " ")
    return normalized.replace("|", "&#124;").replace("`", "&#96;")


def _attribution_sections(frame: pd.DataFrame) -> list[str]:
    required_columns = {
        "base_instance_id",
        "variant",
        "v2_positive_eligible",
        "v2_variant_positive_capable",
        "v2_variant_hard_blocked",
        "worst_variant_score",
        *(column for _, column, _ in HARD_SAFETY_REASONS),
    }
    missing_columns = sorted(required_columns.difference(frame.columns))
    eligible, invalid_eligibility = _strict_eligibility(frame)
    positive_capable, valid_positive_capable = _strict_bool_column(
        frame, "v2_variant_positive_capable"
    )
    hard_blocked, valid_hard_blocked = _strict_bool_column(
        frame, "v2_variant_hard_blocked"
    )
    invalid_diagnostic_count = int(invalid_eligibility.sum())
    if "v2_variant_positive_capable" in frame.columns:
        invalid_diagnostic_count += int((~valid_positive_capable).sum())
    if "v2_variant_hard_blocked" in frame.columns:
        invalid_diagnostic_count += int((~valid_hard_blocked).sum())

    if "base_instance_id" in frame.columns and "variant" in frame.columns:
        valid_keys = np.fromiter(
            (
                isinstance(base, (str, np.str_))
                and base.strip() != ""
                and isinstance(variant, (str, np.str_))
                and variant.strip() != ""
                for base, variant in zip(
                    frame["base_instance_id"].to_numpy(dtype=object),
                    frame["variant"].to_numpy(dtype=object),
                )
            ),
            dtype=bool,
            count=len(frame),
        )
        invalid_diagnostic_count += int((~valid_keys).sum())
    else:
        valid_keys = np.zeros(len(frame), dtype=bool)

    worst_scores = np.full(len(frame), np.nan, dtype=np.float64)
    if "worst_variant_score" in frame.columns:
        worst_scores = pd.to_numeric(
            frame["worst_variant_score"], errors="coerce"
        ).to_numpy(dtype=np.float64)
        invalid_diagnostic_count += int((~np.isfinite(worst_scores)).sum())

    reason_counts: list[tuple[str, int]] = []
    for reason, column, active_value in HARD_SAFETY_REASONS:
        parsed, valid = _strict_bool_column(frame, column)
        if column in frame.columns:
            invalid_diagnostic_count += int((~valid).sum())
            active = parsed if active_value else ~parsed
            reason_count = int((active & valid).sum())
        else:
            reason_count = 0
        reason_counts.append((reason, reason_count))

    attribution = pd.DataFrame(
        {
            "base": (
                frame["base_instance_id"].to_numpy(dtype=object)
                if "base_instance_id" in frame.columns
                else np.full(len(frame), None, dtype=object)
            ),
            "variant": (
                frame["variant"].to_numpy(dtype=object)
                if "variant" in frame.columns
                else np.full(len(frame), None, dtype=object)
            ),
            "eligible": eligible,
            "positive_capable": positive_capable,
            "valid_positive_capable": valid_positive_capable,
            "hard_blocked": hard_blocked,
            "valid_hard_blocked": valid_hard_blocked,
            "worst_score": worst_scores,
            "valid_key": valid_keys,
        }
    )
    attribution = attribution[attribution["valid_key"]].copy()
    variant_rows: list[dict[str, object]] = []
    if not attribution.empty:
        for (base, variant), group in attribution.groupby(
            ["base", "variant"], sort=True
        ):
            variant_rows.append(
                {
                    "base": str(base),
                    "variant": str(variant),
                    "eligible_rows": int(group["eligible"].sum()),
                    "positive_capable": bool(
                        group["valid_positive_capable"].all()
                        and group["positive_capable"].all()
                    ),
                    "hard_blocked": bool(
                        group["valid_hard_blocked"].all()
                        and group["hard_blocked"].any()
                    ),
                }
            )
    variants = pd.DataFrame(
        variant_rows,
        columns=[
            "base",
            "variant",
            "eligible_rows",
            "positive_capable",
            "hard_blocked",
        ],
    )
    positive_capable_count = int(variants["positive_capable"].sum())
    hard_blocked_count = int(variants["hard_blocked"].sum())
    missing_text = ", ".join(missing_columns) if missing_columns else "none"

    lines = [
        "",
        "## Variant Summary",
        "",
        f"- eligible rows: `{int(eligible.sum())}`",
        f"- positive-capable variants: `{positive_capable_count}`",
        f"- hard-blocked variants: `{hard_blocked_count}`",
        f"- missing diagnostics: `{missing_text}`",
        f"- invalid diagnostic values: `{invalid_diagnostic_count}`",
        "",
        "| base | variant | eligible rows | positive capable | hard blocked |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in variants.itertuples(index=False):
        base_cell = _markdown_table_cell(row.base)
        variant_cell = _markdown_table_cell(row.variant)
        lines.append(
            f"| `{base_cell}` | `{variant_cell}` | {row.eligible_rows} | "
            f"{bool(row.positive_capable)} | {bool(row.hard_blocked)} |"
        )

    lines.extend(
        [
            "",
            "## Base Summary",
            "",
            "| base | eligible rows | eligible variants | worst variant score |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    if not attribution.empty:
        for base, group in attribution.groupby("base", sort=True):
            base_variants = variants[variants["base"].eq(str(base))]
            finite_scores = group["worst_score"].to_numpy(dtype=np.float64)
            score_text = (
                f"{float(finite_scores.min()):.12g}"
                if len(finite_scores) > 0 and np.isfinite(finite_scores).all()
                else "missing"
            )
            base_cell = _markdown_table_cell(base)
            lines.append(
                f"| `{base_cell}` | {int(group['eligible'].sum())} | "
                f"{int(base_variants['eligible_rows'].gt(0).sum())} | {score_text} |"
            )

    lines.extend(
        [
            "",
            "## Hard-Safety Rejections",
            "",
            "| reason | rows |",
            "| --- | ---: |",
        ]
    )
    for reason, count in sorted(reason_counts):
        lines.append(f"| `{_markdown_table_cell(reason)}` | {count} |")
    return lines


def build_checks(frame: pd.DataFrame) -> pd.DataFrame:
    eligible, invalid_eligibility = _strict_eligibility(frame)
    blocked = ~eligible
    advantage_present = "grpo_final_advantage" in frame.columns
    if advantage_present:
        advantage = pd.to_numeric(frame["grpo_final_advantage"], errors="coerce").to_numpy(dtype=np.float64)
        advantage_finite = bool(np.isfinite(advantage).all())
        advantage_error = "" if advantage_finite else "nonfinite grpo_final_advantage"
    else:
        advantage = np.zeros(len(frame), dtype=np.float64)
        advantage_finite = False
        advantage_error = "missing grpo_final_advantage"

    blocked_positive_count = int((blocked & np.isfinite(advantage) & (advantage > EPS)).sum())
    eligible_positive_count = int((eligible & np.isfinite(advantage) & (advantage > EPS)).sum())
    blocked_passed = (
        advantage_finite
        and int(invalid_eligibility.sum()) == 0
        and blocked_positive_count == 0
    )
    eligible_passed = advantage_finite and eligible_positive_count > 0
    rows = [
        {
            "check": CHECK_NAMES[0],
            "passed": blocked_passed,
            "evidence": (
                advantage_error
                or f"blocked={int(blocked.sum())} positive={blocked_positive_count} invalid_eligibility={int(invalid_eligibility.sum())}"
            ),
        },
        {
            "check": CHECK_NAMES[1],
            "passed": eligible_passed,
            "evidence": advantage_error or f"eligible={int(eligible.sum())} positive={eligible_positive_count}",
        },
        {
            "check": CHECK_NAMES[2],
            "passed": blocked_passed and eligible_passed,
            "evidence": f"{CHECK_NAMES[0]}={blocked_passed} {CHECK_NAMES[1]}={eligible_passed}",
        },
    ]
    checks = pd.DataFrame(rows, columns=["check", "passed", "evidence"])
    checks.attrs["row_count"] = len(frame)
    checks.attrs["eligible_count"] = int(eligible.sum())
    checks.attrs["blocked_count"] = int(blocked.sum())
    checks.attrs["invalid_eligibility_count"] = int(invalid_eligibility.sum())
    checks.attrs["advantage_error"] = advantage_error
    return checks


def _atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            frame.to_csv(handle, index=False)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _atomic_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(text)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _audit_doc(
    input_rows: Path,
    checks: pd.DataFrame,
    rows: pd.DataFrame,
    read_error: str = "",
) -> str:
    lines = [
        "# EchoSAT v2 Offline Replay Audit",
        "",
        f"- input: `{input_rows}`",
        f"- rows: `{checks.attrs.get('row_count', 0)}`",
        f"- eligible: `{checks.attrs.get('eligible_count', 0)}`",
        f"- blocked: `{checks.attrs.get('blocked_count', 0)}`",
        f"- invalid eligibility: `{checks.attrs.get('invalid_eligibility_count', 0)}`",
    ]
    if read_error:
        lines.append(f"- read error: `{read_error}`")
    if checks.attrs.get("advantage_error"):
        lines.append(f"- advantage error: `{checks.attrs['advantage_error']}`")
    lines.extend(["", "## Checks", ""])
    for row in checks.itertuples(index=False):
        lines.append(f"- `{row.check}`: `{bool(row.passed)}` — {row.evidence}")
    lines.extend(_attribution_sections(rows))
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", "--input-rows", dest="rows", type=Path, required=True)
    parser.add_argument("--checks", type=Path, required=True)
    parser.add_argument("--doc", type=Path, required=True)
    return parser


def _validate_distinct_output_paths(rows: Path, checks: Path, doc: Path) -> None:
    named_paths = [("rows", rows), ("checks", checks), ("doc", doc)]
    for index, (left_name, left_path) in enumerate(named_paths):
        for right_name, right_path in named_paths[index + 1:]:
            aliases = left_path.resolve(strict=False) == right_path.resolve(strict=False)
            if not aliases and left_path.exists() and right_path.exists():
                try:
                    aliases = os.path.samefile(left_path, right_path)
                except OSError:
                    aliases = False
            if aliases:
                raise ValueError(
                    f"{left_name} and {right_name} paths must be distinct"
                )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    _validate_distinct_output_paths(args.rows, args.checks, args.doc)
    read_error = ""
    try:
        rows = pd.read_csv(args.rows)
    except Exception as exc:
        rows = pd.DataFrame()
        read_error = f"{type(exc).__name__}: {exc}"

    checks = build_checks(rows)
    if read_error:
        checks["passed"] = False
        checks["evidence"] = f"rows read error: {read_error}"
    _atomic_write_csv(checks, args.checks)
    _atomic_write_text(_audit_doc(args.rows, checks, rows, read_error), args.doc)

    print(f"EchoSAT v2 replay rows: {len(rows)}")
    for row in checks.itertuples(index=False):
        print(f"{row.check}: {bool(row.passed)} ({row.evidence})")
    print(f"checks: {args.checks}")
    print(f"doc: {args.doc}")
    return 0 if bool(checks.loc[checks["check"].eq("all_v2_stage4_checks"), "passed"].iloc[0]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
