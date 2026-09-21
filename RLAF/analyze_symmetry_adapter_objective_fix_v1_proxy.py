from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

TARGETED_SUMMARY = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_candidate_summary.csv"
TARGETED_ORBITS = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_orbit_rows.csv"
SUBSET_VARIANTS = ROOT / "runs/analysis/symmetry_adapter_objective_subset_variant_summary_v2.csv"
SUBSET_PAIRS = ROOT / "runs/analysis/symmetry_adapter_objective_subset_pair_summary_v2.csv"
RANDOM_CONTROLS = ROOT / "runs/analysis/symmetry_adapter_objective_random_control_summary_v2.csv"
STRICT_SUMMARY = ROOT / "runs/analysis/symmetry_current_strict_positive_v2_summary.csv"

ROWS_OUT = ROOT / "runs/analysis/symmetry_adapter_objective_fix_v1_proxy_rows.csv"
SUMMARY_OUT = ROOT / "runs/analysis/symmetry_adapter_objective_fix_v1_proxy_summary.csv"
DOC_OUT = ROOT / "docs/symmetry_adapter_objective_fix_v1_proxy.md"

SUBSET_BASE = "subset_cardinality_bw12"
HEX_BASE = "dominating_set_hex_3x6_s4"
RANDOM_FAMILY = "random_3sat_control"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def bool_series(values: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False).astype(bool)
    return values.fillna(False).astype(str).str.lower().isin({"true", "1", "yes"})


def num(value: Any, default: float = 0.0) -> float:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(parsed):
        return float(default)
    return float(parsed)


def signed_log_improvement(delta: float) -> float:
    """Positive when the adapter reduces a search count, negative when it increases it."""
    if not math.isfinite(delta):
        return 0.0
    if delta < 0.0:
        return math.log1p(-delta)
    if delta > 0.0:
        return -math.log1p(delta)
    return 0.0


def search_delta_reward(decisions_delta: float, conflicts_delta: float, allow_positive: bool = True) -> float:
    if not allow_positive:
        return 0.0
    return 0.5 * (
        signed_log_improvement(float(decisions_delta))
        + signed_log_improvement(float(conflicts_delta))
    )


def invalid_orbit_identity_penalty(
    valid_event_gain: float,
    invalid_event_gain: float,
    valid_adapter_gain: float,
    invalid_adapter_gain: float,
) -> float:
    event_excess = max(0.0, float(invalid_event_gain) - max(float(valid_event_gain), 0.0))
    adapter_excess = max(0.0, float(invalid_adapter_gain) - max(float(valid_adapter_gain), 0.0))
    return 0.05 * math.log1p(event_excess) + 0.10 * math.log1p(adapter_excess)


def adapter_delta_magnitude_penalty(adapter_gain: float, event_gain: float, search_worse_rate: float) -> float:
    adapter_gain = max(float(adapter_gain), 0.0)
    event_gain = max(float(event_gain), 0.0)
    mild_size = 0.25 * math.log1p(adapter_gain)
    over_event = max(0.0, adapter_gain - event_gain - 0.25)
    worse_multiplier = 1.0 + max(float(search_worse_rate), 0.0)
    return mild_size + worse_multiplier * 0.20 * math.log1p(over_event)


def random_control_penalty(row: pd.Series) -> float:
    rows = max(num(row.get("rows"), default=1.0), 1.0)
    decision_change_rate = (num(row.get("decisions_down_rows")) + num(row.get("decisions_up_rows"))) / rows
    conflict_change_rate = (num(row.get("conflicts_down_rows")) + num(row.get("conflicts_up_rows"))) / rows
    perturbation_rate = 0.5 * (decision_change_rate + conflict_change_rate)
    strict_bonus = 1.0 if str(row.get("primary_classification", "")).lower() == "strict_positive" else 0.0
    activity_bonus = 0.15 * math.log1p(max(num(row.get("event_state_l2_mean")), 0.0))
    return 1.5 + perturbation_rate + strict_bonus + activity_bonus


