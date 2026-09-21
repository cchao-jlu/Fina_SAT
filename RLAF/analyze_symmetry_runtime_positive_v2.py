from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_ATTRIBUTION = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv"
DEFAULT_PER_INSTANCE = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_per_instance.csv"
DEFAULT_ORBITS = ROOT / "runs/analysis/symmetry_patched_pretrue_w05_cached_adapter_orbits.csv"
DEFAULT_BASE_SUMMARY = ROOT / "runs/analysis/symmetry_runtime_positive_v2_base_summary.csv"
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/symmetry_runtime_positive_v2_observations.csv"
DEFAULT_CANDIDATES = ROOT / "runs/analysis/symmetry_runtime_positive_v2_candidate_deep_dive.csv"
DEFAULT_CANDIDATE_VARIANTS = ROOT / "runs/analysis/symmetry_runtime_positive_v2_candidate_variant_summary.csv"
DEFAULT_CORRELATION = ROOT / "runs/analysis/symmetry_runtime_positive_v2_evidence_correlation.csv"
DEFAULT_EVIDENCE_BY_CLASS = ROOT / "runs/analysis/symmetry_runtime_positive_v2_evidence_by_classification.csv"
DEFAULT_ORBIT_OVERLAP = ROOT / "runs/analysis/symmetry_runtime_positive_v2_orbit_overlap.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_runtime_positive_subset_v2.md"

