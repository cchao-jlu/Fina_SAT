from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_PER_INSTANCE = ROOT / "runs/analysis/symmetry_grpo_speedup_best_harder_baseline_per_instance.csv"
DEFAULT_POLICY = ROOT / "runs/analysis/symmetry_harder_weighted_path_veto_policy.csv"
DEFAULT_SWEEP = ROOT / "runs/analysis/symmetry_harder_weighted_path_veto_sweep.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_harder_weighted_path_veto.md"


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def method_wide(per_instance: pd.DataFrame) -> pd.DataFrame:
    keys = ["family", "base_instance_id", "variant", "repeat_id"]
    metrics = [
        "final_cpu_time",
        "protocol_accounted_time",
        "final_decisions",
        "final_conflicts",
        "final_solved",
        "final_cpu_lim",
        "known_expected_result",
        "final_known_expected_match",
    ]
    table = per_instance.pivot_table(index=keys, columns="method", values=metrics, aggfunc="first")
    table.columns = [f"{metric}__{method}" for metric, method in table.columns]
    table = table.reset_index()
    meta_cols = [
        "control_type",
        "scale",
        "benchmark_role",
        "family_scale",
        "symmetry_strength",
        "num_vars",
        "num_clauses",
    ]
    meta = per_instance.sort_values(keys).drop_duplicates(keys)[keys + [c for c in meta_cols if c in per_instance.columns]]
    table = meta.merge(table, on=keys, how="right")
    for method in ["neutral_weighted_glucose", "static_weighted_glucose", "event_adapter_final"]:
        for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
            table[f"{method}_minus_plain_{metric}"] = table[f"{metric}__{method}"] - table[f"{metric}__plain_unguided_glucose"]
    return table