def subset_pair_penalty_by_variant(pair_summary: pd.DataFrame, variant_summary: pd.DataFrame) -> dict[str, float]:
    if pair_summary.empty or variant_summary.empty:
        return {}
    worse_rates = {
        str(row["variant"]): num(row.get("search_worse_rows")) / max(num(row.get("repeat_rows"), default=1.0), 1.0)
        for _, row in variant_summary.iterrows()
    }
    reference_worse_rate = float(np.median(list(worse_rates.values()))) if worse_rates else 0.0
    penalties: dict[str, float] = {variant: 0.0 for variant in worse_rates}
    for _, pair in pair_summary.iterrows():
        left = str(pair["left_variant"])
        right = str(pair["right_variant"])
        orbit_rows = max(num(pair.get("orbit_pair_rows"), default=1.0), 1.0)
        mismatch_rate = num(pair.get("search_direction_mismatch_rows")) / orbit_rows
        adapted_weak = max(0.0, 0.65 - num(pair.get("mean_adapted_mu_spearman"), default=0.65))
        delta_weak = max(0.0, 0.50 - num(pair.get("mean_delta_mu_spearman"), default=0.50))
        gain_gap = 0.20 * math.log1p(max(num(pair.get("valid_mean_adapter_gain_abs_diff")), 0.0))
        pair_penalty = 1.25 * mismatch_rate + adapted_weak + delta_weak + gain_gap
        for variant in [left, right]:
            direction_outlier = abs(worse_rates.get(variant, 0.0) - reference_worse_rate)
            penalties[variant] = max(penalties.get(variant, 0.0), pair_penalty * direction_outlier)
    return penalties


def orbit_summary(orbits: pd.DataFrame, base_instance_id: str) -> dict[str, float]:
    group = orbits[orbits["base_instance_id"].astype(str).eq(base_instance_id)].copy()
    if group.empty:
        return {
            "orbit_rows": 0.0,
            "valid_orbit_rows": 0.0,
            "event_positive_valid_rows": 0.0,
            "event_gain_valid_max": 0.0,
            "event_gain_invalid_max": 0.0,
            "adapter_gain_valid_max": 0.0,
            "adapter_gain_invalid_max": 0.0,
            "adapted_mu_range_valid_max": 0.0,
        }
    valid = bool_series(group["event_row_valid"]) if "event_row_valid" in group.columns else pd.Series(False, index=group.index)
    positive = bool_series(group["event_identity_positive"]) if "event_identity_positive" in group.columns else pd.Series(False, index=group.index)
    valid_group = group[valid].copy()
    invalid_group = group[~valid].copy()

    def max_col(frame: pd.DataFrame, column: str) -> float:
        if frame.empty or column not in frame.columns:
            return 0.0
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        return float(values.max()) if not values.empty else 0.0

    return {
        "orbit_rows": float(len(group)),
        "valid_orbit_rows": float(len(valid_group)),
        "event_positive_valid_rows": float((valid & positive).sum()),
        "event_gain_valid_max": max_col(valid_group, "event_identity_gain"),
        "event_gain_invalid_max": max_col(invalid_group, "event_identity_gain"),
        "adapter_gain_valid_max": max_col(valid_group, "adapter_identity_gain"),
        "adapter_gain_invalid_max": max_col(invalid_group, "adapter_identity_gain"),
        "adapted_mu_range_valid_max": max_col(valid_group, "adapted_mu_range"),
    }


def add_objective(row: dict[str, Any]) -> dict[str, Any]:
    row["objective_score"] = (
        float(row["search_delta_reward"])
        - float(row["permutation_inconsistency_penalty"])
        - float(row["invalid_orbit_identity_penalty"])
        - float(row["non_symmetric_perturbation_penalty"])
        - float(row["adapter_delta_magnitude_penalty"])
    )
    if row["objective_score"] > 0.5:
        row["proxy_label"] = "positive"
    elif row["objective_score"] < -0.5:
        row["proxy_label"] = "negative"
    else:
        row["proxy_label"] = "mixed"
    return row


