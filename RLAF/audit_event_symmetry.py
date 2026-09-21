from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from src.data.dataset import DimacsCNFDataset
from src.data.symmetry import orbit_validity, read_orbits_json
from src.model.model import load_checkpoint
from src.policy.evaluate import compute_solver_stats, sample_var_params
from src.solving.budget import apply_rollout_budget
from src.solving.state import attach_var_event_state_batch, event_state_dim


ROOT = Path(__file__).resolve().parent


def orbit_entropy(variable_orbits: dict[int, str]) -> float:
    total = len(variable_orbits)
    if total <= 0:
        return 0.0
    counts: dict[str, int] = {}
    for orbit in variable_orbits.values():
        counts[str(orbit)] = counts.get(str(orbit), 0) + 1
    entropy = 0.0
    for count in counts.values():
        probability = float(count) / float(total)
        entropy -= probability * math.log(probability)
    return entropy


def normalized_orbit_entropy(variable_orbits: dict[int, str]) -> float:
    total = len(variable_orbits)
    if total <= 1:
        return 0.0
    return orbit_entropy(variable_orbits) / math.log(float(total))


def _column_stats(values: torch.Tensor, prefix: str) -> dict[str, float]:
    values = values.to(dtype=torch.float32)
    return {
        f"{prefix}_mean": float(values.mean()),
        f"{prefix}_std": float(values.std(unbiased=False)),
        f"{prefix}_range": float(values.max() - values.min()),
    }


def tensor_orbit_rows(
    tensor: torch.Tensor,
    variable_orbits: dict[int, str],
    prefix: str,
) -> list[dict[str, object]]:
    if tensor.dim() == 1:
        tensor = tensor.view(-1, 1)
    rows: list[dict[str, object]] = []
    for orbit in sorted(set(variable_orbits.values())):
        variables = [var for var, value in sorted(variable_orbits.items()) if value == orbit]
        indices = torch.tensor([var - 1 for var in variables], dtype=torch.long)
        values = tensor[indices]
        row: dict[str, object] = {"orbit": orbit, "orbit_size": int(len(variables))}
        if values.shape[1] >= 1:
            row.update(_column_stats(values[:, 0], f"{prefix}_rho"))
        if values.shape[1] >= 2:
            row.update(_column_stats(values[:, 1], f"{prefix}_mu"))
        if values.shape[1] > 2:
            row[f"{prefix}_feature_mean_range"] = float(values.mean(dim=1).max() - values.mean(dim=1).min())
            row[f"{prefix}_feature_l2_range"] = float(values.norm(dim=1).max() - values.norm(dim=1).min())
        rows.append(row)
    return rows


def event_state_orbit_rows(
    event_state: torch.Tensor,
    variable_orbits: dict[int, str],
) -> list[dict[str, object]]:
    if event_state.dim() != 2:
        raise ValueError(f"event_state must be 2D, got shape {tuple(event_state.shape)}")
    rows: list[dict[str, object]] = []
    for orbit in sorted(set(variable_orbits.values())):
        variables = [var for var, value in sorted(variable_orbits.items()) if value == orbit]
        indices = torch.tensor([var - 1 for var in variables], dtype=torch.long)
        values = event_state[indices].to(dtype=torch.float32)
        per_var_l2 = values.norm(dim=1)
        per_var_sum = values.sum(dim=1)
        rows.append(
            {
                "orbit": orbit,
                "orbit_size": int(len(variables)),
                "event_feature_mean_range": float(values.mean(dim=1).max() - values.mean(dim=1).min()),
                "event_feature_l2_range": float(per_var_l2.max() - per_var_l2.min()),
                "event_feature_sum_range": float(per_var_sum.max() - per_var_sum.min()),
                "event_nonzero_variables": int((per_var_sum.abs() > 1.0e-9).sum()),
            }
        )
    return rows


