from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import torch


ROOT = Path(__file__).resolve().parent


def int_value(value: Any) -> int:
    if hasattr(value, "item"):
        return int(value.item())
    if isinstance(value, (list, tuple)):
        return int_value(value[0])
    return int(value)


def graph_cnf_id(graph: Any) -> int:
    return int_value(getattr(graph, "cnf_id"))


def load_trace_payload(path: Path) -> dict[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(payload, dict) and "graphs" in payload and "solver_stats" in payload:
        return dict(payload)
    if isinstance(payload, list):
        return {"graphs": payload, "solver_stats": pd.DataFrame()}
    raise ValueError(f"Trace payload must be a graph list or a dict with graphs and solver_stats: {path}")


def event_manifest(manifest_path: Path) -> pd.DataFrame:
    manifest = pd.read_csv(manifest_path)
    if "event_audit_role" in manifest.columns:
        manifest = manifest[manifest["event_audit_role"].fillna("event").astype(str) != "static_only"].copy()
    return manifest.reset_index(drop=True)


def family_by_cnf_id(manifest: pd.DataFrame) -> dict[int, str]:
    return {int(idx): str(row["family"]) for idx, row in manifest.iterrows()}


def cnf_id_to_manifest_row(payload: dict[str, Any], manifest: pd.DataFrame) -> dict[int, pd.Series]:
    solver_stats = payload.get("solver_stats")
    if isinstance(solver_stats, pd.DataFrame) and not solver_stats.empty and "file" in solver_stats.columns:
        by_path = {
            str(Path(path).resolve()): row
            for _, row in manifest.iterrows()
            for path in [row["cnf_path"]]
        }
        mapping: dict[int, pd.Series] = {}
        for cnf_id, group in solver_stats.groupby("cnf_id", sort=True):
            files = sorted({str(Path(path).resolve()) for path in group["file"].dropna().astype(str)})
            if len(files) != 1:
                raise ValueError(f"cnf_id={cnf_id} maps to {len(files)} files: {files}")
            file_path = files[0]
            if file_path not in by_path:
                raise KeyError(f"solver_stats file is absent from manifest: {file_path}")
            mapping[int(cnf_id)] = by_path[file_path]
        return mapping
    return {int(idx): row for idx, row in manifest.iterrows()}


def cnf_id_to_family(payload: dict[str, Any], manifest: pd.DataFrame) -> dict[int, str]:
    return {cnf_id: str(row["family"]) for cnf_id, row in cnf_id_to_manifest_row(payload, manifest).items()}


def filter_payload_by_family(
    payload: dict[str, Any],
    manifest: pd.DataFrame,
    heldout_family: str,
    keep_heldout: bool,
) -> dict[str, Any]:
    cnf_to_family = cnf_id_to_family(payload, manifest)
    graphs = []
    for graph in payload["graphs"]:
        family = cnf_to_family.get(graph_cnf_id(graph))
        if family is None:
            raise KeyError(f"cnf_id={graph_cnf_id(graph)} is not present in the event manifest")
        if (family == heldout_family) == keep_heldout:
            graphs.append(graph)

    solver_stats = payload.get("solver_stats")
    if isinstance(solver_stats, pd.DataFrame) and not solver_stats.empty:
        stats = solver_stats.copy()
        stats_family = stats["cnf_id"].astype(int).map(cnf_to_family)
        stats = stats[(stats_family == heldout_family) == keep_heldout].reset_index(drop=True)
    else:
        stats = pd.DataFrame()

    split_payload = dict(payload)
    split_payload["graphs"] = graphs
    split_payload["solver_stats"] = stats
    split_payload["heldout_family"] = heldout_family
    split_payload["split_role"] = "heldout" if keep_heldout else "train_without_heldout"
    split_payload["source_graphs"] = len(payload["graphs"])
    split_payload["source_solver_stats_rows"] = int(len(solver_stats)) if isinstance(solver_stats, pd.DataFrame) else 0
    return split_payload


def write_split(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)


def slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower()


def build_splits(
    trace_path: Path,
    manifest_path: Path,
    output_dir: Path,
    heldout_families: list[str] | None = None,
) -> pd.DataFrame:
    payload = load_trace_payload(trace_path)
    manifest = event_manifest(manifest_path)
    all_families = sorted(manifest["family"].astype(str).unique())
    if heldout_families is None:
        heldout_families = all_families
    unknown = sorted(set(heldout_families).difference(all_families))
    if unknown:
        raise ValueError(f"Unknown heldout families: {unknown}")

    rows = []
    for family in heldout_families:
        family_slug = slug(family)
        train_payload = filter_payload_by_family(payload, manifest, family, keep_heldout=False)
        heldout_payload = filter_payload_by_family(payload, manifest, family, keep_heldout=True)
        train_path = output_dir / f"symmetry_event_trace_train_without_{family_slug}.pt"
        heldout_path = output_dir / f"symmetry_event_trace_heldout_{family_slug}.pt"
        write_split(train_path, train_payload)
        write_split(heldout_path, heldout_payload)
        rows.append(
            {
                "heldout_family": family,
                "train_graphs": len(train_payload["graphs"]),
                "heldout_graphs": len(heldout_payload["graphs"]),
                "train_stats_rows": int(len(train_payload["solver_stats"])),
                "heldout_stats_rows": int(len(heldout_payload["solver_stats"])),
                "train_trace_path": str(train_path),
                "heldout_trace_path": str(heldout_path),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build leave-one-family-out trace distillation splits.")
    parser.add_argument("--trace", type=Path, default=ROOT / "data/trace_distill/symmetry_event_trace.pt")
    parser.add_argument("--manifest", type=Path, default=ROOT / "runs/analysis/symmetry_stress_manifest.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/trace_distill/symmetry_family_heldout")
    parser.add_argument("--heldout-family", action="append", default=None)
    parser.add_argument("--summary-csv", type=Path, default=ROOT / "runs/analysis/symmetry_family_heldout_trace_splits.csv")
    args = parser.parse_args()

    summary = build_splits(
        trace_path=args.trace,
        manifest_path=args.manifest,
        output_dir=args.output_dir,
        heldout_families=args.heldout_family,
    )
    args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_csv, index=False)
    print(f"wrote {args.summary_csv}")


if __name__ == "__main__":
    main()
