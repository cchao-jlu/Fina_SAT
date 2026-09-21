#!/usr/bin/env python3
"""Offline v1.7 reward replay from persisted v1.5 training batches."""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from hydra import compose, initialize_config_dir

import replay_echosat_symmetry_grpo_v1_6_reward as v16_replay
import train_rlaf


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_5_WC1_PairStrict/reward_replay"
DEFAULT_OUT_PREFIX = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_7_reward_replay_dryrun"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_7_reward_replay_dryrun.md"
CONFIG_NAME = "config_train_rlaf_echosat_symmetry_grpo_v1_7_wc1_positivecap"


def load_cfg():
    with initialize_config_dir(config_dir=str(ROOT / "configs"), version_base=None):
        return compose(config_name=CONFIG_NAME)


def bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index, dtype=bool)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(False).astype(bool)
    if pd.api.types.is_numeric_dtype(values):
        return pd.to_numeric(values, errors="coerce").fillna(0.0).ne(0.0)
    return values.fillna(False).astype(str).str.lower().isin({"true", "1", "yes", "y"})


def numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=np.float64)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(np.float64)


def replay_frame(frame: pd.DataFrame, cfg) -> pd.DataFrame:
    replay = v16_replay.recompute_v16_from_v15_frame(frame, cfg)
    replay["echosat_target_mode"] = "symmetry_grpo_v1_7"

    positive_allowed = bool_series(replay, "echosat_positive_allowed").to_numpy(dtype=bool)
    search_ok = bool_series(replay, "echosat_search_ok").to_numpy(dtype=bool)
    positive_reward = numeric(replay, "echosat_symmetry_reward", 0.0).to_numpy(dtype=np.float64)
    search_blowup_penalty = numeric(replay, "echosat_search_blowup_penalty", 0.0).to_numpy(dtype=np.float64)
    random_control_penalty = numeric(replay, "echosat_random_control_penalty", 0.0).to_numpy(dtype=np.float64)
    perturbation = numeric(replay, "echosat_perturbation_penalty", 0.0).to_numpy(dtype=np.float64)
    perm_delta = numeric(replay, "echosat_perm_delta_penalty", 0.0).to_numpy(dtype=np.float64)
    direction_penalty = numeric(replay, "echosat_direction_consistency_penalty", 0.0).to_numpy(dtype=np.float64)
    pair_rank_penalty = numeric(replay, "echosat_pair_rank_penalty", 0.0).to_numpy(dtype=np.float64)
    weighted_path_risk_penalty = numeric(replay, "echosat_weighted_path_risk_penalty", 0.0).to_numpy(dtype=np.float64)
    near_cap_penalty = numeric(replay, "echosat_near_cap_penalty", 0.0).to_numpy(dtype=np.float64)
    unsupported_positive_penalty = (
        (numeric(replay, "echosat_e_sym", 0.0).to_numpy(dtype=np.float64) <= 0.0).astype(np.float64)
        * (
            numeric(replay, "echosat_r_search_decisions", 0.0).to_numpy(dtype=np.float64)
            + numeric(replay, "echosat_r_search_conflicts", 0.0).to_numpy(dtype=np.float64)
            + numeric(replay, "echosat_r_cpu_clipped", 0.0).to_numpy(dtype=np.float64)
        )
    )
    large_weight_phase_shift_penalty = numeric(replay, "echosat_large_weight_phase_shift_penalty", 0.0).to_numpy(dtype=np.float64)
    hard_negative_penalty = numeric(replay, "echosat_hard_negative_penalty", 0.0).to_numpy(dtype=np.float64)
    anchor_failure_penalty = numeric(replay, "echosat_anchor_failure_penalty", 0.0).to_numpy(dtype=np.float64)
    subset_failure_penalty = numeric(replay, "echosat_subset_failure_penalty", 0.0).to_numpy(dtype=np.float64)

    control_mask = bool_series(replay, "echosat_positive_blocked_control").to_numpy(dtype=bool)
    family = replay.get("family", pd.Series("", index=replay.index)).fillna("").astype(str)
    control_type = replay.get("control_type", pd.Series("", index=replay.index)).fillna("").astype(str)
    symmetry_strength = replay.get("symmetry_strength", pd.Series("", index=replay.index)).fillna("").astype(str)
    is_control = (
        control_mask
        | family.eq("random_3sat_control").to_numpy(dtype=bool)
        | control_type.eq("non_symmetric_control").to_numpy(dtype=bool)
        | symmetry_strength.eq("none").to_numpy(dtype=bool)
    )
    base = replay.get("base_instance_id", pd.Series("", index=replay.index)).fillna("").astype(str)
    variant = replay.get("variant", pd.Series("", index=replay.index)).fillna("").astype(str)
    subset_failure = (
        base.eq(str(cfg.training.echosat_subset_failure_base_id)).to_numpy(dtype=bool)
        & variant.eq(str(cfg.training.echosat_subset_failure_variant)).to_numpy(dtype=bool)
    )

    consistency_penalty_applied = (
        float(cfg.training.echosat_permutation_delta_weight) * (perm_delta + direction_penalty)
        + float(cfg.training.echosat_pair_rank_penalty_weight) * pair_rank_penalty
    )
    large_weight_phase_shift_penalty_applied = (
        float(cfg.training.echosat_large_weight_phase_shift_penalty_weight)
        * large_weight_phase_shift_penalty
    )
    positive_success = positive_allowed & search_ok
    consistency_cap = (
        float(cfg.training.echosat_v17_positive_consistency_penalty_fraction)
        * np.maximum(positive_reward, 0.0)
    )
    large_shift_cap = (
        float(cfg.training.echosat_v17_positive_large_shift_penalty_fraction)
        * np.maximum(positive_reward, 0.0)
    )
    consistency_penalty_applied[positive_success] = np.minimum(
        consistency_penalty_applied[positive_success],
        consistency_cap[positive_success],
    )
    large_weight_phase_shift_penalty_applied[positive_success] = np.minimum(
        large_weight_phase_shift_penalty_applied[positive_success],
        large_shift_cap[positive_success],
    )

    reward = positive_reward - search_blowup_penalty
    reward -= float(cfg.training.echosat_random_control_penalty_weight) * random_control_penalty
    reward -= float(cfg.training.echosat_control_penalty_weight) * is_control.astype(np.float64) * perturbation
    reward -= consistency_penalty_applied
    reward -= float(cfg.training.echosat_weighted_risk_weight) * weighted_path_risk_penalty
    reward -= float(cfg.training.echosat_near_cap_penalty_weight) * near_cap_penalty
    reward -= float(cfg.training.echosat_delta_magnitude_weight) * unsupported_positive_penalty
    reward -= large_weight_phase_shift_penalty_applied
    reward -= float(cfg.training.echosat_hard_negative_penalty_weight) * hard_negative_penalty
    reward -= float(cfg.training.echosat_anchor_failure_penalty_weight) * anchor_failure_penalty
    reward -= float(cfg.training.echosat_subset_failure_penalty_weight) * subset_failure_penalty
    reward -= float(cfg.training.echosat_unsolved_penalty) * (~train_rlaf.solved_mask(replay).to_numpy(dtype=bool))
    reward -= float(cfg.training.echosat_result_mismatch_penalty) * bool_series(replay, "echosat_result_mismatch").to_numpy(dtype=bool)

    replay["echosat_consistency_penalty_applied"] = consistency_penalty_applied
    replay["echosat_large_weight_phase_shift_penalty_applied"] = large_weight_phase_shift_penalty_applied
    replay["echosat_cost"] = np.nan_to_num(-reward, nan=float(cfg.training.echosat_unsolved_penalty), posinf=20.0, neginf=-20.0)

    upper = np.full(len(replay), np.inf, dtype=np.float64)
    upper[~positive_allowed] = 0.0
    upper[reward <= 0.0] = 0.0
    upper[positive_allowed & (positive_reward > 0.0)] = np.inf
    upper[is_control] = 0.0
    upper[bool_series(replay, "echosat_anchor_failure").to_numpy(dtype=bool)] = 0.0
    upper[bool_series(replay, "echosat_hard_negative_failure").to_numpy(dtype=bool)] = 0.0
    upper[subset_failure] = 0.0
    replay["echosat_advantage_upper_bound"] = upper

    raw_upper = np.full(len(replay), np.inf, dtype=np.float64)
    raw_upper[is_control] = 0.0
    raw_upper[bool_series(replay, "echosat_anchor_failure").to_numpy(dtype=bool)] = 0.0
    raw_upper[bool_series(replay, "echosat_hard_negative_failure").to_numpy(dtype=bool)] = 0.0
    raw_upper[subset_failure] = 0.0
    replay["echosat_advantage_raw_upper_bound"] = raw_upper

    replay = train_rlaf.attach_grpo_advantage_columns(replay, cfg)
    replay["echosat_replay_role"] = train_rlaf.echosat_replay_role(replay, cfg)
    return replay