def merge_orbit_rows(*frames: pd.DataFrame) -> pd.DataFrame:
    merged = None
    for frame in frames:
        if frame.empty:
            continue
        if merged is None:
            merged = frame.copy()
        else:
            merged = merged.merge(frame, on=["orbit", "orbit_size"], how="outer")
    return merged if merged is not None else pd.DataFrame()


def annotate_orbit_validity(frame: pd.DataFrame, min_orbit_size: int) -> pd.DataFrame:
    frame = frame.copy()
    if frame.empty:
        frame["orbit_valid"] = []
        frame["orbit_valid_reason"] = []
        return frame
    validity = [
        orbit_validity(row["orbit"], row["orbit_size"], min_orbit_size=min_orbit_size)
        for _, row in frame.iterrows()
    ]
    frame["orbit_valid"] = [valid for valid, _ in validity]
    frame["orbit_valid_reason"] = [reason for _, reason in validity]
    return frame


def solver_had_search_activity(solver_stats: pd.DataFrame) -> bool:
    if solver_stats.empty:
        return False
    for column in ["decisions", "conflicts"]:
        if column not in solver_stats.columns:
            continue
        values = pd.to_numeric(solver_stats[column], errors="coerce").fillna(0.0)
        if bool((values > 0).any()):
            return True
    return False


def annotate_event_row_validity(
    frame: pd.DataFrame,
    solver_stats: pd.DataFrame,
    static_collapse_threshold: float,
    event_identity_eps: float,
) -> pd.DataFrame:
    frame = frame.copy()
    rollout_has_activity = solver_had_search_activity(solver_stats)
    event_valid = []
    reasons = []
    for _, row in frame.iterrows():
        if not bool(row.get("orbit_valid", False)):
            event_valid.append(False)
            reasons.append(str(row.get("orbit_valid_reason", "invalid_orbit")))
            continue
        if str(row.get("audit_status", "ok")) != "ok":
            event_valid.append(False)
            reasons.append(str(row.get("audit_status", "invalid_rollout")))
            continue
        if not rollout_has_activity:
            event_valid.append(False)
            reasons.append("no_solver_activity")
            continue
        static_mu_range = row.get("static_mu_range", float("nan"))
        if pd.isna(static_mu_range):
            event_valid.append(False)
            reasons.append("missing_static_mu_range")
            continue
        if float(static_mu_range) > float(static_collapse_threshold):
            event_valid.append(False)
            reasons.append("static_mu_not_collapsed")
            continue
        event_valid.append(True)
        reasons.append("valid")
    frame["event_row_valid"] = event_valid
    frame["event_row_valid_reason"] = reasons
    identity_values = pd.to_numeric(
        frame.get("event_feature_l2_range", pd.Series([float("nan")] * len(frame))),
        errors="coerce",
    )
    frame["event_identity_positive"] = frame["event_row_valid"].astype(bool) & (identity_values > float(event_identity_eps))
    frame["event_identity_zero"] = frame["event_row_valid"].astype(bool) & ~frame["event_identity_positive"].astype(bool)
    frame["event_identity_eps"] = float(event_identity_eps)
    return frame


def make_dimacs_dataset(cnf_path: Path, transform) -> DimacsCNFDataset:
    try:
        return DimacsCNFDataset(str(cnf_path), transform=transform, lazy=True)
    except TypeError:
        return DimacsCNFDataset(str(cnf_path), transform=transform)


def add_identity_gain_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in ["rho", "mu"]:
        static_col = f"static_{column}_range"
        adapted_col = f"adapted_{column}_range"
        if static_col in frame.columns and adapted_col in frame.columns:
            frame[f"adapter_{column}_identity_gain"] = frame[adapted_col].fillna(0.0) - frame[static_col].fillna(0.0)
    if "event_feature_l2_range" in frame.columns:
        frame["event_identity_gain"] = frame["event_feature_l2_range"].fillna(0.0)
    if "adapted_mu_range" in frame.columns and "static_mu_range" in frame.columns:
        frame["adapter_identity_gain"] = frame["adapted_mu_range"].fillna(0.0) - frame["static_mu_range"].fillna(0.0)
    return frame


