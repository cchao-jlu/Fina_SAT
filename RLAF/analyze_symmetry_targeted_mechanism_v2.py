from __future__ import annotations

import argparse
import hashlib
import math
import time
from copy import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from audit_event_symmetry import (
    add_identity_gain_columns,
    annotate_event_row_validity,
    annotate_orbit_rows,
    annotate_orbit_validity,
    event_state_orbit_rows,
    markdown_table,
    merge_orbit_rows,
    model_supports_event_adapter,
    normalized_orbit_entropy,
    orbit_entropy,
    solver_stats_has_events,
    tensor_orbit_rows,
)
from run_symmetry_solver_protocol_preflight import (
    DEFAULT_CHECKPOINT,
    clean_solver_params,
    graph_var_params,
    make_dimacs_dataset,
    run_solver_batch,
    solver_cli_number,
)
from src.data.symmetry import read_orbits_json
from src.model.model import load_checkpoint
from src.policy.evaluate import sample_var_params
from src.solving.budget import apply_rollout_budget
from src.solving.state import attach_var_event_state, event_state_dim


ROOT = Path(__file__).resolve().parent
DEFAULT_ATTRIBUTION = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv"
DEFAULT_BASE_SUMMARY = ROOT / "runs/analysis/symmetry_runtime_positive_v2_base_summary.csv"
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/symmetry_runtime_positive_v2_observations.csv"
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_targeted_mechanism_audit_v2.md"
DEFAULT_CANDIDATE_SUMMARY = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_candidate_summary.csv"
DEFAULT_REPEAT_JOIN = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_repeat_join.csv"
DEFAULT_ORBIT_ROWS = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_orbit_rows.csv"
DEFAULT_SUBSET_VARIANT = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_subset_variant_diagnosis.csv"
DEFAULT_RANDOM_CONTROL = ROOT / "runs/analysis/symmetry_targeted_mechanism_v2_random_control.csv"

TARGET_CANDIDATES = [
    "dominating_set_hex_3x6_s4",
    "subset_cardinality_bw12",
    "random_3sat_control_v20_c85_seed1901",
]


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def finite_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def bool_series(frame: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=bool)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(default).astype(bool)
    normalized = values.fillna(str(default)).astype(str).str.strip().str.lower()
    return normalized.isin({"1", "true", "yes", "y"})


def event_state_hash(event_state: torch.Tensor) -> str:
    array = event_state.detach().cpu().to(dtype=torch.float32).numpy()
    return hashlib.sha256(array.tobytes()).hexdigest()


def cnf_id_value(graph: Any) -> int:
    value = graph.cnf_id
    return int(value.item() if hasattr(value, "item") else value)


def graph_gate_info(
    event_state: torch.Tensor | None,
    graph_gate_indices: list[int],
    graph_gate_threshold: float | None,
) -> dict[str, Any]:
    if event_state is None:
        return {
            "event_state_nonzero_vars": 0,
            "event_state_l2_sum": 0.0,
            "event_state_l2_max": 0.0,
            "event_adapter_graph_gate_evidence": 0.0,
            "event_adapter_graph_gate_open": False,
            "event_state_hash": "",
        }
    state = event_state.detach().cpu().to(dtype=torch.float32)
    per_var_l2 = state.norm(dim=1)
    nonzero_vars = int((per_var_l2 > 1.0e-9).sum().item())
    l2_sum = float(per_var_l2.sum().item())
    l2_max = float(per_var_l2.max().item()) if per_var_l2.numel() else 0.0
    gate_indices = [int(index) for index in graph_gate_indices if int(index) < state.shape[1]]
    if not gate_indices or graph_gate_threshold is None:
        gate_evidence = 0.0
        gate_open = True
    else:
        gate_values = state[:, gate_indices].clamp_min(0.0)
        gate_evidence = float(gate_values.max().item()) if gate_values.numel() else 0.0
        gate_open = bool(gate_evidence >= float(graph_gate_threshold))
    return {
        "event_state_nonzero_vars": nonzero_vars,
        "event_state_l2_sum": l2_sum,
        "event_state_l2_max": l2_max,
        "event_adapter_graph_gate_evidence": gate_evidence,
        "event_adapter_graph_gate_open": gate_open,
        "event_state_hash": event_state_hash(state),
    }


