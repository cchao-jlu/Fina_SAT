from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import yaml
except Exception:  # pragma: no cover - PyYAML is expected in the training env.
    yaml = None


ROOT = Path(__file__).resolve().parent

DEFAULT_RUN_DIR = ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest"
DEFAULT_HYDRA_DIR = ROOT / "outputs/2026-06-22/18-25-41"
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter0_iter15_observations.csv"
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv"
DEFAULT_OUT_PREFIX = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_4_reward_replay_audit.md"

ANCHOR_BASES = {"k9_color8", "php_p9_h8"}
HARD_NEGATIVE_BASES = {"k10_color9", "php_p10_h9"}
SUBSET_FAILURE_BASE = "subset_cardinality_bw12"
SUBSET_FAILURE_VARIANT = "perm_seed1730"


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def cfg_get(mapping: dict[str, Any], key: str, default: Any) -> Any:
    value = mapping
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=np.float64)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(np.float64)


def bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False).astype(bool)
    return series.fillna(False).astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def target_role(row: pd.Series) -> str:
    base = str(row.get("base_instance_id", ""))
    variant = str(row.get("variant", ""))
    family = str(row.get("family", ""))
    control_type = str(row.get("control_type", ""))
    if family == "random_3sat_control" or control_type == "non_symmetric_control":
        return "random_control"
    if base in ANCHOR_BASES:
        return "anchor"
    if base in HARD_NEGATIVE_BASES:
        return "hard_negative"
    if base == SUBSET_FAILURE_BASE and variant == SUBSET_FAILURE_VARIANT:
        return "subset_failure"
    if base == SUBSET_FAILURE_BASE:
        return "subset_other"
    return "other"


def markdown_table(frame: pd.DataFrame, max_rows: int = 30) -> list[str]:
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


def source_inventory(run_dir: Path, hydra_dir: Path) -> pd.DataFrame:
    candidates = [
        ("run_training_config", run_dir / "training_config.yaml"),
        ("run_config", run_dir / "config.yaml"),
        ("hydra_config", hydra_dir / ".hydra/config.yaml"),
        ("hydra_overrides", hydra_dir / ".hydra/overrides.yaml"),
        ("hydra_train_log", hydra_dir / "train_rlaf.log"),
        ("run_solver_stats", run_dir / "solver_stats.csv"),
        ("run_training_solver_stats", run_dir / "training_solver_stats.csv"),
        ("run_reward_replay", run_dir / "reward_replay.csv"),
    ]
    rows = []
    for name, path in candidates:
        exists = path.exists()
        rows.append(
            {
                "artifact": name,
                "path": display_path(path),
                "exists": bool(exists),
                "size_bytes": int(path.stat().st_size) if exists else 0,
                "usable_for_per_sample_training_replay": bool(
                    exists
                    and path.stat().st_size > 0
                    and path.name.endswith(".csv")
                    and "solver_stats" in path.name
                ),
            }
        )
    return pd.DataFrame(rows)


def manifest_train_rows(manifest: pd.DataFrame) -> pd.DataFrame:
    out = manifest.copy()
    if "split" in out.columns:
        out = out[out["split"].astype(str).eq("train")].copy()
    if out.empty:
        out = manifest.copy()
    out["echosat_sampling_group_id"] = out.get("echosat_sampling_group_id", out["base_instance_id"]).fillna(out["base_instance_id"]).astype(str)
    out["control_type"] = out.get("control_type", pd.Series("", index=out.index)).fillna("").astype(str)
    out["training_priority"] = pd.to_numeric(out.get("training_priority", pd.Series(0.0, index=out.index)), errors="coerce").fillna(0.0)
    return out


def group_role(group: pd.DataFrame) -> str:
    if group["control_type"].astype(str).eq("non_symmetric_control").any() or group["family"].astype(str).eq("random_3sat_control").any():
        return "control"
    if pd.to_numeric(group.get("training_priority", pd.Series(0.0, index=group.index)), errors="coerce").fillna(0.0).max() > 0.0:
        return "priority"
    return "symmetry"


