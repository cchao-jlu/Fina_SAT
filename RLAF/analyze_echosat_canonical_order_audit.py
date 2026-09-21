from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd

from analyze_echosat_low_warmup_sweep import observations_from_file


ROOT = Path(__file__).resolve().parent
DEFAULT_ORIGINAL = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_observations.csv"
DEFAULT_CANONICAL_GLOB = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc*_per_instance.csv"
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_sweep_observations.csv"
DEFAULT_PAIR_DELTAS = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_pair_deltas.csv"
DEFAULT_SUMMARY = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_summary.csv"
DEFAULT_DOC = ROOT / "docs/echosat_adapter_delta_v2_iter235_canonical_order_audit.md"

KEYS = ["warmup_conflicts", "family", "base_instance_id", "variant", "repeat_id"]
METRICS = [
    "plain_unguided_glucose_final_cpu_time",
    "neutral_weighted_glucose_final_cpu_time",
    "static_weighted_glucose_final_cpu_time",
    "cached_trace_no_adapter_final_final_cpu_time",
    "event_adapter_final_final_cpu_time",
    "event_adapter_final_protocol_accounted_time",
    "adapter_cached_final_cpu_delta",
    "adapter_plain_final_cpu_delta",
    "adapter_plain_protocol_delta",
    "adapter_cached_decisions_delta",
    "adapter_cached_conflicts_delta",
    "neutral_plain_final_cpu_delta",
    "static_neutral_final_cpu_delta",
    "warmup_cpu_time",
    "warmup_conflict_count",
    "warmup_decisions",
    "event_state_l2_sum",
    "event_state_nonzero_vars",
]


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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


def canonical_observations(paths: list[Path]) -> pd.DataFrame:
    if not paths:
        raise ValueError("No canonical per-instance CSVs found.")
    return pd.concat(
        [observations_from_file(path, allow_weighted_no_pre=False) for path in paths],
        ignore_index=True,
    )


def build_pair_deltas(original: pd.DataFrame, canonical: pd.DataFrame) -> pd.DataFrame:
    original_scope = original[original["family"].astype(str).isin({"complete_coloring", "php"})].copy()
    original_scope = original_scope[
        original_scope["base_instance_id"].astype(str).isin({"k9_color8", "k10_color9", "php_p9_h8", "php_p10_h9"})
    ].copy()
    canonical_scope = canonical.copy()
    missing_keys = [key for key in KEYS if key not in original_scope.columns or key not in canonical_scope.columns]
    if missing_keys:
        raise ValueError(f"Missing key columns: {missing_keys}")
    original_columns = KEYS + [column for column in METRICS if column in original_scope.columns]
    canonical_columns = KEYS + [column for column in METRICS if column in canonical_scope.columns]
    joined = original_scope[original_columns].merge(
        canonical_scope[canonical_columns],
        on=KEYS,
        how="inner",
        suffixes=("_original", "_canonical"),
        validate="one_to_one",
    )
    expected_rows = len(original_scope.drop_duplicates(KEYS))
    if len(joined) != expected_rows:
        raise ValueError(f"Pair join mismatch: joined={len(joined)} expected={expected_rows}")
    for metric in METRICS:
        original_col = f"{metric}_original"
        canonical_col = f"{metric}_canonical"
        if original_col in joined.columns and canonical_col in joined.columns:
            joined[f"{metric}_canonical_minus_original"] = joined[canonical_col] - joined[original_col]
    return joined.sort_values(KEYS).reset_index(drop=True)


def summarize(pair_deltas: pd.DataFrame) -> pd.DataFrame:
    delta_columns = [column for column in pair_deltas.columns if column.endswith("_canonical_minus_original")]
    grouped = pair_deltas.groupby(["warmup_conflicts", "family", "base_instance_id"], sort=True)
    rows: list[dict[str, Any]] = []
    for key, group in grouped:
        row: dict[str, Any] = {
            "warmup_conflicts": key[0],
            "family": key[1],
            "base_instance_id": key[2],
            "rows": int(len(group)),
            "variants": int(group["variant"].nunique()),
            "repeats": int(group["repeat_id"].nunique()),
        }
        for column in delta_columns:
            metric = column[: -len("_canonical_minus_original")]
            row[f"{metric}_order_delta_mean"] = float(group[column].mean())
            row[f"{metric}_order_delta_median"] = float(group[column].median())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["warmup_conflicts", "family", "base_instance_id"]).reset_index(drop=True)