NAMED_STRICT_CANDIDATES = {
    "dominating_set_hex_3x6_s4",
    "subset_cardinality_bw12",
    "random_3sat_control_v20_c85_seed1901",
}


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def finite_number(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if np.isfinite(number) else default


def direction(delta: float, eps: float) -> str:
    if delta < -eps:
        return "down"
    if delta > eps:
        return "up"
    return "flat"


def majority_threshold(n: int) -> int:
    return int(n // 2 + 1)


def signed_counts(values: pd.Series, eps: float) -> dict[str, int]:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    return {
        "down": int((numeric < -eps).sum()),
        "up": int((numeric > eps).sum()),
        "flat": int((numeric.abs() <= eps).sum()),
    }


def classify_base(row: pd.Series, prefix: str) -> str:
    n = int(row[f"{prefix}_n_observations"])
    threshold = majority_threshold(n)
    cpu_down = int(row[f"{prefix}_final_cpu_down_count"]) >= threshold
    cpu_up = int(row[f"{prefix}_final_cpu_up_count"]) >= threshold
    decisions_down = int(row[f"{prefix}_final_decisions_down_count"]) >= threshold
    decisions_up = int(row[f"{prefix}_final_decisions_up_count"]) >= threshold
    conflicts_down = int(row[f"{prefix}_final_conflicts_down_count"]) >= threshold
    conflicts_up = int(row[f"{prefix}_final_conflicts_up_count"]) >= threshold

    search_down = decisions_down or conflicts_down
    search_up = decisions_up or conflicts_up
    if cpu_down and search_down and not search_up:
        return "strict_positive"
    if cpu_down and not search_down and not search_up:
        return "timing_only_positive"
    if cpu_up or search_up:
        return "negative"
    return "no_effect"


def add_runtime_deltas(frame: pd.DataFrame, cpu_eps: float, count_eps: float) -> pd.DataFrame:
    out = frame.copy()
    out["primary_delta_final_cpu"] = pd.to_numeric(out["adapter_delta_inference_delta_final_cpu"], errors="coerce")
    out["primary_delta_protocol_time"] = pd.to_numeric(
        out["adapter_delta_inference_delta_protocol_time"], errors="coerce"
    )
    out["primary_delta_final_decisions"] = pd.to_numeric(
        out["adapter_delta_inference_delta_final_decisions"], errors="coerce"
    )
    out["primary_delta_final_conflicts"] = pd.to_numeric(
        out["adapter_delta_inference_delta_final_conflicts"], errors="coerce"
    )

    event_cpu = pd.to_numeric(out.get("event_collection_overhead_delta_final_cpu", 0.0), errors="coerce").fillna(0.0)
    event_time = pd.to_numeric(
        out.get("event_collection_overhead_delta_protocol_time", out.get("cached_minus_static_protocol_time", 0.0)),
        errors="coerce",
    ).fillna(0.0)
    event_decisions = pd.to_numeric(
        out.get("event_collection_overhead_delta_final_decisions", 0.0), errors="coerce"
    ).fillna(0.0)
    event_conflicts = pd.to_numeric(
        out.get("event_collection_overhead_delta_final_conflicts", 0.0), errors="coerce"
    ).fillna(0.0)

    out["secondary_delta_final_cpu"] = event_cpu + out["primary_delta_final_cpu"]
    out["secondary_delta_protocol_time"] = event_time + out["primary_delta_protocol_time"]
    out["secondary_delta_final_decisions"] = event_decisions + out["primary_delta_final_decisions"]
    out["secondary_delta_final_conflicts"] = event_conflicts + out["primary_delta_final_conflicts"]

    for prefix in ["primary", "secondary"]:
        for metric in ["final_cpu", "protocol_time", "final_decisions", "final_conflicts"]:
            out[f"{prefix}_improvement_{metric}"] = -pd.to_numeric(out[f"{prefix}_delta_{metric}"], errors="coerce")

    out["primary_cpu_direction"] = out["primary_delta_final_cpu"].map(lambda value: direction(value, cpu_eps))
    out["primary_decisions_direction"] = out["primary_delta_final_decisions"].map(
        lambda value: direction(value, count_eps)
    )
    out["primary_conflicts_direction"] = out["primary_delta_final_conflicts"].map(
        lambda value: direction(value, count_eps)
    )
    out["secondary_cpu_direction"] = out["secondary_delta_final_cpu"].map(lambda value: direction(value, cpu_eps))
    out["secondary_decisions_direction"] = out["secondary_delta_final_decisions"].map(
        lambda value: direction(value, count_eps)
    )
    out["secondary_conflicts_direction"] = out["secondary_delta_final_conflicts"].map(
        lambda value: direction(value, count_eps)
    )
    out["event_adapter_graph_gate_open_int"] = out["event_adapter_graph_gate_open"].astype(bool).astype(int)
    out["named_initial_strict_candidate"] = out["base_instance_id"].astype(str).isin(NAMED_STRICT_CANDIDATES)
    return out


def summarize_base(group: pd.DataFrame, cpu_eps: float, count_eps: float) -> dict[str, Any]:
    first = group.iloc[0]
    row: dict[str, Any] = {
        "family": first["family"],
        "base_instance_id": first["base_instance_id"],
        "control_type": first.get("control_type", ""),
        "symmetry_strength": first.get("symmetry_strength", ""),
        "scale": first.get("scale", ""),
        "benchmark_role": first.get("benchmark_role", ""),
        "n_observations": int(len(group)),
        "variants": int(group["variant"].nunique()),
        "repeats": int(group["repeat_id"].nunique()),
        "named_initial_strict_candidate": bool(first.get("named_initial_strict_candidate", False)),
        "gate_open_rows": int(group["event_adapter_graph_gate_open"].astype(bool).sum()),
        "events_available_rows": int(group["events_available"].astype(bool).sum()),
        "event_state_l2_sum_mean": float(group["event_state_l2_sum"].mean()),
        "event_state_l2_sum_max": float(group["event_state_l2_sum"].max()),
        "event_state_nonzero_vars_mean": float(group["event_state_nonzero_vars"].mean()),
        "event_adapter_graph_gate_evidence_mean": float(group["event_adapter_graph_gate_evidence"].mean()),
        "warmup_decisions_mean": float(group["warmup_decisions"].mean()),
        "warmup_conflicts_mean": float(group["warmup_conflicts"].mean()),
        "adapter_inference_wall_time_mean": float(group["adapter_inference_wall_time"].mean()),
        "event_collection_overhead_protocol_time_mean": float(
            pd.to_numeric(group["event_collection_overhead_delta_protocol_time"], errors="coerce").mean()
        ),
    }
    for prefix, eps_map in [
        ("primary", {"final_cpu": cpu_eps, "protocol_time": cpu_eps, "final_decisions": count_eps, "final_conflicts": count_eps}),
        ("secondary", {"final_cpu": cpu_eps, "protocol_time": cpu_eps, "final_decisions": count_eps, "final_conflicts": count_eps}),
    ]:
        row[f"{prefix}_n_observations"] = int(len(group))
        for metric, eps in eps_map.items():
            values = pd.to_numeric(group[f"{prefix}_delta_{metric}"], errors="coerce")
            counts = signed_counts(values, eps)
            row[f"{prefix}_{metric}_mean_delta"] = float(values.mean())
            row[f"{prefix}_{metric}_median_delta"] = float(values.median())
            row[f"{prefix}_{metric}_min_delta"] = float(values.min())
            row[f"{prefix}_{metric}_max_delta"] = float(values.max())
            row[f"{prefix}_{metric}_down_count"] = counts["down"]
            row[f"{prefix}_{metric}_up_count"] = counts["up"]
            row[f"{prefix}_{metric}_flat_count"] = counts["flat"]
            row[f"{prefix}_{metric}_down_share"] = counts["down"] / float(len(group))
            row[f"{prefix}_{metric}_up_share"] = counts["up"] / float(len(group))
    return row


def build_base_summary(observations: pd.DataFrame, cpu_eps: float, count_eps: float) -> pd.DataFrame:
    rows = [
        summarize_base(group, cpu_eps=cpu_eps, count_eps=count_eps)
        for _, group in observations.groupby("base_instance_id", sort=True)
    ]
    out = pd.DataFrame(rows)
    out["majority_threshold"] = out["n_observations"].map(majority_threshold)
    out["primary_classification"] = out.apply(lambda row: classify_base(row, "primary"), axis=1)
    out["secondary_classification"] = out.apply(lambda row: classify_base(row, "secondary"), axis=1)
    out["primary_search_down_count_max"] = out[
        ["primary_final_decisions_down_count", "primary_final_conflicts_down_count"]
    ].max(axis=1)
    out["primary_search_up_count_max"] = out[
        ["primary_final_decisions_up_count", "primary_final_conflicts_up_count"]
    ].max(axis=1)
    out["secondary_search_down_count_max"] = out[
        ["secondary_final_decisions_down_count", "secondary_final_conflicts_down_count"]
    ].max(axis=1)
    out["secondary_search_up_count_max"] = out[
        ["secondary_final_decisions_up_count", "secondary_final_conflicts_up_count"]
    ].max(axis=1)
    out["primary_adapter_inference_erases_final_cpu_gain"] = (
        (out["primary_final_cpu_mean_delta"] < -cpu_eps) & (out["primary_protocol_time_mean_delta"] > cpu_eps)
    )
    out["secondary_protocol_overhead_swallows_final_cpu_gain"] = (
        (out["secondary_final_cpu_mean_delta"] < -cpu_eps) & (out["secondary_protocol_time_mean_delta"] > cpu_eps)
    )
    sort_key = {
        "strict_positive": 0,
        "timing_only_positive": 1,
        "no_effect": 2,
        "negative": 3,
    }
    out["_sort"] = out["primary_classification"].map(sort_key).fillna(9)
    out = out.sort_values(
        [
            "_sort",
            "primary_final_cpu_down_count",
            "primary_search_down_count_max",
            "primary_final_cpu_mean_delta",
        ],
        ascending=[True, False, False, True],
    ).drop(columns=["_sort"])
    return out


def rank_corr(x: pd.Series, y: pd.Series) -> tuple[float, float, int]:
    data = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(data) < 3 or data["x"].nunique() < 2 or data["y"].nunique() < 2:
        return (np.nan, np.nan, int(len(data)))
    pearson = float(data["x"].corr(data["y"], method="pearson"))
    spearman = float(data["x"].corr(data["y"], method="spearman"))
    return pearson, spearman, int(len(data))


def build_correlation(observations: pd.DataFrame, base_summary: pd.DataFrame) -> pd.DataFrame:
    evidence_columns = [
        "event_state_l2_sum",
        "event_state_nonzero_vars",
        "event_adapter_graph_gate_open_int",
        "event_adapter_graph_gate_evidence",
        "warmup_decisions",
        "warmup_conflicts",
    ]
    target_columns = [
        "primary_improvement_final_cpu",
        "primary_improvement_final_decisions",
        "primary_improvement_final_conflicts",
        "secondary_improvement_final_cpu",
        "secondary_improvement_final_decisions",
        "secondary_improvement_final_conflicts",
    ]
    rows: list[dict[str, Any]] = []
    for unit, frame in [
        ("variant_repeat_observation", observations),
        (
            "base_instance",
            observations.groupby("base_instance_id", as_index=False)[evidence_columns + target_columns].mean(),
        ),
    ]:
        for x_col in evidence_columns:
            for y_col in target_columns:
                pearson, spearman, n = rank_corr(frame[x_col], frame[y_col])
                rows.append(
                    {
                        "unit": unit,
                        "evidence": x_col,
                        "target": y_col,
                        "n": n,
                        "pearson": pearson,
                        "spearman": spearman,
                    }
                )
    return pd.DataFrame(rows)


def build_evidence_by_class(base_summary: pd.DataFrame) -> pd.DataFrame:
    numeric = [
        "event_state_l2_sum_mean",
        "event_state_nonzero_vars_mean",
        "event_adapter_graph_gate_evidence_mean",
        "warmup_decisions_mean",
        "warmup_conflicts_mean",
        "primary_final_cpu_mean_delta",
        "primary_final_decisions_mean_delta",
        "primary_final_conflicts_mean_delta",
        "secondary_protocol_time_mean_delta",
    ]
    rows: list[dict[str, Any]] = []
    for classification, group in base_summary.groupby("primary_classification", sort=True):
        row: dict[str, Any] = {
            "primary_classification": classification,
            "base_instances": int(len(group)),
            "named_initial_strict_candidates": int(group["named_initial_strict_candidate"].sum()),
        }
        for column in numeric:
            row[f"{column}_mean"] = float(group[column].mean())
            row[f"{column}_median"] = float(group[column].median())
        rows.append(row)
    return pd.DataFrame(rows)


def build_candidate_variant_summary(candidates: pd.DataFrame, cpu_eps: float, count_eps: float) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (base_id, variant), group in candidates.groupby(["base_instance_id", "variant"], sort=True):
        first = group.iloc[0]
        row: dict[str, Any] = {
            "family": first["family"],
            "base_instance_id": base_id,
            "variant": variant,
            "repeat_rows": int(len(group)),
            "event_state_l2_sum": float(group["event_state_l2_sum"].mean()),
            "event_state_nonzero_vars": float(group["event_state_nonzero_vars"].mean()),
            "event_adapter_graph_gate_open_rows": int(group["event_adapter_graph_gate_open"].astype(bool).sum()),
            "event_adapter_graph_gate_evidence": float(group["event_adapter_graph_gate_evidence"].mean()),
            "warmup_decisions": float(group["warmup_decisions"].mean()),
            "warmup_conflicts": float(group["warmup_conflicts"].mean()),
            "primary_final_cpu_mean_delta": float(group["primary_delta_final_cpu"].mean()),
            "primary_final_decisions_mean_delta": float(group["primary_delta_final_decisions"].mean()),
            "primary_final_conflicts_mean_delta": float(group["primary_delta_final_conflicts"].mean()),
            "primary_protocol_time_mean_delta": float(group["primary_delta_protocol_time"].mean()),
            "secondary_protocol_time_mean_delta": float(group["secondary_delta_protocol_time"].mean()),
        }
        for metric, column, eps in [
            ("final_cpu", "primary_delta_final_cpu", cpu_eps),
            ("final_decisions", "primary_delta_final_decisions", count_eps),
            ("final_conflicts", "primary_delta_final_conflicts", count_eps),
            ("protocol_time", "primary_delta_protocol_time", cpu_eps),
        ]:
            counts = signed_counts(group[column], eps)
            row[f"primary_{metric}_down_count"] = counts["down"]
            row[f"primary_{metric}_up_count"] = counts["up"]
            row[f"primary_{metric}_flat_count"] = counts["flat"]
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_orbits(path: Path, observations: pd.DataFrame) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    orbits = pd.read_csv(path)
    numeric_aggs: dict[str, tuple[str, str]] = {}
    for column in [
        "event_feature_l2_range",
        "event_identity_gain",
        "adapter_identity_gain",
        "adapter_mu_identity_gain",
        "adapted_mu_range",
        "static_mu_range",
        "event_nonzero_variables",
    ]:
        if column in orbits.columns:
            numeric_aggs[f"orbit_{column}_mean"] = (column, "mean")
            numeric_aggs[f"orbit_{column}_max"] = (column, "max")
    orbit_agg = (
        orbits.groupby(["base_instance_id", "variant"], as_index=False)
        .agg(
            orbit_rows=("orbit", "count"),
            orbit_valid_rows=("orbit_valid", lambda values: int(pd.Series(values).astype(bool).sum())),
            event_row_valid_rows=("event_row_valid", lambda values: int(pd.Series(values).astype(bool).sum())),
            event_identity_positive_rows=(
                "event_identity_positive",
                lambda values: int(pd.Series(values).astype(bool).sum()),
            ),
            **numeric_aggs,
        )
    )
    runtime_variant = (
        observations.groupby(["family", "base_instance_id", "variant"], as_index=False)
        .agg(
            repeat_rows=("repeat_id", "nunique"),
            primary_final_cpu_mean_delta=("primary_delta_final_cpu", "mean"),
            primary_final_decisions_mean_delta=("primary_delta_final_decisions", "mean"),
            primary_final_conflicts_mean_delta=("primary_delta_final_conflicts", "mean"),
            event_state_l2_sum_mean=("event_state_l2_sum", "mean"),
            event_adapter_graph_gate_evidence_mean=("event_adapter_graph_gate_evidence", "mean"),
            warmup_decisions_mean=("warmup_decisions", "mean"),
            warmup_conflicts_mean=("warmup_conflicts", "mean"),
        )
    )
    joined = runtime_variant.merge(orbit_agg, on=["base_instance_id", "variant"], how="left", indicator=True)
    joined["orbit_overlap_available"] = joined["_merge"].eq("both")
    return joined.drop(columns=["_merge"])


def markdown_table(frame: pd.DataFrame, max_rows: int = 30, float_digits: int = 4) -> list[str]:
    if frame.empty:
        return ["_None._"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in view.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, (float, np.floating)):
                if np.isnan(value):
                    values.append("nan")
                else:
                    values.append(f"{value:.{float_digits}g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    if len(frame) > max_rows:
        lines.append(f"| ... truncated ... | {len(frame) - max_rows} more rows |" + " |" * max(0, len(columns) - 2))
    return lines


def compact_base_table(base_summary: pd.DataFrame, classification: str | None = None) -> pd.DataFrame:
    frame = base_summary
    if classification is not None:
        frame = frame[frame["primary_classification"].eq(classification)].copy()
    columns = [
        "family",
        "base_instance_id",
        "control_type",
        "scale",
        "primary_classification",
        "primary_final_cpu_down_count",
        "primary_final_cpu_up_count",
        "primary_final_cpu_mean_delta",
        "primary_final_decisions_down_count",
        "primary_final_decisions_up_count",
        "primary_final_decisions_mean_delta",
        "primary_final_conflicts_down_count",
        "primary_final_conflicts_up_count",
        "primary_final_conflicts_mean_delta",
        "event_state_l2_sum_mean",
        "event_adapter_graph_gate_evidence_mean",
        "warmup_decisions_mean",
        "warmup_conflicts_mean",
        "secondary_protocol_overhead_swallows_final_cpu_gain",
    ]
    return frame[[column for column in columns if column in frame.columns]].copy()


def candidate_notes(base_summary: pd.DataFrame) -> list[str]:
    notes: list[str] = []
    for base_id in sorted(NAMED_STRICT_CANDIDATES):
        row = base_summary[base_summary["base_instance_id"].eq(base_id)]
        if row.empty:
            notes.append(f"- `{base_id}`: missing from v2 attribution.")
            continue
        item = row.iloc[0]
        notes.append(
            "- `{base}`: `{cls}`; CPU down `{cpu_down}/{n}`, decisions down `{dec_down}/{n}`, "
            "conflicts down `{conf_down}/{n}`; mean final CPU delta `{cpu:.4g}`, decisions delta `{dec:.4g}`, "
            "conflicts delta `{conf:.4g}`.".format(
                base=base_id,
                cls=item["primary_classification"],
                cpu_down=int(item["primary_final_cpu_down_count"]),
                dec_down=int(item["primary_final_decisions_down_count"]),
                conf_down=int(item["primary_final_conflicts_down_count"]),
                n=int(item["n_observations"]),
                cpu=float(item["primary_final_cpu_mean_delta"]),
                dec=float(item["primary_final_decisions_mean_delta"]),
                conf=float(item["primary_final_conflicts_mean_delta"]),
            )
        )
    return notes


def classification_counts(base_summary: pd.DataFrame) -> pd.DataFrame:
    order = ["strict_positive", "timing_only_positive", "no_effect", "negative"]
    counts = (
        base_summary.groupby("primary_classification", as_index=False)
        .agg(base_instances=("base_instance_id", "count"))
        .set_index("primary_classification")
        .reindex(order, fill_value=0)
        .reset_index()
    )
    return counts


def write_doc(
    path: Path,
    *,
    attribution_path: Path,
    per_instance_path: Path,
    orbit_path: Path,
    base_summary: pd.DataFrame,
    observations: pd.DataFrame,
    candidates: pd.DataFrame,
    correlation: pd.DataFrame,
    evidence_by_class: pd.DataFrame,
    orbit_overlap: pd.DataFrame,
    cpu_eps: float,
    count_eps: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    class_counts = classification_counts(base_summary)
    family_counts = (
        base_summary.groupby(["family", "primary_classification"], as_index=False)
        .agg(base_instances=("base_instance_id", "count"))
        .sort_values(["family", "primary_classification"])
    )
    strict_table = compact_base_table(base_summary, "strict_positive")
    timing_table = compact_base_table(base_summary, "timing_only_positive")
    no_effect_table = compact_base_table(base_summary, "no_effect")
    negative_table = compact_base_table(base_summary, "negative")

    corr_view = correlation.copy()
    corr_view["abs_spearman"] = corr_view["spearman"].abs()
    corr_view = corr_view.sort_values(["unit", "abs_spearman"], ascending=[True, False])[
        ["unit", "evidence", "target", "n", "pearson", "spearman"]
    ]

    candidate_view = candidates[
        [
            "family",
            "base_instance_id",
            "variant",
            "repeat_id",
            "primary_delta_final_cpu",
            "primary_delta_final_decisions",
            "primary_delta_final_conflicts",
            "primary_delta_protocol_time",
            "event_state_l2_sum",
            "event_state_nonzero_vars",
            "event_adapter_graph_gate_open",
            "event_adapter_graph_gate_evidence",
            "warmup_decisions",
            "warmup_conflicts",
        ]
    ].copy()
    candidate_view = candidate_view.sort_values(["base_instance_id", "variant", "repeat_id"])
    candidate_variant_summary = build_candidate_variant_summary(
        candidates, cpu_eps=cpu_eps, count_eps=count_eps
    )
    candidate_variant_view = candidate_variant_summary[
        [
            "family",
            "base_instance_id",
            "variant",
            "repeat_rows",
            "primary_final_cpu_down_count",
            "primary_final_cpu_up_count",
            "primary_final_cpu_mean_delta",
            "primary_final_decisions_down_count",
            "primary_final_decisions_up_count",
            "primary_final_decisions_mean_delta",
            "primary_final_conflicts_down_count",
            "primary_final_conflicts_up_count",
            "primary_final_conflicts_mean_delta",
            "event_state_l2_sum",
            "event_adapter_graph_gate_open_rows",
            "event_adapter_graph_gate_evidence",
            "warmup_decisions",
            "warmup_conflicts",
            "secondary_protocol_time_mean_delta",
        ]
    ].copy() if not candidate_variant_summary.empty else pd.DataFrame()

    overlap_bases = (
        orbit_overlap[orbit_overlap["orbit_overlap_available"]]["base_instance_id"].nunique()
        if not orbit_overlap.empty
        else 0
    )
    overlap_variants = int(orbit_overlap["orbit_overlap_available"].sum()) if not orbit_overlap.empty else 0
    missing_orbit_bases = sorted(
        set(base_summary["base_instance_id"].astype(str))
        - set(orbit_overlap[orbit_overlap["orbit_overlap_available"]]["base_instance_id"].astype(str))
        if not orbit_overlap.empty
        else set(base_summary["base_instance_id"].astype(str))
    )
    strict_overlap = (
        orbit_overlap[
            orbit_overlap["base_instance_id"].isin(strict_table["base_instance_id"])
            & orbit_overlap["orbit_overlap_available"]
        ].copy()
        if not orbit_overlap.empty
        else pd.DataFrame()
    )
    orbit_columns = [
        "family",
        "base_instance_id",
        "variant",
        "repeat_rows",
        "primary_final_cpu_mean_delta",
        "primary_final_decisions_mean_delta",
        "primary_final_conflicts_mean_delta",
        "orbit_rows",
        "orbit_valid_rows",
        "event_row_valid_rows",
        "event_identity_positive_rows",
        "orbit_event_identity_gain_max",
        "orbit_adapter_identity_gain_max",
        "orbit_adapter_mu_identity_gain_max",
    ]
    strict_overlap = strict_overlap[[column for column in orbit_columns if column in strict_overlap.columns]]

    lines = [
        "# SAT Symmetry Runtime-Positive Subset v2",
        "",
        "This is an offline diagnostic report. It asks whether the event adapter changed",
        "the final solver search on the v2 runtime protocol. It is not a solver speedup",
        "claim, and it does not train a model, run a gate/selector, or rerun any solver.",
        "",
        "## Inputs",
        "",
        f"- attribution CSV: `{attribution_path}`",
        f"- per-instance CSV: `{per_instance_path}`",
        f"- primary comparison: `event_adapter_final - cached_trace_no_adapter_final`",
        f"- secondary comparison: `event_adapter_final - static_weighted_glucose`",
        f"- unit of analysis: `base_instance_id`; `variant x repeat_id` are observations inside each base",
        f"- CPU direction epsilon: `{cpu_eps}` seconds",
        f"- decision/conflict epsilon: `{count_eps}`",
        f"- W05 orbit overlap source: `{orbit_path}`",
        "",
        "## Classification Rules",
        "",
        "Deltas are `adapter - baseline`, so negative deltas mean the adapter used less",
        "final CPU, fewer decisions, or fewer conflicts than the baseline.",
        "",
        "- `strict_positive`: final CPU is down for a majority of observations, and decisions or conflicts are also down for a majority, with no majority search worsening.",
        "- `timing_only_positive`: final CPU is down for a majority, but decisions/conflicts have no stable direction.",
        "- `no_effect`: neither timing nor search has a stable majority direction.",
        "- `negative`: final CPU, decisions, or conflicts increase for a majority.",
        "",
        "## Runtime Viability Mining",
        "",
        *markdown_table(class_counts),
        "",
        "### By Family",
        "",
        *markdown_table(family_counts, max_rows=80),
        "",
        "### Strict Positives",
        "",
        *markdown_table(strict_table, max_rows=80),
        "",
        "The table above is the mechanical strict-positive bucket. The priority deep dive",
        "below stays focused on the three pre-identified candidates; other strict-like rows",
        "are weaker evidence because they are controls, very small timing effects, or",
        "variant-mixed search changes.",
        "",
        "Initial strict candidates requested for first inspection:",
        "",
        *candidate_notes(base_summary),
        "",
        "### Timing-Only Positives",
        "",
        *markdown_table(timing_table, max_rows=80),
        "",
        "### No-Effect Bases",
        "",
        *markdown_table(no_effect_table, max_rows=80),
        "",
        "### Negative / Search-Worsening Bases",
        "",
        *markdown_table(negative_table, max_rows=80),
        "",
        "## Evidence Correlation",
        "",
        "Layer 1 uses only repeat-level fields already present in the v2 attribution table.",
        "Positive target values mean improvement because they are `-delta`.",
        "",
        "### Evidence By Classification",
        "",
        *markdown_table(evidence_by_class, max_rows=20),
        "",
        "### Top Correlations",
        "",
        *markdown_table(corr_view, max_rows=36),
        "",
        "## Candidate Deep Dive",
        "",
        "The primary comparison shares the same warmup/event collection between cached trace",
        "and adapter final solves. Therefore warmup can explain secondary protocol overhead",
        "relative to `static_weighted_glucose`, but not the primary final-search deltas below.",
        "",
        "### Variant Summary",
        "",
        *markdown_table(candidate_variant_view, max_rows=80),
        "",
        "### Variant x Repeat Rows",
        "",
        *markdown_table(candidate_view, max_rows=120),
        "",
        "Interpretation for the named strict candidates:",
        "",
        "- `dominating_set_hex_3x6_s4`: adapter changed search on the final solve; conflicts drop in every variant/repeat, while final CPU mostly drops. Event gate is open on all rows. Protocol time still loses relative to static because event collection is much larger than the local final-solve gain.",
        "- `subset_cardinality_bw12`: adapter changed search on two of three variants; the `perm_seed1730` variant has worse decisions/conflicts, so the evidence is strict by majority but not variant-uniform. Event evidence is strong, and protocol overhead still dominates.",
        "- `random_3sat_control_v20_c85_seed1901`: decisions drop in every row, but conflicts are flat and CPU changes are tiny. Because this is a non-symmetric control, it is evidence that the adapter can perturb search, not evidence of symmetry-specific benefit.",
        "",
        "## Orbit Overlap",
        "",
        "Layer 2 joins existing W05 orbit evidence by `base_instance_id + variant` only.",
        "The orbit table has no `repeat_id`, so this is partial overlap evidence rather",
        "than a full v2 runtime conclusion.",
        "",
        f"- runtime bases: `{base_summary['base_instance_id'].nunique()}`",
        f"- orbit-overlap bases: `{overlap_bases}`",
        f"- runtime variant rows: `{observations[['base_instance_id', 'variant']].drop_duplicates().shape[0]}`",
        f"- orbit-overlap variant rows: `{overlap_variants}`",
        f"- missing orbit bases: `{', '.join(missing_orbit_bases)}`",
        "",
        "### Strict Candidate Orbit Overlap",
        "",
        *markdown_table(strict_overlap, max_rows=80),
        "",
        "## Diagnostic Conclusion",
        "",
        "The v2 data contains a small strict-positive subset where the adapter changes final",
        "search, including the named strict candidates. The signal is not a protocol-time",
        "win: event collection overhead still dominates when comparing to the static weighted",
        "path. The random 3SAT control strict case also means this evidence should be treated",
        "as search-change evidence, not symmetry-specific solver-speed evidence.",
        "",
        "The next representation audit, if pursued, should be targeted before any gate or",
        "selector work: prioritize `dominating_set_hex_3x6_s4` and `subset_cardinality_bw12`,",
        "then nearby same-family/scale bases. The v2-missing orbit bases remain partial-coverage",
        "gaps rather than runtime conclusions.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine v2 runtime-positive adapter subsets without rerunning solvers.")
    parser.add_argument("--attribution-csv", type=Path, default=DEFAULT_ATTRIBUTION)
    parser.add_argument("--per-instance-csv", type=Path, default=DEFAULT_PER_INSTANCE)
    parser.add_argument("--orbit-csv", type=Path, default=DEFAULT_ORBITS)
    parser.add_argument("--base-summary-csv", type=Path, default=DEFAULT_BASE_SUMMARY)
    parser.add_argument("--observations-csv", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--candidate-csv", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--candidate-variant-csv", type=Path, default=DEFAULT_CANDIDATE_VARIANTS)
    parser.add_argument("--correlation-csv", type=Path, default=DEFAULT_CORRELATION)
    parser.add_argument("--evidence-by-class-csv", type=Path, default=DEFAULT_EVIDENCE_BY_CLASS)
    parser.add_argument("--orbit-overlap-csv", type=Path, default=DEFAULT_ORBIT_OVERLAP)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--cpu-eps", type=float, default=1e-6)
    parser.add_argument("--count-eps", type=float, default=0.0)
    args = parser.parse_args()

    attribution_path = resolve(args.attribution_csv)
    per_instance_path = resolve(args.per_instance_csv)
    orbit_path = resolve(args.orbit_csv)
    attribution = pd.read_csv(attribution_path)
    per_instance = pd.read_csv(per_instance_path)

    required_methods = {
        "plain_unguided_glucose",
        "neutral_weighted_glucose",
        "static_weighted_glucose",
        "cached_trace_no_adapter_final",
        "event_adapter_final",
    }
    actual_methods = set(per_instance["method"].astype(str).unique())
    missing_methods = sorted(required_methods - actual_methods)
    if missing_methods:
        raise ValueError(f"per-instance CSV is missing methods: {missing_methods}")
    if per_instance["solver_path_role"].astype(str).nunique() != 1:
        raise ValueError("per-instance CSV has mixed solver_path_role values")
    if bool(per_instance["weighted_no_pre"].astype(bool).any()):
        raise ValueError("v2 runtime-positive mining expects weighted_no_pre=False rows only")

    observations = add_runtime_deltas(attribution, cpu_eps=float(args.cpu_eps), count_eps=float(args.count_eps))
    base_summary = build_base_summary(observations, cpu_eps=float(args.cpu_eps), count_eps=float(args.count_eps))
    observations = observations.merge(
        base_summary[["base_instance_id", "primary_classification", "secondary_classification"]],
        on="base_instance_id",
        how="left",
    )
    candidate_ids = set(NAMED_STRICT_CANDIDATES)
    candidates = observations[observations["base_instance_id"].isin(candidate_ids)].copy()
    candidates = candidates.sort_values(["base_instance_id", "variant", "repeat_id"])
    candidate_variant_summary = build_candidate_variant_summary(
        candidates, cpu_eps=float(args.cpu_eps), count_eps=float(args.count_eps)
    )
    correlation = build_correlation(observations, base_summary)
    evidence_by_class = build_evidence_by_class(base_summary)
    orbit_overlap = aggregate_orbits(orbit_path, observations)

    for path, frame in [
        (resolve(args.base_summary_csv), base_summary),
        (resolve(args.observations_csv), observations),
        (resolve(args.candidate_csv), candidates),
        (resolve(args.candidate_variant_csv), candidate_variant_summary),
        (resolve(args.correlation_csv), correlation),
        (resolve(args.evidence_by_class_csv), evidence_by_class),
        (resolve(args.orbit_overlap_csv), orbit_overlap),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
        print(f"wrote {path}")

    write_doc(
        resolve(args.doc),
        attribution_path=attribution_path,
        per_instance_path=per_instance_path,
        orbit_path=orbit_path,
        base_summary=base_summary,
        observations=observations,
        candidates=candidates,
        correlation=correlation,
        evidence_by_class=evidence_by_class,
        orbit_overlap=orbit_overlap,
        cpu_eps=float(args.cpu_eps),
        count_eps=float(args.count_eps),
    )
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
