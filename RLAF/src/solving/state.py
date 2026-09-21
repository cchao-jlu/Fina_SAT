from __future__ import annotations

from copy import copy
import math

import pandas as pd
import torch
from torch_geometric.data import HeteroData


GLOBAL_STATE_DIM = 6
EVENT_VAR_STATE_DIM = 5
EVENT_VAR_STATE_DIM_ENHANCED = 20
EVENT_VAR_STATE_DIM_POLARITY = 29


def result_to_code(result: str | None) -> float:
    if result == "SATISFIABLE":
        return 1.0
    if result == "UNSATISFIABLE":
        return -1.0
    return 0.0


def safe_log1p_stat(stats: dict, key: str) -> float:
    value = stats.get(key, 0.0)
    if value is None or pd.isna(value):
        value = 0.0
    value = float(value)
    if not math.isfinite(value) or value < 0.0:
        value = 0.0
    return float(torch.log1p(torch.tensor(value)).item())


def solver_stats_to_global_state(stats: dict | pd.Series) -> torch.Tensor:
    if isinstance(stats, pd.Series):
        stats = stats.to_dict()

    return torch.tensor(
        [
            safe_log1p_stat(stats, "decisions"),
            safe_log1p_stat(stats, "conflicts"),
            safe_log1p_stat(stats, "propagations"),
            safe_log1p_stat(stats, "restarts"),
            safe_log1p_stat(stats, "CPU time"),
            result_to_code(stats.get("Result")),
        ],
        dtype=torch.float32,
    )


def event_state_dim(feature_mode: str = "legacy") -> int:
    if feature_mode == "legacy":
        return EVENT_VAR_STATE_DIM
    if feature_mode == "enhanced":
        return EVENT_VAR_STATE_DIM_ENHANCED
    if feature_mode == "polarity":
        return EVENT_VAR_STATE_DIM_POLARITY
    raise ValueError(f"Unknown event state feature mode {feature_mode!r}")


def _event_values(stats: dict, key: str, num_vars: int) -> torch.Tensor:
    value = stats.get(key)
    if isinstance(value, pd.Series):
        value = value.tolist()
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return torch.zeros(num_vars, dtype=torch.float32)
    tensor = torch.as_tensor(value, dtype=torch.float32).flatten()
    if tensor.numel() < num_vars:
        padded = torch.zeros(num_vars, dtype=torch.float32)
        padded[: tensor.numel()] = tensor
        tensor = padded
    elif tensor.numel() > num_vars:
        tensor = tensor[:num_vars]
    return torch.nan_to_num(tensor, nan=0.0, posinf=0.0, neginf=0.0).clamp_min_(0.0)


def _rank01(values: torch.Tensor) -> torch.Tensor:
    if values.numel() <= 1 or torch.all(values == values[0]):
        return torch.zeros_like(values)
    order = torch.argsort(values, stable=True)
    ranks = torch.zeros_like(values)
    ranks[order] = torch.arange(values.numel(), dtype=torch.float32, device=values.device)
    return ranks / float(values.numel() - 1)


def _safe_fraction(numerator: torch.Tensor, denominator: torch.Tensor) -> torch.Tensor:
    return torch.where(denominator > 0.0, numerator / denominator.clamp_min(1.0e-9), torch.zeros_like(numerator))


def _sum_rate(values: torch.Tensor) -> torch.Tensor:
    return (values / values.sum().clamp_min(1.0)).clamp(0.0, 1.0)


def _event_feature_columns(stats: dict, num_vars: int) -> dict[str, torch.Tensor]:
    raw = {
        "decisions": _event_values(stats, "event_var_decisions", num_vars),
        "propagations": _event_values(stats, "event_var_propagations", num_vars),
        "conflict_lits": _event_values(stats, "event_var_conflict_lits", num_vars),
        "learnt_lits": _event_values(stats, "event_var_learnt_lits", num_vars),
        "activity": _event_values(stats, "event_var_activity", num_vars),
    }
    return raw


