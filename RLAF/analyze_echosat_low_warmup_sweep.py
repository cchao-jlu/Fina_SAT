from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
METHODS = [
    "plain_unguided_glucose",
    "neutral_weighted_glucose",
    "static_weighted_glucose",
    "cached_trace_no_adapter_final",
    "event_adapter_final",
]
DEFAULT_GLOB = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc*_per_instance.csv"
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_observations.csv"
DEFAULT_OVERALL = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_overall.csv"
DEFAULT_BY_FAMILY = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_by_family.csv"
DEFAULT_BY_BASE = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_by_base.csv"
DEFAULT_DOC = ROOT / "docs/echosat_adapter_delta_v2_iter235_low_warmup_sweep.md"


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> Path | str:
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return str(path)


def bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values.fillna(False)
    return values.fillna(False).astype(str).str.lower().isin({"1", "true", "yes", "y"})


def finite_float(value: Any, default: float = math.nan) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def method_column(wide: pd.DataFrame, metric: str, method: str) -> pd.Series:
    column = (metric, method)
    if column in wide.columns:
        return pd.to_numeric(wide[column], errors="coerce")
    return pd.Series(math.nan, index=wide.index)


def unique_budget(frame: pd.DataFrame, path: Path) -> int:
    if "warmup_conflicts" not in frame.columns:
        raise ValueError(f"{path} has no warmup_conflicts column")
    values = pd.to_numeric(frame["warmup_conflicts"], errors="coerce").dropna().unique()
    if len(values) != 1:
        raise ValueError(f"{path} has mixed warmup_conflicts values: {sorted(values)}")
    return int(values[0])


def validate_protocol(frame: pd.DataFrame, path: Path, allow_weighted_no_pre: bool) -> None:
    methods = set(frame["method"].astype(str).unique())
    missing = sorted(set(METHODS).difference(methods))
    if missing:
        raise ValueError(f"{path} is missing methods: {missing}")
    if "weighted_no_pre" in frame.columns and not allow_weighted_no_pre:
        if bool(bool_series(frame["weighted_no_pre"]).any()):
            raise ValueError(f"{path} contains weighted_no_pre=True rows")
    if "solver_path_role" in frame.columns:
        roles = sorted(set(frame["solver_path_role"].dropna().astype(str)))
        if roles != ["patched_pretrue_main"]:
            raise ValueError(f"{path} has non-main solver_path_role values: {roles}")


