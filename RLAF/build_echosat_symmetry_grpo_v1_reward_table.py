from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_runtime_v12_canonical_low_warmup_observations.csv"
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_runtime_v12_canonical_manifest.csv"
DEFAULT_ORBIT_OVERLAP = ROOT / "runs/analysis/symmetry_runtime_positive_v2_orbit_overlap.csv"
DEFAULT_TARGETED_ORBITS = ROOT / "runs/analysis/symmetry_targeted_nearby_sanity_v2_orbit_rows.csv"
DEFAULT_OUT = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_reward_table.csv"
DEFAULT_SUMMARY = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_reward_summary.csv"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_reward_table.md"

FORMULA_EQUIVALENCE_GROUPS = {
    "k9_color8": "formula_equiv_k9_php_p9",
    "php_p9_h8": "formula_equiv_k9_php_p9",
    "k10_color9": "formula_equiv_k10_php_p10",
    "php_p10_h9": "formula_equiv_k10_php_p10",
}


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def bool_series(values: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False).astype(bool)
    return values.fillna(False).astype(str).str.lower().isin({"true", "1", "yes", "y"})


def numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=np.float64)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(np.float64)


def safe_div(num: np.ndarray, denom: np.ndarray, eps: float = 1.0) -> np.ndarray:
    return num / np.maximum(denom, eps)


def clipped_reduction(delta: np.ndarray, baseline: np.ndarray, clip: float) -> np.ndarray:
    return np.clip(-safe_div(delta, baseline, eps=1.0), -clip, clip)


