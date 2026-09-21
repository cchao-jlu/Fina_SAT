from __future__ import annotations

import json
from copy import copy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from torch import Tensor
from torch_geometric.data import HeteroData
from torch_geometric.loader import DataLoader

from src.solving.state import attach_var_event_state


@dataclass(frozen=True)
class TraceLabelConfig:
    """Weights and scaling for event-trace pseudo labels."""

    low_lbd_weight: float = 0.35
    useful_decision_weight: float = 0.25
    conflict_rank_weight: float = 0.20
    propagation_rank_weight: float = 0.10
    activity_rank_weight: float = 0.10
    target_scale: float = 2.0
    target_delta_clip: float | None = None
    min_target_mu: float = -4.0
    max_target_mu: float = 4.0
    rho_loss_weight: float = 0.0
    mu_loss_weight: float = 1.0
    focus_gate_enabled: bool = False
    focus_topk_ratio: float = 0.10
    focus_min_topk_mass: float = 0.45
    focus_min_multiplier: float = 0.25
    focus_power: float = 1.0
    no_activity_negative_weight: float = 0.0
    no_activity_gate_indices: list[int] = field(default_factory=lambda: [0, 2])
    no_activity_gate_eps: float = 1.0e-9
    no_activity_negative_rho_loss_weight: float = 0.0
    no_activity_negative_mu_loss_weight: float = 1.0
    permutation_consistency_weight: float = 0.0
    permutation_consistency_rho_loss_weight: float = 0.0
    permutation_consistency_mu_loss_weight: float = 1.0
    permutation_delta_consistency_weight: float = 0.0
    permutation_delta_consistency_rho_loss_weight: float = 0.0
    permutation_delta_consistency_mu_loss_weight: float = 1.0
    permutation_consistency_max_pairs_per_epoch: int | None = None
    valid_orbit_only_distillation: bool = False
    valid_orbit_identity_weight: float = 0.0
    valid_orbit_identity_rho_loss_weight: float = 0.0
    valid_orbit_identity_mu_loss_weight: float = 1.0
    negative_guard_weight: float = 0.0
    negative_guard_rho_loss_weight: float = 0.0
    negative_guard_mu_loss_weight: float = 1.0
    negative_guard_no_valid_orbit: bool = True
    adapter_delta_magnitude_weight: float = 0.0
    adapter_delta_magnitude_rho_loss_weight: float = 0.0
    adapter_delta_magnitude_mu_loss_weight: float = 1.0
    adapter_delta_magnitude_margin: float = 0.0


@dataclass
class TracePseudoLabel:
    target_y: Tensor
    confidence: Tensor
    score: Tensor
    components: dict[str, Tensor] = field(default_factory=dict)


@dataclass(frozen=True)
class PermutationConsistencyPair:
    base_graph: HeteroData
    permuted_graph: HeteroData
    permutation_old_to_new: Tensor
    family: str
    base_instance_id: str
    permuted_instance_id: str
    variant: str
    sample_id: int


def trace_label_config_from_mapping(mapping: Any | None) -> TraceLabelConfig:
    if mapping is None:
        return TraceLabelConfig()
    values = {}
    for key in asdict(TraceLabelConfig()).keys():
        if key in mapping:
            values[key] = mapping[key]
    return TraceLabelConfig(**values)


def trace_label_config_to_dict(config: TraceLabelConfig) -> dict[str, Any]:
    return asdict(config)


def _to_stats_dict(stats: dict[str, Any] | pd.Series) -> dict[str, Any]:
    if isinstance(stats, pd.Series):
        return stats.to_dict()
    return dict(stats)


def _raw_event_values(stats: dict[str, Any] | pd.Series, key: str, num_vars: int) -> Tensor:
    stats = _to_stats_dict(stats)
    values = stats.get(key)
    if values is None or (isinstance(values, float) and pd.isna(values)):
        return torch.zeros(num_vars, dtype=torch.float32)
    values = torch.as_tensor(values, dtype=torch.float32)
    if values.numel() < num_vars:
        values = torch.cat([values, torch.zeros(num_vars - values.numel(), dtype=torch.float32)])
    elif values.numel() > num_vars:
        values = values[:num_vars]
    return torch.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0).clamp_min_(0.0)


def _event_values_with_fallback(
    stats: dict[str, Any] | pd.Series,
    key: str,
    fallback_key: str,
    num_vars: int,
) -> Tensor:
    values = _raw_event_values(stats, key, num_vars)
    if values.sum() > 0:
        return values
    return _raw_event_values(stats, fallback_key, num_vars)