def stats_has_events(row: pd.Series | None) -> bool:
    if row is None:
        return False
    for column, value in row.items():
        if str(column).startswith("event_var_") and isinstance(value, (list, tuple)) and len(value) > 0:
            return True
    return False


def static_graph_for_instance(
    model: torch.nn.Module,
    transform: Any,
    model_cfg: Any,
    instance: pd.Series,
    device: str,
) -> tuple[Any, Any]:
    dataset = make_dimacs_dataset([str(resolve(instance["cnf_path"]))], transform=transform)
    loader = DataLoader(dataset=dataset, batch_size=1, num_workers=0, shuffle=False)
    graphs = sample_var_params(
        model=model,
        loader=loader,
        num_samples=1,
        device=device,
        use_mode=True,
        scale_sigma=float(model_cfg.get("scale_sigma", 0.1) if hasattr(model_cfg, "get") else getattr(model_cfg, "scale_sigma", 0.1)),
        add_timing=True,
        cache_var_features=True,
    )
    if len(graphs) != 1:
        raise RuntimeError(f"expected one static graph for {instance['instance_id']}, got {len(graphs)}")
    return dataset, graphs[0]


def run_warmup_for_observation(
    dataset: Any,
    static_graph: Any,
    solver: str,
    warmup_seed: int,
    warmup_cpu_lim: float,
    warmup_conflicts: int,
    trace_lbd: int,
    rnd_freq: float,
    k_value: float,
) -> pd.Series:
    params = clean_solver_params({"rnd-freq": rnd_freq, "K": k_value})
    params = apply_rollout_budget(
        params,
        budget_type="conflicts",
        cpu_lim=solver_cli_number(warmup_cpu_lim),
        conflicts=int(warmup_conflicts),
    )
    params["collect-events"] = True
    params["trace-lbd"] = int(trace_lbd)
    stats = run_solver_batch(
        dataset=dataset,
        graphs=[static_graph],
        guided=True,
        solver=solver,
        seed=int(warmup_seed),
        solver_params=params,
        num_workers=1,
        phase_name="targeted_event_warmup_collect_events",
        repeat_id=0,
    )
    if stats.empty:
        raise RuntimeError("warmup solver returned no rows")
    return stats.iloc[0]


def attach_event_state(
    graph: Any,
    warmup_stats: pd.Series,
    event_state_features: str,
) -> Any:
    return attach_var_event_state(
        graph,
        stats=warmup_stats,
        var_state_dim=event_state_dim(event_state_features),
        momentum=0.0,
        feature_mode=event_state_features,
    )


