from __future__ import annotations

import argparse
from copy import copy
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from joblib import Parallel, delayed
from torch_geometric.loader import DataLoader

from src.data.dataset import DimacsCNFDataset
from src.model.model import load_checkpoint
from src.policy.evaluate import sample_var_params
from src.solving.budget import apply_rollout_budget
from src.solving.solver import neutral_var_params
from src.solving.solver import solve_cnf
from src.solving.state import attach_var_event_state, event_state_dim


ROOT = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = ROOT / "runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt"
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_stress_manifest.csv"
DEFAULT_PER_INSTANCE = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_per_instance.csv"
DEFAULT_PHASES = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_phases.csv"
DEFAULT_BY_FAMILY = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_by_family.csv"
DEFAULT_BY_BASE_INSTANCE = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_by_base_instance.csv"
DEFAULT_ATTRIBUTION = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_attribution.csv"
DEFAULT_ATTRIBUTION_BY_BASE = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_attribution_by_base.csv"
DEFAULT_LOSS_DIAGNOSTICS = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_guided_loss_diagnostics.csv"
DEFAULT_TIMEOUT_CORRECTNESS = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_timeout_correctness.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_solver_protocol_preflight.md"


METHOD_ORDER = [
    "plain_unguided_glucose",
    "neutral_weighted_glucose",
    "static_weighted_glucose",
    "cached_trace_no_adapter_final",
    "event_adapter_final",
]
FINAL_STATS = ["Result", "decisions", "conflicts", "propagations", "restarts", "CPU time"]
EVENT_COLUMNS = [
    "event_var_decisions",
    "event_var_propagations",
    "event_var_conflict_lits",
    "event_var_learnt_lits",
    "event_var_activity",
]
STRATIFICATION_COLUMNS = [
    "event_audit_role",
    "symmetry_strength",
    "control_type",
    "scale",
    "scale_key",
    "benchmark_role",
    "family_scale",
    "variant_role",
    "permutation_variant",
    "source",
]
ATTRIBUTION_MATRIX_COLUMNS = [
    "weighted_binary_input_delta_final_cpu",
    "weighted_binary_input_delta_protocol_time",
    "weighted_binary_input_delta_final_decisions",
    "weighted_binary_input_delta_final_conflicts",
    "static_weights_delta_final_cpu",
    "static_weights_delta_protocol_time",
    "static_weights_delta_final_decisions",
    "static_weights_delta_final_conflicts",
    "event_collection_overhead_delta_final_cpu",
    "event_collection_overhead_delta_protocol_time",
    "event_collection_overhead_delta_final_decisions",
    "event_collection_overhead_delta_final_conflicts",
    "adapter_delta_inference_delta_final_cpu",
    "adapter_delta_inference_delta_protocol_time",
    "adapter_delta_inference_delta_final_decisions",
    "adapter_delta_inference_delta_final_conflicts",
    "adapter_inference_wall_time",
]