def build_rows() -> pd.DataFrame:
    targeted = read_csv(TARGETED_SUMMARY)
    orbits = read_csv(TARGETED_ORBITS)
    subset_variants = read_csv(SUBSET_VARIANTS)
    subset_pairs = read_csv(SUBSET_PAIRS)
    random_controls = read_csv(RANDOM_CONTROLS)
    strict = read_csv(STRICT_SUMMARY)

    rows: list[dict[str, Any]] = []

    pair_penalty = subset_pair_penalty_by_variant(subset_pairs, subset_variants)
    for _, variant_row in subset_variants.iterrows():
        variant = str(variant_row["variant"])
        repeat_rows = max(num(variant_row.get("repeat_rows"), default=1.0), 1.0)
        search_worse_rate = num(variant_row.get("search_worse_rows")) / repeat_rows
        valid_event = num(variant_row.get("event_identity_gain_max_valid"))
        invalid_event = num(variant_row.get("event_identity_gain_max_invalid"))
        valid_adapter = num(variant_row.get("adapter_identity_gain_max_valid"))
        invalid_adapter = num(variant_row.get("adapter_identity_gain_max_invalid"))
        row = {
            "case_id": f"{SUBSET_BASE}::{variant}",
            "family": "subset_cardinality",
            "base_instance_id": SUBSET_BASE,
            "variant": variant,
            "case_type": "symmetry_variant",
            "repeat_rows": int(repeat_rows),
            "decisions_delta_mean": num(variant_row.get("decisions_delta_mean")),
            "conflicts_delta_mean": num(variant_row.get("conflicts_delta_mean")),
            "search_worse_rate": search_worse_rate,
            "valid_orbit_rows": int(num(variant_row.get("valid_orbit_rows"))),
            "invalid_orbit_rows": int(num(variant_row.get("invalid_orbit_rows"))),
            "event_positive_valid_rows": int(num(variant_row.get("event_positive_valid_rows"))),
            "event_gain_valid_max": valid_event,
            "event_gain_invalid_max": invalid_event,
            "adapter_gain_valid_max": valid_adapter,
            "adapter_gain_invalid_max": invalid_adapter,
            "search_delta_reward": search_delta_reward(
                num(variant_row.get("decisions_delta_mean")),
                num(variant_row.get("conflicts_delta_mean")),
            ),
            "permutation_inconsistency_penalty": pair_penalty.get(variant, 0.0),
            "invalid_orbit_identity_penalty": invalid_orbit_identity_penalty(
                valid_event,
                invalid_event,
                valid_adapter,
                invalid_adapter,
            ),
            "non_symmetric_perturbation_penalty": 0.0,
            "adapter_delta_magnitude_penalty": adapter_delta_magnitude_penalty(
                valid_adapter,
                valid_event,
                search_worse_rate=search_worse_rate,
            ),
            "notes": "subset permutation robustness target",
        }
        rows.append(add_objective(row))

    targeted_by_base = {str(row["base_instance_id"]): row for _, row in targeted.iterrows()}
    if HEX_BASE in targeted_by_base:
        hex_row = targeted_by_base[HEX_BASE]
        summary = orbit_summary(orbits, HEX_BASE)
        search_worse_rate = 1.0 - (
            0.5
            * (
                num(hex_row.get("decisions_down_rows")) / max(num(hex_row.get("repeat_rows"), default=1.0), 1.0)
                + num(hex_row.get("conflicts_down_rows")) / max(num(hex_row.get("repeat_rows"), default=1.0), 1.0)
            )
        )
        row = {
            "case_id": HEX_BASE,
            "family": str(hex_row["family"]),
            "base_instance_id": HEX_BASE,
            "variant": "all_variants",
            "case_type": "symmetry_targeted",
            "repeat_rows": int(num(hex_row.get("repeat_rows"))),
            "decisions_delta_mean": num(hex_row.get("mean_primary_delta_final_decisions")),
            "conflicts_delta_mean": num(hex_row.get("mean_primary_delta_final_conflicts")),
            "search_worse_rate": max(0.0, min(1.0, search_worse_rate)),
            "valid_orbit_rows": int(summary["valid_orbit_rows"]),
            "invalid_orbit_rows": int(summary["orbit_rows"] - summary["valid_orbit_rows"]),
            "event_positive_valid_rows": int(summary["event_positive_valid_rows"]),
            "event_gain_valid_max": summary["event_gain_valid_max"],
            "event_gain_invalid_max": summary["event_gain_invalid_max"],
            "adapter_gain_valid_max": summary["adapter_gain_valid_max"],
            "adapter_gain_invalid_max": summary["adapter_gain_invalid_max"],
            "search_delta_reward": search_delta_reward(
                num(hex_row.get("mean_primary_delta_final_decisions")),
                num(hex_row.get("mean_primary_delta_final_conflicts")),
            ),
            "permutation_inconsistency_penalty": 0.0,
            "invalid_orbit_identity_penalty": invalid_orbit_identity_penalty(
                summary["event_gain_valid_max"],
                summary["event_gain_invalid_max"],
                summary["adapter_gain_valid_max"],
                summary["adapter_gain_invalid_max"],
            ),
            "non_symmetric_perturbation_penalty": 0.0,
            "adapter_delta_magnitude_penalty": adapter_delta_magnitude_penalty(
                num(hex_row.get("mean_adapter_identity_gain_max")),
                num(hex_row.get("mean_event_identity_gain_max")),
                search_worse_rate=max(0.0, min(1.0, search_worse_rate)),
            ),
            "notes": "hex partial mechanism target; conflicts improve but CPU is not used as reward",
        }
        rows.append(add_objective(row))

    for _, control in random_controls.iterrows():
        row = {
            "case_id": str(control["base_instance_id"]),
            "family": RANDOM_FAMILY,
            "base_instance_id": str(control["base_instance_id"]),
            "variant": "all_variants",
            "case_type": "non_symmetric_control",
            "repeat_rows": int(num(control.get("rows"))),
            "decisions_delta_mean": np.nan,
            "conflicts_delta_mean": np.nan,
            "search_worse_rate": (
                num(control.get("decisions_up_rows")) + num(control.get("conflicts_up_rows"))
            )
            / max(2.0 * num(control.get("rows"), default=1.0), 1.0),
            "valid_orbit_rows": int(num(control.get("valid_orbit_rows"))),
            "invalid_orbit_rows": int(num(control.get("orbit_audit_rows"))),
            "event_positive_valid_rows": int(num(control.get("event_positive_orbit_rows"))),
            "event_gain_valid_max": 0.0,
            "event_gain_invalid_max": 0.0,
            "adapter_gain_valid_max": 0.0,
            "adapter_gain_invalid_max": num(control.get("max_adapter_identity_gain_audited")),
            "search_delta_reward": 0.0,
            "permutation_inconsistency_penalty": 0.0,
            "invalid_orbit_identity_penalty": 0.0,
            "non_symmetric_perturbation_penalty": random_control_penalty(control),
            "adapter_delta_magnitude_penalty": 0.0,
            "notes": str(control.get("negative_control_signal", "")),
        }
        rows.append(add_objective(row))

    strict_symmetry = strict[
        strict["base_instance_id"].astype(str).eq("k5_color4")
        & strict["family"].astype(str).eq("complete_coloring")
    ]
    for _, strict_row in strict_symmetry.iterrows():
        row = {
            "case_id": str(strict_row["base_instance_id"]),
            "family": str(strict_row["family"]),
            "base_instance_id": str(strict_row["base_instance_id"]),
            "variant": "all_variants",
            "case_type": "symmetry_calibration",
            "repeat_rows": int(num(strict_row.get("repeat_rows"))),
            "decisions_delta_mean": num(strict_row.get("mean_primary_delta_final_decisions")),
            "conflicts_delta_mean": num(strict_row.get("mean_primary_delta_final_conflicts")),
            "search_worse_rate": 0.0,
            "valid_orbit_rows": np.nan,
            "invalid_orbit_rows": np.nan,
            "event_positive_valid_rows": int(num(strict_row.get("event_identity_positive_rows"))),
            "event_gain_valid_max": num(strict_row.get("mean_event_identity_gain_max")),
            "event_gain_invalid_max": 0.0,
            "adapter_gain_valid_max": num(strict_row.get("mean_adapter_identity_gain_max")),
            "adapter_gain_invalid_max": 0.0,
            "search_delta_reward": search_delta_reward(
                num(strict_row.get("mean_primary_delta_final_decisions")),
                num(strict_row.get("mean_primary_delta_final_conflicts")),
            ),
            "permutation_inconsistency_penalty": 0.0,
            "invalid_orbit_identity_penalty": 0.0,
            "non_symmetric_perturbation_penalty": 0.0,
            "adapter_delta_magnitude_penalty": adapter_delta_magnitude_penalty(
                num(strict_row.get("mean_adapter_identity_gain_max")),
                num(strict_row.get("mean_event_identity_gain_max")),
                search_worse_rate=0.0,
            ),
            "notes": "strict-positive symmetry calibration only; not a speedup claim",
        }
        rows.append(add_objective(row))

    return pd.DataFrame(rows)