def _cnf_id_value(data) -> int:
    value = data.cnf_id
    return int(value.item() if hasattr(value, "item") else value)


def cached_base_graph(model, dataset: DimacsCNFDataset, device: str, scale_sigma: float):
    loader = DataLoader(dataset=dataset, batch_size=1, num_workers=0, shuffle=False)
    try:
        graphs = sample_var_params(
            model=model,
            loader=loader,
            num_samples=1,
            device=device,
            use_mode=True,
            scale_sigma=scale_sigma,
            add_timing=True,
            cache_var_features=True,
        )
    except TypeError:
        graphs = sample_var_params(
            model=model,
            loader=loader,
            num_samples=1,
            device=device,
            use_mode=True,
            scale_sigma=scale_sigma,
            add_timing=True,
        )
        for graph in graphs:
            graph["var"].base_y = graph["var"].y_var_ref
    if len(graphs) != 1:
        raise RuntimeError(f"Expected one graph from {dataset.path}, got {len(graphs)}")
    return graphs[0]


def solver_stats_has_events(solver_stats: pd.DataFrame) -> bool:
    event_columns = [column for column in solver_stats.columns if str(column).startswith("event_var_")]
    if not event_columns:
        return False
    for column in event_columns:
        for value in solver_stats[column]:
            if isinstance(value, (list, tuple)) and len(value) > 0:
                return True
    return False


def model_supports_event_adapter(model) -> bool:
    return bool(getattr(model, "var_state_dim", 0) > 0 and hasattr(model, "event_adapter"))


def annotate_orbit_rows(
    rows: pd.DataFrame,
    instance: pd.Series,
    checkpoint_path: Path,
    solver: str,
    rollout_budget_type: str,
    rollout_cpu_lim: float,
    rollout_conflicts: int,
    event_state_features: str,
    adapter_supported: bool,
    audit_status: str = "ok",
    audit_error: str = "",
) -> pd.DataFrame:
    rows = rows.copy()
    for column, value in [
        ("family", str(instance["family"])),
        ("instance_id", str(instance["instance_id"])),
        ("base_instance_id", str(instance["base_instance_id"])),
        ("variant", str(instance["variant"])),
        ("expected_result", str(instance.get("expected_result", ""))),
        ("num_vars", int(instance["num_vars"])),
        ("num_clauses", int(instance["num_clauses"])),
        ("checkpoint", str(checkpoint_path)),
        ("solver", solver),
        ("rollout_budget_type", rollout_budget_type),
        ("rollout_cpu_lim", float(rollout_cpu_lim)),
        ("rollout_conflicts", int(rollout_conflicts)),
        ("event_state_features", event_state_features),
        ("adapter_supported", bool(adapter_supported)),
        ("audit_status", audit_status),
        ("audit_error", audit_error),
    ]:
        rows[column] = value
    return rows


