from __future__ import annotations

import math
import os
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd


PLAIN_METHOD = "plain_unguided_glucose"
NEUTRAL_METHOD = "neutral_weighted_glucose"
PAIR_COLUMNS = ("repeat_id", "base_instance_id", "variant")
FINAL_COLUMNS = (
    "final_result",
    "final_solved",
    "final_decisions",
    "final_conflicts",
    "final_cpu_time",
)
REQUIRED_COLUMNS = (*PAIR_COLUMNS, "method", *FINAL_COLUMNS)
ALLOWED_RESULTS = frozenset(
    {"SATISFIABLE", "UNSATISFIABLE", "INDETERMINATE"}
)
SOLVED_RESULTS = frozenset({"SATISFIABLE", "UNSATISFIABLE"})
GATE_MODES = ("deterministic", "cpu")
GATE_ACCEPTANCE_RULES = {
    "deterministic": (
        "Acceptance requires valid rows and exact equality of final result, "
        "input final_solved status, decisions, and conflicts."
    ),
    "cpu": (
        "Acceptance requires valid rows and exact equality of final result and "
        "input final_solved status; decisions and conflicts are diagnostic-only."
    ),
}
PAIR_ID_PATTERN = re.compile(r"^repeat=(.*?)\|base=(.*?)\|variant=(.*)$")

AUDIT_COLUMNS = (
    "pair_id",
    *PAIR_COLUMNS,
    "plain_method_count",
    "neutral_method_count",
    "plain_final_result",
    "neutral_final_result",
    "plain_final_solved",
    "neutral_final_solved",
    "plain_final_decisions",
    "neutral_final_decisions",
    "plain_final_conflicts",
    "neutral_final_conflicts",
    "plain_final_cpu_time",
    "neutral_final_cpu_time",
    "final_cpu_time_delta",
    "result_match",
    "solved_match",
    "decisions_match",
    "conflicts_match",
    "accepted",
    "rejection_reason",
)


class EquivalenceInputError(ValueError):
    pass


