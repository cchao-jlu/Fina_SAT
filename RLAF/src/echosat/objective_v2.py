from __future__ import annotations

from numbers import Real

import numpy as np
import pandas as pd


def _require_columns(frame: pd.DataFrame, columns: set[str], context: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{context} missing required columns: {missing}")


def _require_unique_index(frame: pd.DataFrame, context: str) -> None:
    if not frame.index.is_unique:
        raise ValueError(f"{context} requires a unique index")


def _require_string_grouping_keys(frame: pd.DataFrame, context: str) -> None:
    valid_base = frame["base_instance_id"].map(
        lambda value: isinstance(value, (str, np.str_)) and value.strip() != ""
    )
    valid_variant = frame["variant"].map(
        lambda value: isinstance(value, (str, np.str_)) and value.strip() != ""
    )
    if not bool((valid_base & valid_variant).all()):
        raise ValueError(
            f"{context} requires nonempty string base_instance_id and variant values"
        )


def _finite_parameter(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite numeric value")
    numeric = float(value)
    if not np.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _finite_numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    if column not in frame.columns:
        return np.full(len(frame), default, dtype=np.float64), np.zeros(len(frame), dtype=bool)
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=np.float64)
    valid = np.isfinite(values)
    return np.where(valid, values, default), valid


def worst_variant_scores(frame: pd.DataFrame, score_column: str = "search_score") -> pd.Series:
    _require_columns(frame, {"base_instance_id", "variant", score_column}, "worst_variant_scores")
    _require_unique_index(frame, "worst_variant_scores")
    if frame.empty:
        result = pd.Series(index=frame.index, dtype=np.float64, name="worst_variant_score")
        result.attrs["invalid_score_count"] = 0
        result.attrs["invalid_score_indices"] = []
        return result

    _require_string_grouping_keys(frame, "worst_variant_scores")
    base = frame["base_instance_id"]
    variant = frame["variant"]

    raw = pd.to_numeric(frame[score_column], errors="coerce").to_numpy(dtype=np.float64)
    finite = np.isfinite(raw)
    conservative = min(0.0, float(raw[finite].min())) if finite.any() else 0.0
    validated = np.where(finite, raw, conservative)
    grouped = pd.DataFrame(
        {
            "base_instance_id": base.to_numpy(),
            "variant": variant.to_numpy(),
            "score": validated,
        },
        index=frame.index,
    )
    variant_scores = grouped.groupby(["base_instance_id", "variant"], sort=False)["score"].mean()
    base_worst = variant_scores.groupby(level="base_instance_id", sort=False).min()
    result = grouped["base_instance_id"].map(base_worst).astype(np.float64)
    result.name = "worst_variant_score"
    result.attrs["invalid_score_count"] = int((~finite).sum())
    result.attrs["invalid_score_indices"] = frame.index[~finite].tolist()
    return result


def attach_masked_grpo_advantage(
    frame: pd.DataFrame,
    *,
    target_column: str = "echosat_cost",
    eligible_column: str = "v2_positive_eligible",
    blocked_penalty_column: str = "v2_blocked_penalty",
    weight_column: str = "echosat_advantage_weight",
) -> pd.DataFrame:
    required = {"cnf_id", target_column, blocked_penalty_column}
    _require_columns(frame, required, "attach_masked_grpo_advantage")
    _require_unique_index(frame, "attach_masked_grpo_advantage")
    if "sample_id" in frame.columns and frame.duplicated(["cnf_id", "sample_id"]).any():
        raise ValueError("attach_masked_grpo_advantage found duplicate cnf_id/sample_id rows")

    out = frame.copy()
    target_raw = pd.to_numeric(out[target_column], errors="coerce").to_numpy(dtype=np.float64)
    target_finite = np.isfinite(target_raw)
    target = np.where(target_finite, target_raw, 0.0)
    eligibility_values = (
        out[eligible_column].to_numpy(dtype=object)
        if eligible_column in out.columns
        else np.full(len(out), None, dtype=object)
    )
    valid_eligibility = np.fromiter(
        (isinstance(value, (bool, np.bool_)) for value in eligibility_values),
        dtype=bool,
        count=len(out),
    )
    declared_eligible = np.fromiter(
        (bool(value) if valid else False for value, valid in zip(eligibility_values, valid_eligibility)),
        dtype=bool,
        count=len(out),
    )
    eligible = declared_eligible & target_finite

    penalty_raw = pd.to_numeric(out[blocked_penalty_column], errors="coerce").to_numpy(dtype=np.float64)
    penalty = np.where(np.isfinite(penalty_raw), np.maximum(penalty_raw, 0.0), 1.0)
    penalty[~target_finite] = np.maximum(penalty[~target_finite], 1.0)

    group_mean = np.zeros(len(out), dtype=np.float64)
    group_std = np.zeros(len(out), dtype=np.float64)
    raw_unclamped = np.zeros(len(out), dtype=np.float64)
    cnf_ids = out["cnf_id"].to_numpy()
    for cnf_id in pd.unique(cnf_ids):
        group_positions = np.flatnonzero(cnf_ids == cnf_id)
        eligible_positions = group_positions[eligible[group_positions]]
        if eligible_positions.size == 0:
            continue
        values = target[eligible_positions]
        mean = float(values.mean())
        std = float(values.std(ddof=1)) if eligible_positions.size > 1 else 0.0
        group_mean[eligible_positions] = mean
        group_std[eligible_positions] = std
        if std > 1.0e-8:
            raw_unclamped[eligible_positions] = -((values - mean) / std)

    raw_unclamped[~eligible] = -penalty[~eligible]
    raw_advantage = np.nan_to_num(raw_unclamped, nan=0.0, posinf=0.0, neginf=0.0)
    if weight_column in out.columns:
        weight_raw = pd.to_numeric(out[weight_column], errors="coerce").to_numpy(dtype=np.float64)
        weight = np.where(np.isfinite(weight_raw), np.maximum(weight_raw, 0.0), 0.0)
    else:
        weight = np.ones(len(out), dtype=np.float64)
    weighted = raw_advantage * weight
    final = np.nan_to_num(weighted, nan=0.0, posinf=0.0, neginf=0.0)
    final[~eligible] = np.minimum(final[~eligible], 0.0)

    out[target_column] = target
    out[eligible_column] = eligible
    out["v2_invalid_eligibility"] = ~valid_eligibility
    out.attrs["invalid_eligibility_count"] = int((~valid_eligibility).sum())
    out[blocked_penalty_column] = penalty
    out["grpo_target_value"] = target
    out["grpo_group_mean_cost"] = group_mean
    out["grpo_group_std_cost"] = group_std
    out["grpo_raw_advantage_unclamped"] = raw_unclamped
    out["grpo_raw_advantage"] = raw_advantage
    out["grpo_weighted_advantage_before_clamp"] = weighted
    out["grpo_final_advantage"] = final
    out["grpo_positive_raw_advantage_clamped"] = (~eligible) & (raw_unclamped > 0.0)
    out["grpo_positive_advantage_clamped"] = (~eligible) & (weighted > 0.0)
    out["advantage"] = final
    return out


def build_symmetry_grpo_v2_target(
    guided_stats: pd.DataFrame,
    plain_stats: pd.DataFrame | None,
    static_stats: pd.DataFrame | None,
    *,
    cpu_cap: float,
    near_cap_fraction: float = 0.8,
    weighted_risk_threshold: float = 0.0,
    eps_decisions: float = 0.0,
    eps_conflicts: float = 0.0,
) -> pd.DataFrame:
    cpu_cap_value = _finite_parameter(cpu_cap, "cpu_cap")
    near_cap_value = _finite_parameter(near_cap_fraction, "near_cap_fraction")
    risk_threshold_value = _finite_parameter(
        weighted_risk_threshold, "weighted_risk_threshold"
    )
    decisions_epsilon = _finite_parameter(eps_decisions, "eps_decisions")
    conflicts_epsilon = _finite_parameter(eps_conflicts, "eps_conflicts")
    if cpu_cap_value <= 0.0:
        raise ValueError("cpu_cap must be greater than zero")
    if not 0.0 < near_cap_value <= 1.0:
        raise ValueError("near_cap_fraction must be within (0, 1]")
    if decisions_epsilon < 0.0:
        raise ValueError("eps_decisions must be nonnegative")
    if conflicts_epsilon < 0.0:
        raise ValueError("eps_conflicts must be nonnegative")

    required = {
        "cnf_id",
        "sample_id",
        "base_instance_id",
        "variant",
        "Result",
        "CPU time",
        "decisions",
        "conflicts",
    }
    _require_columns(guided_stats, required, "build_symmetry_grpo_v2_target")
    _require_unique_index(guided_stats, "build_symmetry_grpo_v2_target")
    if guided_stats.duplicated(["cnf_id", "sample_id"]).any():
        raise ValueError("build_symmetry_grpo_v2_target found duplicate guided cnf_id/sample_id rows")

    out = guided_stats.copy()
    _require_string_grouping_keys(out, "build_symmetry_grpo_v2_target")
    baseline_columns = ["cnf_id", "sample_id", "Result", "CPU time", "decisions", "conflicts"]

    def baseline_frame(frame: pd.DataFrame | None, name: str) -> pd.DataFrame:
        if frame is None or frame.empty:
            baseline = pd.DataFrame(columns=baseline_columns)
        else:
            missing = [column for column in baseline_columns if column not in frame.columns]
            if missing:
                raise ValueError(f"{name} missing required columns: {missing}")
            baseline = frame[baseline_columns].copy()
            if baseline.duplicated(["cnf_id", "sample_id"]).any():
                raise ValueError(
                    f"build_symmetry_grpo_v2_target found duplicate {name} cnf_id/sample_id rows"
                )
        baseline[f"_{name}_present"] = True
        return baseline.rename(
            columns={
                "Result": f"{name}_Result",
                "CPU time": f"{name}_CPU_time",
                "decisions": f"{name}_decisions",
                "conflicts": f"{name}_conflicts",
            }
        )

    def static_baseline_frame(frame: pd.DataFrame | None) -> pd.DataFrame:
        metric_columns = ["Result", "CPU time", "decisions", "conflicts"]
        if frame is None or frame.empty:
            baseline = pd.DataFrame(columns=["cnf_id", *metric_columns])
        else:
            missing = [column for column in baseline_columns if column not in frame.columns]
            if missing:
                raise ValueError(f"static missing required columns: {missing}")
            baseline = frame[["cnf_id", *metric_columns]].drop_duplicates().copy()
            counts = baseline.groupby("cnf_id", dropna=False, sort=False).size()
            conflicting = counts[counts > 1]
            if not conflicting.empty:
                cnf_id = conflicting.index[0]
                raise ValueError(
                    "build_symmetry_grpo_v2_target found conflicting static baseline "
                    f"rows for cnf_id={cnf_id}"
                )
            baseline = baseline.drop_duplicates("cnf_id", keep="first")
        baseline["_static_present"] = True
        return baseline.rename(
            columns={
                "Result": "static_Result",
                "CPU time": "static_CPU_time",
                "decisions": "static_decisions",
                "conflicts": "static_conflicts",
            }
        )

    plain = baseline_frame(plain_stats, "plain")
    static = static_baseline_frame(static_stats)
    out["_v2_input_order"] = np.arange(len(out), dtype=np.int64)
    out = out.merge(plain, on=["cnf_id", "sample_id"], how="left", sort=False, validate="one_to_one")
    out = out.merge(static, on="cnf_id", how="left", sort=False, validate="many_to_one")
    out = out.sort_values("_v2_input_order", kind="stable").drop(columns="_v2_input_order")
    out.index = guided_stats.index

    guided_cpu, valid_guided_cpu = _finite_numeric(out, "CPU time")
    guided_decisions, valid_guided_decisions = _finite_numeric(out, "decisions")
    guided_conflicts, valid_guided_conflicts = _finite_numeric(out, "conflicts")
    plain_cpu, _ = _finite_numeric(out, "plain_CPU_time")
    static_cpu, valid_static_cpu = _finite_numeric(out, "static_CPU_time")
    static_decisions, valid_static_decisions = _finite_numeric(out, "static_decisions")
    static_conflicts, valid_static_conflicts = _finite_numeric(out, "static_conflicts")
    guided_nonnegative = (guided_cpu >= 0.0) & (guided_decisions >= 0.0) & (guided_conflicts >= 0.0)
    static_nonnegative = (static_cpu >= 0.0) & (static_decisions >= 0.0) & (static_conflicts >= 0.0)
    valid_guided = valid_guided_cpu & valid_guided_decisions & valid_guided_conflicts & guided_nonnegative
    valid_static_metrics = (
        valid_static_cpu
        & valid_static_decisions
        & valid_static_conflicts
        & static_nonnegative
    )

    guided_result = out["Result"].fillna("").astype(str)
    plain_result = out.get("plain_Result", pd.Series("", index=out.index)).fillna("").astype(str)
    static_result = out.get("static_Result", pd.Series("", index=out.index)).fillna("").astype(str)
    solved_values = {"SATISFIABLE", "UNSATISFIABLE"}
    guided_solved = guided_result.isin(solved_values).to_numpy()
    plain_solved = plain_result.isin(solved_values).to_numpy()
    static_solved = static_result.isin(solved_values).to_numpy()
    plain_present = out.get("_plain_present", pd.Series(False, index=out.index)).eq(True).to_numpy()
    static_present = out.get("_static_present", pd.Series(False, index=out.index)).eq(True).to_numpy()
    missing_plain = ~plain_present
    missing_static = ~static_present
    invalid_static = static_present & ~valid_static_metrics
    plain_unsolved = plain_present & ~plain_solved
    static_unsolved = static_present & ~static_solved
    plain_result_mismatch = guided_solved & plain_solved & guided_result.ne(plain_result).to_numpy()
    static_result_mismatch = guided_solved & static_solved & guided_result.ne(static_result).to_numpy()
    plain_solved_guided_unsolved = plain_solved & ~guided_solved
    static_solved_guided_unsolved = static_solved & ~guided_solved

    control_type = out.get("control_type", pd.Series("", index=out.index)).fillna("").astype(str)
    family = out.get("family", pd.Series("", index=out.index)).fillna("").astype(str)
    symmetry_strength = out.get("symmetry_strength", pd.Series("", index=out.index)).fillna("").astype(str)
    control = (
        control_type.eq("non_symmetric_control")
        | family.eq("random_3sat_control")
        | symmetry_strength.eq("none")
    ).to_numpy()

    valid_orbits, valid_orbits_finite = _finite_numeric(out, "valid_orbit_count")
    confidence_column = "orbit_confidence_mean" if "orbit_confidence_mean" in out.columns else "mean_orbit_confidence"
    orbit_confidence, orbit_confidence_finite = _finite_numeric(out, confidence_column)
    valid_evidence = valid_orbits_finite & orbit_confidence_finite & (valid_orbits > 0.0) & (orbit_confidence > 0.0)

    risk, risk_finite = _finite_numeric(out, "echosat_weighted_risk")
    weighted_risk = (~risk_finite) | (risk > risk_threshold_value)
    near_cap = (
        np.maximum(guided_cpu, static_cpu) / cpu_cap_value >= near_cap_value
    )
    valid_search_baseline = valid_guided & valid_static_metrics & static_solved
    decisions_improved = valid_search_baseline & (
        guided_decisions < (static_decisions - decisions_epsilon)
    )
    conflicts_improved = valid_search_baseline & (
        guided_conflicts < (static_conflicts - conflicts_epsilon)
    )
    dual_improvement = decisions_improved & conflicts_improved
    decision_gain = (static_decisions - guided_decisions) / np.maximum(static_decisions, 1.0)
    conflict_gain = (static_conflicts - guided_conflicts) / np.maximum(static_conflicts, 1.0)
    cpu_gain = np.clip((static_cpu - guided_cpu) / np.maximum(static_cpu, 1.0e-8), -1.0, 1.0)
    search_gain = 0.5 * decision_gain + 0.5 * conflict_gain
    decision_regression = np.maximum(guided_decisions - static_decisions, 0.0) / np.maximum(static_decisions, 1.0)
    conflict_regression = np.maximum(guided_conflicts - static_conflicts, 0.0) / np.maximum(static_conflicts, 1.0)
    regression = decision_regression + conflict_regression
    static_search_blowup = (decision_regression > 0.0) | (conflict_regression > 0.0)
    search_score = np.where(dual_improvement, search_gain + 0.05 * cpu_gain, -regression)
    search_score = np.where(valid_search_baseline, search_score, 0.0)
    valid_search_score = np.isfinite(search_score)
    search_score = np.where(valid_search_score, search_score, 0.0)

    hard_safety_blocked = (
        control
        | plain_result_mismatch
        | static_result_mismatch
        | plain_solved_guided_unsolved
        | static_solved_guided_unsolved
        | plain_unsolved
        | static_unsolved
        | near_cap
        | weighted_risk
        | (~valid_evidence)
        | (~valid_guided)
        | (~valid_search_score)
        | missing_plain
        | missing_static
        | invalid_static
    )
    row_positive_candidate = (
        (~hard_safety_blocked)
        & dual_improvement
        & (~static_search_blowup)
    )
    variant_group = [
        out["base_instance_id"],
        out["variant"],
    ]
    variant_hard_blocked = pd.Series(hard_safety_blocked, index=out.index).groupby(
        variant_group, sort=False
    ).transform("any").to_numpy(dtype=bool)
    variant_mean_search_score = pd.Series(search_score, index=out.index).groupby(
        variant_group, sort=False
    ).transform("mean").to_numpy(dtype=np.float64)
    variant_positive_capable = (
        (~variant_hard_blocked)
        & np.isfinite(variant_mean_search_score)
        & (variant_mean_search_score > 0.0)
    )
    positive_eligible = row_positive_candidate & variant_positive_capable
    base_hard_blocked = pd.Series(hard_safety_blocked, index=out.index).groupby(
        out["base_instance_id"], sort=False
    ).transform("any").to_numpy(dtype=bool)
    out["search_score"] = search_score
    worst_variant_score = worst_variant_scores(out, "search_score").to_numpy(
        dtype=np.float64
    )
    worst_variant_penalty = np.maximum(-worst_variant_score, 0.0)
    row_blocked = ~positive_eligible
    blocked_penalty = row_blocked.astype(np.float64) + np.maximum(regression, 0.0)
    blocked_penalty += plain_result_mismatch.astype(np.float64)
    blocked_penalty += static_result_mismatch.astype(np.float64)
    blocked_penalty += plain_solved_guided_unsolved.astype(np.float64)
    blocked_penalty += static_solved_guided_unsolved.astype(np.float64)
    blocked_penalty += weighted_risk.astype(np.float64)
    blocked_penalty += near_cap.astype(np.float64)
    blocked_penalty = np.maximum(
        blocked_penalty,
        variant_hard_blocked.astype(np.float64),
    )
    blocked_penalty += row_blocked.astype(np.float64) * worst_variant_penalty

    out["v2_missing_plain_baseline"] = missing_plain
    out["v2_plain_unsolved"] = plain_unsolved
    out["v2_missing_static_baseline"] = missing_static
    out["v2_invalid_static_baseline"] = invalid_static
    out["v2_static_unsolved"] = static_unsolved
    out["v2_control_blocked"] = control
    out["v2_plain_result_mismatch"] = plain_result_mismatch
    out["v2_static_result_mismatch"] = static_result_mismatch
    out["v2_plain_solved_guided_unsolved"] = plain_solved_guided_unsolved
    out["v2_static_solved_guided_unsolved"] = static_solved_guided_unsolved
    out["v2_near_cap"] = near_cap
    out["v2_weighted_risk"] = weighted_risk
    out["v2_valid_symmetry_orbit_evidence"] = valid_evidence
    out["v2_decisions_improved"] = decisions_improved
    out["v2_conflicts_improved"] = conflicts_improved
    out["v2_static_search_blowup"] = static_search_blowup
    out["v2_hard_safety_blocked"] = hard_safety_blocked
    out["v2_row_positive_candidate"] = row_positive_candidate
    out["v2_variant_hard_blocked"] = variant_hard_blocked
    out["v2_variant_mean_search_score"] = variant_mean_search_score
    out["v2_variant_positive_capable"] = variant_positive_capable
    out["v2_base_hard_blocked"] = base_hard_blocked
    out["v2_base_blocked"] = variant_hard_blocked
    out["worst_variant_score"] = worst_variant_score
    out["worst_variant_penalty"] = worst_variant_penalty
    out["v2_objective_search_score"] = search_score
    out["v2_positive_eligible"] = positive_eligible
    out["v2_blocked_penalty"] = blocked_penalty
    out["baseline_plain_cpu_time"] = plain_cpu
    out["baseline_plain_result"] = plain_result.to_numpy()
    out["baseline_static_cpu_time"] = static_cpu
    out["baseline_static_decisions"] = static_decisions
    out["baseline_static_conflicts"] = static_conflicts
    out["baseline_static_result"] = static_result.to_numpy()
    out["echosat_target_mode"] = "symmetry_grpo_v2"
    out["echosat_cost"] = np.nan_to_num(
        -out["v2_objective_search_score"].to_numpy(dtype=np.float64) + blocked_penalty,
        nan=1.0,
        posinf=1.0,
        neginf=1.0,
    )
    if "echosat_advantage_weight" not in out.columns:
        out["echosat_advantage_weight"] = 1.0
    return out
