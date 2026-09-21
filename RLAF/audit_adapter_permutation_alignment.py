from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from audit_cached_adapter_symmetry import sample_id_value, stats_by_key
from build_symmetry_family_heldout_trace import cnf_id_to_manifest_row, event_manifest, graph_cnf_id, load_trace_payload
from src.data.symmetry import orbit_validity, read_orbits_json
from src.model.model import load_checkpoint
from src.solving.state import event_state_dim


ROOT = Path(__file__).resolve().parent


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def permutation_from_metadata(instance: pd.Series) -> tuple[list[int], list[int], bool]:
    metadata_path = Path(str(instance.get("metadata_path", "")))
    if not metadata_path.exists():
        return [], [], False
    payload = read_json(metadata_path)
    permutation = payload.get("permutation")
    sign_flips = payload.get("sign_flips")
    if not isinstance(permutation, list):
        return [], [], False
    signs = list(sign_flips) if isinstance(sign_flips, list) else [1] * len(permutation)
    return [int(value) for value in permutation], [int(value) for value in signs], True


def inverse_align_new_to_old(tensor: torch.Tensor, permutation_old_to_new: list[int]) -> torch.Tensor:
    if tensor.dim() == 1:
        tensor = tensor.view(-1, 1)
    if tensor.shape[0] != len(permutation_old_to_new):
        raise ValueError(
            f"tensor has {tensor.shape[0]} variables but permutation has {len(permutation_old_to_new)} entries"
        )
    indices = torch.tensor([int(new_var) - 1 for new_var in permutation_old_to_new], dtype=torch.long)
    return tensor[indices]


def tensor_l2(values: torch.Tensor) -> torch.Tensor:
    if values.dim() == 1:
        values = values.view(-1, 1)
    return values.to(dtype=torch.float32).norm(dim=1)


def abs_column(values: torch.Tensor, column: int) -> torch.Tensor:
    if values.dim() == 1:
        values = values.view(-1, 1)
    if values.shape[1] <= column:
        return torch.full((values.shape[0],), float("nan"), dtype=torch.float32)
    return values[:, column].abs().to(dtype=torch.float32)


def metric_summary(prefix: str, diff: torch.Tensor) -> dict[str, float]:
    if diff.dim() == 1:
        diff = diff.view(-1, 1)
    diff = diff.to(dtype=torch.float32)
    l2 = tensor_l2(diff)
    row: dict[str, float] = {
        f"{prefix}_l2_mean": float(l2.mean()),
        f"{prefix}_l2_median": float(l2.median()),
        f"{prefix}_l2_max": float(l2.max()),
    }
    if diff.shape[1] >= 1:
        rho = abs_column(diff, 0)
        row[f"{prefix}_rho_mae"] = float(rho.mean())
        row[f"{prefix}_rho_max_abs"] = float(rho.max())
    if diff.shape[1] >= 2:
        mu = abs_column(diff, 1)
        row[f"{prefix}_mu_mae"] = float(mu.mean())
        row[f"{prefix}_mu_max_abs"] = float(mu.max())
    return row


def graph_outputs(model: torch.nn.Module, graph: Any, device: str) -> dict[str, torch.Tensor]:
    model.eval()
    with torch.no_grad():
        batch = next(iter(DataLoader(dataset=[graph], batch_size=1, num_workers=0, shuffle=False))).to(device)
        adapted = model(batch).detach().cpu()
    return {
        "static": graph["var"].base_y.detach().cpu().to(dtype=torch.float32),
        "event": graph["var"].event_state.detach().cpu().to(dtype=torch.float32),
        "adapted": adapted.to(dtype=torch.float32),
    }