def resolve_path(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def finite_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(out):
        return default
    return out


def solver_cli_number(value: float | int | None) -> int | float | None:
    if value is None:
        return None
    number = float(value)
    if number.is_integer():
        return int(number)
    return number


def clean_solver_params(params: dict[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in params.items() if value is not None}


def with_optional_no_pre(params: dict[str, Any], enabled: bool) -> dict[str, Any]:
    updated = dict(params)
    if enabled:
        updated["no-pre"] = True
    return updated


def solver_path_role(weighted_no_pre: bool) -> str:
    return "weighted_no_pre_diagnostic" if weighted_no_pre else "patched_pretrue_main"


def cnf_id_value(graph: Any) -> int:
    value = graph.cnf_id
    return int(value.item() if hasattr(value, "item") else value)


def graph_var_params(graph: Any, sample_id: int = 0) -> np.ndarray:
    values = graph["var"].var_params.detach().cpu().numpy()
    if values.ndim == 3:
        return values[:, int(sample_id), :]
    if values.ndim == 2:
        return values
    raise ValueError(f"Unexpected var_params shape {tuple(values.shape)}")


def neutral_weighted_graphs(graphs: list[Any], weight: float = 1.0, phase: float = 0.0) -> list[Any]:
    neutral: list[Any] = []
    for graph in graphs:
        updated = graph.clone() if hasattr(graph, "clone") else copy(graph)
        num_vars = int(getattr(updated["var"], "num_nodes", updated["lit"].num_nodes // 2))
        updated["var"].num_nodes = num_vars
        updated["var"].var_params = torch.from_numpy(
            neutral_var_params(num_vars, weight=weight, phase=phase)
        ).unsqueeze(1)
        neutral.append(updated)
    return neutral


def make_dimacs_dataset(paths: list[str], transform: Any) -> DimacsCNFDataset:
    try:
        return DimacsCNFDataset(path=paths, transform=transform, lazy=True)
    except TypeError:
        return DimacsCNFDataset(path=paths, transform=transform)


def load_manifest(
    manifest_path: Path,
    families: list[str] | None,
    control_types: list[str] | None,
    scales: list[str] | None,
    benchmark_roles: list[str] | None,
    include_static_only: bool,
    base_only: bool,
) -> pd.DataFrame:
    manifest = pd.read_csv(manifest_path)
    if not include_static_only and "event_audit_role" in manifest.columns:
        role = manifest["event_audit_role"].fillna("event").astype(str)
        manifest = manifest[role != "static_only"].copy()
    if families:
        manifest = manifest[manifest["family"].astype(str).isin(set(families))].copy()
    if control_types and "control_type" in manifest.columns:
        manifest = manifest[manifest["control_type"].astype(str).isin(set(control_types))].copy()
    if scales and "scale" in manifest.columns:
        manifest = manifest[manifest["scale"].astype(str).isin(set(scales))].copy()
    if benchmark_roles and "benchmark_role" in manifest.columns:
        manifest = manifest[manifest["benchmark_role"].astype(str).isin(set(benchmark_roles))].copy()
    if base_only and "variant" in manifest.columns:
        manifest = manifest[manifest["variant"].astype(str) == "base"].copy()
    if manifest.empty:
        raise ValueError("Manifest filtering produced zero rows")
    manifest["cnf_path"] = manifest["cnf_path"].map(lambda value: str(resolve_path(str(value)).resolve()))
    return manifest.reset_index(drop=True)


def manifest_lookup_by_file(dataset: DimacsCNFDataset, manifest: pd.DataFrame) -> dict[int, pd.Series]:
    by_path = {str(Path(path).resolve()): row for _, row in manifest.iterrows() for path in [row["cnf_path"]]}
    lookup: dict[int, pd.Series] = {}
    missing: list[str] = []
    for cnf_id, file_name in dataset.id_to_file.items():
        key = str(Path(file_name).resolve())
        row = by_path.get(key)
        if row is None:
            missing.append(key)
        else:
            lookup[int(cnf_id)] = row
    if missing:
        raise ValueError(f"Dataset contains files not present in manifest: {missing[:5]}")
    return lookup


def run_solver_one(
    cnf_id: int,
    sample_id: int,
    clauses: list[list[int]],
    file_name: str,
    var_params: np.ndarray | None,
    solver: str,
    seed: int,
    solver_params: dict[str, Any],
    repeat_id: int,
) -> dict[str, Any]:
    start = time.perf_counter()
    stats = solve_cnf(
        clauses,
        var_params=var_params,
        seed=seed,
        solver=solver,
        **solver_params,
    )
    wall = time.perf_counter() - start
    stats["cnf_id"] = int(cnf_id)
    stats["sample_id"] = int(sample_id)
    stats["file"] = file_name
    stats["solver_wall_time"] = float(wall)
    stats["repeat_id"] = int(repeat_id)
    stats["solver_seed"] = int(seed)
    return stats


def run_solver_batch(
    dataset: DimacsCNFDataset,
    graphs: list[Any],
    guided: bool,
    solver: str,
    seed: int,
    solver_params: dict[str, Any],
    num_workers: int,
    phase_name: str,
    repeat_id: int,
) -> pd.DataFrame:
    inputs = []
    for graph in graphs:
        cnf_id = cnf_id_value(graph)
        cnf = dataset.cnf_list[cnf_id]
        file_name = str(dataset.id_to_file[cnf_id])
        params = graph_var_params(graph) if guided else None
        inputs.append((cnf_id, 0, cnf.clauses, file_name, params, solver, seed, solver_params, repeat_id))
    print(f"running {phase_name}: {len(inputs)} solver calls, guided={guided}, workers={num_workers}")
    rows = Parallel(n_jobs=max(1, int(num_workers)))(
        delayed(run_solver_one)(*args)
        for args in inputs
    )
    frame = pd.DataFrame.from_records(rows)
    frame["phase_name"] = phase_name
    return frame


def stats_by_cnf(frame: pd.DataFrame) -> dict[int, pd.Series]:
    if frame.empty:
        return {}
    return {int(row["cnf_id"]): row for _, row in frame.sort_values(["cnf_id", "sample_id"]).iterrows()}


def stats_by_repeat_cnf(frame: pd.DataFrame) -> dict[tuple[int, int], pd.Series]:
    if frame.empty:
        return {}
    if "repeat_id" not in frame.columns:
        return {(0, int(row["cnf_id"])): row for _, row in frame.sort_values(["cnf_id", "sample_id"]).iterrows()}
    return {
        (int(row["repeat_id"]), int(row["cnf_id"])): row
        for _, row in frame.sort_values(["repeat_id", "cnf_id", "sample_id"]).iterrows()
    }


def solver_result_value(row: pd.Series | None) -> str:
    if row is None:
        return ""
    return str(row.get("Result", ""))


def is_solved_result(result: str) -> bool:
    return result in {"SATISFIABLE", "UNSATISFIABLE"}


def expected_matches(result: str, expected: str) -> bool:
    if not expected:
        return False
    if expected == "UNKNOWN":
        return False
    return result == expected


def stats_has_events(row: pd.Series | None) -> bool:
    if row is None:
        return False
    for column in EVENT_COLUMNS:
        value = row.get(column)
        if isinstance(value, (list, tuple)) and len(value) > 0:
            return True
    return False


def attach_event_state_per_graph(
    graphs: list[Any],
    warmup_stats: pd.DataFrame,
    var_state_dim: int,
    feature_mode: str,
    graph_gate_indices: list[int] | None = None,
    graph_gate_threshold: float | None = None,
) -> tuple[list[Any], dict[int, dict[str, float | bool]]]:
    warmup_by_cnf = stats_by_cnf(warmup_stats)
    refined: list[Any] = []
    attach_info: dict[int, dict[str, float | bool]] = {}
    for graph in graphs:
        cnf_id = cnf_id_value(graph)
        stats = warmup_by_cnf.get(cnf_id)
        start = time.perf_counter()
        if stats is None:
            updated = graph
        else:
            updated = attach_var_event_state(
                graph,
                stats=stats,
                var_state_dim=var_state_dim,
                momentum=0.0,
                feature_mode=feature_mode,
            )
        wall = time.perf_counter() - start
        state = getattr(updated["var"], "event_state", None)
        if state is None:
            nonzero_vars = 0
            l2_sum = 0.0
            l2_max = 0.0
        else:
            per_var_l2 = state.detach().cpu().to(dtype=torch.float32).norm(dim=1)
            nonzero_vars = int((per_var_l2 > 1.0e-9).sum().item())
            l2_sum = float(per_var_l2.sum().item())
            l2_max = float(per_var_l2.max().item()) if per_var_l2.numel() else 0.0
        gate_indices = [int(index) for index in (graph_gate_indices or []) if state is not None and int(index) < state.shape[1]]
        if state is None:
            gate_evidence = 0.0
            gate_open = False
        elif not gate_indices or graph_gate_threshold is None:
            gate_evidence = 0.0
            gate_open = True
        else:
            gate_values = state[:, gate_indices].detach().cpu().to(dtype=torch.float32).clamp_min(0.0)
            gate_evidence = float(gate_values.max().item()) if gate_values.numel() else 0.0
            gate_open = bool(gate_evidence >= float(graph_gate_threshold))
        attach_info[cnf_id] = {
            "event_attach_wall_time": float(wall),
            "events_available": bool(stats_has_events(stats)),
            "event_state_nonzero_vars": int(nonzero_vars),
            "event_state_l2_sum": float(l2_sum),
            "event_state_l2_max": float(l2_max),
            "event_adapter_graph_gate_evidence": float(gate_evidence),
            "event_adapter_graph_gate_open": bool(gate_open),
        }
        refined.append(updated)
    return refined, attach_info


def graph_time_map(graphs: list[Any], key: str) -> dict[int, float]:
    return {cnf_id_value(graph): finite_float(getattr(graph, key, 0.0)) for graph in graphs}


def build_method_row(
    method: str,
    graph: Any,
    instance: pd.Series,
    final_stats: pd.Series | None,
    repeat_id: int,
    solver_seed: int,
    final_seed: int,
    warmup_seed: int,
    static_inference_wall_time: float,
    warmup_stats: pd.Series | None,
    warmup_wall_time: float,
    event_attach_info: dict[str, float | bool] | None,
    adapter_inference_wall_time: float,
    uses_static_guidance: bool,
    uses_warmup_events: bool,
    uses_adapter: bool,
    cached_trace_ablation: bool,
    final_reused_from: str,
    checkpoint: Path,
    solver: str,
    final_cpu_lim: float,
    warmup_cpu_lim: float,
    warmup_conflicts: int,
    event_state_features: str,
    weighted_no_pre: bool,
) -> dict[str, Any]:
    event_attach_info = event_attach_info or {}
    final_result = solver_result_value(final_stats)
    expected = str(instance.get("expected_result", ""))
    known_expected = expected in {"SATISFIABLE", "UNSATISFIABLE"}
    final_cpu = finite_float(final_stats.get("CPU time") if final_stats is not None else 0.0)
    final_wall = finite_float(final_stats.get("solver_wall_time") if final_stats is not None else 0.0)
    warmup_cpu = finite_float(warmup_stats.get("CPU time") if warmup_stats is not None else 0.0)
    attach_wall = finite_float(event_attach_info.get("event_attach_wall_time", 0.0))
    static_wall = finite_float(static_inference_wall_time) if uses_static_guidance else 0.0
    adapter_wall = finite_float(adapter_inference_wall_time) if uses_adapter else 0.0
    warmup_wall = finite_float(warmup_wall_time) if uses_warmup_events else 0.0
    accounted = static_wall + warmup_cpu + attach_wall + adapter_wall + final_cpu
    wall_accounted = static_wall + warmup_wall + attach_wall + adapter_wall + final_wall
    row: dict[str, Any] = {
        "family": str(instance["family"]),
        "instance_id": str(instance["instance_id"]),
        "base_instance_id": str(instance["base_instance_id"]),
        "variant": str(instance["variant"]),
        "expected_result": expected,
        "num_vars": int(instance["num_vars"]),
        "num_clauses": int(instance["num_clauses"]),
        "cnf_id": cnf_id_value(graph),
        "cnf_path": str(instance["cnf_path"]),
        "method": method,
        "checkpoint": str(checkpoint),
        "solver": solver,
        "repeat_id": int(repeat_id),
        "seed": int(solver_seed),
        "solver_seed": int(solver_seed),
        "final_seed": int(final_seed),
        "warmup_seed": int(warmup_seed),
        "final_cpu_lim": float(final_cpu_lim),
        "warmup_cpu_lim": float(warmup_cpu_lim),
        "warmup_conflicts": int(warmup_conflicts),
        "event_state_features": event_state_features,
        "weighted_no_pre": bool(weighted_no_pre),
        "solver_path_role": solver_path_role(bool(weighted_no_pre)),
        "uses_static_guidance": bool(uses_static_guidance),
        "uses_warmup_events": bool(uses_warmup_events),
        "uses_adapter": bool(uses_adapter),
        "cached_trace_ablation": bool(cached_trace_ablation),
        "final_reused_from": final_reused_from,
        "final_result": final_result,
        "final_solved": bool(is_solved_result(final_result)),
        "known_expected_result": bool(known_expected),
        "final_expected_match": bool(expected_matches(final_result, expected)),
        "final_known_expected_match": bool(known_expected and expected_matches(final_result, expected)),
        "final_cpu_time": final_cpu,
        "final_wall_time": final_wall,
        "final_decisions": finite_float(final_stats.get("decisions") if final_stats is not None else 0.0),
        "final_conflicts": finite_float(final_stats.get("conflicts") if final_stats is not None else 0.0),
        "final_propagations": finite_float(final_stats.get("propagations") if final_stats is not None else 0.0),
        "final_restarts": finite_float(final_stats.get("restarts") if final_stats is not None else 0.0),
        "final_solver_returncode": int(final_stats.get("solver_returncode", -1)) if final_stats is not None else -1,
        "static_inference_wall_time": static_wall,
        "warmup_result": solver_result_value(warmup_stats),
        "warmup_cpu_time": warmup_cpu,
        "warmup_wall_time": warmup_wall,
        "warmup_decisions": finite_float(warmup_stats.get("decisions") if warmup_stats is not None else 0.0),
        "warmup_conflict_count": finite_float(warmup_stats.get("conflicts") if warmup_stats is not None else 0.0),
        "warmup_solver_returncode": int(warmup_stats.get("solver_returncode", -1)) if warmup_stats is not None else -1,
        "events_available": bool(event_attach_info.get("events_available", False)),
        "event_state_nonzero_vars": int(event_attach_info.get("event_state_nonzero_vars", 0)),
        "event_state_l2_sum": finite_float(event_attach_info.get("event_state_l2_sum", 0.0)),
        "event_state_l2_max": finite_float(event_attach_info.get("event_state_l2_max", 0.0)),
        "event_adapter_graph_gate_evidence": finite_float(event_attach_info.get("event_adapter_graph_gate_evidence", 0.0)),
        "event_adapter_graph_gate_open": bool(event_attach_info.get("event_adapter_graph_gate_open", False)),
        "event_attach_wall_time": attach_wall if uses_warmup_events else 0.0,
        "adapter_inference_wall_time": adapter_wall,
        "protocol_accounted_time": float(accounted),
        "protocol_wall_time": float(wall_accounted),
        "protocol_supported": bool((not uses_warmup_events) or event_attach_info.get("events_available", False)),
    }
    for column in STRATIFICATION_COLUMNS:
        if column in instance.index:
            value = instance.get(column)
            if column == "permutation_variant":
                row[column] = bool(value)
            else:
                row[column] = str(value)
    return row


def phase_rows_for_method(row: dict[str, Any]) -> list[dict[str, Any]]:
    base = {
        key: row[key]
        for key in [
            "family",
            "instance_id",
            "base_instance_id",
            "variant",
            "cnf_id",
            "method",
            "repeat_id",
            "solver_seed",
            "final_seed",
            "warmup_seed",
            "checkpoint",
            "solver",
            "event_state_features",
            "weighted_no_pre",
            "solver_path_role",
        ]
    }
    for column in STRATIFICATION_COLUMNS:
        if column in row:
            base[column] = row[column]
    phases: list[dict[str, Any]] = []

    def add_phase(name: str, accounted: float, wall: float, cpu: float = 0.0, active: bool = True) -> None:
        phases.append(
            {
                **base,
                "phase": name,
                "phase_active": bool(active),
                "phase_accounted_time": float(accounted),
                "phase_wall_time": float(wall),
                "phase_solver_cpu_time": float(cpu),
            }
        )

    add_phase(
        "static_inference",
        row["static_inference_wall_time"],
        row["static_inference_wall_time"],
        active=bool(row["uses_static_guidance"]),
    )
    add_phase(
        "warmup_rollout_collect_events",
        row["warmup_cpu_time"],
        row["warmup_wall_time"],
        cpu=row["warmup_cpu_time"],
        active=bool(row["uses_warmup_events"]),
    )
    add_phase(
        "event_feature_attach",
        row["event_attach_wall_time"],
        row["event_attach_wall_time"],
        active=bool(row["uses_warmup_events"]),
    )
    add_phase(
        "adapter_inference",
        row["adapter_inference_wall_time"],
        row["adapter_inference_wall_time"],
        active=bool(row["uses_adapter"]),
    )
    add_phase(
        "final_solve",
        row["final_cpu_time"],
        row["final_wall_time"],
        cpu=row["final_cpu_time"],
        active=True,
    )
    return phases


def summarize_by_family(per_instance: pd.DataFrame) -> pd.DataFrame:
    if per_instance.empty:
        return pd.DataFrame()

    def aggregate(frame: pd.DataFrame, family_name: str) -> pd.DataFrame:
        out = (
            frame.groupby("method", sort=False)
            .agg(
                rows=("instance_id", "count"),
                families=("family", "nunique"),
                solved_instances=("final_solved", lambda values: int(pd.Series(values).astype(bool).sum())),
                known_expected_instances=("known_expected_result", lambda values: int(pd.Series(values).astype(bool).sum())),
                known_expected_match_instances=("final_known_expected_match", lambda values: int(pd.Series(values).astype(bool).sum())),
                protocol_supported_instances=("protocol_supported", lambda values: int(pd.Series(values).astype(bool).sum())),
                events_available_instances=("events_available", lambda values: int(pd.Series(values).astype(bool).sum())),
                mean_protocol_accounted_time=("protocol_accounted_time", "mean"),
                median_protocol_accounted_time=("protocol_accounted_time", "median"),
                mean_protocol_wall_time=("protocol_wall_time", "mean"),
                mean_final_cpu_time=("final_cpu_time", "mean"),
                median_final_cpu_time=("final_cpu_time", "median"),
                mean_final_wall_time=("final_wall_time", "mean"),
                mean_final_decisions=("final_decisions", "mean"),
                mean_final_conflicts=("final_conflicts", "mean"),
                mean_static_inference_wall_time=("static_inference_wall_time", "mean"),
                mean_warmup_cpu_time=("warmup_cpu_time", "mean"),
                mean_warmup_wall_time=("warmup_wall_time", "mean"),
                mean_event_attach_wall_time=("event_attach_wall_time", "mean"),
                mean_adapter_inference_wall_time=("adapter_inference_wall_time", "mean"),
                mean_event_state_nonzero_vars=("event_state_nonzero_vars", "mean"),
                mean_event_state_l2_sum=("event_state_l2_sum", "mean"),
            )
            .reset_index()
        )
        out.insert(0, "family", family_name)
        return out

    frames = [aggregate(group, str(family)) for family, group in per_instance.groupby("family", sort=True)]
    frames.append(aggregate(per_instance, "__overall__"))
    return pd.concat(frames, ignore_index=True)


def summarize_by_base_instance(per_instance: pd.DataFrame) -> pd.DataFrame:
    if per_instance.empty:
        return pd.DataFrame()
    out = (
        per_instance.groupby(["family", "base_instance_id", "method"], sort=True)
        .agg(
            repeats=("repeat_id", "nunique"),
            variants=("variant", "nunique"),
            rows=("instance_id", "count"),
            solved_rows=("final_solved", lambda values: int(pd.Series(values).astype(bool).sum())),
            known_expected_rows=("known_expected_result", lambda values: int(pd.Series(values).astype(bool).sum())),
            known_expected_match_rows=("final_known_expected_match", lambda values: int(pd.Series(values).astype(bool).sum())),
            protocol_supported_rows=("protocol_supported", lambda values: int(pd.Series(values).astype(bool).sum())),
            events_available_rows=("events_available", lambda values: int(pd.Series(values).astype(bool).sum())),
            mean_protocol_accounted_time=("protocol_accounted_time", "mean"),
            median_protocol_accounted_time=("protocol_accounted_time", "median"),
            std_protocol_accounted_time=("protocol_accounted_time", "std"),
            mean_final_cpu_time=("final_cpu_time", "mean"),
            median_final_cpu_time=("final_cpu_time", "median"),
            std_final_cpu_time=("final_cpu_time", "std"),
            mean_warmup_cpu_time=("warmup_cpu_time", "mean"),
            mean_adapter_inference_wall_time=("adapter_inference_wall_time", "mean"),
            mean_event_state_nonzero_vars=("event_state_nonzero_vars", "mean"),
            graph_gate_open_rows=("event_adapter_graph_gate_open", lambda values: int(pd.Series(values).astype(bool).sum())),
        )
        .reset_index()
    )
    out["method"] = pd.Categorical(out["method"], categories=METHOD_ORDER, ordered=True)
    return out.sort_values(["family", "base_instance_id", "method"]).reset_index(drop=True)


def classify_degradation(unguided_solved: bool, candidate_solved: bool, candidate_result: str) -> str:
    if not unguided_solved:
        return "unguided_not_solved"
    if candidate_solved:
        return "not_lost"
    if candidate_result == "INDETERMINATE":
        return "lost_indeterminate"
    if candidate_result:
        return "lost_wrong_or_unknown_result"
    return "lost_missing_result"


def build_attribution(per_instance: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if per_instance.empty:
        return pd.DataFrame(), pd.DataFrame()
    keys = ["repeat_id", "family", "base_instance_id", "variant", "instance_id"]
    strat_keys = [column for column in STRATIFICATION_COLUMNS if column in per_instance.columns]
    required = set(keys + ["method"])
    if not required.issubset(per_instance.columns):
        return pd.DataFrame(), pd.DataFrame()
    value_columns = [
        "final_solved",
        "final_result",
        "final_cpu_time",
        "protocol_accounted_time",
        "final_decisions",
        "final_conflicts",
        "adapter_inference_wall_time",
        "warmup_decisions",
        "warmup_conflict_count",
        "events_available",
        "event_state_nonzero_vars",
        "event_state_l2_sum",
        "event_adapter_graph_gate_open",
        "event_adapter_graph_gate_evidence",
    ]
    key_meta = (
        per_instance[keys + strat_keys]
        .drop_duplicates(subset=keys)
        .set_index(keys)
        if strat_keys
        else pd.DataFrame()
    )
    wide = per_instance[keys + ["method", *value_columns]].pivot_table(
        index=keys,
        columns="method",
        values=value_columns,
        aggfunc="first",
    )
    rows: list[dict[str, Any]] = []
    loss_rows: list[dict[str, Any]] = []
    loss_columns = [
        "repeat_id",
        "family",
        "base_instance_id",
        "variant",
        "instance_id",
        "plain_solved",
        "neutral_solved",
        "static_solved",
        "cached_trace_solved",
        "adapter_solved",
        "neutral_degradation",
        "static_degradation",
        "adapter_degradation",
        "neutral_lost_from_plain",
        "static_lost_after_neutral",
        "adapter_lost_after_static",
        "primary_attribution",
        "static_minus_neutral_final_cpu",
        "cached_minus_static_protocol_time",
        "adapter_minus_cached_protocol_time",
        *ATTRIBUTION_MATRIX_COLUMNS,
        "warmup_decisions",
        "warmup_conflicts",
        "events_available",
        "event_state_nonzero_vars",
        "event_state_l2_sum",
        "event_adapter_graph_gate_open",
        "event_adapter_graph_gate_evidence",
        "static_final_lost",
        "event_final_lost",
        "event_worse_than_static",
        "static_final_result",
        "event_final_result",
        "neutral_final_result",
        "final_loss_mode",
    ]
    for key_values, row in wide.iterrows():
        key_dict = dict(zip(keys, key_values))
        if strat_keys and key_values in key_meta.index:
            for column in strat_keys:
                key_dict[column] = key_meta.loc[key_values, column]

        def value(method: str, column: str, default: Any = None) -> Any:
            try:
                out = row[(column, method)]
            except KeyError:
                return default
            if pd.isna(out):
                return default
            return out

        missing_methods = [method for method in METHOD_ORDER if pd.isna(value(method, "final_cpu_time", float("nan")))]
        plain_final_cpu = finite_float(value("plain_unguided_glucose", "final_cpu_time", 0.0))
        neutral_final_cpu = finite_float(value("neutral_weighted_glucose", "final_cpu_time", 0.0))
        static_final_cpu = finite_float(value("static_weighted_glucose", "final_cpu_time", 0.0))
        cached_final_cpu = finite_float(value("cached_trace_no_adapter_final", "final_cpu_time", 0.0))
        adapter_final_cpu = finite_float(value("event_adapter_final", "final_cpu_time", 0.0))
        plain_protocol = finite_float(value("plain_unguided_glucose", "protocol_accounted_time", 0.0))
        neutral_protocol = finite_float(value("neutral_weighted_glucose", "protocol_accounted_time", 0.0))
        static_protocol = finite_float(value("static_weighted_glucose", "protocol_accounted_time", 0.0))
        cached_protocol = finite_float(value("cached_trace_no_adapter_final", "protocol_accounted_time", 0.0))
        adapter_protocol = finite_float(value("event_adapter_final", "protocol_accounted_time", 0.0))
        plain_decisions = finite_float(value("plain_unguided_glucose", "final_decisions", 0.0))
        neutral_decisions = finite_float(value("neutral_weighted_glucose", "final_decisions", 0.0))
        static_decisions = finite_float(value("static_weighted_glucose", "final_decisions", 0.0))
        cached_decisions = finite_float(value("cached_trace_no_adapter_final", "final_decisions", 0.0))
        adapter_decisions = finite_float(value("event_adapter_final", "final_decisions", 0.0))
        plain_conflicts = finite_float(value("plain_unguided_glucose", "final_conflicts", 0.0))
        neutral_conflicts = finite_float(value("neutral_weighted_glucose", "final_conflicts", 0.0))
        static_conflicts = finite_float(value("static_weighted_glucose", "final_conflicts", 0.0))
        cached_conflicts = finite_float(value("cached_trace_no_adapter_final", "final_conflicts", 0.0))
        adapter_conflicts = finite_float(value("event_adapter_final", "final_conflicts", 0.0))
        plain_solved = bool(value("plain_unguided_glucose", "final_solved", False))
        neutral_solved = bool(value("neutral_weighted_glucose", "final_solved", False))
        static_solved = bool(value("static_weighted_glucose", "final_solved", False))
        cached_solved = bool(value("cached_trace_no_adapter_final", "final_solved", False))
        adapter_solved = bool(value("event_adapter_final", "final_solved", False))
        neutral_result = str(value("neutral_weighted_glucose", "final_result", ""))
        static_result = str(value("static_weighted_glucose", "final_result", ""))
        adapter_result = str(value("event_adapter_final", "final_result", ""))
        neutral_lost = plain_solved and not neutral_solved
        static_lost = plain_solved and neutral_solved and not static_solved
        adapter_lost = plain_solved and static_solved and not adapter_solved
        weighted_final_cpu_delta = neutral_final_cpu - plain_final_cpu
        weighted_protocol_delta = neutral_protocol - plain_protocol
        static_final_cpu_delta = static_final_cpu - neutral_final_cpu
        static_protocol_delta = static_protocol - neutral_protocol
        event_final_cpu_delta = cached_final_cpu - static_final_cpu
        event_protocol_delta = cached_protocol - static_protocol
        adapter_final_cpu_delta = adapter_final_cpu - cached_final_cpu
        adapter_protocol_delta = adapter_protocol - cached_protocol
        if neutral_lost:
            primary = "weighted_binary_or_input_path"
        elif static_lost:
            primary = "static_gnn_weights"
        elif adapter_lost:
            primary = "adapter_delta_or_event_guidance"
        elif plain_solved and static_solved and adapter_solved and event_protocol_delta > 1.0e-6:
            primary = "event_collection_overhead_only"
        elif plain_solved:
            primary = "no_guided_loss"
        else:
            primary = "plain_unsolved_or_unknown"

        attribution = {
            **key_dict,
            "plain_solved": plain_solved,
            "neutral_solved": neutral_solved,
            "static_solved": static_solved,
            "cached_trace_solved": cached_solved,
            "adapter_solved": adapter_solved,
            "neutral_degradation": classify_degradation(plain_solved, neutral_solved, neutral_result),
            "static_degradation": classify_degradation(plain_solved, static_solved, static_result),
            "adapter_degradation": classify_degradation(plain_solved, adapter_solved, adapter_result),
            "neutral_lost_from_plain": bool(neutral_lost),
            "static_lost_after_neutral": bool(static_lost),
            "adapter_lost_after_static": bool(adapter_lost),
            "primary_attribution": primary,
            "missing_methods": ",".join(missing_methods),
            "static_minus_neutral_final_cpu": static_final_cpu_delta,
            "cached_minus_static_protocol_time": event_protocol_delta,
            "adapter_minus_cached_protocol_time": adapter_protocol_delta,
            "weighted_binary_input_delta_final_cpu": weighted_final_cpu_delta,
            "weighted_binary_input_delta_protocol_time": weighted_protocol_delta,
            "weighted_binary_input_delta_final_decisions": neutral_decisions - plain_decisions,
            "weighted_binary_input_delta_final_conflicts": neutral_conflicts - plain_conflicts,
            "static_weights_delta_final_cpu": static_final_cpu_delta,
            "static_weights_delta_protocol_time": static_protocol_delta,
            "static_weights_delta_final_decisions": static_decisions - neutral_decisions,
            "static_weights_delta_final_conflicts": static_conflicts - neutral_conflicts,
            "event_collection_overhead_delta_final_cpu": event_final_cpu_delta,
            "event_collection_overhead_delta_protocol_time": event_protocol_delta,
            "event_collection_overhead_delta_final_decisions": cached_decisions - static_decisions,
            "event_collection_overhead_delta_final_conflicts": cached_conflicts - static_conflicts,
            "adapter_delta_inference_delta_final_cpu": adapter_final_cpu_delta,
            "adapter_delta_inference_delta_protocol_time": adapter_protocol_delta,
            "adapter_delta_inference_delta_final_decisions": adapter_decisions - cached_decisions,
            "adapter_delta_inference_delta_final_conflicts": adapter_conflicts - cached_conflicts,
            "adapter_inference_wall_time": finite_float(value("event_adapter_final", "adapter_inference_wall_time", 0.0)),
            "warmup_decisions": finite_float(value("event_adapter_final", "warmup_decisions", 0.0)),
            "warmup_conflicts": finite_float(value("event_adapter_final", "warmup_conflict_count", 0.0)),
            "events_available": bool(value("event_adapter_final", "events_available", False)),
            "event_state_nonzero_vars": int(finite_float(value("event_adapter_final", "event_state_nonzero_vars", 0.0))),
            "event_state_l2_sum": finite_float(value("event_adapter_final", "event_state_l2_sum", 0.0)),
            "event_adapter_graph_gate_open": bool(value("event_adapter_final", "event_adapter_graph_gate_open", False)),
            "event_adapter_graph_gate_evidence": finite_float(value("event_adapter_final", "event_adapter_graph_gate_evidence", 0.0)),
        }
        rows.append(attribution)
        guided_lost = plain_solved and ((not static_solved) or (not adapter_solved))
        if guided_lost:
            loss_rows.append(
                {
                    **attribution,
                    "static_final_lost": bool(not static_solved),
                    "event_final_lost": bool(not adapter_solved),
                    "event_worse_than_static": bool(static_solved and not adapter_solved),
                    "static_final_result": static_result,
                    "event_final_result": adapter_result,
                    "neutral_final_result": neutral_result,
                    "final_loss_mode": (
                        "static_and_event_lost"
                        if (not static_solved and not adapter_solved)
                        else "event_only_lost"
                        if static_solved and not adapter_solved
                        else "static_only_lost"
                    ),
                }
            )

    attribution_frame = pd.DataFrame(rows)
    loss_frame = pd.DataFrame(loss_rows, columns=loss_columns)
    if not attribution_frame.empty:
        attribution_frame = attribution_frame.sort_values(keys).reset_index(drop=True)
    if not loss_frame.empty:
        loss_frame = loss_frame.sort_values(keys).reset_index(drop=True)
    return attribution_frame, loss_frame


def summarize_attribution_by_base(attribution: pd.DataFrame) -> pd.DataFrame:
    if attribution.empty:
        return pd.DataFrame()
    def repeat_consistency(values: pd.Series) -> float:
        frame = attribution.loc[values.index, ["repeat_id"]].copy()
        frame["value"] = values.astype(str).to_numpy()
        checks = frame.groupby("repeat_id", sort=True)["value"].nunique() <= 1
        return float(checks.mean()) if len(checks) else float("nan")

    aggregation: dict[str, tuple[str, Any]] = {
        "repeats": ("repeat_id", "nunique"),
        "variants": ("variant", "nunique"),
        "rows": ("instance_id", "count"),
        "plain_solved_rows": ("plain_solved", lambda values: int(pd.Series(values).astype(bool).sum())),
        "neutral_lost_rows": ("neutral_lost_from_plain", lambda values: int(pd.Series(values).astype(bool).sum())),
        "static_lost_rows": ("static_lost_after_neutral", lambda values: int(pd.Series(values).astype(bool).sum())),
        "adapter_lost_rows": ("adapter_lost_after_static", lambda values: int(pd.Series(values).astype(bool).sum())),
        "weighted_binary_input_delta_final_cpu_mean": ("weighted_binary_input_delta_final_cpu", "mean"),
        "weighted_binary_input_delta_protocol_time_mean": ("weighted_binary_input_delta_protocol_time", "mean"),
        "static_weights_delta_final_cpu_mean": ("static_weights_delta_final_cpu", "mean"),
        "static_weights_delta_protocol_time_mean": ("static_weights_delta_protocol_time", "mean"),
        "event_collection_overhead_delta_final_cpu_mean": ("event_collection_overhead_delta_final_cpu", "mean"),
        "event_collection_overhead_delta_protocol_time_mean": ("event_collection_overhead_delta_protocol_time", "mean"),
        "adapter_delta_inference_delta_final_cpu_mean": ("adapter_delta_inference_delta_final_cpu", "mean"),
        "adapter_delta_inference_delta_protocol_time_mean": ("adapter_delta_inference_delta_protocol_time", "mean"),
        "adapter_inference_wall_time_mean": ("adapter_inference_wall_time", "mean"),
        "event_overhead_mean": ("cached_minus_static_protocol_time", "mean"),
        "adapter_delta_overhead_mean": ("adapter_minus_cached_protocol_time", "mean"),
        "warmup_decisions_mean": ("warmup_decisions", "mean"),
        "warmup_conflicts_mean": ("warmup_conflicts", "mean"),
        "event_state_nonzero_vars_mean": ("event_state_nonzero_vars", "mean"),
        "graph_gate_open_rows": ("event_adapter_graph_gate_open", lambda values: int(pd.Series(values).astype(bool).sum())),
        "primary_attribution_modes": ("primary_attribution", lambda values: ",".join(sorted(set(map(str, values))))),
        "primary_attribution_variant_consistency": ("primary_attribution", repeat_consistency),
        "plain_solved_variant_consistency": ("plain_solved", repeat_consistency),
        "neutral_solved_variant_consistency": ("neutral_solved", repeat_consistency),
        "static_solved_variant_consistency": ("static_solved", repeat_consistency),
        "adapter_solved_variant_consistency": ("adapter_solved", repeat_consistency),
    }
    for column in STRATIFICATION_COLUMNS:
        if column in attribution.columns:
            aggregation[column] = (column, lambda values: ",".join(sorted(set(map(str, values)))))
    out = (
        attribution.groupby(["family", "base_instance_id"], sort=True)
        .agg(**aggregation)
        .reset_index()
    )
    return out


def summarize_timeout_correctness(per_instance: pd.DataFrame) -> pd.DataFrame:
    if per_instance.empty:
        return pd.DataFrame()
    group_columns = [
        column
        for column in ["method", "family", "control_type", "scale", "benchmark_role", "solver_path_role"]
        if column in per_instance.columns
    ]
    frame = per_instance.copy()
    frame["final_indeterminate"] = frame["final_result"].astype(str) == "INDETERMINATE"
    frame["final_wrong_known"] = frame["known_expected_result"].astype(bool) & ~frame["final_known_expected_match"].astype(bool)
    frame["final_timeout_or_indeterminate"] = ~frame["final_solved"].astype(bool)
    frame["unknown_expected_result"] = ~frame["known_expected_result"].astype(bool)
    out = (
        frame.groupby(group_columns, sort=True)
        .agg(
            rows=("instance_id", "count"),
            base_instances=("base_instance_id", "nunique"),
            solved_rows=("final_solved", lambda values: int(pd.Series(values).astype(bool).sum())),
            unsolved_rows=("final_timeout_or_indeterminate", lambda values: int(pd.Series(values).astype(bool).sum())),
            indeterminate_rows=("final_indeterminate", lambda values: int(pd.Series(values).astype(bool).sum())),
            known_expected_rows=("known_expected_result", lambda values: int(pd.Series(values).astype(bool).sum())),
            unknown_expected_rows=("unknown_expected_result", lambda values: int(pd.Series(values).astype(bool).sum())),
            known_expected_match_rows=("final_known_expected_match", lambda values: int(pd.Series(values).astype(bool).sum())),
            known_expected_wrong_rows=("final_wrong_known", lambda values: int(pd.Series(values).astype(bool).sum())),
            mean_final_cpu_time=("final_cpu_time", "mean"),
            median_final_cpu_time=("final_cpu_time", "median"),
            mean_protocol_accounted_time=("protocol_accounted_time", "mean"),
            median_protocol_accounted_time=("protocol_accounted_time", "median"),
        )
        .reset_index()
    )
    overall_group_columns = [column for column in ["method", "solver_path_role"] if column in per_instance.columns]
    overall = (
        frame.groupby(overall_group_columns, sort=True)
        .agg(
            rows=("instance_id", "count"),
            base_instances=("base_instance_id", "nunique"),
            solved_rows=("final_solved", lambda values: int(pd.Series(values).astype(bool).sum())),
            unsolved_rows=("final_timeout_or_indeterminate", lambda values: int(pd.Series(values).astype(bool).sum())),
            indeterminate_rows=("final_indeterminate", lambda values: int(pd.Series(values).astype(bool).sum())),
            known_expected_rows=("known_expected_result", lambda values: int(pd.Series(values).astype(bool).sum())),
            unknown_expected_rows=("unknown_expected_result", lambda values: int(pd.Series(values).astype(bool).sum())),
            known_expected_match_rows=("final_known_expected_match", lambda values: int(pd.Series(values).astype(bool).sum())),
            known_expected_wrong_rows=("final_wrong_known", lambda values: int(pd.Series(values).astype(bool).sum())),
            mean_final_cpu_time=("final_cpu_time", "mean"),
            median_final_cpu_time=("final_cpu_time", "median"),
            mean_protocol_accounted_time=("protocol_accounted_time", "mean"),
            median_protocol_accounted_time=("protocol_accounted_time", "median"),
        )
        .reset_index()
    )
    for column in ["family", "control_type", "scale", "benchmark_role"]:
        if column in out.columns and column not in overall.columns:
            overall[column] = "__overall__"
    if "solver_path_role" in out.columns and "solver_path_role" not in overall.columns and "solver_path_role" in frame.columns:
        overall["solver_path_role"] = str(frame["solver_path_role"].iloc[0])
    columns = list(out.columns)
    overall = overall[[column for column in columns if column in overall.columns]]
    return pd.concat([out, overall], ignore_index=True)


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> list[str]:
    if frame.empty:
        return ["_None._"]
    view = frame.copy()
    if max_rows is not None:
        view = view.head(int(max_rows))
    columns = list(view.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in view.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_doc(
    path: Path,
    per_instance: pd.DataFrame,
    by_family: pd.DataFrame,
    by_base_instance: pd.DataFrame,
    attribution: pd.DataFrame,
    loss_diagnostics: pd.DataFrame,
    checkpoint: Path,
    manifest: Path,
    per_instance_csv: Path,
    phases_csv: Path,
    by_family_csv: Path,
    by_base_instance_csv: Path,
    attribution_csv: Path,
    attribution_by_base_csv: Path,
    loss_diagnostics_csv: Path,
    timeout_correctness_csv: Path,
    final_cpu_lim: float,
    warmup_cpu_lim: float,
    warmup_conflicts: int,
    trace_lbd: int,
    include_static_only: bool,
    repeats: int,
    solver_seed: int,
    warmup_seed: int,
    final_seed: int,
    neutral_weight: float,
    neutral_phase: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    overall = by_family[by_family["family"].astype(str) == "__overall__"].copy()
    coverage_columns = [
        column
        for column in [
            "family",
            "instance_id",
            "base_instance_id",
            "variant",
            "control_type",
            "scale",
            "benchmark_role",
            "symmetry_strength",
        ]
        if column in per_instance.columns
    ]
    coverage_agg: dict[str, tuple[str, Any]] = {
        "instances": ("instance_id", "count"),
        "base_instances": ("base_instance_id", "nunique"),
    }
    for source_column, output_column in [
        ("control_type", "control_types"),
        ("scale", "scales"),
        ("benchmark_role", "benchmark_roles"),
        ("symmetry_strength", "symmetry_strengths"),
    ]:
        if source_column in per_instance.columns:
            coverage_agg[output_column] = (
                source_column,
                lambda values: ",".join(sorted(set(map(str, values)))),
            )
    coverage = (
        per_instance[coverage_columns]
        .drop_duplicates()
        .groupby("family", sort=True)
        .agg(**coverage_agg)
        .reset_index()
    )
    event_methods = per_instance[per_instance["uses_warmup_events"].astype(bool)]
    event_overall = pd.DataFrame(
        [
            {
                "event_method_rows": int(len(event_methods)),
                "events_available_rows": int(event_methods["events_available"].astype(bool).sum()) if not event_methods.empty else 0,
                "protocol_supported_rows": int(event_methods["protocol_supported"].astype(bool).sum()) if not event_methods.empty else 0,
                "mean_warmup_cpu_time": float(event_methods["warmup_cpu_time"].mean()) if not event_methods.empty else float("nan"),
                "mean_event_attach_wall_time": float(event_methods["event_attach_wall_time"].mean()) if not event_methods.empty else float("nan"),
                "mean_adapter_inference_wall_time": float(event_methods["adapter_inference_wall_time"].mean()) if not event_methods.empty else float("nan"),
            }
        ]
    )
    method_view = overall[
        [
            "method",
            "rows",
            "solved_instances",
            "known_expected_instances",
            "known_expected_match_instances",
            "protocol_supported_instances",
            "events_available_instances",
            "mean_protocol_accounted_time",
            "median_protocol_accounted_time",
            "mean_final_cpu_time",
            "mean_warmup_cpu_time",
            "mean_adapter_inference_wall_time",
        ]
    ].copy()
    base_attr_view = summarize_attribution_by_base(attribution)
    attr_matrix_columns = [
        column
        for column in [
            "weighted_binary_input_delta_final_cpu",
            "weighted_binary_input_delta_protocol_time",
            "static_weights_delta_final_cpu",
            "static_weights_delta_protocol_time",
            "event_collection_overhead_delta_final_cpu",
            "event_collection_overhead_delta_protocol_time",
            "adapter_delta_inference_delta_final_cpu",
            "adapter_delta_inference_delta_protocol_time",
            "adapter_inference_wall_time",
        ]
        if column in attribution.columns
    ]
    attr_matrix_overall = (
        attribution[attr_matrix_columns].mean().reset_index(name="mean_delta").rename(columns={"index": "attribution_delta"})
        if attr_matrix_columns and not attribution.empty
        else pd.DataFrame()
    )
    attr_matrix_by_control = (
        attribution.groupby([column for column in ["control_type", "scale"] if column in attribution.columns], sort=True)[attr_matrix_columns]
        .mean()
        .reset_index()
        if attr_matrix_columns and not attribution.empty and any(column in attribution.columns for column in ["control_type", "scale"])
        else pd.DataFrame()
    )
    attr_overall = (
        attribution.groupby("primary_attribution", sort=True)
        .agg(
            rows=("instance_id", "count"),
            base_instances=("base_instance_id", "nunique"),
            variants=("variant", "nunique"),
        )
        .reset_index()
        if not attribution.empty
        else pd.DataFrame()
    )
    loss_view = loss_diagnostics[
        [
            column
            for column in [
                "family",
                "base_instance_id",
                "variant",
                "repeat_id",
                "primary_attribution",
                "final_loss_mode",
                "neutral_final_result",
                "static_final_result",
                "event_final_result",
                "warmup_decisions",
                "warmup_conflicts",
                "event_state_nonzero_vars",
                "event_adapter_graph_gate_open",
            ]
            if column in loss_diagnostics.columns
        ]
    ].copy() if not loss_diagnostics.empty else pd.DataFrame()
    family_view = by_family[
        by_family["family"].astype(str) != "__overall__"
    ][
        [
            "family",
            "method",
            "rows",
            "solved_instances",
            "mean_protocol_accounted_time",
            "mean_final_cpu_time",
            "mean_warmup_cpu_time",
            "events_available_instances",
        ]
    ].copy()
    lines = [
        "# SAT Symmetry Solver Protocol Preflight",
        "",
        "This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.",
        "It is not a solver speedup claim. The purpose is to verify that the solver-level",
        "pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,",
        "adapter inference, and the final solve.",
        "",
        "## Inputs",
        "",
        f"- checkpoint: `{checkpoint}`",
        f"- manifest: `{manifest}`",
        f"- event-role rows: `{int(per_instance['instance_id'].nunique())}` distinct CNFs",
        f"- repeats: `{int(repeats)}`",
        f"- solver seed base: `{int(solver_seed)}`",
        f"- warmup seed base: `{int(warmup_seed)}`",
        f"- final seed base: `{int(final_seed)}`",
        f"- static-only rows included: `{bool(include_static_only)}`",
        f"- final CPU limit: `{final_cpu_lim}` seconds",
        f"- warmup CPU limit: `{warmup_cpu_lim}` seconds",
        f"- warmup conflict limit: `{warmup_conflicts}`",
        f"- trace LBD threshold: `{trace_lbd}`",
        f"- variants included: `{','.join(sorted(set(map(str, per_instance['variant'])))) if 'variant' in per_instance.columns and not per_instance.empty else 'unknown'}`",
        f"- permutation variants included: `{bool(per_instance['permutation_variant'].astype(bool).any()) if 'permutation_variant' in per_instance.columns and not per_instance.empty else False}`",
        f"- neutral weighted baseline: phase `{neutral_phase}`, weight `{neutral_weight}`",
        f"- weighted solver no-pre: `{bool(per_instance['weighted_no_pre'].any()) if 'weighted_no_pre' in per_instance.columns else False}`",
        f"- solver path role: `{str(per_instance['solver_path_role'].iloc[0]) if 'solver_path_role' in per_instance.columns and not per_instance.empty else 'unknown'}`",
        "",
        "## Method Semantics",
        "",
        "- `plain_unguided_glucose`: plain Glucose final solve, no weighted input path and no model inference.",
        "- `neutral_weighted_glucose`: weighted Glucose binary with all variables assigned the same phase/weight.",
        "- `static_weighted_glucose`: W0.5 checkpoint static/base guidance, then weighted Glucose final solve.",
        "- `cached_trace_no_adapter_final`: pays static inference, event-collecting warmup, and event attach; the final solve reuses the static guidance and does not run adapter inference.",
        "- `event_adapter_final`: pays static inference, event-collecting warmup, event attach, adapter inference, and weighted Glucose final solve.",
        "",
        "`neutral_weighted_glucose` is not bit-identical to plain Glucose. It isolates the",
        "weighted binary / weighted input parsing path from the learned static and event weights.",
        "",
        "`cached_trace_no_adapter_final` is the required ablation for separating event collection cost",
        "from the adapter's effect on final variable weights.",
        "",
        "`patched_pretrue_main` is the main patched weighted Glucose path. "
        "`weighted_no_pre_diagnostic` is only a diagnostic path for isolating preprocessing effects; "
        "do not merge it with the main runtime protocol.",
        "",
        "Permutation variants are not treated as independent evidence in the attribution tables;",
        "those summaries are grouped by `base_instance_id`.",
        "",
        "## Artifacts",
        "",
        f"- per-instance CSV: `{per_instance_csv}`",
        f"- phase accounting CSV: `{phases_csv}`",
        f"- family summary CSV: `{by_family_csv}`",
        f"- base-instance paired summary CSV: `{by_base_instance_csv}`",
        f"- attribution CSV: `{attribution_csv}`",
        f"- base-instance attribution CSV: `{attribution_by_base_csv}`",
        f"- guided-loss diagnostics CSV: `{loss_diagnostics_csv}`",
        f"- timeout/correctness CSV: `{timeout_correctness_csv}`",
        "",
        "## Coverage",
        "",
        *markdown_table(coverage),
        "",
        "## Overall Method Accounting",
        "",
        "`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;",
        "`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.",
        "",
        *markdown_table(method_view),
        "",
        "## Event Accounting",
        "",
        *markdown_table(event_overall),
        "",
        "## Attribution Modes",
        "",
        *markdown_table(attr_overall),
        "",
        "## Fixed Attribution Matrix",
        "",
        "The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:",
        "",
        "- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`",
        "- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`",
        "- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`",
        "- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`",
        "",
        *markdown_table(attr_matrix_overall),
        "",
        "## Attribution Matrix By Stratum",
        "",
        *markdown_table(attr_matrix_by_control, max_rows=80),
        "",
        "## Base-Instance Attribution",
        "",
        *markdown_table(
            base_attr_view[
                [
                    column
                    for column in [
                        "family",
                        "base_instance_id",
                        "repeats",
                        "variants",
                        "plain_solved_rows",
                        "neutral_lost_rows",
                        "static_lost_rows",
                        "adapter_lost_rows",
                        "weighted_binary_input_delta_protocol_time_mean",
                        "static_weights_delta_protocol_time_mean",
                        "event_collection_overhead_delta_protocol_time_mean",
                        "adapter_delta_inference_delta_protocol_time_mean",
                        "warmup_decisions_mean",
                        "warmup_conflicts_mean",
                        "graph_gate_open_rows",
                        "primary_attribution_modes",
                    ]
                    if column in base_attr_view.columns
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Guided Loss Diagnostics",
        "",
        *markdown_table(loss_view, max_rows=80),
        "",
        "## Family Breakdown",
        "",
        *markdown_table(family_view, max_rows=80),
        "",
        "## Interpretation",
        "",
        "This run is a repeated paired runtime preflight and attribution ledger, not a",
        "solver speedup claim. If the Glucose seed has no measurable effect on these",
        "instances, interpret repeats as runtime stability rather than seed stability.",
        "Any later runtime comparison should keep the neutral weighted baseline and the",
        "cached-trace no-adapter ablation so the weighted path, static weights, event",
        "collection overhead, and adapter delta remain separable.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SAT symmetry solver protocol preflight with full overhead accounting.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--per-instance-csv", type=Path, default=DEFAULT_PER_INSTANCE)
    parser.add_argument("--phases-csv", type=Path, default=DEFAULT_PHASES)
    parser.add_argument("--by-family-csv", type=Path, default=DEFAULT_BY_FAMILY)
    parser.add_argument("--by-base-instance-csv", type=Path, default=DEFAULT_BY_BASE_INSTANCE)
    parser.add_argument("--attribution-csv", type=Path, default=DEFAULT_ATTRIBUTION)
    parser.add_argument("--attribution-by-base-csv", type=Path, default=DEFAULT_ATTRIBUTION_BY_BASE)
    parser.add_argument("--loss-diagnostics-csv", type=Path, default=DEFAULT_LOSS_DIAGNOSTICS)
    parser.add_argument("--timeout-correctness-csv", type=Path, default=DEFAULT_TIMEOUT_CORRECTNESS)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--control-types", nargs="*", default=None)
    parser.add_argument("--scales", nargs="*", default=None)
    parser.add_argument("--benchmark-roles", nargs="*", default=None)
    parser.add_argument("--include-static-only", action="store_true")
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--solver", default="glucose")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--solver-seed", type=int, default=None)
    parser.add_argument("--warmup-seed", type=int, default=None)
    parser.add_argument("--final-seed", type=int, default=None)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--neutral-weight", type=float, default=1.0)
    parser.add_argument("--neutral-phase", type=float, default=0.0)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--loader-workers", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--event-state-features", default="enhanced", choices=["legacy", "enhanced", "polarity"])
    parser.add_argument("--final-cpu-lim", type=float, default=5.0)
    parser.add_argument("--warmup-cpu-lim", type=float, default=5.0)
    parser.add_argument("--warmup-conflicts", type=int, default=20)
    parser.add_argument("--trace-lbd", type=int, default=2)
    parser.add_argument("--rnd-freq", type=float, default=0.0)
    parser.add_argument("--K", type=float, default=0.1)
    parser.add_argument(
        "--weighted-no-pre",
        action="store_true",
        help="Pass -no-pre only to guided/weighted Glucose calls; plain unguided remains unchanged.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    checkpoint = resolve_path(args.checkpoint).resolve()
    manifest_path = resolve_path(args.manifest).resolve()
    per_instance_csv = resolve_path(args.per_instance_csv)
    phases_csv = resolve_path(args.phases_csv)
    by_family_csv = resolve_path(args.by_family_csv)
    by_base_instance_csv = resolve_path(args.by_base_instance_csv)
    attribution_csv = resolve_path(args.attribution_csv)
    attribution_by_base_csv = resolve_path(args.attribution_by_base_csv)
    loss_diagnostics_csv = resolve_path(args.loss_diagnostics_csv)
    timeout_correctness_csv = resolve_path(args.timeout_correctness_csv)
    doc_path = resolve_path(args.doc)
    repeats = max(1, int(args.repeats))
    solver_seed_base = int(args.seed if args.solver_seed is None else args.solver_seed)
    warmup_seed_base = int(solver_seed_base if args.warmup_seed is None else args.warmup_seed)
    final_seed_base = int(solver_seed_base if args.final_seed is None else args.final_seed)

    device = args.device
    if device == "auto":
        device = "cuda:0" if torch.cuda.is_available() else "cpu"

    print(f"loading checkpoint: {checkpoint}")
    model, transform, model_cfg = load_checkpoint(str(checkpoint), var_output=True)
    model.to(device)
    model.eval()
    expected_dim = event_state_dim(args.event_state_features)
    model_var_state_dim = int(getattr(model, "var_state_dim", 0))
    if model_var_state_dim != expected_dim:
        raise ValueError(
            f"event_state_features={args.event_state_features} has dim {expected_dim}, "
            f"but checkpoint model.var_state_dim={model_var_state_dim}"
        )

    manifest = load_manifest(
        manifest_path,
        families=args.families,
        control_types=args.control_types,
        scales=args.scales,
        benchmark_roles=args.benchmark_roles,
        include_static_only=bool(args.include_static_only),
        base_only=bool(args.base_only),
    )
    dataset = make_dimacs_dataset(manifest["cnf_path"].astype(str).tolist(), transform=transform)
    lookup = manifest_lookup_by_file(dataset, manifest)
    loader = DataLoader(
        dataset=dataset,
        batch_size=int(args.batch_size),
        num_workers=int(args.loader_workers),
        shuffle=False,
    )
    print(f"loaded {len(dataset)} CNFs for protocol preflight")

    final_params = clean_solver_params(
        {
            "cpu-lim": solver_cli_number(args.final_cpu_lim),
            "rnd-freq": args.rnd_freq,
            "K": args.K,
        }
    )
    weighted_final_params = with_optional_no_pre(final_params, bool(args.weighted_no_pre))
    warmup_base_params = clean_solver_params(
        {
            "rnd-freq": args.rnd_freq,
            "K": args.K,
        }
    )
    warmup_params = apply_rollout_budget(
        warmup_base_params,
        budget_type="conflicts",
        cpu_lim=solver_cli_number(args.warmup_cpu_lim),
        conflicts=int(args.warmup_conflicts),
    )
    warmup_params["collect-events"] = True
    warmup_params["trace-lbd"] = int(args.trace_lbd)
    weighted_warmup_params = with_optional_no_pre(warmup_params, bool(args.weighted_no_pre))

    rows: list[dict[str, Any]] = []
    phases: list[dict[str, Any]] = []
    scale_sigma = finite_float(model_cfg.get("scale_sigma", 0.1), default=0.1)
    graph_gate_indices = list(getattr(model, "event_adapter_graph_gate_indices", []) or [])
    graph_gate_threshold = getattr(model, "event_adapter_graph_gate_threshold", None)

    for repeat_id in range(repeats):
        solver_seed = solver_seed_base + repeat_id
        warmup_seed = warmup_seed_base + repeat_id
        final_seed = final_seed_base + repeat_id
        print(
            f"repeat {repeat_id + 1}/{repeats}: "
            f"solver_seed={solver_seed} warmup_seed={warmup_seed} final_seed={final_seed}"
        )

        static_start = time.perf_counter()
        static_graphs = sample_var_params(
            model=model,
            loader=loader,
            num_samples=1,
            device=device,
            use_mode=True,
            scale_sigma=scale_sigma,
            add_timing=True,
            cache_var_features=True,
        )
        static_total_wall = time.perf_counter() - static_start
        if len(static_graphs) != len(dataset):
            raise RuntimeError(f"Expected {len(dataset)} static graphs, got {len(static_graphs)}")
        static_inference = graph_time_map(static_graphs, "gpu_time")
        if not any(value > 0.0 for value in static_inference.values()) and static_graphs:
            per_graph = static_total_wall / float(len(static_graphs))
            static_inference = {cnf_id_value(graph): per_graph for graph in static_graphs}
        print(f"static inference complete: {len(static_graphs)} graphs in {static_total_wall:.4f}s wall")

        neutral_graphs = neutral_weighted_graphs(
            static_graphs,
            weight=float(args.neutral_weight),
            phase=float(args.neutral_phase),
        )

        plain_final = run_solver_batch(
            dataset=dataset,
            graphs=static_graphs,
            guided=False,
            solver=args.solver,
            seed=final_seed,
            solver_params=final_params,
            num_workers=int(args.num_workers),
            phase_name="plain_unguided_glucose",
            repeat_id=repeat_id,
        )
        neutral_final = run_solver_batch(
            dataset=dataset,
            graphs=neutral_graphs,
            guided=True,
            solver=args.solver,
            seed=final_seed,
            solver_params=weighted_final_params,
            num_workers=int(args.num_workers),
            phase_name="neutral_weighted_glucose",
            repeat_id=repeat_id,
        )
        static_final = run_solver_batch(
            dataset=dataset,
            graphs=static_graphs,
            guided=True,
            solver=args.solver,
            seed=final_seed,
            solver_params=weighted_final_params,
            num_workers=int(args.num_workers),
            phase_name="static_weighted_glucose",
            repeat_id=repeat_id,
        )
        warmup_stats = run_solver_batch(
            dataset=dataset,
            graphs=static_graphs,
            guided=True,
            solver=args.solver,
            seed=warmup_seed,
            solver_params=weighted_warmup_params,
            num_workers=int(args.num_workers),
            phase_name="event_warmup_collect_events",
            repeat_id=repeat_id,
        )
        refined_graphs, attach_info = attach_event_state_per_graph(
            static_graphs,
            warmup_stats=warmup_stats,
            var_state_dim=expected_dim,
            feature_mode=args.event_state_features,
            graph_gate_indices=graph_gate_indices,
            graph_gate_threshold=graph_gate_threshold,
        )
        adapter_loader = DataLoader(
            dataset=refined_graphs,
            batch_size=int(args.batch_size),
            num_workers=int(args.loader_workers),
            shuffle=False,
        )
        adapter_start = time.perf_counter()
        adapter_graphs = sample_var_params(
            model=model,
            loader=adapter_loader,
            num_samples=1,
            device=device,
            use_mode=True,
            scale_sigma=scale_sigma,
            add_timing=True,
            cache_var_features=False,
        )
        adapter_total_wall = time.perf_counter() - adapter_start
        adapter_inference = graph_time_map(adapter_graphs, "gpu_time")
        if not any(value > 0.0 for value in adapter_inference.values()) and adapter_graphs:
            per_graph = adapter_total_wall / float(len(adapter_graphs))
            adapter_inference = {cnf_id_value(graph): per_graph for graph in adapter_graphs}
        print(f"adapter inference complete: {len(adapter_graphs)} graphs in {adapter_total_wall:.4f}s wall")

        adapter_final = run_solver_batch(
            dataset=dataset,
            graphs=adapter_graphs,
            guided=True,
            solver=args.solver,
            seed=final_seed,
            solver_params=weighted_final_params,
            num_workers=int(args.num_workers),
            phase_name="event_adapter_final",
            repeat_id=repeat_id,
        )

        plain_by_cnf = stats_by_cnf(plain_final)
        neutral_by_cnf = stats_by_cnf(neutral_final)
        static_by_cnf = stats_by_cnf(static_final)
        warmup_by_cnf = stats_by_cnf(warmup_stats)
        adapter_by_cnf = stats_by_cnf(adapter_final)
        adapter_graph_by_cnf = {cnf_id_value(graph): graph for graph in adapter_graphs}

        for graph in static_graphs:
            cnf_id = cnf_id_value(graph)
            instance = lookup[cnf_id]
            static_wall = static_inference.get(cnf_id, 0.0)
            warm_row = warmup_by_cnf.get(cnf_id)
            warm_wall = finite_float(warm_row.get("solver_wall_time") if warm_row is not None else 0.0)
            event_info = attach_info.get(cnf_id, {})
            adapter_graph = adapter_graph_by_cnf.get(cnf_id, graph)
            adapter_wall = adapter_inference.get(cnf_id_value(adapter_graph), 0.0)
            method_rows = [
                build_method_row(
                    method="plain_unguided_glucose",
                    graph=graph,
                    instance=instance,
                    final_stats=plain_by_cnf.get(cnf_id),
                    repeat_id=repeat_id,
                    solver_seed=solver_seed,
                    final_seed=final_seed,
                    warmup_seed=warmup_seed,
                    static_inference_wall_time=0.0,
                    warmup_stats=None,
                    warmup_wall_time=0.0,
                    event_attach_info=None,
                    adapter_inference_wall_time=0.0,
                    uses_static_guidance=False,
                    uses_warmup_events=False,
                    uses_adapter=False,
                    cached_trace_ablation=False,
                    final_reused_from="",
                    checkpoint=checkpoint,
                    solver=args.solver,
                    final_cpu_lim=float(args.final_cpu_lim),
                    warmup_cpu_lim=float(args.warmup_cpu_lim),
                    warmup_conflicts=int(args.warmup_conflicts),
                    event_state_features=args.event_state_features,
                    weighted_no_pre=bool(args.weighted_no_pre),
                ),
                build_method_row(
                    method="neutral_weighted_glucose",
                    graph=graph,
                    instance=instance,
                    final_stats=neutral_by_cnf.get(cnf_id),
                    repeat_id=repeat_id,
                    solver_seed=solver_seed,
                    final_seed=final_seed,
                    warmup_seed=warmup_seed,
                    static_inference_wall_time=0.0,
                    warmup_stats=None,
                    warmup_wall_time=0.0,
                    event_attach_info=None,
                    adapter_inference_wall_time=0.0,
                    uses_static_guidance=False,
                    uses_warmup_events=False,
                    uses_adapter=False,
                    cached_trace_ablation=False,
                    final_reused_from="",
                    checkpoint=checkpoint,
                    solver=args.solver,
                    final_cpu_lim=float(args.final_cpu_lim),
                    warmup_cpu_lim=float(args.warmup_cpu_lim),
                    warmup_conflicts=int(args.warmup_conflicts),
                    event_state_features=args.event_state_features,
                    weighted_no_pre=bool(args.weighted_no_pre),
                ),
                build_method_row(
                    method="static_weighted_glucose",
                    graph=graph,
                    instance=instance,
                    final_stats=static_by_cnf.get(cnf_id),
                    repeat_id=repeat_id,
                    solver_seed=solver_seed,
                    final_seed=final_seed,
                    warmup_seed=warmup_seed,
                    static_inference_wall_time=static_wall,
                    warmup_stats=None,
                    warmup_wall_time=0.0,
                    event_attach_info=None,
                    adapter_inference_wall_time=0.0,
                    uses_static_guidance=True,
                    uses_warmup_events=False,
                    uses_adapter=False,
                    cached_trace_ablation=False,
                    final_reused_from="",
                    checkpoint=checkpoint,
                    solver=args.solver,
                    final_cpu_lim=float(args.final_cpu_lim),
                    warmup_cpu_lim=float(args.warmup_cpu_lim),
                    warmup_conflicts=int(args.warmup_conflicts),
                    event_state_features=args.event_state_features,
                    weighted_no_pre=bool(args.weighted_no_pre),
                ),
                build_method_row(
                    method="cached_trace_no_adapter_final",
                    graph=graph,
                    instance=instance,
                    final_stats=static_by_cnf.get(cnf_id),
                    repeat_id=repeat_id,
                    solver_seed=solver_seed,
                    final_seed=final_seed,
                    warmup_seed=warmup_seed,
                    static_inference_wall_time=static_wall,
                    warmup_stats=warm_row,
                    warmup_wall_time=warm_wall,
                    event_attach_info=event_info,
                    adapter_inference_wall_time=0.0,
                    uses_static_guidance=True,
                    uses_warmup_events=True,
                    uses_adapter=False,
                    cached_trace_ablation=True,
                    final_reused_from="static_weighted_glucose",
                    checkpoint=checkpoint,
                    solver=args.solver,
                    final_cpu_lim=float(args.final_cpu_lim),
                    warmup_cpu_lim=float(args.warmup_cpu_lim),
                    warmup_conflicts=int(args.warmup_conflicts),
                    event_state_features=args.event_state_features,
                    weighted_no_pre=bool(args.weighted_no_pre),
                ),
                build_method_row(
                    method="event_adapter_final",
                    graph=graph,
                    instance=instance,
                    final_stats=adapter_by_cnf.get(cnf_id),
                    repeat_id=repeat_id,
                    solver_seed=solver_seed,
                    final_seed=final_seed,
                    warmup_seed=warmup_seed,
                    static_inference_wall_time=static_wall,
                    warmup_stats=warm_row,
                    warmup_wall_time=warm_wall,
                    event_attach_info=event_info,
                    adapter_inference_wall_time=adapter_wall,
                    uses_static_guidance=True,
                    uses_warmup_events=True,
                    uses_adapter=True,
                    cached_trace_ablation=False,
                    final_reused_from="",
                    checkpoint=checkpoint,
                    solver=args.solver,
                    final_cpu_lim=float(args.final_cpu_lim),
                    warmup_cpu_lim=float(args.warmup_cpu_lim),
                    warmup_conflicts=int(args.warmup_conflicts),
                    event_state_features=args.event_state_features,
                    weighted_no_pre=bool(args.weighted_no_pre),
                ),
            ]
            rows.extend(method_rows)
            for method_row in method_rows:
                phases.extend(phase_rows_for_method(method_row))

    per_instance = pd.DataFrame.from_records(rows)
    phase_frame = pd.DataFrame.from_records(phases)
    by_family = summarize_by_family(per_instance)
    by_base_instance = summarize_by_base_instance(per_instance)
    attribution, loss_diagnostics = build_attribution(per_instance)
    attribution_by_base = summarize_attribution_by_base(attribution)
    timeout_correctness = summarize_timeout_correctness(per_instance)

    per_instance_csv.parent.mkdir(parents=True, exist_ok=True)
    phases_csv.parent.mkdir(parents=True, exist_ok=True)
    by_family_csv.parent.mkdir(parents=True, exist_ok=True)
    by_base_instance_csv.parent.mkdir(parents=True, exist_ok=True)
    attribution_csv.parent.mkdir(parents=True, exist_ok=True)
    attribution_by_base_csv.parent.mkdir(parents=True, exist_ok=True)
    loss_diagnostics_csv.parent.mkdir(parents=True, exist_ok=True)
    timeout_correctness_csv.parent.mkdir(parents=True, exist_ok=True)
    per_instance.to_csv(per_instance_csv, index=False)
    phase_frame.to_csv(phases_csv, index=False)
    by_family.to_csv(by_family_csv, index=False)
    by_base_instance.to_csv(by_base_instance_csv, index=False)
    attribution.to_csv(attribution_csv, index=False)
    attribution_by_base.to_csv(attribution_by_base_csv, index=False)
    loss_diagnostics.to_csv(loss_diagnostics_csv, index=False)
    timeout_correctness.to_csv(timeout_correctness_csv, index=False)
    write_doc(
        doc_path,
        per_instance=per_instance,
        by_family=by_family,
        by_base_instance=by_base_instance,
        attribution=attribution,
        loss_diagnostics=loss_diagnostics,
        checkpoint=checkpoint,
        manifest=manifest_path,
        per_instance_csv=per_instance_csv,
        phases_csv=phases_csv,
        by_family_csv=by_family_csv,
        by_base_instance_csv=by_base_instance_csv,
        attribution_csv=attribution_csv,
        attribution_by_base_csv=attribution_by_base_csv,
        loss_diagnostics_csv=loss_diagnostics_csv,
        timeout_correctness_csv=timeout_correctness_csv,
        final_cpu_lim=float(args.final_cpu_lim),
        warmup_cpu_lim=float(args.warmup_cpu_lim),
        warmup_conflicts=int(args.warmup_conflicts),
        trace_lbd=int(args.trace_lbd),
        include_static_only=bool(args.include_static_only),
        repeats=repeats,
        solver_seed=solver_seed_base,
        warmup_seed=warmup_seed_base,
        final_seed=final_seed_base,
        neutral_weight=float(args.neutral_weight),
        neutral_phase=float(args.neutral_phase),
    )
    print(f"wrote {per_instance_csv}")
    print(f"wrote {phases_csv}")
    print(f"wrote {by_family_csv}")
    print(f"wrote {by_base_instance_csv}")
    print(f"wrote {attribution_csv}")
    print(f"wrote {attribution_by_base_csv}")
    print(f"wrote {loss_diagnostics_csv}")
    print(f"wrote {timeout_correctness_csv}")
    print(f"wrote {doc_path}")


if __name__ == "__main__":
    main()