def base_risk_features(wide: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "family",
        "base_instance_id",
        "control_type",
        "scale",
        "benchmark_role",
        "family_scale",
        "symmetry_strength",
    ]
    rows = []
    for key, group in wide.groupby(group_cols, sort=True):
        row = dict(zip(group_cols, key))
        row["rows"] = int(len(group))
        row["variants"] = int(group["variant"].nunique())
        row["repeats"] = int(group["repeat_id"].nunique())
        for method in ["neutral_weighted_glucose", "static_weighted_glucose", "event_adapter_final"]:
            row[f"mean_{method}_minus_plain_final_cpu"] = float(group[f"{method}_minus_plain_final_cpu_time"].mean())
            row[f"median_{method}_minus_plain_final_cpu"] = float(group[f"{method}_minus_plain_final_cpu_time"].median())
            row[f"mean_{method}_minus_plain_protocol"] = float(group[f"{method}_minus_plain_protocol_accounted_time"].mean())
            row[f"near_cap_rows_{method}"] = int(
                (
                    group[f"final_cpu_time__{method}"]
                    >= 0.8 * group[f"final_cpu_lim__{method}"].fillna(group[f"final_cpu_lim__{method}"].max())
                ).sum()
            )
        row["plain_near_cap_rows"] = int(
            (
                group["final_cpu_time__plain_unguided_glucose"]
                >= 0.8 * group["final_cpu_lim__plain_unguided_glucose"].fillna(group["final_cpu_lim__plain_unguided_glucose"].max())
            ).sum()
        )
        row["plain_protocol_mean"] = float(group["protocol_accounted_time__plain_unguided_glucose"].mean())
        row["adapter_protocol_mean"] = float(group["protocol_accounted_time__event_adapter_final"].mean())
        row["adapter_final_cpu_mean"] = float(group["final_cpu_time__event_adapter_final"].mean())
        row["plain_final_cpu_mean"] = float(group["final_cpu_time__plain_unguided_glucose"].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate_policy(wide: pd.DataFrame, base_features: pd.DataFrame, *, slowdown_threshold: float, cap_veto: bool) -> tuple[pd.DataFrame, dict[str, Any]]:
    risk = base_features.copy()
    risk["neutral_slowdown_risk"] = risk["mean_neutral_weighted_glucose_minus_plain_final_cpu"] > float(slowdown_threshold)
    risk["static_slowdown_risk"] = risk["mean_static_weighted_glucose_minus_plain_final_cpu"] > float(slowdown_threshold)
    risk["cap_risk"] = (
        (risk["near_cap_rows_neutral_weighted_glucose"] > 0)
        | (risk["near_cap_rows_static_weighted_glucose"] > 0)
        | (risk["near_cap_rows_event_adapter_final"] > 0)
    )
    risk["weighted_path_veto"] = risk["neutral_slowdown_risk"] | risk["static_slowdown_risk"] | (risk["cap_risk"] if cap_veto else False)
    policy = wide.merge(
        risk[
            [
                "base_instance_id",
                "weighted_path_veto",
                "neutral_slowdown_risk",
                "static_slowdown_risk",
                "cap_risk",
            ]
        ],
        on="base_instance_id",
        how="left",
    )
    use_adapter = ~policy["weighted_path_veto"].astype(bool)
    for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
        policy[f"policy_{metric}"] = np.where(
            use_adapter,
            policy[f"{metric}__event_adapter_final"],
            policy[f"{metric}__plain_unguided_glucose"],
        )
        policy[f"policy_minus_plain_{metric}"] = policy[f"policy_{metric}"] - policy[f"{metric}__plain_unguided_glucose"]
        policy[f"policy_minus_adapter_{metric}"] = policy[f"policy_{metric}"] - policy[f"{metric}__event_adapter_final"]
    policy["policy_method"] = np.where(use_adapter, "event_adapter_final", "plain_unguided_glucose")
    base_policy = (
        policy.groupby(["family", "base_instance_id", "control_type", "scale", "benchmark_role"], sort=True)
        .agg(
            rows=("repeat_id", "size"),
            variants=("variant", "nunique"),
            repeats=("repeat_id", "nunique"),
            veto=("weighted_path_veto", "first"),
            policy_minus_plain_protocol=("policy_minus_plain_protocol_accounted_time", "mean"),
            policy_minus_plain_final_cpu=("policy_minus_plain_final_cpu_time", "mean"),
            adapter_minus_plain_protocol=("event_adapter_final_minus_plain_protocol_accounted_time", "mean"),
            adapter_minus_plain_final_cpu=("event_adapter_final_minus_plain_final_cpu_time", "mean"),
            policy_minus_adapter_protocol=("policy_minus_adapter_protocol_accounted_time", "mean"),
            policy_minus_adapter_final_cpu=("policy_minus_adapter_final_cpu_time", "mean"),
        )
        .reset_index()
    )
    summary = {
        "slowdown_threshold": float(slowdown_threshold),
        "cap_veto": bool(cap_veto),
        "bases": int(base_policy["base_instance_id"].nunique()),
        "vetoed_bases": int(base_policy["veto"].astype(bool).sum()),
        "policy_protocol_delta_mean": float(base_policy["policy_minus_plain_protocol"].mean()),
        "policy_final_cpu_delta_mean": float(base_policy["policy_minus_plain_final_cpu"].mean()),
        "adapter_protocol_delta_mean": float(base_policy["adapter_minus_plain_protocol"].mean()),
        "adapter_final_cpu_delta_mean": float(base_policy["adapter_minus_plain_final_cpu"].mean()),
        "policy_improves_vs_plain_protocol_bases": int((base_policy["policy_minus_plain_protocol"] < 0.0).sum()),
        "policy_improves_vs_plain_final_cpu_bases": int((base_policy["policy_minus_plain_final_cpu"] < 0.0).sum()),
        "policy_improves_vs_adapter_protocol_bases": int((base_policy["policy_minus_adapter_protocol"] < 0.0).sum()),
        "policy_improves_vs_adapter_final_cpu_bases": int((base_policy["policy_minus_adapter_final_cpu"] < 0.0).sum()),
    }
    for family, group in base_policy.groupby("family", sort=True):
        summary[f"{family}_bases"] = int(group["base_instance_id"].nunique())
        summary[f"{family}_vetoed_bases"] = int(group["veto"].astype(bool).sum())
        summary[f"{family}_policy_protocol_delta_mean"] = float(group["policy_minus_plain_protocol"].mean())
        summary[f"{family}_adapter_protocol_delta_mean"] = float(group["adapter_minus_plain_protocol"].mean())
    return base_policy, summary


def markdown_table(frame: pd.DataFrame, max_rows: int = 30) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                cells.append(f"{value:.6g}" if math.isfinite(value) else "nan")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(path: Path, *, policy: pd.DataFrame, sweep: pd.DataFrame, policy_csv: Path, sweep_csv: Path) -> None:
    best = sweep.sort_values(["policy_protocol_delta_mean", "vetoed_bases"]).head(8).copy()
    family = (
        policy.groupby("family", sort=True)
        .agg(
            bases=("base_instance_id", "nunique"),
            vetoed_bases=("veto", lambda values: int(pd.Series(values).astype(bool).sum())),
            policy_protocol_delta_mean=("policy_minus_plain_protocol", "mean"),
            adapter_protocol_delta_mean=("adapter_minus_plain_protocol", "mean"),
            policy_final_cpu_delta_mean=("policy_minus_plain_final_cpu", "mean"),
            adapter_final_cpu_delta_mean=("adapter_minus_plain_final_cpu", "mean"),
        )
        .reset_index()
        .sort_values("policy_protocol_delta_mean")
    )
    lines = [
        "# Weighted-Path Veto Offline Audit",
        "",
        "This evaluates rule-based veto policies on the already measured harder-baseline runtime table. It does not rerun solvers and does not train a selector.",
        "",
        "## Artifacts",
        "",
        f"- policy CSV: `{policy_csv}`",
        f"- sweep CSV: `{sweep_csv}`",
        "",
        "## Best Sweep Rows",
        "",
        *markdown_table(best, max_rows=12),
        "",
        "## Family Summary For Selected Policy",
        "",
        *markdown_table(family, max_rows=30),
        "",
        "## Interpretation",
        "",
        "- A vetoed base uses plain Glucose instead of the event-adapter weighted path.",
        "- The rule uses already observed neutral/static weighted slowdown and optional near-cap risk, so this is an oracle-style diagnostic, not a deployable gate.",
        "- If veto sharply improves hex/torus without killing random-control wins, weighted-path risk is a real blocker and should be handled before training a selector.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline weighted-path veto audit for SAT symmetry harder baseline.")
    parser.add_argument("--per-instance-csv", type=Path, default=DEFAULT_PER_INSTANCE)
    parser.add_argument("--policy-csv", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--sweep-csv", type=Path, default=DEFAULT_SWEEP)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--selected-threshold", type=float, default=0.05)
    parser.add_argument("--selected-cap-veto", action="store_true")
    parser.add_argument("--thresholds", nargs="*", type=float, default=[0.0, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    per_instance = pd.read_csv(resolve(args.per_instance_csv))
    wide = method_wide(per_instance)
    features = base_risk_features(wide)
    sweep_rows = []
    selected_policy = None
    for cap_veto in [False, True]:
        for threshold in args.thresholds:
            policy, summary = evaluate_policy(wide, features, slowdown_threshold=float(threshold), cap_veto=bool(cap_veto))
            sweep_rows.append(summary)
            if bool(cap_veto) == bool(args.selected_cap_veto) and abs(float(threshold) - float(args.selected_threshold)) < 1.0e-12:
                selected_policy = policy
    if selected_policy is None:
        selected_policy, _ = evaluate_policy(
            wide,
            features,
            slowdown_threshold=float(args.selected_threshold),
            cap_veto=bool(args.selected_cap_veto),
        )
    sweep = pd.DataFrame(sweep_rows).sort_values(["policy_protocol_delta_mean", "vetoed_bases"]).reset_index(drop=True)
    policy_path = resolve(args.policy_csv)
    sweep_path = resolve(args.sweep_csv)
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    selected_policy.to_csv(policy_path, index=False)
    sweep.to_csv(sweep_path, index=False)
    write_doc(
        resolve(args.doc),
        policy=selected_policy,
        sweep=sweep,
        policy_csv=policy_path.relative_to(ROOT),
        sweep_csv=sweep_path.relative_to(ROOT),
    )
    print(f"wrote {policy_path}")
    print(f"wrote {sweep_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
