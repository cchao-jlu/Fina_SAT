from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from run_symmetry_solver_protocol_preflight import (
    clean_solver_params,
    make_dimacs_dataset,
    run_solver_batch,
    solver_cli_number,
)
from src.model.model import load_checkpoint
from src.policy.evaluate import sample_var_params
from src.solving.budget import apply_rollout_budget
from src.solving.state import attach_var_event_state, event_state_dim


ROOT = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = ROOT / "runs/GNN_Glucose_3SAT_EventVarSpeedupFull/best.pt"
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv"
DEFAULT_PER_INSTANCE = ROOT / "runs/analysis/symmetry_grpo_speedup_best_v2_per_instance.csv"
DEFAULT_ATTRIBUTION = ROOT / "runs/analysis/symmetry_grpo_speedup_best_v2_attribution.csv"
DEFAULT_VS_PLAIN_BASE = ROOT / "runs/analysis/symmetry_grpo_speedup_best_v2_vs_plain_by_base.csv"
DEFAULT_RANDOM_BASE = ROOT / "runs/analysis/symmetry_grpo_random_control_failure_audit_base.csv"
DEFAULT_SYMMETRY_BASE = ROOT / "runs/analysis/symmetry_grpo_hex_torus_failure_audit_base.csv"
DEFAULT_RANDOM_PARAM = ROOT / "runs/analysis/symmetry_grpo_random_control_adapter_param_shift.csv"
DEFAULT_FAMILY = ROOT / "runs/analysis/symmetry_grpo_control_vs_symmetry_failure_by_family.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_grpo_control_vs_symmetry_failure.md"

TARGET_SYMMETRY_FAMILIES = {"dominating_set_hex", "vertex_cover_torus"}


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def stats_by_cnf(frame: pd.DataFrame) -> dict[int, pd.Series]:
    return {int(row["cnf_id"]): row for _, row in frame.iterrows()}


def graph_cnf_id(graph: Any) -> int:
    value = getattr(graph, "cnf_id", None)
    if value is None and hasattr(graph, "__getitem__"):
        try:
            value = graph["cnf_id"]
        except Exception:
            value = None
    if hasattr(value, "item"):
        return int(value.item())
    return int(value)


def graph_var_params_array(graph: Any) -> np.ndarray:
    values = graph["var"].var_params.detach().cpu().numpy()
    if values.ndim == 3:
        values = values[:, 0, :]
    if values.ndim != 2 or values.shape[1] < 2:
        raise ValueError(f"unexpected var_params shape {values.shape}")
    return values[:, :2].astype(np.float64)


def method_wide(per_instance: pd.DataFrame) -> pd.DataFrame:
    keys = ["family", "base_instance_id", "variant", "repeat_id"]
    values = [
        "final_cpu_time",
        "protocol_accounted_time",
        "final_decisions",
        "final_conflicts",
        "final_solved",
        "warmup_cpu_time",
        "static_inference_wall_time",
        "event_attach_wall_time",
        "adapter_inference_wall_time",
        "event_state_l2_sum",
        "event_state_nonzero_vars",
        "event_adapter_graph_gate_open",
        "final_cpu_lim",
    ]
    meta_columns = [
        "seed",
        "solver_seed",
        "final_seed",
        "warmup_seed",
        "control_type",
        "scale",
        "benchmark_role",
        "family_scale",
        "symmetry_strength",
        "event_audit_role",
        "num_vars",
        "num_clauses",
    ]
    table = per_instance.pivot_table(index=keys, columns="method", values=values, aggfunc="first")
    table.columns = [f"{metric}__{method}" for metric, method in table.columns]
    table = table.reset_index()
    meta = per_instance.sort_values(keys).drop_duplicates(keys)[keys + [c for c in meta_columns if c in per_instance.columns]]
    table = meta.merge(table, on=keys, how="right")
    for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
        adapter = f"{metric}__event_adapter_final"
        plain = f"{metric}__plain_unguided_glucose"
        static = f"{metric}__static_weighted_glucose"
        cached = f"{metric}__cached_trace_no_adapter_final"
        if adapter in table.columns and plain in table.columns:
            table[f"adapter_minus_plain_{metric}"] = table[adapter] - table[plain]
        if adapter in table.columns and static in table.columns:
            table[f"adapter_minus_static_{metric}"] = table[adapter] - table[static]
        if adapter in table.columns and cached in table.columns:
            table[f"adapter_minus_cached_{metric}"] = table[adapter] - table[cached]
        if cached in table.columns and static in table.columns:
            table[f"cached_minus_static_{metric}"] = table[cached] - table[static]
    table["adapter_near_cap"] = (
        table["final_cpu_time__event_adapter_final"]
        >= 0.8 * table["final_cpu_lim__event_adapter_final"].fillna(table["final_cpu_lim__event_adapter_final"].max())
    )
    table["plain_near_cap"] = (
        table["final_cpu_time__plain_unguided_glucose"]
        >= 0.8 * table["final_cpu_lim__plain_unguided_glucose"].fillna(table["final_cpu_lim__plain_unguided_glucose"].max())
    )
    return table