def orbit_rows_for_observation(
    *,
    model: torch.nn.Module,
    instance: pd.Series,
    refined_graph: Any,
    warmup_stats: pd.Series,
    runtime_row: pd.Series,
    checkpoint: Path,
    device: str,
    event_state_features: str,
    min_orbit_size: int,
    static_collapse_threshold: float,
    event_identity_eps: float,
    event_info: dict[str, Any],
) -> pd.DataFrame:
    variable_orbits = read_orbits_json(
        resolve(instance["orbits_path"]),
        num_vars=int(refined_graph["var"].base_y.shape[0]),
    )
    frames = [
        pd.DataFrame(tensor_orbit_rows(refined_graph["var"].base_y, variable_orbits, prefix="static")),
        pd.DataFrame(event_state_orbit_rows(refined_graph["var"].event_state, variable_orbits)),
    ]
    if model_supports_event_adapter(model):
        model.to(device)
        model.eval()
        with torch.no_grad():
            batch = next(iter(DataLoader(dataset=[refined_graph], batch_size=1, num_workers=0, shuffle=False))).to(device)
            adapted_y = model(batch).detach().cpu()
        frames.append(pd.DataFrame(tensor_orbit_rows(adapted_y, variable_orbits, prefix="adapted")))
    rows = merge_orbit_rows(*frames)
    rows = add_identity_gain_columns(rows)
    rows = annotate_orbit_validity(rows, min_orbit_size=min_orbit_size)
    rows = annotate_orbit_rows(
        rows,
        instance=instance,
        checkpoint_path=checkpoint,
        solver=str(runtime_row.get("solver", "glucose")),
        rollout_budget_type="conflicts",
        rollout_cpu_lim=float(runtime_row.get("warmup_cpu_lim", 5.0)),
        rollout_conflicts=int(runtime_row.get("warmup_conflict_budget", 20)),
        event_state_features=event_state_features,
        adapter_supported=model_supports_event_adapter(model),
        audit_status="ok" if stats_has_events(warmup_stats) else "missing_events",
        audit_error="" if stats_has_events(warmup_stats) else "warmup solver did not emit event_var_* columns",
    )
    rows = annotate_event_row_validity(
        rows,
        solver_stats=pd.DataFrame([warmup_stats]),
        static_collapse_threshold=static_collapse_threshold,
        event_identity_eps=event_identity_eps,
    )
    rows["orbit_entropy"] = float(orbit_entropy(variable_orbits))
    rows["orbit_entropy_norm"] = float(normalized_orbit_entropy(variable_orbits))
    for key in [
        "repeat_id",
        "solver_seed",
        "warmup_seed",
        "final_seed",
        "primary_delta_final_cpu",
        "primary_delta_final_decisions",
        "primary_delta_final_conflicts",
        "primary_delta_protocol_time",
        "secondary_delta_final_cpu",
        "secondary_delta_final_decisions",
        "secondary_delta_final_conflicts",
        "secondary_delta_protocol_time",
        "event_collection_overhead_delta_protocol_time",
    ]:
        rows[key] = runtime_row.get(key, np.nan)
    for key, value in event_info.items():
        rows[key] = value
    rows["trace_event_identifier"] = rows["event_state_hash"].astype(str)
    rows["cnf_path"] = str(instance["cnf_path"])
    return rows


def aggregate_repeat_join(orbit_rows: pd.DataFrame) -> pd.DataFrame:
    if orbit_rows.empty:
        return pd.DataFrame()
    bool_event_valid = bool_series(orbit_rows, "event_row_valid", default=False)
    bool_positive = bool_series(orbit_rows, "event_identity_positive", default=False)
    work = orbit_rows.copy()
    work["_event_row_valid_bool"] = bool_event_valid
    work["_event_identity_positive_bool"] = bool_positive
    grouped = work.groupby(["family", "base_instance_id", "variant", "repeat_id"], sort=True)
    return grouped.agg(
        solver_seed=("solver_seed", "first"),
        warmup_seed=("warmup_seed", "first"),
        final_seed=("final_seed", "first"),
        trace_event_identifier=("trace_event_identifier", "first"),
        event_state_hash=("event_state_hash", "first"),
        event_state_l2_sum=("event_state_l2_sum", "first"),
        event_state_nonzero_vars=("event_state_nonzero_vars", "first"),
        event_adapter_graph_gate_evidence=("event_adapter_graph_gate_evidence", "first"),
        event_adapter_graph_gate_open=("event_adapter_graph_gate_open", "first"),
        warmup_decisions=("warmup_decisions", "first"),
        warmup_conflicts=("warmup_conflicts", "first"),
        orbit_rows=("orbit", "count"),
        orbit_valid_rows=("orbit_valid", lambda values: int(pd.Series(values).astype(bool).sum())),
        event_row_valid_rows=("_event_row_valid_bool", "sum"),
        event_identity_positive_rows=("_event_identity_positive_bool", "sum"),
        event_identity_gain_mean=("event_identity_gain", "mean"),
        event_identity_gain_max=("event_identity_gain", "max"),
        adapter_identity_gain_mean=("adapter_identity_gain", "mean"),
        adapter_identity_gain_max=("adapter_identity_gain", "max"),
        adapted_mu_range_mean=("adapted_mu_range", "mean"),
        adapted_mu_range_max=("adapted_mu_range", "max"),
        adapted_rho_range_mean=("adapted_rho_range", "mean"),
        adapted_rho_range_max=("adapted_rho_range", "max"),
        primary_delta_final_cpu=("primary_delta_final_cpu", "first"),
        primary_delta_final_decisions=("primary_delta_final_decisions", "first"),
        primary_delta_final_conflicts=("primary_delta_final_conflicts", "first"),
        primary_delta_protocol_time=("primary_delta_protocol_time", "first"),
        secondary_delta_final_cpu=("secondary_delta_final_cpu", "first"),
        secondary_delta_final_decisions=("secondary_delta_final_decisions", "first"),
        secondary_delta_final_conflicts=("secondary_delta_final_conflicts", "first"),
        secondary_delta_protocol_time=("secondary_delta_protocol_time", "first"),
        event_collection_overhead_delta_protocol_time=("event_collection_overhead_delta_protocol_time", "first"),
    ).reset_index()


