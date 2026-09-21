from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parent


NUMERIC_METRICS = [
    "static_mu_mean",
    "static_mu_range",
    "event_feature_l2_range",
    "event_feature_mean_range",
    "event_nonzero_variables",
    "adapted_mu_mean",
    "adapted_mu_range",
    "adapter_identity_gain",
]


def truthy_series(frame: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=bool)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(default).astype(bool)
    normalized = values.fillna(str(default)).astype(str).str.strip().str.lower()
    return normalized.isin({"1", "true", "yes", "y"})


def numeric_series(group: pd.DataFrame, column: str) -> pd.Series:
    if column not in group.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(group[column], errors="coerce").dropna()


def variant_std(group: pd.DataFrame, column: str) -> float:
    values = numeric_series(group, column)
    if values.empty:
        return float("nan")
    return float(values.std(ddof=0))


def variant_range(group: pd.DataFrame, column: str) -> float:
    values = numeric_series(group, column)
    if values.empty:
        return float("nan")
    return float(values.max() - values.min())


def variant_mean(group: pd.DataFrame, column: str) -> float:
    values = numeric_series(group, column)
    if values.empty:
        return float("nan")
    return float(values.mean())


def variant_max(group: pd.DataFrame, column: str) -> float:
    values = numeric_series(group, column)
    if values.empty:
        return float("nan")
    return float(values.max())


def load_permutation_metadata(manifest_path: Path | None) -> dict[str, bool]:
    if manifest_path is None or not manifest_path.exists():
        return {}
    manifest = pd.read_csv(manifest_path)
    metadata_available: dict[str, bool] = {}
    for _, row in manifest.iterrows():
        instance_id = str(row.get("instance_id", ""))
        variant = str(row.get("variant", ""))
        metadata_path = Path(str(row.get("metadata_path", "")))
        if not instance_id or not metadata_path.exists():
            metadata_available[instance_id] = False
            continue
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            metadata_available[instance_id] = False
            continue
        if variant == "base":
            metadata_available[instance_id] = True
        else:
            permutation = payload.get("permutation")
            metadata_available[instance_id] = isinstance(permutation, list) and len(permutation) > 0
    return metadata_available


def filter_orbit_rows(frame: pd.DataFrame, row_filter: str) -> pd.DataFrame:
    if row_filter == "all":
        return frame.copy()
    mask = pd.Series(True, index=frame.index)
    if row_filter in {"orbit-valid", "event-valid", "event-positive"}:
        mask &= truthy_series(frame, "orbit_valid", default=True)
    if row_filter in {"event-valid", "event-positive"}:
        mask &= truthy_series(frame, "event_row_valid", default=False)
    if row_filter == "event-positive":
        mask &= truthy_series(frame, "event_identity_positive", default=False)
    return frame[mask].copy()


def build_consistency_frame(
    orbit_frame: pd.DataFrame,
    metadata_available: dict[str, bool] | None = None,
    row_filter: str = "event-valid",
) -> pd.DataFrame:
    metadata_available = metadata_available or {}
    frame = filter_orbit_rows(orbit_frame, row_filter=row_filter)
    rows: list[dict[str, object]] = []
    required = {"family", "base_instance_id", "orbit", "variant", "instance_id"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"orbit CSV missing required columns: {sorted(missing)}")

    for (family, base_instance_id, orbit), group in frame.groupby(
        ["family", "base_instance_id", "orbit"],
        sort=True,
    ):
        variants = sorted(group["variant"].astype(str).unique())
        if len(variants) <= 1:
            continue
        instances = sorted(group["instance_id"].astype(str).unique())
        row: dict[str, object] = {
            "family": family,
            "base_instance_id": base_instance_id,
            "orbit": orbit,
            "row_filter": row_filter,
            "variants": len(variants),
            "variant_list": ",".join(variants),
            "instances": len(instances),
            "permutation_metadata_available": all(metadata_available.get(instance, False) for instance in instances),
            "event_positive_rows": int(truthy_series(group, "event_identity_positive", default=False).sum()),
            "zero_identity_rows": int(truthy_series(group, "event_identity_zero", default=False).sum()),
        }
        if "orbit_size" in group.columns:
            row["mean_orbit_size"] = variant_mean(group, "orbit_size")
            row["max_orbit_size"] = variant_max(group, "orbit_size")
        for metric in NUMERIC_METRICS:
            if metric not in group.columns:
                continue
            row[f"{metric}_variant_mean"] = variant_mean(group, metric)
            row[f"{metric}_variant_std"] = variant_std(group, metric)
            row[f"{metric}_variant_range"] = variant_range(group, metric)
            row[f"{metric}_variant_max"] = variant_max(group, metric)
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_by_family(consistency: pd.DataFrame) -> pd.DataFrame:
    if consistency.empty:
        return pd.DataFrame()
    aggregations: dict[str, tuple[str, str]] = {
        "groups": ("orbit", "count"),
        "base_instances": ("base_instance_id", "nunique"),
        "mean_variants": ("variants", "mean"),
    }
    for column in [
        "static_mu_mean_variant_std",
        "static_mu_range_variant_max",
        "event_feature_l2_range_variant_std",
        "event_feature_l2_range_variant_range",
        "adapted_mu_mean_variant_std",
        "adapted_mu_range_variant_std",
        "adapter_identity_gain_variant_std",
        "adapter_identity_gain_variant_range",
    ]:
        if column in consistency.columns:
            aggregations[f"mean_{column}"] = (column, "mean")
            aggregations[f"max_{column}"] = (column, "max")
    return consistency.groupby("family", sort=True).agg(**aggregations).reset_index()