def percentile_rank(values: Tensor) -> Tensor:
    """Map non-negative event values to [0, 1] ranks with equal values tied."""
    values = torch.nan_to_num(values.to(dtype=torch.float32), nan=0.0, posinf=0.0, neginf=0.0).clamp_min(0.0)
    if values.numel() <= 1 or torch.all(values == values[0]):
        return torch.zeros_like(values)
    unique_values, inverse = torch.unique(values, sorted=True, return_inverse=True)
    if unique_values.numel() <= 1:
        return torch.zeros_like(values)
    unique_ranks = torch.linspace(0.0, 1.0, unique_values.numel(), dtype=torch.float32, device=values.device)
    return unique_ranks[inverse]


def _weighted_score(components: dict[str, Tensor], config: TraceLabelConfig) -> Tensor:
    weighted_terms = [
        (config.low_lbd_weight, components["low_lbd_rank"]),
        (config.useful_decision_weight, components["useful_decision_rank"]),
        (config.conflict_rank_weight, components["conflict_rank"]),
        (config.propagation_rank_weight, components["propagation_rank"]),
        (config.activity_rank_weight, components["activity_rank"]),
    ]
    total_weight = sum(max(float(weight), 0.0) for weight, _ in weighted_terms)
    if total_weight <= 0.0:
        raise ValueError("Trace pseudo-label score requires at least one positive component weight")
    score = sum(max(float(weight), 0.0) * value for weight, value in weighted_terms)
    return (score / total_weight).clamp_(0.0, 1.0)


def _topk_mass(values: Tensor, ratio: float) -> float:
    values = torch.nan_to_num(values.to(dtype=torch.float32), nan=0.0, posinf=0.0, neginf=0.0).clamp_min(0.0)
    total = values.sum()
    if values.numel() == 0 or total <= 1.0e-9:
        return 0.0
    k = max(1, int(torch.floor(torch.tensor(float(ratio) * values.numel())).item()))
    return float((values.topk(k).values.sum() / total).clamp(0.0, 1.0).item())


def _focus_multiplier(
    focus_values: Tensor,
    config: TraceLabelConfig,
) -> float:
    if not bool(config.focus_gate_enabled):
        return 1.0
    mass = _topk_mass(focus_values, ratio=max(float(config.focus_topk_ratio), 0.0))
    min_mass = max(float(config.focus_min_topk_mass), 1.0e-9)
    min_multiplier = min(max(float(config.focus_min_multiplier), 0.0), 1.0)
    if mass <= 0.0:
        return min_multiplier
    normalized = min(max(mass / min_mass, 0.0), 1.0)
    power = max(float(config.focus_power), 1.0e-6)
    scaled = normalized ** power
    return min_multiplier + (1.0 - min_multiplier) * scaled


def build_trace_pseudo_label(
    stats: dict[str, Any] | pd.Series,
    num_vars: int,
    base_y: Tensor | None = None,
    config: TraceLabelConfig | None = None,
) -> TracePseudoLabel:
    """Build adapter distillation targets from one solver rollout event trace."""
    if config is None:
        config = TraceLabelConfig()
    if base_y is None:
        base_y = torch.zeros((num_vars, 2), dtype=torch.float32)
    else:
        base_y = base_y.detach().to(dtype=torch.float32)
        if base_y.dim() == 1:
            base_y = base_y.view(num_vars, -1)
        if base_y.shape[0] != num_vars or base_y.shape[1] < 2:
            raise ValueError(f"base_y must have shape ({num_vars}, >=2), got {tuple(base_y.shape)}")

    low_lbd = _event_values_with_fallback(
        stats,
        key="event_var_low_lbd_learnt_lits",
        fallback_key="event_var_learnt_lits",
        num_vars=num_vars,
    )
    useful_decisions = _event_values_with_fallback(
        stats,
        key="event_var_useful_decisions",
        fallback_key="event_var_decisions",
        num_vars=num_vars,
    )
    conflict_lits = _raw_event_values(stats, "event_var_conflict_lits", num_vars)
    propagations = _raw_event_values(stats, "event_var_propagations", num_vars)
    activity = _raw_event_values(stats, "event_var_activity", num_vars)
    focus_values = low_lbd + conflict_lits

    components = {
        "low_lbd_rank": percentile_rank(low_lbd),
        "useful_decision_rank": percentile_rank(useful_decisions),
        "conflict_rank": percentile_rank(conflict_lits),
        "propagation_rank": percentile_rank(propagations),
        "activity_rank": percentile_rank(activity),
    }
    score = _weighted_score(components, config)
    focus_scale = _focus_multiplier(focus_values, config)
    centered = score - score.mean()
    std = centered.std(unbiased=False)
    if torch.isfinite(std) and std > 1.0e-6:
        centered = centered / std
    delta_mu = float(focus_scale) * config.target_scale * centered
    if config.target_delta_clip is not None:
        delta_clip = abs(float(config.target_delta_clip))
        delta_mu = delta_mu.clamp(-delta_clip, delta_clip)

    target_y = base_y[:, :2].clone()
    target_y[:, 1] = (target_y[:, 1] + delta_mu).clamp(config.min_target_mu, config.max_target_mu)

    confidence = score.clone()
    max_conf = confidence.max()
    if torch.isfinite(max_conf) and max_conf > 0:
        confidence = confidence / max_conf
    confidence = confidence * float(focus_scale)
    components["focus_topk_mass"] = torch.full_like(score, _topk_mass(focus_values, config.focus_topk_ratio))
    components["focus_multiplier"] = torch.full_like(score, float(focus_scale))

    return TracePseudoLabel(
        target_y=torch.nan_to_num(target_y, nan=0.0, posinf=config.max_target_mu, neginf=config.min_target_mu),
        confidence=torch.nan_to_num(confidence, nan=0.0, posinf=1.0, neginf=0.0).clamp_(0.0, 1.0),
        score=score,
        components=components,
    )


