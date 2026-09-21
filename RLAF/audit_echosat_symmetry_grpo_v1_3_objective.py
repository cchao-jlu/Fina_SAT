from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_iter15_targeted_acceptance_observations.csv"
DEFAULT_COMPONENTS = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_3_objective_components.csv"
DEFAULT_CANDIDATES = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_3_objective_candidate_scores.csv"
DEFAULT_CHECKS = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_3_objective_checks.csv"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_3_objective_audit.md"

ANCHOR_BASES = ["k9_color8", "php_p9_h8"]
HARD_RECOVERY_BASES = ["k10_color9", "php_p10_h9"]
SUBSET_FAILURE_BASE = "subset_cardinality_bw12"
SUBSET_FAILURE_VARIANT = "perm_seed1730"
MAIN_CANDIDATE = "v1_2_iter15"
CONTROL_CANDIDATES = ["v1_2_best", "v1_2_iter235", "v1_1_iter85"]
WC3_DIAGNOSTIC = "v1_2_iter50"


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values.fillna(False)
    return values.fillna(False).astype(str).str.lower().isin({"1", "true", "yes", "y"})


def numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=np.float64)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(np.float64)


def finite_mean(values: pd.Series, default: float = 0.0) -> float:
    if values.empty:
        return default
    value = pd.to_numeric(values, errors="coerce").mean()
    return float(value) if pd.notna(value) and math.isfinite(float(value)) else default


def finite_min(values: list[float], default: float = 0.0) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return min(finite) if finite else default


def base_frac(group: pd.DataFrame, base_id: str, column: str = "v13_search_ok") -> float:
    rows = group[group["base_instance_id"].astype(str).eq(str(base_id))]
    return finite_mean(rows[column]) if not rows.empty else math.nan


def variant_frac(group: pd.DataFrame, base_id: str, variant: str, column: str = "v13_search_ok") -> float:
    rows = group[
        group["base_instance_id"].astype(str).eq(str(base_id))
        & group["variant"].astype(str).eq(str(variant))
    ]
    return finite_mean(rows[column]) if not rows.empty else math.nan


