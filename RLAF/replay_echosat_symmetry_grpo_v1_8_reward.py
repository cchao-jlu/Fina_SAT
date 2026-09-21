#!/usr/bin/env python3
"""Offline v1.8 objective-repair dry-run over v1.7 reward replay rows."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from train_rlaf import apply_echosat_v18_advantage_repair


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_ROWS = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_7_reward_replay_dryrun_rows.csv"
DEFAULT_OUT_PREFIX = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_8_reward_replay_dryrun"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_8_reward_replay_dryrun.md"

EPS = 1.0e-12
SUBSET_FAILURE_BASE = "subset_cardinality_bw12"
SUBSET_FAILURE_VARIANT = "perm_seed1730"


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def bool_series(values: pd.Series | Any, index: pd.Index | None = None) -> pd.Series:
    if not isinstance(values, pd.Series):
        values = pd.Series(values, index=index)
    if values.dtype == bool:
        return values.fillna(False).astype(bool)
    numeric = pd.to_numeric(values, errors="coerce")
    text = values.fillna("").astype(str).str.strip().str.lower()
    return (numeric.notna() & numeric.ne(0.0)) | text.isin({"true", "t", "yes", "y"})


def bool_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index, dtype=bool)
    return bool_series(frame[column])


def numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(default).astype("float64")


def finite(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def fmt(value: Any) -> str:
    value = finite(value)
    if not math.isfinite(value):
        return "nan"
    return f"{value:.6g}"


def infer_role(frame: pd.DataFrame) -> pd.Series:
    if "echosat_replay_role" in frame.columns:
        return frame["echosat_replay_role"].fillna("other").astype(str)
    role = pd.Series("other", index=frame.index, dtype=object)
    family = frame.get("family", pd.Series("", index=frame.index)).fillna("").astype(str)
    control_type = frame.get("control_type", pd.Series("", index=frame.index)).fillna("").astype(str)
    base = frame.get("base_instance_id", pd.Series("", index=frame.index)).fillna("").astype(str)
    variant = frame.get("variant", pd.Series("", index=frame.index)).fillna("").astype(str)
    role[family.eq("random_3sat_control") | control_type.eq("non_symmetric_control")] = "random_control"
    role[base.eq(SUBSET_FAILURE_BASE) & variant.eq(SUBSET_FAILURE_VARIANT)] = "subset_failure"
    role[bool_column(frame, "echosat_hard_negative_candidate")] = "hard_negative"
    role[bool_column(frame, "echosat_anchor_candidate")] = "anchor"
    role[bool_column(frame, "echosat_anchor_failure")] = "anchor_failure"
    role[bool_column(frame, "echosat_hard_negative_failure")] = "hard_negative_failure"
    role[base.eq(SUBSET_FAILURE_BASE) & variant.eq(SUBSET_FAILURE_VARIANT)] = "subset_failure"
    return role


def apply_v18_objective_repair(
    frame: pd.DataFrame,
    *,
    hard_negative_pressure_multiplier: float = 1.25,
) -> pd.DataFrame:
    return apply_echosat_v18_advantage_repair(
        frame,
        hard_negative_pressure_multiplier=hard_negative_pressure_multiplier,
    )


def summarize(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_cols = [
        "echosat_search_ok",
        "echosat_search_blowup",
        "echosat_positive_allowed",
        "echosat_v18_blocked_positive_signal",
        "echosat_v18_cpu_only_search_bad",
        "echosat_v18_weighted_risk_blocked",
        "echosat_v18_near_cap_blocked",
        "echosat_v18_unclamped_positive_blocked",
        "echosat_v18_hard_negative_pressure",
        "echosat_symmetry_reward",
        "echosat_cost",
        "grpo_raw_advantage_unclamped",
        "v17_grpo_raw_advantage",
        "grpo_raw_advantage",
        "v17_grpo_final_advantage",
        "grpo_final_advantage",
        "grpo_positive_raw_advantage_clamped",
        "grpo_positive_advantage_clamped",
    ]
    present = [column for column in metric_cols if column in frame.columns]
    working = frame.copy()
    for column in present:
        if working[column].dtype == bool:
            working[column] = working[column].astype(float)
    role = working.groupby("echosat_replay_role", dropna=False)[present].mean(numeric_only=True).reset_index()
    role["rows"] = working.groupby("echosat_replay_role", dropna=False).size().to_numpy(dtype=np.int64)

    base_cols = [column for column in ["echosat_replay_role", "family", "base_instance_id"] if column in working.columns]
    base = working.groupby(base_cols, dropna=False)[present].mean(numeric_only=True).reset_index()
    base["rows"] = working.groupby(base_cols, dropna=False).size().to_numpy(dtype=np.int64)

    check_cols = [
        "echosat_replay_role",
        "echosat_search_ok",
        "echosat_v18_blocked_positive_signal",
        "echosat_v18_cpu_only_search_bad",
        "echosat_v18_weighted_risk_blocked",
        "echosat_v18_near_cap_blocked",
        "grpo_raw_advantage",
        "grpo_final_advantage",
        "v17_grpo_final_advantage",
    ]
    checks = working[[column for column in check_cols if column in working.columns]].copy()
    return role, base, checks


def _any_positive(frame: pd.DataFrame, mask: pd.Series, column: str) -> bool:
    if column not in frame.columns:
        return False
    return bool((mask & (numeric(frame, column, 0.0) > EPS)).any())


def _role_mask(frame: pd.DataFrame, role: str) -> pd.Series:
    return frame["echosat_replay_role"].astype(str).eq(role) if "echosat_replay_role" in frame.columns else pd.Series(False, index=frame.index)


def build_checks(frame: pd.DataFrame, role_summary: pd.DataFrame, base_summary: pd.DataFrame, checks_frame: pd.DataFrame) -> pd.DataFrame:
    del role_summary, base_summary
    rows: list[dict[str, Any]] = []

    def add(check: str, passed: bool, evidence: str) -> None:
        rows.append({"check": check, "passed": bool(passed), "evidence": evidence})

    anchor = _role_mask(frame, "anchor")
    hard = _role_mask(frame, "hard_negative")
    blocked = bool_column(frame, "echosat_v18_blocked_positive_signal")
    cpu_only = bool_column(frame, "echosat_v18_cpu_only_search_bad")
    weighted = bool_column(frame, "echosat_v18_weighted_risk_blocked")
    near_cap = bool_column(frame, "echosat_v18_near_cap_blocked")

    raw_pos = numeric(frame, "grpo_raw_advantage", 0.0) > EPS
    final_pos = numeric(frame, "grpo_final_advantage", 0.0) > EPS
    hard_mean = numeric(frame[hard], "grpo_final_advantage", 0.0).mean() if bool(hard.any()) else float("nan")
    hard_v17_mean = numeric(frame[hard], "v17_grpo_final_advantage", 0.0).mean() if bool(hard.any()) else float("nan")

    add(
        "anchor_final_positive_recovered",
        _any_positive(frame, anchor, "grpo_final_advantage"),
        f"anchor positive rows={int((anchor & final_pos).sum())}",
    )
    add(
        "hard_negative_final_positive_recovered",
        _any_positive(frame, hard, "grpo_final_advantage"),
        f"hard_negative positive rows={int((hard & final_pos).sum())}",
    )
    add(
        "hard_negative_final_pressure_not_weaker_than_v1_7",
        math.isfinite(finite(hard_mean)) and math.isfinite(finite(hard_v17_mean)) and hard_mean >= hard_v17_mean - EPS,
        f"v18_mean={fmt(hard_mean)} v17_mean={fmt(hard_v17_mean)}",
    )
    for role in ["random_control", "subset_failure", "anchor_failure", "hard_negative_failure"]:
        mask = _role_mask(frame, role)
        add(
            f"{role}_no_raw_or_final_positive",
            not bool((mask & (raw_pos | final_pos)).any()),
            f"raw_pos={int((mask & raw_pos).sum())} final_pos={int((mask & final_pos).sum())}",
        )
    add(
        "blocked_rows_no_raw_or_final_positive",
        not bool((blocked & (raw_pos | final_pos)).any()),
        f"blocked={int(blocked.sum())} raw_pos={int((blocked & raw_pos).sum())} final_pos={int((blocked & final_pos).sum())}",
    )
    add(
        "cpu_only_search_bad_no_raw_or_final_positive",
        not bool((cpu_only & (raw_pos | final_pos)).any()),
        f"cpu_only={int(cpu_only.sum())} raw_pos={int((cpu_only & raw_pos).sum())} final_pos={int((cpu_only & final_pos).sum())}",
    )
    add(
        "weighted_risk_no_raw_or_final_positive",
        not bool((weighted & (raw_pos | final_pos)).any()),
        f"weighted_risk={int(weighted.sum())} raw_pos={int((weighted & raw_pos).sum())} final_pos={int((weighted & final_pos).sum())}",
    )
    add(
        "near_cap_no_raw_or_final_positive",
        not bool((near_cap & (raw_pos | final_pos)).any()),
        f"near_cap={int(near_cap.sum())} raw_pos={int((near_cap & raw_pos).sum())} final_pos={int((near_cap & final_pos).sum())}",
    )
    subset_guard = (
        frame.get("base_instance_id", pd.Series("", index=frame.index)).fillna("").astype(str).eq(SUBSET_FAILURE_BASE)
        & frame.get("variant", pd.Series("", index=frame.index)).fillna("").astype(str).eq(SUBSET_FAILURE_VARIANT)
    )
    add(
        "subset_bw12_perm1730_no_raw_or_final_positive",
        not bool((subset_guard & (raw_pos | final_pos)).any()),
        f"rows={int(subset_guard.sum())} raw_pos={int((subset_guard & raw_pos).sum())} final_pos={int((subset_guard & final_pos).sum())}",
    )
    add(
        "positive_allowed_not_all_zero",
        bool(bool_column(frame, "echosat_positive_allowed").any() or _any_positive(frame, ~blocked, "grpo_final_advantage")),
        f"nonblocked_final_pos={int(((~blocked) & final_pos).sum())}",
    )
    add(
        "ALL_V1_8_DRYRUN_CHECKS",
        all(row["passed"] for row in rows),
        "aggregate of preceding checks",
    )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells: list[str] = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                cells.append(fmt(value))
            else:
                cells.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(
    *,
    path: Path,
    input_rows: Path,
    rows: pd.DataFrame,
    role: pd.DataFrame,
    base: pd.DataFrame,
    checks: pd.DataFrame,
    outputs: dict[str, Path],
) -> None:
    priority_bases = {
        "k9_color8",
        "php_p9_h8",
        "k10_color9",
        "php_p10_h9",
        SUBSET_FAILURE_BASE,
    }
    priority = base[
        base.get("base_instance_id", pd.Series("", index=base.index)).astype(str).isin(priority_bases)
        | base.get("family", pd.Series("", index=base.index)).astype(str).eq("random_3sat_control")
    ].copy()
    all_pass = bool(checks.loc[checks["check"].eq("ALL_V1_8_DRYRUN_CHECKS"), "passed"].iloc[0]) if not checks.empty else False
    lines = [
        "# EchoSAT Symmetry GRPO v1.8 Reward Replay Dry-Run",
        "",
        "This is an offline objective-repair dry-run over existing v1.7 reward replay rows. It does not rerun solvers, train a checkpoint, expand the benchmark, or add a gate/selector.",
        "",
        "v1.8 keeps the strict search-work lens: a row may carry positive training advantage only when adapter-vs-cached decisions and conflicts both improve and the row is not a random control, protected subset failure, anchor/hard-negative failure, weighted-risk row, near-cap row, CPU-only win, or result mismatch.",
        "",
        "The `grpo_raw_advantage_unclamped` column remains a diagnostic group-normalization value. The hard requirement here is that the training-visible `grpo_raw_advantage` and `grpo_final_advantage` are non-positive on blocked rows.",
        "",
        "## Inputs",
        "",
        f"- v1.7 replay rows: `{display_path(input_rows)}`",
        "",
        "## Outputs",
        "",
        *[f"- {name}: `{display_path(output)}`" for name, output in outputs.items()],
        "",
        "## Scope",
        "",
        f"- rows: `{len(rows)}`",
        f"- roles: `{', '.join(sorted(rows['echosat_replay_role'].astype(str).unique()))}`",
        f"- dry-run pass: `{all_pass}`",
        "",
        "## Checks",
        "",
        *markdown_table(checks, max_rows=30),
        "",
        "## Role Summary",
        "",
        *markdown_table(role.round(6), max_rows=30),
        "",
        "## Priority Base Summary",
        "",
        *markdown_table(priority.round(6), max_rows=80),
        "",
        "## Conclusion",
        "",
        "- If these checks pass, the v1.8 objective is ready to be ported into the formal training path for a short local run.",
        "- If a later formal replay diverges from these checks, do not train; inspect the training integration first.",
        "- `v1.2 iter=15.pt` remains the conservative runtime checkpoint until v1.8 training beats it on targeted acceptance.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--out-prefix", type=Path, default=DEFAULT_OUT_PREFIX)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--hard-negative-pressure-multiplier", type=float, default=1.25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_rows = resolve(args.input_rows)
    out_prefix = resolve(args.out_prefix)
    doc = resolve(args.doc)
    source = pd.read_csv(input_rows)
    repaired = apply_v18_objective_repair(
        source,
        hard_negative_pressure_multiplier=float(args.hard_negative_pressure_multiplier),
    )
    role, base, checks_input = summarize(repaired)
    checks = build_checks(repaired, role, base, checks_input)

    outputs = {
        "rows": out_prefix.with_name(out_prefix.name + "_rows.csv"),
        "role summary": out_prefix.with_name(out_prefix.name + "_role_summary.csv"),
        "base summary": out_prefix.with_name(out_prefix.name + "_base_summary.csv"),
        "checks": out_prefix.with_name(out_prefix.name + "_checks.csv"),
    }
    for output in outputs.values():
        output.parent.mkdir(parents=True, exist_ok=True)
    repaired.to_csv(outputs["rows"], index=False)
    role.to_csv(outputs["role summary"], index=False)
    base.to_csv(outputs["base summary"], index=False)
    checks.to_csv(outputs["checks"], index=False)
    write_doc(path=doc, input_rows=input_rows, rows=repaired, role=role, base=base, checks=checks, outputs=outputs)

    print(f"v1.8 dry-run rows: {len(repaired)}")
    for _, row in checks.iterrows():
        print(f"{row['check']}: {row['passed']} ({row['evidence']})")
    for name, output in outputs.items():
        print(f"{name}: {output}")
    print(f"doc: {doc}")


if __name__ == "__main__":
    main()