def aggregate_base(wide: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        c
        for c in [
            "family",
            "base_instance_id",
            "control_type",
            "scale",
            "benchmark_role",
            "family_scale",
            "symmetry_strength",
        ]
        if c in wide.columns
    ]
    agg: dict[str, tuple[str, Any]] = {
        "rows": ("repeat_id", "size"),
        "variants": ("variant", "nunique"),
        "repeats": ("repeat_id", "nunique"),
        "num_vars_mean": ("num_vars", "mean"),
        "num_clauses_mean": ("num_clauses", "mean"),
        "adapter_near_cap_rows": ("adapter_near_cap", "sum"),
        "plain_near_cap_rows": ("plain_near_cap", "sum"),
    }
    for metric in ["final_cpu_time", "protocol_accounted_time", "final_decisions", "final_conflicts"]:
        for prefix in ["adapter_minus_plain", "adapter_minus_static", "adapter_minus_cached", "cached_minus_static"]:
            column = f"{prefix}_{metric}"
            if column in wide.columns:
                agg[f"mean_{column}"] = (column, "mean")
                agg[f"median_{column}"] = (column, "median")
                agg[f"improved_rows_{column}"] = (column, lambda values: int((pd.to_numeric(values, errors="coerce") < 0.0).sum()))
    for metric_column in [
        "warmup_cpu_time__event_adapter_final",
        "static_inference_wall_time__event_adapter_final",
        "event_attach_wall_time__event_adapter_final",
        "adapter_inference_wall_time__event_adapter_final",
        "event_state_l2_sum__event_adapter_final",
        "event_state_nonzero_vars__event_adapter_final",
    ]:
        if metric_column in wide.columns:
            agg[f"mean_{metric_column}"] = (metric_column, "mean")
    out = wide.groupby(group_cols, sort=True).agg(**agg).reset_index()
    out["adapter_final_solve_better_than_static"] = out["mean_adapter_minus_static_final_cpu_time"] < 0
    out["adapter_final_solve_worse_than_static"] = out["mean_adapter_minus_static_final_cpu_time"] > 0
    out["adapter_final_solve_better_than_plain"] = out["mean_adapter_minus_plain_final_cpu_time"] < 0
    out["protocol_loses_to_plain"] = out["mean_adapter_minus_plain_protocol_accounted_time"] > 0
    out["event_overhead_dominates_plain_gap"] = (
        out["mean_cached_minus_static_protocol_accounted_time"]
        > out["mean_adapter_minus_plain_protocol_accounted_time"].abs()
    )
    out["cap_risk"] = out["adapter_near_cap_rows"] > 0
    return out


