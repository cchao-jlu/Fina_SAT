from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_PER_INSTANCE = ROOT / "runs/analysis/symmetry_grpo_speedup_best_harder_baseline_per_instance.csv"
DEFAULT_POLICY = ROOT / "runs/analysis/echosat_weighted_path_veto_policy.csv"
DEFAULT_SWEEP = ROOT / "runs/analysis/echosat_weighted_path_veto_sweep.csv"
DEFAULT_DOC = ROOT / "docs/echosat_weighted_path_veto.md"


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
        "warmup_cpu_time",
        "event_state_l2_sum",
        "event_state_nonzero_vars",
    ]
    frame = per_instance.copy()
    table = frame.pivot_table(index=keys, columns="method", values=[m for m in metrics if m in frame.columns], aggfunc="first")
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
    meta = frame.sort_values(keys).drop_duplicates(keys)[keys + [c for c in meta_cols if c in frame.columns]]
    table = meta.merge(table, on=keys, how="right")
    return table


def rel_slowdown(delta: pd.Series, baseline: pd.Series) -> pd.Series:
    return delta / baseline.clip(lower=1.0e-9)


def row_veto_features(wide: pd.DataFrame) -> pd.DataFrame:
    out = wide.copy()
    out["neutral_delta_cpu"] = out["final_cpu_time__neutral_weighted_glucose"] - out["final_cpu_time__plain_unguided_glucose"]
    out["neutral_rel_delta_cpu"] = rel_slowdown(out["neutral_delta_cpu"], out["final_cpu_time__plain_unguided_glucose"])
    out["static_delta_vs_neutral_cpu"] = out["final_cpu_time__static_weighted_glucose"] - out["final_cpu_time__neutral_weighted_glucose"]
    out["static_rel_delta_vs_neutral_cpu"] = rel_slowdown(out["static_delta_vs_neutral_cpu"], out["final_cpu_time__neutral_weighted_glucose"])
    out["event_overhead_cpu"] = out.get("warmup_cpu_time__event_adapter_final", pd.Series(0.0, index=out.index)).fillna(0.0)
    out["event_l2_sum"] = out.get("event_state_l2_sum__event_adapter_final", pd.Series(0.0, index=out.index)).fillna(0.0)
    cap = out["final_cpu_lim__plain_unguided_glucose"].fillna(out["final_cpu_lim__plain_unguided_glucose"].max()).clip(lower=1.0e-9)
    out["neutral_near_cap"] = out["final_cpu_time__neutral_weighted_glucose"] >= 0.8 * cap
    out["static_near_cap"] = out["final_cpu_time__static_weighted_glucose"] >= 0.8 * cap
    out["plain_near_cap"] = out["final_cpu_time__plain_unguided_glucose"] >= 0.8 * cap
    return out