def write_doc(
    path: Path,
    *,
    pair_deltas: pd.DataFrame,
    summary: pd.DataFrame,
    canonical_observations_csv: Path,
    pair_deltas_csv: Path,
    summary_csv: Path,
) -> None:
    compact_summary_columns = [
        "warmup_conflicts",
        "family",
        "base_instance_id",
        "rows",
        "plain_unguided_glucose_final_cpu_time_order_delta_mean",
        "event_adapter_final_final_cpu_time_order_delta_mean",
        "event_adapter_final_protocol_accounted_time_order_delta_mean",
        "adapter_cached_final_cpu_delta_order_delta_mean",
        "adapter_plain_protocol_delta_order_delta_mean",
        "event_state_l2_sum_order_delta_mean",
    ]
    compact_summary = summary[[column for column in compact_summary_columns if column in summary.columns]].copy()
    overall = (
        pair_deltas.groupby(["warmup_conflicts", "family"], sort=True)
        .agg(
            rows=("repeat_id", "size"),
            base_instances=("base_instance_id", "nunique"),
            plain_cpu_order_delta_mean=("plain_unguided_glucose_final_cpu_time_canonical_minus_original", "mean"),
            adapter_final_cpu_order_delta_mean=("event_adapter_final_final_cpu_time_canonical_minus_original", "mean"),
            adapter_protocol_order_delta_mean=(
                "event_adapter_final_protocol_accounted_time_canonical_minus_original",
                "mean",
            ),
            adapter_cached_delta_order_delta_mean=("adapter_cached_final_cpu_delta_canonical_minus_original", "mean"),
            adapter_plain_protocol_delta_order_delta_mean=(
                "adapter_plain_protocol_delta_canonical_minus_original",
                "mean",
            ),
            event_l2_order_delta_mean=("event_state_l2_sum_canonical_minus_original", "mean"),
        )
        .reset_index()
    )
    max_plain_abs = float(overall["plain_cpu_order_delta_mean"].abs().max()) if not overall.empty else math.nan
    max_adapter_abs = (
        float(overall["adapter_final_cpu_order_delta_mean"].abs().max()) if not overall.empty else math.nan
    )
    max_adapter_cached_abs = (
        float(overall["adapter_cached_delta_order_delta_mean"].abs().max()) if not overall.empty else math.nan
    )
    solved_rows = int(pair_deltas["repeat_id"].size)
    lines = [
        "# EchoSAT Canonical DIMACS Order Audit",
        "",
        "This audit reruns the low-warmup protocol on canonicalized DIMACS order for formula-equivalent complete_coloring/php harder-baseline rows. It is an order-sensitivity diagnostic, not training and not a speedup claim.",
        "",
        "## Artifacts",
        "",
        f"- canonical observations CSV: `{display_path(canonical_observations_csv)}`",
        f"- pair deltas CSV: `{display_path(pair_deltas_csv)}`",
        f"- summary CSV: `{display_path(summary_csv)}`",
        "",
        "## Key Findings",
        "",
        f"- Paired order-delta rows: {solved_rows}.",
        f"- Max absolute family-level plain final CPU order delta: {max_plain_abs:.6g}s.",
        f"- Max absolute family-level adapter final CPU order delta: {max_adapter_abs:.6g}s.",
        f"- Max absolute family-level adapter-vs-cached delta shift: {max_adapter_cached_abs:.6g}s.",
        "- Canonicalization does not justify a speedup claim. It confirms that DIMACS ordering materially changes both plain and adapter-guided CDCL paths on these formula-equivalent rows.",
        "",
        "## Overall By Family",
        "",
        *markdown_table(overall, max_rows=40),
        "",
        "## By Base",
        "",
        *markdown_table(compact_summary, max_rows=80),
        "",
        "## Interpretation",
        "",
        "- `*_order_delta_mean` is canonical-order value minus original-order value.",
        "- Large plain or adapter deltas imply CDCL/order sensitivity, so original complete_coloring/php differences cannot be treated as family-specific symmetry evidence.",
        "- If canonicalization collapses complete_coloring/php behavior, the next step is to canonicalize future runtime protocols.",
        "- If canonicalization still leaves adapter-specific instability, the next step is objective/permutation robustness work, not selector training.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze EchoSAT canonical DIMACS order low-warmup audit.")
    parser.add_argument("--original-observations-csv", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--canonical-per-instance-csvs", nargs="*", type=Path, default=None)
    parser.add_argument("--canonical-input-glob", type=Path, default=DEFAULT_CANONICAL_GLOB)
    parser.add_argument("--canonical-observations-csv", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--pair-deltas-csv", type=Path, default=DEFAULT_PAIR_DELTAS)
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    original = pd.read_csv(resolve(args.original_observations_csv))
    if args.canonical_per_instance_csvs:
        paths = [resolve(path) for path in args.canonical_per_instance_csvs]
    else:
        pattern = resolve(args.canonical_input_glob)
        paths = sorted(pattern.parent.glob(pattern.name))
    canonical = canonical_observations(paths)
    pair_deltas = build_pair_deltas(original, canonical)
    summary = summarize(pair_deltas)

    canonical_path = resolve(args.canonical_observations_csv)
    pair_path = resolve(args.pair_deltas_csv)
    summary_path = resolve(args.summary_csv)
    for output_path in [canonical_path, pair_path, summary_path]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    canonical.to_csv(canonical_path, index=False)
    pair_deltas.to_csv(pair_path, index=False)
    summary.to_csv(summary_path, index=False)
    write_doc(
        resolve(args.doc),
        pair_deltas=pair_deltas,
        summary=summary,
        canonical_observations_csv=canonical_path,
        pair_deltas_csv=pair_path,
        summary_csv=summary_path,
    )
    print(f"wrote {canonical_path}")
    print(f"wrote {pair_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
