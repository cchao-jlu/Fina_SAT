#!/usr/bin/env python3
"""Offline v1.6 reward replay from persisted v1.5 training batches."""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

import train_rlaf


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_5_WC1_PairStrict/reward_replay"
DEFAULT_OUT_PREFIX = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_6_reward_replay_dryrun"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_6_reward_replay_dryrun.md"
CONFIG_NAME = "config_train_rlaf_echosat_symmetry_grpo_v1_6_wc1_softpair"


def bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index, dtype=bool)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(False).astype(bool)
    return values.fillna(False).astype(str).str.lower().isin({"true", "1", "yes", "y"})


def numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=np.float64)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(np.float64)


def load_cfg():
    with initialize_config_dir(config_dir=str(ROOT / "configs"), version_base=None):
        cfg = compose(config_name=CONFIG_NAME)
    return cfg


def recompute_v16_from_v15_frame(frame: pd.DataFrame, cfg) -> pd.DataFrame:
    out = frame.copy()
    out["echosat_target_mode"] = "symmetry_grpo_v1_6"

    search_ok = bool_series(out, "echosat_search_ok").to_numpy(dtype=bool)
    search_blowup = bool_series(out, "echosat_search_blowup").to_numpy(dtype=bool)
    family = out.get("family", pd.Series("", index=out.index)).fillna("").astype(str)
    control_type = out.get("control_type", pd.Series("", index=out.index)).fillna("").astype(str)
    symmetry_strength = out.get("symmetry_strength", pd.Series("", index=out.index)).fillna("").astype(str)
    base = out.get("base_instance_id", pd.Series("", index=out.index)).fillna("").astype(str)
    variant = out.get("variant", pd.Series("", index=out.index)).fillna("").astype(str)

    is_control = (
        control_type.eq("non_symmetric_control")
        | symmetry_strength.eq("none")
        | family.eq("random_3sat_control")
    ).to_numpy(dtype=bool)
    non_control = ~is_control

    e_sym = numeric(out, "echosat_e_sym", 0.0).to_numpy(dtype=np.float64)
    weighted_risk = numeric(out, "echosat_weighted_risk", 0.0).to_numpy(dtype=np.float64)
    weighted_risk_ok = weighted_risk <= float(cfg.training.echosat_weighted_risk_positive_threshold)

    cpu = numeric(out, "CPU time", 0.0).to_numpy(dtype=np.float64)
    static_cpu = numeric(out, "baseline_static_cpu_time", 0.0).to_numpy(dtype=np.float64)
    neutral_cpu = numeric(out, "baseline_neutral_cpu_time", 0.0).replace([np.inf, -np.inf], np.nan).to_numpy(dtype=np.float64)
    cap = float(dict(cfg.solver.params).get("cpu-lim", cfg.training.get("echosat_cpu_cap", 5.0)))
    eps = float(cfg.training.echosat_ratio_eps)
    near_cap = np.maximum.reduce(
        [
            cpu / max(cap, eps),
            static_cpu / max(cap, eps),
            np.nan_to_num(neutral_cpu / max(cap, eps), nan=0.0),
        ]
    )
    near_cap_mask = near_cap >= float(cfg.training.echosat_near_cap_fraction)

    subset_base = str(cfg.training.echosat_subset_failure_base_id)
    subset_variant = str(cfg.training.echosat_subset_failure_variant)
    subset_failure = (base.eq(subset_base) & variant.eq(subset_variant)).to_numpy(dtype=bool)
    anchor_failure = bool_series(out, "echosat_anchor_failure").to_numpy(dtype=bool)
    hard_negative_failure = bool_series(out, "echosat_hard_negative_failure").to_numpy(dtype=bool)
    mixed_pair = bool_series(out, "echosat_group_mixed_direction").to_numpy(dtype=bool)

    positive_allowed_search = search_ok & non_control & (e_sym > 0.0)
    positive_allowed = positive_allowed_search & (~near_cap_mask) & weighted_risk_ok
    positive_allowed &= ~subset_failure
    positive_allowed &= ~anchor_failure
    positive_allowed &= ~hard_negative_failure
    if bool(cfg.training.echosat_v16_hard_block_mixed_positive):
        positive_allowed &= ~mixed_pair

    r_dec = numeric(out, "echosat_r_search_decisions", 0.0).to_numpy(dtype=np.float64)
    r_conf = numeric(out, "echosat_r_search_conflicts", 0.0).to_numpy(dtype=np.float64)
    r_cpu = numeric(out, "echosat_r_cpu_clipped", 0.0).to_numpy(dtype=np.float64)
    search_blowup_penalty = numeric(out, "echosat_search_blowup_penalty", 0.0).to_numpy(dtype=np.float64)
    perturbation = numeric(out, "echosat_perturbation_penalty", 0.0).to_numpy(dtype=np.float64)
    perm_delta = numeric(out, "echosat_perm_delta_penalty", 0.0).to_numpy(dtype=np.float64)
    direction_penalty = numeric(out, "echosat_direction_consistency_penalty", 0.0).to_numpy(dtype=np.float64)
    pair_rank_penalty = numeric(out, "echosat_pair_rank_penalty", 0.0).to_numpy(dtype=np.float64)
    if "echosat_weighted_path_risk_penalty" in out.columns:
        weighted_path_risk_penalty = numeric(out, "echosat_weighted_path_risk_penalty", 0.0).to_numpy(dtype=np.float64)
    else:
        weighted_path_risk_penalty = weighted_risk * (1.0 + perturbation)
    near_cap_penalty = near_cap_mask.astype(np.float64) * (r_dec + r_conf + r_cpu + search_blowup_penalty)
    large_weight_phase_shift_penalty = perturbation * (1.0 - e_sym)

    decision_reduction = numeric(out, "echosat_decision_reduction", 0.0).to_numpy(dtype=np.float64)
    conflict_reduction = numeric(out, "echosat_conflict_reduction", 0.0).to_numpy(dtype=np.float64)
    hard_negative_penalty = hard_negative_failure.astype(np.float64) * (
        search_blowup_penalty
        + direction_penalty
        + pair_rank_penalty
        + np.maximum(0.0, -decision_reduction)
        + np.maximum(0.0, -conflict_reduction)
        + float(cfg.training.echosat_hard_negative_failure_floor)
    )
    anchor_failure_penalty = anchor_failure.astype(np.float64) * (
        search_blowup_penalty
        + direction_penalty
        + pair_rank_penalty
        + np.maximum(0.0, -decision_reduction)
        + np.maximum(0.0, -conflict_reduction)
        + float(cfg.training.echosat_anchor_catastrophic_failure_floor)
    )
    subset_failure_penalty = subset_failure.astype(np.float64) * search_ok.astype(np.float64) * (
        r_dec + r_conf + r_cpu + search_blowup_penalty + float(cfg.training.echosat_subset_failure_floor)
    )
    positive_reward = positive_allowed.astype(np.float64) * e_sym * (r_dec + r_conf + r_cpu)
    random_control_penalty = is_control.astype(np.float64) * np.maximum(search_blowup_penalty + positive_reward, perturbation)
    unsupported_positive_penalty = (e_sym <= 0.0).astype(np.float64) * (r_dec + r_conf + r_cpu)

    reward = positive_reward - search_blowup_penalty
    reward -= float(cfg.training.echosat_random_control_penalty_weight) * random_control_penalty
    reward -= float(cfg.training.echosat_control_penalty_weight) * is_control.astype(np.float64) * perturbation
    reward -= float(cfg.training.echosat_permutation_delta_weight) * (perm_delta + direction_penalty)
    reward -= float(cfg.training.echosat_pair_rank_penalty_weight) * pair_rank_penalty
    reward -= float(cfg.training.echosat_weighted_risk_weight) * weighted_path_risk_penalty
    reward -= float(cfg.training.echosat_near_cap_penalty_weight) * near_cap_penalty
    reward -= float(cfg.training.echosat_delta_magnitude_weight) * unsupported_positive_penalty
    reward -= float(cfg.training.echosat_large_weight_phase_shift_penalty_weight) * large_weight_phase_shift_penalty
    reward -= float(cfg.training.echosat_hard_negative_penalty_weight) * hard_negative_penalty
    reward -= float(cfg.training.echosat_anchor_failure_penalty_weight) * anchor_failure_penalty
    reward -= float(cfg.training.echosat_subset_failure_penalty_weight) * subset_failure_penalty
    reward -= float(cfg.training.echosat_unsolved_penalty) * (~train_rlaf.solved_mask(out).to_numpy(dtype=bool))
    reward -= float(cfg.training.echosat_result_mismatch_penalty) * bool_series(out, "echosat_result_mismatch").to_numpy(dtype=bool)

    out["echosat_positive_allowed_search"] = positive_allowed_search
    out["echosat_positive_allowed"] = positive_allowed
    out["echosat_positive_blocked_control"] = search_ok & is_control
    out["echosat_positive_blocked_subset_failure"] = positive_allowed_search & subset_failure
    out["echosat_positive_blocked_weighted_risk"] = positive_allowed_search & (~weighted_risk_ok)
    out["echosat_positive_blocked_near_cap"] = positive_allowed_search & near_cap_mask
    out["echosat_positive_blocked_pair_inconsistency"] = positive_allowed_search & mixed_pair
    out["echosat_positive_blocked_anchor_failure"] = anchor_failure
    out["echosat_positive_blocked_hard_negative_failure"] = hard_negative_failure
    out["echosat_symmetry_reward"] = positive_reward
    out["echosat_search_reward"] = positive_reward - search_blowup_penalty
    out["echosat_random_control_penalty"] = random_control_penalty
    out["echosat_hard_negative_penalty"] = hard_negative_penalty
    out["echosat_anchor_failure_penalty"] = anchor_failure_penalty
    out["echosat_subset_failure_penalty"] = subset_failure_penalty
    out["echosat_cost"] = np.nan_to_num(-reward, nan=float(cfg.training.echosat_unsolved_penalty), posinf=20.0, neginf=-20.0)

    advantage_weight = np.zeros(len(out), dtype=np.float64)
    advantage_weight[symmetry_strength.eq("strong").to_numpy(dtype=bool)] = float(cfg.training.echosat_strong_advantage_weight)
    advantage_weight[symmetry_strength.eq("weak").to_numpy(dtype=bool)] = float(cfg.training.echosat_weak_advantage_weight)
    advantage_weight[non_control] *= np.clip(e_sym[non_control], 0.0, 1.0)
    advantage_weight[is_control] = float(cfg.training.echosat_control_negative_advantage_weight)
    out["echosat_advantage_weight"] = advantage_weight

    raw_upper = np.full(len(out), np.inf, dtype=np.float64)
    raw_upper[is_control] = 0.0
    raw_upper[anchor_failure] = 0.0
    raw_upper[hard_negative_failure] = 0.0
    raw_upper[subset_failure] = 0.0
    if bool(cfg.training.echosat_v16_hard_block_mixed_positive):
        raw_upper[mixed_pair] = 0.0
    upper = np.full(len(out), np.inf, dtype=np.float64)
    upper[~positive_allowed] = 0.0
    upper[reward <= 0.0] = 0.0
    upper[is_control] = 0.0
    upper[anchor_failure] = 0.0
    upper[hard_negative_failure] = 0.0
    upper[subset_failure] = 0.0
    if bool(cfg.training.echosat_v16_hard_block_mixed_positive):
        upper[mixed_pair] = 0.0
    out["echosat_advantage_raw_upper_bound"] = raw_upper
    out["echosat_advantage_upper_bound"] = upper

    return train_rlaf.attach_grpo_advantage_columns(out, cfg)