def load_observations(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    required = [
        "candidate_label",
        "candidate_name",
        "candidate_role",
        "warmup_conflicts",
        "repeat_id",
        "base_instance_id",
        "variant",
        "family",
        "control_type",
        "symmetry_strength",
        "cached_trace_no_adapter_final_final_decisions",
        "cached_trace_no_adapter_final_final_conflicts",
        "cached_trace_no_adapter_final_final_cpu_time",
        "adapter_cached_decisions_delta",
        "adapter_cached_conflicts_delta",
        "adapter_cached_final_cpu_delta",
    ]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    if "source_csv" in frame.columns:
        bad = frame["source_csv"].astype(str).str.contains("weighted_no_pre", case=False, na=False)
        if bool(bad.any()):
            raise ValueError(f"{path} includes weighted_no_pre source rows")
    return frame


def add_v13_components(frame: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    out = frame.copy()
    decision_delta = numeric(out, "adapter_cached_decisions_delta")
    conflict_delta = numeric(out, "adapter_cached_conflicts_delta")
    cpu_delta = numeric(out, "adapter_cached_final_cpu_delta")
    cached_decisions = numeric(out, "cached_trace_no_adapter_final_final_decisions", 1.0).clip(lower=1.0)
    cached_conflicts = numeric(out, "cached_trace_no_adapter_final_final_conflicts", 1.0).clip(lower=1.0)
    cached_cpu = numeric(out, "cached_trace_no_adapter_final_final_cpu_time", 1.0).clip(lower=1.0e-3)

    decision_reduction = (-decision_delta / cached_decisions).clip(-args.reduction_clip, args.reduction_clip)
    conflict_reduction = (-conflict_delta / cached_conflicts).clip(-args.reduction_clip, args.reduction_clip)
    cpu_reduction = (-cpu_delta / cached_cpu).clip(-args.cpu_clip, args.cpu_clip)
    search_ok = (decision_delta < -args.eps_decisions) & (conflict_delta < -args.eps_conflicts)
    search_blowup = (decision_delta > args.eps_decisions) | (conflict_delta > args.eps_conflicts)

    random_control = (
        out["family"].astype(str).eq("random_3sat_control")
        | out["control_type"].astype(str).eq("non_symmetric_control")
    )
    strong = out["symmetry_strength"].astype(str).eq("strong")
    weak = out["symmetry_strength"].astype(str).eq("weak")
    e_sym = np.where(strong, 1.0, np.where(weak, 0.6, 0.35)).astype(np.float64)
    e_sym = np.where(random_control.to_numpy(dtype=bool), 0.0, e_sym)
    has_event = (numeric(out, "event_state_l2_sum") > 0.0) | (numeric(out, "event_state_nonzero_vars") > 0.0)
    e_sym = np.where(has_event.to_numpy(dtype=bool), e_sym, 0.0)

    final_cap = numeric(out, "final_cpu_lim", 10.0).replace(0.0, 10.0)
    near_cap = (
        pd.concat(
            [
                numeric(out, "plain_unguided_glucose_final_cpu_time"),
                numeric(out, "neutral_weighted_glucose_final_cpu_time"),
                numeric(out, "static_weighted_glucose_final_cpu_time"),
                numeric(out, "cached_trace_no_adapter_final_final_cpu_time"),
                numeric(out, "event_adapter_final_final_cpu_time"),
            ],
            axis=1,
        ).max(axis=1)
        >= float(args.near_cap_fraction) * final_cap
    )
    plain_cpu = numeric(out, "plain_unguided_glucose_final_cpu_time", 1.0).clip(lower=1.0e-3)
    neutral_cpu = numeric(out, "neutral_weighted_glucose_final_cpu_time")
    static_cpu = numeric(out, "static_weighted_glucose_final_cpu_time")
    weighted_path_risk = (
        ((neutral_cpu - plain_cpu) / plain_cpu).clip(lower=0.0)
        + ((static_cpu - neutral_cpu) / neutral_cpu.clip(lower=1.0e-3)).clip(lower=0.0)
    )

    r_decisions = args.decisions_weight * decision_reduction.clip(lower=0.0)
    r_conflicts = args.conflicts_weight * conflict_reduction.clip(lower=0.0)
    r_cpu = args.cpu_weight * cpu_reduction.clip(lower=0.0)
    search_blowup_penalty = (
        args.decision_blowup_penalty_weight * (decision_delta.clip(lower=0.0) / cached_decisions).clip(0.0, args.reduction_clip)
        + args.conflict_blowup_penalty_weight * (conflict_delta.clip(lower=0.0) / cached_conflicts).clip(0.0, args.reduction_clip)
    )

    base = out["base_instance_id"].astype(str)
    variant = out["variant"].astype(str)
    anchor_mask = base.isin(ANCHOR_BASES)
    hard_recovery_mask = base.isin(HARD_RECOVERY_BASES)
    subset_failure_mask = base.eq(SUBSET_FAILURE_BASE) & variant.eq(SUBSET_FAILURE_VARIANT)

    positive_allowed = (
        search_ok.to_numpy(dtype=bool)
        & (~random_control.to_numpy(dtype=bool))
        & (~subset_failure_mask.to_numpy(dtype=bool))
        & (e_sym > 0.0)
        & (~near_cap.to_numpy(dtype=bool))
        & (weighted_path_risk.to_numpy(dtype=np.float64) <= float(args.weighted_risk_positive_threshold))
    )
    positive_symmetry_reward = positive_allowed.astype(np.float64) * e_sym * (
        r_decisions.to_numpy(dtype=np.float64)
        + r_conflicts.to_numpy(dtype=np.float64)
        + r_cpu.to_numpy(dtype=np.float64)
    )

    random_control_penalty = random_control.astype(np.float64) * np.maximum(
        search_blowup_penalty.to_numpy(dtype=np.float64) + positive_symmetry_reward,
        np.abs(decision_reduction.to_numpy(dtype=np.float64))
        + np.abs(conflict_reduction.to_numpy(dtype=np.float64))
        + np.abs(cpu_reduction.to_numpy(dtype=np.float64)),
    )
    hard_negative_penalty = hard_recovery_mask.astype(np.float64) * search_blowup.astype(np.float64) * (
        search_blowup_penalty.to_numpy(dtype=np.float64)
        + np.abs(decision_reduction.to_numpy(dtype=np.float64))
        + np.abs(conflict_reduction.to_numpy(dtype=np.float64))
    )
    subset_failure_penalty = subset_failure_mask.astype(np.float64) * search_ok.astype(np.float64) * (
        r_decisions.to_numpy(dtype=np.float64)
        + r_conflicts.to_numpy(dtype=np.float64)
        + search_blowup_penalty.to_numpy(dtype=np.float64)
        + 1.0
    )
    anchor_failure_penalty = anchor_mask.astype(np.float64) * (~search_ok).astype(np.float64) * (
        search_blowup_penalty.to_numpy(dtype=np.float64)
        + np.maximum(0.0, -decision_reduction.to_numpy(dtype=np.float64))
        + np.maximum(0.0, -conflict_reduction.to_numpy(dtype=np.float64))
        + 0.25
    )
    weighted_path_risk_penalty = weighted_path_risk.to_numpy(dtype=np.float64)
    near_cap_penalty = near_cap.astype(np.float64) * (
        r_decisions.to_numpy(dtype=np.float64)
        + r_conflicts.to_numpy(dtype=np.float64)
        + search_blowup_penalty.to_numpy(dtype=np.float64)
    )
    final_reward = (
        positive_symmetry_reward
        - search_blowup_penalty.to_numpy(dtype=np.float64)
        - args.random_control_penalty_weight * random_control_penalty.to_numpy(dtype=np.float64)
        - args.hard_negative_penalty_weight * hard_negative_penalty.to_numpy(dtype=np.float64)
        - args.subset_failure_penalty_weight * subset_failure_penalty.to_numpy(dtype=np.float64)
        - args.anchor_failure_penalty_weight * anchor_failure_penalty.to_numpy(dtype=np.float64)
        - args.weighted_risk_penalty_weight * weighted_path_risk_penalty
        - args.near_cap_penalty_weight * near_cap_penalty.to_numpy(dtype=np.float64)
    )

    out["v13_decision_reduction"] = decision_reduction
    out["v13_conflict_reduction"] = conflict_reduction
    out["v13_cpu_reduction"] = cpu_reduction
    out["v13_search_ok"] = search_ok
    out["v13_search_blowup"] = search_blowup
    out["v13_random_control"] = random_control
    out["v13_e_sym"] = e_sym
    out["v13_near_cap"] = near_cap
    out["v13_weighted_path_risk"] = weighted_path_risk
    out["v13_r_search_decisions"] = r_decisions
    out["v13_r_search_conflicts"] = r_conflicts
    out["v13_r_cpu_clipped"] = r_cpu
    out["v13_positive_allowed"] = positive_allowed
    out["v13_positive_symmetry_reward"] = positive_symmetry_reward
    out["v13_search_blowup_penalty"] = search_blowup_penalty
    out["v13_random_control_penalty"] = random_control_penalty
    out["v13_hard_negative_penalty"] = hard_negative_penalty
    out["v13_subset_failure_penalty"] = subset_failure_penalty
    out["v13_anchor_failure_penalty"] = anchor_failure_penalty
    out["v13_weighted_path_risk_penalty"] = weighted_path_risk_penalty
    out["v13_near_cap_penalty"] = near_cap_penalty
    out["v13_final_reward"] = final_reward
    out["v13_final_cost"] = -final_reward
    return out


def candidate_score(components: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, name, role), candidate_rows in components.groupby(
        ["candidate_label", "candidate_name", "candidate_role"],
        sort=True,
        dropna=False,
    ):
        by_warmup: dict[int, pd.DataFrame] = {
            int(warmup): group.copy()
            for warmup, group in candidate_rows.groupby("warmup_conflicts", sort=True, dropna=False)
        }
        wc1 = by_warmup.get(1, pd.DataFrame())
        if wc1.empty:
            raise ValueError(f"{candidate} has no wc1 rows")

        anchor_values = [base_frac(wc1, base) for base in ANCHOR_BASES]
        hard_values = [base_frac(wc1, base) for base in HARD_RECOVERY_BASES]
        anchor_min = finite_min(anchor_values)
        hard_min = finite_min(hard_values)
        strong_wc1 = finite_mean(wc1.loc[wc1["symmetry_strength"].astype(str).eq("strong"), "v13_search_ok"])
        random_wc1 = finite_mean(wc1.loc[bool_series(wc1["v13_random_control"]), "v13_search_ok"])
        subset_wc1 = variant_frac(wc1, SUBSET_FAILURE_BASE, SUBSET_FAILURE_VARIANT)
        blowup_wc1 = finite_mean(wc1["v13_search_blowup"])

        primary_score = (
            args.primary_anchor_weight * anchor_min
            + args.primary_hard_recovery_weight * hard_min
            + args.primary_strong_symmetry_weight * strong_wc1
            - args.primary_random_control_penalty_weight * random_wc1
            - args.primary_subset_failure_penalty_weight * (subset_wc1 if math.isfinite(subset_wc1) else 0.0)
            - args.primary_search_blowup_penalty_weight * blowup_wc1
        )

        diagnostic_score = 0.0
        consistency_penalty = 0.0
        warmup_metrics: dict[str, float] = {}
        for warmup, weight in [(3, args.wc3_diagnostic_weight), (5, args.wc5_diagnostic_weight)]:
            group = by_warmup.get(warmup, pd.DataFrame())
            if group.empty:
                continue
            anchor_diag = finite_min([base_frac(group, base) for base in ANCHOR_BASES])
            hard_diag = finite_min([base_frac(group, base) for base in HARD_RECOVERY_BASES])
            strong_diag = finite_mean(group.loc[group["symmetry_strength"].astype(str).eq("strong"), "v13_search_ok"])
            random_diag = finite_mean(group.loc[bool_series(group["v13_random_control"]), "v13_search_ok"])
            subset_diag = variant_frac(group, SUBSET_FAILURE_BASE, SUBSET_FAILURE_VARIANT)
            blowup_diag = finite_mean(group["v13_search_blowup"])
            diagnostic_score += weight * (
                args.diagnostic_anchor_weight * anchor_diag
                + args.diagnostic_strong_symmetry_weight * strong_diag
                - args.diagnostic_random_control_penalty_weight * random_diag
                - args.diagnostic_subset_failure_penalty_weight * (subset_diag if math.isfinite(subset_diag) else 0.0)
                - args.diagnostic_search_blowup_penalty_weight * blowup_diag
            )
            consistency_penalty += weight * (
                max(0.0, anchor_min - anchor_diag)
                + max(0.0, hard_min - hard_diag)
                + max(0.0, strong_wc1 - strong_diag)
                + max(0.0, random_diag - random_wc1)
                + max(0.0, (subset_diag if math.isfinite(subset_diag) else 0.0) - (subset_wc1 if math.isfinite(subset_wc1) else 0.0))
            )
            warmup_metrics[f"wc{warmup}_anchor_min_search_ok_frac"] = anchor_diag
            warmup_metrics[f"wc{warmup}_hard_recovery_min_search_ok_frac"] = hard_diag
            warmup_metrics[f"wc{warmup}_strong_symmetry_search_ok_frac"] = strong_diag
            warmup_metrics[f"wc{warmup}_random_control_search_ok_frac"] = random_diag
            warmup_metrics[f"wc{warmup}_subset_failure_search_ok_frac"] = subset_diag
            warmup_metrics[f"wc{warmup}_search_blowup_frac"] = blowup_diag

        reward_mean = finite_mean(wc1["v13_final_reward"])
        positive_reward_rows = float((wc1["v13_final_reward"] > 0.0).mean())
        score = primary_score + diagnostic_score - args.consistency_penalty_weight * consistency_penalty
        known = bool_series(wc1["known_expected_result"]) if "known_expected_result" in wc1.columns else pd.Series(False, index=wc1.index)
        matched = bool_series(wc1["event_adapter_final_known_expected_match"]) if "event_adapter_final_known_expected_match" in wc1.columns else pd.Series(True, index=wc1.index)
        rows.append(
            {
                "candidate_label": candidate,
                "candidate_name": name,
                "candidate_role": role,
                "v13_candidate_score": float(score),
                "primary_wc1_score": float(primary_score),
                "diagnostic_score": float(diagnostic_score),
                "warmup_consistency_penalty": float(consistency_penalty),
                "wc1_anchor_min_search_ok_frac": float(anchor_min),
                "wc1_hard_recovery_min_search_ok_frac": float(hard_min),
                "wc1_strong_symmetry_search_ok_frac": float(strong_wc1),
                "wc1_random_control_search_ok_frac": float(random_wc1),
                "wc1_subset_failure_search_ok_frac": float(subset_wc1 if math.isfinite(subset_wc1) else 0.0),
                "wc1_search_blowup_frac": float(blowup_wc1),
                "wc1_final_reward_mean": float(reward_mean),
                "wc1_positive_reward_row_frac": float(positive_reward_rows),
                "known_expected_rows_wc1": int(known.sum()),
                "known_expected_match_rows_wc1": int(matched[known].sum()) if bool(known.any()) else 0,
                "known_expected_all_match_wc1": bool(matched[known].all()) if bool(known.any()) else True,
                **warmup_metrics,
            }
        )
    return pd.DataFrame(rows).sort_values("v13_candidate_score", ascending=False).reset_index(drop=True)


def build_checks(scores: pd.DataFrame, components: pd.DataFrame, random_threshold: float) -> pd.DataFrame:
    lookup = scores.set_index("candidate_label")
    if MAIN_CANDIDATE not in lookup.index:
        raise ValueError(f"missing main candidate {MAIN_CANDIDATE}")
    main = lookup.loc[MAIN_CANDIDATE]
    checks: dict[str, bool] = {
        "main_candidate_is_top_v13_score": str(scores.iloc[0]["candidate_label"]) == MAIN_CANDIDATE,
        "main_candidate_beats_v1_2_best": float(main["v13_candidate_score"]) > float(lookup.loc["v1_2_best", "v13_candidate_score"]),
        "main_candidate_beats_v1_2_iter235": float(main["v13_candidate_score"]) > float(lookup.loc["v1_2_iter235", "v13_candidate_score"]),
        "main_candidate_wc1_anchor_min_is_1": float(main["wc1_anchor_min_search_ok_frac"]) >= 1.0,
        "main_candidate_wc1_hard_recovery_at_least_2_of_3": float(main["wc1_hard_recovery_min_search_ok_frac"]) >= (2.0 / 3.0),
        "main_candidate_wc1_random_control_near_zero": float(main["wc1_random_control_search_ok_frac"]) <= float(random_threshold),
        "main_candidate_wc1_subset_failure_zero": float(main["wc1_subset_failure_search_ok_frac"]) <= 0.0,
        "main_candidate_known_expected_all_match_wc1": bool(main["known_expected_all_match_wc1"]),
    }
    random_rows = components[
        components["candidate_label"].astype(str).eq(MAIN_CANDIDATE)
        & bool_series(components["v13_random_control"])
    ]
    checks["main_candidate_random_controls_positive_reward_zero"] = bool((numeric(random_rows, "v13_positive_symmetry_reward") <= 0.0).all())
    subset_rows = components[
        components["candidate_label"].astype(str).eq(MAIN_CANDIDATE)
        & components["base_instance_id"].astype(str).eq(SUBSET_FAILURE_BASE)
        & components["variant"].astype(str).eq(SUBSET_FAILURE_VARIANT)
    ]
    checks["subset_failure_has_no_positive_reward"] = bool((numeric(subset_rows, "v13_positive_symmetry_reward") <= 0.0).all())
    out = pd.DataFrame([{"check": name, "passed": bool(value)} for name, value in checks.items()])
    out.loc[len(out)] = {"check": "V13_OBJECTIVE_AUDIT_PASS", "passed": bool(all(checks.values()))}
    return out


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows)
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells: list[str] = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                cells.append(f"{value:.6g}" if math.isfinite(value) else "nan")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(
    path: Path,
    *,
    observations: pd.DataFrame,
    components: pd.DataFrame,
    scores: pd.DataFrame,
    checks: pd.DataFrame,
    outputs: dict[str, Path],
) -> None:
    pass_row = checks.loc[checks["check"].eq("V13_OBJECTIVE_AUDIT_PASS"), "passed"]
    audit_pass = bool(pass_row.iloc[0]) if not pass_row.empty else False
    component_cols = [
        "candidate_label",
        "warmup_conflicts",
        "base_instance_id",
        "variant",
        "repeat_id",
        "v13_search_ok",
        "v13_search_blowup",
        "v13_positive_symmetry_reward",
        "v13_search_blowup_penalty",
        "v13_random_control_penalty",
        "v13_hard_negative_penalty",
        "v13_subset_failure_penalty",
        "v13_anchor_failure_penalty",
        "v13_final_reward",
    ]
    focus = components[
        components["base_instance_id"].astype(str).isin(ANCHOR_BASES + HARD_RECOVERY_BASES + [SUBSET_FAILURE_BASE])
        & components["candidate_label"].astype(str).eq(MAIN_CANDIDATE)
    ].sort_values(["warmup_conflicts", "base_instance_id", "variant", "repeat_id"])
    random_focus = components[
        components["candidate_label"].astype(str).eq(MAIN_CANDIDATE)
        & bool_series(components["v13_random_control"])
    ].groupby(["warmup_conflicts"], sort=True).agg(
        rows=("instance_id", "size"),
        search_ok_frac=("v13_search_ok", "mean"),
        positive_symmetry_reward_sum=("v13_positive_symmetry_reward", "sum"),
        final_reward_mean=("v13_final_reward", "mean"),
    ).reset_index()

    lines = [
        "# EchoSAT Symmetry GRPO v1.3 Objective Audit",
        "",
        "This is an offline objective audit over the existing iter=15 targeted acceptance table. It does not train, rerun solver protocols, expand benchmarks, or add a gate/selector.",
        "",
        "## Artifacts",
        "",
        *[f"- {name}: `{display_path(output)}`" for name, output in outputs.items()],
        "",
        "## Scope",
        "",
        f"- observation rows: `{len(observations)}`",
        f"- component rows: `{len(components)}`",
        "- primary budget: `wc1`",
        "- diagnostic budgets: `wc3`, `wc5`",
        "- success metric: evidence-gated adapter-vs-cached decisions/conflicts reduction.",
        "- CPU and adapter-vs-plain protocol time remain diagnostics, not objective success.",
        "",
        "## Audit Result",
        "",
        f"- v1.3 offline objective audit: `{'PASS' if audit_pass else 'FAIL'}`",
        "",
        *markdown_table(checks, max_rows=30),
        "",
        "## Candidate Scores",
        "",
        *markdown_table(
            scores[
                [
                    "candidate_label",
                    "candidate_role",
                    "v13_candidate_score",
                    "primary_wc1_score",
                    "diagnostic_score",
                    "warmup_consistency_penalty",
                    "wc1_anchor_min_search_ok_frac",
                    "wc1_hard_recovery_min_search_ok_frac",
                    "wc1_random_control_search_ok_frac",
                    "wc1_subset_failure_search_ok_frac",
                    "wc1_search_blowup_frac",
                ]
            ],
            max_rows=20,
        ),
        "",
        "## Main Candidate Focus Rows",
        "",
        *markdown_table(focus[component_cols], max_rows=80),
        "",
        "## Main Candidate Random Controls",
        "",
        *markdown_table(random_focus, max_rows=20),
        "",
        "## Interpretation",
        "",
        "- `v1_2_iter15` remains the v1.3 continuation seed under the offline strict objective.",
        "- Random controls receive zero positive symmetry reward; any random-control improvement is treated as robustness/control behavior, not symmetry evidence.",
        "- `wc3` and `wc5` are used only as consistency diagnostics in this audit. Training-time best checkpointing remains a wc1 strict search-work validation metric unless a separate multi-budget validation protocol is run after training.",
        "- No solver speedup claim follows from this audit.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit EchoSAT Symmetry GRPO v1.3 objective on existing targeted acceptance rows.")
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--components-csv", type=Path, default=DEFAULT_COMPONENTS)
    parser.add_argument("--candidate-scores-csv", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--checks-csv", type=Path, default=DEFAULT_CHECKS)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--random-threshold", type=float, default=0.05)
    parser.add_argument("--eps-decisions", type=float, default=0.0)
    parser.add_argument("--eps-conflicts", type=float, default=0.0)
    parser.add_argument("--reduction-clip", type=float, default=1.0)
    parser.add_argument("--cpu-clip", type=float, default=0.05)
    parser.add_argument("--near-cap-fraction", type=float, default=0.8)
    parser.add_argument("--weighted-risk-positive-threshold", type=float, default=0.0)
    parser.add_argument("--decisions-weight", type=float, default=0.55)
    parser.add_argument("--conflicts-weight", type=float, default=0.45)
    parser.add_argument("--cpu-weight", type=float, default=0.0)
    parser.add_argument("--decision-blowup-penalty-weight", type=float, default=2.5)
    parser.add_argument("--conflict-blowup-penalty-weight", type=float, default=2.5)
    parser.add_argument("--random-control-penalty-weight", type=float, default=5.0)
    parser.add_argument("--hard-negative-penalty-weight", type=float, default=3.0)
    parser.add_argument("--subset-failure-penalty-weight", type=float, default=3.0)
    parser.add_argument("--anchor-failure-penalty-weight", type=float, default=2.0)
    parser.add_argument("--weighted-risk-penalty-weight", type=float, default=1.25)
    parser.add_argument("--near-cap-penalty-weight", type=float, default=1.0)
    parser.add_argument("--primary-anchor-weight", type=float, default=4.0)
    parser.add_argument("--primary-hard-recovery-weight", type=float, default=3.0)
    parser.add_argument("--primary-strong-symmetry-weight", type=float, default=1.0)
    parser.add_argument("--primary-random-control-penalty-weight", type=float, default=3.0)
    parser.add_argument("--primary-subset-failure-penalty-weight", type=float, default=2.0)
    parser.add_argument("--primary-search-blowup-penalty-weight", type=float, default=1.5)
    parser.add_argument("--wc3-diagnostic-weight", type=float, default=0.2)
    parser.add_argument("--wc5-diagnostic-weight", type=float, default=0.1)
    parser.add_argument("--diagnostic-anchor-weight", type=float, default=0.5)
    parser.add_argument("--diagnostic-strong-symmetry-weight", type=float, default=0.25)
    parser.add_argument("--diagnostic-random-control-penalty-weight", type=float, default=2.0)
    parser.add_argument("--diagnostic-subset-failure-penalty-weight", type=float, default=0.5)
    parser.add_argument("--diagnostic-search-blowup-penalty-weight", type=float, default=0.5)
    parser.add_argument("--consistency-penalty-weight", type=float, default=0.4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    observations = load_observations(args.observations)
    components = add_v13_components(observations, args)
    scores = candidate_score(components, args)
    checks = build_checks(scores, components, random_threshold=float(args.random_threshold))

    outputs = {
        "components": args.components_csv,
        "candidate scores": args.candidate_scores_csv,
        "checks": args.checks_csv,
        "report": args.doc,
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    components.to_csv(args.components_csv, index=False)
    scores.to_csv(args.candidate_scores_csv, index=False)
    checks.to_csv(args.checks_csv, index=False)
    write_doc(
        args.doc,
        observations=observations,
        components=components,
        scores=scores,
        checks=checks,
        outputs=outputs,
    )
    print(f"wrote {args.components_csv}")
    print(f"wrote {args.candidate_scores_csv}")
    print(f"wrote {args.checks_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