def validate_equivalence_input(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise EquivalenceInputError(
            "missing required columns: " + ", ".join(missing)
        )


def build_pair_id(frame: pd.DataFrame) -> pd.Series:
    missing = [column for column in PAIR_COLUMNS if column not in frame.columns]
    if missing:
        raise EquivalenceInputError(
            "missing pair columns: " + ", ".join(missing)
        )
    return (
        "repeat="
        + frame["repeat_id"].map(_format_pair_value)
        + "|base="
        + frame["base_instance_id"].map(_format_pair_value)
        + "|variant="
        + frame["variant"].map(_format_pair_value)
    )


def build_expected_pair_ids(
    manifest: pd.DataFrame,
    repeats: Sequence[int],
) -> list[str]:
    required = ["base_instance_id", "variant"]
    missing = [column for column in required if column not in manifest.columns]
    if missing:
        raise EquivalenceInputError(
            "expected manifest missing required columns: " + ", ".join(missing)
        )
    base_variants = (
        manifest[required]
        .drop_duplicates()
        .sort_values(required, kind="stable")
        .reset_index(drop=True)
    )
    expected = []
    for repeat_id in sorted(set(repeats)):
        repeated = base_variants.assign(repeat_id=repeat_id)
        expected.extend(build_pair_id(repeated).tolist())
    return expected


def audit_plain_neutral_equivalence(
    frame: pd.DataFrame,
    expected_pair_ids: Iterable[str] | None = None,
    gate_mode: str = "deterministic",
) -> pd.DataFrame:
    _validate_gate_mode(gate_mode)
    validate_equivalence_input(frame)
    coverage_requested = expected_pair_ids is not None
    expected_source = [] if expected_pair_ids is None else expected_pair_ids
    expected = sorted(set(expected_source))
    if frame.empty:
        if expected:
            return _audit_frame(
                [_missing_pair_record(pair_id) for pair_id in expected]
            )
        if coverage_requested:
            return _audit_frame(
                [_coverage_failure_record("expected_pair_set_empty")]
            )
        return input_error_audit("input contains no rows")

    working = frame.copy()
    working["pair_id"] = build_pair_id(working)
    records = []
    for pair_values, group in working.groupby(
        list(PAIR_COLUMNS), sort=True, dropna=False
    ):
        records.append(_audit_pair(pair_values, group, gate_mode))

    actual_pair_ids = {str(record["pair_id"]) for record in records}
    records.extend(
        _missing_pair_record(pair_id)
        for pair_id in expected
        if pair_id not in actual_pair_ids
    )
    if coverage_requested and not expected:
        records.append(_coverage_failure_record("expected_pair_set_empty"))
    records.sort(key=lambda record: str(record["pair_id"]))
    return _audit_frame(records)


def input_error_audit(message: str) -> pd.DataFrame:
    record = {column: pd.NA for column in AUDIT_COLUMNS}
    record.update(
        {
            "pair_id": "__input__",
            "plain_method_count": 0,
            "neutral_method_count": 0,
            "accepted": False,
            "rejection_reason": f"input_error: {message}",
        }
    )
    return _audit_frame([record])


def canonicalize_repo_path(path: str | Path, root: str | Path) -> str:
    resolved_path = Path(path).resolve()
    resolved_root = Path(root).resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError:
        relative = Path(os.path.relpath(resolved_path, resolved_root))
    return relative.as_posix()


def accepted_mask(audit: pd.DataFrame) -> pd.Series:
    return pd.Series(
        [False if pd.isna(value) else bool(value) for value in audit["accepted"]],
        index=audit.index,
        dtype=bool,
    )


def render_equivalence_markdown(
    audit: pd.DataFrame,
    input_path: str,
    expected_manifest_path: str | None = None,
    gate_mode: str = "deterministic",
) -> str:
    _validate_gate_mode(gate_mode)
    accepted = accepted_mask(audit)
    accepted_rows = int(accepted.sum())
    rejected_rows = int((~accepted).sum())
    missing_pairs = int((audit["rejection_reason"] == "missing_pair").sum())
    status = "ACCEPT" if rejected_rows == 0 else "REJECT"
    cpu_delta = pd.to_numeric(audit["final_cpu_time_delta"], errors="coerce")
    cpu_delta = cpu_delta.dropna()
    cpu_mean = "n/a" if cpu_delta.empty else f"{cpu_delta.mean():.9g}"
    cpu_max_abs = "n/a" if cpu_delta.empty else f"{cpu_delta.abs().max():.9g}"
    lines = [
        "# EchoSAT v2 Weighted Neutral Equivalence Audit",
        "",
        f"- Status: **{status}**",
        f"- Gate mode: `{gate_mode}`",
        f"- Input: `{input_path}`",
    ]
    if expected_manifest_path is not None:
        lines.append(f"- Expected manifest: `{expected_manifest_path}`")
    lines.extend(
        [
            f"- Pairs: {len(audit)}",
            f"- Accepted pairs: {accepted_rows}",
            f"- Rejected pairs: {rejected_rows}",
            f"- Missing expected pairs: {missing_pairs}",
            f"- Mean neutral-minus-plain final CPU time: {cpu_mean}",
            f"- Maximum absolute final CPU delta: {cpu_max_abs}",
            "- CPU time is diagnostic-only and does not affect acceptance.",
            "",
            GATE_ACCEPTANCE_RULES[gate_mode],
        ]
    )
    if rejected_rows:
        lines.extend(["", "## Rejections", ""])
        for row in audit.loc[~accepted].itertuples(index=False):
            lines.append(f"- `{row.pair_id}`: {row.rejection_reason}")
    return "\n".join(lines) + "\n"


def _audit_pair(
    pair_values: Iterable[object],
    group: pd.DataFrame,
    gate_mode: str,
) -> dict[str, object]:
    repeat_id, base_instance_id, variant = pair_values
    plain = group.loc[group["method"] == PLAIN_METHOD]
    neutral = group.loc[group["method"] == NEUTRAL_METHOD]
    record: dict[str, object] = {
        "pair_id": group["pair_id"].iloc[0],
        "repeat_id": repeat_id,
        "base_instance_id": base_instance_id,
        "variant": variant,
        "plain_method_count": len(plain),
        "neutral_method_count": len(neutral),
    }
    reasons = _pair_key_reasons(pair_values)
    if len(plain) != 1:
        reasons.append(f"plain_method_count={len(plain)}")
    if len(neutral) != 1:
        reasons.append(f"neutral_method_count={len(neutral)}")
    if len(plain) != 1 or len(neutral) != 1:
        record.update(_empty_comparison_values())
        record["accepted"] = False
        record["rejection_reason"] = "; ".join(reasons)
        return record

    plain_values, plain_reasons = _validated_final_values(plain.iloc[0], "plain")
    neutral_values, neutral_reasons = _validated_final_values(
        neutral.iloc[0], "neutral"
    )
    record.update(plain_values)
    record.update(neutral_values)
    reasons.extend(plain_reasons)
    reasons.extend(neutral_reasons)
    record["final_cpu_time_delta"] = _numeric_delta(
        record["neutral_final_cpu_time"], record["plain_final_cpu_time"]
    )

    comparisons = {
        "result_match": _exact_equal(
            record["plain_final_result"], record["neutral_final_result"]
        ),
        "solved_match": _exact_equal(
            record["plain_final_solved"], record["neutral_final_solved"]
        ),
        "decisions_match": _exact_equal(
            record["plain_final_decisions"], record["neutral_final_decisions"]
        ),
        "conflicts_match": _exact_equal(
            record["plain_final_conflicts"], record["neutral_final_conflicts"]
        ),
    }
    record.update(comparisons)
    gated_comparisons = (
        comparisons
        if gate_mode == "deterministic"
        else {
            name: comparisons[name]
            for name in ("result_match", "solved_match")
        }
    )
    reasons.extend(
        name.removesuffix("_match") + "_mismatch"
        for name, matches in gated_comparisons.items()
        if not matches
    )
    record["accepted"] = not reasons
    record["rejection_reason"] = "; ".join(reasons)
    return record


def _validate_gate_mode(gate_mode: str) -> None:
    if gate_mode not in GATE_MODES:
        allowed = ", ".join(GATE_MODES)
        raise EquivalenceInputError(
            f"invalid gate_mode={gate_mode!r}; expected one of: {allowed}"
        )


def _validated_final_values(
    row: pd.Series,
    prefix: str,
) -> tuple[dict[str, object], list[str]]:
    values = {f"{prefix}_{column}": row[column] for column in FINAL_COLUMNS}
    reasons = []

    result = row["final_result"]
    if not isinstance(result, str) or result not in ALLOWED_RESULTS:
        reasons.append(f"{prefix}_invalid_final_result={result!r}")

    solved, solved_valid = _normalize_boolean(row["final_solved"])
    values[f"{prefix}_final_solved"] = solved
    if not solved_valid:
        reasons.append(f"{prefix}_invalid_final_solved={row['final_solved']!r}")
    elif isinstance(result, str) and result in ALLOWED_RESULTS:
        expected_solved = result in SOLVED_RESULTS
        if solved != expected_solved:
            reasons.append(f"{prefix}_final_solved_inconsistent_with_result")

    for column in ("final_decisions", "final_conflicts"):
        normalized, valid = _normalize_nonnegative_integer(row[column])
        values[f"{prefix}_{column}"] = normalized
        if not valid:
            reasons.append(f"{prefix}_invalid_{column}={row[column]!r}")

    cpu_time, cpu_valid = _normalize_nonnegative_float(row["final_cpu_time"])
    values[f"{prefix}_final_cpu_time"] = cpu_time
    if not cpu_valid:
        reasons.append(
            f"{prefix}_invalid_final_cpu_time={row['final_cpu_time']!r}"
        )
    return values, reasons


def _missing_pair_record(pair_id: str) -> dict[str, object]:
    repeat_id, base_instance_id, variant = _parse_pair_id(pair_id)
    record: dict[str, object] = {
        "pair_id": pair_id,
        "repeat_id": repeat_id,
        "base_instance_id": base_instance_id,
        "variant": variant,
        "plain_method_count": 0,
        "neutral_method_count": 0,
        "accepted": False,
        "rejection_reason": "missing_pair",
    }
    record.update(_empty_comparison_values())
    return record


def _coverage_failure_record(reason: str) -> dict[str, object]:
    record: dict[str, object] = {
        "pair_id": "__coverage__",
        "plain_method_count": 0,
        "neutral_method_count": 0,
        "accepted": False,
        "rejection_reason": reason,
    }
    record.update(_empty_comparison_values())
    return record


def _empty_comparison_values() -> dict[str, object]:
    columns = [
        *(f"plain_{column}" for column in FINAL_COLUMNS),
        *(f"neutral_{column}" for column in FINAL_COLUMNS),
        "final_cpu_time_delta",
        "result_match",
        "solved_match",
        "decisions_match",
        "conflicts_match",
    ]
    return {column: pd.NA for column in columns}


def _audit_frame(records: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(records, columns=AUDIT_COLUMNS, dtype=object)


def _pair_key_reasons(pair_values: Iterable[object]) -> list[str]:
    return [
        f"invalid_{column}_missing"
        for column, value in zip(PAIR_COLUMNS, pair_values)
        if pd.isna(value)
    ]


def _format_pair_value(value: object) -> str:
    if pd.isna(value):
        return "<missing>"
    if isinstance(value, (float, np.floating)) and float(value).is_integer():
        return str(int(value))
    return str(value)


def _parse_pair_id(pair_id: str) -> tuple[object, object, object]:
    match = PAIR_ID_PATTERN.fullmatch(pair_id)
    if match is None:
        return pd.NA, pd.NA, pd.NA
    repeat_value, base_instance_id, variant = match.groups()
    try:
        repeat_id: object = int(repeat_value)
    except ValueError:
        repeat_id = repeat_value
    return repeat_id, base_instance_id, variant


def _normalize_boolean(value: object) -> tuple[object, bool]:
    if isinstance(value, (bool, np.bool_)):
        return bool(value), True
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return True, True
        if normalized in {"false", "0"}:
            return False, True
    if isinstance(value, (int, np.integer)) and not isinstance(
        value, (bool, np.bool_)
    ):
        if value == 1:
            return True, True
        if value == 0:
            return False, True
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if math.isfinite(number) and number == 1:
            return True, True
        if math.isfinite(number) and number == 0:
            return False, True
    return pd.NA, False


def _normalize_nonnegative_integer(value: object) -> tuple[object, bool]:
    if isinstance(value, (int, np.integer)) and not isinstance(
        value, (bool, np.bool_)
    ):
        return (int(value), True) if value >= 0 else (value, False)
    if not isinstance(value, (float, np.floating)):
        return value, False
    number = float(value)
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        return value, False
    return int(number), True


def _normalize_nonnegative_float(value: object) -> tuple[object, bool]:
    if not _is_numeric(value):
        return value, False
    try:
        number = float(value)
    except OverflowError:
        return value, False
    if not math.isfinite(number) or number < 0:
        return value, False
    return number, True


def _is_numeric(value: object) -> bool:
    return isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(
        value, (bool, np.bool_)
    )


def _exact_equal(left: object, right: object) -> bool:
    if pd.isna(left) or pd.isna(right):
        return False
    return bool(left == right)


def _numeric_delta(neutral: object, plain: object) -> float:
    if not _is_numeric(neutral) or not _is_numeric(plain):
        return float("nan")
    neutral_number = float(neutral)
    plain_number = float(plain)
    if not math.isfinite(neutral_number) or not math.isfinite(plain_number):
        return float("nan")
    return neutral_number - plain_number