def candidate_qualification(base_summary: pd.DataFrame) -> pd.DataFrame:
    selected = base_summary[base_summary["base_instance_id"].isin(TARGET_CANDIDATES)].copy()
    tiers = []
    notes = []
    for _, row in selected.iterrows():
        base = str(row["base_instance_id"])
        primary_classification = str(row.get("primary_classification", ""))
        if str(row.get("control_type", "")) == "non_symmetric_control":
            tiers.append("control_perturbation")
            notes.append("non-symmetric control; search change is not symmetry-specific evidence")
        elif base == "dominating_set_hex_3x6_s4":
            tiers.append(
                "strong_strict_positive"
                if primary_classification == "strict_positive"
                else "strong_named_runtime_regressed"
            )
            notes.append(
                "primary symmetry candidate; conflicts drop in all observed rows, "
                "but current full-v2 CPU direction no longer qualifies as strict-positive"
                if primary_classification != "strict_positive"
                else "primary symmetry candidate; conflicts drop in all observed rows"
            )
        elif base == "subset_cardinality_bw12":
            tiers.append(
                "weak_strict_positive"
                if primary_classification == "strict_positive"
                else "weak_named_runtime_regressed"
            )
            notes.append(
                "symmetry candidate with variant-mixed search response; current full-v2 CPU "
                "direction no longer qualifies as strict-positive"
                if primary_classification != "strict_positive"
                else "symmetry candidate with variant-mixed search response"
            )
        else:
            tiers.append("weak_strict_positive" if primary_classification == "strict_positive" else "named_runtime_regressed")
            notes.append("named target retained for diagnostic continuity")
    selected["qualification_tier"] = tiers
    selected["qualification_note"] = notes
    return selected


def ensure_protocol_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    repeat_id = pd.to_numeric(frame["repeat_id"], errors="coerce").fillna(0).astype(int)
    for column in ["solver_seed", "warmup_seed", "final_seed"]:
        if column not in frame.columns:
            frame[column] = repeat_id + 1
        else:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(repeat_id + 1).astype(int)
    defaults = {
        "warmup_cpu_lim": 5.0,
        "final_cpu_lim": 5.0,
        "solver": "glucose",
    }
    for column, value in defaults.items():
        if column not in frame.columns:
            frame[column] = value
        else:
            frame[column] = frame[column].fillna(value)
    # `warmup_conflicts` in the v2 positive-observation table is the observed
    # warmup conflict count. Keep it for diagnosis and use a separate protocol
    # budget field when replaying event collection.
    frame["warmup_conflict_budget"] = 20
    return frame