def observations_from_file(path: Path, allow_weighted_no_pre: bool) -> pd.DataFrame:
    frame = pd.read_csv(path)
    validate_protocol(frame, path, allow_weighted_no_pre=allow_weighted_no_pre)
    budget = unique_budget(frame, path)
    keys = ["repeat_id", "base_instance_id", "variant", "instance_id"]
    missing_keys = [key for key in keys if key not in frame.columns]
    if missing_keys:
        raise ValueError(f"{path} is missing key columns: {missing_keys}")
    metrics = [
        "final_cpu_time",
        "protocol_accounted_time",
        "final_decisions",
        "final_conflicts",
        "final_solved",
        "final_known_expected_match",
        "known_expected_result",
        "warmup_cpu_time",
        "warmup_conflict_count",
        "warmup_decisions",
        "event_state_l2_sum",
        "event_state_nonzero_vars",
        "event_adapter_graph_gate_evidence",
        "event_adapter_graph_gate_open",
        "adapter_inference_wall_time",
    ]
    wide = frame.pivot_table(
        index=keys,
        columns="method",
        values=[metric for metric in metrics if metric in frame.columns],
        aggfunc="first",
    )
    meta_columns = [
        "family",
        "control_type",
        "scale",
        "benchmark_role",
        "symmetry_strength",
        "num_vars",
        "num_clauses",
        "final_cpu_lim",
        "warmup_cpu_lim",
        "checkpoint",
    ]
    meta = (
        frame.sort_values(keys)
        .drop_duplicates(keys)
        .set_index(keys)[[column for column in meta_columns if column in frame.columns]]
        .reindex(wide.index)
    )
    out = pd.DataFrame(
        {
            "warmup_conflicts": budget,
            "source_csv": str(path),
            "repeat_id": [idx[0] for idx in wide.index],
            "base_instance_id": [idx[1] for idx in wide.index],
            "variant": [idx[2] for idx in wide.index],
            "instance_id": [idx[3] for idx in wide.index],
            "family": meta["family"].astype(str).to_numpy() if "family" in meta.columns else "",
            "control_type": meta["control_type"].astype(str).to_numpy() if "control_type" in meta.columns else "",
            "scale": meta["scale"].astype(str).to_numpy() if "scale" in meta.columns else "",
            "benchmark_role": meta["benchmark_role"].astype(str).to_numpy() if "benchmark_role" in meta.columns else "",
            "symmetry_strength": meta["symmetry_strength"].astype(str).to_numpy()
            if "symmetry_strength" in meta.columns
            else "",
            "num_vars": pd.to_numeric(meta["num_vars"], errors="coerce").to_numpy()
            if "num_vars" in meta.columns
            else math.nan,
            "num_clauses": pd.to_numeric(meta["num_clauses"], errors="coerce").to_numpy()
            if "num_clauses" in meta.columns
            else math.nan,
            "final_cpu_lim": pd.to_numeric(meta["final_cpu_lim"], errors="coerce").to_numpy()
            if "final_cpu_lim" in meta.columns
            else math.nan,
            "warmup_cpu_lim": pd.to_numeric(meta["warmup_cpu_lim"], errors="coerce").to_numpy()
            if "warmup_cpu_lim" in meta.columns
            else math.nan,
            "checkpoint": meta["checkpoint"].astype(str).to_numpy() if "checkpoint" in meta.columns else "",
        }
    )
    for method in METHODS:
        out[f"{method}_final_cpu_time"] = method_column(wide, "final_cpu_time", method).to_numpy()
        out[f"{method}_protocol_accounted_time"] = method_column(wide, "protocol_accounted_time", method).to_numpy()
        out[f"{method}_final_decisions"] = method_column(wide, "final_decisions", method).to_numpy()
        out[f"{method}_final_conflicts"] = method_column(wide, "final_conflicts", method).to_numpy()
        out[f"{method}_final_solved"] = method_column(wide, "final_solved", method).to_numpy()
    out["known_expected_result"] = method_column(wide, "known_expected_result", "event_adapter_final").fillna(0).to_numpy()
    out["event_adapter_final_known_expected_match"] = method_column(
        wide,
        "final_known_expected_match",
        "event_adapter_final",
    ).to_numpy()
    out["warmup_cpu_time"] = method_column(wide, "warmup_cpu_time", "event_adapter_final").to_numpy()
    out["warmup_conflict_count"] = method_column(wide, "warmup_conflict_count", "event_adapter_final").to_numpy()
    out["warmup_decisions"] = method_column(wide, "warmup_decisions", "event_adapter_final").to_numpy()
    out["event_state_l2_sum"] = method_column(wide, "event_state_l2_sum", "event_adapter_final").to_numpy()
    out["event_state_nonzero_vars"] = method_column(wide, "event_state_nonzero_vars", "event_adapter_final").to_numpy()
    out["event_adapter_graph_gate_evidence"] = method_column(
        wide,
        "event_adapter_graph_gate_evidence",
        "event_adapter_final",
    ).to_numpy()
    out["event_adapter_graph_gate_open"] = method_column(
        wide,
        "event_adapter_graph_gate_open",
        "event_adapter_final",
    ).to_numpy()
    out["adapter_inference_wall_time"] = method_column(
        wide,
        "adapter_inference_wall_time",
        "event_adapter_final",
    ).to_numpy()

    out["adapter_cached_final_cpu_delta"] = (
        out["event_adapter_final_final_cpu_time"] - out["cached_trace_no_adapter_final_final_cpu_time"]
    )
    out["adapter_cached_protocol_delta"] = (
        out["event_adapter_final_protocol_accounted_time"]
        - out["cached_trace_no_adapter_final_protocol_accounted_time"]
    )
    out["adapter_plain_final_cpu_delta"] = (
        out["event_adapter_final_final_cpu_time"] - out["plain_unguided_glucose_final_cpu_time"]
    )
    out["adapter_plain_protocol_delta"] = (
        out["event_adapter_final_protocol_accounted_time"]
        - out["plain_unguided_glucose_protocol_accounted_time"]
    )
    out["adapter_cached_decisions_delta"] = (
        out["event_adapter_final_final_decisions"] - out["cached_trace_no_adapter_final_final_decisions"]
    )
    out["adapter_cached_conflicts_delta"] = (
        out["event_adapter_final_final_conflicts"] - out["cached_trace_no_adapter_final_final_conflicts"]
    )
    out["neutral_plain_final_cpu_delta"] = (
        out["neutral_weighted_glucose_final_cpu_time"] - out["plain_unguided_glucose_final_cpu_time"]
    )
    out["static_neutral_final_cpu_delta"] = (
        out["static_weighted_glucose_final_cpu_time"] - out["neutral_weighted_glucose_final_cpu_time"]
    )
    out["adapter_cached_final_cpu_improved"] = out["adapter_cached_final_cpu_delta"] < 0.0
    out["adapter_plain_final_cpu_improved"] = out["adapter_plain_final_cpu_delta"] < 0.0
    out["adapter_plain_protocol_improved"] = out["adapter_plain_protocol_delta"] < 0.0
    return out