def solver_stats_to_var_event_state(
    stats: dict | pd.Series,
    num_vars: int,
    feature_mode: str = "legacy",
) -> torch.Tensor:
    if isinstance(stats, pd.Series):
        stats = stats.to_dict()
    num_vars = int(num_vars)
    raw = _event_feature_columns(stats, num_vars=num_vars)
    base = torch.stack(
        [
            torch.log1p(raw["decisions"]),
            torch.log1p(raw["propagations"]),
            torch.log1p(raw["conflict_lits"]),
            torch.log1p(raw["learnt_lits"]),
            torch.log1p(raw["activity"]),
        ],
        dim=1,
    )
    if feature_mode == "legacy":
        return base

    raw_stack = torch.stack(
        [
            raw["decisions"],
            raw["propagations"],
            raw["conflict_lits"],
            raw["learnt_lits"],
            raw["activity"],
        ],
        dim=1,
    )
    rate_stack = torch.stack(
        [
            _sum_rate(raw["decisions"]),
            _sum_rate(raw["propagations"]),
            _sum_rate(raw["conflict_lits"]),
            _sum_rate(raw["learnt_lits"]),
            _sum_rate(raw["activity"]),
        ],
        dim=1,
    )
    enhanced = torch.cat(
        [
            base,
            torch.log1p(raw_stack),
            rate_stack,
            torch.stack(
                [
                    _rank01(raw["decisions"]),
                    _rank01(raw["propagations"]),
                    _rank01(raw["conflict_lits"]),
                    _rank01(raw["learnt_lits"]),
                    _rank01(raw["activity"]),
                ],
                dim=1,
            ),
        ],
        dim=1,
    )
    if feature_mode == "enhanced":
        return enhanced
    if feature_mode != "polarity":
        raise ValueError(f"Unknown event state feature mode {feature_mode!r}")

    pos_conflict = _event_values(stats, "event_var_pos_conflict_lits", num_vars)
    neg_conflict = _event_values(stats, "event_var_neg_conflict_lits", num_vars)
    pos_prop = _event_values(stats, "event_var_pos_propagations", num_vars)
    neg_prop = _event_values(stats, "event_var_neg_propagations", num_vars)
    pos_assign = _event_values(stats, "event_var_pos_assignments", num_vars)
    neg_assign = _event_values(stats, "event_var_neg_assignments", num_vars)

    conflict_total = pos_conflict + neg_conflict
    prop_total = pos_prop + neg_prop
    assign_total = pos_assign + neg_assign
    conflict_bias = _safe_fraction(pos_conflict - neg_conflict, conflict_total)
    propagation_bias = _safe_fraction(pos_prop - neg_prop, prop_total)
    assignment_bias = _safe_fraction(pos_assign - neg_assign, assign_total)
    polarity = torch.stack(
        [
            _safe_fraction(pos_conflict, conflict_total),
            conflict_bias,
            assignment_bias,
            _safe_fraction(neg_conflict, conflict_total),
            propagation_bias,
            _safe_fraction(pos_prop, prop_total),
            _safe_fraction(neg_prop, prop_total),
            _safe_fraction(pos_assign, assign_total),
            assignment_bias,
        ],
        dim=1,
    )
    return torch.cat([enhanced, polarity], dim=1)


def attach_global_state(
    data: HeteroData,
    stats: dict | pd.Series,
    global_state_dim: int,
) -> HeteroData:
    data = copy(data)
    global_state = solver_stats_to_global_state(stats)
    if global_state_dim != global_state.shape[0]:
        raise ValueError(
            f"feedback refinement expected global_state_dim={global_state.shape[0]}, "
            f"got model.global_state_dim={global_state_dim}"
        )
    data.global_state = global_state
    return data


def attach_global_state_batch(
    data_list: list[HeteroData],
    solver_stats: pd.DataFrame,
    global_state_dim: int,
) -> list[HeteroData]:
    stats_by_cnf = {
        int(cnf_id): group.iloc[0]
        for cnf_id, group in solver_stats.groupby("cnf_id", sort=False)
    }

    updated = []
    for data in data_list:
        cnf_id = int(data.cnf_id.item())
        stats = stats_by_cnf.get(cnf_id)
        if stats is None:
            updated.append(copy(data))
            continue
        updated.append(attach_global_state(data, stats=stats, global_state_dim=global_state_dim))
    return updated


def attach_var_event_state(
    data: HeteroData,
    stats: dict | pd.Series,
    var_state_dim: int,
    momentum: float = 0.0,
    feature_mode: str = "legacy",
) -> HeteroData:
    data = copy(data)
    num_vars = int(getattr(data["var"], "num_nodes", data["lit"].num_nodes // 2))
    event_state = solver_stats_to_var_event_state(stats, num_vars=num_vars, feature_mode=feature_mode)
    if int(var_state_dim) != event_state.shape[1]:
        raise ValueError(
            f"event state feature_mode={feature_mode} has dim {event_state.shape[1]}, "
            f"got var_state_dim={var_state_dim}"
        )
    if hasattr(data["var"], "event_state") and float(momentum) > 0.0:
        previous = data["var"].event_state.to(dtype=torch.float32)
        if previous.shape == event_state.shape:
            event_state = float(momentum) * previous + (1.0 - float(momentum)) * event_state
    data["var"].num_nodes = num_vars
    data["var"].event_state = event_state
    data["var"].event_memory = event_state
    return data


def attach_var_event_state_batch(
    data_list: list[HeteroData],
    solver_stats: pd.DataFrame,
    var_state_dim: int,
    momentum: float = 0.0,
    feature_mode: str = "legacy",
) -> list[HeteroData]:
    stats_by_cnf = {
        int(cnf_id): group.sort_values("sample_id").iloc[0]
        for cnf_id, group in solver_stats.groupby("cnf_id", sort=False)
    }

    updated = []
    for data in data_list:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        stats = stats_by_cnf.get(cnf_id)
        if stats is None:
            updated.append(copy(data))
            continue
        updated.append(
            attach_var_event_state(
                data,
                stats=stats,
                var_state_dim=var_state_dim,
                momentum=momentum,
                feature_mode=feature_mode,
            )
        )
    return updated