def evaluate_policy(
    features: pd.DataFrame,
    *,
    abs_threshold: float,
    rel_threshold: float,
    cap_veto: bool,
    overhead_threshold: float,
    event_l2_epsilon: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    row = features.copy()
    row["neutral_slowdown_risk"] = (row["neutral_delta_cpu"] > float(abs_threshold)) | (row["neutral_rel_delta_cpu"] > float(rel_threshold))
    row["static_slowdown_risk"] = (row["static_delta_vs_neutral_cpu"] > float(abs_threshold)) | (row["static_rel_delta_vs_neutral_cpu"] > float(rel_threshold))
    row["cap_risk"] = row["neutral_near_cap"].astype(bool) | row["static_near_cap"].astype(bool)
    row["event_overhead_risk"] = row["event_overhead_cpu"] > float(overhead_threshold)
    row["weak_event_signal"] = row["event_l2_sum"] <= float(event_l2_epsilon)
    base_risk = (
        row.groupby(["family", "base_instance_id", "control_type", "scale", "benchmark_role"], sort=True)
        .agg(
            rows=("repeat_id", "size"),
            variants=("variant", "nunique"),
            repeats=("repeat_id", "nunique"),
            neutral_slowdown_risk=("neutral_slowdown_risk", "max"),
            static_slowdown_risk=("static_slowdown_risk", "max"),
            cap_risk=("cap_risk", "max"),
            event_overhead_risk=("event_overhead_risk", "max"),
            weak_event_signal=("weak_event_signal", "max"),
        )
        .reset_index()
    )
    base_risk["weighted_path_veto"] = (
        base_risk["neutral_slowdown_risk"].astype(bool)
        | base_risk["static_slowdown_risk"].astype(bool)
        | (base_risk["cap_risk"].astype(bool) if cap_veto else False)
    )
    base_risk["event_path_veto"] = base_risk["weighted_path_veto"].astype(bool) | base_risk["event_overhead_risk"].astype(bool) | base_risk["weak_event_signal"].astype(bool)
    policy = row.merge(
        base_risk[
            [
                "base_instance_id",
                "weighted_path_veto",
                "event_path_veto",
                "neutral_slowdown_risk",
                "static_slowdown_risk",
                "cap_risk",
                "event_overhead_risk",
                "weak_event_signal",
            ]
        ],
        on="base_instance_id",
        how="left",
    )
    use_adapter = ~policy["event_path_veto"].astype(bool)
    for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
        policy[f"policy_{metric}"] = np.where(
            use_adapter,
            policy[f"{metric}__event_adapter_final"],
            policy[f"{metric}__plain_unguided_glucose"],
        )
        policy[f"policy_minus_plain_{metric}"] = policy[f"policy_{metric}"] - policy[f"{metric}__plain_unguided_glucose"]
        policy[f"policy_minus_adapter_{metric}"] = policy[f"policy_{metric}"] - policy[f"{metric}__event_adapter_final"]
    policy["solver_path_role"] = np.where(use_adapter, "event_adapter_allowed", "plain_fallback_veto")
    base_policy = (
        policy.groupby(["family", "base_instance_id", "control_type", "scale", "benchmark_role"], sort=True)
        .agg(
            rows=("repeat_id", "size"),
            variants=("variant", "nunique"),
            repeats=("repeat_id", "nunique"),
            weighted_path_veto=("weighted_path_veto", "first"),
            event_path_veto=("event_path_veto", "first"),
            neutral_slowdown_risk=("neutral_slowdown_risk_y", "first"),
            static_slowdown_risk=("static_slowdown_risk_y", "first"),
            cap_risk=("cap_risk_y", "first"),
            event_overhead_risk=("event_overhead_risk_y", "first"),
            weak_event_signal=("weak_event_signal_y", "first"),
            policy_minus_plain_protocol=("policy_minus_plain_protocol_accounted_time", "mean"),
            policy_minus_plain_final_cpu=("policy_minus_plain_final_cpu_time", "mean"),
            adapter_minus_plain_protocol=("protocol_accounted_time__event_adapter_final", lambda values: float((values - policy.loc[values.index, "protocol_accounted_time__plain_unguided_glucose"]).mean())),
            adapter_minus_plain_final_cpu=("final_cpu_time__event_adapter_final", lambda values: float((values - policy.loc[values.index, "final_cpu_time__plain_unguided_glucose"]).mean())),
        )
        .reset_index()
    )
    summary = {
        "abs_threshold": float(abs_threshold),
        "rel_threshold": float(rel_threshold),
        "cap_veto": bool(cap_veto),
        "overhead_threshold": float(overhead_threshold),
        "event_l2_epsilon": float(event_l2_epsilon),
        "bases": int(base_policy["base_instance_id"].nunique()),
        "weighted_vetoed_bases": int(base_policy["weighted_path_veto"].astype(bool).sum()),
        "event_vetoed_bases": int(base_policy["event_path_veto"].astype(bool).sum()),
        "policy_protocol_delta_mean": float(base_policy["policy_minus_plain_protocol"].mean()),
        "policy_final_cpu_delta_mean": float(base_policy["policy_minus_plain_final_cpu"].mean()),
        "adapter_protocol_delta_mean": float(base_policy["adapter_minus_plain_protocol"].mean()),
        "adapter_final_cpu_delta_mean": float(base_policy["adapter_minus_plain_final_cpu"].mean()),
    }
    for family, group in base_policy.groupby("family", sort=True):
        summary[f"{family}_bases"] = int(group["base_instance_id"].nunique())
        summary[f"{family}_event_vetoed_bases"] = int(group["event_path_veto"].astype(bool).sum())
        summary[f"{family}_policy_protocol_delta_mean"] = float(group["policy_minus_plain_protocol"].mean())
        summary[f"{family}_adapter_protocol_delta_mean"] = float(group["adapter_minus_plain_protocol"].mean())
    return base_policy, summary


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
            if isinstance(value, float):
                cells.append(f"{value:.6g}" if math.isfinite(value) else "nan")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(path: Path, policy: pd.DataFrame, sweep: pd.DataFrame, policy_csv: Path, sweep_csv: Path) -> None:
    best = sweep.sort_values(["policy_protocol_delta_mean", "event_vetoed_bases"]).head(10)
    family = (
        policy.groupby("family", sort=True)
        .agg(
            bases=("base_instance_id", "nunique"),
            weighted_vetoed_bases=("weighted_path_veto", lambda values: int(pd.Series(values).astype(bool).sum())),
            event_vetoed_bases=("event_path_veto", lambda values: int(pd.Series(values).astype(bool).sum())),
            policy_protocol_delta_mean=("policy_minus_plain_protocol", "mean"),
            adapter_protocol_delta_mean=("adapter_minus_plain_protocol", "mean"),
            policy_final_cpu_delta_mean=("policy_minus_plain_final_cpu", "mean"),
            adapter_final_cpu_delta_mean=("adapter_minus_plain_final_cpu", "mean"),
        )
        .reset_index()
        .sort_values("policy_protocol_delta_mean")
    )
    lines = [
        "# EchoSAT Weighted-Path Veto v0",
        "",
        "This is a deployable-style rule audit: the veto inputs are plain/neutral/static calibration, near-cap risk, warmup overhead, and event signal. The rule does not use adapter final runtime as an input. It is still an offline replay over an existing runtime table.",
        "",
        "## Artifacts",
        "",
        f"- policy CSV: `{policy_csv}`",
        f"- sweep CSV: `{sweep_csv}`",
        "",
        "## Best Sweep Rows",
        "",
        *markdown_table(best, max_rows=10),
        "",
        "## Family Summary For Selected Policy",
        "",
        *markdown_table(family, max_rows=40),
        "",
        "## Interpretation",
        "",
        "- `weighted_path_veto` uses neutral-vs-plain and static-vs-neutral slowdown plus optional near-cap risk.",
        "- `event_path_veto` additionally includes warmup/event-overhead and weak-event-signal rules.",
        "- This is a protocol variant candidate, not a learned selector and not a speedup claim.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EchoSAT deployable-style weighted/event path veto audit.")
    parser.add_argument("--per-instance-csv", type=Path, default=DEFAULT_PER_INSTANCE)
    parser.add_argument("--policy-csv", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--sweep-csv", type=Path, default=DEFAULT_SWEEP)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--selected-abs-threshold", type=float, default=0.05)
    parser.add_argument("--selected-rel-threshold", type=float, default=0.10)
    parser.add_argument("--selected-overhead-threshold", type=float, default=1.0)
    parser.add_argument("--selected-event-l2-epsilon", type=float, default=0.0)
    parser.add_argument("--selected-cap-veto", action="store_true")
    parser.add_argument("--abs-thresholds", nargs="*", type=float, default=[0.0, 0.01, 0.05, 0.1, 0.5])
    parser.add_argument("--rel-thresholds", nargs="*", type=float, default=[0.0, 0.05, 0.10, 0.25])
    parser.add_argument("--overhead-thresholds", nargs="*", type=float, default=[0.25, 0.5, 1.0, 2.0, 5.0])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    per_instance = pd.read_csv(resolve(args.per_instance_csv))
    features = row_veto_features(method_wide(per_instance))
    sweep_rows = []
    selected = None
    for cap_veto in [False, True]:
        for abs_threshold in args.abs_thresholds:
            for rel_threshold in args.rel_thresholds:
                for overhead_threshold in args.overhead_thresholds:
                    policy, summary = evaluate_policy(
                        features,
                        abs_threshold=float(abs_threshold),
                        rel_threshold=float(rel_threshold),
                        cap_veto=bool(cap_veto),
                        overhead_threshold=float(overhead_threshold),
                        event_l2_epsilon=float(args.selected_event_l2_epsilon),
                    )
                    sweep_rows.append(summary)
                    if (
                        bool(cap_veto) == bool(args.selected_cap_veto)
                        and abs(float(abs_threshold) - float(args.selected_abs_threshold)) < 1.0e-12
                        and abs(float(rel_threshold) - float(args.selected_rel_threshold)) < 1.0e-12
                        and abs(float(overhead_threshold) - float(args.selected_overhead_threshold)) < 1.0e-12
                    ):
                        selected = policy
    if selected is None:
        selected, _ = evaluate_policy(
            features,
            abs_threshold=float(args.selected_abs_threshold),
            rel_threshold=float(args.selected_rel_threshold),
            cap_veto=bool(args.selected_cap_veto),
            overhead_threshold=float(args.selected_overhead_threshold),
            event_l2_epsilon=float(args.selected_event_l2_epsilon),
        )
    sweep = pd.DataFrame(sweep_rows).sort_values(["policy_protocol_delta_mean", "event_vetoed_bases"]).reset_index(drop=True)
    policy_path = resolve(args.policy_csv)
    sweep_path = resolve(args.sweep_csv)
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(policy_path, index=False)
    sweep.to_csv(sweep_path, index=False)
    write_doc(resolve(args.doc), selected, sweep, policy_path.relative_to(ROOT), sweep_path.relative_to(ROOT))
    print(f"wrote {policy_path}")
    print(f"wrote {sweep_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