def attach_trace_pseudo_labels(
    data: HeteroData,
    stats: dict[str, Any] | pd.Series,
    config: TraceLabelConfig | None = None,
) -> HeteroData:
    """Attach trace distillation targets to a graph with cached slow-GNN features."""
    data = copy(data)
    num_vars = int(data["lit"].num_nodes // 2)
    base_y = data["var"].base_y if "var" in data.node_types and hasattr(data["var"], "base_y") else None
    label = build_trace_pseudo_label(stats, num_vars=num_vars, base_y=base_y, config=config)
    data["var"].num_nodes = num_vars
    data["var"].trace_target_y = label.target_y
    data["var"].trace_confidence = label.confidence
    data["var"].trace_score = label.score
    for key, value in label.components.items():
        setattr(data["var"], key, value)
    return data


def _single_sample_var_params(var_params: Tensor, sample_id: int) -> Tensor:
    if var_params.dim() == 3:
        return var_params[:, sample_id : sample_id + 1, :]
    if var_params.dim() == 2:
        return var_params.unsqueeze(1)
    raise ValueError(f"Expected var_params with shape [num_vars, samples, 2] or [num_vars, 2], got {tuple(var_params.shape)}")


def build_trace_distillation_graphs(
    data_list: list[HeteroData],
    solver_stats: pd.DataFrame,
    var_state_dim: int,
    event_state_feature_mode: str = "legacy",
    state_momentum: float = 0.0,
    label_config: TraceLabelConfig | None = None,
) -> list[HeteroData]:
    """Expand rollout stats into one cached adapter-training graph per solver sample."""
    if solver_stats.empty:
        return []
    required_cols = {"cnf_id", "sample_id"}
    missing = required_cols.difference(solver_stats.columns)
    if missing:
        raise ValueError(f"solver_stats missing required columns: {sorted(missing)}")

    stats_by_cnf = {
        int(cnf_id): group.sort_values("sample_id")
        for cnf_id, group in solver_stats.groupby("cnf_id", sort=False)
    }

    trace_graphs: list[HeteroData] = []
    for data in data_list:
        cnf_id = int(data.cnf_id.item())
        cnf_stats = stats_by_cnf.get(cnf_id)
        if cnf_stats is None:
            continue
        for _, stats in cnf_stats.iterrows():
            sample_id = int(stats["sample_id"])
            graph = copy(data)
            graph.sample_id = torch.tensor(sample_id, dtype=torch.long)
            if "var" in graph.node_types and hasattr(graph["var"], "var_params"):
                graph["var"].var_params = _single_sample_var_params(graph["var"].var_params, sample_id)
            graph = attach_var_event_state(
                graph,
                stats=stats,
                var_state_dim=var_state_dim,
                momentum=state_momentum,
                feature_mode=event_state_feature_mode,
            )
            graph = attach_trace_pseudo_labels(graph, stats=stats, config=label_config)
            trace_graphs.append(graph)

    return trace_graphs


def relabel_trace_distillation_graphs(
    trace_graphs: list[HeteroData],
    solver_stats: pd.DataFrame,
    label_config: TraceLabelConfig | None = None,
) -> list[HeteroData]:
    if solver_stats.empty:
        return trace_graphs
    required_cols = {"cnf_id", "sample_id"}
    missing = required_cols.difference(solver_stats.columns)
    if missing:
        raise ValueError(f"solver_stats missing required columns: {sorted(missing)}")

    stats_by_key = {
        (int(row["cnf_id"]), int(row["sample_id"])): row
        for _, row in solver_stats.iterrows()
    }

    relabelled: list[HeteroData] = []
    for data in trace_graphs:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        sample_id = int(data.sample_id.item() if hasattr(data.sample_id, "item") else getattr(data, "sample_id", 0))
        stats = stats_by_key.get((cnf_id, sample_id))
        if stats is None:
            relabelled.append(data)
            continue
        relabelled.append(attach_trace_pseudo_labels(data, stats=stats, config=label_config))
    return relabelled


def _graph_int_attr(graph: HeteroData, name: str, default: int = 0) -> int:
    value = getattr(graph, name, default)
    if hasattr(value, "item"):
        return int(value.item())
    if isinstance(value, (list, tuple)):
        return _graph_int_attr(type("_Tmp", (), {name: value[0]})(), name, default)
    return int(value)


def _manifest_row_mapping(
    solver_stats: pd.DataFrame,
    manifest: pd.DataFrame,
) -> dict[int, pd.Series]:
    if not solver_stats.empty and "file" in solver_stats.columns and "cnf_path" in manifest.columns:
        by_path = {
            str(Path(str(row["cnf_path"])).resolve()): row
            for _, row in manifest.iterrows()
        }
        mapping: dict[int, pd.Series] = {}
        for cnf_id, group in solver_stats.groupby("cnf_id", sort=True):
            files = sorted({str(Path(path).resolve()) for path in group["file"].dropna().astype(str)})
            if len(files) != 1:
                continue
            row = by_path.get(files[0])
            if row is not None:
                mapping[int(cnf_id)] = row
        if mapping:
            return mapping
    return {int(idx): row for idx, row in manifest.iterrows()}


def _read_permutation(metadata_path: Path, expected_num_vars: int) -> list[int] | None:
    if not metadata_path.exists():
        return None
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    permutation = payload.get("permutation")
    sign_flips = payload.get("sign_flips")
    if not isinstance(permutation, list) or len(permutation) != expected_num_vars:
        return None
    if isinstance(sign_flips, list) and any(int(sign) != 1 for sign in sign_flips):
        return None
    return [int(value) for value in permutation]


def build_permutation_consistency_pairs(
    trace_graphs: list[HeteroData],
    solver_stats: pd.DataFrame,
    manifest: pd.DataFrame,
) -> list[PermutationConsistencyPair]:
    """Build base/permuted cached-graph pairs for adapter permutation consistency."""
    if not trace_graphs or solver_stats.empty or manifest.empty:
        return []
    manifest = manifest.copy()
    if "event_audit_role" in manifest.columns:
        manifest = manifest[manifest["event_audit_role"].fillna("event").astype(str) != "static_only"].copy()
    row_by_cnf = _manifest_row_mapping(solver_stats=solver_stats, manifest=manifest)
    graph_by_key: dict[tuple[str, str, int], HeteroData] = {}
    row_by_key: dict[tuple[str, str, int], pd.Series] = {}
    for graph in trace_graphs:
        cnf_id = _graph_int_attr(graph, "cnf_id")
        sample_id = _graph_int_attr(graph, "sample_id", default=0)
        row = row_by_cnf.get(cnf_id)
        if row is None:
            continue
        key = (str(row["base_instance_id"]), str(row["variant"]), sample_id)
        graph_by_key[key] = graph
        row_by_key[key] = row

    pairs: list[PermutationConsistencyPair] = []
    for key, perm_graph in sorted(graph_by_key.items()):
        base_instance_id, variant, sample_id = key
        if variant == "base":
            continue
        base_key = (base_instance_id, "base", sample_id)
        base_graph = graph_by_key.get(base_key)
        if base_graph is None:
            continue
        row = row_by_key[key]
        num_vars = int(perm_graph["var"].base_y.shape[0]) if hasattr(perm_graph["var"], "base_y") else int(perm_graph["var"].num_nodes)
        permutation = _read_permutation(Path(str(row.get("metadata_path", ""))), expected_num_vars=num_vars)
        if permutation is None:
            continue
        pairs.append(
            PermutationConsistencyPair(
                base_graph=base_graph,
                permuted_graph=perm_graph,
                permutation_old_to_new=torch.tensor([value - 1 for value in permutation], dtype=torch.long),
                family=str(row["family"]),
                base_instance_id=base_instance_id,
                permuted_instance_id=str(row["instance_id"]),
                variant=variant,
                sample_id=int(sample_id),
            )
        )
    return pairs


def trace_distillation_loss(
    pred_y: Tensor,
    target_y: Tensor,
    confidence: Tensor,
    base_y: Tensor | None = None,
    event_state: Tensor | None = None,
    var_batch: Tensor | None = None,
    valid_orbit_mask: Tensor | None = None,
    negative_guard_mask: Tensor | None = None,
    config: TraceLabelConfig | None = None,
) -> Tensor:
    if config is None:
        config = TraceLabelConfig()
    pred_y = pred_y.to(dtype=torch.float32)
    target_y = target_y.to(dtype=torch.float32, device=pred_y.device)
    confidence = confidence.to(dtype=torch.float32, device=pred_y.device).view(-1)
    if valid_orbit_mask is not None:
        valid_orbit_mask = _as_bool_mask(
            valid_orbit_mask,
            expected_rows=pred_y.shape[0],
            device=pred_y.device,
            name="valid_orbit_mask",
        )
    if negative_guard_mask is not None:
        negative_guard_mask = _as_bool_mask(
            negative_guard_mask,
            expected_rows=pred_y.shape[0],
            device=pred_y.device,
            name="negative_guard_mask",
        )

    output_weights = torch.tensor(
        [float(config.rho_loss_weight), float(config.mu_loss_weight)],
        dtype=torch.float32,
        device=pred_y.device,
    )
    squared_error = (pred_y[:, :2] - target_y[:, :2]).pow(2) * output_weights
    per_var_loss = squared_error.sum(dim=1)
    effective_confidence = confidence
    if bool(config.valid_orbit_only_distillation):
        if valid_orbit_mask is None:
            effective_confidence = torch.zeros_like(confidence)
        else:
            effective_confidence = confidence * valid_orbit_mask.to(dtype=torch.float32)
    denom = effective_confidence.sum()
    if denom <= 0:
        base_loss = per_var_loss.mean() * 0.0
    else:
        base_loss = (per_var_loss * effective_confidence).sum() / denom.clamp_min(1.0e-6)
    valid_loss = valid_orbit_identity_loss(
        pred_y=pred_y,
        target_y=target_y,
        confidence=confidence,
        valid_orbit_mask=valid_orbit_mask,
        config=config,
    )
    guard_loss = negative_guard_loss(
        pred_y=pred_y,
        base_y=base_y,
        negative_guard_mask=negative_guard_mask,
        valid_orbit_mask=valid_orbit_mask,
        var_batch=var_batch,
        config=config,
    )
    magnitude_loss = adapter_delta_magnitude_loss(
        pred_y=pred_y,
        base_y=base_y,
        config=config,
    )
    negative_loss = no_activity_negative_loss(
        pred_y=pred_y,
        base_y=base_y,
        event_state=event_state,
        var_batch=var_batch,
        config=config,
    )
    return base_loss + valid_loss + guard_loss + magnitude_loss + negative_loss


def _as_bool_mask(mask: Tensor, expected_rows: int, device: torch.device, name: str) -> Tensor:
    mask = mask.to(device=device).view(-1)
    if mask.numel() != int(expected_rows):
        raise ValueError(f"{name} length {mask.numel()} does not match variable rows {expected_rows}")
    if mask.dtype == torch.bool:
        return mask
    return mask.to(dtype=torch.float32) > 0.0


def _graph_level_no_valid_mask(
    valid_orbit_mask: Tensor,
    var_batch: Tensor | None = None,
) -> Tensor:
    valid_orbit_mask = valid_orbit_mask.to(dtype=torch.bool)
    if var_batch is None:
        return torch.full_like(valid_orbit_mask, not bool(valid_orbit_mask.any()), dtype=torch.bool)
    var_batch = var_batch.to(dtype=torch.long, device=valid_orbit_mask.device).view(-1)
    if var_batch.numel() != valid_orbit_mask.numel():
        raise ValueError(f"var_batch length {var_batch.numel()} does not match valid_orbit_mask rows {valid_orbit_mask.numel()}")
    num_graphs = int(var_batch.max().item()) + 1 if var_batch.numel() > 0 else 0
    graph_has_valid = torch.zeros(num_graphs, dtype=torch.bool, device=valid_orbit_mask.device)
    for graph_id in range(num_graphs):
        graph_has_valid[graph_id] = bool(valid_orbit_mask[var_batch == graph_id].any())
    return ~graph_has_valid[var_batch]


def valid_orbit_identity_loss(
    pred_y: Tensor,
    target_y: Tensor,
    confidence: Tensor,
    valid_orbit_mask: Tensor | None,
    config: TraceLabelConfig,
) -> Tensor:
    weight = float(config.valid_orbit_identity_weight)
    if weight <= 0.0 or valid_orbit_mask is None:
        return pred_y.sum() * 0.0
    pred_y = pred_y.to(dtype=torch.float32)
    target_y = target_y.to(dtype=torch.float32, device=pred_y.device)
    confidence = confidence.to(dtype=torch.float32, device=pred_y.device).view(-1)
    mask = _as_bool_mask(valid_orbit_mask, expected_rows=pred_y.shape[0], device=pred_y.device, name="valid_orbit_mask")
    if not bool(mask.any()):
        return pred_y.sum() * 0.0
    output_weights = torch.tensor(
        [
            float(config.valid_orbit_identity_rho_loss_weight),
            float(config.valid_orbit_identity_mu_loss_weight),
        ],
        dtype=torch.float32,
        device=pred_y.device,
    )
    squared_error = (pred_y[:, :2] - target_y[:, :2]).pow(2) * output_weights
    per_var_loss = squared_error.sum(dim=1)
    weights = confidence * mask.to(dtype=torch.float32)
    denom = weights.sum()
    if denom <= 0:
        return pred_y.sum() * 0.0
    return weight * (per_var_loss * weights).sum() / denom.clamp_min(1.0e-6)


def negative_guard_loss(
    pred_y: Tensor,
    base_y: Tensor | None,
    negative_guard_mask: Tensor | None,
    valid_orbit_mask: Tensor | None,
    var_batch: Tensor | None,
    config: TraceLabelConfig,
) -> Tensor:
    weight = float(config.negative_guard_weight)
    if weight <= 0.0 or base_y is None:
        return pred_y.sum() * 0.0
    pred_y = pred_y.to(dtype=torch.float32)
    base_y = base_y.to(dtype=torch.float32, device=pred_y.device)
    mask = torch.zeros(pred_y.shape[0], dtype=torch.bool, device=pred_y.device)
    if negative_guard_mask is not None:
        mask |= _as_bool_mask(
            negative_guard_mask,
            expected_rows=pred_y.shape[0],
            device=pred_y.device,
            name="negative_guard_mask",
        )
    if bool(config.negative_guard_no_valid_orbit) and valid_orbit_mask is not None:
        valid_orbit_mask = _as_bool_mask(
            valid_orbit_mask,
            expected_rows=pred_y.shape[0],
            device=pred_y.device,
            name="valid_orbit_mask",
        )
        if var_batch is not None:
            var_batch = var_batch.to(device=pred_y.device)
        mask |= _graph_level_no_valid_mask(valid_orbit_mask, var_batch=var_batch)
    if not bool(mask.any()):
        return pred_y.sum() * 0.0
    output_weights = torch.tensor(
        [
            float(config.negative_guard_rho_loss_weight),
            float(config.negative_guard_mu_loss_weight),
        ],
        dtype=torch.float32,
        device=pred_y.device,
    )
    squared_error = (pred_y[:, :2] - base_y[:, :2]).pow(2) * output_weights
    per_var_loss = squared_error.sum(dim=1)
    return weight * per_var_loss[mask].mean()


def adapter_delta_magnitude_loss(
    pred_y: Tensor,
    base_y: Tensor | None,
    config: TraceLabelConfig,
) -> Tensor:
    weight = float(config.adapter_delta_magnitude_weight)
    if weight <= 0.0 or base_y is None:
        return pred_y.sum() * 0.0
    pred_y = pred_y.to(dtype=torch.float32)
    base_y = base_y.to(dtype=torch.float32, device=pred_y.device)
    margin = max(float(config.adapter_delta_magnitude_margin), 0.0)
    output_weights = torch.tensor(
        [
            float(config.adapter_delta_magnitude_rho_loss_weight),
            float(config.adapter_delta_magnitude_mu_loss_weight),
        ],
        dtype=torch.float32,
        device=pred_y.device,
    )
    excess = (pred_y[:, :2] - base_y[:, :2]).abs().sub(margin).clamp_min(0.0)
    per_var_loss = (excess.pow(2) * output_weights).sum(dim=1)
    return weight * per_var_loss.mean()


def no_activity_variable_mask(
    event_state: Tensor,
    var_batch: Tensor | None = None,
    gate_indices: list[int] | None = None,
    gate_eps: float = 1.0e-9,
) -> Tensor:
    event_state = event_state.to(dtype=torch.float32)
    indices = [int(index) for index in (gate_indices or []) if int(index) < event_state.shape[1]]
    if not indices:
        return torch.zeros(event_state.shape[0], dtype=torch.bool, device=event_state.device)
    evidence = event_state[:, indices].clamp_min(0.0).max(dim=1).values
    if var_batch is None:
        return torch.full(
            (event_state.shape[0],),
            bool(evidence.max() <= float(gate_eps)),
            dtype=torch.bool,
            device=event_state.device,
        )
    var_batch = var_batch.to(dtype=torch.long, device=event_state.device).view(-1)
    if var_batch.numel() != evidence.numel():
        raise ValueError(f"var_batch length {var_batch.numel()} does not match event_state rows {event_state.shape[0]}")
    num_graphs = int(var_batch.max().item()) + 1 if var_batch.numel() > 0 else 0
    graph_evidence = torch.zeros(num_graphs, dtype=torch.float32, device=event_state.device)
    for graph_id in range(num_graphs):
        graph_values = evidence[var_batch == graph_id]
        if graph_values.numel() > 0:
            graph_evidence[graph_id] = graph_values.max()
    return graph_evidence[var_batch] <= float(gate_eps)


def no_activity_negative_loss(
    pred_y: Tensor,
    base_y: Tensor | None,
    event_state: Tensor | None,
    var_batch: Tensor | None,
    config: TraceLabelConfig,
) -> Tensor:
    weight = float(config.no_activity_negative_weight)
    if weight <= 0.0 or base_y is None or event_state is None:
        return pred_y.sum() * 0.0
    pred_y = pred_y.to(dtype=torch.float32)
    base_y = base_y.to(dtype=torch.float32, device=pred_y.device)
    event_state = event_state.to(dtype=torch.float32, device=pred_y.device)
    if var_batch is not None:
        var_batch = var_batch.to(device=pred_y.device)
    mask = no_activity_variable_mask(
        event_state=event_state,
        var_batch=var_batch,
        gate_indices=list(config.no_activity_gate_indices),
        gate_eps=float(config.no_activity_gate_eps),
    )
    if not bool(mask.any()):
        return pred_y.sum() * 0.0
    output_weights = torch.tensor(
        [
            float(config.no_activity_negative_rho_loss_weight),
            float(config.no_activity_negative_mu_loss_weight),
        ],
        dtype=torch.float32,
        device=pred_y.device,
    )
    squared_error = (pred_y[:, :2] - base_y[:, :2]).pow(2) * output_weights
    per_var_loss = squared_error.sum(dim=1)
    return weight * per_var_loss[mask].mean()


def align_new_to_old(tensor: Tensor, permutation_old_to_new_zero_based: Tensor) -> Tensor:
    if tensor.dim() == 1:
        tensor = tensor.view(-1, 1)
    indices = permutation_old_to_new_zero_based.to(dtype=torch.long, device=tensor.device).view(-1)
    if tensor.shape[0] != indices.numel():
        raise ValueError(f"tensor has {tensor.shape[0]} variables but permutation has {indices.numel()} entries")
    return tensor.index_select(0, indices)


def permutation_consistency_loss(
    model: torch.nn.Module,
    pairs: list[PermutationConsistencyPair],
    device: torch.device | str,
    config: TraceLabelConfig,
) -> Tensor:
    weight = float(config.permutation_consistency_weight)
    delta_weight = float(config.permutation_delta_consistency_weight)
    params = list(model.parameters())
    zero = params[0].sum() * 0.0 if params else torch.tensor(0.0, device=device)
    if (weight <= 0.0 and delta_weight <= 0.0) or not pairs:
        return zero
    max_pairs = config.permutation_consistency_max_pairs_per_epoch
    selected = pairs[: int(max_pairs)] if max_pairs is not None and int(max_pairs) > 0 else pairs
    if not selected:
        return zero

    output_weights = torch.tensor(
        [
            float(config.permutation_consistency_rho_loss_weight),
            float(config.permutation_consistency_mu_loss_weight),
        ],
        dtype=torch.float32,
        device=device,
    )
    delta_output_weights = torch.tensor(
        [
            float(config.permutation_delta_consistency_rho_loss_weight),
            float(config.permutation_delta_consistency_mu_loss_weight),
        ],
        dtype=torch.float32,
        device=device,
    )
    pair_losses: list[Tensor] = []
    for pair in selected:
        base_batch = next(iter(DataLoader(dataset=[pair.base_graph], batch_size=1, num_workers=0, shuffle=False))).to(device)
        perm_batch = next(iter(DataLoader(dataset=[pair.permuted_graph], batch_size=1, num_workers=0, shuffle=False))).to(device)
        base_y = model(base_batch)[:, :2].to(dtype=torch.float32)
        perm_y = model(perm_batch)[:, :2].to(dtype=torch.float32)
        losses: list[Tensor] = []
        if weight > 0.0:
            aligned_perm_y = align_new_to_old(perm_y, pair.permutation_old_to_new)
            squared_error = (aligned_perm_y - base_y).pow(2) * output_weights
            losses.append(weight * squared_error.sum(dim=1).mean())
        if delta_weight > 0.0 and hasattr(base_batch["var"], "base_y") and hasattr(perm_batch["var"], "base_y"):
            base_static_y = base_batch["var"].base_y[:, :2].to(dtype=torch.float32, device=base_y.device)
            perm_static_y = perm_batch["var"].base_y[:, :2].to(dtype=torch.float32, device=perm_y.device)
            base_delta = base_y - base_static_y
            perm_delta = perm_y - perm_static_y
            aligned_perm_delta = align_new_to_old(perm_delta, pair.permutation_old_to_new)
            squared_delta_error = (aligned_perm_delta - base_delta).pow(2) * delta_output_weights
            losses.append(delta_weight * squared_delta_error.sum(dim=1).mean())
        if losses:
            pair_losses.append(torch.stack(losses).sum())
    if not pair_losses:
        return zero
    return torch.stack(pair_losses).mean()


def freeze_non_adapter_parameters(
    model: torch.nn.Module,
    adapter_train_mode: str = "adapter",
) -> None:
    if adapter_train_mode not in {"adapter", "polarity_gate"}:
        raise ValueError(f"Unknown trace distillation adapter_train_mode {adapter_train_mode}")
    has_adapter_param = False
    for name, param in model.named_parameters():
        if adapter_train_mode == "polarity_gate":
            train_adapter = "event_adapter_polarity_gate" in name
        else:
            train_adapter = "event_adapter" in name
        param.requires_grad = train_adapter
        has_adapter_param = has_adapter_param or train_adapter
    if not has_adapter_param:
        raise ValueError("Cannot freeze for trace distillation: model has no event_adapter parameters")


def train_trace_distillation_epoch(
    model: torch.nn.Module,
    loader,
    optimizer: torch.optim.Optimizer,
    device: torch.device | str = "cpu",
    config: TraceLabelConfig | None = None,
    permutation_pairs: list[PermutationConsistencyPair] | None = None,
    use_amp: bool = False,
) -> dict[str, float]:
    if config is None:
        config = TraceLabelConfig()
    model.to(device)
    model.train()
    amp_enabled = use_amp and torch.cuda.is_available() and str(device).startswith("cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)

    total_loss = 0.0
    total_weight = 0.0
    num_batches = 0
    for data in loader:
        data = data.to(device)
        optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda", enabled=amp_enabled):
            pred_y = model(data)
            loss = trace_distillation_loss(
                pred_y,
                data["var"].trace_target_y,
                data["var"].trace_confidence,
                base_y=data["var"].base_y if hasattr(data["var"], "base_y") else None,
                event_state=data["var"].event_state if hasattr(data["var"], "event_state") else None,
                var_batch=data["var"].batch if hasattr(data["var"], "batch") else None,
                valid_orbit_mask=data["var"].valid_orbit_mask if hasattr(data["var"], "valid_orbit_mask") else None,
                negative_guard_mask=data["var"].negative_guard_mask if hasattr(data["var"], "negative_guard_mask") else None,
                config=config,
            )
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        batch_weight = float(data["var"].trace_confidence.sum().detach().cpu().item())
        total_loss += float(loss.detach().cpu().item()) * max(batch_weight, 1.0)
        total_weight += max(batch_weight, 1.0)
        num_batches += 1

    consistency_value = 0.0
    if permutation_pairs:
        optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda", enabled=amp_enabled):
            consistency = permutation_consistency_loss(
                model=model,
                pairs=permutation_pairs,
                device=device,
                config=config,
            )
        scaler.scale(consistency).backward()
        scaler.step(optimizer)
        scaler.update()
        consistency_value = float(consistency.detach().cpu().item())

    mean_distillation_loss = total_loss / max(total_weight, 1.0)
    return {
        "loss": mean_distillation_loss + consistency_value,
        "distillation_loss": mean_distillation_loss,
        "batches": float(num_batches),
        "permutation_consistency_loss": consistency_value,
    }
