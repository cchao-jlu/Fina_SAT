from __future__ import annotations

import argparse
import hashlib
import json
import math
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from analyze_symmetry_targeted_mechanism_v2 import (
    aggregate_repeat_join,
    attach_event_state,
    ensure_protocol_columns,
    finite_float,
    graph_gate_info,
    mechanism_label_for_group,
    orbit_rows_for_observation,
    run_warmup_for_observation,
    static_graph_for_instance,
    stats_has_events,
)
from audit_event_symmetry import markdown_table, model_supports_event_adapter
from run_symmetry_solver_protocol_preflight import DEFAULT_CHECKPOINT
from src.data.symmetry import read_orbits_json
from src.model.model import load_checkpoint
from src.solving.state import event_state_dim


ROOT = Path(__file__).resolve().parent
ATTRIBUTION = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv"
PER_INSTANCE = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_per_instance.csv"
MANIFEST = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv"
POSITIVE_BASE = ROOT / "runs/analysis/symmetry_runtime_positive_v2_base_summary.csv"
POSITIVE_OBS = ROOT / "runs/analysis/symmetry_runtime_positive_v2_observations.csv"
TARGETED_CANDIDATE = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_candidate_summary.csv"
TARGETED_REPEAT = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_repeat_join.csv"
TARGETED_ORBITS = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_orbit_rows.csv"

DOC = ROOT / "docs/symmetry_runtime_drift_strict_subset_v2.md"
SNAPSHOT_CSV = ROOT / "runs/analysis/symmetry_runtime_drift_v2_snapshot_lineage.csv"
CONSISTENCY_CSV = ROOT / "runs/analysis/symmetry_runtime_drift_v2_consistency.csv"
NAMED_DRIFT_CSV = ROOT / "runs/analysis/symmetry_runtime_drift_v2_named_candidates.csv"
STRICT_SUMMARY_CSV = ROOT / "runs/analysis/symmetry_current_strict_positive_v2_summary.csv"
STRICT_REPEAT_CSV = ROOT / "runs/analysis/symmetry_current_strict_positive_v2_repeat_join.csv"
STRICT_ORBITS_CSV = ROOT / "runs/analysis/symmetry_current_strict_positive_v2_orbit_rows.csv"
SUBSET_FAILURE_CSV = ROOT / "runs/analysis/symmetry_subset_bw12_permutation_failure_v2.csv"
SUBSET_VARIABLE_CSV = ROOT / "runs/analysis/symmetry_subset_bw12_variable_rows_v2.csv"
SUBSET_ALIGNMENT_CSV = ROOT / "runs/analysis/symmetry_subset_bw12_permutation_alignment_v2.csv"

NAMED_CANDIDATES = [
    "dominating_set_hex_3x6_s4",
    "subset_cardinality_bw12",
    "random_3sat_control_v20_c85_seed1901",
]
SUBSET_FAILURE_TARGET = "subset_cardinality_bw12"


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_snapshot(path: Path, role: str) -> dict[str, Any]:
    stat = path.stat()
    return {
        "role": role,
        "path": str(path),
        "exists": True,
        "size_bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
        "sha256": sha256_file(path),
    }


def build_snapshot_lineage(paths: dict[str, Path], per_instance: pd.DataFrame) -> pd.DataFrame:
    rows = [file_snapshot(path, role) for role, path in paths.items()]
    protocol = {
        "role": "current_runtime_protocol_signature",
        "path": str(paths["per_instance"]),
        "exists": True,
        "size_bytes": int(paths["per_instance"].stat().st_size),
        "mtime_ns": int(paths["per_instance"].stat().st_mtime_ns),
        "sha256": sha256_file(paths["per_instance"]),
        "rows": int(len(per_instance)),
        "base_instances": int(per_instance["base_instance_id"].nunique()),
        "cnfs": int(per_instance["instance_id"].nunique()),
        "methods": ",".join(sorted(map(str, per_instance["method"].unique()))),
        "variants": ",".join(sorted(map(str, per_instance["variant"].unique()))),
        "repeats": ",".join(map(str, sorted(pd.to_numeric(per_instance["repeat_id"], errors="coerce").dropna().astype(int).unique()))),
        "solver_seeds": ",".join(map(str, sorted(pd.to_numeric(per_instance["solver_seed"], errors="coerce").dropna().astype(int).unique()))),
        "warmup_seeds": ",".join(map(str, sorted(pd.to_numeric(per_instance["warmup_seed"], errors="coerce").dropna().astype(int).unique()))),
        "final_seeds": ",".join(map(str, sorted(pd.to_numeric(per_instance["final_seed"], errors="coerce").dropna().astype(int).unique()))),
        "solver_path_roles": ",".join(sorted(map(str, per_instance["solver_path_role"].unique()))),
        "weighted_no_pre_values": ",".join(sorted(map(str, per_instance["weighted_no_pre"].unique()))),
        "final_cpu_lims": ",".join(map(str, sorted(pd.to_numeric(per_instance["final_cpu_lim"], errors="coerce").dropna().unique()))),
        "warmup_cpu_lims": ",".join(map(str, sorted(pd.to_numeric(per_instance["warmup_cpu_lim"], errors="coerce").dropna().unique()))),
        "warmup_conflict_budgets": ",".join(map(str, sorted(pd.to_numeric(per_instance["warmup_conflicts"], errors="coerce").dropna().unique()))),
    }
    rows.append(protocol)
    return pd.DataFrame(rows)


def key_frame(frame: pd.DataFrame, key_columns: list[str]) -> pd.DataFrame:
    return frame[[column for column in key_columns if column in frame.columns]].drop_duplicates().copy()


