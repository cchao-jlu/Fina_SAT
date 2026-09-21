from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from analyze_symmetry_targeted_mechanism_v2 import (
    DEFAULT_BASE_SUMMARY,
    DEFAULT_CHECKPOINT,
    DEFAULT_MANIFEST,
    DEFAULT_OBSERVATIONS,
    aggregate_repeat_join,
    attach_event_state,
    finite_float,
    graph_gate_info,
    markdown_table,
    mechanism_label_for_group,
    orbit_rows_for_observation,
    resolve,
    run_warmup_for_observation,
    static_graph_for_instance,
    stats_has_events,
)
from src.model.model import load_checkpoint
from src.solving.state import event_state_dim


ROOT = Path(__file__).resolve().parent

DEFAULT_DOC = ROOT / "docs/symmetry_targeted_nearby_sanity_v2.md"
DEFAULT_BASE_CSV = ROOT / "runs/analysis/symmetry_targeted_nearby_sanity_v2_base_summary.csv"
DEFAULT_VARIANT_CSV = ROOT / "runs/analysis/symmetry_targeted_nearby_sanity_v2_variant_summary.csv"
DEFAULT_REPEAT_CSV = ROOT / "runs/analysis/symmetry_targeted_nearby_sanity_v2_repeat_join.csv"
DEFAULT_ORBIT_CSV = ROOT / "runs/analysis/symmetry_targeted_nearby_sanity_v2_orbit_rows.csv"
DEFAULT_VALIDITY_CSV = ROOT / "runs/analysis/symmetry_targeted_nearby_sanity_v2_orbit_validity.csv"

NEARBY_BASES = [
    "dominating_set_hex_3x5_s3",
    "dominating_set_hex_3x6_s4",
    "dominating_set_hex_4x5_s5",
    "subset_cardinality_bw8",
    "subset_cardinality_bw10",
    "subset_cardinality_bw12",
]


def bool_count(values: pd.Series) -> int:
    return int(pd.Series(values).fillna(False).astype(bool).sum())


def limited_markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_None._"]
    view = frame.head(int(max_rows)).copy()
    lines = markdown_table(view)
    if len(frame) > int(max_rows):
        columns = list(view.columns)
        lines.append(f"| ... | {len(frame) - int(max_rows)} more rows |" + " |" * max(0, len(columns) - 2))
    return lines


def search_improved(decisions: pd.Series, conflicts: pd.Series) -> pd.Series:
    decisions = pd.to_numeric(decisions, errors="coerce").fillna(0.0)
    conflicts = pd.to_numeric(conflicts, errors="coerce").fillna(0.0)
    return (decisions < 0.0) | (conflicts < 0.0)


def search_worse(decisions: pd.Series, conflicts: pd.Series) -> pd.Series:
    decisions = pd.to_numeric(decisions, errors="coerce").fillna(0.0)
    conflicts = pd.to_numeric(conflicts, errors="coerce").fillna(0.0)
    return (decisions > 0.0) | (conflicts > 0.0)