def build_summary(rows: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, Any]] = []
    for case_type, group in rows.groupby("case_type", sort=True):
        summary_rows.append(
            {
                "case_type": case_type,
                "rows": int(len(group)),
                "positive_rows": int((group["proxy_label"] == "positive").sum()),
                "mixed_rows": int((group["proxy_label"] == "mixed").sum()),
                "negative_rows": int((group["proxy_label"] == "negative").sum()),
                "objective_score_mean": float(group["objective_score"].mean()),
                "search_delta_reward_mean": float(group["search_delta_reward"].mean()),
                "penalty_mean": float(
                    (
                        group["permutation_inconsistency_penalty"]
                        + group["invalid_orbit_identity_penalty"]
                        + group["non_symmetric_perturbation_penalty"]
                        + group["adapter_delta_magnitude_penalty"]
                    ).mean()
                ),
            }
        )
    return pd.DataFrame(summary_rows)


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_None._"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in view.iterrows():
        values: list[str] = []
        for column in columns:
            value = row[column]
            if isinstance(value, (float, np.floating)):
                values.append("nan" if math.isnan(float(value)) else f"{float(value):.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    if len(frame) > max_rows:
        lines.append(f"| ... | {len(frame) - max_rows} more rows |" + " |" * max(0, len(columns) - 2))
    return lines


def write_doc(rows: pd.DataFrame, summary: pd.DataFrame) -> None:
    key_cols = [
        "case_id",
        "case_type",
        "proxy_label",
        "objective_score",
        "search_delta_reward",
        "permutation_inconsistency_penalty",
        "invalid_orbit_identity_penalty",
        "non_symmetric_perturbation_penalty",
        "adapter_delta_magnitude_penalty",
    ]
    subset = rows[rows["base_instance_id"].astype(str).eq(SUBSET_BASE)][key_cols].copy()
    named = rows[
        rows["case_id"].astype(str).isin(
            [
                HEX_BASE,
                f"{SUBSET_BASE}::base",
                f"{SUBSET_BASE}::perm_seed1730",
                f"{SUBSET_BASE}::perm_seed1731",
                "k5_color4",
            ]
        )
    ][key_cols].copy()
    controls = rows[rows["case_type"].astype(str).eq("non_symmetric_control")][
        ["case_id", "proxy_label", "objective_score", "non_symmetric_perturbation_penalty", "notes"]
    ].copy()

    lines = [
        "# Symmetry Adapter Objective Fix v1 Proxy",
        "",
        "This is an offline objective proxy over the frozen v2 diagnosis CSVs. It is not a solver speedup claim, does not expand the full runtime benchmark, and does not train a gate/selector.",
        "",
        "Proxy formula:",
        "",
        "```text",
        "objective_score = search_delta_reward",
        "  - permutation_inconsistency_penalty",
        "  - invalid_orbit_identity_penalty",
        "  - non_symmetric_perturbation_penalty",
        "  - adapter_delta_magnitude_penalty",
        "```",
        "",
        "Positive search-count deltas are penalized and negative deltas are rewarded. Non-symmetric controls receive no positive search reward; their search changes are treated as perturbation risk.",
        "",
        "## Summary",
        "",
        *markdown_table(summary),
        "",
        "## Named Checks",
        "",
        *markdown_table(named),
        "",
        "## Subset Permutation Split",
        "",
        *markdown_table(subset),
        "",
        "## Random Controls",
        "",
        *markdown_table(controls),
        "",
        "## Interpretation",
        "",
        "- `subset_cardinality_bw12::perm_seed1730` is penalized because it is the direction-outlier permutation variant: valid orbit evidence exists, but final decisions/conflicts worsen and pairwise permutation consistency is poor.",
        "- `subset_cardinality_bw12::base` and `subset_cardinality_bw12::perm_seed1731` remain positive despite invalid-orbit warnings because their search-count deltas improve and they are not the direction outlier.",
        "- `dominating_set_hex_3x6_s4` remains positive/mixed-aligned on the proxy: conflicts improve and valid event-orbit evidence exists, while CPU is intentionally ignored.",
        "- Random controls are all negative under the non-symmetric perturbation guard, including the strict-positive runtime perturbation control.",
        "",
        "Next step remains default-off loss implementation plus unit/smoke verification, not full runtime or gate training.",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_rows()
    rows = rows.sort_values(["case_type", "case_id"]).reset_index(drop=True)
    summary = build_summary(rows)
    ROWS_OUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(ROWS_OUT, index=False)
    summary.to_csv(SUMMARY_OUT, index=False)
    write_doc(rows, summary)
    print(f"Wrote {ROWS_OUT}")
    print(f"Wrote {SUMMARY_OUT}")
    print(f"Wrote {DOC_OUT}")


if __name__ == "__main__":
    main()