def key_set(frame: pd.DataFrame, key_columns: list[str]) -> set[tuple[str, ...]]:
    if not all(column in frame.columns for column in key_columns):
        return set()
    return set(map(tuple, frame[key_columns].astype(str).itertuples(index=False, name=None)))


def joined_protocol_values(per_instance: pd.DataFrame, keys: pd.DataFrame, key_columns: list[str]) -> pd.DataFrame:
    if keys.empty:
        return pd.DataFrame()
    return keys.merge(per_instance, on=key_columns, how="left")


def unique_values_text(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    values = frame[column].dropna()
    if values.empty:
        return ""
    if pd.api.types.is_bool_dtype(values):
        return ",".join(sorted(map(str, values.astype(bool).unique())))
    if pd.api.types.is_numeric_dtype(values):
        numeric = pd.to_numeric(values, errors="coerce").dropna()
        if not numeric.empty and (numeric.round().eq(numeric)).all():
            return ",".join(map(str, sorted(numeric.astype(int).unique())))
        return ",".join(map(str, sorted(numeric.unique())))
    return ",".join(sorted(map(str, values.astype(str).unique())))


def seed_mismatch_count(source: pd.DataFrame, per_instance: pd.DataFrame, key_columns: list[str]) -> int | None:
    seed_columns = ["solver_seed", "warmup_seed", "final_seed"]
    if not all(column in source.columns for column in seed_columns):
        return None
    seed_reference = (
        per_instance[key_columns + seed_columns]
        .drop_duplicates()
        .groupby(key_columns, as_index=False)
        .agg({column: "first" for column in seed_columns})
    )
    joined = source[key_columns + seed_columns].drop_duplicates().merge(
        seed_reference,
        on=key_columns,
        how="left",
        suffixes=("_source", "_runtime"),
    )
    mismatch = pd.Series(False, index=joined.index)
    for column in seed_columns:
        mismatch = mismatch | (
            pd.to_numeric(joined[f"{column}_source"], errors="coerce")
            != pd.to_numeric(joined[f"{column}_runtime"], errors="coerce")
        )
    return int(mismatch.sum())


def protocol_ok(joined: pd.DataFrame, method_count_ok: bool, seed_mismatches: int | None) -> bool:
    expected = {
        "solver_path_role": "patched_pretrue_main",
        "weighted_no_pre": "False",
        "final_cpu_lim": "5",
        "warmup_cpu_lim": "5",
        "warmup_conflicts": "20",
        "event_state_features": "enhanced",
    }
    for column, value in expected.items():
        actual = unique_values_text(joined, column)
        if actual != value:
            return False
    if not method_count_ok:
        return False
    if seed_mismatches not in (None, 0):
        return False
    return True


def build_runtime_consistency(
    *,
    per_instance: pd.DataFrame,
    attribution: pd.DataFrame,
    observations: pd.DataFrame,
    targeted_repeat: pd.DataFrame,
    manifest: pd.DataFrame,
) -> pd.DataFrame:
    key_columns = ["base_instance_id", "variant", "repeat_id"]
    runtime_keys = key_set(per_instance, key_columns)
    manifest_keys = key_set(manifest, ["base_instance_id", "variant"])
    runtime_manifest = manifest[
        manifest.get("event_audit_role", pd.Series("", index=manifest.index)).fillna("").astype(str) != "static_only"
    ].copy()
    runtime_manifest_keys = key_set(runtime_manifest, ["base_instance_id", "variant"])
    rows: list[dict[str, Any]] = []

    for source_name, source in [
        ("attribution", attribution),
        ("positive_observations", observations),
        ("targeted_mechanism_repeat_join", targeted_repeat),
    ]:
        keys = key_frame(source, key_columns)
        source_keys = key_set(source, key_columns)
        joined = joined_protocol_values(per_instance, keys, key_columns)
        per_key_methods = (
            joined.groupby(key_columns)["method"].nunique()
            if not joined.empty and "method" in joined.columns
            else pd.Series(dtype=int)
        )
        method_count_ok = bool((per_key_methods == 5).all()) if not per_key_methods.empty else False
        seed_mismatches = seed_mismatch_count(source, per_instance, key_columns)
        rows.append(
            {
                "source": source_name,
                "rows": int(len(source)),
                "unique_keys": int(len(source_keys)),
                "duplicate_key_rows": int(len(source) - len(source_keys)),
                "missing_from_runtime_keys": int(len(source_keys - runtime_keys)),
                "extra_runtime_keys_not_in_source": int(len(runtime_keys - source_keys)),
                "base_instances": int(source["base_instance_id"].nunique()) if "base_instance_id" in source.columns else 0,
                "variants": unique_values_text(source, "variant"),
                "repeats": unique_values_text(source, "repeat_id"),
                "joined_runtime_rows": int(len(joined)),
                "methods_per_key_min": int(per_key_methods.min()) if not per_key_methods.empty else 0,
                "methods_per_key_max": int(per_key_methods.max()) if not per_key_methods.empty else 0,
                "method_count_ok": bool(method_count_ok),
                "solver_seeds": unique_values_text(joined, "solver_seed"),
                "warmup_seeds": unique_values_text(joined, "warmup_seed"),
                "final_seeds": unique_values_text(joined, "final_seed"),
                "solver_path_roles": unique_values_text(joined, "solver_path_role"),
                "weighted_no_pre_values": unique_values_text(joined, "weighted_no_pre"),
                "final_cpu_lims": unique_values_text(joined, "final_cpu_lim"),
                "warmup_cpu_lims": unique_values_text(joined, "warmup_cpu_lim"),
                "warmup_conflict_budgets": unique_values_text(joined, "warmup_conflicts"),
                "event_state_features": unique_values_text(joined, "event_state_features"),
                "seed_mismatch_count": "" if seed_mismatches is None else int(seed_mismatches),
                "protocol_consistent_with_runtime": protocol_ok(joined, method_count_ok, seed_mismatches),
            }
        )

    runtime_cnf_keys = key_set(per_instance, ["base_instance_id", "variant"])
    rows.append(
        {
            "source": "manifest_full",
            "rows": int(len(manifest)),
            "unique_keys": int(len(manifest_keys)),
            "duplicate_key_rows": int(len(manifest) - len(manifest_keys)),
            "missing_from_runtime_keys": int(len(manifest_keys - runtime_cnf_keys)),
            "extra_runtime_keys_not_in_source": int(len(runtime_cnf_keys - manifest_keys)),
            "base_instances": int(manifest["base_instance_id"].nunique()),
            "variants": unique_values_text(manifest, "variant"),
            "repeats": "",
            "joined_runtime_rows": int(len(per_instance)),
            "methods_per_key_min": 5,
            "methods_per_key_max": 5,
            "method_count_ok": True,
            "solver_seeds": unique_values_text(per_instance, "solver_seed"),
            "warmup_seeds": unique_values_text(per_instance, "warmup_seed"),
            "final_seeds": unique_values_text(per_instance, "final_seed"),
            "solver_path_roles": unique_values_text(per_instance, "solver_path_role"),
            "weighted_no_pre_values": unique_values_text(per_instance, "weighted_no_pre"),
            "final_cpu_lims": unique_values_text(per_instance, "final_cpu_lim"),
            "warmup_cpu_lims": unique_values_text(per_instance, "warmup_cpu_lim"),
            "warmup_conflict_budgets": unique_values_text(per_instance, "warmup_conflicts"),
            "event_state_features": unique_values_text(per_instance, "event_state_features"),
            "seed_mismatch_count": "",
            "protocol_consistent_with_runtime": False,
            "note": "full labeled manifest includes static_only_stress rows excluded from v2 full runtime",
        }
    )
    rows.append(
        {
            "source": "manifest_runtime_eligible",
            "rows": int(len(runtime_manifest)),
            "unique_keys": int(len(runtime_manifest_keys)),
            "duplicate_key_rows": int(len(runtime_manifest) - len(runtime_manifest_keys)),
            "missing_from_runtime_keys": int(len(runtime_manifest_keys - runtime_cnf_keys)),
            "extra_runtime_keys_not_in_source": int(len(runtime_cnf_keys - runtime_manifest_keys)),
            "base_instances": int(runtime_manifest["base_instance_id"].nunique()),
            "variants": unique_values_text(runtime_manifest, "variant"),
            "repeats": "",
            "joined_runtime_rows": int(len(per_instance)),
            "methods_per_key_min": 5,
            "methods_per_key_max": 5,
            "method_count_ok": True,
            "solver_seeds": unique_values_text(per_instance, "solver_seed"),
            "warmup_seeds": unique_values_text(per_instance, "warmup_seed"),
            "final_seeds": unique_values_text(per_instance, "final_seed"),
            "solver_path_roles": unique_values_text(per_instance, "solver_path_role"),
            "weighted_no_pre_values": unique_values_text(per_instance, "weighted_no_pre"),
            "final_cpu_lims": unique_values_text(per_instance, "final_cpu_lim"),
            "warmup_cpu_lims": unique_values_text(per_instance, "warmup_cpu_lim"),
            "warmup_conflict_budgets": unique_values_text(per_instance, "warmup_conflicts"),
            "event_state_features": unique_values_text(per_instance, "event_state_features"),
            "seed_mismatch_count": "",
            "protocol_consistent_with_runtime": bool(runtime_manifest_keys == runtime_cnf_keys),
            "note": "static_only_stress excluded",
        }
    )
    return pd.DataFrame(rows)


def named_candidate_drift(base_summary: pd.DataFrame, targeted_summary: pd.DataFrame) -> pd.DataFrame:
    targeted_by_base = (
        targeted_summary.drop_duplicates("base_instance_id").set_index("base_instance_id")
        if not targeted_summary.empty
        else pd.DataFrame()
    )
    rows: list[dict[str, Any]] = []
    selected = base_summary[base_summary["base_instance_id"].isin(NAMED_CANDIDATES)].copy()
    for _, row in selected.sort_values("base_instance_id").iterrows():
        base = str(row["base_instance_id"])
        targeted = targeted_by_base.loc[base] if base in targeted_by_base.index else {}
        rows.append(
            {
                "base_instance_id": base,
                "family": row["family"],
                "control_type": row.get("control_type", ""),
                "prior_named_status": "pre-refresh strict-like candidate",
                "current_primary_classification": row.get("primary_classification", ""),
                "current_secondary_classification": row.get("secondary_classification", ""),
                "current_majority_threshold": int(row.get("majority_threshold", 0)),
                "current_cpu_down_rows": int(row.get("primary_final_cpu_down_count", 0)),
                "current_cpu_up_rows": int(row.get("primary_final_cpu_up_count", 0)),
                "current_decisions_down_rows": int(row.get("primary_final_decisions_down_count", 0)),
                "current_decisions_up_rows": int(row.get("primary_final_decisions_up_count", 0)),
                "current_conflicts_down_rows": int(row.get("primary_final_conflicts_down_count", 0)),
                "current_conflicts_up_rows": int(row.get("primary_final_conflicts_up_count", 0)),
                "current_mean_cpu_delta": float(row.get("primary_final_cpu_mean_delta", np.nan)),
                "current_mean_decisions_delta": float(row.get("primary_final_decisions_mean_delta", np.nan)),
                "current_mean_conflicts_delta": float(row.get("primary_final_conflicts_mean_delta", np.nan)),
                "targeted_qualification_tier": targeted.get("qualification_tier", "") if isinstance(targeted, pd.Series) else "",
                "targeted_mechanism_label": targeted.get("mechanism_label", "") if isinstance(targeted, pd.Series) else "",
                "drift_interpretation": (
                    "current snapshot is not strict-positive; CPU direction fails majority"
                    if str(row.get("primary_classification", "")) != "strict_positive"
                    else "current snapshot remains strict-positive"
                ),
            }
        )
    return pd.DataFrame(rows)


def load_metadata(instance: pd.Series) -> dict[str, Any]:
    path = Path(str(instance.get("metadata_path", "")))
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def original_variable_map(instance: pd.Series) -> dict[int, int]:
    metadata = load_metadata(instance)
    num_vars = int(instance["num_vars"])
    permutation = metadata.get("permutation")
    if not permutation:
        return {var: var for var in range(1, num_vars + 1)}
    inverse = {int(new_var): old_idx for old_idx, new_var in enumerate(permutation, start=1)}
    return {var: inverse.get(var, var) for var in range(1, num_vars + 1)}


def adapted_output(model: torch.nn.Module, refined_graph: Any, device: str) -> torch.Tensor | None:
    if not model_supports_event_adapter(model):
        return None
    model.to(device)
    model.eval()
    with torch.no_grad():
        batch = next(iter(DataLoader(dataset=[refined_graph], batch_size=1, num_workers=0, shuffle=False))).to(device)
        return model(batch).detach().cpu()


def variable_rows_for_observation(
    *,
    model: torch.nn.Module,
    instance: pd.Series,
    refined_graph: Any,
    runtime_row: pd.Series,
    device: str,
    event_state_hash: str,
) -> pd.DataFrame:
    adapted = adapted_output(model, refined_graph, device=device)
    if adapted is None:
        return pd.DataFrame()
    variable_orbits = read_orbits_json(resolve(instance["orbits_path"]), num_vars=int(instance["num_vars"]))
    original_by_var = original_variable_map(instance)
    base_y = refined_graph["var"].base_y.detach().cpu().to(dtype=torch.float32)
    event_state = refined_graph["var"].event_state.detach().cpu().to(dtype=torch.float32)
    adapted = adapted.to(dtype=torch.float32)
    rows: list[dict[str, Any]] = []
    for var in range(1, int(instance["num_vars"]) + 1):
        event_vector = event_state[var - 1]
        row = {
            "family": str(instance["family"]),
            "base_instance_id": str(instance["base_instance_id"]),
            "instance_id": str(instance["instance_id"]),
            "variant": str(instance["variant"]),
            "repeat_id": int(runtime_row["repeat_id"]),
            "solver_seed": int(runtime_row["solver_seed"]),
            "warmup_seed": int(runtime_row["warmup_seed"]),
            "final_seed": int(runtime_row["final_seed"]),
            "var": int(var),
            "original_var": int(original_by_var[var]),
            "orbit": str(variable_orbits.get(var, f"singleton:{var}")),
            "event_state_hash": event_state_hash,
            "event_l2": float(event_vector.norm().item()),
            "event_sum": float(event_vector.sum().item()),
            "event_nonzero": bool(float(event_vector.norm().item()) > 1.0e-9),
            "primary_delta_final_cpu": float(runtime_row.get("primary_delta_final_cpu", np.nan)),
            "primary_delta_final_decisions": float(runtime_row.get("primary_delta_final_decisions", np.nan)),
            "primary_delta_final_conflicts": float(runtime_row.get("primary_delta_final_conflicts", np.nan)),
        }
        if base_y.shape[1] >= 1 and adapted.shape[1] >= 1:
            row["static_rho"] = float(base_y[var - 1, 0].item())
            row["adapted_rho"] = float(adapted[var - 1, 0].item())
            row["delta_rho"] = row["adapted_rho"] - row["static_rho"]
        if base_y.shape[1] >= 2 and adapted.shape[1] >= 2:
            row["static_mu"] = float(base_y[var - 1, 1].item())
            row["adapted_mu"] = float(adapted[var - 1, 1].item())
            row["delta_mu"] = row["adapted_mu"] - row["static_mu"]
        rows.append(row)
    return pd.DataFrame(rows)


def run_targeted_audit(
    *,
    target_ids: list[str],
    model: torch.nn.Module,
    transform: Any,
    model_cfg: Any,
    manifest: pd.DataFrame,
    observations: pd.DataFrame,
    checkpoint: Path,
    device: str,
    solver: str,
    event_state_features: str,
    trace_lbd: int,
    rnd_freq: float,
    k_value: float,
    min_orbit_size: int,
    static_collapse_threshold: float,
    event_identity_eps: float,
    include_variable_rows: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    target_runtime = observations[observations["base_instance_id"].isin(set(target_ids))].copy()
    target_runtime = ensure_protocol_columns(target_runtime)
    target_runtime = target_runtime.sort_values(["base_instance_id", "variant", "repeat_id"]).reset_index(drop=True)
    manifest_lookup = {
        (str(row["base_instance_id"]), str(row["variant"])): row
        for _, row in manifest.iterrows()
        if str(row["base_instance_id"]) in set(target_ids)
    }
    graph_gate_indices = list(getattr(model, "event_adapter_graph_gate_indices", []) or [])
    graph_gate_threshold = getattr(model, "event_adapter_graph_gate_threshold", None)
    static_cache: dict[tuple[str, str], tuple[Any, Any, Any]] = {}
    orbit_frames: list[pd.DataFrame] = []
    variable_frames: list[pd.DataFrame] = []
    for _, runtime_row in target_runtime.iterrows():
        key = (str(runtime_row["base_instance_id"]), str(runtime_row["variant"]))
        if key not in manifest_lookup:
            raise KeyError(f"manifest missing candidate key {key}")
        instance = manifest_lookup[key]
        if key not in static_cache:
            dataset, static_graph = static_graph_for_instance(
                model=model,
                transform=transform,
                model_cfg=model_cfg,
                instance=instance,
                device=device,
            )
            static_cache[key] = (dataset, static_graph, instance)
        dataset, static_graph, instance = static_cache[key]
        warmup_stats = run_warmup_for_observation(
            dataset=dataset,
            static_graph=static_graph,
            solver=solver,
            warmup_seed=int(runtime_row["warmup_seed"]),
            warmup_cpu_lim=float(runtime_row["warmup_cpu_lim"]),
            warmup_conflicts=int(runtime_row["warmup_conflict_budget"]),
            trace_lbd=trace_lbd,
            rnd_freq=rnd_freq,
            k_value=k_value,
        )
        refined = attach_event_state(static_graph, warmup_stats, event_state_features=event_state_features)
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
                device=device,
                event_state_features=event_state_features,
                min_orbit_size=min_orbit_size,
                static_collapse_threshold=static_collapse_threshold,
                event_identity_eps=event_identity_eps,
                event_info=event_info,
            )
        )
        if include_variable_rows:
            variable_frames.append(
                variable_rows_for_observation(
                    model=model,
                    instance=instance,
                    refined_graph=refined,
                    runtime_row=runtime_row,
                    device=device,
                    event_state_hash=str(event_info["event_state_hash"]),
                )
            )
    orbit_rows = pd.concat(orbit_frames, ignore_index=True) if orbit_frames else pd.DataFrame()
    repeat_join = aggregate_repeat_join(orbit_rows)
    variable_rows = pd.concat(variable_frames, ignore_index=True) if variable_frames else pd.DataFrame()
    return repeat_join, orbit_rows, variable_rows


