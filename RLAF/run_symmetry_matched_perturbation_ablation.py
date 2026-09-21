from __future__ import annotations

import argparse
import hashlib
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from pysat.formula import CNF

from run_symmetry_solver_protocol_preflight import clean_solver_params, solver_cli_number
from src.solving.solver import solve_cnf


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_harder_baseline_target_manifest.csv"
DEFAULT_REFERENCE = ROOT / "runs/analysis/symmetry_grpo_harder_random_control_adapter_param_shift.csv"
DEFAULT_BASELINE = ROOT / "runs/analysis/symmetry_grpo_speedup_best_harder_baseline_per_instance.csv"
DEFAULT_PER_INSTANCE = ROOT / "runs/analysis/symmetry_harder_matched_perturbation_per_instance.csv"
DEFAULT_BY_BASE = ROOT / "runs/analysis/symmetry_harder_matched_perturbation_by_base.csv"
DEFAULT_BY_FAMILY = ROOT / "runs/analysis/symmetry_harder_matched_perturbation_by_family.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_harder_matched_perturbation_ablation.md"

METHODS = ["matched_weight_only", "matched_weight_phase"]


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values
    return values.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def stable_seed(*parts: Any) -> int:
    text = "::".join(map(str, parts))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little") % (2**31 - 1)


def reference_lookup(reference: pd.DataFrame) -> tuple[dict[tuple[str, str, int], dict[str, float]], dict[str, float]]:
    ref = reference.copy()
    ref["phase_flip_frac"] = pd.to_numeric(ref["phase_flip_frac"], errors="coerce").fillna(0.0)
    ref["weight_delta_abs_mean"] = pd.to_numeric(ref["weight_delta_abs_mean"], errors="coerce").fillna(0.0)
    ref["weight_ratio_mean"] = pd.to_numeric(ref["weight_ratio_mean"], errors="coerce").fillna(1.0)
    ref["weight_static_mean"] = pd.to_numeric(ref.get("weight_static_mean", pd.Series(1.0, index=ref.index)), errors="coerce").fillna(1.0)
    ref["relative_abs_delta"] = ref["weight_delta_abs_mean"] / ref["weight_static_mean"].clip(lower=1.0e-6)
    global_stats = {
        "phase_flip_frac": float(ref["phase_flip_frac"].mean()),
        "relative_abs_delta": float(ref["relative_abs_delta"].mean()),
        "weight_ratio_mean": float(ref["weight_ratio_mean"].mean()),
    }
    lookup: dict[tuple[str, str, int], dict[str, float]] = {}
    for _, row in ref.iterrows():
        lookup[(str(row["base_instance_id"]), str(row["variant"]), int(row["repeat_id"]))] = {
            "phase_flip_frac": float(row["phase_flip_frac"]),
            "relative_abs_delta": float(row["relative_abs_delta"]),
            "weight_ratio_mean": float(row["weight_ratio_mean"]),
        }
    return lookup, global_stats


def ratio_probabilities(relative_abs_delta: float, weight_ratio_mean: float) -> tuple[float, float]:
    """Fit a clipped three-point ratio distribution: exp(+1), exp(-1), or 1."""
    high_delta = math.e - 1.0
    low_delta = 1.0 - math.exp(-1.0)
    target_abs = max(0.0, finite_float(relative_abs_delta, 0.0))
    target_signed = finite_float(weight_ratio_mean, 1.0) - 1.0
    p_high = max(0.0, (target_abs + target_signed) / (2.0 * high_delta))
    p_low = max(0.0, (target_abs - target_signed) / (2.0 * low_delta))
    total = p_high + p_low
    if total > 0.95:
        scale = 0.95 / total
        p_high *= scale
        p_low *= scale
    return p_high, p_low


