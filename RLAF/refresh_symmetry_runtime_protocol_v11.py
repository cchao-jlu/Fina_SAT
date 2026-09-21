from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from run_symmetry_solver_protocol_preflight import (
    build_attribution,
    markdown_table,
    summarize_attribution_by_base,
    summarize_by_base_instance,
    summarize_by_family,
    summarize_timeout_correctness,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_per_instance.csv"
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_manifest_labeled.csv"
DEFAULT_PER_INSTANCE = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_1_per_instance.csv"
DEFAULT_BY_FAMILY = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_1_by_family.csv"
DEFAULT_BY_BASE = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_1_by_base_instance.csv"
DEFAULT_ATTRIBUTION = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_1_attribution.csv"
DEFAULT_ATTRIBUTION_BY_BASE = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_1_attribution_by_base.csv"
DEFAULT_LOSS = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_1_guided_loss_diagnostics.csv"
DEFAULT_TIMEOUT = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_1_timeout_correctness.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_runtime_protocol_v1_1.md"


SOLVED = {"SATISFIABLE", "UNSATISFIABLE"}


def refresh_expected_labels(per_instance: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    label_columns = [
        column
        for column in [
            "cnf_path",
            "instance_id",
            "expected_result",
            "label_provenance",
            "control_type",
            "scale",
            "benchmark_role",
            "symmetry_strength",
        ]
        if column in manifest.columns
    ]
    labels = manifest[label_columns].drop_duplicates("cnf_path").copy()
    labels = labels.rename(
        columns={
            "expected_result": "manifest_expected_result",
            "label_provenance": "manifest_label_provenance",
        }
    )
    manifest_owned_columns = [
        "manifest_expected_result",
        "manifest_label_provenance",
        "label_provenance",
        "control_type",
        "scale",
        "benchmark_role",
        "symmetry_strength",
    ]
    frame = per_instance.drop(columns=[column for column in manifest_owned_columns if column in per_instance.columns]).copy()
    frame = frame.merge(
        labels[[column for column in labels.columns if column != "instance_id"]],
        on="cnf_path",
        how="left",
    )
    frame["expected_result"] = frame["manifest_expected_result"].fillna(frame["expected_result"]).astype(str)
    frame["known_expected_result"] = frame["expected_result"].isin(SOLVED)
    frame["final_expected_match"] = frame["known_expected_result"] & frame["final_result"].astype(str).eq(frame["expected_result"].astype(str))
    frame["final_known_expected_match"] = frame["final_expected_match"]
    if "manifest_label_provenance" in frame.columns:
        frame["label_provenance"] = frame["manifest_label_provenance"].fillna("")
    return frame


def correctness_denominator_by_family(per_instance: pd.DataFrame) -> pd.DataFrame:
    frame = per_instance[["family", "base_instance_id", "instance_id", "expected_result", "known_expected_result"]].drop_duplicates()
    return (
        frame.groupby("family", sort=True)
        .agg(
            cnfs=("instance_id", "count"),
            base_instances=("base_instance_id", "nunique"),
            known_expected_cnfs=("known_expected_result", lambda values: int(pd.Series(values).astype(bool).sum())),
            unknown_expected_cnfs=("known_expected_result", lambda values: int((~pd.Series(values).astype(bool)).sum())),
            expected_results=("expected_result", lambda values: ",".join(sorted(set(map(str, values))))),
        )
        .reset_index()
    )


def write_doc(
    path: Path,
    per_instance: pd.DataFrame,
    by_family: pd.DataFrame,
    attribution: pd.DataFrame,
    attribution_by_base: pd.DataFrame,
    timeout_correctness: pd.DataFrame,
    input_csv: Path,
    manifest: Path,
    per_instance_csv: Path,
    attribution_csv: Path,
    timeout_csv: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    overall = by_family[by_family["family"].astype(str).eq("__overall__")].copy()
    method_view = overall[
        [
            "method",
            "rows",
            "solved_instances",
            "known_expected_instances",
            "known_expected_match_instances",
            "mean_protocol_accounted_time",
            "mean_final_cpu_time",
            "mean_warmup_cpu_time",
            "mean_adapter_inference_wall_time",
        ]
    ].copy()
    denominator = correctness_denominator_by_family(per_instance)
    attr_matrix_columns = [
        column
        for column in [
            "weighted_binary_input_delta_protocol_time",
            "static_weights_delta_protocol_time",
            "event_collection_overhead_delta_protocol_time",
            "adapter_delta_inference_delta_protocol_time",
        ]
        if column in attribution.columns
    ]
    attr_overall = (
        attribution[attr_matrix_columns].mean().reset_index(name="mean_delta").rename(columns={"index": "attribution_delta"})
        if attr_matrix_columns
        else pd.DataFrame()
    )
    attr_modes = (
        attribution.groupby("primary_attribution", sort=True)
        .agg(rows=("instance_id", "count"), base_instances=("base_instance_id", "nunique"))
        .reset_index()
        if not attribution.empty
        else pd.DataFrame()
    )
    base_view_columns = [
        column
        for column in [
            "family",
            "base_instance_id",
            "weighted_binary_input_delta_protocol_time_mean",
            "static_weights_delta_protocol_time_mean",
            "event_collection_overhead_delta_protocol_time_mean",
            "adapter_delta_inference_delta_protocol_time_mean",
            "primary_attribution_modes",
        ]
        if column in attribution_by_base.columns
    ]
    timeout_view = timeout_correctness[
        [
            column
            for column in [
                "method",
                "family",
                "control_type",
                "scale",
                "rows",
                "known_expected_rows",
                "known_expected_match_rows",
                "known_expected_wrong_rows",
                "unknown_expected_rows",
                "solved_rows",
                "unsolved_rows",
                "indeterminate_rows",
            ]
            if column in timeout_correctness.columns
        ]
    ].copy()
    lines = [
        "# SAT Symmetry Runtime Protocol v1.1",
        "",
        "This is a protocol hygiene refresh based on the existing v1 per-instance runtime CSV.",
        "No full solver protocol was rerun, no adapter was trained, and no gate or selector was built.",
        "",
        "Main scope: viability / attribution evidence only. This is not a solver speedup claim.",
        "",
        "## Inputs",
        "",
        f"- source per-instance CSV: `{input_csv}`",
        f"- refreshed manifest: `{manifest}`",
        f"- refreshed per-instance CSV: `{per_instance_csv}`",
        f"- refreshed attribution CSV: `{attribution_csv}`",
        f"- refreshed timeout/correctness CSV: `{timeout_csv}`",
        "",
        "## Hygiene Changes",
        "",
        "- `random_3sat_control` rows now use trusted plain-solver labels when plain Glucose and CaDiCaL agree.",
        "- Until labeled, random controls are only runtime stability / attribution controls; after labeling they enter known correctness denominators.",
        "- `dominating_set_hex` remains `UNKNOWN`; it stays in runtime/attribution tables but not in correctness denominators.",
        "- Correctness metrics are computed only over `known_expected_result=True` rows. UNKNOWN rows are excluded from correctness denominators.",
        "- `weighted_no_pre_diagnostic` remains an appendix path and is not included in v1.1 main tables.",
        "",
        "## Correctness Denominators",
        "",
        *markdown_table(denominator),
        "",
        "## Overall Method Accounting",
        "",
        *markdown_table(method_view),
        "",
        "## Attribution Modes",
        "",
        *markdown_table(attr_modes),
        "",
        "## Fixed Attribution Matrix",
        "",
        *markdown_table(attr_overall),
        "",
        "## Base Attribution",
        "",
        *markdown_table(attribution_by_base[base_view_columns], max_rows=80),
        "",
        "## Timeout / Correctness",
        "",
        *markdown_table(timeout_view, max_rows=120),
        "",
        "## Interpretation Boundary",
        "",
        "The refreshed tables can support runtime viability and attribution statements.",
        "They do not establish solver speedup. Runtime benchmark v2 should expand the benchmark separately,",
        "and gate/selector work remains postponed until family/scale-specific viability is stable.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh SAT symmetry runtime protocol v1.1 summaries from existing v1 rows.")
    parser.add_argument("--input-per-instance", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--per-instance-csv", type=Path, default=DEFAULT_PER_INSTANCE)
    parser.add_argument("--by-family-csv", type=Path, default=DEFAULT_BY_FAMILY)
    parser.add_argument("--by-base-instance-csv", type=Path, default=DEFAULT_BY_BASE)
    parser.add_argument("--attribution-csv", type=Path, default=DEFAULT_ATTRIBUTION)
    parser.add_argument("--attribution-by-base-csv", type=Path, default=DEFAULT_ATTRIBUTION_BY_BASE)
    parser.add_argument("--loss-diagnostics-csv", type=Path, default=DEFAULT_LOSS)
    parser.add_argument("--timeout-correctness-csv", type=Path, default=DEFAULT_TIMEOUT)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    args = parser.parse_args()

    per_instance = pd.read_csv(args.input_per_instance)
    manifest = pd.read_csv(args.manifest)
    refreshed = refresh_expected_labels(per_instance, manifest)
    by_family = summarize_by_family(refreshed)
    by_base = summarize_by_base_instance(refreshed)
    attribution, loss = build_attribution(refreshed)
    attribution_by_base = summarize_attribution_by_base(attribution)
    timeout_correctness = summarize_timeout_correctness(refreshed)

    for path in [
        args.per_instance_csv,
        args.by_family_csv,
        args.by_base_instance_csv,
        args.attribution_csv,
        args.attribution_by_base_csv,
        args.loss_diagnostics_csv,
        args.timeout_correctness_csv,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
    refreshed.to_csv(args.per_instance_csv, index=False)
    by_family.to_csv(args.by_family_csv, index=False)
    by_base.to_csv(args.by_base_instance_csv, index=False)
    attribution.to_csv(args.attribution_csv, index=False)
    attribution_by_base.to_csv(args.attribution_by_base_csv, index=False)
    loss.to_csv(args.loss_diagnostics_csv, index=False)
    timeout_correctness.to_csv(args.timeout_correctness_csv, index=False)
    write_doc(
        args.doc,
        per_instance=refreshed,
        by_family=by_family,
        attribution=attribution,
        attribution_by_base=attribution_by_base,
        timeout_correctness=timeout_correctness,
        input_csv=args.input_per_instance,
        manifest=args.manifest,
        per_instance_csv=args.per_instance_csv,
        attribution_csv=args.attribution_csv,
        timeout_csv=args.timeout_correctness_csv,
    )
    print(f"wrote {args.per_instance_csv}")
    print(f"wrote {args.attribution_csv}")
    print(f"wrote {args.timeout_correctness_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