def simulate_group_sampling(manifest: pd.DataFrame, cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = manifest_train_rows(manifest)
    group_col = str(cfg_get(cfg, "training.echosat_group_column", "echosat_sampling_group_id"))
    if group_col not in train.columns:
        group_col = "base_instance_id"
    group_count = int(cfg_get(cfg, "training.echosat_base_groups_per_iter", 4))
    control_count = max(0, min(int(cfg_get(cfg, "training.echosat_control_base_groups_per_iter", 1)), group_count))
    priority_count = max(0, min(int(cfg_get(cfg, "training.echosat_priority_groups_per_iter", 2)), group_count - control_count))
    iterations = int(cfg_get(cfg, "training.iterations", 120))
    seed = int(cfg_get(cfg, "training.echosat_base_group_seed", cfg_get(cfg, "seed", 0)))

    group_rows = []
    for group_id, group in train.groupby(group_col, sort=True):
        group_rows.append(
            {
                "group_id": str(group_id),
                "group_role": group_role(group),
                "rows": int(len(group)),
                "bases": int(group["base_instance_id"].nunique()),
                "variants": int(group["variant"].nunique()) if "variant" in group.columns else int(len(group)),
                "families": ",".join(sorted(group["family"].dropna().astype(str).unique())) if "family" in group.columns else "",
                "base_instance_ids": ",".join(sorted(group["base_instance_id"].dropna().astype(str).unique())),
                "training_priority_max": float(pd.to_numeric(group.get("training_priority", pd.Series(0.0, index=group.index)), errors="coerce").fillna(0.0).max()),
                "formula_equivalence_group": ",".join(sorted(group.get("formula_equivalence_group", pd.Series("", index=group.index)).dropna().astype(str).unique())),
            }
        )
    group_summary = pd.DataFrame(group_rows)

    control_groups = group_summary[group_summary["group_role"].eq("control")]["group_id"].tolist()
    priority_groups = group_summary[group_summary["group_role"].eq("priority")]["group_id"].tolist()
    symmetry_groups = group_summary[group_summary["group_role"].eq("symmetry")]["group_id"].tolist()
    all_groups = group_summary["group_id"].tolist()

    def choose(rng: np.random.Generator, values: list[str], count: int) -> list[str]:
        if count <= 0 or not values:
            return []
        count = min(count, len(values))
        return list(rng.choice(np.asarray(values, dtype=object), size=count, replace=False))

    iter_rows = []
    for iteration in range(iterations):
        rng = np.random.default_rng(seed + iteration)
        selected: list[str] = []
        selected += choose(rng, control_groups, control_count)
        selected += choose(rng, [g for g in priority_groups if g not in set(selected)], priority_count)
        selected += choose(rng, [g for g in symmetry_groups if g not in set(selected)], group_count - len(selected))
        if len(selected) < group_count:
            selected += choose(rng, [g for g in all_groups if g not in set(selected)], group_count - len(selected))
        for rank, group_id in enumerate(selected):
            row = group_summary[group_summary["group_id"].eq(group_id)].iloc[0].to_dict()
            row.update({"iteration": int(iteration), "selection_rank": int(rank)})
            iter_rows.append(row)
    iteration_table = pd.DataFrame(iter_rows)
    selected_counts = (
        iteration_table.groupby("group_id", sort=True)
        .agg(
            selected_iterations=("iteration", "nunique"),
            selected_rows=("iteration", "size"),
        )
        .reset_index()
    )
    group_summary = group_summary.merge(selected_counts, on="group_id", how="left")
    group_summary["selected_iterations"] = group_summary["selected_iterations"].fillna(0).astype(int)
    group_summary["selection_rate"] = group_summary["selected_iterations"] / max(iterations, 1)

    integrity_rows = []
    for group_id in ["formula_equiv_k9_php_p9", "formula_equiv_k10_php_p10", "subset_cardinality_bw12"]:
        rows = train[train[group_col].astype(str).eq(group_id)]
        integrity_rows.append(
            {
                "group_id": group_id,
                "present_in_train_manifest": bool(not rows.empty),
                "rows": int(len(rows)),
                "bases": int(rows["base_instance_id"].nunique()) if not rows.empty else 0,
                "variants": int(rows["variant"].nunique()) if not rows.empty and "variant" in rows.columns else 0,
                "selected_iterations": int(group_summary.loc[group_summary["group_id"].eq(group_id), "selected_iterations"].iloc[0])
                if bool(group_summary["group_id"].eq(group_id).any())
                else 0,
                "selected_together_at_iteration_level": bool(not rows.empty and rows["base_instance_id"].nunique() >= 1),
                "grpo_advantage_normalization_group": "cnf_id",
                "paired_variants_share_grpo_advantage_group": False,
            }
        )
    return iteration_table, group_summary, pd.DataFrame(integrity_rows)


def group_direction_penalty(frame: pd.DataFrame, group_col: str, sign: np.ndarray, magnitude: np.ndarray, negative_scale: float, positive_scale: float) -> tuple[np.ndarray, np.ndarray]:
    penalty = np.zeros(len(frame), dtype=np.float64)
    mixed = np.zeros(len(frame), dtype=bool)
    if group_col not in frame.columns:
        return penalty, mixed
    temp = pd.DataFrame({"group": frame[group_col].fillna("").astype(str).to_numpy(), "sign": sign, "idx": np.arange(len(frame))})
    temp = temp[temp["group"].ne("")]
    for _, group in temp.groupby("group", sort=False):
        signs = group["sign"].to_numpy(dtype=np.float64)
        if not ((signs > 0.0).any() and (signs < 0.0).any()):
            continue
        idx = group["idx"].to_numpy(dtype=np.int64)
        row_scale = np.where(sign[idx] < 0.0, negative_scale, positive_scale)
        penalty[idx] += row_scale * magnitude[idx]
        mixed[idx] = True
    return penalty, mixed


def compute_proxy_replay(observations: pd.DataFrame, manifest: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    out = observations.copy()
    meta_cols = [
        "base_instance_id",
        "variant",
        "valid_orbit_count",
        "orbit_confidence_mean",
        "orbit_confidence_max",
        "formula_equivalence_group",
        "echosat_sampling_group_id",
        "training_priority",
    ]
    meta = manifest[[c for c in meta_cols if c in manifest.columns]].drop_duplicates(["base_instance_id", "variant"])
    out = out.merge(meta, on=["base_instance_id", "variant"], how="left")
    out["target_role"] = out.apply(target_role, axis=1)

    eps = float(cfg_get(cfg, "training.echosat_ratio_eps", 1.0e-6))
    clip = float(cfg_get(cfg, "training.echosat_delta_clip", 1.0))
    cap = float(cfg_get(cfg, "solver.params.cpu-lim", 5.0))
    static_threshold = float(cfg_get(cfg, "training.echosat_static_risk_threshold", 0.1))
    near_cap_fraction = float(cfg_get(cfg, "training.echosat_near_cap_fraction", 0.8))

    adapter_cpu = numeric(out, "event_adapter_final_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    adapter_decisions = numeric(out, "event_adapter_final_final_decisions", 0.0).to_numpy(dtype=np.float64)
    adapter_conflicts = numeric(out, "event_adapter_final_final_conflicts", 0.0).to_numpy(dtype=np.float64)
    static_cpu = numeric(out, "static_weighted_glucose_final_cpu_time", 0.0).to_numpy(dtype=np.float64)
    static_decisions = numeric(out, "static_weighted_glucose_final_decisions", 0.0).to_numpy(dtype=np.float64)
    static_conflicts = numeric(out, "static_weighted_glucose_final_conflicts", 0.0).to_numpy(dtype=np.float64)
    neutral_cpu = numeric(out, "neutral_weighted_glucose_final_cpu_time", np.nan).to_numpy(dtype=np.float64)

    decision_delta = adapter_decisions - static_decisions
    conflict_delta = adapter_conflicts - static_conflicts
    cpu_delta = adapter_cpu - static_cpu
    decision_reduction = np.clip(-decision_delta / np.maximum(static_decisions, 1.0), -clip, clip)
    conflict_reduction = np.clip(-conflict_delta / np.maximum(static_conflicts, 1.0), -clip, clip)
    cpu_reduction = np.clip(
        -cpu_delta / np.maximum(static_cpu, eps),
        -float(cfg_get(cfg, "training.echosat_cpu_reduction_clip", 0.05)),
        float(cfg_get(cfg, "training.echosat_cpu_reduction_clip", 0.05)),
    )

    eps_dec = float(cfg_get(cfg, "training.echosat_search_eps_decisions", 0.0))
    eps_conf = float(cfg_get(cfg, "training.echosat_search_eps_conflicts", 0.0))
    search_ok = (decision_delta < -eps_dec) & (conflict_delta < -eps_conf)
    search_blowup = (decision_delta > eps_dec) | (conflict_delta > eps_conf)

    r_dec = float(cfg_get(cfg, "training.echosat_decisions_weight", 0.55)) * np.maximum(decision_reduction, 0.0)
    r_conf = float(cfg_get(cfg, "training.echosat_conflicts_weight", 0.45)) * np.maximum(conflict_reduction, 0.0)
    r_cpu = float(cfg_get(cfg, "training.echosat_final_cpu_weight", 0.0)) * np.maximum(cpu_reduction, 0.0)
    decision_blowup = np.maximum(decision_delta, 0.0) / np.maximum(static_decisions, 1.0)
    conflict_blowup = np.maximum(conflict_delta, 0.0) / np.maximum(static_conflicts, 1.0)
    search_blowup_penalty = (
        float(cfg_get(cfg, "training.echosat_decision_blowup_penalty_weight", 2.5)) * np.clip(decision_blowup, 0.0, clip)
        + float(cfg_get(cfg, "training.echosat_conflict_blowup_penalty_weight", 2.5)) * np.clip(conflict_blowup, 0.0, clip)
    )

    family = out["family"].astype(str)
    control_type = out.get("control_type", pd.Series("", index=out.index)).fillna("").astype(str)
    symmetry_strength = out.get("symmetry_strength", pd.Series("", index=out.index)).fillna("").astype(str)
    is_control = family.eq("random_3sat_control") | control_type.eq("non_symmetric_control") | symmetry_strength.eq("none")
    valid_orbits = numeric(out, "valid_orbit_count", 0.0).to_numpy(dtype=np.float64)
    orbit_conf = numeric(out, "orbit_confidence_mean", 0.0).to_numpy(dtype=np.float64)
    event_l2 = numeric(out, "event_state_l2_sum", 0.0).to_numpy(dtype=np.float64)
    event_nonzero = numeric(out, "event_state_nonzero_vars", 0.0).to_numpy(dtype=np.float64)
    tau_event = float(cfg_get(cfg, "training.echosat_event_tau", 0.0))
    event_gate = 1.0 / (1.0 + np.exp(-(np.log1p(event_l2) - tau_event)))
    explicit_event_gate = ((event_l2 > 0.0) | (event_nonzero > 0.0)).astype(np.float64)
    e_sym = (~is_control).to_numpy(dtype=np.float64) * (valid_orbits > 0.0).astype(np.float64) * orbit_conf * event_gate * explicit_event_gate
    e_sym = np.clip(e_sym, 0.0, 1.0)

    if np.all(np.isnan(neutral_cpu)):
        static_weighted_risk = np.zeros(len(out), dtype=np.float64)
    else:
        static_weighted_risk = np.maximum(0.0, ((static_cpu - neutral_cpu) / np.maximum(neutral_cpu, eps)) - static_threshold)
    near_cap = np.maximum.reduce([adapter_cpu / max(cap, eps), static_cpu / max(cap, eps), np.nan_to_num(neutral_cpu / max(cap, eps), nan=0.0)])
    cap_risk = np.maximum(0.0, near_cap - near_cap_fraction)
    weighted_risk = static_weighted_risk + cap_risk
    near_cap_mask = near_cap >= near_cap_fraction

    perturbation = np.zeros(len(out), dtype=np.float64)
    positive_allowed = search_ok & (~is_control.to_numpy(dtype=bool)) & (e_sym > 0.0) & (~near_cap_mask) & (
        weighted_risk <= float(cfg_get(cfg, "training.echosat_weighted_risk_positive_threshold", 0.0))
    )
    positive_reward = positive_allowed.astype(np.float64) * e_sym * (r_dec + r_conf + r_cpu)

    out["formula_equivalence_group"] = out.get("formula_equivalence_group", pd.Series("", index=out.index)).fillna("").astype(str)
    out["echosat_sampling_group_id"] = out.get("echosat_sampling_group_id", out["base_instance_id"]).fillna(out["base_instance_id"]).astype(str)
    out["base_group"] = out["base_instance_id"].fillna("").astype(str)
    search_sign = np.where(search_ok, 1.0, np.where(search_blowup, -1.0, 0.0))
    inconsistency_magnitude = search_blowup_penalty + np.abs(decision_reduction) + np.abs(conflict_reduction) + positive_reward
    direction_penalty = np.zeros(len(out), dtype=np.float64)
    mixed_group_mask = np.zeros(len(out), dtype=bool)
    neg_scale = float(cfg_get(cfg, "training.echosat_mixed_group_negative_scale", 2.0))
    pos_scale = float(cfg_get(cfg, "training.echosat_mixed_group_positive_scale", 1.0))
    # The training code computes these penalties over the current iteration frame.
    # This proxy scopes them per checkpoint/warmup to avoid mixing unrelated runs.
    for _, idx_frame in out.groupby(["checkpoint", "warmup_conflicts"], sort=False):
        idx = idx_frame.index.to_numpy(dtype=np.int64)
        local = out.loc[idx].reset_index(drop=True)
        local_sign = search_sign[idx]
        local_mag = inconsistency_magnitude[idx]
        for col in ["base_group", "formula_equivalence_group", "echosat_sampling_group_id"]:
            penalty, mixed = group_direction_penalty(local, col, local_sign, local_mag, neg_scale, pos_scale)
            direction_penalty[idx] += penalty
            mixed_group_mask[idx] |= mixed

    if bool(cfg_get(cfg, "training.echosat_suppress_mixed_group_positive", True)):
        positive_allowed = positive_allowed & (~mixed_group_mask)
        positive_reward = positive_allowed.astype(np.float64) * e_sym * (r_dec + r_conf + r_cpu)

    base_group = out["base_instance_id"].fillna("").astype(str)
    variant = out["variant"].fillna("").astype(str)
    hard_negative_mask = base_group.isin(set(cfg_get(cfg, "training.echosat_hard_negative_base_ids", list(HARD_NEGATIVE_BASES)))).to_numpy(dtype=bool)
    anchor_mask = base_group.isin(set(cfg_get(cfg, "training.echosat_anchor_base_ids", list(ANCHOR_BASES)))).to_numpy(dtype=bool)
    subset_failure_mask = (
        base_group.eq(str(cfg_get(cfg, "training.echosat_subset_failure_base_id", SUBSET_FAILURE_BASE))).to_numpy(dtype=bool)
        & variant.eq(str(cfg_get(cfg, "training.echosat_subset_failure_variant", SUBSET_FAILURE_VARIANT))).to_numpy(dtype=bool)
    )

    if bool(cfg_get(cfg, "training.echosat_suppress_subset_failure_positive", True)):
        positive_allowed = positive_allowed & (~subset_failure_mask)
        positive_reward = positive_allowed.astype(np.float64) * e_sym * (r_dec + r_conf + r_cpu)

    hard_negative_penalty = hard_negative_mask.astype(np.float64) * search_blowup.astype(np.float64) * (
        search_blowup_penalty + direction_penalty + np.abs(decision_reduction) + np.abs(conflict_reduction)
    )
    anchor_failure_penalty = anchor_mask.astype(np.float64) * (~search_ok).astype(np.float64) * (
        search_blowup_penalty
        + np.maximum(0.0, -decision_reduction)
        + np.maximum(0.0, -conflict_reduction)
        + float(cfg_get(cfg, "training.echosat_anchor_failure_floor", 0.25))
    )
    subset_failure_penalty = subset_failure_mask.astype(np.float64) * search_ok.astype(np.float64) * (
        r_dec + r_conf + r_cpu + search_blowup_penalty + float(cfg_get(cfg, "training.echosat_subset_failure_floor", 1.0))
    )

    random_control_penalty = is_control.to_numpy(dtype=np.float64) * np.maximum(search_blowup_penalty + positive_reward, perturbation)
    unsupported_positive_penalty = (e_sym <= 0.0).astype(np.float64) * (r_dec + r_conf + r_cpu)
    weighted_path_risk_penalty = weighted_risk * (1.0 + perturbation)
    near_cap_penalty = near_cap_mask.astype(np.float64) * (r_dec + r_conf + r_cpu + search_blowup_penalty)
    large_weight_phase_shift_penalty = perturbation * (1.0 - e_sym)

    reward = positive_reward - search_blowup_penalty
    reward -= float(cfg_get(cfg, "training.echosat_random_control_penalty_weight", 5.0)) * random_control_penalty
    reward -= float(cfg_get(cfg, "training.echosat_control_penalty_weight", 2.5)) * is_control.to_numpy(dtype=np.float64) * perturbation
    reward -= float(cfg_get(cfg, "training.echosat_permutation_delta_weight", 3.0)) * direction_penalty
    reward -= float(cfg_get(cfg, "training.echosat_weighted_risk_weight", 1.25)) * weighted_path_risk_penalty
    reward -= float(cfg_get(cfg, "training.echosat_near_cap_penalty_weight", 1.0)) * near_cap_penalty
    reward -= float(cfg_get(cfg, "training.echosat_delta_magnitude_weight", 0.5)) * unsupported_positive_penalty
    reward -= float(cfg_get(cfg, "training.echosat_large_weight_phase_shift_penalty_weight", 1.25)) * large_weight_phase_shift_penalty
    reward -= float(cfg_get(cfg, "training.echosat_hard_negative_penalty_weight", 3.0)) * hard_negative_penalty
    reward -= float(cfg_get(cfg, "training.echosat_anchor_failure_penalty_weight", 2.0)) * anchor_failure_penalty
    reward -= float(cfg_get(cfg, "training.echosat_subset_failure_penalty_weight", 3.0)) * subset_failure_penalty

    cost = -reward
    advantage_weight = np.zeros(len(out), dtype=np.float64)
    advantage_weight[symmetry_strength.eq("strong").to_numpy()] = float(cfg_get(cfg, "training.echosat_strong_advantage_weight", 1.0))
    advantage_weight[symmetry_strength.eq("weak").to_numpy()] = float(cfg_get(cfg, "training.echosat_weak_advantage_weight", 0.6))
    non_control = ~is_control.to_numpy(dtype=bool)
    advantage_weight[non_control] *= np.clip(e_sym[non_control], 0.0, 1.0)
    # Mirrors the current v1.4 branch: controls get weight 1.0, then positive
    # advantages are supposed to be removed by advantage_upper_bound.
    advantage_weight[is_control.to_numpy(dtype=bool)] = 1.0
    advantage_upper_bound = np.full(len(out), np.inf, dtype=np.float64)
    advantage_upper_bound[~positive_allowed] = 0.0
    advantage_upper_bound[reward <= 0.0] = 0.0

    raw_adv = np.zeros(len(out), dtype=np.float64)
    group_mean = np.zeros(len(out), dtype=np.float64)
    group_std = np.zeros(len(out), dtype=np.float64)
    proxy_group = (
        out["checkpoint"].astype(str)
        + "::wc"
        + out["warmup_conflicts"].astype(str)
        + "::"
        + out["base_instance_id"].astype(str)
        + "::"
        + out["variant"].astype(str)
    )
    for _, group in pd.DataFrame({"group": proxy_group, "cost": cost, "idx": np.arange(len(out))}).groupby("group", sort=False):
        values = group["cost"].to_numpy(dtype=np.float64)
        mean = float(np.nanmean(values))
        std = float(np.nanstd(values, ddof=1)) if len(values) > 1 else 0.0
        idx = group["idx"].to_numpy(dtype=np.int64)
        group_mean[idx] = mean
        group_std[idx] = std
        if math.isfinite(std) and std > 1.0e-8:
            raw_adv[idx] = -((values - mean) / (std + 1.0e-8))
    weighted_adv = raw_adv * advantage_weight
    final_adv = np.minimum(weighted_adv, advantage_upper_bound)
    final_adv = np.nan_to_num(final_adv, nan=0.0, posinf=0.0, neginf=0.0)

    out["training_baseline_used_by_current_code"] = "static_weighted_glucose"
    out["acceptance_primary_baseline"] = "cached_trace_no_adapter_final"
    out["static_adapter_decisions_delta"] = decision_delta
    out["static_adapter_conflicts_delta"] = conflict_delta
    out["static_adapter_final_cpu_delta"] = cpu_delta
    out["static_search_ok"] = search_ok
    out["static_search_blowup"] = search_blowup
    out["cached_search_ok"] = (numeric(out, "adapter_cached_decisions_delta", 0.0).to_numpy(dtype=np.float64) < 0.0) & (
        numeric(out, "adapter_cached_conflicts_delta", 0.0).to_numpy(dtype=np.float64) < 0.0
    )
    out["echosat_e_sym_proxy"] = e_sym
    out["echosat_positive_allowed"] = positive_allowed
    out["echosat_r_search_decisions"] = r_dec
    out["echosat_r_search_conflicts"] = r_conf
    out["echosat_r_cpu_clipped"] = r_cpu
    out["echosat_positive_reward"] = positive_reward
    out["echosat_search_blowup_penalty"] = search_blowup_penalty
    out["echosat_random_control_penalty"] = random_control_penalty
    out["echosat_direction_consistency_penalty"] = direction_penalty
    out["echosat_group_mixed_direction"] = mixed_group_mask
    out["echosat_hard_negative_candidate"] = hard_negative_mask
    out["echosat_hard_negative_penalty"] = hard_negative_penalty
    out["echosat_anchor_candidate"] = anchor_mask
    out["echosat_anchor_failure_penalty"] = anchor_failure_penalty
    out["echosat_subset_failure_candidate"] = subset_failure_mask
    out["echosat_subset_failure_penalty"] = subset_failure_penalty
    out["echosat_weighted_path_risk_penalty"] = weighted_path_risk_penalty
    out["echosat_near_cap_penalty"] = near_cap_penalty
    out["echosat_large_weight_phase_shift_penalty"] = large_weight_phase_shift_penalty
    out["echosat_reward_proxy"] = reward
    out["echosat_cost_proxy"] = cost
    out["grpo_proxy_group_id"] = proxy_group
    out["grpo_group_mean_cost_proxy"] = group_mean
    out["grpo_group_std_cost_proxy"] = group_std
    out["grpo_raw_advantage_proxy"] = raw_adv
    out["echosat_advantage_weight_proxy"] = advantage_weight
    out["echosat_advantage_upper_bound_proxy"] = advantage_upper_bound
    out["grpo_weighted_advantage_proxy_before_clamp"] = weighted_adv
    out["grpo_final_advantage_proxy"] = final_adv
    out["raw_positive_advantage"] = raw_adv > 1.0e-12
    out["weighted_positive_advantage_before_clamp"] = weighted_adv > 1.0e-12
    out["final_positive_advantage"] = final_adv > 1.0e-12
    out["positive_advantage_clamped_to_zero"] = (weighted_adv > 1.0e-12) & (final_adv <= 1.0e-12)
    out["parameter_shift_available_in_proxy"] = False
    return out


def summarize_roles(replay: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in replay.groupby(["checkpoint", "warmup_conflicts", "target_role"], sort=True):
        checkpoint, warmup, role = keys
        rows.append(
            {
                "checkpoint": checkpoint,
                "warmup_conflicts": int(warmup),
                "target_role": role,
                "rows": int(len(group)),
                "bases": int(group["base_instance_id"].nunique()),
                "static_search_ok_frac": float(bool_series(group["static_search_ok"]).mean()),
                "cached_search_ok_frac": float(bool_series(group["cached_search_ok"]).mean()),
                "positive_allowed_frac": float(bool_series(group["echosat_positive_allowed"]).mean()),
                "reward_mean": float(group["echosat_reward_proxy"].mean()),
                "reward_min": float(group["echosat_reward_proxy"].min()),
                "raw_positive_advantage_frac": float(bool_series(group["raw_positive_advantage"]).mean()),
                "weighted_positive_before_clamp_frac": float(bool_series(group["weighted_positive_advantage_before_clamp"]).mean()),
                "final_positive_advantage_frac": float(bool_series(group["final_positive_advantage"]).mean()),
                "positive_advantage_clamped_rows": int(bool_series(group["positive_advantage_clamped_to_zero"]).sum()),
                "random_control_penalty_mean": float(group["echosat_random_control_penalty"].mean()),
                "anchor_failure_penalty_mean": float(group["echosat_anchor_failure_penalty"].mean()),
                "hard_negative_penalty_mean": float(group["echosat_hard_negative_penalty"].mean()),
                "subset_failure_penalty_mean": float(group["echosat_subset_failure_penalty"].mean()),
                "direction_penalty_mean": float(group["echosat_direction_consistency_penalty"].mean()),
            }
        )
    return pd.DataFrame(rows)


def summarize_base(replay: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in replay.groupby(["checkpoint", "warmup_conflicts", "family", "base_instance_id"], sort=True):
        checkpoint, warmup, family, base = keys
        rows.append(
            {
                "checkpoint": checkpoint,
                "warmup_conflicts": int(warmup),
                "family": family,
                "base_instance_id": base,
                "target_role": ",".join(sorted(group["target_role"].dropna().astype(str).unique())),
                "rows": int(len(group)),
                "variants": int(group["variant"].nunique()),
                "static_search_ok_frac": float(bool_series(group["static_search_ok"]).mean()),
                "cached_search_ok_frac": float(bool_series(group["cached_search_ok"]).mean()),
                "final_positive_advantage_frac": float(bool_series(group["final_positive_advantage"]).mean()),
                "raw_positive_advantage_frac": float(bool_series(group["raw_positive_advantage"]).mean()),
                "positive_advantage_clamped_rows": int(bool_series(group["positive_advantage_clamped_to_zero"]).sum()),
                "reward_mean": float(group["echosat_reward_proxy"].mean()),
                "static_decisions_delta_mean": float(group["static_adapter_decisions_delta"].mean()),
                "static_conflicts_delta_mean": float(group["static_adapter_conflicts_delta"].mean()),
                "cached_decisions_delta_mean": float(group["adapter_cached_decisions_delta"].mean()),
                "cached_conflicts_delta_mean": float(group["adapter_cached_conflicts_delta"].mean()),
            }
        )
    return pd.DataFrame(rows)


def failure_rows(replay: pd.DataFrame) -> pd.DataFrame:
    bad = (
        replay["target_role"].isin(["random_control", "subset_failure"])
        | (replay["target_role"].eq("anchor") & ~bool_series(replay["cached_search_ok"]))
        | (replay["target_role"].eq("hard_negative") & bool_series(replay["static_search_blowup"]))
    )
    interesting = bad & (bool_series(replay["raw_positive_advantage"]) | bool_series(replay["weighted_positive_advantage_before_clamp"]) | bool_series(replay["final_positive_advantage"]) | bool_series(replay["positive_advantage_clamped_to_zero"]))
    cols = [
        "checkpoint",
        "warmup_conflicts",
        "family",
        "base_instance_id",
        "variant",
        "repeat_id",
        "target_role",
        "static_search_ok",
        "cached_search_ok",
        "echosat_positive_allowed",
        "echosat_reward_proxy",
        "grpo_group_mean_cost_proxy",
        "grpo_group_std_cost_proxy",
        "grpo_raw_advantage_proxy",
        "echosat_advantage_weight_proxy",
        "grpo_weighted_advantage_proxy_before_clamp",
        "echosat_advantage_upper_bound_proxy",
        "grpo_final_advantage_proxy",
        "positive_advantage_clamped_to_zero",
        "echosat_anchor_failure_penalty",
        "echosat_hard_negative_penalty",
        "echosat_random_control_penalty",
        "echosat_direction_consistency_penalty",
        "static_adapter_decisions_delta",
        "static_adapter_conflicts_delta",
        "adapter_cached_decisions_delta",
        "adapter_cached_conflicts_delta",
    ]
    return replay.loc[interesting, [c for c in cols if c in replay.columns]].sort_values(
        ["checkpoint", "warmup_conflicts", "target_role", "base_instance_id", "variant", "repeat_id"]
    )


def write_doc(
    path: Path,
    *,
    inventory: pd.DataFrame,
    replay: pd.DataFrame,
    role_summary: pd.DataFrame,
    base_summary: pd.DataFrame,
    sampling_summary: pd.DataFrame,
    group_integrity: pd.DataFrame,
    failures: pd.DataFrame,
    outputs: dict[str, Path],
) -> None:
    usable_training = bool(inventory["usable_for_per_sample_training_replay"].any())
    train_log = inventory[inventory["artifact"].eq("hydra_train_log")]
    train_log_size = int(train_log["size_bytes"].iloc[0]) if not train_log.empty else 0
    control_roles = role_summary[role_summary["target_role"].eq("random_control")]
    anchor_roles = role_summary[role_summary["target_role"].eq("anchor")]
    hard_roles = role_summary[role_summary["target_role"].eq("hard_negative")]
    subset_roles = role_summary[role_summary["target_role"].eq("subset_failure")]
    target_bases = base_summary[
        base_summary["base_instance_id"].isin(["k9_color8", "php_p9_h8", "k10_color9", "php_p10_h9", "subset_cardinality_bw12"])
        | base_summary["family"].eq("random_3sat_control")
    ].sort_values(["checkpoint", "warmup_conflicts", "target_role", "base_instance_id"])
    selected_focus = sampling_summary[
        sampling_summary["group_id"].isin(["formula_equiv_k9_php_p9", "formula_equiv_k10_php_p10", "subset_cardinality_bw12"])
        | sampling_summary["group_role"].eq("control")
    ].sort_values(["group_role", "group_id"])

    lines = [
        "# EchoSAT Symmetry GRPO v1.4 Reward Replay Audit",
        "",
        "This audit does not train, rerun solver rollouts, expand benchmarks, or add a gate/selector.",
        "",
        "## Artifacts",
        "",
        *[f"- {name}: `{display_path(path)}`" for name, path in outputs.items()],
        "",
        "## Source Availability",
        "",
        *markdown_table(inventory, max_rows=20),
        "",
        f"- raw per-sample training solver_stats recoverable: `{usable_training}`",
        f"- Hydra train log size: `{train_log_size}` bytes",
        "- Because v1.4 did not persist per-iteration `solver_stats` and wandb was disabled, exact historical training-batch reward replay is not recoverable from disk. The replay below is a proxy over existing targeted acceptance rows using the current v1.4 reward/advantage equations.",
        "",
        "## Key Code-Level Findings",
        "",
        "- Current `symmetry_grpo_v1_4` reward code uses `static_weighted_glucose` final solve as the search-work baseline. In the current runtime protocol, `cached_trace_no_adapter_final` reuses the static final solve, so adapter-vs-cached and adapter-vs-static final decisions/conflicts are equivalent in these acceptance rows.",
        "- GRPO normalization is by `cnf_id`, not by `base_instance_id`, `formula_equivalence_group`, or `echosat_sampling_group_id`. Paired variants can be selected in the same iteration, but they do not share the GRPO mean/std normalization group.",
        "- In the v1.4 branch, controls receive `echosat_advantage_weight = 1.0` before the positive-advantage upper-bound clamp, even though config has `echosat_control_advantage_weight: 0.0`. The clamp prevents positive control advantages in this proxy, but controls still carry negative gradients.",
        "- Parameter-shift diagnostics are not available in the acceptance rows, so this proxy sets perturbation-derived penalties to zero. That underestimates control/phase-shift penalties relative to an exact live training batch.",
        "",
        "## Proxy Replay Scope",
        "",
        f"- rows: `{len(replay)}`",
        f"- checkpoints: `{', '.join(map(str, replay['checkpoint'].drop_duplicates().tolist()))}`",
        f"- warmup conflicts: `{', '.join(map(str, sorted(replay['warmup_conflicts'].drop_duplicates().astype(int).tolist())))}`",
        "",
        "## Role Advantage Summary",
        "",
        *markdown_table(
            role_summary[
                [
                    "checkpoint",
                    "warmup_conflicts",
                    "target_role",
                    "rows",
                    "static_search_ok_frac",
                    "cached_search_ok_frac",
                    "positive_allowed_frac",
                    "reward_mean",
                    "raw_positive_advantage_frac",
                    "weighted_positive_before_clamp_frac",
                    "final_positive_advantage_frac",
                    "positive_advantage_clamped_rows",
                    "anchor_failure_penalty_mean",
                    "hard_negative_penalty_mean",
                    "random_control_penalty_mean",
                    "direction_penalty_mean",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Target Base Summary",
        "",
        *markdown_table(
            target_bases[
                [
                    "checkpoint",
                    "warmup_conflicts",
                    "target_role",
                    "family",
                    "base_instance_id",
                    "rows",
                    "static_search_ok_frac",
                    "cached_search_ok_frac",
                    "raw_positive_advantage_frac",
                    "final_positive_advantage_frac",
                    "positive_advantage_clamped_rows",
                    "reward_mean",
                    "static_decisions_delta_mean",
                    "cached_decisions_delta_mean",
                ]
            ],
            max_rows=120,
        ),
        "",
        "## Positive Advantage Failure Rows",
        "",
        *markdown_table(failures, max_rows=80),
        "",
        "## Group Sampling Audit",
        "",
        *markdown_table(selected_focus[["group_id", "group_role", "rows", "bases", "variants", "selected_iterations", "selection_rate", "base_instance_ids"]], max_rows=80),
        "",
        "## Pair Integrity",
        "",
        *markdown_table(group_integrity, max_rows=20),
        "",
        "## Interpretation",
        "",
        "- Random controls do not receive final positive advantage in the proxy replay; positive raw/weighted cases are clamped to zero when the upper bound is active.",
        "- Anchor rows do not receive raw or final positive advantage in this proxy replay. Since v1.4 still degraded wc1 anchors by iter=15, the missing exact training-batch solver_stats are material: the failure is not explained by the targeted acceptance proxy alone.",
        "- Hard-negative recovery remains weak under the acceptance metric. Some hard-negative rows are search-positive relative to static weighted, which can be rewarded even when adapter-vs-cached acceptance is still mixed.",
        "- The main actionable issue for v1.5 is not best checkpoint selection alone. Paired ranking and anchor preservation should become direct training constraints, and random/control positive raw advantages should be impossible by construction rather than only removed by a late upper-bound clamp.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit v1.4 EchoSAT Symmetry GRPO reward/advantage replay from available artifacts.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--hydra-dir", type=Path, default=DEFAULT_HYDRA_DIR)
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-prefix", type=Path, default=DEFAULT_OUT_PREFIX)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = resolve(args.run_dir)
    hydra_dir = resolve(args.hydra_dir)
    observations_path = resolve(args.observations)
    manifest_path = resolve(args.manifest)
    out_prefix = resolve(args.out_prefix)
    doc_path = resolve(args.doc)

    cfg = load_yaml(run_dir / "training_config.yaml")
    if not cfg:
        cfg = load_yaml(hydra_dir / ".hydra/config.yaml")
    inventory = source_inventory(run_dir, hydra_dir)
    observations = pd.read_csv(observations_path)
    manifest = pd.read_csv(manifest_path)

    sampling_iterations, sampling_summary, group_integrity = simulate_group_sampling(manifest, cfg)
    replay = compute_proxy_replay(observations, manifest, cfg)
    role_summary = summarize_roles(replay)
    base_summary = summarize_base(replay)
    failures = failure_rows(replay)

    outputs = {
        "source inventory": out_prefix.with_name(out_prefix.name + "_source_inventory.csv"),
        "proxy replay table": out_prefix.with_name(out_prefix.name + "_proxy_table.csv"),
        "role summary": out_prefix.with_name(out_prefix.name + "_role_summary.csv"),
        "base summary": out_prefix.with_name(out_prefix.name + "_base_summary.csv"),
        "positive advantage failures": out_prefix.with_name(out_prefix.name + "_positive_advantage_failures.csv"),
        "group sampling iterations": out_prefix.with_name(out_prefix.name + "_group_sampling_iterations.csv"),
        "group sampling summary": out_prefix.with_name(out_prefix.name + "_group_sampling_summary.csv"),
        "group integrity": out_prefix.with_name(out_prefix.name + "_group_integrity.csv"),
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(outputs["source inventory"], index=False)
    replay.to_csv(outputs["proxy replay table"], index=False)
    role_summary.to_csv(outputs["role summary"], index=False)
    base_summary.to_csv(outputs["base summary"], index=False)
    failures.to_csv(outputs["positive advantage failures"], index=False)
    sampling_iterations.to_csv(outputs["group sampling iterations"], index=False)
    sampling_summary.to_csv(outputs["group sampling summary"], index=False)
    group_integrity.to_csv(outputs["group integrity"], index=False)

    write_doc(
        doc_path,
        inventory=inventory,
        replay=replay,
        role_summary=role_summary,
        base_summary=base_summary,
        sampling_summary=sampling_summary,
        group_integrity=group_integrity,
        failures=failures,
        outputs=outputs,
    )
    for name, path in outputs.items():
        print(f"wrote {name}: {path}")
    print(f"wrote doc: {doc_path}")


if __name__ == "__main__":
    main()