def matched_var_params(
    num_vars: int,
    *,
    method: str,
    stats: dict[str, float],
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(int(seed))
    p_high, p_low = ratio_probabilities(
        relative_abs_delta=float(stats.get("relative_abs_delta", 0.0)),
        weight_ratio_mean=float(stats.get("weight_ratio_mean", 1.0)),
    )
    draws = rng.random(int(num_vars))
    weights = np.ones(int(num_vars), dtype=np.float64)
    weights[draws < p_high] = math.e
    weights[(draws >= p_high) & (draws < p_high + p_low)] = math.exp(-1.0)
    phases = np.ones(int(num_vars), dtype=np.float64)
    if method == "matched_weight_phase":
        flip_frac = min(max(float(stats.get("phase_flip_frac", 0.0)), 0.0), 1.0)
        flip_count = int(round(flip_frac * int(num_vars)))
        if flip_count > 0:
            phases[rng.choice(int(num_vars), size=min(flip_count, int(num_vars)), replace=False)] = 0.0
    elif method != "matched_weight_only":
        raise ValueError(f"unknown matched perturbation method {method!r}")
    return np.stack([phases, weights], axis=1)


def solve_one(
    *,
    row: dict[str, Any],
    repeat_id: int,
    method: str,
    stats: dict[str, float],
    final_seed: int,
    sample_seed: int,
    final_params: dict[str, Any],
    solver: str,
) -> dict[str, Any]:
    cnf_path = str(row["cnf_path"])
    cnf = CNF(from_file=cnf_path)
    var_params = matched_var_params(
        int(cnf.nv),
        method=method,
        stats=stats,
        seed=sample_seed,
    )
    start = time.perf_counter()
    result = solve_cnf(
        cnf.clauses,
        var_params=var_params,
        seed=int(final_seed),
        solver=solver,
        **final_params,
    )
    wall = time.perf_counter() - start
    expected = str(row.get("expected_result", "UNKNOWN"))
    known = expected in {"SATISFIABLE", "UNSATISFIABLE"}
    final_result = str(result.get("Result", "INDETERMINATE"))
    final_solved = final_result in {"SATISFIABLE", "UNSATISFIABLE"}
    return {
        "family": str(row["family"]),
        "instance_id": str(row["instance_id"]),
        "base_instance_id": str(row["base_instance_id"]),
        "variant": str(row["variant"]),
        "expected_result": expected,
        "num_vars": int(row["num_vars"]),
        "num_clauses": int(row["num_clauses"]),
        "cnf_path": cnf_path,
        "method": method,
        "repeat_id": int(repeat_id),
        "seed": int(final_seed),
        "final_seed": int(final_seed),
        "sample_seed": int(sample_seed),
        "solver": solver,
        "final_cpu_lim": float(final_params.get("cpu-lim", float("nan"))),
        "final_result": final_result,
        "final_solved": bool(final_solved),
        "known_expected_result": bool(known),
        "final_expected_match": bool(final_result == expected) if known else False,
        "final_known_expected_match": bool(final_result == expected) if known else False,
        "final_cpu_time": finite_float(result.get("CPU time")),
        "final_wall_time": float(wall),
        "final_decisions": finite_float(result.get("decisions")),
        "final_conflicts": finite_float(result.get("conflicts")),
        "final_propagations": finite_float(result.get("propagations")),
        "final_restarts": finite_float(result.get("restarts")),
        "final_solver_returncode": int(result.get("solver_returncode", -1)),
        "solver_timeout": bool(result.get("solver_timeout", False)),
        "protocol_accounted_time": finite_float(result.get("CPU time")),
        "protocol_wall_time": float(wall),
        "matched_phase_flip_frac": float(stats.get("phase_flip_frac", 0.0)),
        "matched_relative_abs_delta": float(stats.get("relative_abs_delta", 0.0)),
        "matched_weight_ratio_mean": float(stats.get("weight_ratio_mean", 1.0)),
        "matched_p_high": ratio_probabilities(float(stats.get("relative_abs_delta", 0.0)), float(stats.get("weight_ratio_mean", 1.0)))[0],
        "matched_p_low": ratio_probabilities(float(stats.get("relative_abs_delta", 0.0)), float(stats.get("weight_ratio_mean", 1.0)))[1],
        "event_audit_role": str(row.get("event_audit_role", "")),
        "symmetry_strength": str(row.get("symmetry_strength", "")),
        "control_type": str(row.get("control_type", "")),
        "scale": str(row.get("scale", "")),
        "scale_key": str(row.get("scale_key", "")),
        "benchmark_role": str(row.get("benchmark_role", "")),
        "family_scale": str(row.get("family_scale", "")),
        "variant_role": str(row.get("variant_role", "")),
        "permutation_variant": bool(str(row.get("permutation_variant", "False")).lower() == "true"),
        "source": str(row.get("source", "")),
    }


def run_ablation(args: argparse.Namespace) -> pd.DataFrame:
    manifest = pd.read_csv(resolve(args.manifest))
    reference = pd.read_csv(resolve(args.reference_csv))
    lookup, global_stats = reference_lookup(reference)
    if args.families:
        manifest = manifest[manifest["family"].astype(str).isin(set(args.families))].copy()
    if args.control_types:
        manifest = manifest[manifest["control_type"].astype(str).isin(set(args.control_types))].copy()
    if manifest.empty:
        raise ValueError("manifest filters produced no rows")
    methods = list(args.methods or METHODS)
    final_params = clean_solver_params(
        {
            "cpu-lim": solver_cli_number(args.final_cpu_lim),
            "rnd-freq": args.rnd_freq,
            "K": args.K,
        }
    )
    inputs = []
    for repeat_id in range(int(args.repeats)):
        final_seed = int(args.seed) + repeat_id
        for _, instance in manifest.iterrows():
            key = (str(instance["base_instance_id"]), str(instance["variant"]), int(repeat_id))
            stats = lookup.get(key, global_stats)
            for method in methods:
                sample_seed = stable_seed(args.sample_seed, method, instance["base_instance_id"], instance["variant"], repeat_id)
                inputs.append(
                    {
                        "row": instance.to_dict(),
                        "repeat_id": repeat_id,
                        "method": method,
                        "stats": stats,
                        "final_seed": final_seed,
                        "sample_seed": sample_seed,
                        "final_params": final_params,
                        "solver": str(args.solver),
                    }
                )
    print(f"running matched perturbation ablation: {len(inputs)} solver calls, workers={args.num_workers}")
    rows = Parallel(n_jobs=max(1, int(args.num_workers)))(
        delayed(solve_one)(**item)
        for item in inputs
    )
    return pd.DataFrame(rows).sort_values(["family", "base_instance_id", "variant", "repeat_id", "method"]).reset_index(drop=True)


def comparison_frames(ablation: pd.DataFrame, baseline_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline = pd.read_csv(baseline_path)
    baseline_methods = [
        "plain_unguided_glucose",
        "neutral_weighted_glucose",
        "static_weighted_glucose",
        "event_adapter_final",
    ]
    keys = ["family", "base_instance_id", "variant", "repeat_id"]
    metrics = ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts", "final_solved", "final_known_expected_match"]
    base = baseline[baseline["method"].astype(str).isin(baseline_methods)].copy()
    wide_base = base.pivot_table(index=keys, columns="method", values=metrics, aggfunc="first")
    wide_base.columns = [f"{metric}__{method}" for metric, method in wide_base.columns]
    wide_base = wide_base.reset_index()
    meta_cols = [
        "control_type",
        "scale",
        "benchmark_role",
        "family_scale",
        "symmetry_strength",
        "num_vars",
        "num_clauses",
    ]
    meta = ablation.sort_values(keys).drop_duplicates(keys)[keys + [c for c in meta_cols if c in ablation.columns]]
    rows = []
    for method, group in ablation.groupby("method", sort=True):
        method_wide = group.pivot_table(index=keys, values=metrics, aggfunc="first").reset_index()
        method_wide = method_wide.rename(columns={metric: f"{metric}__{method}" for metric in metrics})
        joined = meta.merge(wide_base, on=keys, how="left").merge(method_wide, on=keys, how="inner")
        joined["method"] = method
        for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
            for baseline_method in ["plain_unguided_glucose", "static_weighted_glucose", "event_adapter_final"]:
                left = f"{metric}__{method}"
                right = f"{metric}__{baseline_method}"
                if left in joined.columns and right in joined.columns:
                    joined[f"delta_vs_{baseline_method}_{metric}"] = joined[left] - joined[right]
        rows.append(joined)
    comparison = pd.concat(rows, ignore_index=True)
    group_cols = [
        "method",
        "family",
        "base_instance_id",
        "control_type",
        "scale",
        "benchmark_role",
        "family_scale",
    ]
    aggregations: dict[str, tuple[str, Any]] = {
        "rows": ("variant", "size"),
        "variants": ("variant", "nunique"),
        "repeats": ("repeat_id", "nunique"),
    }
    for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
        for baseline_method in ["plain_unguided_glucose", "static_weighted_glucose", "event_adapter_final"]:
            column = f"delta_vs_{baseline_method}_{metric}"
            if column in comparison.columns:
                aggregations[f"mean_{column}"] = (column, "mean")
                aggregations[f"median_{column}"] = (column, "median")
                aggregations[f"improved_rows_{column}"] = (column, lambda values: int((pd.to_numeric(values, errors="coerce") < 0.0).sum()))
    by_base = comparison.groupby(group_cols, sort=True).agg(**aggregations).reset_index()
    return comparison, by_base


def family_summary(by_base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (method, family), group in by_base.groupby(["method", "family"], sort=True):
        row = {
            "method": method,
            "family": family,
            "bases": int(group["base_instance_id"].nunique()),
            "rows": int(group["rows"].sum()),
        }
        for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
            for baseline_method in ["plain_unguided_glucose", "static_weighted_glucose", "event_adapter_final"]:
                column = f"mean_delta_vs_{baseline_method}_{metric}"
                if column in group.columns:
                    row[column] = float(group[column].mean())
                    row[f"better_bases_vs_{baseline_method}_{metric}"] = int((group[column] < 0.0).sum())
        rows.append(row)
    return pd.DataFrame(rows)


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


def write_doc(path: Path, *, per_instance: Path, by_base: Path, by_family: Path, family: pd.DataFrame) -> None:
    view_cols = [
        "method",
        "family",
        "bases",
        "mean_delta_vs_plain_unguided_glucose_final_cpu_time",
        "better_bases_vs_plain_unguided_glucose_final_cpu_time",
        "mean_delta_vs_plain_unguided_glucose_protocol_accounted_time",
        "better_bases_vs_plain_unguided_glucose_protocol_accounted_time",
        "mean_delta_vs_event_adapter_final_final_cpu_time",
        "better_bases_vs_event_adapter_final_final_cpu_time",
    ]
    view = family[[c for c in view_cols if c in family.columns]].sort_values(["method", "family"])
    random_view = view[view["family"].astype(str).eq("random_3sat_control")].copy()
    lines = [
        "# Matched Non-Learned Perturbation Ablation",
        "",
        "This runs weighted Glucose with non-learned variable weights matched to the observed GRPO random-control adapter perturbation scale. It is a controlled ablation, not training and not a speedup claim.",
        "",
        "## Artifacts",
        "",
        f"- per-instance CSV: `{per_instance}`",
        f"- base summary CSV: `{by_base}`",
        f"- family summary CSV: `{by_family}`",
        "",
        "## Random-Control Readout",
        "",
        *markdown_table(random_view, max_rows=10),
        "",
        "## Family Summary",
        "",
        *markdown_table(view, max_rows=40),
        "",
        "## Interpretation Guide",
        "",
        "- If matched perturbation wins random controls similarly to GRPO, the current GRPO gain is likely generic weighted-search perturbation.",
        "- If matched perturbation does not win random controls, learned static/event structure is doing something beyond a simple matched random perturbation.",
        "- `matched_weight_only` changes weights only and keeps all positive neutral phase.",
        "- `matched_weight_phase` adds a small matched phase-flip rate on top of the weight perturbation.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run matched non-learned perturbation baseline on SAT symmetry target manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--reference-csv", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--baseline-per-instance-csv", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--per-instance-csv", type=Path, default=DEFAULT_PER_INSTANCE)
    parser.add_argument("--comparison-csv", type=Path, default=ROOT / "runs/analysis/symmetry_harder_matched_perturbation_comparison.csv")
    parser.add_argument("--by-base-csv", type=Path, default=DEFAULT_BY_BASE)
    parser.add_argument("--by-family-csv", type=Path, default=DEFAULT_BY_FAMILY)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--methods", nargs="*", default=METHODS, choices=METHODS)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--control-types", nargs="*", default=None)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--sample-seed", type=int, default=1729)
    parser.add_argument("--final-cpu-lim", type=float, default=10.0)
    parser.add_argument("--rnd-freq", type=float, default=0.0)
    parser.add_argument("--K", type=float, default=0.1)
    parser.add_argument("--solver", default="glucose")
    parser.add_argument("--num-workers", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    per_instance = run_ablation(args)
    per_instance_path = resolve(args.per_instance_csv)
    comparison_path = resolve(args.comparison_csv)
    by_base_path = resolve(args.by_base_csv)
    by_family_path = resolve(args.by_family_csv)
    per_instance_path.parent.mkdir(parents=True, exist_ok=True)
    per_instance.to_csv(per_instance_path, index=False)
    comparison, by_base = comparison_frames(per_instance, resolve(args.baseline_per_instance_csv))
    comparison.to_csv(comparison_path, index=False)
    by_base.to_csv(by_base_path, index=False)
    by_family = family_summary(by_base).sort_values(["method", "family"]).reset_index(drop=True)
    by_family.to_csv(by_family_path, index=False)
    write_doc(
        resolve(args.doc),
        per_instance=per_instance_path.relative_to(ROOT),
        by_base=by_base_path.relative_to(ROOT),
        by_family=by_family_path.relative_to(ROOT),
        family=by_family,
    )
    print(f"wrote {per_instance_path}")
    print(f"wrote {comparison_path}")
    print(f"wrote {by_base_path}")
    print(f"wrote {by_family_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