def mechanism_label_for_group(group: pd.DataFrame, require_variant_stability: bool = False) -> str:
    if group.empty:
        return "mechanism not aligned"
    cpu_down = int((pd.to_numeric(group["primary_delta_final_cpu"], errors="coerce") < 0.0).sum())
    decisions_down = int((pd.to_numeric(group["primary_delta_final_decisions"], errors="coerce") < 0.0).sum())
    conflicts_down = int((pd.to_numeric(group["primary_delta_final_conflicts"], errors="coerce") < 0.0).sum())
    search_down = max(decisions_down, conflicts_down)
    n = len(group)
    event_positive = int((pd.to_numeric(group["event_identity_gain_max"], errors="coerce").fillna(0.0) > 1.0e-6).sum())
    adapter_positive = int((pd.to_numeric(group["adapter_identity_gain_max"], errors="coerce").fillna(0.0) > 1.0e-6).sum())
    if require_variant_stability:
        variant_ok = True
        for _, variant_group in group.groupby("variant"):
            v_search = max(
                int((pd.to_numeric(variant_group["primary_delta_final_decisions"], errors="coerce") < 0.0).sum()),
                int((pd.to_numeric(variant_group["primary_delta_final_conflicts"], errors="coerce") < 0.0).sum()),
            )
            variant_ok = variant_ok and v_search >= max(1, len(variant_group) // 2 + 1)
        if not variant_ok:
            return "mechanism partially aligned"
    if search_down >= n // 2 + 1 and event_positive >= n // 2 + 1 and adapter_positive >= n // 2 + 1:
        return "mechanism aligned" if cpu_down >= n // 2 + 1 else "mechanism partially aligned"
    if search_down >= n // 2 + 1 or event_positive >= n // 2 + 1 or adapter_positive >= n // 2 + 1:
        return "mechanism partially aligned"
    return "mechanism not aligned"


def build_candidate_summary(qualification: pd.DataFrame, repeat_join: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, q in qualification.iterrows():
        base = str(q["base_instance_id"])
        group = repeat_join[repeat_join["base_instance_id"].astype(str).eq(base)].copy()
        label = mechanism_label_for_group(group, require_variant_stability=(base == "dominating_set_hex_3x6_s4"))
        rows.append(
            {
                "family": q["family"],
                "base_instance_id": base,
                "control_type": q.get("control_type", ""),
                "scale": q.get("scale", ""),
                "primary_classification": q.get("primary_classification", ""),
                "qualification_tier": q["qualification_tier"],
                "qualification_note": q["qualification_note"],
                "mechanism_label": label,
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
                "mean_secondary_delta_protocol_time": float(group["secondary_delta_protocol_time"].mean()) if not group.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def subset_variant_diagnosis(repeat_join: pd.DataFrame) -> pd.DataFrame:
    subset = repeat_join[repeat_join["base_instance_id"].eq("subset_cardinality_bw12")].copy()
    if subset.empty:
        return pd.DataFrame()
    rows = []
    for variant, group in subset.groupby("variant", sort=True):
        decisions_delta = pd.to_numeric(group["primary_delta_final_decisions"], errors="coerce")
        conflicts_delta = pd.to_numeric(group["primary_delta_final_conflicts"], errors="coerce")
        cpu_delta = pd.to_numeric(group["primary_delta_final_cpu"], errors="coerce")
        rows.append(
            {
                "base_instance_id": "subset_cardinality_bw12",
                "variant": variant,
                "repeat_rows": int(len(group)),
                "cpu_down_rows": int((cpu_delta < 0.0).sum()),
                "decisions_down_rows": int((decisions_delta < 0.0).sum()),
                "decisions_up_rows": int((decisions_delta > 0.0).sum()),
                "conflicts_down_rows": int((conflicts_delta < 0.0).sum()),
                "conflicts_up_rows": int((conflicts_delta > 0.0).sum()),
                "mean_event_l2": float(group["event_state_l2_sum"].mean()),
                "mean_gate_evidence": float(group["event_adapter_graph_gate_evidence"].mean()),
                "gate_open_rows": int(group["event_adapter_graph_gate_open"].astype(bool).sum()),
                "mean_event_identity_gain_max": float(group["event_identity_gain_max"].mean()),
                "mean_adapter_identity_gain_max": float(group["adapter_identity_gain_max"].mean()),
                "mean_warmup_decisions": float(group["warmup_decisions"].mean()),
                "mean_warmup_conflicts": float(group["warmup_conflicts"].mean()),
                "mean_primary_delta_final_cpu": float(cpu_delta.mean()),
                "mean_primary_delta_final_decisions": float(decisions_delta.mean()),
                "mean_primary_delta_final_conflicts": float(conflicts_delta.mean()),
                "diagnosis": (
                    "variant_search_worse_over_adaptation_or_perm_nonrobust"
                    if (decisions_delta > 0.0).sum() >= 2 or (conflicts_delta > 0.0).sum() >= 2
                    else "variant_search_improved"
                ),
            }
        )
    return pd.DataFrame(rows)


def random_control_summary(repeat_join: pd.DataFrame) -> pd.DataFrame:
    group = repeat_join[repeat_join["base_instance_id"].eq("random_3sat_control_v20_c85_seed1901")].copy()
    if group.empty:
        return pd.DataFrame()
    return group.groupby(["family", "base_instance_id", "variant"], sort=True).agg(
        repeat_rows=("repeat_id", "count"),
        decisions_down_rows=("primary_delta_final_decisions", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.0).sum())),
        conflicts_down_rows=("primary_delta_final_conflicts", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.0).sum())),
        cpu_down_rows=("primary_delta_final_cpu", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.0).sum())),
        mean_event_identity_gain_max=("event_identity_gain_max", "mean"),
        mean_adapter_identity_gain_max=("adapter_identity_gain_max", "mean"),
        mean_primary_delta_final_decisions=("primary_delta_final_decisions", "mean"),
        mean_primary_delta_final_cpu=("primary_delta_final_cpu", "mean"),
    ).reset_index()