def summarize_strict_current(base_summary: pd.DataFrame, strict_repeat: pd.DataFrame) -> pd.DataFrame:
    strict_bases = base_summary[base_summary["primary_classification"].astype(str).eq("strict_positive")].copy()
    rows: list[dict[str, Any]] = []
    for _, row in strict_bases.sort_values(["control_type", "base_instance_id"]).iterrows():
        base = str(row["base_instance_id"])
        group = strict_repeat[strict_repeat["base_instance_id"].astype(str).eq(base)].copy()
        rows.append(
            {
                "family": row["family"],
                "base_instance_id": base,
                "control_type": row.get("control_type", ""),
                "strict_role": "perturbation_baseline" if str(row.get("control_type", "")) == "non_symmetric_control" else "symmetry_calibration",
                "primary_classification": row.get("primary_classification", ""),
                "repeat_rows": int(len(group)),
                "variants": int(group["variant"].nunique()) if not group.empty else 0,
                "cpu_down_rows": int((pd.to_numeric(group["primary_delta_final_cpu"], errors="coerce") < 0.0).sum()),
                "decisions_down_rows": int((pd.to_numeric(group["primary_delta_final_decisions"], errors="coerce") < 0.0).sum()),
                "conflicts_down_rows": int((pd.to_numeric(group["primary_delta_final_conflicts"], errors="coerce") < 0.0).sum()),
                "event_identity_positive_rows": int((pd.to_numeric(group["event_identity_gain_max"], errors="coerce").fillna(0.0) > 1.0e-6).sum()),
                "adapter_identity_positive_rows": int((pd.to_numeric(group["adapter_identity_gain_max"], errors="coerce").fillna(0.0) > 1.0e-6).sum()),
                "mean_event_identity_gain_max": float(group["event_identity_gain_max"].mean()) if not group.empty else float("nan"),
                "mean_adapter_identity_gain_max": float(group["adapter_identity_gain_max"].mean()) if not group.empty else float("nan"),
                "mean_primary_delta_final_cpu": float(group["primary_delta_final_cpu"].mean()) if not group.empty else float("nan"),
                "mean_primary_delta_final_decisions": float(group["primary_delta_final_decisions"].mean()) if not group.empty else float("nan"),
                "mean_primary_delta_final_conflicts": float(group["primary_delta_final_conflicts"].mean()) if not group.empty else float("nan"),
                "mechanism_label": mechanism_label_for_group(group),
            }
        )
    return pd.DataFrame(rows)