def variable_orbit_rows(base_instance: pd.Series, num_vars: int, min_orbit_size: int) -> dict[int, dict[str, object]]:
    orbits = read_orbits_json(Path(str(base_instance["orbits_path"])), num_vars=num_vars)
    orbit_sizes = pd.Series(list(orbits.values())).value_counts().to_dict()
    rows: dict[int, dict[str, object]] = {}
    for var in range(1, num_vars + 1):
        orbit = str(orbits.get(var, f"singleton:{var}"))
        orbit_size = int(orbit_sizes.get(orbit, 1))
        valid, reason = orbit_validity(orbit, orbit_size=orbit_size, min_orbit_size=min_orbit_size)
        rows[var] = {
            "base_var": int(var),
            "orbit": orbit,
            "orbit_size": orbit_size,
            "orbit_valid": bool(valid),
            "orbit_valid_reason": reason,
        }
    return rows


def pair_alignment_rows(
    base_graph: Any,
    perm_graph: Any,
    base_instance: pd.Series,
    perm_instance: pd.Series,
    base_outputs: dict[str, torch.Tensor],
    perm_outputs: dict[str, torch.Tensor],
    checkpoint: Path,
    event_state_features: str,
    min_orbit_size: int,
    include_signed: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    permutation, sign_flips, metadata_available = permutation_from_metadata(perm_instance)
    if not metadata_available:
        raise ValueError(f"Missing permutation metadata for {perm_instance['instance_id']}")
    if len(permutation) != int(base_outputs["static"].shape[0]):
        raise ValueError(
            f"Permutation length mismatch for {perm_instance['instance_id']}: "
            f"{len(permutation)} vs {int(base_outputs['static'].shape[0])}"
        )
    signs_all_positive = all(int(sign) == 1 for sign in sign_flips)
    if not signs_all_positive and not include_signed:
        raise ValueError(f"Signed permutation is not supported without --include-signed: {perm_instance['instance_id']}")

    aligned = {name: inverse_align_new_to_old(values, permutation) for name, values in perm_outputs.items()}
    diffs = {name: aligned[name] - base_outputs[name] for name in ["static", "event", "adapted"]}
    num_vars = int(base_outputs["static"].shape[0])
    orbit_rows = variable_orbit_rows(base_instance, num_vars=num_vars, min_orbit_size=min_orbit_size)

    summary: dict[str, object] = {
        "family": str(base_instance["family"]),
        "base_instance_id": str(base_instance["base_instance_id"]),
        "base_instance": str(base_instance["instance_id"]),
        "perm_instance": str(perm_instance["instance_id"]),
        "perm_variant": str(perm_instance["variant"]),
        "sample_id": sample_id_value(base_graph),
        "num_vars": num_vars,
        "checkpoint": str(checkpoint),
        "event_state_features": event_state_features,
        "permutation_metadata_available": bool(metadata_available),
        "sign_flips_all_positive": bool(signs_all_positive),
    }
    for name in ["static", "event", "adapted"]:
        summary.update(metric_summary(name, diffs[name]))
    if "adapted_mu_mae" in summary and "static_mu_mae" in summary:
        summary["adapted_minus_static_mu_mae"] = float(summary["adapted_mu_mae"]) - float(summary["static_mu_mae"])
    if "adapted_l2_mean" in summary and "event_l2_mean" in summary:
        denominator = max(float(summary["event_l2_mean"]), 1.0e-9)
        summary["adapted_to_event_l2_mean_ratio"] = float(summary["adapted_l2_mean"]) / denominator

    variable_rows: list[dict[str, object]] = []
    event_l2 = tensor_l2(diffs["event"])
    static_l2 = tensor_l2(diffs["static"])
    adapted_l2 = tensor_l2(diffs["adapted"])
    static_mu = abs_column(diffs["static"], 1)
    adapted_mu = abs_column(diffs["adapted"], 1)
    for old_var, new_var in enumerate(permutation, start=1):
        orbit_info = orbit_rows[old_var]
        variable_rows.append(
            {
                "family": str(base_instance["family"]),
                "base_instance_id": str(base_instance["base_instance_id"]),
                "base_instance": str(base_instance["instance_id"]),
                "perm_instance": str(perm_instance["instance_id"]),
                "perm_variant": str(perm_instance["variant"]),
                "sample_id": sample_id_value(base_graph),
                "base_var": int(old_var),
                "perm_var": int(new_var),
                **orbit_info,
                "static_l2_diff": float(static_l2[old_var - 1]),
                "static_mu_abs_diff": float(static_mu[old_var - 1]),
                "event_l2_diff": float(event_l2[old_var - 1]),
                "base_event_l2": float(tensor_l2(base_outputs["event"])[old_var - 1]),
                "aligned_perm_event_l2": float(tensor_l2(aligned["event"])[old_var - 1]),
                "adapted_l2_diff": float(adapted_l2[old_var - 1]),
                "adapted_mu_abs_diff": float(adapted_mu[old_var - 1]),
                "base_adapted_mu": float(base_outputs["adapted"][old_var - 1, 1]),
                "aligned_perm_adapted_mu": float(aligned["adapted"][old_var - 1, 1]),
            }
        )
    return summary, variable_rows


def audit_alignment(
    checkpoint: Path,
    trace_path: Path,
    manifest_path: Path,
    device: str,
    event_state_features: str,
    min_orbit_size: int,
    include_signed: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    expected_dim = event_state_dim(event_state_features)
    model, _, _ = load_checkpoint(str(checkpoint.resolve()), var_output=True)
    model.to(device)
    payload = load_trace_payload(trace_path)
    manifest = event_manifest(manifest_path)
    manifest_by_cnf = cnf_id_to_manifest_row(payload, manifest)
    stats_lookup = stats_by_key(payload["solver_stats"])

    records: dict[tuple[str, str, int], dict[str, Any]] = {}
    outputs_by_key: dict[tuple[str, str, int], dict[str, torch.Tensor]] = {}
    for graph in payload["graphs"]:
        cnf_id = graph_cnf_id(graph)
        if cnf_id not in manifest_by_cnf:
            continue
        instance = manifest_by_cnf[cnf_id]
        sample_id = sample_id_value(graph)
        if (cnf_id, sample_id) not in stats_lookup:
            continue
        if int(graph["var"].event_state.shape[1]) != expected_dim:
            raise ValueError(
                f"event_state_features={event_state_features} has dim {expected_dim}, "
                f"but graph cnf_id={cnf_id} has event_state dim {int(graph['var'].event_state.shape[1])}"
            )
        key = (str(instance["base_instance_id"]), str(instance["variant"]), sample_id)
        records[key] = {"graph": graph, "instance": instance}
        outputs_by_key[key] = graph_outputs(model, graph, device=device)

    summaries: list[dict[str, object]] = []
    variable_rows: list[dict[str, object]] = []
    base_ids = sorted({key[0] for key in records})
    for base_id in base_ids:
        sample_ids = sorted({key[2] for key in records if key[0] == base_id})
        for sample_id in sample_ids:
            base_key = (base_id, "base", sample_id)
            if base_key not in records:
                continue
            perm_keys = sorted(
                key
                for key in records
                if key[0] == base_id and key[2] == sample_id and key[1] != "base"
            )
            for perm_key in perm_keys:
                summary, variables = pair_alignment_rows(
                    base_graph=records[base_key]["graph"],
                    perm_graph=records[perm_key]["graph"],
                    base_instance=records[base_key]["instance"],
                    perm_instance=records[perm_key]["instance"],
                    base_outputs=outputs_by_key[base_key],
                    perm_outputs=outputs_by_key[perm_key],
                    checkpoint=checkpoint.resolve(),
                    event_state_features=event_state_features,
                    min_orbit_size=min_orbit_size,
                    include_signed=include_signed,
                )
                summaries.append(summary)
                variable_rows.extend(variables)
    return pd.DataFrame(summaries), pd.DataFrame(variable_rows)


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


def family_summary(pair_frame: pd.DataFrame) -> pd.DataFrame:
    if pair_frame.empty:
        return pd.DataFrame()
    return (
        pair_frame.groupby("family", sort=True)
        .agg(
            pairs=("perm_instance", "count"),
            base_instances=("base_instance_id", "nunique"),
            mean_static_mu_mae=("static_mu_mae", "mean"),
            max_static_mu_max_abs=("static_mu_max_abs", "max"),
            mean_event_l2_mean=("event_l2_mean", "mean"),
            max_event_l2_max=("event_l2_max", "max"),
            mean_adapted_mu_mae=("adapted_mu_mae", "mean"),
            max_adapted_mu_max_abs=("adapted_mu_max_abs", "max"),
            mean_adapted_minus_static_mu_mae=("adapted_minus_static_mu_mae", "mean"),
        )
        .reset_index()
    )


def write_doc(path: Path, pair_frame: pd.DataFrame, variable_frame: pd.DataFrame, checkpoint: Path, trace_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    worst_pairs = pair_frame.sort_values("adapted_mu_mae", ascending=False) if "adapted_mu_mae" in pair_frame.columns else pair_frame
    worst_variables = (
        variable_frame.sort_values("adapted_mu_abs_diff", ascending=False)
        if "adapted_mu_abs_diff" in variable_frame.columns
        else variable_frame
    )
    lines = [
        "# Adapter Variable-Level Permutation Alignment Audit",
        "",
        f"- checkpoint: `{checkpoint}`",
        f"- cached trace: `{trace_path}`",
        "",
        "This audit directly compares `P^{-1} y(P(CNF))` with `y(CNF)` using",
        "the 1-based `permutation` stored in each instance metadata file.",
        "It reports static, event-state, and adapter-output alignment errors.",
        "Because the solver rollout itself can depend on variable order, nonzero",
        "event-state alignment error is reported separately from adapter error.",
        "This is still a representation audit, not a solver speedup claim.",
        "",
        "## Family Summary",
        "",
        *markdown_table(family_summary(pair_frame)),
        "",
        "## Worst Pair Alignments",
        "",
        *markdown_table(
            worst_pairs[
                [
                    column
                    for column in [
                        "family",
                        "base_instance_id",
                        "perm_variant",
                        "static_mu_mae",
                        "event_l2_mean",
                        "adapted_mu_mae",
                        "adapted_mu_max_abs",
                        "adapted_to_event_l2_mean_ratio",
                    ]
                    if column in worst_pairs.columns
                ]
            ],
            max_rows=20,
        ),
        "",
        "## Worst Variable Alignments",
        "",
        *markdown_table(
            worst_variables[
                [
                    column
                    for column in [
                        "family",
                        "base_instance_id",
                        "perm_variant",
                        "base_var",
                        "perm_var",
                        "orbit",
                        "event_l2_diff",
                        "adapted_mu_abs_diff",
                    ]
                    if column in worst_variables.columns
                ]
            ],
            max_rows=30,
        ),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit variable-level adapter alignment under CNF variable permutation.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs/GNN_Glucose_3SAT_SymmetryTraceAdapter/best.pt")
    parser.add_argument("--trace", type=Path, default=ROOT / "data/trace_distill/symmetry_event_trace.pt")
    parser.add_argument("--manifest", type=Path, default=ROOT / "runs/analysis/symmetry_stress_manifest.csv")
    parser.add_argument("--output-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_permutation_alignment_pairs.csv")
    parser.add_argument("--variable-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_permutation_alignment_variables.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_adapter_permutation_alignment_audit.md")
    parser.add_argument("--event-state-features", choices=["legacy", "enhanced", "polarity"], default="enhanced")
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--min-orbit-size", type=int, default=2)
    parser.add_argument("--include-signed", action="store_true")
    args = parser.parse_args()

    pair_frame, variable_frame = audit_alignment(
        checkpoint=args.checkpoint,
        trace_path=args.trace,
        manifest_path=args.manifest,
        device=str(args.device),
        event_state_features=str(args.event_state_features),
        min_orbit_size=int(args.min_orbit_size),
        include_signed=bool(args.include_signed),
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    pair_frame.to_csv(args.output_csv, index=False)
    args.variable_csv.parent.mkdir(parents=True, exist_ok=True)
    variable_frame.to_csv(args.variable_csv, index=False)
    write_doc(args.doc, pair_frame=pair_frame, variable_frame=variable_frame, checkpoint=args.checkpoint, trace_path=args.trace)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.variable_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