def family_summary(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family, group in base.groupby("family", sort=True):
        rows.append(
            {
                "family": family,
                "bases": int(group["base_instance_id"].nunique()),
                "mean_adapter_minus_plain_protocol": float(group["mean_adapter_minus_plain_protocol_accounted_time"].mean()),
                "mean_adapter_minus_plain_final_cpu": float(group["mean_adapter_minus_plain_final_cpu_time"].mean()),
                "mean_adapter_minus_static_final_cpu": float(group["mean_adapter_minus_static_final_cpu_time"].mean()),
                "mean_cached_minus_static_protocol": float(group["mean_cached_minus_static_protocol_accounted_time"].mean()),
                "final_solve_better_than_static_bases": int(group["adapter_final_solve_better_than_static"].sum()),
                "final_solve_worse_than_static_bases": int(group["adapter_final_solve_worse_than_static"].sum()),
                "final_solve_better_than_plain_bases": int(group["adapter_final_solve_better_than_plain"].sum()),
                "cap_risk_bases": int(group["cap_risk"].sum()),
                "mean_warmup_cpu": float(group["mean_warmup_cpu_time__event_adapter_final"].mean()),
                "mean_adapter_inference_wall": float(group["mean_adapter_inference_wall_time__event_adapter_final"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("mean_adapter_minus_plain_protocol").reset_index(drop=True)


def final_params_for_warmup(warmup_cpu_lim: float, warmup_conflicts: int, trace_lbd: int, rnd_freq: float, k_value: float) -> dict[str, Any]:
    params = clean_solver_params({"rnd-freq": rnd_freq, "K": k_value})
    params = apply_rollout_budget(
        params,
        budget_type="conflicts",
        cpu_lim=solver_cli_number(warmup_cpu_lim),
        conflicts=int(warmup_conflicts),
    )
    params["collect-events"] = True
    params["trace-lbd"] = int(trace_lbd)
    return params


def param_shift_rows(
    *,
    checkpoint: Path,
    manifest: pd.DataFrame,
    observations: pd.DataFrame,
    event_state_features: str,
    warmup_cpu_lim: float,
    warmup_conflicts: int,
    trace_lbd: int,
    rnd_freq: float,
    k_value: float,
    solver: str,
    device: str,
) -> pd.DataFrame:
    if observations.empty:
        return pd.DataFrame()
    model, transform, model_cfg = load_checkpoint(str(checkpoint), var_output=True)
    model.to(device)
    model.eval()
    expected_dim = event_state_dim(event_state_features)
    if int(getattr(model, "var_state_dim", 0)) != expected_dim:
        raise ValueError(f"checkpoint var_state_dim={getattr(model, 'var_state_dim', 0)} does not match {event_state_features} dim {expected_dim}")
    scale_sigma = finite_float(model_cfg.get("scale_sigma", 0.1), default=0.1) if hasattr(model_cfg, "get") else 0.1
    manifest_lookup = {
        (str(row["base_instance_id"]), str(row["variant"])): row
        for _, row in manifest.iterrows()
    }
    warmup_params = final_params_for_warmup(
        warmup_cpu_lim=warmup_cpu_lim,
        warmup_conflicts=warmup_conflicts,
        trace_lbd=trace_lbd,
        rnd_freq=rnd_freq,
        k_value=k_value,
    )
    rows: list[dict[str, Any]] = []
    for _, obs in observations.sort_values(["base_instance_id", "variant", "repeat_id"]).iterrows():
        key = (str(obs["base_instance_id"]), str(obs["variant"]))
        instance = manifest_lookup.get(key)
        if instance is None:
            continue
        dataset = make_dimacs_dataset([str(resolve(instance["cnf_path"]))], transform=transform)
        loader = DataLoader(dataset=dataset, batch_size=1, num_workers=0, shuffle=False)
        static_graphs = sample_var_params(
            model=model,
            loader=loader,
            num_samples=1,
            device=device,
            use_mode=True,
            scale_sigma=float(scale_sigma),
            add_timing=False,
            cache_var_features=True,
        )
        if len(static_graphs) != 1:
            raise RuntimeError(f"expected one static graph for {key}, got {len(static_graphs)}")
        static_graph = static_graphs[0]
        warmup = run_solver_batch(
            dataset=dataset,
            graphs=[static_graph],
            guided=True,
            solver=solver,
            seed=int(obs["warmup_seed"]),
            solver_params=warmup_params,
            num_workers=1,
            phase_name="random_control_param_shift_warmup",
            repeat_id=int(obs["repeat_id"]),
        )
        warmup_row = warmup.iloc[0]
        refined = attach_var_event_state(
            static_graph,
            stats=warmup_row,
            var_state_dim=expected_dim,
            momentum=0.0,
            feature_mode=event_state_features,
        )
        adapter_loader = DataLoader(dataset=[refined], batch_size=1, num_workers=0, shuffle=False)
        adapter_graphs = sample_var_params(
            model=model,
            loader=adapter_loader,
            num_samples=1,
            device=device,
            use_mode=True,
            scale_sigma=float(scale_sigma),
            add_timing=False,
            cache_var_features=False,
        )
        adapter_graph = adapter_graphs[0]
        static_params = graph_var_params_array(static_graph)
        adapter_params = graph_var_params_array(adapter_graph)
        if static_params.shape != adapter_params.shape:
            raise ValueError(f"param shape mismatch for {key}: {static_params.shape} vs {adapter_params.shape}")
        phase_delta = adapter_params[:, 0] - static_params[:, 0]
        weight_delta = adapter_params[:, 1] - static_params[:, 1]
        weight_ratio = adapter_params[:, 1] / np.clip(static_params[:, 1], 1.0e-12, None)
        event_state = getattr(refined["var"], "event_state", None)
        if event_state is None:
            event_l2 = np.zeros(static_params.shape[0], dtype=np.float64)
        else:
            event_l2 = event_state.detach().cpu().to(dtype=torch.float32).norm(dim=1).numpy().astype(np.float64)
        rows.append(
            {
                "family": str(obs["family"]),
                "base_instance_id": str(obs["base_instance_id"]),
                "variant": str(obs["variant"]),
                "repeat_id": int(obs["repeat_id"]),
                "instance_id": str(instance["instance_id"]),
                "num_vars": int(instance["num_vars"]),
                "num_clauses": int(instance["num_clauses"]),
                "adapter_minus_plain_final_cpu_time": finite_float(obs.get("adapter_minus_plain_final_cpu_time")),
                "adapter_minus_plain_protocol_accounted_time": finite_float(obs.get("adapter_minus_plain_protocol_accounted_time")),
                "adapter_minus_plain_final_decisions": finite_float(obs.get("adapter_minus_plain_final_decisions")),
                "adapter_minus_plain_final_conflicts": finite_float(obs.get("adapter_minus_plain_final_conflicts")),
                "adapter_minus_static_final_cpu_time": finite_float(obs.get("adapter_minus_static_final_cpu_time")),
                "adapter_minus_cached_final_cpu_time": finite_float(obs.get("adapter_minus_cached_final_cpu_time")),
                "warmup_cpu_time": finite_float(warmup_row.get("CPU time")),
                "warmup_decisions": finite_float(warmup_row.get("decisions")),
                "warmup_conflicts": finite_float(warmup_row.get("conflicts")),
                "event_state_l2_sum_replayed": float(event_l2.sum()),
                "event_state_nonzero_vars_replayed": int((event_l2 > 1.0e-9).sum()),
                "phase_flip_count": int(np.abs(phase_delta).sum()),
                "phase_flip_frac": float((np.abs(phase_delta) > 0.0).mean()),
                "static_phase_one_frac": float((static_params[:, 0] > 0.5).mean()),
                "adapter_phase_one_frac": float((adapter_params[:, 0] > 0.5).mean()),
                "weight_static_mean": float(static_params[:, 1].mean()),
                "weight_adapter_mean": float(adapter_params[:, 1].mean()),
                "weight_delta_mean": float(weight_delta.mean()),
                "weight_delta_abs_mean": float(np.abs(weight_delta).mean()),
                "weight_delta_abs_max": float(np.abs(weight_delta).max()) if weight_delta.size else 0.0,
                "weight_ratio_mean": float(np.mean(weight_ratio)),
                "weight_ratio_max": float(np.max(weight_ratio)) if weight_ratio.size else float("nan"),
                "weight_ratio_min": float(np.min(weight_ratio)) if weight_ratio.size else float("nan"),
                "weight_rank_spearman": float(pd.Series(static_params[:, 1]).corr(pd.Series(adapter_params[:, 1]), method="spearman")),
                "event_l2_weight_abs_delta_spearman": float(pd.Series(event_l2).corr(pd.Series(np.abs(weight_delta)), method="spearman")),
                "event_l2_phase_flip_mean": float(event_l2[np.abs(phase_delta) > 0.0].mean()) if bool((np.abs(phase_delta) > 0.0).any()) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int = 20) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                if math.isfinite(value):
                    cells.append(f"{value:.6g}")
                else:
                    cells.append("nan")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(
    *,
    path: Path,
    random_base: pd.DataFrame,
    symmetry_base: pd.DataFrame,
    param_rows: pd.DataFrame,
    family: pd.DataFrame,
    checkpoint: Path,
    per_instance: Path,
) -> None:
    random_summary = random_base[
        [
            "base_instance_id",
            "scale",
            "mean_adapter_minus_plain_final_cpu_time",
            "mean_adapter_minus_plain_protocol_accounted_time",
            "mean_adapter_minus_static_final_cpu_time",
            "mean_adapter_minus_plain_final_decisions",
            "mean_adapter_minus_plain_final_conflicts",
            "mean_cached_minus_static_protocol_accounted_time",
            "mean_warmup_cpu_time__event_adapter_final",
            "adapter_final_solve_better_than_static",
        ]
    ].sort_values("mean_adapter_minus_plain_final_cpu_time")
    symmetry_summary = symmetry_base[
        [
            "family",
            "base_instance_id",
            "scale",
            "mean_adapter_minus_plain_final_cpu_time",
            "mean_adapter_minus_plain_protocol_accounted_time",
            "mean_adapter_minus_static_final_cpu_time",
            "mean_adapter_minus_cached_final_cpu_time",
            "mean_cached_minus_static_protocol_accounted_time",
            "mean_warmup_cpu_time__event_adapter_final",
            "adapter_near_cap_rows",
            "cap_risk",
        ]
    ].sort_values(["family", "mean_adapter_minus_plain_protocol_accounted_time"], ascending=[True, False])
    param_summary = (
        param_rows.groupby("base_instance_id", sort=True)
        .agg(
            rows=("repeat_id", "size"),
            phase_flip_frac_mean=("phase_flip_frac", "mean"),
            weight_delta_abs_mean=("weight_delta_abs_mean", "mean"),
            weight_ratio_mean=("weight_ratio_mean", "mean"),
            weight_ratio_max=("weight_ratio_max", "max"),
            weight_rank_spearman_mean=("weight_rank_spearman", "mean"),
            event_l2_weight_abs_delta_spearman_mean=("event_l2_weight_abs_delta_spearman", "mean"),
            final_cpu_delta_mean=("adapter_minus_plain_final_cpu_time", "mean"),
            decisions_delta_mean=("adapter_minus_plain_final_decisions", "mean"),
            conflicts_delta_mean=("adapter_minus_plain_final_conflicts", "mean"),
        )
        .reset_index()
        .sort_values("final_cpu_delta_mean")
        if not param_rows.empty
        else pd.DataFrame()
    )
    random_better_final = int(random_base["adapter_final_solve_better_than_plain"].sum())
    random_better_static = int(random_base["adapter_final_solve_better_than_static"].sum())
    random_count = int(random_base["base_instance_id"].nunique())
    symmetry_count = int(symmetry_base["base_instance_id"].nunique())
    symmetry_static_worse = int(symmetry_base["adapter_final_solve_worse_than_static"].sum())
    symmetry_cap = int(symmetry_base["cap_risk"].sum())
    mean_hex_torus_overhead = float(symmetry_base["mean_cached_minus_static_protocol_accounted_time"].mean())
    mean_hex_torus_adapter_final = float(symmetry_base["mean_adapter_minus_static_final_cpu_time"].mean())
    lines = [
        "# GRPO Control Wins vs Symmetry Family Losses",
        "",
        "This is a targeted post-hoc diagnosis of existing GRPO runtime outputs. It does not expand the benchmark and does not train or build a gate.",
        "",
        "## Inputs",
        "",
        f"- checkpoint: `{checkpoint}`",
        f"- per-instance runtime CSV: `{per_instance}`",
        "",
        "## Headline",
        "",
        f"- random-control bases where adapter final CPU beats plain: {random_better_final}/{random_count}",
        f"- random-control bases where adapter final CPU beats static weighted: {random_better_static}/{random_count}",
        f"- hex/torus bases audited: {symmetry_count}",
        f"- hex/torus bases where adapter final solve is worse than static weighted: {symmetry_static_worse}/{symmetry_count}",
        f"- hex/torus bases with adapter final CPU within 80% of cap: {symmetry_cap}/{symmetry_count}",
        f"- mean hex/torus event-collection overhead delta: {mean_hex_torus_overhead:.6g}s",
        f"- mean hex/torus adapter-minus-static final CPU delta: {mean_hex_torus_adapter_final:.6g}s",
        "",
        "Interpretation: random-control wins look generic rather than symmetry-specific unless they correlate with valid symmetry evidence. The audited random controls show adapter-induced phase/weight shifts, while hex/torus losses are dominated by large event-collection overhead plus several cases where the adapter final solve is itself worse than static weighted.",
        "",
        "## Random Controls",
        "",
        *markdown_table(random_summary, max_rows=30),
        "",
        "## Random Control Parameter Shifts",
        "",
        *markdown_table(param_summary, max_rows=30),
        "",
        "## Dominating Set Hex / Vertex Cover Torus",
        "",
        *markdown_table(symmetry_summary, max_rows=40),
        "",
        "## Family-Level Decomposition",
        "",
        *markdown_table(family, max_rows=30),
        "",
        "## Notes",
        "",
        "- `adapter_minus_static_final_cpu_time` isolates adapter final-solve effect after static weighted guidance.",
        "- `cached_minus_static_protocol_accounted_time` is the event warmup/attach overhead paid before adapter inference.",
        "- `phase_flip_frac` and weight deltas come from replaying the short warmup and doing model forward only; no final solver benchmark was rerun for these parameter-shift rows.",
        "- A negative final CPU delta on non-symmetric controls is generic search perturbation evidence, not SAT symmetry evidence.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose GRPO random-control wins vs hex/torus symmetry losses.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--per-instance-csv", type=Path, default=DEFAULT_PER_INSTANCE)
    parser.add_argument("--attribution-csv", type=Path, default=DEFAULT_ATTRIBUTION)
    parser.add_argument("--vs-plain-base-csv", type=Path, default=DEFAULT_VS_PLAIN_BASE)
    parser.add_argument("--random-base-csv", type=Path, default=DEFAULT_RANDOM_BASE)
    parser.add_argument("--symmetry-base-csv", type=Path, default=DEFAULT_SYMMETRY_BASE)
    parser.add_argument("--random-param-csv", type=Path, default=DEFAULT_RANDOM_PARAM)
    parser.add_argument("--family-csv", type=Path, default=DEFAULT_FAMILY)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--event-state-features", default="enhanced", choices=["legacy", "enhanced", "polarity"])
    parser.add_argument("--warmup-cpu-lim", type=float, default=5.0)
    parser.add_argument("--warmup-conflicts", type=int, default=20)
    parser.add_argument("--trace-lbd", type=int, default=2)
    parser.add_argument("--rnd-freq", type=float, default=0.0)
    parser.add_argument("--K", type=float, default=0.1)
    parser.add_argument("--solver", default="glucose")
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--skip-param-shift", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    checkpoint = resolve(args.checkpoint).resolve()
    manifest_path = resolve(args.manifest).resolve()
    per_instance_path = resolve(args.per_instance_csv).resolve()
    per_instance = pd.read_csv(per_instance_path)
    manifest = pd.read_csv(manifest_path)
    wide = method_wide(per_instance)
    base = aggregate_base(wide)
    random_base = base[base["family"].astype(str).eq("random_3sat_control")].copy()
    symmetry_base = base[base["family"].astype(str).isin(TARGET_SYMMETRY_FAMILIES)].copy()
    family = family_summary(base[base["family"].astype(str).isin(TARGET_SYMMETRY_FAMILIES | {"random_3sat_control"})].copy())

    random_base_path = resolve(args.random_base_csv)
    symmetry_base_path = resolve(args.symmetry_base_csv)
    family_path = resolve(args.family_csv)
    random_base_path.parent.mkdir(parents=True, exist_ok=True)
    random_base.to_csv(random_base_path, index=False)
    symmetry_base.to_csv(symmetry_base_path, index=False)
    family.to_csv(family_path, index=False)

    param_path = resolve(args.random_param_csv)
    if args.skip_param_shift:
        param_rows = pd.DataFrame()
    else:
        random_obs = wide[wide["family"].astype(str).eq("random_3sat_control")].copy()
        param_rows = param_shift_rows(
            checkpoint=checkpoint,
            manifest=manifest,
            observations=random_obs,
            event_state_features=str(args.event_state_features),
            warmup_cpu_lim=float(args.warmup_cpu_lim),
            warmup_conflicts=int(args.warmup_conflicts),
            trace_lbd=int(args.trace_lbd),
            rnd_freq=float(args.rnd_freq),
            k_value=float(args.K),
            solver=str(args.solver),
            device=str(args.device),
        )
    param_path.parent.mkdir(parents=True, exist_ok=True)
    param_rows.to_csv(param_path, index=False)

    write_doc(
        path=resolve(args.doc),
        random_base=random_base,
        symmetry_base=symmetry_base,
        param_rows=param_rows,
        family=family,
        checkpoint=checkpoint,
        per_instance=per_instance_path,
    )
    print(f"wrote {random_base_path}")
    print(f"wrote {symmetry_base_path}")
    print(f"wrote {param_path}")
    print(f"wrote {family_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
