from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

SUBSET_VARIABLE_ROWS = ROOT / "runs/analysis/symmetry_subset_bw12_variable_rows_v2.csv"
TARGETED_ORBIT_ROWS = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_orbit_rows.csv"
TARGETED_REPEAT_JOIN = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_repeat_join.csv"
STRICT_ORBIT_ROWS = ROOT / "runs/analysis/symmetry_current_strict_positive_v2_orbit_rows.csv"
STRICT_REPEAT_JOIN = ROOT / "runs/analysis/symmetry_current_strict_positive_v2_repeat_join.csv"
POSITIVE_OBSERVATIONS = ROOT / "runs/analysis/symmetry_runtime_positive_v2_observations.csv"
POSITIVE_BASE_SUMMARY = ROOT / "runs/analysis/symmetry_runtime_positive_v2_base_summary.csv"

DOC = ROOT / "docs/symmetry_adapter_objective_robustness_v2.md"
SUBSET_PAIR_ALIGNMENT_CSV = ROOT / "runs/analysis/symmetry_adapter_objective_subset_pair_alignment_v2.csv"
SUBSET_PAIR_SUMMARY_CSV = ROOT / "runs/analysis/symmetry_adapter_objective_subset_pair_summary_v2.csv"
SUBSET_VARIANT_SUMMARY_CSV = ROOT / "runs/analysis/symmetry_adapter_objective_subset_variant_summary_v2.csv"
SUBSET_ORBIT_CONTRIB_CSV = ROOT / "runs/analysis/symmetry_adapter_objective_subset_orbit_contrib_v2.csv"
OVERADAPTATION_ORBITS_CSV = ROOT / "runs/analysis/symmetry_adapter_objective_overadaptation_orbits_v2.csv"
RANDOM_CONTROL_SUMMARY_CSV = ROOT / "runs/analysis/symmetry_adapter_objective_random_control_summary_v2.csv"
OBJECTIVE_RECOMMENDATIONS_CSV = ROOT / "runs/analysis/symmetry_adapter_objective_recommendations_v2.csv"

SUBSET_BASE = "subset_cardinality_bw12"
RANDOM_FAMILY = "random_3sat_control"


def bool_series(values: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False).astype(bool)
    return values.fillna(False).astype(str).str.lower().isin({"true", "1", "yes"})


def numeric(frame: pd.DataFrame, column: str, default: float = np.nan) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    valid = left.notna() & right.notna()
    if int(valid.sum()) < 2:
        return float("nan")
    left_valid = left[valid]
    right_valid = right[valid]
    if left_valid.nunique(dropna=True) < 2 or right_valid.nunique(dropna=True) < 2:
        return float("nan")
    return float(left_valid.corr(right_valid, method=method))


def mean_or_nan(values: pd.Series) -> float:
    values = pd.to_numeric(values, errors="coerce").dropna()
    return float(values.mean()) if not values.empty else float("nan")


def max_or_nan(values: pd.Series) -> float:
    values = pd.to_numeric(values, errors="coerce").dropna()
    return float(values.max()) if not values.empty else float("nan")


def search_direction(decision_delta: float, conflict_delta: float) -> str:
    worse = (decision_delta > 0.0) or (conflict_delta > 0.0)
    better = (decision_delta < 0.0) or (conflict_delta < 0.0)
    if worse and not better:
        return "search_worse"
    if better and not worse:
        return "search_better"
    if worse and better:
        return "mixed_search"
    return "search_flat"


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
        values = []
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