def role_for(frame: pd.DataFrame, cfg) -> pd.Series:
    return train_rlaf.echosat_replay_role(frame, cfg)


def summarize(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_cols = [
        "echosat_cost",
        "echosat_search_ok",
        "echosat_search_blowup",
        "echosat_positive_allowed_search",
        "echosat_positive_allowed",
        "echosat_positive_blocked_control",
        "echosat_positive_blocked_subset_failure",
        "echosat_positive_blocked_weighted_risk",
        "echosat_positive_blocked_near_cap",
        "echosat_positive_blocked_pair_inconsistency",
        "echosat_positive_blocked_anchor_failure",
        "echosat_positive_blocked_hard_negative_failure",
        "grpo_raw_advantage_unclamped",
        "grpo_raw_advantage",
        "grpo_final_advantage",
        "grpo_positive_raw_advantage_clamped",
        "grpo_positive_advantage_clamped",
    ]
    for column in metric_cols:
        if column in frame.columns and frame[column].dtype == bool:
            frame[column] = frame[column].astype(float)
    role = (
        frame.groupby("echosat_replay_role", dropna=False)[metric_cols]
        .mean(numeric_only=True)
        .reset_index()
    )
    role["rows"] = frame.groupby("echosat_replay_role", dropna=False).size().to_numpy(dtype=np.int64)
    base_cols = ["echosat_replay_role", "family", "base_instance_id"]
    base = frame.groupby(base_cols, dropna=False)[metric_cols].mean(numeric_only=True).reset_index()
    base["rows"] = frame.groupby(base_cols, dropna=False).size().to_numpy(dtype=np.int64)
    iteration = frame.groupby(["iteration", "echosat_replay_role"], dropna=False)[metric_cols].mean(numeric_only=True).reset_index()
    iteration["rows"] = frame.groupby(["iteration", "echosat_replay_role"], dropna=False).size().to_numpy(dtype=np.int64)
    return role, base, iteration


def frame_block(frame: pd.DataFrame) -> str:
    return "```text\n" + frame.to_string(index=False) + "\n```"


def write_doc(path: Path, role: pd.DataFrame, base: pd.DataFrame, checks: dict[str, bool], outputs: dict[str, Path]) -> None:
    lines = [
        "# EchoSAT Symmetry GRPO v1.6 Reward Replay Dry-Run",
        "",
        "This is an offline replay over v1.5 persisted training batches. It does not rerun solvers and does not train.",
        "",
        "## Outputs",
        "",
    ]
    for name, out_path in outputs.items():
        lines.append(f"- {name}: `{out_path}`")
    lines += [
        "",
        "## Pass Checks",
        "",
    ]
    for name, passed in checks.items():
        lines.append(f"- {name}: `{passed}`")
    lines += [
        "",
        "## Role Summary",
        "",
        frame_block(role),
        "",
        "## Priority Base Summary",
        "",
    ]
    priority = base[
        base["base_instance_id"].isin(
            [
                "k9_color8",
                "php_p9_h8",
                "k10_color9",
                "php_p10_h9",
                "subset_cardinality_bw12",
            ]
        )
        | base["family"].eq("random_3sat_control")
    ].copy()
    lines.append(frame_block(priority))
    lines += [
        "",
        "## Conclusion",
        "",
        "v1.6 repairs the v1.5 failure mode if anchors and hard-negative search_ok rows recover positive final advantage while random controls and the subset failure remain positive-clamped.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-prefix", type=Path, default=DEFAULT_OUT_PREFIX)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--max-files", type=int, default=0)
    args = parser.parse_args()

    files = sorted(glob.glob(str(args.input_dir / "iter=*_solver_stats.csv")))
    if args.max_files > 0:
        files = files[: args.max_files]
    if not files:
        raise FileNotFoundError(f"No replay files found in {args.input_dir}")

    cfg = load_cfg()
    frames = []
    for file in files:
        frame = pd.read_csv(file)
        replay = recompute_v16_from_v15_frame(frame, cfg)
        replay["echosat_replay_role"] = role_for(replay, cfg)
        frames.append(replay)
    all_rows = pd.concat(frames, ignore_index=True)
    role, base, iteration = summarize(all_rows)

    out_prefix = args.out_prefix
    outputs = {
        "rows": out_prefix.with_name(out_prefix.name + "_rows.csv"),
        "role summary": out_prefix.with_name(out_prefix.name + "_role_summary.csv"),
        "base summary": out_prefix.with_name(out_prefix.name + "_base_summary.csv"),
        "iteration summary": out_prefix.with_name(out_prefix.name + "_iteration_summary.csv"),
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    all_rows.to_csv(outputs["rows"], index=False)
    role.to_csv(outputs["role summary"], index=False)
    base.to_csv(outputs["base summary"], index=False)
    iteration.to_csv(outputs["iteration summary"], index=False)

    def role_frac(role_name: str, column: str) -> float:
        rows = role[role["echosat_replay_role"].eq(role_name)]
        if rows.empty or column not in rows:
            return 0.0
        return float(rows[column].iloc[0])

    checks = {
        "anchor_final_positive_recovered": role_frac("anchor", "grpo_final_advantage") > 0.0
        or float((all_rows["echosat_replay_role"].eq("anchor") & (all_rows["grpo_final_advantage"] > 1.0e-12)).mean()) > 0.0,
        "hard_negative_final_positive_recovered": role_frac("hard_negative", "grpo_final_advantage") > 0.0
        or float((all_rows["echosat_replay_role"].eq("hard_negative") & (all_rows["grpo_final_advantage"] > 1.0e-12)).mean()) > 0.0,
        "random_control_no_final_positive": not bool((all_rows["echosat_replay_role"].eq("random_control") & (all_rows["grpo_final_advantage"] > 1.0e-12)).any()),
        "subset_failure_no_final_positive": not bool((all_rows["echosat_replay_role"].eq("subset_failure") & (all_rows["grpo_final_advantage"] > 1.0e-12)).any()),
        "anchor_failure_negative_or_zero": not bool((all_rows["echosat_replay_role"].eq("anchor_failure") & (all_rows["grpo_final_advantage"] > 1.0e-12)).any()),
        "hard_negative_failure_negative_or_zero": not bool((all_rows["echosat_replay_role"].eq("hard_negative_failure") & (all_rows["grpo_final_advantage"] > 1.0e-12)).any()),
        "positive_allowed_not_all_zero": bool(all_rows["echosat_positive_allowed"].astype(bool).any()),
    }
    write_doc(args.doc, role.round(6), base.round(6), checks, outputs)
    print(f"replayed rows: {len(all_rows)} from {len(files)} files")
    for name, passed in checks.items():
        print(f"{name}: {passed}")
    for name, path in outputs.items():
        print(f"{name}: {path}")
    print(f"doc: {args.doc}")


if __name__ == "__main__":
    main()