def summarize(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_cols = [
        "echosat_cost",
        "echosat_search_ok",
        "echosat_search_blowup",
        "echosat_positive_allowed_search",
        "echosat_positive_allowed",
        "echosat_symmetry_reward",
        "echosat_r_search_decisions",
        "echosat_r_search_conflicts",
        "echosat_r_cpu_clipped",
        "echosat_search_blowup_penalty",
        "echosat_consistency_penalty_applied",
        "echosat_large_weight_phase_shift_penalty_applied",
        "echosat_random_control_penalty",
        "echosat_hard_negative_penalty",
        "echosat_anchor_failure_penalty",
        "echosat_subset_failure_penalty",
        "echosat_positive_blocked_control",
        "echosat_positive_blocked_subset_failure",
        "echosat_positive_blocked_weighted_risk",
        "echosat_positive_blocked_near_cap",
        "echosat_positive_blocked_pair_inconsistency",
        "echosat_positive_blocked_anchor_failure",
        "echosat_positive_blocked_hard_negative_failure",
        "grpo_raw_advantage_unclamped",
        "grpo_raw_advantage",
        "grpo_weighted_advantage_before_clamp",
        "grpo_final_advantage",
        "grpo_positive_raw_advantage_clamped",
        "grpo_positive_advantage_clamped",
    ]
    present = [column for column in metric_cols if column in frame.columns]
    for column in present:
        if frame[column].dtype == bool:
            frame[column] = frame[column].astype(float)
    role = frame.groupby("echosat_replay_role", dropna=False)[present].mean(numeric_only=True).reset_index()
    role["rows"] = frame.groupby("echosat_replay_role", dropna=False).size().to_numpy(dtype=np.int64)
    base_cols = ["echosat_replay_role", "family", "base_instance_id"]
    base = frame.groupby(base_cols, dropna=False)[present].mean(numeric_only=True).reset_index()
    base["rows"] = frame.groupby(base_cols, dropna=False).size().to_numpy(dtype=np.int64)
    iteration = frame.groupby(["iteration", "echosat_replay_role"], dropna=False)[present].mean(numeric_only=True).reset_index()
    iteration["rows"] = frame.groupby(["iteration", "echosat_replay_role"], dropna=False).size().to_numpy(dtype=np.int64)
    return role, base, iteration


def frame_block(frame: pd.DataFrame) -> str:
    return "```text\n" + frame.to_string(index=False) + "\n```"


def write_doc(path: Path, role: pd.DataFrame, base: pd.DataFrame, checks: dict[str, bool], outputs: dict[str, Path]) -> None:
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
    lines = [
        "# EchoSAT Symmetry GRPO v1.7 Reward Replay Dry-Run",
        "",
        "This is an offline replay over v1.5 persisted training batches. It does not rerun solvers and does not train.",
        "",
        "v1.7 keeps controls and known failures positive-clamped, while capping pair/order and large-shift penalties on strict search-work positive rows so that the positive learning signal is not erased by group-level mixed-direction diagnostics.",
        "",
        "## Outputs",
        "",
    ]
    for name, out_path in outputs.items():
        lines.append(f"- {name}: `{out_path}`")
    lines += ["", "## Pass Checks", ""]
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
        frame_block(priority),
        "",
        "## Conclusion",
        "",
        "Training should proceed only if anchors and hard-negative search-ok rows recover positive final advantage, while random controls, subset failure, anchor failures, and hard-negative failures remain non-positive.",
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
        replay = replay_frame(frame, cfg)
        replay["iteration"] = int(Path(file).stem.split("_")[0].split("=")[1])
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
    for out_path in outputs.values():
        out_path.parent.mkdir(parents=True, exist_ok=True)
    all_rows.to_csv(outputs["rows"], index=False)
    role.to_csv(outputs["role summary"], index=False)
    base.to_csv(outputs["base summary"], index=False)
    iteration.to_csv(outputs["iteration summary"], index=False)

    def any_positive(role_name: str) -> bool:
        rows = all_rows[all_rows["echosat_replay_role"].eq(role_name)]
        return bool((rows["grpo_final_advantage"] > 1.0e-12).any())

    def no_positive(role_name: str) -> bool:
        return not any_positive(role_name)

    checks = {
        "anchor_final_positive_recovered": any_positive("anchor"),
        "hard_negative_final_positive_recovered": any_positive("hard_negative"),
        "random_control_no_final_positive": no_positive("random_control"),
        "subset_failure_no_final_positive": no_positive("subset_failure"),
        "anchor_failure_negative_or_zero": no_positive("anchor_failure"),
        "hard_negative_failure_negative_or_zero": no_positive("hard_negative_failure"),
        "positive_allowed_not_all_zero": bool(bool_series(all_rows, "echosat_positive_allowed").any()),
    }
    write_doc(args.doc, role.round(6), base.round(6), checks, outputs)
    print(f"replayed rows: {len(all_rows)} from {len(files)} files")
    for name, passed in checks.items():
        print(f"{name}: {passed}")
    for name, out_path in outputs.items():
        print(f"{name}: {out_path}")
    print(f"doc: {args.doc}")


if __name__ == "__main__":
    main()