def write_doc(
    path: Path,
    *,
    candidate_summary: pd.DataFrame,
    repeat_join: pd.DataFrame,
    orbit_rows: pd.DataFrame,
    subset_diag: pd.DataFrame,
    random_control: pd.DataFrame,
    attribution_csv: Path,
    base_summary_csv: Path,
    observations_csv: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dom = repeat_join[repeat_join["base_instance_id"].eq("dominating_set_hex_3x6_s4")].copy()
    subset = repeat_join[repeat_join["base_instance_id"].eq("subset_cardinality_bw12")].copy()
    control = repeat_join[repeat_join["base_instance_id"].eq("random_3sat_control_v20_c85_seed1901")].copy()
    label_by_base = (
        candidate_summary.drop_duplicates("base_instance_id")
        .set_index("base_instance_id")["mechanism_label"]
        .astype(str)
        .to_dict()
        if not candidate_summary.empty
        else {}
    )
    tier_by_base = (
        candidate_summary.drop_duplicates("base_instance_id")
        .set_index("base_instance_id")["qualification_tier"]
        .astype(str)
        .to_dict()
        if not candidate_summary.empty
        else {}
    )
    dom_view = dom[
        [
            "variant",
            "repeat_id",
            "event_state_l2_sum",
            "event_identity_gain_max",
            "adapter_identity_gain_max",
            "event_adapter_graph_gate_evidence",
            "primary_delta_final_cpu",
            "primary_delta_final_decisions",
            "primary_delta_final_conflicts",
            "secondary_delta_protocol_time",
        ]
    ].copy()
    subset_view = subset[
        [
            "variant",
            "repeat_id",
            "event_state_l2_sum",
            "event_identity_gain_max",
            "adapter_identity_gain_max",
            "warmup_decisions",
            "warmup_conflicts",
            "primary_delta_final_cpu",
            "primary_delta_final_decisions",
            "primary_delta_final_conflicts",
        ]
    ].copy()
    control_view = control[
        [
            "variant",
            "repeat_id",
            "event_state_l2_sum",
            "event_identity_gain_max",
            "adapter_identity_gain_max",
            "primary_delta_final_cpu",
            "primary_delta_final_decisions",
            "primary_delta_final_conflicts",
        ]
    ].copy()
    validity = (
        orbit_rows.groupby(["base_instance_id", "event_row_valid_reason"], sort=True)
        .agg(rows=("orbit", "count"))
        .reset_index()
        if not orbit_rows.empty and "event_row_valid_reason" in orbit_rows.columns
        else pd.DataFrame()
    )
    lines = [
        "# Targeted v2 Mechanism Audit",
        "",
        "## 1. Scope and Non-Claims",
        "",
        "This targeted audit tests whether selected positive runtime cases form a plausible",
        "mechanism chain: event identity signal -> adapter orbit separation -> final search",
        "changes -> decisions/conflicts/final-CPU improvement. It does not train, does not",
        "build a gate/selector, does not expand the full runtime benchmark, and does not",
        "make a solver speedup claim.",
        "",
        "Fixed inputs:",
        "",
        f"- attribution CSV: `{attribution_csv}`",
        f"- base summary CSV: `{base_summary_csv}`",
        f"- observations CSV: `{observations_csv}`",
        "",
        "## 2. Candidate Qualification",
        "",
        *markdown_table(candidate_summary),
        "",
        "The named candidates are retained for mechanism diagnostics. In the refreshed v2 full",
        "runtime run used here, the two symmetry candidates no longer satisfy current",
        "`strict_positive` qualification because final CPU is not majority-down. The audit",
        "therefore treats them as diagnostic named targets, not as fresh runtime-positive",
        "evidence.",
        "",
        "## 3. Per-Repeat Join Method",
        "",
        "For each targeted `base_instance_id + variant + repeat_id`, the script replays only",
        "the short event-collecting warmup with the recorded `warmup_seed`, attaches the",
        "enhanced event state, computes orbit-level event identity and adapter separation,",
        "and joins those representation rows back to the v2 runtime deltas. The join key is",
        "`base_instance_id + variant + repeat_id`; `event_state_hash` is recorded as the",
        "trace/event identifier.",
        "",
        "Orbit validity summary:",
        "",
        *markdown_table(validity),
        "",
        "## 4. Dominating Set Hex Mechanism",
        "",
        *markdown_table(dom_view),
        "",
        f"Conclusion: `dominating_set_hex_3x6_s4` is `{label_by_base.get('dominating_set_hex_3x6_s4', 'mechanism not aligned')}` under the refreshed v2 runtime rows.",
        "Conflicts drop in all nine rows, event identity is positive on valid orbit rows,",
        "and adapter separation is present. CPU does not move in the same direction on a",
        "majority of rows, and the `perm_seed1730` variant has decision increases, so the",
        "evidence is conflicts-driven and only partial. Protocol time still loses against",
        "static because event collection overhead is much larger than the local final-solve",
        "gain.",
        "",
        "## 5. Subset Cardinality Variant Diagnosis",
        "",
        *markdown_table(subset_diag),
        "",
        *markdown_table(subset_view),
        "",
        "Conclusion: `subset_cardinality_bw12` is mechanism partially aligned and",
        "variant-mixed. The base and `perm_seed1731` variants show large search reductions,",
        "but `perm_seed1730` consistently worsens decisions/conflicts despite strong event",
        "L2, open graph gate, and nonzero adapter separation. That points to permutation",
        "non-robustness or over-adaptation in the adapter objective rather than a clean",
        "family-level mechanism.",
        "",
        "## 6. Random Control Check",
        "",
        *markdown_table(random_control),
        "",
        *markdown_table(control_view),
        "",
        "Conclusion: the random 3SAT control shows adapter-induced search perturbation",
        "without symmetry-specific evidence. It must stay separate from symmetry-positive",
        "claims.",
        "",
        "## 7. Decision and Next Step",
        "",
        f"- Dominating hex: `{tier_by_base.get('dominating_set_hex_3x6_s4', '')}` and `{label_by_base.get('dominating_set_hex_3x6_s4', '')}`; do not expand to gate/selector. Recheck nearby hex only after runtime qualification is stable.",
        f"- Subset cardinality: `{tier_by_base.get('subset_cardinality_bw12', '')}` and `{label_by_base.get('subset_cardinality_bw12', '')}`; investigate permutation robustness/objective before broader runtime work.",
        "- Random control: generic perturbation exists; do not treat search changes alone as symmetry benefit.",
        "- Full gate/selector remains postponed until multiple symmetry families show stable aligned mechanisms and event overhead has a credible reduction path.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Targeted v2 mechanism audit for selected SAT symmetry runtime positives.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--attribution-csv", type=Path, default=DEFAULT_ATTRIBUTION)
    parser.add_argument("--base-summary-csv", type=Path, default=DEFAULT_BASE_SUMMARY)
    parser.add_argument("--observations-csv", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--candidate-summary-csv", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--repeat-join-csv", type=Path, default=DEFAULT_REPEAT_JOIN)
    parser.add_argument("--orbit-rows-csv", type=Path, default=DEFAULT_ORBIT_ROWS)
    parser.add_argument("--subset-variant-csv", type=Path, default=DEFAULT_SUBSET_VARIANT)
    parser.add_argument("--random-control-csv", type=Path, default=DEFAULT_RANDOM_CONTROL)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
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

    checkpoint = resolve(args.checkpoint).resolve()
    manifest = pd.read_csv(resolve(args.manifest))
    attribution = pd.read_csv(resolve(args.attribution_csv))
    base_summary = pd.read_csv(resolve(args.base_summary_csv))
    observations = pd.read_csv(resolve(args.observations_csv))

    target_runtime = observations[observations["base_instance_id"].isin(TARGET_CANDIDATES)].copy()
    target_runtime = ensure_protocol_columns(target_runtime)
    if target_runtime.empty:
        raise ValueError("No target candidates found in observations CSV")
    target_runtime = target_runtime.sort_values(["base_instance_id", "variant", "repeat_id"]).reset_index(drop=True)
    manifest_lookup = {
        (str(row["base_instance_id"]), str(row["variant"])): row
        for _, row in manifest.iterrows()
        if str(row["base_instance_id"]) in TARGET_CANDIDATES
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
    start_all = time.perf_counter()
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

    orbit_rows = pd.concat(orbit_frames, ignore_index=True)
    repeat_join = aggregate_repeat_join(orbit_rows)
    qualification = candidate_qualification(base_summary)
    candidate_summary = build_candidate_summary(qualification, repeat_join)
    subset_diag = subset_variant_diagnosis(repeat_join)
    random_control = random_control_summary(repeat_join)
    elapsed = time.perf_counter() - start_all
    candidate_summary["targeted_audit_wall_time_total"] = float(elapsed)

    outputs = [
        (resolve(args.candidate_summary_csv), candidate_summary),
        (resolve(args.repeat_join_csv), repeat_join),
        (resolve(args.orbit_rows_csv), orbit_rows),
        (resolve(args.subset_variant_csv), subset_diag),
        (resolve(args.random_control_csv), random_control),
    ]
    for path, frame in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
        print(f"wrote {path}")
    write_doc(
        resolve(args.doc),
        candidate_summary=candidate_summary,
        repeat_join=repeat_join,
        orbit_rows=orbit_rows,
        subset_diag=subset_diag,
        random_control=random_control,
        attribution_csv=resolve(args.attribution_csv),
        base_summary_csv=resolve(args.base_summary_csv),
        observations_csv=resolve(args.observations_csv),
    )
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
