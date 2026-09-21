from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import pandas as pd


SOLVED_RESULTS = {"SATISFIABLE", "UNSATISFIABLE"}


@dataclass(frozen=True)
class CounterfactualLabelSpec:
    positive_speedup_ratio: float = 0.95
    positive_min_base_time: float = 0.0
    positive_min_delta_time: float = 0.0
    negative_slowdown_ratio: float = 1.05
    negative_min_delta_time: float = 0.0
    easy_base_time_cutoff: float = 0.0
    easy_negative_delta_time: float = 0.0
    speedup_weight: float = 1.0
    easy_slowdown_weight: float = 1.0
    lost_weight: float = 1.0
    neutral_weight: float = 1.0


def _parse_points(value: object) -> list[int]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_values = value.split(",")
    elif isinstance(value, Iterable):
        raw_values = list(value)
    else:
        raw_values = [value]
    points = []
    for raw in raw_values:
        if raw is None or str(raw).strip() == "":
            continue
        points.append(int(raw))
    return points


def intervention_conflict_points(cfg) -> list[int]:
    warmup = _parse_points(getattr(cfg, "warmup_conflicts", None))
    intervention = _parse_points(getattr(cfg, "intervention_conflicts", None))
    return sorted(set(warmup + intervention))


def _result_is_solved(result: object) -> bool:
    return str(result) in SOLVED_RESULTS


def _class_row(row: pd.Series, spec: CounterfactualLabelSpec) -> tuple[str, str, int, float]:
    if _result_is_solved(row.get("warmup_result")):
        return "warmup_solved", "warmup_solved", -2, 0.0

    base_solved = _result_is_solved(row.get("base_result"))
    adapter_solved = _result_is_solved(row.get("adapter_result"))
    base_time = float(row.get("base_time", 0.0))
    adapter_time = float(row.get("adapter_time", 0.0))
    delta = adapter_time - base_time

    if not base_solved and adapter_solved:
        return "positive", "recovered_timeout", 1, float(spec.speedup_weight)
    if base_solved and not adapter_solved:
        return "negative", "lost_solution", 0, float(spec.lost_weight)
    if base_solved and adapter_solved:
        speedup = base_time - adapter_time
        ratio = adapter_time / base_time if base_time > 0.0 else 1.0
        hard_enough = base_time >= float(spec.positive_min_base_time)
        if spec.easy_base_time_cutoff > 0.0:
            hard_enough = hard_enough and base_time >= float(spec.easy_base_time_cutoff)
        if ratio <= float(spec.positive_speedup_ratio) and speedup >= float(spec.positive_min_delta_time) and hard_enough:
            return "positive", "hard_speedup", 1, float(spec.speedup_weight)
        if (
            spec.easy_base_time_cutoff > 0.0
            and base_time <= float(spec.easy_base_time_cutoff)
            and delta >= float(spec.easy_negative_delta_time)
        ):
            return "negative", "easy_slowdown", 0, float(spec.easy_slowdown_weight)
        if ratio >= float(spec.negative_slowdown_ratio) and delta >= float(spec.negative_min_delta_time):
            return "negative", "slowdown", 0, float(spec.easy_slowdown_weight)

    return "neutral", "neutral", -1, float(spec.neutral_weight)


def _label_rows(frame: pd.DataFrame, spec: CounterfactualLabelSpec) -> pd.DataFrame:
    out = frame.copy()
    labels = out.apply(lambda row: _class_row(row, spec), axis=1)
    out["counterfactual_class"] = [item[0] for item in labels]
    out["counterfactual_reason"] = [item[1] for item in labels]
    out["counterfactual_class_code"] = [item[2] for item in labels]
    out["counterfactual_weight"] = [item[3] for item in labels]
    return out


def _cnf_id(graph) -> int:
    value = getattr(graph, "cnf_id")
    if hasattr(value, "item"):
        return int(value.item())
    if isinstance(value, (list, tuple)) and value:
        return int(value[0])
    return int(value)


def _frame_by_cnf(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    return frame.sort_values(["cnf_id", "sample_id"] if "sample_id" in frame.columns else ["cnf_id"]).drop_duplicates("cnf_id").set_index("cnf_id")


def _multi_point_frame(
    points: list[int],
    stats_by_point: dict[int, pd.DataFrame],
    graphs_by_point: dict[int, list],
    feature_frames_by_point: dict[int, pd.DataFrame],
    feature_names: list[str],
) -> pd.DataFrame:
    points = sorted(set(int(point) for point in points))
    final_point = points[-1]
    cnf_ids = set()
    for frame in stats_by_point.values():
        if frame is not None and "cnf_id" in frame.columns:
            cnf_ids.update(int(value) for value in frame["cnf_id"].tolist())
    for graphs in graphs_by_point.values():
        cnf_ids.update(_cnf_id(graph) for graph in graphs)

    stats_index = {point: _frame_by_cnf(stats_by_point.get(point)) for point in points}
    feature_index = {point: _frame_by_cnf(feature_frames_by_point.get(point)) for point in points}
    rows = []
    for cnf_id in sorted(cnf_ids):
        row = {"cnf_id": cnf_id}
        solved_by_point = {}
        for point in points:
            prefix = f"warmup_c{point}"
            stats = stats_index[point]
            if cnf_id in stats.index:
                stat_row = stats.loc[cnf_id]
                for column, value in stat_row.items():
                    if column not in {"cnf_id", "sample_id"}:
                        row[f"{prefix}_{column}"] = value
                solved_by_point[point] = _result_is_solved(stat_row.get("Result"))
            else:
                solved_by_point[point] = False
            features = feature_index[point]
            if cnf_id in features.index:
                feature_row = features.loc[cnf_id]
                for name in feature_names:
                    if name in feature_row:
                        row[f"{prefix}_{name}"] = feature_row[name]
            row[f"{prefix}_solved"] = solved_by_point[point]

        for prev, current in zip(points, points[1:]):
            for name in set(feature_names + ["propagations", "decisions", "conflicts", "CPU time"]):
                current_key = f"warmup_c{current}_{name}"
                prev_key = f"warmup_c{prev}_{name}"
                if current_key in row and prev_key in row:
                    row[f"warmup_c{current}_minus_warmup_c{prev}_{name}"] = row[current_key] - row[prev_key]
        row["solved_before_final_intervention"] = any(solved_by_point[point] for point in points if point < final_point)
        rows.append(row)
    return pd.DataFrame(rows)


def _disable_adapter_gates(model, cfg) -> None:
    counterfactual = getattr(cfg, "counterfactual", {})
    preserve_names = bool(counterfactual.get("preserve_selector_feature_names", False))
    if counterfactual.get("disable_adapter_selector", False) and not preserve_names:
        model.event_adapter_selector_feature_names = []
    if counterfactual.get("disable_adapter_base_rho_gate", False):
        model.event_adapter_base_rho_gate_threshold = None
    if counterfactual.get("disable_adapter_graph_gate", False):
        model.event_adapter_graph_gate_indices = []
        model.event_adapter_graph_gate_threshold = None


@contextmanager
def _preserve_model_selector_names(model) -> Iterator[None]:
    names = list(getattr(model, "event_adapter_selector_feature_names", []))
    model.event_adapter_selector_feature_names = []
    try:
        yield
    finally:
        model.event_adapter_selector_feature_names = names
