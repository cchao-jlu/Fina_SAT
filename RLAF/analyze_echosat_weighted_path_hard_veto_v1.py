from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_PER_INSTANCE = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_per_instance.csv"
DEFAULT_POLICY = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_hard_veto_v1_policy.csv"
DEFAULT_SWEEP = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_hard_veto_v1_sweep.csv"
DEFAULT_DOC = ROOT / "docs/echosat_adapter_delta_v2_iter235_hard_veto_v1.md"


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values.fillna(False)
    return values.fillna(False).astype(str).str.lower().isin({"1", "true", "yes", "y"})


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
        "event_adapter_graph_gate_evidence",
        "event_adapter_graph_gate_open",
    ]
    frame = per_instance.copy()
    table = frame.pivot_table(
        index=keys,
        columns="method",
        values=[metric for metric in metrics if metric in frame.columns],
        aggfunc="first",
    )
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
        "warmup_conflicts",
    ]
    meta = frame.sort_values(keys).drop_duplicates(keys)[keys + [column for column in meta_cols if column in frame.columns]]
    return meta.merge(table, on=keys, how="right")


def rel_slowdown(delta: pd.Series, baseline: pd.Series) -> pd.Series:
    return delta / baseline.clip(lower=1.0e-9)


def validate_input(per_instance: pd.DataFrame, allow_weighted_no_pre: bool) -> None:
    methods = set(per_instance["method"].astype(str).unique())
    required = {
        "plain_unguided_glucose",
        "neutral_weighted_glucose",
        "static_weighted_glucose",
        "event_adapter_final",
    }
    missing = sorted(required.difference(methods))
    if missing:
        raise ValueError(f"missing required methods: {missing}")
    if "weighted_no_pre" in per_instance.columns and not allow_weighted_no_pre:
        if bool(bool_series(per_instance["weighted_no_pre"]).any()):
            raise ValueError("hard veto v1 expects patched_pretrue_main rows, found weighted_no_pre=True")
    if "solver_path_role" in per_instance.columns:
        roles = sorted(set(per_instance["solver_path_role"].dropna().astype(str)))
        if roles != ["patched_pretrue_main"]:
            raise ValueError(f"hard veto v1 expects patched_pretrue_main only, found {roles}")


def row_veto_features(wide: pd.DataFrame, near_cap_fraction: float) -> pd.DataFrame:
    out = wide.copy()
    out["neutral_delta_cpu"] = out["final_cpu_time__neutral_weighted_glucose"] - out["final_cpu_time__plain_unguided_glucose"]
    out["neutral_rel_delta_cpu"] = rel_slowdown(out["neutral_delta_cpu"], out["final_cpu_time__plain_unguided_glucose"])
    out["static_delta_vs_neutral_cpu"] = out["final_cpu_time__static_weighted_glucose"] - out[
        "final_cpu_time__neutral_weighted_glucose"
    ]
    out["static_rel_delta_vs_neutral_cpu"] = rel_slowdown(
        out["static_delta_vs_neutral_cpu"],
        out["final_cpu_time__neutral_weighted_glucose"],
    )
    cap = out["final_cpu_lim__plain_unguided_glucose"].fillna(
        out["final_cpu_lim__plain_unguided_glucose"].max()
    ).clip(lower=1.0e-9)
    threshold = float(near_cap_fraction) * cap
    out["plain_near_cap"] = out["final_cpu_time__plain_unguided_glucose"] >= threshold
    out["neutral_near_cap"] = out["final_cpu_time__neutral_weighted_glucose"] >= threshold
    out["static_near_cap"] = out["final_cpu_time__static_weighted_glucose"] >= threshold
    out["known_expected_match_risk"] = False
    if "known_expected_result__event_adapter_final" in out.columns and "final_known_expected_match__event_adapter_final" in out.columns:
        known = bool_series(out["known_expected_result__event_adapter_final"])
        match = bool_series(out["final_known_expected_match__event_adapter_final"])
        out["known_expected_match_risk"] = known & ~match
    return out