def load_orbit_overlap(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return frame
    keys = ["base_instance_id", "variant"]
    agg = (
        frame.groupby(keys, sort=True)
        .agg(
            orbit_rows=("orbit_rows", "mean"),
            orbit_valid_rows=("orbit_valid_rows", "mean"),
            event_identity_positive_rows=("event_identity_positive_rows", "mean"),
            orbit_adapter_identity_gain_mean=("orbit_adapter_identity_gain_mean", "mean"),
            orbit_adapter_identity_gain_max=("orbit_adapter_identity_gain_max", "max"),
            orbit_event_identity_gain_mean=("orbit_event_identity_gain_mean", "mean"),
            orbit_overlap_available=("orbit_overlap_available", "max"),
        )
        .reset_index()
    )
    return agg


def load_targeted_orbits(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return frame
    frame = frame.copy()
    frame["_valid"] = bool_series(frame.get("event_row_valid", pd.Series(False, index=frame.index)))
    frame["_positive"] = bool_series(frame.get("event_identity_positive", pd.Series(False, index=frame.index)))
    agg = (
        frame.groupby(["base_instance_id", "variant", "repeat_id"], sort=True)
        .agg(
            targeted_orbit_rows=("orbit", "size"),
            targeted_valid_orbit_count=("_valid", "sum"),
            targeted_event_positive_orbit_count=("_positive", "sum"),
            targeted_adapter_orbit_separation=("adapter_identity_gain", "mean"),
            targeted_adapter_orbit_separation_max=("adapter_identity_gain", "max"),
            targeted_event_identity_gain=("event_identity_gain", "mean"),
        )
        .reset_index()
    )
    return agg


def manifest_summary(path: Path) -> pd.DataFrame:
    manifest = pd.read_csv(path)
    manifest = manifest.copy()
    manifest["random_control_mask_manifest"] = (
        manifest["family"].astype(str).eq("random_3sat_control")
        | manifest.get("control_type", pd.Series("", index=manifest.index)).astype(str).eq("non_symmetric_control")
    )
    manifest["permutation_pair_id"] = manifest["base_instance_id"].astype(str)
    manifest["formula_equivalence_group"] = manifest["base_instance_id"].astype(str).map(FORMULA_EQUIVALENCE_GROUPS).fillna("")
    manifest.loc[manifest["formula_equivalence_group"].ne(""), "permutation_pair_id"] = manifest.loc[
        manifest["formula_equivalence_group"].ne(""),
        "formula_equivalence_group",
    ]
    cols = [
        "base_instance_id",
        "variant",
        "cnf_path",
        "orbits_path",
        "metadata_path",
        "random_control_mask_manifest",
        "permutation_pair_id",
        "formula_equivalence_group",
        "source_cnf_path",
    ]
    return manifest[[column for column in cols if column in manifest.columns]].drop_duplicates(["base_instance_id", "variant"])


def compute_group_direction_penalties(frame: pd.DataFrame, group_col: str, prefix: str) -> pd.Series:
    penalties = pd.Series(0.0, index=frame.index, dtype=np.float64)
    for _, group in frame.groupby(group_col, sort=False, dropna=False):
        if len(group) < 2:
            continue
        search_score = -(
            numeric(group, "adapter_cached_decisions_delta", 0.0)
            + numeric(group, "adapter_cached_conflicts_delta", 0.0)
        )
        signs = np.sign(search_score.to_numpy(dtype=np.float64))
        nonzero = signs[signs != 0]
        if len(nonzero) == 0:
            continue
        majority = 1.0 if np.sum(nonzero > 0) >= np.sum(nonzero < 0) else -1.0
        mismatch = (signs != 0) & (signs != majority)
        magnitude = np.log1p(np.abs(search_score.to_numpy(dtype=np.float64)))
        penalties.loc[group.index] = mismatch.astype(float) * magnitude
    penalties.name = f"{prefix}_direction_penalty"
    return penalties


def build_reward_table(
    observations: pd.DataFrame,
    manifest: pd.DataFrame,
    orbit_overlap: pd.DataFrame,
    targeted_orbits: pd.DataFrame,
    *,
    decisions_weight: float,
    conflicts_weight: float,
    cpu_weight: float,
    random_control_penalty_weight: float,
    control_perturbation_penalty_weight: float,
    permutation_penalty_weight: float,
    weighted_risk_penalty_weight: float,
    near_cap_penalty_weight: float,
    phase_shift_penalty_weight: float,
    reduction_clip: float,
) -> pd.DataFrame:
    out = observations.copy()
    out = out.merge(manifest, on=["base_instance_id", "variant"], how="left")
    if not orbit_overlap.empty:
        out = out.merge(orbit_overlap, on=["base_instance_id", "variant"], how="left")
    if not targeted_orbits.empty:
        out = out.merge(targeted_orbits, on=["base_instance_id", "variant", "repeat_id"], how="left")

    random_mask = (
        out["family"].astype(str).eq("random_3sat_control")
        | out.get("control_type", pd.Series("", index=out.index)).astype(str).eq("non_symmetric_control")
        | bool_series(out.get("random_control_mask_manifest", pd.Series(False, index=out.index)))
    )
    out["random_control_mask"] = random_mask

    final_cap = numeric(out, "final_cpu_lim", 10.0).replace(0.0, 10.0).to_numpy(dtype=np.float64)
    cached_cpu = numeric(out, "cached_trace_no_adapter_final_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    cached_decisions = numeric(out, "cached_trace_no_adapter_final_final_decisions", 0.0).to_numpy(dtype=np.float64)
    cached_conflicts = numeric(out, "cached_trace_no_adapter_final_final_conflicts", 0.0).to_numpy(dtype=np.float64)

    decision_delta = numeric(out, "adapter_cached_decisions_delta", 0.0).to_numpy(dtype=np.float64)
    conflict_delta = numeric(out, "adapter_cached_conflicts_delta", 0.0).to_numpy(dtype=np.float64)
    cpu_delta = numeric(out, "adapter_cached_final_cpu_delta", 0.0).to_numpy(dtype=np.float64)
    decision_reduction = clipped_reduction(decision_delta, cached_decisions, reduction_clip)
    conflict_reduction = clipped_reduction(conflict_delta, cached_conflicts, reduction_clip)
    cpu_reduction = np.clip(-(cpu_delta / np.maximum(cached_cpu, 1.0e-3)), -0.25, 0.25)

    out["normalized_decisions_reduction"] = decision_reduction
    out["normalized_conflicts_reduction"] = conflict_reduction
    out["clipped_final_cpu_reduction"] = cpu_reduction
    out["search_reward_raw"] = (
        float(decisions_weight) * decision_reduction
        + float(conflicts_weight) * conflict_reduction
        + float(cpu_weight) * cpu_reduction
    )

    valid_orbit_count = numeric(out, "targeted_valid_orbit_count", np.nan)
    valid_orbit_count = valid_orbit_count.fillna(numeric(out, "orbit_valid_rows", 0.0))
    event_positive = numeric(out, "targeted_event_positive_orbit_count", np.nan)
    event_positive = event_positive.fillna(numeric(out, "event_identity_positive_rows", 0.0))
    adapter_sep = numeric(out, "targeted_adapter_orbit_separation", np.nan)
    adapter_sep = adapter_sep.fillna(numeric(out, "orbit_adapter_identity_gain_mean", 0.0))
    event_l2 = numeric(out, "event_state_l2_sum", 0.0)
    graph_gate = numeric(out, "event_adapter_graph_gate_evidence", 0.0)
    non_control = (~random_mask).astype(float).to_numpy(dtype=np.float64)
    orbit_gate = (valid_orbit_count.to_numpy(dtype=np.float64) > 0).astype(np.float64)
    event_positive_gate = (event_positive.to_numpy(dtype=np.float64) > 0).astype(np.float64)
    event_state_gate = (event_l2.to_numpy(dtype=np.float64) > 0).astype(np.float64)
    strength = out.get("symmetry_strength", pd.Series("", index=out.index)).astype(str)
    strength_score = np.where(strength.eq("strong"), 1.0, np.where(strength.eq("weak"), 0.6, 0.35))
    symmetry_evidence_score = non_control * strength_score * np.maximum(event_positive_gate, event_state_gate) * np.maximum(orbit_gate, graph_gate.to_numpy(dtype=np.float64) > 0)
    symmetry_evidence_score = np.clip(symmetry_evidence_score, 0.0, 1.0)
    out["valid_orbit_count"] = valid_orbit_count
    out["event_positive_orbit_count"] = event_positive
    out["adapter_orbit_separation"] = adapter_sep
    out["symmetry_evidence_score"] = symmetry_evidence_score

    neutral_cpu = numeric(out, "neutral_weighted_glucose_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    static_cpu = numeric(out, "static_weighted_glucose_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    event_cpu = numeric(out, "event_adapter_final_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    plain_cpu = numeric(out, "plain_unguided_glucose_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    weighted_path_risk = np.maximum(0.0, (neutral_cpu - plain_cpu) / np.maximum(plain_cpu, 1.0e-3))
    weighted_path_risk += np.maximum(0.0, (static_cpu - neutral_cpu) / np.maximum(neutral_cpu, 1.0e-3))
    out["weighted_path_risk"] = weighted_path_risk
    near_cap_mask = np.maximum.reduce([plain_cpu, neutral_cpu, static_cpu, event_cpu, cached_cpu]) >= 0.8 * final_cap
    out["near_cap_mask"] = near_cap_mask

    if "permutation_pair_id" not in out.columns:
        out["permutation_pair_id"] = out["base_instance_id"].astype(str)
    out["permutation_pair_id"] = out["permutation_pair_id"].fillna(out["base_instance_id"]).astype(str)
    out["formula_equivalence_group"] = out.get("formula_equivalence_group", pd.Series("", index=out.index)).fillna("").astype(str)
    out["permutation_consistency_delta"] = compute_group_direction_penalties(out, "base_instance_id", "permutation")
    formula_penalty = compute_group_direction_penalties(
        out[out["formula_equivalence_group"].ne("")].copy(),
        "formula_equivalence_group",
        "formula_equivalence",
    )
    out["formula_equivalence_direction_penalty"] = 0.0
    if not formula_penalty.empty:
        out.loc[formula_penalty.index, "formula_equivalence_direction_penalty"] = formula_penalty
    out["permutation_consistency_delta"] += out["formula_equivalence_direction_penalty"]

    control_perturbation_score = random_mask.astype(float).to_numpy(dtype=np.float64) * (
        np.abs(decision_reduction) + np.abs(conflict_reduction) + np.abs(cpu_reduction)
    )
    out["control_perturbation_score"] = control_perturbation_score
    out["large_weight_phase_shift_penalty"] = 0.0

    positive_search = np.maximum(out["search_reward_raw"].to_numpy(dtype=np.float64), 0.0)
    negative_search = np.minimum(out["search_reward_raw"].to_numpy(dtype=np.float64), 0.0)
    gated_search = positive_search * symmetry_evidence_score + negative_search
    out["random_control_penalty"] = random_mask.astype(float).to_numpy(dtype=np.float64) * np.maximum(positive_search, control_perturbation_score)
    out["control_perturbation_penalty"] = control_perturbation_score
    out["near_cap_penalty"] = near_cap_mask.astype(float) * np.maximum(0.0, positive_search)
    out["symmetry_grpo_v1_reward"] = (
        gated_search
        - float(random_control_penalty_weight) * out["random_control_penalty"].to_numpy(dtype=np.float64)
        - float(control_perturbation_penalty_weight) * out["control_perturbation_penalty"].to_numpy(dtype=np.float64)
        - float(permutation_penalty_weight) * out["permutation_consistency_delta"].to_numpy(dtype=np.float64)
        - float(weighted_risk_penalty_weight) * out["weighted_path_risk"].to_numpy(dtype=np.float64)
        - float(near_cap_penalty_weight) * out["near_cap_penalty"].to_numpy(dtype=np.float64)
        - float(phase_shift_penalty_weight) * out["large_weight_phase_shift_penalty"].to_numpy(dtype=np.float64)
    )
    out["symmetry_grpo_v1_cost"] = -out["symmetry_grpo_v1_reward"]
    out["reward_label"] = np.where(out["symmetry_grpo_v1_reward"] > 0.01, "positive", np.where(out["symmetry_grpo_v1_reward"] < -0.01, "negative", "neutral"))
    columns = [
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
        "permutation_consistency_delta",
        "control_perturbation_score",
        "large_weight_phase_shift_penalty",
        "normalized_decisions_reduction",
        "normalized_conflicts_reduction",
        "clipped_final_cpu_reduction",
        "search_reward_raw",
        "random_control_penalty",
        "control_perturbation_penalty",
        "near_cap_penalty",
        "symmetry_grpo_v1_reward",
        "symmetry_grpo_v1_cost",
        "reward_label",
    ]
    return out[[column for column in columns if column in out.columns]].sort_values(
        ["warmup_conflicts", "family", "base_instance_id", "variant", "repeat_id"]
    )


def summarize(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groupings = [
        ("overall", []),
        ("by_warmup", ["warmup_conflicts"]),
        ("by_family", ["warmup_conflicts", "family"]),
        ("by_base", ["warmup_conflicts", "family", "base_instance_id"]),
    ]
    for level, columns in groupings:
        grouped = [((), table)] if not columns else table.groupby(columns, sort=True, dropna=False)
        for key, group in grouped:
            if not isinstance(key, tuple):
                key = (key,)
            row: dict[str, Any] = {"level": level}
            for column, value in zip(columns, key):
                row[column] = value
            row.update(
                {
                    "rows": int(len(group)),
                    "bases": int(group["base_instance_id"].nunique()),
                    "reward_mean": float(group["symmetry_grpo_v1_reward"].mean()),
                    "reward_median": float(group["symmetry_grpo_v1_reward"].median()),
                    "positive_rows": int((group["symmetry_grpo_v1_reward"] > 0.01).sum()),
                    "negative_rows": int((group["symmetry_grpo_v1_reward"] < -0.01).sum()),
                    "random_rows": int(bool_series(group["random_control_mask"]).sum()),
                    "symmetry_evidence_mean": float(group["symmetry_evidence_score"].mean()),
                    "search_reward_raw_mean": float(group["search_reward_raw"].mean()),
                    "permutation_penalty_mean": float(group["permutation_consistency_delta"].mean()),
                    "control_perturbation_mean": float(group["control_perturbation_score"].mean()),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, (float, np.floating)):
                cells.append(f"{float(value):.6g}" if math.isfinite(float(value)) else "nan")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(path: Path, table: pd.DataFrame, summary: pd.DataFrame, out_csv: Path, summary_csv: Path) -> None:
    positive = table[table["symmetry_grpo_v1_reward"] > 0.01].sort_values("symmetry_grpo_v1_reward", ascending=False)
    negative = table[table["symmetry_grpo_v1_reward"] < -0.01].sort_values("symmetry_grpo_v1_reward")
    key_bases = table[table["base_instance_id"].astype(str).isin(["k9_color8", "php_p9_h8", "k10_color9", "php_p10_h9", "subset_cardinality_bw12"])]
    lines = [
        "# EchoSAT Symmetry GRPO v1 Offline Reward Table",
        "",
        "This is a dry-run reward ledger from canonical v1.2 low-warmup runtime. It does not train a model and does not claim speedup.",
        "",
        "## Artifacts",
        "",
        f"- reward table CSV: `{display_path(out_csv)}`",
        f"- summary CSV: `{display_path(summary_csv)}`",
        "",
        "## Summary",
        "",
        *markdown_table(summary[summary["level"].isin(["overall", "by_warmup", "by_family"])], max_rows=80),
        "",
        "## Key Symmetry/Failure Bases",
        "",
        *markdown_table(
            key_bases[
                [
                    "warmup_conflicts",
                    "family",
                    "base_instance_id",
                    "variant",
                    "repeat_id",
                    "symmetry_grpo_v1_reward",
                    "search_reward_raw",
                    "symmetry_evidence_score",
                    "permutation_consistency_delta",
                    "adapter_cached_decisions_delta",
                    "adapter_cached_conflicts_delta",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Top Positive Rows",
        "",
        *markdown_table(
            positive[
                [
                    "warmup_conflicts",
                    "family",
                    "base_instance_id",
                    "variant",
                    "repeat_id",
                    "symmetry_grpo_v1_reward",
                    "search_reward_raw",
                    "symmetry_evidence_score",
                ]
            ],
            max_rows=30,
        ),
        "",
        "## Top Negative Rows",
        "",
        *markdown_table(
            negative[
                [
                    "warmup_conflicts",
                    "family",
                    "base_instance_id",
                    "variant",
                    "repeat_id",
                    "symmetry_grpo_v1_reward",
                    "search_reward_raw",
                    "random_control_mask",
                    "permutation_consistency_delta",
                    "control_perturbation_score",
                ]
            ],
            max_rows=30,
        ),
        "",
        "## Reading Rules",
        "",
        "- Positive reward requires adapter-vs-cached search reduction and symmetry evidence.",
        "- Random controls have `symmetry_evidence_score = 0` and cannot earn symmetry-positive reward.",
        "- Formula-equivalent and permutation-paired direction disagreement enters `permutation_consistency_delta`.",
        "- Adapter-vs-plain protocol time is retained as a diagnostic field, not a reward term.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build offline EchoSAT Symmetry GRPO v1 reward table.")
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--orbit-overlap", type=Path, default=DEFAULT_ORBIT_OVERLAP)
    parser.add_argument("--targeted-orbits", type=Path, default=DEFAULT_TARGETED_ORBITS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--decisions-weight", type=float, default=0.55)
    parser.add_argument("--conflicts-weight", type=float, default=0.45)
    parser.add_argument("--cpu-weight", type=float, default=0.15)
    parser.add_argument("--random-control-penalty-weight", type=float, default=2.0)
    parser.add_argument("--control-perturbation-penalty-weight", type=float, default=1.0)
    parser.add_argument("--permutation-penalty-weight", type=float, default=0.15)
    parser.add_argument("--weighted-risk-penalty-weight", type=float, default=0.5)
    parser.add_argument("--near-cap-penalty-weight", type=float, default=0.25)
    parser.add_argument("--phase-shift-penalty-weight", type=float, default=0.2)
    parser.add_argument("--reduction-clip", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    table = build_reward_table(
        pd.read_csv(resolve(args.observations)),
        manifest_summary(resolve(args.manifest)),
        load_orbit_overlap(resolve(args.orbit_overlap)),
        load_targeted_orbits(resolve(args.targeted_orbits)),
        decisions_weight=float(args.decisions_weight),
        conflicts_weight=float(args.conflicts_weight),
        cpu_weight=float(args.cpu_weight),
        random_control_penalty_weight=float(args.random_control_penalty_weight),
        control_perturbation_penalty_weight=float(args.control_perturbation_penalty_weight),
        permutation_penalty_weight=float(args.permutation_penalty_weight),
        weighted_risk_penalty_weight=float(args.weighted_risk_penalty_weight),
        near_cap_penalty_weight=float(args.near_cap_penalty_weight),
        phase_shift_penalty_weight=float(args.phase_shift_penalty_weight),
        reduction_clip=float(args.reduction_clip),
    )
    summary = summarize(table)
    out = resolve(args.out)
    summary_path = resolve(args.summary)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False)
    summary.to_csv(summary_path, index=False)
    write_doc(resolve(args.doc), table=table, summary=summary, out_csv=out, summary_csv=summary_path)
    print(f"wrote {out}")
    print(f"wrote {summary_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
