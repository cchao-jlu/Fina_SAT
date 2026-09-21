from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from build_echosat_symmetry_grpo_v1_reward_table import (
    display_path,
    load_orbit_overlap,
    load_targeted_orbits,
    manifest_summary,
    numeric,
    resolve,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_iter235_canonical_low_warmup_observations.csv"
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_runtime_v12_canonical_manifest.csv"
DEFAULT_ORBIT_OVERLAP = ROOT / "runs/analysis/symmetry_runtime_positive_v2_orbit_overlap.csv"
DEFAULT_TARGETED_ORBITS = ROOT / "runs/analysis/symmetry_targeted_nearby_sanity_v2_orbit_rows.csv"
DEFAULT_OUT = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_1_reward_audit_table.csv"
DEFAULT_SUMMARY = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_1_reward_audit_summary.csv"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_1_reward_audit.md"


def bool_values(values: pd.Series) -> np.ndarray:
    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False).to_numpy(dtype=bool)
    return values.fillna(False).astype(str).str.lower().isin({"true", "1", "yes", "y"}).to_numpy(dtype=bool)


def clipped_reduction(delta: np.ndarray, baseline: np.ndarray, clip: float) -> np.ndarray:
    return np.clip(-delta / np.maximum(baseline, 1.0), -clip, clip)


def group_inconsistency_penalty(frame: pd.DataFrame, group_col: str, sign: np.ndarray, magnitude: np.ndarray) -> np.ndarray:
    penalty = np.zeros(len(frame), dtype=np.float64)
    temp = pd.DataFrame(
        {
            "group": frame[group_col].fillna("").astype(str).to_numpy(),
            "sign": sign,
            "idx": np.arange(len(frame)),
        }
    )
    temp = temp[temp["group"].ne("")]
    for _, group in temp.groupby("group", sort=False):
        signs = group["sign"].to_numpy(dtype=np.float64)
        if not ((signs > 0.0).any() and (signs < 0.0).any()):
            continue
        idx = group["idx"].to_numpy(dtype=np.int64)
        row_scale = np.where(sign[idx] < 0.0, 1.0, 0.5)
        penalty[idx] += row_scale * magnitude[idx]
    return penalty


def add_context(observations: pd.DataFrame, manifest: pd.DataFrame, orbit_overlap: pd.DataFrame, targeted_orbits: pd.DataFrame) -> pd.DataFrame:
    out = observations.copy()
    out = out.merge(manifest, on=["base_instance_id", "variant"], how="left")
    if not orbit_overlap.empty:
        out = out.merge(orbit_overlap, on=["base_instance_id", "variant"], how="left")
    if not targeted_orbits.empty:
        out = out.merge(targeted_orbits, on=["base_instance_id", "variant", "repeat_id"], how="left")

    random_mask = (
        out["family"].astype(str).eq("random_3sat_control")
        | out.get("control_type", pd.Series("", index=out.index)).astype(str).eq("non_symmetric_control")
        | bool_values(out.get("random_control_mask_manifest", pd.Series(False, index=out.index)))
    )
    out["random_control_mask"] = random_mask

    valid_orbits = numeric(out, "targeted_valid_orbit_count", np.nan)
    valid_orbits = valid_orbits.fillna(numeric(out, "orbit_valid_rows", 0.0))
    event_positive = numeric(out, "targeted_event_positive_orbit_count", np.nan)
    event_positive = event_positive.fillna(numeric(out, "event_identity_positive_rows", 0.0))
    adapter_sep = numeric(out, "targeted_adapter_orbit_separation", np.nan)
    adapter_sep = adapter_sep.fillna(numeric(out, "orbit_adapter_identity_gain_mean", 0.0))
    event_l2 = numeric(out, "event_state_l2_sum", 0.0)
    graph_gate = numeric(out, "event_adapter_graph_gate_evidence", 0.0)
    strength = out.get("symmetry_strength", pd.Series("", index=out.index)).astype(str)
    strength_score = np.where(strength.eq("strong"), 1.0, np.where(strength.eq("weak"), 0.6, 0.35))
    evidence = (~random_mask).astype(float)
    evidence *= strength_score
    evidence *= np.maximum((event_positive.to_numpy(dtype=np.float64) > 0.0), (event_l2.to_numpy(dtype=np.float64) > 0.0))
    evidence *= np.maximum((valid_orbits.to_numpy(dtype=np.float64) > 0.0), (graph_gate.to_numpy(dtype=np.float64) > 0.0))
    out["valid_orbit_count"] = valid_orbits
    out["event_positive_orbit_count"] = event_positive
    out["adapter_orbit_separation"] = adapter_sep
    out["symmetry_evidence_score"] = np.clip(evidence, 0.0, 1.0)
    out["permutation_pair_id"] = out.get("permutation_pair_id", out["base_instance_id"]).fillna(out["base_instance_id"]).astype(str)
    out["formula_equivalence_group"] = out.get("formula_equivalence_group", pd.Series("", index=out.index)).fillna("").astype(str)
    return out


