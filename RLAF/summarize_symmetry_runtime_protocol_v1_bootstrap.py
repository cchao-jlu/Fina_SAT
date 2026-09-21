from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
METHOD_ORDER = [
    "plain_unguided_glucose",
    "neutral_weighted_glucose",
    "static_weighted_glucose",
    "cached_trace_no_adapter_final",
    "event_adapter_final",
]
METHOD_PAIRS = [
    ("neutral_weighted_glucose", "plain_unguided_glucose", "weighted_binary_input_delta"),
    ("static_weighted_glucose", "neutral_weighted_glucose", "static_weights_delta"),
    ("cached_trace_no_adapter_final", "static_weighted_glucose", "event_collection_overhead_delta"),
    ("event_adapter_final", "cached_trace_no_adapter_final", "adapter_delta_inference_delta"),
]
STRATA = ["__overall__", "family", "control_type", "scale", "benchmark_role", "family_scale"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Base-instance paired bootstrap for SAT symmetry runtime protocol v1.")
    parser.add_argument("--per-instance-csv", type=Path, default=ROOT / "runs/analysis/symmetry_runtime_protocol_v1_per_instance.csv")
    parser.add_argument("--out-csv", type=Path, default=ROOT / "runs/analysis/symmetry_runtime_protocol_v1_bootstrap_ci.csv")
    parser.add_argument("--samples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--alpha", type=float, default=0.05)
    return parser.parse_args()


def base_method_frame(frame: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        column
        for column in [
            "base_instance_id",
            "family",
            "control_type",
            "scale",
            "benchmark_role",
            "family_scale",
            "method",
        ]
        if column in frame.columns
    ]
    aggregations: dict[str, tuple[str, Any]] = {
        "rows": ("instance_id", "count"),
        "variants": ("variant", "nunique"),
        "repeats": ("repeat_id", "nunique"),
        "solved_rate": ("final_solved", lambda values: float(pd.Series(values).astype(bool).mean())),
        "known_expected_rows": ("known_expected_result", lambda values: int(pd.Series(values).astype(bool).sum())),
        "known_expected_match_rate": (
            "final_known_expected_match",
            lambda values: float(pd.Series(values).astype(bool).mean()),
        ),
        "mean_final_cpu_time": ("final_cpu_time", "mean"),
        "mean_protocol_accounted_time": ("protocol_accounted_time", "mean"),
        "mean_final_decisions": ("final_decisions", "mean"),
        "mean_final_conflicts": ("final_conflicts", "mean"),
    }
    base = frame.groupby(group_columns, sort=True).agg(**aggregations).reset_index()
    known = frame[frame["known_expected_result"].astype(bool)].copy()
    if known.empty:
        base["known_expected_match_rate"] = np.nan
        return base
    known_rates = (
        known.groupby(group_columns, sort=True)
        .agg(
            known_expected_rows=("instance_id", "count"),
            known_expected_match_rate=("final_known_expected_match", lambda values: float(pd.Series(values).astype(bool).mean())),
        )
        .reset_index()
    )
    base = base.drop(columns=["known_expected_rows", "known_expected_match_rate"]).merge(
        known_rates,
        on=group_columns,
        how="left",
    )
    base["known_expected_match_rate"] = base["known_expected_match_rate"].where(
        base["known_expected_rows"].fillna(0).astype(int) > 0,
        np.nan,
    )
    base["known_expected_rows"] = base["known_expected_rows"].fillna(0).astype(int)
    return base


def paired_base_delta(base_methods: pd.DataFrame, method: str, baseline: str, label: str) -> pd.DataFrame:
    index_columns = [
        column
        for column in ["base_instance_id", "family", "control_type", "scale", "benchmark_role", "family_scale"]
        if column in base_methods.columns
    ]
    metric_columns = [
        "solved_rate",
        "known_expected_match_rate",
        "mean_final_cpu_time",
        "mean_protocol_accounted_time",
        "mean_final_decisions",
        "mean_final_conflicts",
    ]
    left = base_methods[base_methods["method"].astype(str) == method][index_columns + metric_columns].copy()
    right = base_methods[base_methods["method"].astype(str) == baseline][index_columns + metric_columns].copy()
    paired = left.merge(right, on=index_columns, how="inner", suffixes=("_method", "_baseline"))
    for metric in metric_columns:
        paired[f"delta_{metric}"] = paired[f"{metric}_method"] - paired[f"{metric}_baseline"]
    paired["method"] = method
    paired["baseline"] = baseline
    paired["delta_label"] = label
    return paired


def bootstrap_mean(values: np.ndarray, rng: np.random.Generator, samples: int, alpha: float) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "mean": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "positive_probability": float("nan"),
            "negative_probability": float("nan"),
        }
    if values.size == 1:
        mean = float(values[0])
        return {
            "mean": mean,
            "ci_low": mean,
            "ci_high": mean,
            "positive_probability": float(mean > 0.0),
            "negative_probability": float(mean < 0.0),
        }
    indices = rng.integers(0, values.size, size=(int(samples), values.size))
    means = values[indices].mean(axis=1)
    return {
        "mean": float(values.mean()),
        "ci_low": float(np.quantile(means, alpha / 2.0)),
        "ci_high": float(np.quantile(means, 1.0 - alpha / 2.0)),
        "positive_probability": float((means > 0.0).mean()),
        "negative_probability": float((means < 0.0).mean()),
    }


def summarize_stratum(
    paired: pd.DataFrame,
    stratum_column: str,
    rng: np.random.Generator,
    samples: int,
    alpha: float,
) -> list[dict[str, object]]:
    if stratum_column == "__overall__":
        groups = [("__overall__", paired)]
    elif stratum_column not in paired.columns:
        return []
    else:
        groups = list(paired.groupby(stratum_column, sort=True))
    rows: list[dict[str, object]] = []
    delta_metrics = [
        "delta_solved_rate",
        "delta_known_expected_match_rate",
        "delta_mean_final_cpu_time",
        "delta_mean_protocol_accounted_time",
        "delta_mean_final_decisions",
        "delta_mean_final_conflicts",
    ]
    for stratum_value, group in groups:
        for metric in delta_metrics:
            summary = bootstrap_mean(group[metric].to_numpy(dtype=np.float64), rng=rng, samples=samples, alpha=alpha)
            rows.append(
                {
                    "stratum": stratum_column,
                    "stratum_value": str(stratum_value),
                    "delta_label": str(group["delta_label"].iloc[0]),
                    "method": str(group["method"].iloc[0]),
                    "baseline": str(group["baseline"].iloc[0]),
                    "metric": metric,
                    "base_instances": int(group["base_instance_id"].nunique()),
                    "mean": summary["mean"],
                    "ci_low": summary["ci_low"],
                    "ci_high": summary["ci_high"],
                    "positive_probability": summary["positive_probability"],
                    "negative_probability": summary["negative_probability"],
                }
            )
    return rows


def main() -> None:
    args = parse_args()
    frame = pd.read_csv(args.per_instance_csv)
    base_methods = base_method_frame(frame)
    rng = np.random.default_rng(int(args.seed))
    rows: list[dict[str, object]] = []
    for method, baseline, label in METHOD_PAIRS:
        paired = paired_base_delta(base_methods, method=method, baseline=baseline, label=label)
        for stratum in STRATA:
            rows.extend(
                summarize_stratum(
                    paired,
                    stratum_column=stratum,
                    rng=rng,
                    samples=int(args.samples),
                    alpha=float(args.alpha),
                )
            )
    out = pd.DataFrame(rows)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False)
    print(f"wrote {args.out_csv}")


if __name__ == "__main__":
    main()