def mean_bool(values: pd.Series) -> float:
    return float(pd.Series(values).fillna(False).astype(bool).mean())


def summarize(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(group_columns, sort=True, dropna=False)
    out = grouped.agg(
        observations=("instance_id", "size"),
        base_instances=("base_instance_id", "nunique"),
        variants=("variant", "nunique"),
        repeats=("repeat_id", "nunique"),
        final_cpu_lim=("final_cpu_lim", "first"),
        warmup_cpu_lim=("warmup_cpu_lim", "first"),
        event_adapter_solved_rows=("event_adapter_final_final_solved", "sum"),
        known_expected_rows=("known_expected_result", "sum"),
        known_expected_match_rows=("event_adapter_final_known_expected_match", "sum"),
        warmup_cpu_mean=("warmup_cpu_time", "mean"),
        warmup_cpu_median=("warmup_cpu_time", "median"),
        warmup_conflict_count_mean=("warmup_conflict_count", "mean"),
        event_state_l2_sum_mean=("event_state_l2_sum", "mean"),
        event_state_nonzero_vars_mean=("event_state_nonzero_vars", "mean"),
        graph_gate_open_fraction=("event_adapter_graph_gate_open", "mean"),
        adapter_cached_final_cpu_delta_mean=("adapter_cached_final_cpu_delta", "mean"),
        adapter_cached_final_cpu_delta_median=("adapter_cached_final_cpu_delta", "median"),
        adapter_cached_protocol_delta_mean=("adapter_cached_protocol_delta", "mean"),
        adapter_plain_final_cpu_delta_mean=("adapter_plain_final_cpu_delta", "mean"),
        adapter_plain_final_cpu_delta_median=("adapter_plain_final_cpu_delta", "median"),
        adapter_plain_protocol_delta_mean=("adapter_plain_protocol_delta", "mean"),
        adapter_plain_protocol_delta_median=("adapter_plain_protocol_delta", "median"),
        adapter_cached_decisions_delta_mean=("adapter_cached_decisions_delta", "mean"),
        adapter_cached_conflicts_delta_mean=("adapter_cached_conflicts_delta", "mean"),
        neutral_plain_final_cpu_delta_mean=("neutral_plain_final_cpu_delta", "mean"),
        static_neutral_final_cpu_delta_mean=("static_neutral_final_cpu_delta", "mean"),
        adapter_cached_final_cpu_improved_fraction=("adapter_cached_final_cpu_improved", mean_bool),
        adapter_plain_final_cpu_improved_fraction=("adapter_plain_final_cpu_improved", mean_bool),
        adapter_plain_protocol_improved_fraction=("adapter_plain_protocol_improved", mean_bool),
    )
    return out.reset_index()


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


def write_doc(
    path: Path,
    observations: pd.DataFrame,
    overall: pd.DataFrame,
    by_family: pd.DataFrame,
    by_base: pd.DataFrame,
    observation_csv: Path,
    overall_csv: Path,
    by_family_csv: Path,
    by_base_csv: Path,
) -> None:
    compact_overall = overall[
        [
            "warmup_conflicts",
            "observations",
            "base_instances",
            "warmup_cpu_mean",
            "adapter_cached_final_cpu_delta_mean",
            "adapter_plain_final_cpu_delta_mean",
            "adapter_plain_protocol_delta_mean",
            "adapter_cached_decisions_delta_mean",
            "adapter_cached_conflicts_delta_mean",
            "adapter_cached_final_cpu_improved_fraction",
            "adapter_plain_protocol_improved_fraction",
        ]
    ].sort_values("warmup_conflicts")
    compact_family = by_family[
        [
            "warmup_conflicts",
            "family",
            "observations",
            "base_instances",
            "warmup_cpu_mean",
            "adapter_cached_final_cpu_delta_mean",
            "adapter_plain_final_cpu_delta_mean",
            "adapter_plain_protocol_delta_mean",
            "adapter_cached_decisions_delta_mean",
            "adapter_cached_conflicts_delta_mean",
            "adapter_cached_final_cpu_improved_fraction",
            "adapter_plain_protocol_improved_fraction",
        ]
    ].sort_values(["warmup_conflicts", "family"])
    best_bases = by_base.sort_values(["warmup_conflicts", "adapter_cached_final_cpu_delta_mean"])[
        [
            "warmup_conflicts",
            "family",
            "base_instance_id",
            "observations",
            "warmup_cpu_mean",
            "adapter_cached_final_cpu_delta_mean",
            "adapter_plain_final_cpu_delta_mean",
            "adapter_plain_protocol_delta_mean",
            "adapter_cached_decisions_delta_mean",
            "adapter_cached_conflicts_delta_mean",
        ]
    ]
    lines = [
        "# EchoSAT AdapterDelta v2 Low-Warmup Sweep",
        "",
        "This report summarizes a fixed-checkpoint runtime sweep over lower event warmup conflict budgets. It is not training, not a learned selector, and not a solver speedup claim.",
        "",
        "## Scope",
        "",
        "- checkpoint: AdapterDelta v2 `iter=235.pt` unless overridden in the source protocol runs",
        "- intended families: `complete_coloring`, `php`, `random_3sat_control`",
        "- intended warmup conflict budgets: `1, 3, 5, 10, 20`",
        "- intended final CPU limit: `10s`",
        "- methods: plain, neutral weighted, static weighted, cached trace no-adapter, event adapter",
        "",
        "## Artifacts",
        "",
        f"- observations CSV: `{observation_csv}`",
        f"- overall CSV: `{overall_csv}`",
        f"- by-family CSV: `{by_family_csv}`",
        f"- by-base CSV: `{by_base_csv}`",
        "",
        "## Overall",
        "",
        *markdown_table(compact_overall, max_rows=20),
        "",
        "## By Family",
        "",
        *markdown_table(compact_family, max_rows=80),
        "",
        "## Best Base Rows By Budget",
        "",
        *markdown_table(best_bases, max_rows=60),
        "",
        "## Reading Rules",
        "",
        "- `adapter_cached_final_cpu_delta_mean < 0` means the adapter changed final search beneficially after paying the same warmup/event path.",
        "- `adapter_plain_protocol_delta_mean < 0` is the stricter end-to-end comparison against basic Glucose.",
        "- If low budgets preserve complete_coloring/php `adapter_cached_final_cpu_delta_mean` while reducing `warmup_cpu_mean`, the next step is a deployable pre-final gate.",
        "- If low budgets erase the adapter-cached signal, the next step is objective work with low-warmup traces rather than selector training.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize EchoSAT low-warmup runtime sweep outputs.")
    parser.add_argument("--per-instance-csvs", nargs="*", type=Path, default=None)
    parser.add_argument("--input-glob", type=Path, default=DEFAULT_GLOB)
    parser.add_argument("--observations-csv", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--overall-csv", type=Path, default=DEFAULT_OVERALL)
    parser.add_argument("--by-family-csv", type=Path, default=DEFAULT_BY_FAMILY)
    parser.add_argument("--by-base-csv", type=Path, default=DEFAULT_BY_BASE)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--families", nargs="*", default=["complete_coloring", "php", "random_3sat_control"])
    parser.add_argument("--allow-weighted-no-pre", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.per_instance_csvs:
        paths = [resolve(path) for path in args.per_instance_csvs]
    else:
        pattern = resolve(args.input_glob)
        paths = sorted(pattern.parent.glob(pattern.name))
    if not paths:
        raise SystemExit("No per-instance CSVs found for low-warmup sweep analysis.")
    observations = pd.concat(
        [observations_from_file(path, allow_weighted_no_pre=bool(args.allow_weighted_no_pre)) for path in paths],
        ignore_index=True,
    )
    if args.families:
        observations = observations[observations["family"].astype(str).isin(set(args.families))].copy()
    if observations.empty:
        raise SystemExit("No observations remain after filtering.")

    overall = summarize(observations, ["warmup_conflicts"])
    by_family = summarize(observations, ["warmup_conflicts", "family"])
    by_base = summarize(observations, ["warmup_conflicts", "family", "base_instance_id"])

    observation_path = resolve(args.observations_csv)
    overall_path = resolve(args.overall_csv)
    by_family_path = resolve(args.by_family_csv)
    by_base_path = resolve(args.by_base_csv)
    for path in [observation_path, overall_path, by_family_path, by_base_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
    observations.to_csv(observation_path, index=False)
    overall.to_csv(overall_path, index=False)
    by_family.to_csv(by_family_path, index=False)
    by_base.to_csv(by_base_path, index=False)
    write_doc(
        resolve(args.doc),
        observations=observations,
        overall=overall,
        by_family=by_family,
        by_base=by_base,
        observation_csv=display_path(observation_path),
        overall_csv=display_path(overall_path),
        by_family_csv=display_path(by_family_path),
        by_base_csv=display_path(by_base_path),
    )
    print(f"wrote {observation_path}")
    print(f"wrote {overall_path}")
    print(f"wrote {by_family_path}")
    print(f"wrote {by_base_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