def markdown_table(frame: pd.DataFrame, columns: Iterable[str] | None = None, max_rows: int | None = None) -> list[str]:
    if frame.empty:
        return ["_None._"]
    view = frame.copy()
    if columns is not None:
        view = view[[column for column in columns if column in view.columns]]
    if max_rows is not None:
        view = view.head(int(max_rows))
    cols = list(view.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in view.iterrows():
        values = []
        for column in cols:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_doc(
    path: Path,
    orbit_frame: pd.DataFrame,
    consistency: pd.DataFrame,
    row_filter: str,
    orbit_csv: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    filtered = filter_orbit_rows(orbit_frame, row_filter=row_filter)
    family_summary = summarize_by_family(consistency)
    input_summary = (
        filtered.groupby("family", sort=True)
        .agg(
            orbit_rows=("orbit", "count"),
            instances=("instance_id", "nunique"),
            base_instances=("base_instance_id", "nunique"),
            variants=("variant", "nunique"),
            event_positive_rows=("event_identity_positive", lambda values: int(truthy_series(pd.DataFrame({"v": values}), "v").sum())),
        )
        .reset_index()
        if not filtered.empty
        else pd.DataFrame()
    )
    worst = (
        consistency.sort_values("adapter_identity_gain_variant_std", ascending=False)
        if "adapter_identity_gain_variant_std" in consistency.columns
        else consistency
    )
    lines = [
        "# Adapter Permutation Consistency Audit",
        "",
        f"- source orbit CSV: `{orbit_csv}`",
        f"- row filter: `{row_filter}`",
        "",
        "This is an orbit-aggregated renamed-variant audit. It groups rows by",
        "`family`, `base_instance_id`, and refined `orbit`, then compares the",
        "base and permuted variants. The current adapter event CSV does not",
        "contain per-variable vectors, so this does not claim a variable-level",
        "equivariance proof.",
        "",
        "## Input Rows",
        "",
        *markdown_table(input_summary),
        "",
        "## Family Consistency",
        "",
        *markdown_table(family_summary),
        "",
        "## Largest Adapter Variant Std",
        "",
        *markdown_table(
            worst,
            columns=[
                "family",
                "base_instance_id",
                "orbit",
                "variants",
                "event_feature_l2_range_variant_std",
                "adapted_mu_mean_variant_std",
                "adapted_mu_range_variant_std",
                "adapter_identity_gain_variant_std",
                "permutation_metadata_available",
            ],
            max_rows=20,
        ),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit adapter consistency across renamed symmetry variants.")
    parser.add_argument("--orbits-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_event_orbits.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "runs/analysis/symmetry_stress_manifest.csv")
    parser.add_argument("--output-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_permutation_consistency.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_adapter_permutation_consistency_audit.md")
    parser.add_argument(
        "--row-filter",
        choices=["all", "orbit-valid", "event-valid", "event-positive"],
        default="event-valid",
    )
    args = parser.parse_args()

    orbit_frame = pd.read_csv(args.orbits_csv)
    metadata_available = load_permutation_metadata(args.manifest)
    consistency = build_consistency_frame(
        orbit_frame,
        metadata_available=metadata_available,
        row_filter=str(args.row_filter),
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    consistency.to_csv(args.output_csv, index=False)
    write_doc(
        args.doc,
        orbit_frame=orbit_frame,
        consistency=consistency,
        row_filter=str(args.row_filter),
        orbit_csv=args.orbits_csv,
    )
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