def audit_instance(
    instance: pd.Series,
    model,
    transform,
    model_cfg,
    checkpoint_path: Path,
    device: str,
    solver: str,
    solver_params: dict,
    rollout_budget_type: str,
    rollout_cpu_lim: float,
    rollout_conflicts: int,
    event_state_features: str,
    min_orbit_size: int,
    static_collapse_threshold: float,
    event_identity_eps: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cnf_path = Path(str(instance["cnf_path"]))
    orbits_path = Path(str(instance["orbits_path"]))
    dataset = make_dimacs_dataset(cnf_path, transform=transform)
    base_graph = cached_base_graph(
        model=model,
        dataset=dataset,
        device=device,
        scale_sigma=float(model_cfg.scale_sigma),
    )
    variable_orbits = read_orbits_json(orbits_path, num_vars=base_graph["var"].base_y.shape[0])
    entropy = orbit_entropy(variable_orbits)
    entropy_norm = normalized_orbit_entropy(variable_orbits)

    rollout_params = apply_rollout_budget(
        dict(solver_params),
        budget_type=rollout_budget_type,
        cpu_lim=rollout_cpu_lim,
        conflicts=rollout_conflicts,
    )
    rollout_params["collect-events"] = True
    solver_stats = compute_solver_stats(
        dataset=dataset,
        data_list=[base_graph],
        num_workers=1,
        solver=solver,
        **rollout_params,
    )
    if not solver_stats_has_events(solver_stats):
        static_rows = pd.DataFrame(tensor_orbit_rows(base_graph["var"].base_y, variable_orbits, prefix="static"))
        static_rows = annotate_orbit_validity(static_rows, min_orbit_size=min_orbit_size)
        error = (
            "solver rollout did not emit event_var_* columns; "
            f"returncode={solver_stats.get('solver_returncode', pd.Series([''])).iloc[0] if not solver_stats.empty else ''}, "
            f"stdout_bytes={solver_stats.get('solver_stdout_bytes', pd.Series([''])).iloc[0] if not solver_stats.empty else ''}, "
            f"stderr_bytes={solver_stats.get('solver_stderr_bytes', pd.Series([''])).iloc[0] if not solver_stats.empty else ''}"
        )
        rows = annotate_orbit_rows(
            static_rows,
            instance=instance,
            checkpoint_path=checkpoint_path,
            solver=solver,
            rollout_budget_type=rollout_budget_type,
            rollout_cpu_lim=rollout_cpu_lim,
            rollout_conflicts=rollout_conflicts,
            event_state_features=event_state_features,
            adapter_supported=model_supports_event_adapter(model),
            audit_status="missing_events",
            audit_error=error,
        )
        rows = annotate_event_row_validity(
            rows,
            solver_stats=solver_stats,
            static_collapse_threshold=static_collapse_threshold,
            event_identity_eps=event_identity_eps,
        )
        rows["orbit_entropy"] = float(entropy)
        rows["orbit_entropy_norm"] = float(entropy_norm)
        stats = solver_stats.copy()
        stats["family"] = str(instance["family"])
        stats["instance_id"] = str(instance["instance_id"])
        stats["base_instance_id"] = str(instance["base_instance_id"])
        stats["variant"] = str(instance["variant"])
        stats["audit_status"] = "missing_events"
        stats["audit_error"] = error
        return rows, stats

    var_state_dim = event_state_dim(event_state_features)
    expected_dim = event_state_dim(event_state_features)
    refined = attach_var_event_state_batch(
        [base_graph],
        solver_stats,
        var_state_dim=var_state_dim,
        momentum=0.0,
        feature_mode=event_state_features,
    )[0]

    static_rows = pd.DataFrame(tensor_orbit_rows(refined["var"].base_y, variable_orbits, prefix="static"))
    event_rows = pd.DataFrame(event_state_orbit_rows(refined["var"].event_state, variable_orbits))
    frames = [static_rows, event_rows]
    if model_supports_event_adapter(model):
        model_var_state_dim = int(getattr(model, "var_state_dim", 0))
        if model_var_state_dim != expected_dim:
            raise ValueError(
                f"event_state_features={event_state_features} has dim {expected_dim}, "
                f"but checkpoint model.var_state_dim={model_var_state_dim}."
            )
        model.to(device)
        model.eval()
        with torch.no_grad():
            batch = next(iter(DataLoader(dataset=[refined], batch_size=1, num_workers=0, shuffle=False))).to(device)
            adapted_y = model(batch).detach().cpu()
        frames.append(pd.DataFrame(tensor_orbit_rows(adapted_y, variable_orbits, prefix="adapted")))
    rows = merge_orbit_rows(*frames)
    rows = add_identity_gain_columns(rows)
    rows = annotate_orbit_validity(rows, min_orbit_size=min_orbit_size)

    rows = annotate_orbit_rows(
        rows,
        instance=instance,
        checkpoint_path=checkpoint_path,
        solver=solver,
        rollout_budget_type=rollout_budget_type,
        rollout_cpu_lim=rollout_cpu_lim,
        rollout_conflicts=rollout_conflicts,
        event_state_features=event_state_features,
        adapter_supported=model_supports_event_adapter(model),
    )
    rows = annotate_event_row_validity(
        rows,
        solver_stats=solver_stats,
        static_collapse_threshold=static_collapse_threshold,
        event_identity_eps=event_identity_eps,
    )
    rows["orbit_entropy"] = float(entropy)
    rows["orbit_entropy_norm"] = float(entropy_norm)

    stats = solver_stats.copy()
    stats["family"] = str(instance["family"])
    stats["instance_id"] = str(instance["instance_id"])
    stats["base_instance_id"] = str(instance["base_instance_id"])
    stats["variant"] = str(instance["variant"])
    stats["audit_status"] = "ok"
    stats["audit_error"] = ""
    return rows, stats


def summarize_orbits(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    aggregations = {
        "instances": ("instance_id", "nunique"),
        "orbits": ("orbit", "count"),
        "mean_static_mu_range": ("static_mu_range", "mean"),
    }
    if "audit_status" in frame.columns:
        aggregations["valid_rollout_rows"] = ("event_row_valid", lambda values: int(pd.Series(values).astype(bool).sum()))
        aggregations["event_positive_rows"] = (
            "event_identity_positive",
            lambda values: int(pd.Series(values).astype(bool).sum()),
        )
        aggregations["zero_identity_rows"] = (
            "event_identity_zero",
            lambda values: int(pd.Series(values).astype(bool).sum()),
        )
        aggregations["missing_event_rows"] = (
            "audit_status",
            lambda values: int((values == "missing_events").sum()),
        )
    if "event_feature_l2_range" in frame.columns:
        aggregations["mean_event_l2_range"] = ("event_feature_l2_range", "mean")
        aggregations["max_event_l2_range"] = ("event_feature_l2_range", "max")
    if "event_identity_gain" in frame.columns:
        aggregations["mean_event_identity_gain"] = ("event_identity_gain", "mean")
    if "adapted_mu_range" in frame.columns:
        aggregations["mean_adapted_mu_range"] = ("adapted_mu_range", "mean")
    if "adapter_identity_gain" in frame.columns:
        aggregations["mean_adapter_identity_gain"] = ("adapter_identity_gain", "mean")
        aggregations["max_adapter_identity_gain"] = ("adapter_identity_gain", "max")
    return frame.groupby("family", sort=True).agg(**aggregations).reset_index()


def layered_family_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    rows = []
    for family, group in frame.groupby("family", sort=True):
        valid = group[group.get("event_row_valid", pd.Series(False, index=group.index)).astype(bool)].copy()
        positive = group[group.get("event_identity_positive", pd.Series(False, index=group.index)).astype(bool)].copy()
        zero = group[group.get("event_identity_zero", pd.Series(False, index=group.index)).astype(bool)].copy()
        rows.append(
            {
                "family": family,
                "instances": int(group["instance_id"].nunique()),
                "orbit_rows": int(len(group)),
                "valid_rollout_rows": int(len(valid)),
                "event_positive_rows": int(len(positive)),
                "zero_identity_rows": int(len(zero)),
                "missing_event_rows": int((group["audit_status"] == "missing_events").sum()) if "audit_status" in group.columns else 0,
                "mean_static_mu_range_valid": float(valid["static_mu_range"].mean()) if not valid.empty else float("nan"),
                "mean_event_l2_valid": float(valid["event_feature_l2_range"].mean()) if not valid.empty and "event_feature_l2_range" in valid.columns else float("nan"),
                "max_event_l2_valid": float(valid["event_feature_l2_range"].max()) if not valid.empty and "event_feature_l2_range" in valid.columns else float("nan"),
                "mean_event_l2_positive": float(positive["event_feature_l2_range"].mean()) if not positive.empty and "event_feature_l2_range" in positive.columns else float("nan"),
                "max_event_l2_positive": float(positive["event_feature_l2_range"].max()) if not positive.empty and "event_feature_l2_range" in positive.columns else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def adapter_family_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "adapted_mu_range" not in frame.columns or "adapter_identity_gain" not in frame.columns:
        return pd.DataFrame()
    rows = []
    for family, group in frame.groupby("family", sort=True):
        valid = group[group.get("event_row_valid", pd.Series(False, index=group.index)).astype(bool)].copy()
        positive = group[group.get("event_identity_positive", pd.Series(False, index=group.index)).astype(bool)].copy()
        zero = group[group.get("event_identity_zero", pd.Series(False, index=group.index)).astype(bool)].copy()
        rows.append(
            {
                "family": family,
                "valid_rollout_rows": int(len(valid)),
                "event_positive_rows": int(len(positive)),
                "zero_identity_rows": int(len(zero)),
                "mean_static_mu_range_valid": float(valid["static_mu_range"].mean()) if not valid.empty else float("nan"),
                "mean_event_l2_valid": float(valid["event_feature_l2_range"].mean()) if not valid.empty and "event_feature_l2_range" in valid.columns else float("nan"),
                "mean_adapted_mu_range_valid": float(valid["adapted_mu_range"].mean()) if not valid.empty else float("nan"),
                "max_adapted_mu_range_valid": float(valid["adapted_mu_range"].max()) if not valid.empty else float("nan"),
                "mean_adapter_gain_valid": float(valid["adapter_identity_gain"].mean()) if not valid.empty else float("nan"),
                "mean_adapter_gain_positive": float(positive["adapter_identity_gain"].mean()) if not positive.empty else float("nan"),
                "mean_adapter_gain_zero": float(zero["adapter_identity_gain"].mean()) if not zero.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return ["_None._"]
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_doc(path: Path, orbit_frame: pd.DataFrame, solver_stats: pd.DataFrame, checkpoint: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = layered_family_summary(orbit_frame)
    positive_frame = (
        orbit_frame[orbit_frame["event_identity_positive"].astype(bool)].copy()
        if "event_identity_positive" in orbit_frame.columns
        else pd.DataFrame()
    )
    positive_summary = layered_family_summary(positive_frame)
    adapter_summary = adapter_family_summary(orbit_frame)
    validity_summary = (
        orbit_frame.groupby(["family", "event_row_valid_reason"], sort=True)
        .agg(rows=("orbit", "count"))
        .reset_index()
        if "event_row_valid_reason" in orbit_frame.columns and not orbit_frame.empty
        else pd.DataFrame()
    )
    stat_columns = [
        column
        for column in [
            "family",
            "instance_id",
            "variant",
            "Result",
            "conflicts",
            "decisions",
            "CPU time",
        ]
        if column in solver_stats.columns
    ]
    stat_view = solver_stats[stat_columns].head(40) if stat_columns else pd.DataFrame()
    lines = [
        "# Event Symmetry Audit",
        "",
        f"- checkpoint: `{checkpoint}`",
        "",
        "This audit is a representation test, not a solver-performance claim.",
        "It measures whether short solver rollouts create within-orbit event",
        "identity. Adapter output separation is reported only when the",
        "checkpoint actually contains an event adapter.",
        "The family summary separates valid rollout rows, event-positive rows,",
        "zero-identity rows, and missing-event rows.",
        "",
        "## Family Summary",
        "",
        *markdown_table(summary),
        "",
        "## Event-Positive Summary",
        "",
        *markdown_table(positive_summary),
        "",
        "## Adapter Summary",
        "",
        *markdown_table(adapter_summary),
        "",
        "## Valid Row Filter",
        "",
        *markdown_table(validity_summary),
        "",
        "## Rollout Stats",
        "",
        *markdown_table(stat_view),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_solver_param(raw: str) -> dict:
    params: dict[str, object] = {}
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"Invalid solver param {item!r}; expected key=value.")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.lower() in {"none", "null"}:
            continue
        try:
            if "." in value:
                parsed: object = float(value)
            else:
                parsed = int(value)
        except ValueError:
            parsed = value
        params[key] = parsed
    return params


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit search-induced symmetry breaking from solver events.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/symmetry_stress/manifest.csv")
    parser.add_argument("--output-csv", type=Path, default=ROOT / "runs/analysis/symmetry_event_orbits.csv")
    parser.add_argument("--stats-csv", type=Path, default=ROOT / "runs/analysis/symmetry_event_rollout_stats.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_event_audit.md")
    parser.add_argument("--limit-instances", type=int, default=0)
    parser.add_argument("--families", default="")
    parser.add_argument("--solver", default="glucose")
    parser.add_argument("--solver-params", default="rnd-freq=0.0,K=0.1")
    parser.add_argument("--rollout-budget-type", choices=["cpu_time", "conflicts"], default="conflicts")
    parser.add_argument("--rollout-cpu-lim", type=float, default=5.0)
    parser.add_argument("--rollout-conflicts", type=int, default=20)
    parser.add_argument("--event-state-features", choices=["legacy", "enhanced", "polarity"], default="legacy")
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--min-orbit-size", type=int, default=2)
    parser.add_argument("--static-collapse-threshold", type=float, default=1.0e-4)
    parser.add_argument("--event-identity-eps", type=float, default=1.0e-6)
    parser.add_argument("--include-static-only", action="store_true")
    args = parser.parse_args()

    checkpoint = args.checkpoint.resolve()
    model, transform, model_cfg = load_checkpoint(str(checkpoint), var_output=True)
    manifest = pd.read_csv(args.manifest)
    families = {part.strip() for part in args.families.split(",") if part.strip()}
    if families:
        manifest = manifest[manifest["family"].astype(str).isin(families)].copy()
    if not bool(args.include_static_only) and "event_audit_role" in manifest.columns:
        manifest = manifest[manifest["event_audit_role"].fillna("event").astype(str) != "static_only"].copy()
    if int(args.limit_instances) > 0:
        manifest = manifest.head(int(args.limit_instances)).copy()
    if manifest.empty:
        raise ValueError("No symmetry stress instances selected.")

    solver_params = parse_solver_param(args.solver_params)
    orbit_frames = []
    stats_frames = []
    for _, instance in manifest.iterrows():
        orbit_frame, stats = audit_instance(
            instance=instance,
            model=model,
            transform=transform,
            model_cfg=model_cfg,
            checkpoint_path=checkpoint,
            device=args.device,
            solver=str(args.solver),
            solver_params=solver_params,
            rollout_budget_type=str(args.rollout_budget_type),
            rollout_cpu_lim=float(args.rollout_cpu_lim),
            rollout_conflicts=int(args.rollout_conflicts),
            event_state_features=str(args.event_state_features),
            min_orbit_size=int(args.min_orbit_size),
            static_collapse_threshold=float(args.static_collapse_threshold),
            event_identity_eps=float(args.event_identity_eps),
        )
        orbit_frames.append(orbit_frame)
        stats_frames.append(stats)

    orbit_all = pd.concat(orbit_frames, ignore_index=True)
    stats_all = pd.concat(stats_frames, ignore_index=True)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    orbit_all.to_csv(args.output_csv, index=False)
    args.stats_csv.parent.mkdir(parents=True, exist_ok=True)
    stats_all.to_csv(args.stats_csv, index=False)
    write_doc(args.doc, orbit_frame=orbit_all, solver_stats=stats_all, checkpoint=checkpoint)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.stats_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