def evaluate_policy(
    features: pd.DataFrame,
    *,
    abs_threshold: float,
    rel_threshold: float,
    near_cap_fraction: float,
    cap_veto: bool,
    slowdown_logic: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    row = row_veto_features(features, near_cap_fraction=float(near_cap_fraction))
    if slowdown_logic == "either":
        row["neutral_slowdown_risk"] = (row["neutral_delta_cpu"] > float(abs_threshold)) | (
            row["neutral_rel_delta_cpu"] > float(rel_threshold)
        )
        row["static_slowdown_risk"] = (row["static_delta_vs_neutral_cpu"] > float(abs_threshold)) | (
            row["static_rel_delta_vs_neutral_cpu"] > float(rel_threshold)
        )
    elif slowdown_logic == "both":
        row["neutral_slowdown_risk"] = (row["neutral_delta_cpu"] > float(abs_threshold)) & (
            row["neutral_rel_delta_cpu"] > float(rel_threshold)
        )
        row["static_slowdown_risk"] = (row["static_delta_vs_neutral_cpu"] > float(abs_threshold)) & (
            row["static_rel_delta_vs_neutral_cpu"] > float(rel_threshold)
        )
    else:
        raise ValueError(f"Unknown slowdown_logic={slowdown_logic!r}")
    row["cap_risk"] = (
        row["plain_near_cap"].astype(bool)
        | row["neutral_near_cap"].astype(bool)
        | row["static_near_cap"].astype(bool)
    )
    base_risk = (
        row.groupby(["family", "base_instance_id", "control_type", "scale", "benchmark_role"], sort=True)
        .agg(
            rows=("repeat_id", "size"),
            variants=("variant", "nunique"),
            repeats=("repeat_id", "nunique"),
            neutral_delta_cpu_mean=("neutral_delta_cpu", "mean"),
            neutral_rel_delta_cpu_mean=("neutral_rel_delta_cpu", "mean"),
            static_delta_vs_neutral_cpu_mean=("static_delta_vs_neutral_cpu", "mean"),
            static_rel_delta_vs_neutral_cpu_mean=("static_rel_delta_vs_neutral_cpu", "mean"),
            plain_final_cpu_mean=("final_cpu_time__plain_unguided_glucose", "mean"),
            neutral_final_cpu_mean=("final_cpu_time__neutral_weighted_glucose", "mean"),
            static_final_cpu_mean=("final_cpu_time__static_weighted_glucose", "mean"),
            event_adapter_final_cpu_mean=("final_cpu_time__event_adapter_final", "mean"),
            warmup_cpu_mean=("warmup_cpu_time__event_adapter_final", "mean"),
            event_l2_sum_mean=("event_state_l2_sum__event_adapter_final", "mean"),
            graph_gate_open_fraction=("event_adapter_graph_gate_open__event_adapter_final", "mean"),
            neutral_slowdown_risk=("neutral_slowdown_risk", "max"),
            static_slowdown_risk=("static_slowdown_risk", "max"),
            cap_risk=("cap_risk", "max"),
            known_expected_match_risk=("known_expected_match_risk", "max"),
        )
        .reset_index()
    )
    base_risk["weighted_path_veto"] = (
        base_risk["neutral_slowdown_risk"].astype(bool)
        | base_risk["static_slowdown_risk"].astype(bool)
        | (base_risk["cap_risk"].astype(bool) if cap_veto else False)
        | base_risk["known_expected_match_risk"].astype(bool)
    )
    policy = row.merge(
        base_risk[
            [
                "base_instance_id",
                "weighted_path_veto",
                "neutral_slowdown_risk",
                "static_slowdown_risk",
                "cap_risk",
                "known_expected_match_risk",
            ]
        ],
        on="base_instance_id",
        how="left",
        suffixes=("", "_base"),
    )
    use_adapter = ~policy["weighted_path_veto"].astype(bool)
    for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
        policy[f"policy_{metric}"] = np.where(
            use_adapter,
            policy[f"{metric}__event_adapter_final"],
            policy[f"{metric}__plain_unguided_glucose"],
        )
        policy[f"policy_minus_plain_{metric}"] = (
            policy[f"policy_{metric}"] - policy[f"{metric}__plain_unguided_glucose"]
        )
        policy[f"adapter_minus_plain_{metric}"] = (
            policy[f"{metric}__event_adapter_final"] - policy[f"{metric}__plain_unguided_glucose"]
        )
        if f"{metric}__cached_trace_no_adapter_final" in policy.columns:
            policy[f"adapter_minus_cached_{metric}"] = (
                policy[f"{metric}__event_adapter_final"] - policy[f"{metric}__cached_trace_no_adapter_final"]
            )
    policy["policy_solver_path_role"] = np.where(use_adapter, "event_adapter_allowed", "plain_fallback_hard_veto")
    base_policy = (
        policy.groupby(["family", "base_instance_id", "control_type", "scale", "benchmark_role"], sort=True)
        .agg(
            rows=("repeat_id", "size"),
            variants=("variant", "nunique"),
            repeats=("repeat_id", "nunique"),
            weighted_path_veto=("weighted_path_veto", "first"),
            neutral_slowdown_risk=("neutral_slowdown_risk_base", "first"),
            static_slowdown_risk=("static_slowdown_risk_base", "first"),
            cap_risk=("cap_risk_base", "first"),
            known_expected_match_risk=("known_expected_match_risk_base", "first"),
            neutral_delta_cpu_mean=("neutral_delta_cpu", "mean"),
            neutral_rel_delta_cpu_mean=("neutral_rel_delta_cpu", "mean"),
            static_delta_vs_neutral_cpu_mean=("static_delta_vs_neutral_cpu", "mean"),
            static_rel_delta_vs_neutral_cpu_mean=("static_rel_delta_vs_neutral_cpu", "mean"),
            plain_final_cpu_mean=("final_cpu_time__plain_unguided_glucose", "mean"),
            neutral_final_cpu_mean=("final_cpu_time__neutral_weighted_glucose", "mean"),
            static_final_cpu_mean=("final_cpu_time__static_weighted_glucose", "mean"),
            adapter_final_cpu_mean=("final_cpu_time__event_adapter_final", "mean"),
            warmup_cpu_mean=("warmup_cpu_time__event_adapter_final", "mean"),
            event_l2_sum_mean=("event_state_l2_sum__event_adapter_final", "mean"),
            graph_gate_open_fraction=("event_adapter_graph_gate_open__event_adapter_final", "mean"),
            policy_minus_plain_protocol=("policy_minus_plain_protocol_accounted_time", "mean"),
            policy_minus_plain_final_cpu=("policy_minus_plain_final_cpu_time", "mean"),
            adapter_minus_plain_protocol=("adapter_minus_plain_protocol_accounted_time", "mean"),
            adapter_minus_plain_final_cpu=("adapter_minus_plain_final_cpu_time", "mean"),
            adapter_minus_cached_final_cpu=("adapter_minus_cached_final_cpu_time", "mean"),
            adapter_minus_cached_decisions=("adapter_minus_cached_final_decisions", "mean"),
            adapter_minus_cached_conflicts=("adapter_minus_cached_final_conflicts", "mean"),
        )
        .reset_index()
    )
    summary = {
        "abs_threshold": float(abs_threshold),
        "rel_threshold": float(rel_threshold),
        "near_cap_fraction": float(near_cap_fraction),
        "cap_veto": bool(cap_veto),
        "slowdown_logic": slowdown_logic,
        "bases": int(base_policy["base_instance_id"].nunique()),
        "weighted_vetoed_bases": int(base_policy["weighted_path_veto"].astype(bool).sum()),
        "policy_protocol_delta_mean": float(base_policy["policy_minus_plain_protocol"].mean()),
        "policy_final_cpu_delta_mean": float(base_policy["policy_minus_plain_final_cpu"].mean()),
        "adapter_protocol_delta_mean": float(base_policy["adapter_minus_plain_protocol"].mean()),
        "adapter_final_cpu_delta_mean": float(base_policy["adapter_minus_plain_final_cpu"].mean()),
        "adapter_cached_final_cpu_delta_mean": float(base_policy["adapter_minus_cached_final_cpu"].mean()),
    }
    for family, group in base_policy.groupby("family", sort=True):
        summary[f"{family}_bases"] = int(group["base_instance_id"].nunique())
        summary[f"{family}_weighted_vetoed_bases"] = int(group["weighted_path_veto"].astype(bool).sum())
        summary[f"{family}_policy_protocol_delta_mean"] = float(group["policy_minus_plain_protocol"].mean())
        summary[f"{family}_adapter_protocol_delta_mean"] = float(group["adapter_minus_plain_protocol"].mean())
        summary[f"{family}_adapter_cached_final_cpu_delta_mean"] = float(group["adapter_minus_cached_final_cpu"].mean())
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
    best = sweep.sort_values(["policy_protocol_delta_mean", "weighted_vetoed_bases"]).head(10)
    family = (
        policy.groupby("family", sort=True)
        .agg(
            bases=("base_instance_id", "nunique"),
            weighted_vetoed_bases=("weighted_path_veto", lambda values: int(pd.Series(values).astype(bool).sum())),
            neutral_risk_bases=("neutral_slowdown_risk", lambda values: int(pd.Series(values).astype(bool).sum())),
            static_risk_bases=("static_slowdown_risk", lambda values: int(pd.Series(values).astype(bool).sum())),
            cap_risk_bases=("cap_risk", lambda values: int(pd.Series(values).astype(bool).sum())),
            policy_protocol_delta_mean=("policy_minus_plain_protocol", "mean"),
            adapter_protocol_delta_mean=("adapter_minus_plain_protocol", "mean"),
            policy_final_cpu_delta_mean=("policy_minus_plain_final_cpu", "mean"),
            adapter_final_cpu_delta_mean=("adapter_minus_plain_final_cpu", "mean"),
            adapter_cached_final_cpu_delta_mean=("adapter_minus_cached_final_cpu", "mean"),
        )
        .reset_index()
        .sort_values("family")
    )
    selected_columns = [
        "family",
        "base_instance_id",
        "weighted_path_veto",
        "neutral_slowdown_risk",
        "static_slowdown_risk",
        "cap_risk",
        "neutral_delta_cpu_mean",
        "static_delta_vs_neutral_cpu_mean",
        "plain_final_cpu_mean",
        "neutral_final_cpu_mean",
        "static_final_cpu_mean",
        "policy_minus_plain_protocol",
        "adapter_minus_plain_protocol",
        "adapter_minus_cached_final_cpu",
    ]
    lines = [
        "# EchoSAT Weighted-Path Hard Veto v1",
        "",
        "This audit replays a conservative hard-veto policy over an existing runtime table. It does not train a selector and does not use event-adapter final runtime as a veto input.",
        "",
        "## Policy Inputs",
        "",
        "- neutral weighted final CPU versus plain final CPU",
        "- static weighted final CPU versus neutral weighted final CPU",
        "- near-cap risk from plain, neutral weighted, or static weighted final CPU",
        "- known expected-result mismatch risk, if present",
        "",
        "Warmup/event overhead and weak event signal are deliberately not veto inputs in v1, so complete_coloring/php mechanism candidates are not rejected only because warmup is expensive.",
        "The selected policy treats weighted slowdown as hard evidence only when both the absolute and relative slowdown thresholds are exceeded; this avoids vetoing tiny fast-instance fluctuations.",
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
        "## Selected Policy By Family",
        "",
        *markdown_table(family, max_rows=40),
        "",
        "## Selected Policy By Base",
        "",
        *markdown_table(policy[selected_columns].sort_values(["family", "base_instance_id"]), max_rows=80),
        "",
        "## Interpretation",
        "",
        "- This veto is intended to isolate weighted-path risk, not to solve event overhead.",
        "- A good policy should avoid hex/torus near-cap or weighted-path failures without vetoing all complete_coloring/php candidates.",
        "- Any later deployable gate still must use only pre-final information; this offline replay is not a speedup claim.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EchoSAT weighted-path hard-veto v1 audit.")
    parser.add_argument("--per-instance-csv", type=Path, default=DEFAULT_PER_INSTANCE)
    parser.add_argument("--policy-csv", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--sweep-csv", type=Path, default=DEFAULT_SWEEP)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--selected-abs-threshold", type=float, default=0.25)
    parser.add_argument("--selected-rel-threshold", type=float, default=0.10)
    parser.add_argument("--selected-near-cap-fraction", type=float, default=0.80)
    parser.add_argument("--selected-slowdown-logic", choices=["both", "either"], default="both")
    parser.add_argument("--no-selected-cap-veto", action="store_true")
    parser.add_argument("--abs-thresholds", nargs="*", type=float, default=[0.05, 0.10, 0.25, 0.50, 1.0])
    parser.add_argument("--rel-thresholds", nargs="*", type=float, default=[0.05, 0.10, 0.25, 0.50])
    parser.add_argument("--near-cap-fractions", nargs="*", type=float, default=[0.70, 0.80, 0.90])
    parser.add_argument("--slowdown-logics", nargs="*", choices=["both", "either"], default=["both", "either"])
    parser.add_argument("--allow-weighted-no-pre", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    per_instance = pd.read_csv(resolve(args.per_instance_csv))
    validate_input(per_instance, allow_weighted_no_pre=bool(args.allow_weighted_no_pre))
    wide = method_wide(per_instance)
    sweep_rows = []
    selected = None
    selected_cap_veto = not bool(args.no_selected_cap_veto)
    for cap_veto in [False, True]:
        for slowdown_logic in args.slowdown_logics:
            for abs_threshold in args.abs_thresholds:
                for rel_threshold in args.rel_thresholds:
                    for near_cap_fraction in args.near_cap_fractions:
                        policy, summary = evaluate_policy(
                            wide,
                            abs_threshold=float(abs_threshold),
                            rel_threshold=float(rel_threshold),
                            near_cap_fraction=float(near_cap_fraction),
                            cap_veto=bool(cap_veto),
                            slowdown_logic=str(slowdown_logic),
                        )
                        sweep_rows.append(summary)
                        if (
                            bool(cap_veto) == bool(selected_cap_veto)
                            and str(slowdown_logic) == str(args.selected_slowdown_logic)
                            and abs(float(abs_threshold) - float(args.selected_abs_threshold)) < 1.0e-12
                            and abs(float(rel_threshold) - float(args.selected_rel_threshold)) < 1.0e-12
                            and abs(float(near_cap_fraction) - float(args.selected_near_cap_fraction)) < 1.0e-12
                        ):
                            selected = policy
    if selected is None:
        selected, _ = evaluate_policy(
            wide,
            abs_threshold=float(args.selected_abs_threshold),
            rel_threshold=float(args.selected_rel_threshold),
            near_cap_fraction=float(args.selected_near_cap_fraction),
            cap_veto=bool(selected_cap_veto),
            slowdown_logic=str(args.selected_slowdown_logic),
        )
    sweep = pd.DataFrame(sweep_rows).sort_values(["policy_protocol_delta_mean", "weighted_vetoed_bases"]).reset_index(drop=True)
    policy_path = resolve(args.policy_csv)
    sweep_path = resolve(args.sweep_csv)
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(policy_path, index=False)
    sweep.to_csv(sweep_path, index=False)
    write_doc(resolve(args.doc), selected, sweep, policy_path.relative_to(ROOT), sweep_path.relative_to(ROOT))
    print(f"wrote {policy_path}")
    print(f"wrote {sweep_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
