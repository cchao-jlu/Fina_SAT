from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from audit_event_symmetry import (
    add_identity_gain_columns,
    adapter_family_summary,
    annotate_event_row_validity,
    annotate_orbit_rows,
    annotate_orbit_validity,
    event_state_orbit_rows,
    markdown_table,
    model_supports_event_adapter,
    normalized_orbit_entropy,
    orbit_entropy,
    tensor_orbit_rows,
)
from build_symmetry_family_heldout_trace import cnf_id_to_manifest_row, event_manifest, graph_cnf_id, int_value, load_trace_payload
from src.data.symmetry import read_orbits_json
from src.model.model import load_checkpoint
from src.solving.state import event_state_dim


ROOT = Path(__file__).resolve().parent


def bool_series(frame: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=bool)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(default).astype(bool)
    normalized = values.fillna(str(default)).astype(str).str.strip().str.lower()
    return normalized.isin({"1", "true", "yes", "y"})


def sample_id_value(graph: Any) -> int:
    value = getattr(graph, "sample_id", 0)
    return int_value(value)


def stats_by_key(solver_stats: pd.DataFrame) -> dict[tuple[int, int], pd.Series]:
    if solver_stats.empty:
        return {}
    required = {"cnf_id", "sample_id"}
    missing = required.difference(solver_stats.columns)
    if missing:
        raise ValueError(f"solver_stats missing required columns: {sorted(missing)}")
    return {
        (int(row["cnf_id"]), int(row["sample_id"])): row
        for _, row in solver_stats.iterrows()
    }


def entropy_norm(variable_orbits: dict[int, str]) -> tuple[float, float]:
    return float(orbit_entropy(variable_orbits)), float(normalized_orbit_entropy(variable_orbits))


def audit_cached_graph(
    graph: Any,
    stats_row: pd.Series,
    instance: pd.Series,
    model: torch.nn.Module,
    checkpoint_path: Path,
    device: str,
    event_state_features: str,
    min_orbit_size: int,
    static_collapse_threshold: float,
    event_identity_eps: float,
    heldout_family: str,
) -> pd.DataFrame:
    expected_dim = event_state_dim(event_state_features)
    if not hasattr(graph["var"], "event_state"):
        raise ValueError(f"cached graph cnf_id={graph_cnf_id(graph)} has no var.event_state")
    if int(graph["var"].event_state.shape[1]) != expected_dim:
        raise ValueError(
            f"event_state_features={event_state_features} has dim {expected_dim}, "
            f"but cached graph has dim {int(graph['var'].event_state.shape[1])}"
        )
    if not model_supports_event_adapter(model):
        raise ValueError(f"checkpoint does not expose an event adapter: {checkpoint_path}")
    model_var_state_dim = int(getattr(model, "var_state_dim", 0))
    if model_var_state_dim != expected_dim:
        raise ValueError(
            f"event_state_features={event_state_features} has dim {expected_dim}, "
            f"but checkpoint model.var_state_dim={model_var_state_dim}."
        )

    variable_orbits = read_orbits_json(
        Path(str(instance["orbits_path"])),
        num_vars=int(graph["var"].base_y.shape[0]),
    )
    entropy, entropy_normalized = entropy_norm(variable_orbits)

    static_rows = pd.DataFrame(tensor_orbit_rows(graph["var"].base_y, variable_orbits, prefix="static"))
    event_rows = pd.DataFrame(event_state_orbit_rows(graph["var"].event_state, variable_orbits))
    model.eval()
    with torch.no_grad():
        batch = next(iter(DataLoader(dataset=[graph], batch_size=1, num_workers=0, shuffle=False))).to(device)
        adapted_y = model(batch).detach().cpu()
    adapted_rows = pd.DataFrame(tensor_orbit_rows(adapted_y, variable_orbits, prefix="adapted"))
    rows = static_rows.merge(event_rows, on=["orbit", "orbit_size"], how="outer")
    rows = rows.merge(adapted_rows, on=["orbit", "orbit_size"], how="outer")
    rows = add_identity_gain_columns(rows)
    rows = annotate_orbit_validity(rows, min_orbit_size=min_orbit_size)
    rows = annotate_orbit_rows(
        rows,
        instance=instance,
        checkpoint_path=checkpoint_path,
        solver=str(stats_row.get("solver", "cached_trace")),
        rollout_budget_type=str(stats_row.get("rollout_budget_type", "cached_trace")),
        rollout_cpu_lim=float(stats_row.get("cpu-lim", math.nan)) if not pd.isna(stats_row.get("cpu-lim", math.nan)) else math.nan,
        rollout_conflicts=int(stats_row.get("conflict_budget", 0)) if not pd.isna(stats_row.get("conflict_budget", 0)) else 0,
        event_state_features=event_state_features,
        adapter_supported=True,
    )
    rows = annotate_event_row_validity(
        rows,
        solver_stats=pd.DataFrame([stats_row]),
        static_collapse_threshold=static_collapse_threshold,
        event_identity_eps=event_identity_eps,
    )
    rows["orbit_entropy"] = entropy
    rows["orbit_entropy_norm"] = entropy_normalized
    rows["cnf_id"] = graph_cnf_id(graph)
    rows["sample_id"] = sample_id_value(graph)
    rows["heldout_family"] = heldout_family
    rows["adapter_train_split"] = "heldout" if str(instance["family"]) == heldout_family else "train"
    return rows


