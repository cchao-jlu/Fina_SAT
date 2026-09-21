from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from analyze_echosat_low_warmup_sweep import (
    DEFAULT_GLOB,
    display_path,
    markdown_table,
    observations_from_file,
    resolve,
    summarize,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_GLOB = ROOT / "runs/analysis/echosat_runtime_v12_canonical_low_warmup_wc*_per_instance.csv"
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_runtime_v12_canonical_low_warmup_observations.csv"
DEFAULT_OVERALL = ROOT / "runs/analysis/echosat_runtime_v12_canonical_low_warmup_overall.csv"
DEFAULT_BY_FAMILY = ROOT / "runs/analysis/echosat_runtime_v12_canonical_low_warmup_by_family.csv"
DEFAULT_BY_BASE = ROOT / "runs/analysis/echosat_runtime_v12_canonical_low_warmup_by_base.csv"
DEFAULT_DOC = ROOT / "docs/echosat_runtime_v12_canonical_low_warmup.md"


def compact_overall(overall: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "warmup_conflicts",
        "observations",
        "base_instances",
        "warmup_cpu_mean",
        "adapter_cached_final_cpu_delta_mean",
        "adapter_plain_protocol_delta_mean",
        "adapter_cached_decisions_delta_mean",
        "adapter_cached_conflicts_delta_mean",
        "adapter_cached_final_cpu_improved_fraction",
        "adapter_plain_protocol_improved_fraction",
    ]
    return overall[[column for column in columns if column in overall.columns]].sort_values("warmup_conflicts")


def compact_family(by_family: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "warmup_conflicts",
        "family",
        "observations",
        "base_instances",
        "warmup_cpu_mean",
        "adapter_cached_final_cpu_delta_mean",
        "adapter_plain_protocol_delta_mean",
        "adapter_cached_decisions_delta_mean",
        "adapter_cached_conflicts_delta_mean",
        "adapter_cached_final_cpu_improved_fraction",
        "adapter_plain_protocol_improved_fraction",
        "neutral_plain_final_cpu_delta_mean",
        "static_neutral_final_cpu_delta_mean",
    ]
    return by_family[[column for column in columns if column in by_family.columns]].sort_values(["warmup_conflicts", "family"])


def compact_base(by_base: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "warmup_conflicts",
        "family",
        "base_instance_id",
        "observations",
        "warmup_cpu_mean",
        "adapter_cached_final_cpu_delta_mean",
        "adapter_plain_protocol_delta_mean",
        "adapter_cached_decisions_delta_mean",
        "adapter_cached_conflicts_delta_mean",
        "adapter_cached_final_cpu_improved_fraction",
        "adapter_plain_protocol_improved_fraction",
    ]
    return by_base[[column for column in columns if column in by_base.columns]].sort_values(
        ["warmup_conflicts", "family", "adapter_cached_final_cpu_delta_mean"]
    )


def classification(by_base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in by_base.iterrows():
        adapter_cached = float(row.get("adapter_cached_final_cpu_delta_mean", math.nan))
        adapter_protocol = float(row.get("adapter_plain_protocol_delta_mean", math.nan))
        decision_delta = float(row.get("adapter_cached_decisions_delta_mean", math.nan))
        conflict_delta = float(row.get("adapter_cached_conflicts_delta_mean", math.nan))
        if adapter_cached < 0 and decision_delta <= 0 and conflict_delta <= 0:
            cls = "search_reduction_positive"
        elif adapter_cached < 0:
            cls = "timing_positive_only"
        elif adapter_protocol < 0:
            cls = "plain_protocol_positive_but_not_adapter_cached"
        else:
            cls = "negative_or_no_signal"
        rows.append(
            {
                "warmup_conflicts": row["warmup_conflicts"],
                "family": row["family"],
                "base_instance_id": row["base_instance_id"],
                "classification": cls,
                "adapter_cached_final_cpu_delta_mean": adapter_cached,
                "adapter_plain_protocol_delta_mean": adapter_protocol,
                "adapter_cached_decisions_delta_mean": decision_delta,
                "adapter_cached_conflicts_delta_mean": conflict_delta,
            }
        )
    return pd.DataFrame(rows).sort_values(["warmup_conflicts", "family", "classification", "base_instance_id"])


def write_doc(
    path: Path,
    *,
    observations: pd.DataFrame,
    overall: pd.DataFrame,
    by_family: pd.DataFrame,
    by_base: pd.DataFrame,
    observations_csv: Path,
    overall_csv: Path,
    by_family_csv: Path,
    by_base_csv: Path,
) -> None:
    cls = classification(by_base)
    cls_summary = (
        cls.groupby(["warmup_conflicts", "family", "classification"], sort=True)
        .agg(base_instances=("base_instance_id", "nunique"))
        .reset_index()
    )
    solved_min = min(
        int(pd.Series(observations[column]).astype(bool).sum())
        for column in observations.columns
        if column.endswith("_final_solved")
    )
    known = int(pd.Series(observations["known_expected_result"]).astype(bool).sum())
    matched = int(pd.Series(observations["event_adapter_final_known_expected_match"]).astype(bool).sum())
    lines = [
        "# EchoSAT Runtime Protocol v1.2 Canonical Low-Warmup",
        "",
        "This is the canonical-order runtime protocol v1.2 main table for the current SAT symmetry check. It does not train a model, does not use a gate/selector, and does not claim solver speedup.",
        "",
        "## Scope",
        "",
        "- canonical DIMACS order: variable ids, orbit files, and expected labels preserved",
        "- methods: plain, neutral weighted, static weighted, cached trace no-adapter, event adapter",
        "- warmup budgets: low conflict budgets from this run",
        "- primary families: complete_coloring, php, random_3sat_control, subset_cardinality",
        "- original-order runs are appendix/order-sensitivity diagnostics, not mixed into these tables",
        "",
        "## Sanity",
        "",
        f"- observations: {len(observations)}",
        f"- minimum solved rows across method columns: {solved_min}",
        f"- known correctness rows: {known}",
        f"- event-adapter known matches: {matched}",
        "",
        "## Artifacts",
        "",
        f"- observations CSV: `{display_path(observations_csv)}`",
        f"- overall CSV: `{display_path(overall_csv)}`",
        f"- by-family CSV: `{display_path(by_family_csv)}`",
        f"- by-base CSV: `{display_path(by_base_csv)}`",
        "",
        "## Overall",
        "",
        *markdown_table(compact_overall(overall), max_rows=20),
        "",
        "## By Family",
        "",
        *markdown_table(compact_family(by_family), max_rows=80),
        "",
        "## Base Classification",
        "",
        *markdown_table(cls_summary, max_rows=80),
        "",
        "## By Base",
        "",
        *markdown_table(compact_base(by_base), max_rows=120),
        "",
        "## Interpretation",
        "",
        "- `adapter_cached_final_cpu_delta_mean < 0` is the main final-search viability signal after sharing the same cached-trace path.",
        "- `adapter_plain_protocol_delta_mean < 0` is the stricter end-to-end comparison against basic Glucose.",
        "- Random-control wins remain generic perturbation evidence, not SAT symmetry-specific benefit.",
        "- If canonical-order results are still unstable, objective/order-robustness work should precede any gate or selector.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze EchoSAT runtime v1.2 canonical low-warmup outputs.")
    parser.add_argument("--per-instance-csvs", nargs="*", type=Path, default=None)
    parser.add_argument("--input-glob", type=Path, default=DEFAULT_INPUT_GLOB)
    parser.add_argument("--observations-csv", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--overall-csv", type=Path, default=DEFAULT_OVERALL)
    parser.add_argument("--by-family-csv", type=Path, default=DEFAULT_BY_FAMILY)
    parser.add_argument("--by-base-csv", type=Path, default=DEFAULT_BY_BASE)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--families", nargs="*", default=["complete_coloring", "php", "random_3sat_control", "subset_cardinality"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.per_instance_csvs:
        paths = [resolve(path) for path in args.per_instance_csvs]
    else:
        pattern = resolve(args.input_glob)
        paths = sorted(pattern.parent.glob(pattern.name))
    if not paths:
        raise SystemExit("No v1.2 canonical per-instance CSVs found.")

    observations = pd.concat(
        [observations_from_file(path, allow_weighted_no_pre=False) for path in paths],
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
    family_path = resolve(args.by_family_csv)
    base_path = resolve(args.by_base_csv)
    for output_path in [observation_path, overall_path, family_path, base_path]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    observations.to_csv(observation_path, index=False)
    overall.to_csv(overall_path, index=False)
    by_family.to_csv(family_path, index=False)
    by_base.to_csv(base_path, index=False)
    write_doc(
        resolve(args.doc),
        observations=observations,
        overall=overall,
        by_family=by_family,
        by_base=by_base,
        observations_csv=observation_path,
        overall_csv=overall_path,
        by_family_csv=family_path,
        by_base_csv=base_path,
    )
    print(f"wrote {observation_path}")
    print(f"wrote {overall_path}")
    print(f"wrote {family_path}")
    print(f"wrote {base_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