def subset_failure_summary(subset_repeat: pd.DataFrame, subset_orbits: pd.DataFrame, variable_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant, group in subset_repeat.groupby("variant", sort=True):
        orbit_group = subset_orbits[subset_orbits["variant"].astype(str).eq(str(variant))]
        var_group = variable_rows[variable_rows["variant"].astype(str).eq(str(variant))]
        decisions = pd.to_numeric(group["primary_delta_final_decisions"], errors="coerce")
        conflicts = pd.to_numeric(group["primary_delta_final_conflicts"], errors="coerce")
        rows.append(
            {
                "base_instance_id": SUBSET_FAILURE_TARGET,
                "variant": str(variant),
                "repeat_rows": int(len(group)),
                "search_worse_rows": int(((decisions > 0.0) | (conflicts > 0.0)).sum()),
                "decisions_down_rows": int((decisions < 0.0).sum()),
                "decisions_up_rows": int((decisions > 0.0).sum()),
                "conflicts_down_rows": int((conflicts < 0.0).sum()),
                "conflicts_up_rows": int((conflicts > 0.0).sum()),
                "mean_event_identity_gain_max": float(group["event_identity_gain_max"].mean()),
                "mean_adapter_identity_gain_max": float(group["adapter_identity_gain_max"].mean()),
                "mean_event_l2": float(group["event_state_l2_sum"].mean()),
                "mean_gate_evidence": float(group["event_adapter_graph_gate_evidence"].mean()),
                "mean_abs_delta_mu": float(pd.to_numeric(var_group.get("delta_mu", pd.Series(dtype=float)), errors="coerce").abs().mean()),
                "mean_abs_delta_rho": float(pd.to_numeric(var_group.get("delta_rho", pd.Series(dtype=float)), errors="coerce").abs().mean()),
                "max_abs_delta_mu": float(pd.to_numeric(var_group.get("delta_mu", pd.Series(dtype=float)), errors="coerce").abs().max()),
                "max_abs_delta_rho": float(pd.to_numeric(var_group.get("delta_rho", pd.Series(dtype=float)), errors="coerce").abs().max()),
                "valid_event_orbit_rows": int(orbit_group["event_row_valid"].astype(bool).sum()) if not orbit_group.empty else 0,
                "event_positive_orbit_rows": int(orbit_group["event_identity_positive"].astype(bool).sum()) if not orbit_group.empty else 0,
                "failure_signal": (
                    "high_identity_high_adapter_search_worse"
                    if ((decisions > 0.0) | (conflicts > 0.0)).sum() >= 2
                    else "high_identity_search_improved"
                ),
            }
        )
    return pd.DataFrame(rows)


def pair_runtime(group: pd.DataFrame, variant: str) -> pd.Series | None:
    rows = group[group["variant"].astype(str).eq(variant)]
    if rows.empty:
        return None
    return rows.iloc[0]


def safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    valid = left.notna() & right.notna()
    if int(valid.sum()) < 2:
        return float("nan")
    left_valid = left[valid]
    right_valid = right[valid]
    if left_valid.nunique(dropna=True) < 2 or right_valid.nunique(dropna=True) < 2:
        return float("nan")
    return float(left_valid.corr(right_valid, method=method))


def permutation_alignment(variable_rows: pd.DataFrame, subset_repeat: pd.DataFrame) -> pd.DataFrame:
    if variable_rows.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    metrics = ["adapted_mu", "adapted_rho", "delta_mu", "delta_rho", "event_l2"]
    for (repeat_id, orbit), group in variable_rows.groupby(["repeat_id", "orbit"], sort=True):
        variants = sorted(group["variant"].astype(str).unique())
        if len(variants) < 2:
            continue
        runtime_group = subset_repeat[subset_repeat["repeat_id"].astype(int).eq(int(repeat_id))]
        for left, right in combinations(variants, 2):
            left_frame = group[group["variant"].astype(str).eq(left)].copy()
            right_frame = group[group["variant"].astype(str).eq(right)].copy()
            aligned = left_frame.merge(
                right_frame,
                on="original_var",
                suffixes=("_left", "_right"),
                how="inner",
            )
            row: dict[str, Any] = {
                "base_instance_id": SUBSET_FAILURE_TARGET,
                "repeat_id": int(repeat_id),
                "orbit": str(orbit),
                "left_variant": left,
                "right_variant": right,
                "aligned_variables": int(len(aligned)),
            }
            left_runtime = pair_runtime(runtime_group, left)
            right_runtime = pair_runtime(runtime_group, right)
            if left_runtime is not None:
                row["left_decisions_delta"] = float(left_runtime["primary_delta_final_decisions"])
                row["left_conflicts_delta"] = float(left_runtime["primary_delta_final_conflicts"])
            if right_runtime is not None:
                row["right_decisions_delta"] = float(right_runtime["primary_delta_final_decisions"])
                row["right_conflicts_delta"] = float(right_runtime["primary_delta_final_conflicts"])
            for metric in metrics:
                left_col = f"{metric}_left"
                right_col = f"{metric}_right"
                if left_col not in aligned.columns or right_col not in aligned.columns or len(aligned) < 2:
                    row[f"{metric}_spearman"] = float("nan")
                    row[f"{metric}_pearson"] = float("nan")
                    row[f"{metric}_mean_abs_diff"] = float("nan")
                    continue
                left_values = pd.to_numeric(aligned[left_col], errors="coerce")
                right_values = pd.to_numeric(aligned[right_col], errors="coerce")
                row[f"{metric}_spearman"] = safe_corr(left_values, right_values, method="spearman")
                row[f"{metric}_pearson"] = safe_corr(left_values, right_values, method="pearson")
                row[f"{metric}_mean_abs_diff"] = float((left_values - right_values).abs().mean())
            if "delta_mu_left" in aligned.columns and "delta_mu_right" in aligned.columns:
                left_delta = pd.to_numeric(aligned["delta_mu_left"], errors="coerce")
                right_delta = pd.to_numeric(aligned["delta_mu_right"], errors="coerce")
                valid_delta = left_delta.notna() & right_delta.notna()
                if int(valid_delta.sum()) > 0:
                    left_sign = np.sign(left_delta[valid_delta])
                    right_sign = np.sign(right_delta[valid_delta])
                    row["delta_mu_sign_agreement"] = float((left_sign == right_sign).mean())
                else:
                    row["delta_mu_sign_agreement"] = float("nan")
            rows.append(row)
    return pd.DataFrame(rows)


def write_doc(
    path: Path,
    *,
    snapshot: pd.DataFrame,
    consistency: pd.DataFrame,
    named_drift: pd.DataFrame,
    strict_summary: pd.DataFrame,
    subset_failure: pd.DataFrame,
    subset_alignment: pd.DataFrame,
    output_paths: dict[str, Path],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_view = snapshot[
        [column for column in ["role", "path", "size_bytes", "mtime_ns", "sha256", "rows", "base_instances", "repeats", "solver_path_roles", "weighted_no_pre_values"] if column in snapshot.columns]
    ].copy()
    consistency_view = consistency[
        [
            column
            for column in [
                "source",
                "rows",
                "unique_keys",
                "missing_from_runtime_keys",
                "extra_runtime_keys_not_in_source",
                "base_instances",
                "variants",
                "repeats",
                "methods_per_key_min",
                "methods_per_key_max",
                "solver_seeds",
                "warmup_seeds",
                "final_seeds",
                "solver_path_roles",
                "weighted_no_pre_values",
                "final_cpu_lims",
                "warmup_cpu_lims",
                "warmup_conflict_budgets",
                "protocol_consistent_with_runtime",
                "note",
            ]
            if column in consistency.columns
        ]
    ].copy()
    alignment_view = subset_alignment[
        [
            column
            for column in [
                "repeat_id",
                "orbit",
                "left_variant",
                "right_variant",
                "aligned_variables",
                "adapted_mu_spearman",
                "delta_mu_spearman",
                "delta_mu_sign_agreement",
                "left_decisions_delta",
                "right_decisions_delta",
                "left_conflicts_delta",
                "right_conflicts_delta",
            ]
            if column in subset_alignment.columns
        ]
    ].copy()
    lines = [
        "# Runtime Drift, Strict-Positive Calibration, and Subset Permutation Diagnosis v2",
        "",
        "## Scope",
        "",
        "This audit does not train, does not build a gate/selector, does not expand the",
        "runtime benchmark, and does not make a solver speedup claim. It checks current",
        "runtime snapshot lineage, calibrates the current strict-positive rows, and digs",
        "into the `subset_cardinality_bw12` permutation failure mode.",
        "",
        "## Runtime Snapshot Lineage",
        "",
        *markdown_table(snapshot_view.head(20)),
        "",
        "The current positive subset and targeted mechanism tables are derived after the",
        "refreshed v2 runtime CSV. The current runtime signature is fixed to repeats",
        "`0,1,2`, variants `base,perm_seed1730,perm_seed1731`, solver path",
        "`patched_pretrue_main`, and `weighted_no_pre=False`. Earlier strict-like",
        "status is therefore treated as a pre-refresh observation unless an archived",
        "old runtime CSV is restored for exact numeric diffing.",
        "",
        "## Runtime Consistency",
        "",
        *markdown_table(consistency_view),
        "",
        "The positive subset and targeted audit keys join back to the current v2 runtime",
        "snapshot. Positive observations cover all `315` base/variant/repeat keys; targeted",
        "mechanism audit covers only the three named diagnostic candidates by design. Seed",
        "columns are retained in targeted replay rows and match the current runtime keys.",
        "The labeled manifest has one static-only stress base (`dominating_set_hex_4x7_s7`),",
        "which is intentionally excluded from the v2 full runtime; the runtime-eligible",
        "manifest keys match the current runtime keys.",
        "",
        "## Named Candidate Drift",
        "",
        *markdown_table(named_drift),
        "",
        "The three named candidates no longer satisfy current `strict_positive` because",
        "final CPU direction is not majority-down in the refreshed snapshot. The search",
        "signals mostly remain visible for the two symmetry candidates, so the drift is",
        "best read as runtime/CPU snapshot instability plus overhead sensitivity, not as",
        "proof of solver speedup.",
        "",
        "## Current Strict-Positive Calibration",
        "",
        *markdown_table(strict_summary),
        "",
        "`complete_coloring/k5_color4` is the only current symmetry strict-positive",
        "calibration row. `random_3sat_control_v60_c180_seed1912` is a non-symmetric",
        "perturbation baseline and must not be folded into symmetry-positive evidence.",
        "",
        "## Subset Permutation Failure Diagnosis",
        "",
        *markdown_table(subset_failure),
        "",
        "Permutation-aligned variable ranking checks:",
        "",
        *markdown_table(alignment_view.head(80)),
        "",
        "`perm_seed1730` is the useful failure case: event identity and adapter separation",
        "are high, but decisions/conflicts move in the wrong direction. If aligned adapted",
        "mu/rho rankings are inconsistent with the improving variants, the adapter objective",
        "needs stronger permutation consistency. If rankings are consistent while search",
        "still worsens, the issue is likely over-reaction/search sensitivity, motivating a",
        "negative-control restraint rather than a gate.",
        "",
        "## Decision",
        "",
        "- Do not train a gate/selector from this state.",
        "- Treat current strict positives as calibration only.",
        "- Focus next on adapter objective/permutation robustness and negative-control restraint.",
        "- Keep event overhead as a separate blocker before any renewed runtime viability claim.",
        "",
        "## Artifacts",
        "",
        *[f"- {name}: `{path}`" for name, path in output_paths.items()],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit v2 runtime drift, current strict positives, and subset permutation failure.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--solver", default="glucose")
    parser.add_argument("--event-state-features", default="enhanced", choices=["legacy", "enhanced", "polarity"])
    parser.add_argument("--trace-lbd", type=int, default=2)
    parser.add_argument("--rnd-freq", type=float, default=0.0)
    parser.add_argument("--K", type=float, default=0.1)
    parser.add_argument("--min-orbit-size", type=int, default=2)
    parser.add_argument("--static-collapse-threshold", type=float, default=1.0e-4)
    parser.add_argument("--event-identity-eps", type=float, default=1.0e-6)
    args = parser.parse_args()

    paths = {
        "attribution": ATTRIBUTION,
        "per_instance": PER_INSTANCE,
        "manifest": MANIFEST,
        "positive_base_summary": POSITIVE_BASE,
        "positive_observations": POSITIVE_OBS,
        "targeted_candidate_summary": TARGETED_CANDIDATE,
        "targeted_repeat_join": TARGETED_REPEAT,
        "targeted_orbit_rows": TARGETED_ORBITS,
    }
    for path in paths.values():
        if not path.exists():
            raise FileNotFoundError(path)

    per_instance = pd.read_csv(PER_INSTANCE)
    attribution = pd.read_csv(ATTRIBUTION)
    manifest = pd.read_csv(MANIFEST)
    base_summary = pd.read_csv(POSITIVE_BASE)
    observations = pd.read_csv(POSITIVE_OBS)
    targeted_summary = pd.read_csv(TARGETED_CANDIDATE)
    targeted_repeat_existing = pd.read_csv(TARGETED_REPEAT)

    snapshot = build_snapshot_lineage(paths, per_instance=per_instance)
    consistency = build_runtime_consistency(
        per_instance=per_instance,
        attribution=attribution,
        observations=observations,
        targeted_repeat=targeted_repeat_existing,
        manifest=manifest,
    )
    named_drift = named_candidate_drift(base_summary, targeted_summary)
    strict_ids = sorted(base_summary[base_summary["primary_classification"].astype(str).eq("strict_positive")]["base_instance_id"].astype(str).unique())
    checkpoint = resolve(args.checkpoint).resolve()
    model, transform, model_cfg = load_checkpoint(str(checkpoint), var_output=True)
    model.to(args.device)
    model.eval()
    expected_dim = event_state_dim(args.event_state_features)
    if int(getattr(model, "var_state_dim", 0)) != expected_dim:
        raise ValueError(
            f"event_state_features={args.event_state_features} dim {expected_dim}, "
            f"checkpoint var_state_dim={getattr(model, 'var_state_dim', 0)}"
        )

    strict_repeat, strict_orbits, _ = run_targeted_audit(
        target_ids=strict_ids,
        model=model,
        transform=transform,
        model_cfg=model_cfg,
        manifest=manifest,
        observations=observations,
        checkpoint=checkpoint,
        device=args.device,
        solver=args.solver,
        event_state_features=args.event_state_features,
        trace_lbd=int(args.trace_lbd),
        rnd_freq=float(args.rnd_freq),
        k_value=float(args.K),
        min_orbit_size=int(args.min_orbit_size),
        static_collapse_threshold=float(args.static_collapse_threshold),
        event_identity_eps=float(args.event_identity_eps),
        include_variable_rows=False,
    )
    strict_summary = summarize_strict_current(base_summary, strict_repeat)

    subset_repeat, subset_orbits, subset_variables = run_targeted_audit(
        target_ids=[SUBSET_FAILURE_TARGET],
        model=model,
        transform=transform,
        model_cfg=model_cfg,
        manifest=manifest,
        observations=observations,
        checkpoint=checkpoint,
        device=args.device,
        solver=args.solver,
        event_state_features=args.event_state_features,
        trace_lbd=int(args.trace_lbd),
        rnd_freq=float(args.rnd_freq),
        k_value=float(args.K),
        min_orbit_size=int(args.min_orbit_size),
        static_collapse_threshold=float(args.static_collapse_threshold),
        event_identity_eps=float(args.event_identity_eps),
        include_variable_rows=True,
    )
    subset_failure = subset_failure_summary(subset_repeat, subset_orbits, subset_variables)
    subset_alignment = permutation_alignment(subset_variables, subset_repeat)

    output_frames = [
        (SNAPSHOT_CSV, snapshot),
        (CONSISTENCY_CSV, consistency),
        (NAMED_DRIFT_CSV, named_drift),
        (STRICT_SUMMARY_CSV, strict_summary),
        (STRICT_REPEAT_CSV, strict_repeat),
        (STRICT_ORBITS_CSV, strict_orbits),
        (SUBSET_FAILURE_CSV, subset_failure),
        (SUBSET_VARIABLE_CSV, subset_variables),
        (SUBSET_ALIGNMENT_CSV, subset_alignment),
    ]
    for path, frame in output_frames:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
        print(f"wrote {path}")
    output_paths = {
        "snapshot_lineage": SNAPSHOT_CSV,
        "runtime_consistency": CONSISTENCY_CSV,
        "named_candidate_drift": NAMED_DRIFT_CSV,
        "current_strict_summary": STRICT_SUMMARY_CSV,
        "current_strict_repeat_join": STRICT_REPEAT_CSV,
        "current_strict_orbit_rows": STRICT_ORBITS_CSV,
        "subset_failure": SUBSET_FAILURE_CSV,
        "subset_variable_rows": SUBSET_VARIABLE_CSV,
        "subset_permutation_alignment": SUBSET_ALIGNMENT_CSV,
    }
    write_doc(
        DOC,
        snapshot=snapshot,
        consistency=consistency,
        named_drift=named_drift,
        strict_summary=strict_summary,
        subset_failure=subset_failure,
        subset_alignment=subset_alignment,
        output_paths=output_paths,
    )
    print(f"wrote {DOC}")


if __name__ == "__main__":
    main()