def compute_components(frame: pd.DataFrame, objective: str, args: argparse.Namespace) -> pd.DataFrame:
    out = frame.copy()
    objective = objective.lower()
    if objective not in {"v1", "v1_1"}:
        raise ValueError(f"unknown objective {objective!r}")

    cached_cpu = numeric(out, "cached_trace_no_adapter_final_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    cached_decisions = numeric(out, "cached_trace_no_adapter_final_final_decisions", 0.0).to_numpy(dtype=np.float64)
    cached_conflicts = numeric(out, "cached_trace_no_adapter_final_final_conflicts", 0.0).to_numpy(dtype=np.float64)
    decision_delta = numeric(out, "adapter_cached_decisions_delta", 0.0).to_numpy(dtype=np.float64)
    conflict_delta = numeric(out, "adapter_cached_conflicts_delta", 0.0).to_numpy(dtype=np.float64)
    cpu_delta = numeric(out, "adapter_cached_final_cpu_delta", 0.0).to_numpy(dtype=np.float64)
    decision_reduction = clipped_reduction(decision_delta, cached_decisions, args.reduction_clip)
    conflict_reduction = clipped_reduction(conflict_delta, cached_conflicts, args.reduction_clip)
    cpu_reduction = np.clip(-(cpu_delta / np.maximum(cached_cpu, 1.0e-3)), -args.cpu_reduction_clip, args.cpu_reduction_clip)

    out["objective"] = objective
    out["normalized_decisions_reduction"] = decision_reduction
    out["normalized_conflicts_reduction"] = conflict_reduction
    out["clipped_final_cpu_reduction"] = cpu_reduction
    out["R_search_decisions"] = args.decisions_weight * np.maximum(decision_reduction, 0.0)
    out["R_search_conflicts"] = args.conflicts_weight * np.maximum(conflict_reduction, 0.0)
    out["R_cpu_clipped"] = args.cpu_weight * np.maximum(cpu_reduction, 0.0)

    random_mask = bool_values(out["random_control_mask"])
    evidence = numeric(out, "symmetry_evidence_score", 0.0).to_numpy(dtype=np.float64)
    final_cap = numeric(out, "final_cpu_lim", 10.0).replace(0.0, 10.0).to_numpy(dtype=np.float64)
    plain_cpu = numeric(out, "plain_unguided_glucose_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    neutral_cpu = numeric(out, "neutral_weighted_glucose_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    static_cpu = numeric(out, "static_weighted_glucose_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    event_cpu = numeric(out, "event_adapter_final_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    weighted_risk = np.maximum(0.0, (neutral_cpu - plain_cpu) / np.maximum(plain_cpu, 1.0e-3))
    weighted_risk += np.maximum(0.0, (static_cpu - neutral_cpu) / np.maximum(neutral_cpu, 1.0e-3))
    near_cap = np.maximum.reduce([plain_cpu, neutral_cpu, static_cpu, event_cpu, cached_cpu]) >= args.near_cap_fraction * final_cap

    control_perturbation = random_mask.astype(np.float64) * (
        np.abs(decision_reduction) + np.abs(conflict_reduction) + np.abs(cpu_reduction)
    )
    parameter_shift_available = all(column in out.columns for column in ["phase_flip_frac", "weight_relative_abs_mean", "weight_rank_change_penalty"])
    if parameter_shift_available:
        large_shift = (
            numeric(out, "phase_flip_frac", 0.0)
            + numeric(out, "weight_relative_abs_mean", 0.0)
            + numeric(out, "weight_rank_change_penalty", 0.0)
        ).to_numpy(dtype=np.float64)
    else:
        large_shift = np.zeros(len(out), dtype=np.float64)

    search_ok = (decision_delta < -args.search_eps_decisions) & (conflict_delta < -args.search_eps_conflicts)
    search_blowup = (decision_delta > args.search_eps_decisions) | (conflict_delta > args.search_eps_conflicts)
    search_blowup_penalty = (
        args.decision_blowup_penalty_weight * np.clip(np.maximum(decision_delta, 0.0) / np.maximum(cached_decisions, 1.0), 0.0, args.reduction_clip)
        + args.conflict_blowup_penalty_weight * np.clip(np.maximum(conflict_delta, 0.0) / np.maximum(cached_conflicts, 1.0), 0.0, args.reduction_clip)
    )
    positive_raw = out["R_search_decisions"].to_numpy(dtype=np.float64) + out["R_search_conflicts"].to_numpy(dtype=np.float64) + out["R_cpu_clipped"].to_numpy(dtype=np.float64)

    if objective == "v1":
        signed_search = (
            args.decisions_weight * decision_reduction
            + args.conflicts_weight * conflict_reduction
            + args.v1_cpu_weight * np.clip(-(cpu_delta / np.maximum(cached_cpu, 1.0e-3)), -0.25, 0.25)
        )
        positive_search = np.maximum(signed_search, 0.0)
        negative_search = np.minimum(signed_search, 0.0)
        positive_reward = positive_search * evidence
        random_penalty = random_mask.astype(np.float64) * np.maximum(positive_search, control_perturbation)
        sign = np.sign(decision_reduction + conflict_reduction)
        magnitude = np.log1p(np.abs(decision_reduction + conflict_reduction))
        perm_penalty = group_inconsistency_penalty(out, "base_instance_id", sign, magnitude)
        if out["formula_equivalence_group"].ne("").any():
            perm_penalty += group_inconsistency_penalty(out, "formula_equivalence_group", sign, magnitude)
        weighted_penalty = weighted_risk
        near_cap_penalty = near_cap.astype(np.float64) * positive_search
        large_shift_penalty = large_shift * (1.0 - evidence)
        reward = (
            positive_reward
            + negative_search
            - args.v1_random_control_penalty_weight * random_penalty
            - args.v1_control_perturbation_penalty_weight * control_perturbation
            - args.v1_permutation_penalty_weight * perm_penalty
            - args.v1_weighted_risk_penalty_weight * weighted_penalty
            - args.v1_near_cap_penalty_weight * near_cap_penalty
            - args.v1_phase_shift_penalty_weight * large_shift_penalty
        )
        out["positive_symmetry_reward"] = positive_reward
        out["search_blowup_penalty"] = search_blowup_penalty
        out["random_control_penalty"] = random_penalty
        out["control_perturbation_penalty"] = control_perturbation
        out["permutation_inconsistency_penalty"] = perm_penalty
        out["weighted_path_risk_penalty"] = weighted_penalty
        out["near_cap_penalty"] = near_cap_penalty
        out["large_weight_phase_shift_penalty"] = large_shift_penalty
    else:
        positive_allowed = search_ok & (~random_mask) & (evidence > 0.0) & (~near_cap) & (weighted_risk <= args.weighted_risk_positive_threshold)
        positive_reward = positive_allowed.astype(np.float64) * evidence * positive_raw
        sign = np.where(search_ok, 1.0, np.where(search_blowup, -1.0, 0.0))
        magnitude = search_blowup_penalty + np.abs(decision_reduction) + np.abs(conflict_reduction) + positive_reward
        perm_penalty = group_inconsistency_penalty(out, "base_instance_id", sign, magnitude)
        if out["formula_equivalence_group"].ne("").any():
            perm_penalty += group_inconsistency_penalty(out, "formula_equivalence_group", sign, magnitude)
        weighted_penalty = weighted_risk * (1.0 + control_perturbation)
        near_cap_penalty = near_cap.astype(np.float64) * (positive_raw + search_blowup_penalty)
        large_shift_penalty = large_shift * (1.0 - evidence)
        random_penalty = random_mask.astype(np.float64) * np.maximum(search_blowup_penalty + positive_reward, control_perturbation)
        reward = (
            positive_reward
            - search_blowup_penalty
            - args.random_control_penalty_weight * random_penalty
            - args.control_perturbation_penalty_weight * control_perturbation
            - args.permutation_penalty_weight * perm_penalty
            - args.weighted_risk_penalty_weight * weighted_penalty
            - args.near_cap_penalty_weight * near_cap_penalty
            - args.phase_shift_penalty_weight * large_shift_penalty
        )
        out["positive_symmetry_reward"] = positive_reward
        out["search_blowup_penalty"] = search_blowup_penalty
        out["random_control_penalty"] = random_penalty
        out["control_perturbation_penalty"] = control_perturbation
        out["permutation_inconsistency_penalty"] = perm_penalty
        out["weighted_path_risk_penalty"] = weighted_penalty
        out["near_cap_penalty"] = near_cap_penalty
        out["large_weight_phase_shift_penalty"] = large_shift_penalty

    out["search_ok"] = search_ok
    out["search_blowup"] = search_blowup
    out["weighted_path_risk"] = weighted_risk
    out["near_cap_mask"] = near_cap
    out["control_perturbation_score"] = control_perturbation
    out["parameter_shift_available"] = parameter_shift_available
    out["final_reward"] = reward
    out["final_cost"] = -reward
    out["reward_label"] = np.where(reward > 0.01, "positive", np.where(reward < -0.01, "negative", "neutral"))
    out["advantage_group_id"] = (
        out["base_instance_id"].astype(str)
        + "::"
        + out["variant"].astype(str)
        + "::wc"
        + out["warmup_conflicts"].astype(str)
    )
    raw_advantage = np.zeros(len(out), dtype=np.float64)
    for _, group in out.groupby("advantage_group_id", sort=False):
        values = group["final_cost"].to_numpy(dtype=np.float64)
        std = float(np.nanstd(values, ddof=1)) if len(values) > 1 else 0.0
        if not math.isfinite(std) or std <= 1.0e-8:
            continue
        mean = float(np.nanmean(values))
        raw_advantage[group.index.to_numpy(dtype=np.int64)] = -((values - mean) / (std + 1.0e-8))
    out["grpo_raw_advantage"] = raw_advantage
    if objective == "v1_1":
        positive_allowed_series = (out["final_reward"].to_numpy(dtype=np.float64) > 0.0)
        out["grpo_advantage"] = np.where((~positive_allowed_series) & (raw_advantage > 0.0), 0.0, raw_advantage)
    else:
        out["grpo_advantage"] = raw_advantage
    out["grpo_positive_advantage"] = out["grpo_advantage"] > 1.0e-12
    return out


def summarize(table: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    groupings = [
        ("overall", ["objective"]),
        ("by_warmup", ["objective", "warmup_conflicts"]),
        ("by_family", ["objective", "warmup_conflicts", "family"]),
        ("by_base", ["objective", "warmup_conflicts", "family", "base_instance_id"]),
    ]
    for level, cols in groupings:
        for key, group in table.groupby(cols, sort=True, dropna=False):
            if not isinstance(key, tuple):
                key = (key,)
            row: dict[str, Any] = {"level": level}
            for col, value in zip(cols, key):
                row[col] = value
            row.update(
                {
                    "rows": int(len(group)),
                    "bases": int(group["base_instance_id"].nunique()),
                    "reward_mean": float(group["final_reward"].mean()),
                    "positive_reward_rows": int((group["final_reward"] > 0.01).sum()),
                    "negative_reward_rows": int((group["final_reward"] < -0.01).sum()),
                    "positive_advantage_rows": int(group["grpo_positive_advantage"].sum()),
                    "random_positive_reward_rows": int(((group["random_control_mask"]) & (group["final_reward"] > 0.01)).sum()),
                    "random_positive_advantage_rows": int(((group["random_control_mask"]) & (group["grpo_advantage"] > 1.0e-12)).sum()),
                    "search_ok_rows": int(group["search_ok"].sum()),
                    "search_blowup_rows": int(group["search_blowup"].sum()),
                    "cpu_only_positive_reward_rows": int(((~group["search_ok"]) & (group["adapter_cached_final_cpu_delta"] < 0.0) & (group["final_reward"] > 0.01)).sum()),
                    "near_cap_positive_reward_rows": int(((group["near_cap_mask"]) & (group["final_reward"] > 0.01)).sum()),
                    "weighted_risk_positive_reward_rows": int(((group["weighted_path_risk"] > 0.0) & (group["final_reward"] > 0.01)).sum()),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows)
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        cells = []
        for col in cols:
            value = row[col]
            if isinstance(value, (float, np.floating)):
                cells.append(f"{float(value):.6g}" if math.isfinite(float(value)) else "nan")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def strict_checks(table: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    v11 = table[table["objective"].eq("v1_1")].copy()
    if v11.empty:
        return ["missing v1_1 rows"]
    random_rows = v11[v11["random_control_mask"]]
    if int((random_rows["final_reward"] > 0.01).sum()) != 0:
        errors.append("random controls have positive reward")
    if int((random_rows["grpo_advantage"] > 1.0e-12).sum()) != 0:
        errors.append("random controls have positive GRPO advantage")
    for base in ["k9_color8", "php_p9_h8"]:
        rows = v11[v11["base_instance_id"].eq(base)]
        if rows.empty or int((rows["final_reward"] > 0.01).sum()) == 0:
            errors.append(f"{base} has no positive reward rows")
    for base in ["k10_color9", "php_p10_h9"]:
        rows = v11[v11["base_instance_id"].eq(base)]
        if rows.empty or int((rows["final_reward"] < -0.01).sum()) == 0:
            errors.append(f"{base} has no negative reward rows")
    subset_failure = v11[v11["base_instance_id"].eq("subset_cardinality_bw12") & v11["variant"].astype(str).eq("perm_seed1730")]
    if subset_failure.empty or int((subset_failure["final_reward"] < -0.01).sum()) == 0:
        errors.append("subset_cardinality_bw12::perm_seed1730 has no negative reward rows")
    if int(((v11["near_cap_mask"]) & (v11["final_reward"] > 0.01)).sum()) != 0:
        errors.append("near-cap rows have positive reward")
    if int(((v11["weighted_path_risk"] > 0.0) & (v11["final_reward"] > 0.01)).sum()) != 0:
        errors.append("weighted-risk rows have positive reward")
    cpu_only = (~v11["search_ok"]) & (v11["adapter_cached_final_cpu_delta"] < 0.0) & (v11["final_reward"] > 0.01)
    if int(cpu_only.sum()) != 0:
        errors.append("CPU-only win rows have positive reward")
    non_positive_reward_positive_advantage = (v11["final_reward"] <= 0.0) & (v11["grpo_advantage"] > 1.0e-12)
    if int(non_positive_reward_positive_advantage.sum()) != 0:
        errors.append("non-positive reward rows have positive GRPO advantage")
    return errors


def write_doc(path: Path, table: pd.DataFrame, summary: pd.DataFrame, out_csv: Path, summary_csv: Path, errors: list[str]) -> None:
    key_bases = table[
        table["base_instance_id"].astype(str).isin(
            ["k9_color8", "php_p9_h8", "k10_color9", "php_p10_h9", "subset_cardinality_bw12"]
        )
    ]
    random_summary = summary[summary["level"].eq("by_family") & summary["family"].astype(str).eq("random_3sat_control")]
    v11_positive = table[table["objective"].eq("v1_1") & (table["final_reward"] > 0.01)].sort_values("final_reward", ascending=False)
    v11_negative = table[table["objective"].eq("v1_1") & (table["final_reward"] < -0.01)].sort_values("final_reward")
    lines = [
        "# EchoSAT Symmetry GRPO v1.1 Reward Audit",
        "",
        "This is an offline reward attribution and dry-run table from existing canonical low-warmup runtime outputs. It does not train a model, does not expand the benchmark, and does not use a gate/selector.",
        "",
        "## Artifacts",
        "",
        f"- reward audit CSV: `{display_path(out_csv)}`",
        f"- summary CSV: `{display_path(summary_csv)}`",
        "",
        "## Dry-Run Gate",
        "",
        "- status: " + ("PASS" if not errors else "FAIL"),
        *[f"- failure: {error}" for error in errors],
        "",
        "## Summary",
        "",
        *markdown_table(summary[summary["level"].isin(["overall", "by_warmup", "by_family"])], max_rows=120),
        "",
        "## Random Controls",
        "",
        *markdown_table(random_summary, max_rows=40),
        "",
        "## Key Bases",
        "",
        *markdown_table(
            key_bases[
                [
                    "objective",
                    "warmup_conflicts",
                    "base_instance_id",
                    "variant",
                    "repeat_id",
                    "final_reward",
                    "grpo_advantage",
                    "search_ok",
                    "search_blowup",
                    "adapter_cached_decisions_delta",
                    "adapter_cached_conflicts_delta",
                    "adapter_cached_final_cpu_delta",
                    "R_search_decisions",
                    "R_search_conflicts",
                    "R_cpu_clipped",
                    "search_blowup_penalty",
                    "permutation_inconsistency_penalty",
                ]
            ].sort_values(["objective", "warmup_conflicts", "base_instance_id", "variant", "repeat_id"]),
            max_rows=120,
        ),
        "",
        "## v1.1 Top Positive Rows",
        "",
        *markdown_table(
            v11_positive[
                [
                    "warmup_conflicts",
                    "family",
                    "base_instance_id",
                    "variant",
                    "repeat_id",
                    "final_reward",
                    "grpo_advantage",
                    "R_search_decisions",
                    "R_search_conflicts",
                    "R_cpu_clipped",
                ]
            ],
            max_rows=30,
        ),
        "",
        "## v1.1 Top Negative Rows",
        "",
        *markdown_table(
            v11_negative[
                [
                    "warmup_conflicts",
                    "family",
                    "base_instance_id",
                    "variant",
                    "repeat_id",
                    "final_reward",
                    "grpo_advantage",
                    "search_blowup_penalty",
                    "random_control_penalty",
                    "permutation_inconsistency_penalty",
                    "weighted_path_risk_penalty",
                ]
            ],
            max_rows=30,
        ),
        "",
        "## Notes",
        "",
        "- v1.1 positive reward is allowed only when adapter-vs-cached decisions and conflicts both decrease.",
        "- CPU is only a tie-breaker after strict search-work improvement; this dry-run uses the configured CPU weight.",
        "- Random controls and all non-positive-reward rows are hard-clamped to non-positive GRPO advantage in v1.1.",
        "- Runtime CSVs do not contain actual adapter phase/weight deltas, so offline `large_weight_phase_shift_penalty` is zero unless those columns are present. Training uses live `phase_flip_frac`, `weight_relative_abs_mean`, and `weight_rank_change_penalty` from sampled variable parameters.",
        "- Adapter-vs-plain protocol time is retained in the table only as a diagnostic field.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit EchoSAT Symmetry GRPO v1 reward and dry-run v1.1 strict objective.")
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--orbit-overlap", type=Path, default=DEFAULT_ORBIT_OVERLAP)
    parser.add_argument("--targeted-orbits", type=Path, default=DEFAULT_TARGETED_ORBITS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--decisions-weight", type=float, default=0.55)
    parser.add_argument("--conflicts-weight", type=float, default=0.45)
    parser.add_argument("--cpu-weight", type=float, default=0.0)
    parser.add_argument("--v1-cpu-weight", type=float, default=0.15)
    parser.add_argument("--reduction-clip", type=float, default=1.0)
    parser.add_argument("--cpu-reduction-clip", type=float, default=0.05)
    parser.add_argument("--search-eps-decisions", type=float, default=0.0)
    parser.add_argument("--search-eps-conflicts", type=float, default=0.0)
    parser.add_argument("--decision-blowup-penalty-weight", type=float, default=2.0)
    parser.add_argument("--conflict-blowup-penalty-weight", type=float, default=2.0)
    parser.add_argument("--random-control-penalty-weight", type=float, default=4.0)
    parser.add_argument("--control-perturbation-penalty-weight", type=float, default=2.0)
    parser.add_argument("--permutation-penalty-weight", type=float, default=2.0)
    parser.add_argument("--weighted-risk-penalty-weight", type=float, default=1.25)
    parser.add_argument("--near-cap-penalty-weight", type=float, default=1.0)
    parser.add_argument("--phase-shift-penalty-weight", type=float, default=1.0)
    parser.add_argument("--weighted-risk-positive-threshold", type=float, default=0.0)
    parser.add_argument("--near-cap-fraction", type=float, default=0.8)
    parser.add_argument("--v1-random-control-penalty-weight", type=float, default=2.0)
    parser.add_argument("--v1-control-perturbation-penalty-weight", type=float, default=1.0)
    parser.add_argument("--v1-permutation-penalty-weight", type=float, default=0.75)
    parser.add_argument("--v1-weighted-risk-penalty-weight", type=float, default=0.75)
    parser.add_argument("--v1-near-cap-penalty-weight", type=float, default=0.25)
    parser.add_argument("--v1-phase-shift-penalty-weight", type=float, default=0.2)
    parser.add_argument("--no-strict-checks", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = add_context(
        pd.read_csv(resolve(args.observations)),
        manifest_summary(resolve(args.manifest)),
        load_orbit_overlap(resolve(args.orbit_overlap)),
        load_targeted_orbits(resolve(args.targeted_orbits)),
    )
    tables = [compute_components(context, "v1", args), compute_components(context, "v1_1", args)]
    table = pd.concat(tables, ignore_index=True)
    columns = [
        "objective",
        "family",
        "base_instance_id",
        "variant",
        "repeat_id",
        "warmup_conflicts",
        "adapter_cached_final_cpu_delta",
        "adapter_cached_decisions_delta",
        "adapter_cached_conflicts_delta",
        "adapter_plain_protocol_delta",
        "random_control_mask",
        "symmetry_evidence_score",
        "valid_orbit_count",
        "event_positive_orbit_count",
        "adapter_orbit_separation",
        "weighted_path_risk",
        "near_cap_mask",
        "permutation_pair_id",
        "formula_equivalence_group",
        "search_ok",
        "search_blowup",
        "normalized_decisions_reduction",
        "normalized_conflicts_reduction",
        "clipped_final_cpu_reduction",
        "R_search_decisions",
        "R_search_conflicts",
        "R_cpu_clipped",
        "positive_symmetry_reward",
        "search_blowup_penalty",
        "random_control_penalty",
        "control_perturbation_penalty",
        "permutation_inconsistency_penalty",
        "weighted_path_risk_penalty",
        "near_cap_penalty",
        "large_weight_phase_shift_penalty",
        "final_reward",
        "final_cost",
        "reward_label",
        "advantage_group_id",
        "grpo_raw_advantage",
        "grpo_advantage",
        "grpo_positive_advantage",
        "parameter_shift_available",
    ]
    table = table[[column for column in columns if column in table.columns]].sort_values(
        ["objective", "warmup_conflicts", "family", "base_instance_id", "variant", "repeat_id"]
    )
    summary = summarize(table)
    errors = [] if args.no_strict_checks else strict_checks(table)
    out = resolve(args.out)
    summary_path = resolve(args.summary)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False)
    summary.to_csv(summary_path, index=False)
    write_doc(resolve(args.doc), table=table, summary=summary, out_csv=out, summary_csv=summary_path, errors=errors)
    print(f"wrote {out}")
    print(f"wrote {summary_path}")
    print(f"wrote {resolve(args.doc)}")
    if errors:
        raise SystemExit("strict reward dry-run failed: " + "; ".join(errors))


if __name__ == "__main__":
    main()