def build_variant_summary(repeat_join: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (family, base, variant), group in repeat_join.groupby(["family", "base_instance_id", "variant"], sort=True):
        dec = pd.to_numeric(group["primary_delta_final_decisions"], errors="coerce")
        conf = pd.to_numeric(group["primary_delta_final_conflicts"], errors="coerce")
        cpu = pd.to_numeric(group["primary_delta_final_cpu"], errors="coerce")
        rows.append(
            {
                "family": family,
                "base_instance_id": base,
                "variant": variant,
                "repeat_rows": int(len(group)),
                "cpu_down_rows": int((cpu < 0.0).sum()),
                "cpu_up_rows": int((cpu > 0.0).sum()),
                "search_improved_rows": int(search_improved(dec, conf).sum()),
                "search_worse_rows": int(search_worse(dec, conf).sum()),
                "decisions_delta_mean": float(dec.mean()),
                "conflicts_delta_mean": float(conf.mean()),
                "event_positive_rows": int((pd.to_numeric(group["event_identity_gain_max"], errors="coerce").fillna(0.0) > 1.0e-6).sum()),
                "adapter_positive_rows": int((pd.to_numeric(group["adapter_identity_gain_max"], errors="coerce").fillna(0.0) > 1.0e-6).sum()),
                "event_identity_gain_max_mean": float(group["event_identity_gain_max"].mean()),
                "adapter_identity_gain_max_mean": float(group["adapter_identity_gain_max"].mean()),
                "event_row_valid_rows_sum": int(group["event_row_valid_rows"].sum()),
                "warmup_decisions_mean": float(group["warmup_decisions"].mean()),
                "warmup_conflicts_mean": float(group["warmup_conflicts"].mean()),
                "graph_gate_open_rows": bool_count(group["event_adapter_graph_gate_open"]),
            }
        )
    return pd.DataFrame(rows)


def build_base_summary(repeat_join: pd.DataFrame, runtime_base_summary: pd.DataFrame) -> pd.DataFrame:
    meta_by_base = (
        runtime_base_summary.drop_duplicates("base_instance_id").set_index("base_instance_id").to_dict("index")
        if not runtime_base_summary.empty
        else {}
    )
    rows: list[dict[str, Any]] = []
    for (family, base), group in repeat_join.groupby(["family", "base_instance_id"], sort=True):
        dec = pd.to_numeric(group["primary_delta_final_decisions"], errors="coerce")
        conf = pd.to_numeric(group["primary_delta_final_conflicts"], errors="coerce")
        cpu = pd.to_numeric(group["primary_delta_final_cpu"], errors="coerce")
        meta = meta_by_base.get(str(base), {})
        label = mechanism_label_for_group(group, require_variant_stability=True)
        rows.append(
            {
                "family": family,
                "base_instance_id": base,
                "scale": meta.get("scale", ""),
                "runtime_primary_classification": meta.get("primary_classification", ""),
                "mechanism_label": label,
                "repeat_rows": int(len(group)),
                "variants": int(group["variant"].nunique()),
                "cpu_down_rows": int((cpu < 0.0).sum()),
                "cpu_up_rows": int((cpu > 0.0).sum()),
                "search_improved_rows": int(search_improved(dec, conf).sum()),
                "search_worse_rows": int(search_worse(dec, conf).sum()),
                "decisions_delta_mean": float(dec.mean()),
                "conflicts_delta_mean": float(conf.mean()),
                "event_positive_rows": int((pd.to_numeric(group["event_identity_gain_max"], errors="coerce").fillna(0.0) > 1.0e-6).sum()),
                "adapter_positive_rows": int((pd.to_numeric(group["adapter_identity_gain_max"], errors="coerce").fillna(0.0) > 1.0e-6).sum()),
                "event_identity_gain_max_mean": float(group["event_identity_gain_max"].mean()),
                "adapter_identity_gain_max_mean": float(group["adapter_identity_gain_max"].mean()),
                "event_row_valid_rows_sum": int(group["event_row_valid_rows"].sum()),
                "warmup_decisions_mean": float(group["warmup_decisions"].mean()),
                "warmup_conflicts_mean": float(group["warmup_conflicts"].mean()),
                "graph_gate_open_rows": bool_count(group["event_adapter_graph_gate_open"]),
            }
        )
    return pd.DataFrame(rows)


def build_validity(orbit_rows: pd.DataFrame) -> pd.DataFrame:
    if orbit_rows.empty:
        return pd.DataFrame()
    return (
        orbit_rows.groupby(["family", "base_instance_id", "event_row_valid_reason"], sort=True)
        .agg(
            rows=("orbit", "count"),
            event_identity_gain_mean=("event_identity_gain", "mean"),
            event_identity_gain_max=("event_identity_gain", "max"),
            adapter_identity_gain_mean=("adapter_identity_gain", "mean"),
            adapter_identity_gain_max=("adapter_identity_gain", "max"),
            adapted_mu_range_max=("adapted_mu_range", "max"),
            static_mu_range_max=("static_mu_range", "max"),
        )
        .reset_index()
    )


def write_doc(
    *,
    doc: Path,
    bases: list[str],
    base_summary: pd.DataFrame,
    variant_summary: pd.DataFrame,
    validity: pd.DataFrame,
    elapsed: float,
    observations_csv: Path,
    manifest: Path,
) -> None:
    doc.parent.mkdir(parents=True, exist_ok=True)
    hex_summary = base_summary[base_summary["family"].astype(str).eq("dominating_set_hex")].copy()
    subset_summary = base_summary[base_summary["family"].astype(str).eq("subset_cardinality")].copy()
    key_variant_cols = [
        "family",
        "base_instance_id",
        "variant",
        "search_improved_rows",
        "search_worse_rows",
        "decisions_delta_mean",
        "conflicts_delta_mean",
        "event_positive_rows",
        "adapter_positive_rows",
        "event_identity_gain_max_mean",
        "adapter_identity_gain_max_mean",
    ]
    elapsed_text = f"{elapsed:.3f} seconds" if float(elapsed) > 0.0 else "not rerun; report regenerated from existing CSVs"
    lines = [
        "# Targeted Nearby Sanity v2",
        "",
        "## Scope",
        "",
        "This is a small targeted mechanism sanity audit around the current hex/subset diagnostic targets. It replays only the short event warmup and orbit audit for selected nearby bases; it does not expand the full v2 runtime benchmark, does not train, does not build a gate/selector, and does not make a speedup claim.",
        "",
        f"- bases: `{', '.join(bases)}`",
        f"- observations source: `{observations_csv}`",
        f"- manifest: `{manifest}`",
        f"- wall time for this audit: `{elapsed_text}`",
        "",
        "## Base Summary",
        "",
        *markdown_table(base_summary),
        "",
        "## Hex Nearby",
        "",
        *markdown_table(hex_summary),
        "",
        "## Subset Nearby",
        "",
        *markdown_table(subset_summary),
        "",
        "## Variant Summary",
        "",
        *limited_markdown_table(variant_summary[key_variant_cols], max_rows=60),
        "",
        "## Orbit Validity",
        "",
        *limited_markdown_table(validity, max_rows=80),
        "",
        "## Interpretation",
        "",
        "- Hex partial alignment is not an isolated single row: nearby hex bases emit valid event-positive rows and adapter separation, but search direction is variant-mixed and CPU is not a stable positive signal.",
        "- Subset nearby cases show the same core risk as `bw12`: event/adapter identity exists, but permutation variants can move final decisions/conflicts in opposite directions.",
        "- These results support Objective Fix v1 and targeted re-audit; they do not justify full benchmark expansion or gate/selector training.",
        "",
    ]
    doc.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Small nearby targeted sanity audit for SAT symmetry hex/subset cases.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--base-summary-csv-in", type=Path, default=DEFAULT_BASE_SUMMARY)
    parser.add_argument("--observations-csv", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--base-csv", type=Path, default=DEFAULT_BASE_CSV)
    parser.add_argument("--variant-csv", type=Path, default=DEFAULT_VARIANT_CSV)
    parser.add_argument("--repeat-csv", type=Path, default=DEFAULT_REPEAT_CSV)
    parser.add_argument("--orbit-csv", type=Path, default=DEFAULT_ORBIT_CSV)
    parser.add_argument("--validity-csv", type=Path, default=DEFAULT_VALIDITY_CSV)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--doc-only", action="store_true", help="Regenerate the markdown report from existing output CSVs.")
    parser.add_argument("--bases", nargs="*", default=NEARBY_BASES)
    parser.add_argument("--solver", default="glucose")
    parser.add_argument("--event-state-features", default="enhanced", choices=["legacy", "enhanced", "polarity"])
    parser.add_argument("--trace-lbd", type=int, default=2)
    parser.add_argument("--rnd-freq", type=float, default=0.0)
    parser.add_argument("--K", type=float, default=0.1)
    parser.add_argument("--min-orbit-size", type=int, default=2)
    parser.add_argument("--static-collapse-threshold", type=float, default=1.0e-4)
    parser.add_argument("--event-identity-eps", type=float, default=1.0e-6)
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    bases = [str(base) for base in args.bases]
    if args.doc_only:
        base_summary = pd.read_csv(resolve(args.base_csv))
        variant_summary = pd.read_csv(resolve(args.variant_csv))
        validity = pd.read_csv(resolve(args.validity_csv))
        write_doc(
            doc=resolve(args.doc),
            bases=bases,
            base_summary=base_summary,
            variant_summary=variant_summary,
            validity=validity,
            elapsed=0.0,
            observations_csv=resolve(args.observations_csv),
            manifest=resolve(args.manifest),
        )
        print(f"wrote {resolve(args.doc)}")
        return

    checkpoint = resolve(args.checkpoint).resolve()
    manifest = pd.read_csv(resolve(args.manifest))
    observations = pd.read_csv(resolve(args.observations_csv))
    runtime_base_summary = pd.read_csv(resolve(args.base_summary_csv_in))

    target_runtime = observations[observations["base_instance_id"].astype(str).isin(set(bases))].copy()
    target_runtime = target_runtime[target_runtime["event_audit_role"].fillna("event").astype(str) != "static_only"].copy()
    target_runtime = target_runtime.sort_values(["family", "base_instance_id", "variant", "repeat_id"]).reset_index(drop=True)
    if target_runtime.empty:
        raise ValueError(f"No nearby target rows found for bases: {bases}")
    from analyze_symmetry_targeted_mechanism_v2 import ensure_protocol_columns

    target_runtime = ensure_protocol_columns(target_runtime)
    manifest_lookup = {
        (str(row["base_instance_id"]), str(row["variant"])): row
        for _, row in manifest.iterrows()
        if str(row["base_instance_id"]) in set(bases)
        and str(row.get("event_audit_role", "event")) != "static_only"
    }

    model, transform, model_cfg = load_checkpoint(str(checkpoint), var_output=True)
    model.to(args.device)
    model.eval()
    expected_dim = event_state_dim(args.event_state_features)
    if int(getattr(model, "var_state_dim", 0)) != expected_dim:
        raise ValueError(
            f"event_state_features={args.event_state_features} dim {expected_dim}, "
            f"checkpoint var_state_dim={getattr(model, 'var_state_dim', 0)}"
        )
    graph_gate_indices = list(getattr(model, "event_adapter_graph_gate_indices", []) or [])
    graph_gate_threshold = getattr(model, "event_adapter_graph_gate_threshold", None)

    static_cache: dict[tuple[str, str], tuple[Any, Any, Any]] = {}
    orbit_frames: list[pd.DataFrame] = []
    start = time.perf_counter()
    for _, runtime_row in target_runtime.iterrows():
        key = (str(runtime_row["base_instance_id"]), str(runtime_row["variant"]))
        if key not in manifest_lookup:
            raise KeyError(f"manifest missing nearby key {key}")
        instance = manifest_lookup[key]
        if key not in static_cache:
            dataset, static_graph = static_graph_for_instance(
                model=model,
                transform=transform,
                model_cfg=model_cfg,
                instance=instance,
                device=args.device,
            )
            static_cache[key] = (dataset, static_graph, instance)
        dataset, static_graph, instance = static_cache[key]
        warmup_stats = run_warmup_for_observation(
            dataset=dataset,
            static_graph=static_graph,
            solver=str(args.solver),
            warmup_seed=int(runtime_row["warmup_seed"]),
            warmup_cpu_lim=float(runtime_row["warmup_cpu_lim"]),
            warmup_conflicts=int(runtime_row["warmup_conflict_budget"]),
            trace_lbd=int(args.trace_lbd),
            rnd_freq=float(args.rnd_freq),
            k_value=float(args.K),
        )
        refined = attach_event_state(static_graph, warmup_stats, event_state_features=str(args.event_state_features))
        event_info = graph_gate_info(
            getattr(refined["var"], "event_state", None),
            graph_gate_indices=graph_gate_indices,
            graph_gate_threshold=graph_gate_threshold,
        )
        event_info["events_available"] = stats_has_events(warmup_stats)
        event_info["warmup_decisions"] = finite_float(warmup_stats.get("decisions", 0.0))
        event_info["warmup_conflicts"] = finite_float(warmup_stats.get("conflicts", 0.0))
        orbit_frames.append(
            orbit_rows_for_observation(
                model=model,
                instance=instance,
                refined_graph=refined,
                warmup_stats=warmup_stats,
                runtime_row=runtime_row,
                checkpoint=checkpoint,
                device=args.device,
                event_state_features=str(args.event_state_features),
                min_orbit_size=int(args.min_orbit_size),
                static_collapse_threshold=float(args.static_collapse_threshold),
                event_identity_eps=float(args.event_identity_eps),
                event_info=event_info,
            )
        )
    elapsed = time.perf_counter() - start

    orbit_rows = pd.concat(orbit_frames, ignore_index=True)
    repeat_join = aggregate_repeat_join(orbit_rows)
    variant_summary = build_variant_summary(repeat_join)
    base_summary = build_base_summary(repeat_join, runtime_base_summary=runtime_base_summary)
    validity = build_validity(orbit_rows)

    outputs = [
        (resolve(args.base_csv), base_summary),
        (resolve(args.variant_csv), variant_summary),
        (resolve(args.repeat_csv), repeat_join),
        (resolve(args.orbit_csv), orbit_rows),
        (resolve(args.validity_csv), validity),
    ]
    for path, frame in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
        print(f"wrote {path}")
    write_doc(
        doc=resolve(args.doc),
        bases=bases,
        base_summary=base_summary,
        variant_summary=variant_summary,
        validity=validity,
        elapsed=elapsed,
        observations_csv=resolve(args.observations_csv),
        manifest=resolve(args.manifest),
    )
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