def audit_cached_trace(
    checkpoint: Path,
    trace_path: Path,
    manifest_path: Path,
    device: str,
    event_state_features: str,
    min_orbit_size: int,
    static_collapse_threshold: float,
    event_identity_eps: float,
    heldout_family: str,
    families: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    checkpoint = checkpoint.resolve()
    model, _, _ = load_checkpoint(str(checkpoint), var_output=True)
    model.to(device)
    payload = load_trace_payload(trace_path)
    manifest = event_manifest(manifest_path)
    manifest_by_cnf = cnf_id_to_manifest_row(payload, manifest)
    if families:
        allowed_cnf_ids = {
            int(cnf_id)
            for cnf_id, row in manifest_by_cnf.items()
            if str(row["family"]) in families
        }
    else:
        allowed_cnf_ids = set(manifest_by_cnf)
    stats_lookup = stats_by_key(payload["solver_stats"])

    orbit_frames = []
    stats_rows = []
    for graph in payload["graphs"]:
        cnf_id = graph_cnf_id(graph)
        if cnf_id not in allowed_cnf_ids:
            continue
        if cnf_id not in manifest_by_cnf:
            raise KeyError(f"cnf_id={cnf_id} is not present in the event manifest")
        key = (cnf_id, sample_id_value(graph))
        if key not in stats_lookup:
            raise KeyError(f"solver_stats missing cnf_id/sample_id={key}")
        instance = manifest_by_cnf[cnf_id]
        stats_row = stats_lookup[key]
        orbit_frames.append(
            audit_cached_graph(
                graph=graph,
                stats_row=stats_row,
                instance=instance,
                model=model,
                checkpoint_path=checkpoint,
                device=device,
                event_state_features=event_state_features,
                min_orbit_size=min_orbit_size,
                static_collapse_threshold=static_collapse_threshold,
                event_identity_eps=event_identity_eps,
                heldout_family=heldout_family,
            )
        )
        stats_copy = stats_row.copy()
        stats_copy["family"] = str(instance["family"])
        stats_copy["instance_id"] = str(instance["instance_id"])
        stats_copy["base_instance_id"] = str(instance["base_instance_id"])
        stats_copy["variant"] = str(instance["variant"])
        stats_copy["heldout_family"] = heldout_family
        stats_copy["adapter_train_split"] = "heldout" if str(instance["family"]) == heldout_family else "train"
        stats_rows.append(stats_copy)

    if not orbit_frames:
        raise ValueError("No cached trace graphs selected.")
    return pd.concat(orbit_frames, ignore_index=True), pd.DataFrame(stats_rows)


def split_summary(orbit_frame: pd.DataFrame) -> pd.DataFrame:
    if orbit_frame.empty:
        return pd.DataFrame()
    rows = []
    for (heldout_family, split), group in orbit_frame.groupby(["heldout_family", "adapter_train_split"], sort=True):
        valid = group[bool_series(group, "event_row_valid", default=False)].copy()
        positive = group[bool_series(group, "event_identity_positive", default=False)].copy()
        rows.append(
            {
                "heldout_family": heldout_family,
                "adapter_train_split": split,
                "families": int(group["family"].nunique()),
                "instances": int(group["instance_id"].nunique()),
                "orbit_rows": int(len(group)),
                "valid_rollout_rows": int(len(valid)),
                "event_positive_rows": int(len(positive)),
                "mean_event_l2_valid": float(valid["event_feature_l2_range"].mean()) if not valid.empty else float("nan"),
                "mean_adapted_mu_range_valid": float(valid["adapted_mu_range"].mean()) if not valid.empty else float("nan"),
                "mean_adapter_gain_valid": float(valid["adapter_identity_gain"].mean()) if not valid.empty else float("nan"),
                "max_adapter_gain_valid": float(valid["adapter_identity_gain"].max()) if not valid.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def write_doc(path: Path, orbit_frame: pd.DataFrame, stats_frame: pd.DataFrame, checkpoint: Path, trace_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    family_summary = adapter_family_summary(orbit_frame)
    split_view = split_summary(orbit_frame)
    stats_columns = [
        column
        for column in ["family", "instance_id", "variant", "conflicts", "decisions", "CPU time", "heldout_family", "adapter_train_split"]
        if column in stats_frame.columns
    ]
    lines = [
        "# Cached Adapter Symmetry Audit",
        "",
        f"- checkpoint: `{checkpoint}`",
        f"- cached trace: `{trace_path}`",
        "",
        "This audit reuses cached short-rollout event states and measures adapter",
        "representation behavior only. It does not run or compare solver speed.",
        "",
        "## Split Summary",
        "",
        *markdown_table(split_view),
        "",
        "## Family Summary",
        "",
        *markdown_table(family_summary),
        "",
        "## Trace Rows",
        "",
        *markdown_table(stats_frame[stats_columns].head(40) if stats_columns else pd.DataFrame()),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit an event adapter on cached symmetry trace graphs.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--trace", type=Path, default=ROOT / "data/trace_distill/symmetry_event_trace.pt")
    parser.add_argument("--manifest", type=Path, default=ROOT / "runs/analysis/symmetry_stress_manifest.csv")
    parser.add_argument("--output-csv", type=Path, default=ROOT / "runs/analysis/symmetry_cached_adapter_orbits.csv")
    parser.add_argument("--stats-csv", type=Path, default=ROOT / "runs/analysis/symmetry_cached_adapter_stats.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_cached_adapter_audit.md")
    parser.add_argument("--heldout-family", default="none")
    parser.add_argument("--families", default="")
    parser.add_argument("--event-state-features", choices=["legacy", "enhanced", "polarity"], default="enhanced")
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--min-orbit-size", type=int, default=2)
    parser.add_argument("--static-collapse-threshold", type=float, default=1.0e-4)
    parser.add_argument("--event-identity-eps", type=float, default=1.0e-6)
    args = parser.parse_args()

    families = {part.strip() for part in args.families.split(",") if part.strip()}
    orbit_frame, stats_frame = audit_cached_trace(
        checkpoint=args.checkpoint,
        trace_path=args.trace,
        manifest_path=args.manifest,
        device=str(args.device),
        event_state_features=str(args.event_state_features),
        min_orbit_size=int(args.min_orbit_size),
        static_collapse_threshold=float(args.static_collapse_threshold),
        event_identity_eps=float(args.event_identity_eps),
        heldout_family=str(args.heldout_family),
        families=families or None,
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    orbit_frame.to_csv(args.output_csv, index=False)
    args.stats_csv.parent.mkdir(parents=True, exist_ok=True)
    stats_frame.to_csv(args.stats_csv, index=False)
    write_doc(args.doc, orbit_frame=orbit_frame, stats_frame=stats_frame, checkpoint=args.checkpoint, trace_path=args.trace)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.stats_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