def load_inputs() -> dict[str, pd.DataFrame]:
    paths = {
        "subset_variables": SUBSET_VARIABLE_ROWS,
        "targeted_orbits": TARGETED_ORBIT_ROWS,
        "targeted_repeat": TARGETED_REPEAT_JOIN,
        "strict_orbits": STRICT_ORBIT_ROWS,
        "strict_repeat": STRICT_REPEAT_JOIN,
        "positive_observations": POSITIVE_OBSERVATIONS,
        "positive_base": POSITIVE_BASE_SUMMARY,
    }
    missing = [path for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")
    return {name: pd.read_csv(path) for name, path in paths.items()}


def runtime_lookup(repeat_join: pd.DataFrame) -> dict[tuple[int, str], pd.Series]:
    lookup: dict[tuple[int, str], pd.Series] = {}
    for _, row in repeat_join.iterrows():
        lookup[(int(row["repeat_id"]), str(row["variant"]))] = row
    return lookup


def orbit_lookup(orbit_rows: pd.DataFrame) -> dict[tuple[int, str, str], pd.Series]:
    lookup: dict[tuple[int, str, str], pd.Series] = {}
    for _, row in orbit_rows.iterrows():
        lookup[(int(row["repeat_id"]), str(row["variant"]), str(row["orbit"]))] = row
    return lookup


def build_subset_pair_alignment(
    variable_rows: pd.DataFrame,
    subset_repeat: pd.DataFrame,
    subset_orbits: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rt = runtime_lookup(subset_repeat)
    orbit_by_key = orbit_lookup(subset_orbits)
    metrics = [
        "static_mu",
        "static_rho",
        "adapted_mu",
        "adapted_rho",
        "delta_mu",
        "delta_rho",
        "event_l2",
    ]
    for (repeat_id, orbit), group in variable_rows.groupby(["repeat_id", "orbit"], sort=True):
        variants = sorted(group["variant"].astype(str).unique())
        if len(variants) < 2:
            continue
        for left, right in combinations(variants, 2):
            left_frame = group[group["variant"].astype(str).eq(left)].copy()
            right_frame = group[group["variant"].astype(str).eq(right)].copy()
            aligned = left_frame.merge(
                right_frame,
                on="original_var",
                suffixes=("_left", "_right"),
                how="inner",
            )
            row: dict[str, Any] = {
                "base_instance_id": SUBSET_BASE,
                "repeat_id": int(repeat_id),
                "orbit": str(orbit),
                "left_variant": left,
                "right_variant": right,
                "aligned_variables": int(len(aligned)),
            }
            left_rt = rt.get((int(repeat_id), left))
            right_rt = rt.get((int(repeat_id), right))
            for side, variant, runtime_row in [("left", left, left_rt), ("right", right, right_rt)]:
                if runtime_row is not None:
                    dec = float(runtime_row["primary_delta_final_decisions"])
                    conf = float(runtime_row["primary_delta_final_conflicts"])
                    row[f"{side}_decisions_delta"] = dec
                    row[f"{side}_conflicts_delta"] = conf
                    row[f"{side}_search_direction"] = search_direction(dec, conf)
                orbit_row = orbit_by_key.get((int(repeat_id), variant, str(orbit)))
                if orbit_row is not None:
                    row[f"{side}_event_identity_gain"] = float(orbit_row.get("event_identity_gain", np.nan))
                    row[f"{side}_adapter_identity_gain"] = float(orbit_row.get("adapter_identity_gain", np.nan))
                    row[f"{side}_adapted_mu_range"] = float(orbit_row.get("adapted_mu_range", np.nan))
                    row[f"{side}_static_mu_range"] = float(orbit_row.get("static_mu_range", np.nan))
                    row[f"{side}_event_row_valid"] = bool(orbit_row.get("event_row_valid", False))
                    row[f"{side}_event_row_valid_reason"] = str(orbit_row.get("event_row_valid_reason", ""))
            for metric in metrics:
                left_values = pd.to_numeric(aligned.get(f"{metric}_left", pd.Series(dtype=float)), errors="coerce")
                right_values = pd.to_numeric(aligned.get(f"{metric}_right", pd.Series(dtype=float)), errors="coerce")
                row[f"{metric}_spearman"] = safe_corr(left_values, right_values, method="spearman")
                row[f"{metric}_pearson"] = safe_corr(left_values, right_values, method="pearson")
                row[f"{metric}_mean_abs_diff"] = float((left_values - right_values).abs().mean()) if len(aligned) else float("nan")
            for metric in ["delta_mu", "delta_rho"]:
                left_values = pd.to_numeric(aligned.get(f"{metric}_left", pd.Series(dtype=float)), errors="coerce")
                right_values = pd.to_numeric(aligned.get(f"{metric}_right", pd.Series(dtype=float)), errors="coerce")
                valid = left_values.notna() & right_values.notna()
                row[f"{metric}_sign_agreement"] = (
                    float((np.sign(left_values[valid]) == np.sign(right_values[valid])).mean())
                    if int(valid.sum()) > 0
                    else float("nan")
                )
            row["search_direction_mismatch"] = row.get("left_search_direction") != row.get("right_search_direction")
            row["adapter_gain_abs_diff"] = abs(row.get("left_adapter_identity_gain", np.nan) - row.get("right_adapter_identity_gain", np.nan))
            row["event_gain_abs_diff"] = abs(row.get("left_event_identity_gain", np.nan) - row.get("right_event_identity_gain", np.nan))
            rows.append(row)
    return pd.DataFrame(rows)


def build_pair_summary(pair_alignment: pd.DataFrame) -> pd.DataFrame:
    if pair_alignment.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (left, right), group in pair_alignment.groupby(["left_variant", "right_variant"], sort=True):
        valid_pair = group[
            bool_series(group.get("left_event_row_valid", pd.Series(False, index=group.index)))
            & bool_series(group.get("right_event_row_valid", pd.Series(False, index=group.index)))
        ].copy()
        rows.append(
            {
                "left_variant": left,
                "right_variant": right,
                "orbit_pair_rows": int(len(group)),
                "valid_pair_rows": int(len(valid_pair)),
                "search_direction_mismatch_rows": int(bool_series(group["search_direction_mismatch"]).sum()),
                "mean_static_mu_spearman": mean_or_nan(group["static_mu_spearman"]),
                "mean_static_rho_spearman": mean_or_nan(group["static_rho_spearman"]),
                "mean_adapted_mu_spearman": mean_or_nan(group["adapted_mu_spearman"]),
                "mean_adapted_rho_spearman": mean_or_nan(group["adapted_rho_spearman"]),
                "mean_delta_mu_spearman": mean_or_nan(group["delta_mu_spearman"]),
                "mean_delta_mu_sign_agreement": mean_or_nan(group["delta_mu_sign_agreement"]),
                "valid_mean_event_gain_abs_diff": mean_or_nan(valid_pair["event_gain_abs_diff"]) if not valid_pair.empty else float("nan"),
                "valid_mean_adapter_gain_abs_diff": mean_or_nan(valid_pair["adapter_gain_abs_diff"]) if not valid_pair.empty else float("nan"),
                "all_mean_event_gain_abs_diff": mean_or_nan(group["event_gain_abs_diff"]),
                "all_mean_adapter_gain_abs_diff": mean_or_nan(group["adapter_gain_abs_diff"]),
            }
        )
    return pd.DataFrame(rows)


def build_subset_variant_summary(subset_repeat: pd.DataFrame, subset_orbits: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    subset_orbits = subset_orbits.copy()
    subset_orbits["_event_valid"] = bool_series(subset_orbits["event_row_valid"])
    subset_orbits["_event_positive"] = bool_series(subset_orbits["event_identity_positive"])
    for variant, group in subset_repeat.groupby("variant", sort=True):
        orbit_group = subset_orbits[subset_orbits["variant"].astype(str).eq(str(variant))].copy()
        valid = orbit_group[orbit_group["_event_valid"]].copy()
        invalid = orbit_group[~orbit_group["_event_valid"]].copy()
        dec = pd.to_numeric(group["primary_delta_final_decisions"], errors="coerce")
        conf = pd.to_numeric(group["primary_delta_final_conflicts"], errors="coerce")
        rows.append(
            {
                "variant": str(variant),
                "repeat_rows": int(len(group)),
                "search_worse_rows": int(((dec > 0.0) | (conf > 0.0)).sum()),
                "decisions_delta_mean": float(dec.mean()),
                "conflicts_delta_mean": float(conf.mean()),
                "event_identity_gain_max_all": max_or_nan(orbit_group["event_identity_gain"]),
                "event_identity_gain_max_valid": max_or_nan(valid["event_identity_gain"]),
                "event_identity_gain_max_invalid": max_or_nan(invalid["event_identity_gain"]),
                "adapter_identity_gain_max_all": max_or_nan(orbit_group["adapter_identity_gain"]),
                "adapter_identity_gain_max_valid": max_or_nan(valid["adapter_identity_gain"]),
                "adapter_identity_gain_max_invalid": max_or_nan(invalid["adapter_identity_gain"]),
                "adapted_mu_range_max_valid": max_or_nan(valid["adapted_mu_range"]),
                "adapted_mu_range_max_invalid": max_or_nan(invalid["adapted_mu_range"]),
                "valid_orbit_rows": int(len(valid)),
                "invalid_orbit_rows": int(len(invalid)),
                "event_positive_valid_rows": int(valid["_event_positive"].sum()),
                "event_positive_invalid_rows": int(invalid["_event_positive"].sum()),
            }
        )
    return pd.DataFrame(rows)


def build_subset_orbit_contrib(subset_orbits: pd.DataFrame) -> pd.DataFrame:
    work = subset_orbits.copy()
    work["search_worse"] = (numeric(work, "primary_delta_final_decisions") > 0.0) | (
        numeric(work, "primary_delta_final_conflicts") > 0.0
    )
    grouped = work.groupby(["variant", "event_row_valid_reason"], sort=True)
    return grouped.agg(
        rows=("orbit", "size"),
        search_worse_rows=("search_worse", "sum"),
        event_identity_gain_mean=("event_identity_gain", "mean"),
        event_identity_gain_max=("event_identity_gain", "max"),
        adapter_identity_gain_mean=("adapter_identity_gain", "mean"),
        adapter_identity_gain_max=("adapter_identity_gain", "max"),
        adapted_mu_range_mean=("adapted_mu_range", "mean"),
        adapted_mu_range_max=("adapted_mu_range", "max"),
        static_mu_range_mean=("static_mu_range", "mean"),
        static_mu_range_max=("static_mu_range", "max"),
    ).reset_index()


def build_overadaptation_orbits(subset_orbits: pd.DataFrame) -> pd.DataFrame:
    work = subset_orbits.copy()
    work["search_worse"] = (numeric(work, "primary_delta_final_decisions") > 0.0) | (
        numeric(work, "primary_delta_final_conflicts") > 0.0
    )
    event_gain = numeric(work, "event_identity_gain").replace(0.0, np.nan)
    work["adapter_to_event_gain_ratio"] = numeric(work, "adapter_identity_gain") / event_gain
    work["valid_orbit"] = bool_series(work["event_row_valid"])
    columns = [
        "base_instance_id",
        "variant",
        "repeat_id",
        "orbit",
        "orbit_size",
        "event_row_valid_reason",
        "valid_orbit",
        "search_worse",
        "event_identity_gain",
        "adapter_identity_gain",
        "adapter_to_event_gain_ratio",
        "adapted_mu_range",
        "static_mu_range",
        "event_feature_l2_range",
        "primary_delta_final_decisions",
        "primary_delta_final_conflicts",
    ]
    return work[[column for column in columns if column in work.columns]].sort_values(
        ["search_worse", "valid_orbit", "adapter_identity_gain", "event_identity_gain"],
        ascending=[False, False, False, False],
    )


def build_random_control_summary(
    observations: pd.DataFrame,
    targeted_orbits: pd.DataFrame,
    strict_orbits: pd.DataFrame,
    base_summary: pd.DataFrame,
) -> pd.DataFrame:
    random_obs = observations[observations["family"].astype(str).eq(RANDOM_FAMILY)].copy()
    orbit_rows = pd.concat(
        [
            targeted_orbits[targeted_orbits["family"].astype(str).eq(RANDOM_FAMILY)].copy(),
            strict_orbits[strict_orbits["family"].astype(str).eq(RANDOM_FAMILY)].copy(),
        ],
        ignore_index=True,
    )
    orbit_rows["_event_valid"] = bool_series(orbit_rows["event_row_valid"]) if not orbit_rows.empty else pd.Series(dtype=bool)
    orbit_rows["_event_positive"] = bool_series(orbit_rows["event_identity_positive"]) if not orbit_rows.empty else pd.Series(dtype=bool)
    base_class = base_summary.set_index("base_instance_id")["primary_classification"].to_dict()
    rows: list[dict[str, Any]] = []
    for base, group in random_obs.groupby("base_instance_id", sort=True):
        dec = numeric(group, "primary_delta_final_decisions")
        conf = numeric(group, "primary_delta_final_conflicts")
        cpu = numeric(group, "primary_delta_final_cpu")
        orbit_group = orbit_rows[orbit_rows["base_instance_id"].astype(str).eq(str(base))].copy()
        rows.append(
            {
                "base_instance_id": str(base),
                "primary_classification": base_class.get(base, ""),
                "rows": int(len(group)),
                "cpu_down_rows": int((cpu < 0.0).sum()),
                "cpu_up_rows": int((cpu > 0.0).sum()),
                "decisions_down_rows": int((dec < 0.0).sum()),
                "decisions_up_rows": int((dec > 0.0).sum()),
                "conflicts_down_rows": int((conf < 0.0).sum()),
                "conflicts_up_rows": int((conf > 0.0).sum()),
                "event_state_l2_mean": mean_or_nan(group["event_state_l2_sum"]),
                "event_adapter_graph_gate_evidence_mean": mean_or_nan(group["event_adapter_graph_gate_evidence"]),
                "warmup_decisions_mean": mean_or_nan(group["warmup_decisions"]),
                "warmup_conflicts_mean": mean_or_nan(group["warmup_conflicts"]),
                "orbit_audit_rows": int(len(orbit_group)),
                "valid_orbit_rows": int(orbit_group["_event_valid"].sum()) if not orbit_group.empty else 0,
                "event_positive_orbit_rows": int(orbit_group["_event_positive"].sum()) if not orbit_group.empty else 0,
                "max_adapter_identity_gain_audited": max_or_nan(orbit_group["adapter_identity_gain"]) if not orbit_group.empty else float("nan"),
                "negative_control_signal": negative_control_signal(group, base_class.get(base, ""), orbit_group),
            }
        )
    return pd.DataFrame(rows)


def negative_control_signal(group: pd.DataFrame, classification: str, orbit_group: pd.DataFrame) -> str:
    dec = numeric(group, "primary_delta_final_decisions")
    conf = numeric(group, "primary_delta_final_conflicts")
    majority = int(len(group) // 2 + 1)
    dec_up = int((dec > 0.0).sum())
    conf_up = int((conf > 0.0).sum())
    dec_down = int((dec < 0.0).sum())
    conf_down = int((conf < 0.0).sum())
    valid_orbits = int(bool_series(orbit_group["event_row_valid"]).sum()) if not orbit_group.empty else 0
    if classification == "strict_positive" and valid_orbits == 0:
        return "non_symmetric_strict_positive_perturbation"
    if dec_up >= majority or conf_up >= majority:
        return "non_symmetric_search_worsening"
    if dec_down >= majority or conf_down >= majority:
        return "non_symmetric_search_change"
    return "non_symmetric_mixed_or_weak_change"


def build_objective_recommendations(
    pair_summary: pd.DataFrame,
    variant_summary: pd.DataFrame,
    random_summary: pd.DataFrame,
) -> pd.DataFrame:
    base_perm1730 = pair_summary[
        pair_summary["left_variant"].astype(str).eq("base")
        & pair_summary["right_variant"].astype(str).eq("perm_seed1730")
    ]
    base_perm1730_mu = (
        float(base_perm1730["mean_adapted_mu_spearman"].iloc[0])
        if not base_perm1730.empty
        else float("nan")
    )
    perm1730 = variant_summary[variant_summary["variant"].astype(str).eq("perm_seed1730")]
    valid_adapter = (
        float(perm1730["adapter_identity_gain_max_valid"].iloc[0])
        if not perm1730.empty
        else float("nan")
    )
    valid_event = (
        float(perm1730["event_identity_gain_max_valid"].iloc[0])
        if not perm1730.empty
        else float("nan")
    )
    random_strict = int(
        (random_summary["negative_control_signal"].astype(str) == "non_symmetric_strict_positive_perturbation").sum()
    )
    random_worsening = int(
        (random_summary["negative_control_signal"].astype(str) == "non_symmetric_search_worsening").sum()
    )
    return pd.DataFrame(
        [
            {
                "issue": "permutation_non_robust_adapter_alignment",
                "evidence": f"subset base-vs-perm_seed1730 mean adapted_mu_spearman={base_perm1730_mu:.3g}; perm_seed1730 is search-worse while base improves",
                "objective_change": "add variable-level permutation consistency on adapted mu/rho and adapter delta using metadata permutations",
                "priority": "high",
            },
            {
                "issue": "valid_invalid_orbit_mixing",
                "evidence": "subset repeat-level event/adaptor maxima are dominated by static_mu_not_collapsed rows; only one refined orbit is event-row-valid per variant",
                "objective_change": "compute reward/identity losses on valid event rows only and report invalid-orbit diagnostics separately",
                "priority": "high",
            },
            {
                "issue": "over_adaptation_magnitude_risk",
                "evidence": f"subset perm_seed1730 valid orbit has event_gain={valid_event:.3g}, adapter_gain={valid_adapter:.3g}, and search worsens in 3/3 repeats",
                "objective_change": "add adapter delta magnitude regularization or amplification cap, especially when one valid orbit dominates the delta",
                "priority": "medium",
            },
            {
                "issue": "non_symmetric_generic_perturbation",
                "evidence": f"random controls include {random_strict} non-symmetric strict-positive perturbation and {random_worsening} majority search-worsening controls",
                "objective_change": "add non-symmetric/no-valid-orbit negative guard that suppresses adapter deltas unless valid orbit-aligned identity evidence exists",
                "priority": "high",
            },
            {
                "issue": "gate_selector_not_ready",
                "evidence": "mechanism is not stable across permutations or controls; runtime positives include perturbation baselines",
                "objective_change": "keep gate/selector postponed until multiple symmetry families show stable aligned mechanism and controls stay bounded",
                "priority": "policy",
            },
        ]
    )


def write_doc(
    *,
    pair_summary: pd.DataFrame,
    variant_summary: pd.DataFrame,
    orbit_contrib: pd.DataFrame,
    overadaptation: pd.DataFrame,
    random_summary: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> None:
    DOC.parent.mkdir(parents=True, exist_ok=True)
    over_view = overadaptation[
        [
            "variant",
            "repeat_id",
            "orbit",
            "event_row_valid_reason",
            "valid_orbit",
            "search_worse",
            "event_identity_gain",
            "adapter_identity_gain",
            "adapter_to_event_gain_ratio",
            "adapted_mu_range",
            "static_mu_range",
            "primary_delta_final_decisions",
            "primary_delta_final_conflicts",
        ]
    ].copy()
    lines = [
        "# Adapter Objective and Robustness Diagnosis v2",
        "",
        "## Scope",
        "",
        "This is an offline objective-level diagnosis. It does not train, does not build",
        "a gate/selector, does not expand full runtime, and does not make a solver speedup",
        "claim. It reuses the current v2 runtime snapshot and targeted orbit/variable",
        "audits to ask whether the adapter uses event identity signal in a stable,",
        "permutation-robust, symmetry-specific way.",
        "",
        "## Permutation Robustness",
        "",
        *markdown_table(pair_summary),
        "",
        "`subset_cardinality_bw12::perm_seed1730` remains the key failure sample: the",
        "same base under another variable permutation has event/adapter signal, but the",
        "final decisions/conflicts move in the wrong direction. Static alignment is not",
        "enough; adapted mu/delta alignment is weak for the failing pair.",
        "",
        "## Subset Variant Summary",
        "",
        *markdown_table(variant_summary),
        "",
        "The repeat-level identity maxima mix valid and invalid orbit rows. For subset",
        "only one refined orbit is event-row-valid per variant; several larger",
        "`static_mu_not_collapsed` rows carry much larger event identity ranges and must",
        "not be used as positive identity training evidence.",
        "",
        "## Valid/Invalid Orbit Contribution",
        "",
        *markdown_table(orbit_contrib),
        "",
        "## Over-Adaptation Rows",
        "",
        *markdown_table(over_view, max_rows=30),
        "",
        "The failing `perm_seed1730` valid orbit shows a large adapter gain relative to",
        "its event gain and worsens search in all repeats. However `perm_seed1731` also",
        "has a large valid-orbit adapter gain while improving search, so magnitude alone",
        "does not explain the failure. The objective needs both permutation consistency",
        "and magnitude restraint.",
        "",
        "## Random Negative Control",
        "",
        *markdown_table(random_summary),
        "",
        "Random controls show that adapter/runtime changes can be generic perturbations.",
        "The current strict-positive random control is a perturbation baseline, not",
        "symmetry evidence. Non-symmetric controls should therefore constrain adapter",
        "delta unless valid orbit-aligned evidence exists.",
        "",
        "## Objective-Level Fixes",
        "",
        *markdown_table(recommendations),
        "",
        "## Decision",
        "",
        "- Do not proceed to gate/selector from this state.",
        "- Do not expand full runtime to chase surface positives.",
        "- Fix the objective side first: permutation consistency, valid-orbit masking,",
        "  non-symmetric negative guard, and adapter delta magnitude restraint.",
        "",
        "## Artifacts",
        "",
        f"- subset pair alignment: `{SUBSET_PAIR_ALIGNMENT_CSV}`",
        f"- subset pair summary: `{SUBSET_PAIR_SUMMARY_CSV}`",
        f"- subset variant summary: `{SUBSET_VARIANT_SUMMARY_CSV}`",
        f"- subset orbit contribution: `{SUBSET_ORBIT_CONTRIB_CSV}`",
        f"- over-adaptation orbits: `{OVERADAPTATION_ORBITS_CSV}`",
        f"- random control summary: `{RANDOM_CONTROL_SUMMARY_CSV}`",
        f"- objective recommendations: `{OBJECTIVE_RECOMMENDATIONS_CSV}`",
    ]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    data = load_inputs()
    subset_variables = data["subset_variables"]
    targeted_orbits = data["targeted_orbits"]
    targeted_repeat = data["targeted_repeat"]
    subset_orbits = targeted_orbits[targeted_orbits["base_instance_id"].astype(str).eq(SUBSET_BASE)].copy()
    subset_repeat = targeted_repeat[targeted_repeat["base_instance_id"].astype(str).eq(SUBSET_BASE)].copy()

    pair_alignment = build_subset_pair_alignment(subset_variables, subset_repeat, subset_orbits)
    pair_summary = build_pair_summary(pair_alignment)
    variant_summary = build_subset_variant_summary(subset_repeat, subset_orbits)
    orbit_contrib = build_subset_orbit_contrib(subset_orbits)
    overadaptation = build_overadaptation_orbits(subset_orbits)
    random_summary = build_random_control_summary(
        observations=data["positive_observations"],
        targeted_orbits=targeted_orbits,
        strict_orbits=data["strict_orbits"],
        base_summary=data["positive_base"],
    )
    recommendations = build_objective_recommendations(pair_summary, variant_summary, random_summary)

    outputs = [
        (SUBSET_PAIR_ALIGNMENT_CSV, pair_alignment),
        (SUBSET_PAIR_SUMMARY_CSV, pair_summary),
        (SUBSET_VARIANT_SUMMARY_CSV, variant_summary),
        (SUBSET_ORBIT_CONTRIB_CSV, orbit_contrib),
        (OVERADAPTATION_ORBITS_CSV, overadaptation),
        (RANDOM_CONTROL_SUMMARY_CSV, random_summary),
        (OBJECTIVE_RECOMMENDATIONS_CSV, recommendations),
    ]
    for path, frame in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
        print(f"wrote {path}")
    write_doc(
        pair_summary=pair_summary,
        variant_summary=variant_summary,
        orbit_contrib=orbit_contrib,
        overadaptation=overadaptation,
        random_summary=random_summary,
        recommendations=recommendations,
    )
    print(f"wrote {DOC}")


if __name__ == "__main__":
    main()
