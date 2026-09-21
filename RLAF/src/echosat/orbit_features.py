from __future__ import annotations

from copy import copy
from dataclasses import dataclass
import math
import warnings

import pandas as pd
import torch
from torch_geometric.data import HeteroData


STRUCTURE_CATEGORIES = (
    "unknown",
    "row_column",
    "bandwidth_cardinality",
    "grid_or_torus",
    "graph_coloring",
    "complete_graph_parity",
    "none",
)

_VARIABLE_COLUMNS = {
    "variable_id",
    "orbit_index",
    "orbit_size",
    "structure_type",
    "orbit_confidence",
    "valid_orbit_mask",
}
_STORE_KEY_COLUMNS = {"base_instance_id", "variant"}
_METADATA_COLUMNS = {"cnf_id", "base_instance_id", "variant"}


def _require_columns(frame: pd.DataFrame, required: set[str], table_name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{table_name} missing required columns: {missing}")


def _integer(value: object, name: str, *, minimum: int) -> int:
    if isinstance(value, (bool, torch.Tensor)):
        raise ValueError(f"{name} must be an integer")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise ValueError(f"{name} must be an integer")
    integer = int(numeric)
    if integer < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return integer


def _confidence(value: object) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("orbit_confidence must be numeric") from exc
    if not math.isfinite(confidence):
        raise ValueError("orbit_confidence contains nonfinite values")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("orbit_confidence must be between 0 and 1")
    return confidence


def _strict_bool(value: object, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if hasattr(value, "item"):
        scalar = value.item()
        if isinstance(scalar, bool):
            return scalar
    raise ValueError(f"{name} must contain bool values")


def _structure(value: object) -> str:
    structure = str(value)
    if structure not in STRUCTURE_CATEGORIES:
        warnings.warn(
            f"unknown structure_type {structure!r}; mapping to 'unknown'",
            UserWarning,
            stacklevel=3,
        )
        return "unknown"
    return structure


def _is_random_control(row: pd.Series) -> bool:
    control_values = {
        str(row.get(column, ""))
        for column in ("control_type", "control_type_metadata", "control_type_variable")
    }
    family_values = {
        str(row.get(column, ""))
        for column in ("family", "family_metadata", "family_variable")
    }
    return "non_symmetric_control" in control_values or "random_3sat_control" in family_values


def _normalize_rows(rows: pd.DataFrame, num_vars: int) -> pd.DataFrame:
    _require_columns(rows, _VARIABLE_COLUMNS, "variable_rows")
    if rows.empty:
        raise ValueError(f"variable rows must cover variable IDs 1..{num_vars}")

    normalized = rows.copy()
    normalized["variable_id"] = [
        _integer(value, "variable_id", minimum=1) for value in normalized["variable_id"]
    ]
    if normalized["variable_id"].duplicated().any():
        duplicates = sorted(normalized.loc[normalized["variable_id"].duplicated(False), "variable_id"].unique())
        raise ValueError(f"duplicate variable_id values: {duplicates}")
    out_of_range = normalized.loc[normalized["variable_id"] > num_vars, "variable_id"].tolist()
    if out_of_range:
        raise ValueError(f"variable_id out of range for num_vars={num_vars}: {out_of_range}")
    expected_ids = list(range(1, num_vars + 1))
    actual_ids = sorted(normalized["variable_id"].tolist())
    if actual_ids != expected_ids:
        raise ValueError(f"variable rows must cover variable IDs 1..{num_vars}")

    normalized["orbit_index"] = [
        _integer(value, "orbit_index", minimum=0) for value in normalized["orbit_index"]
    ]
    normalized["orbit_size"] = [
        _integer(value, "orbit_size", minimum=0) for value in normalized["orbit_size"]
    ]
    normalized["orbit_confidence"] = [
        _confidence(value) for value in normalized["orbit_confidence"]
    ]
    normalized["valid_orbit_mask"] = [
        _strict_bool(value, "valid_orbit_mask") for value in normalized["valid_orbit_mask"]
    ]
    normalized["structure_type"] = [_structure(value) for value in normalized["structure_type"]]

    random_mask = normalized.apply(_is_random_control, axis=1)
    normalized.loc[random_mask, "valid_orbit_mask"] = False
    normalized.loc[random_mask, "orbit_confidence"] = 0.0

    for orbit_index, group in normalized.groupby("orbit_index", sort=False):
        valid_values = group["valid_orbit_mask"].unique().tolist()
        if len(valid_values) > 1:
            raise ValueError(f"inconsistent valid_orbit_mask for orbit_index={orbit_index}")
        if group["orbit_size"].nunique() != 1:
            raise ValueError(f"inconsistent orbit_size for orbit_index={orbit_index}")
        declared_size = int(group["orbit_size"].iloc[0])
        if bool(valid_values[0]) and declared_size != len(group):
            raise ValueError(
                f"orbit_size for orbit_index={orbit_index} is {declared_size}, expected {len(group)}"
            )
        if bool(valid_values[0]) and declared_size <= 0:
            raise ValueError(f"valid orbit_index={orbit_index} must have positive orbit_size")
        if group["structure_type"].nunique() != 1:
            raise ValueError(f"inconsistent structure_type for orbit_index={orbit_index}")
        if bool(valid_values[0]) and group["orbit_confidence"].nunique() != 1:
            raise ValueError(f"inconsistent orbit_confidence for orbit_index={orbit_index}")

    return normalized.sort_values("variable_id", kind="mergesort").reset_index(drop=True)


@dataclass(frozen=True)
class OrbitFeatureStore:
    _rows_by_cnf: dict[int, pd.DataFrame]

    @classmethod
    def from_tables(
        cls,
        variable_rows: pd.DataFrame,
        metadata: pd.DataFrame,
    ) -> "OrbitFeatureStore":
        if not isinstance(variable_rows, pd.DataFrame) or not isinstance(metadata, pd.DataFrame):
            raise TypeError("variable_rows and metadata must be pandas DataFrames")
        _require_columns(variable_rows, _VARIABLE_COLUMNS | _STORE_KEY_COLUMNS, "variable_rows")
        _require_columns(metadata, _METADATA_COLUMNS, "metadata")

        meta = metadata.copy()
        meta["cnf_id"] = [_integer(value, "cnf_id", minimum=0) for value in meta["cnf_id"]]
        if meta.duplicated(["base_instance_id", "variant"]).any():
            raise ValueError("duplicate metadata key (base_instance_id, variant)")
        if meta["cnf_id"].duplicated().any():
            raise ValueError("duplicate cnf_id in metadata")

        metadata_keys = set(
            meta[["base_instance_id", "variant"]].itertuples(index=False, name=None)
        )
        variable_keys = set(
            variable_rows[["base_instance_id", "variant"]].itertuples(index=False, name=None)
        )
        uncovered_keys = metadata_keys.difference(variable_keys)
        if uncovered_keys:
            uncovered = meta[
                meta[["base_instance_id", "variant"]].apply(tuple, axis=1).isin(uncovered_keys)
            ]
            details = [
                f"cnf_id={int(row.cnf_id)} key=({row.base_instance_id!r}, {row.variant!r})"
                for row in uncovered.itertuples(index=False)
            ]
            raise ValueError("metadata keys/cnf_ids have no variable rows: " + ", ".join(details))

        merged = variable_rows.merge(
            meta,
            on=["base_instance_id", "variant"],
            how="left",
            validate="many_to_one",
            indicator=True,
            suffixes=("_variable", "_metadata"),
        )
        if not merged["_merge"].eq("both").all():
            missing = merged.loc[merged["_merge"].ne("both"), ["base_instance_id", "variant"]]
            raise ValueError(f"variable rows do not match exactly one metadata row: {missing.to_dict('records')[:5]}")
        merged = merged.drop(columns="_merge")

        rows_by_cnf: dict[int, pd.DataFrame] = {}
        for cnf_id, group in merged.groupby("cnf_id", sort=True):
            if "num_vars" in group.columns and group["num_vars"].notna().any():
                values = group.loc[group["num_vars"].notna(), "num_vars"].unique().tolist()
                if len(values) != 1:
                    raise ValueError(f"inconsistent num_vars for cnf_id={cnf_id}")
                num_vars = _integer(values[0], "num_vars", minimum=1)
            else:
                variable_ids = [_integer(value, "variable_id", minimum=1) for value in group["variable_id"]]
                num_vars = max(variable_ids, default=0)
                if num_vars == 0:
                    raise ValueError(f"no variable rows for cnf_id={cnf_id}")
            normalized = _normalize_rows(group, num_vars=num_vars)
            normalized["cnf_id"] = int(cnf_id)
            rows_by_cnf[int(cnf_id)] = normalized
        uncovered_cnf_ids = sorted(set(meta["cnf_id"]).difference(rows_by_cnf))
        if uncovered_cnf_ids:
            raise ValueError(f"metadata cnf_ids have no variable rows after join: {uncovered_cnf_ids}")
        if "num_vars" in meta.columns:
            for _, metadata_row in meta.loc[meta["num_vars"].notna()].iterrows():
                cnf_id = int(metadata_row["cnf_id"])
                num_vars = _integer(metadata_row["num_vars"], "num_vars", minimum=1)
                if cnf_id not in rows_by_cnf:
                    raise ValueError(
                        f"variable rows for cnf_id={cnf_id} must cover variable IDs 1..{num_vars}"
                    )
        return cls(rows_by_cnf)

    def rows_for(self, cnf_id: int) -> pd.DataFrame | None:
        rows = self._rows_by_cnf.get(int(cnf_id))
        return None if rows is None else rows.copy()


def _graph_num_vars(data: HeteroData) -> int:
    var_nodes = getattr(data["var"], "num_nodes", None)
    lit_nodes = getattr(data["lit"], "num_nodes", None)
    if var_nodes is not None:
        num_vars = int(var_nodes)
        if lit_nodes is not None and int(lit_nodes) != 2 * num_vars:
            raise ValueError(
                f"graph num_vars={num_vars} is inconsistent with lit.num_nodes={int(lit_nodes)}"
            )
        return num_vars
    if lit_nodes is None or int(lit_nodes) % 2:
        raise ValueError("graph must expose var.num_nodes or an even lit.num_nodes")
    return int(lit_nodes) // 2


def _copy_graph(data: HeteroData) -> HeteroData:
    return data.clone() if hasattr(data, "clone") else copy(data)


def _tensor_device(data: HeteroData) -> torch.device:
    if hasattr(data["var"], "event_state"):
        return data["var"].event_state.device
    if hasattr(data["lit"], "x"):
        return data["lit"].x.device
    return torch.device("cpu")


def orbit_relative_event_features(
    event_state: torch.Tensor,
    orbit_index: torch.Tensor,
    valid_mask: torch.Tensor,
) -> torch.Tensor:
    if not isinstance(event_state, torch.Tensor) or event_state.ndim != 2:
        raise ValueError("event_state must be a two-dimensional tensor")
    if not event_state.is_floating_point():
        raise TypeError("event_state must have a floating dtype")
    if not torch.isfinite(event_state).all():
        raise ValueError("event_state contains nonfinite values")
    if not isinstance(orbit_index, torch.Tensor) or orbit_index.ndim != 1:
        raise ValueError("orbit_index must be a one-dimensional integer tensor")
    if orbit_index.dtype not in (torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8):
        raise TypeError("orbit_index must have an integer dtype")
    if not isinstance(valid_mask, torch.Tensor) or valid_mask.ndim != 1:
        raise ValueError("valid_mask must be a one-dimensional bool tensor")
    if valid_mask.dtype != torch.bool:
        raise TypeError("valid_mask must have bool dtype")
    if orbit_index.numel() != event_state.shape[0] or valid_mask.numel() != event_state.shape[0]:
        raise ValueError("event_state, orbit_index, and valid_mask length must match")
    if orbit_index.numel() and bool((orbit_index < 0).any()):
        raise ValueError("orbit_index values must be nonnegative")
    if orbit_index.device != event_state.device or valid_mask.device != event_state.device:
        raise ValueError("event_state, orbit_index, and valid_mask must share a device")

    num_vars, channels = event_state.shape
    output = torch.zeros((num_vars, channels, 5), dtype=event_state.dtype, device=event_state.device)
    for orbit in torch.unique(orbit_index[valid_mask], sorted=True):
        member_mask = valid_mask & orbit_index.eq(orbit)
        values = event_state[member_mask]
        size = values.shape[0]
        mean = values.mean(dim=0)
        variance = ((values - mean) ** 2).mean(dim=0)
        zscore = torch.where(
            variance > 0.0,
            (values - mean) / torch.sqrt(variance).clamp_min(torch.finfo(values.dtype).eps),
            torch.zeros_like(values),
        )
        absolute_sum = values.abs().sum(dim=0)
        share = torch.where(
            absolute_sum > 0.0,
            values / absolute_sum.clamp_min(torch.finfo(values.dtype).eps),
            torch.zeros_like(values),
        )
        coverage = values.ne(0.0).to(values.dtype).mean(dim=0).expand_as(values)
        if size == 1:
            rank = torch.zeros_like(values)
        else:
            less = (values.unsqueeze(1) > values.unsqueeze(0)).sum(dim=1).to(values.dtype)
            equal = (values.unsqueeze(1) == values.unsqueeze(0)).sum(dim=1).to(values.dtype)
            rank = (less + 0.5 * (equal - 1.0)) / float(size - 1)
            rank[:, values.eq(values[0]).all(dim=0)] = 0.0
        output[member_mask] = torch.stack(
            [rank, zscore, share, variance.expand_as(values), coverage],
            dim=2,
        )
    return output.reshape(num_vars, channels * 5)


def attach_orbit_features(
    data: HeteroData,
    rows: pd.DataFrame | None,
) -> HeteroData:
    attached = _copy_graph(data)
    num_vars = _graph_num_vars(attached)
    attached["var"].num_nodes = num_vars
    device = _tensor_device(attached)

    if rows is None:
        orbit_index = torch.zeros(num_vars, dtype=torch.long, device=device)
        orbit_size = torch.zeros(num_vars, dtype=torch.float32, device=device)
        confidence = torch.zeros(num_vars, dtype=torch.float32, device=device)
        valid_mask = torch.zeros(num_vars, dtype=torch.bool, device=device)
        structures = ["unknown"] * num_vars
    else:
        normalized = _normalize_rows(rows, num_vars=num_vars)
        orbit_index = torch.tensor(normalized["orbit_index"].tolist(), dtype=torch.long, device=device)
        orbit_size = torch.tensor(normalized["orbit_size"].tolist(), dtype=torch.float32, device=device)
        confidence = torch.tensor(normalized["orbit_confidence"].tolist(), dtype=torch.float32, device=device)
        valid_mask = torch.tensor(normalized["valid_orbit_mask"].tolist(), dtype=torch.bool, device=device)
        structures = normalized["structure_type"].tolist()

    structure_one_hot = torch.zeros(
        (num_vars, len(STRUCTURE_CATEGORIES)), dtype=torch.float32, device=device
    )
    if num_vars:
        structure_indices = torch.tensor(
            [STRUCTURE_CATEGORIES.index(structure) for structure in structures],
            dtype=torch.long,
            device=device,
        )
        structure_one_hot.scatter_(1, structure_indices.unsqueeze(1), 1.0)
    log1p_orbit_size = torch.log1p(orbit_size)
    attached["var"].orbit_index = orbit_index
    attached["var"].log1p_orbit_size = log1p_orbit_size
    attached["var"].orbit_size_log1p = log1p_orbit_size
    attached["var"].orbit_confidence = confidence
    attached["var"].valid_orbit_mask = valid_mask
    attached["var"].structure_one_hot = structure_one_hot
    attached["var"].orbit_structure_one_hot = structure_one_hot
    attached["var"].orbit_features = torch.cat(
        [
            log1p_orbit_size.unsqueeze(1),
            confidence.unsqueeze(1),
            valid_mask.to(torch.float32).unsqueeze(1),
            structure_one_hot,
        ],
        dim=1,
    )

    valid_orbits = torch.unique(orbit_index[valid_mask], sorted=True)
    valid_count = float(valid_orbits.numel())
    valid_fraction = float(valid_mask.to(torch.float32).mean().item()) if num_vars else 0.0
    mean_confidence = (
        float(
            torch.stack(
                [confidence[valid_mask & orbit_index.eq(orbit)][0] for orbit in valid_orbits]
            ).mean().item()
        )
        if valid_orbits.numel()
        else 0.0
    )
    active_orbit_fraction = 0.0
    mean_event_variance = 0.0

    if hasattr(attached["var"], "event_state"):
        event_state = attached["var"].event_state
        if event_state.shape[0] != num_vars:
            raise ValueError(
                f"event_state has {event_state.shape[0]} rows, expected graph num_vars={num_vars}"
            )
        relative = orbit_relative_event_features(event_state, orbit_index, valid_mask)
        channels = event_state.shape[1]
        variance = relative.reshape(num_vars, channels, 5)[:, :, 3]
        attached["var"].orbit_event_state = relative
        attached["var"].orbit_event_variance = variance
        if valid_orbits.numel():
            active = []
            orbit_variances = []
            for orbit in valid_orbits:
                member_mask = valid_mask & orbit_index.eq(orbit)
                active.append(event_state[member_mask].ne(0.0).any().to(torch.float32))
                orbit_variances.append(variance[member_mask][0].mean())
            active_orbit_fraction = float(torch.stack(active).mean().item())
            mean_event_variance = float(torch.stack(orbit_variances).mean().item())

    scalar = lambda value: torch.tensor([value], dtype=torch.float32, device=device)
    attached.valid_orbit_count = scalar(valid_count)
    attached.valid_orbit_variable_fraction = scalar(valid_fraction)
    attached.mean_orbit_confidence = scalar(mean_confidence)
    attached.event_active_orbit_fraction = scalar(active_orbit_fraction)
    attached.mean_orbit_event_variance = scalar(mean_event_variance)
    return attached


__all__ = [
    "OrbitFeatureStore",
    "STRUCTURE_CATEGORIES",
    "attach_orbit_features",
    "orbit_relative_event_features",
]
