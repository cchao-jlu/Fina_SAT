from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from src.data.dataset import DimacsCNFDataset
from src.data.symmetry import orbit_validity, read_orbits_json
from src.model.model import load_checkpoint


ROOT = Path(__file__).resolve().parent


def make_dimacs_dataset(cnf_path: Path, transform) -> DimacsCNFDataset:
    try:
        return DimacsCNFDataset(str(cnf_path), transform=transform, lazy=True)
    except TypeError:
        return DimacsCNFDataset(str(cnf_path), transform=transform)


def graph_outputs(checkpoint: Path, cnf_path: Path, device: str):
    model, transform, model_cfg = load_checkpoint(str(checkpoint), var_output=True)
    model.to(device)
    model.eval()
    dataset = make_dimacs_dataset(cnf_path, transform=transform)
    loader = DataLoader(dataset=dataset, batch_size=1, num_workers=0, shuffle=False)
    with torch.no_grad():
        data = next(iter(loader)).to(device)
        y_var = model(data).detach().cpu()
    return y_var, model_cfg


def orbit_summary(
    instance: pd.Series,
    checkpoint: Path,
    device: str,
    min_orbit_size: int,
) -> list[dict[str, object]]:
    cnf_path = Path(str(instance["cnf_path"]))
    orbits_path = Path(str(instance["orbits_path"]))
    y_var, _ = graph_outputs(checkpoint=checkpoint, cnf_path=cnf_path, device=device)
    orbits = read_orbits_json(orbits_path, num_vars=y_var.shape[0])
    rows = []
    for orbit_id in sorted(set(orbits.values())):
        variables = [var for var, orbit in sorted(orbits.items()) if orbit == orbit_id]
        orbit_valid, orbit_valid_reason = orbit_validity(
            orbit_id,
            orbit_size=len(variables),
            min_orbit_size=min_orbit_size,
        )
        idx = torch.tensor([var - 1 for var in variables], dtype=torch.long)
        values = y_var[idx]
        rows.append(
            {
                "family": str(instance["family"]),
                "instance_id": str(instance["instance_id"]),
                "base_instance_id": str(instance["base_instance_id"]),
                "variant": str(instance["variant"]),
                "orbit": orbit_id,
                "orbit_size": int(len(variables)),
                "orbit_valid": bool(orbit_valid),
                "orbit_valid_reason": orbit_valid_reason,
                "rho_mean": float(values[:, 0].mean()),
                "rho_std": float(values[:, 0].std(unbiased=False)),
                "rho_range": float(values[:, 0].max() - values[:, 0].min()),
                "mu_mean": float(values[:, 1].mean()),
                "mu_std": float(values[:, 1].std(unbiased=False)),
                "mu_range": float(values[:, 1].max() - values[:, 1].min()),
            }
        )
    return rows


def permutation_stability_summary(orbit_frame: pd.DataFrame) -> pd.DataFrame:
    if orbit_frame.empty:
        return pd.DataFrame()
    if "orbit_valid" in orbit_frame.columns:
        orbit_frame = orbit_frame[orbit_frame["orbit_valid"].astype(bool)].copy()
        if orbit_frame.empty:
            return pd.DataFrame()
    rows = []
    for (family, base_instance_id, orbit), group in orbit_frame.groupby(
        ["family", "base_instance_id", "orbit"],
        sort=True,
    ):
        if group["variant"].nunique() <= 1:
            continue
        rows.append(
            {
                "family": family,
                "base_instance_id": base_instance_id,
                "orbit": orbit,
                "variants": int(group["variant"].nunique()),
                "rho_mean_across_variant_std": float(group["rho_mean"].std(ddof=0)),
                "mu_mean_across_variant_std": float(group["mu_mean"].std(ddof=0)),
                "max_rho_orbit_range": float(group["rho_range"].max()),
                "max_mu_orbit_range": float(group["mu_range"].max()),
            }
        )
    return pd.DataFrame(rows)


def write_doc(path: Path, orbit_frame: pd.DataFrame, stability: pd.DataFrame, checkpoint: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    valid_frame = (
        orbit_frame[orbit_frame["orbit_valid"].astype(bool)].copy()
        if "orbit_valid" in orbit_frame.columns
        else orbit_frame.copy()
    )
    family_summary = (
        valid_frame.groupby("family", sort=True)
        .agg(
            instances=("instance_id", "nunique"),
            orbits=("orbit", "count"),
            valid_orbit_rows=("orbit_valid", "sum") if "orbit_valid" in valid_frame.columns else ("orbit", "count"),
            mean_rho_range=("rho_range", "mean"),
            max_rho_range=("rho_range", "max"),
            mean_mu_range=("mu_range", "mean"),
            max_mu_range=("mu_range", "max"),
        )
        .reset_index()
        if not valid_frame.empty
        else pd.DataFrame()
    )
    validity_summary = (
        orbit_frame.groupby(["family", "orbit_valid_reason"], sort=True)
        .agg(rows=("orbit", "count"))
        .reset_index()
        if "orbit_valid_reason" in orbit_frame.columns and not orbit_frame.empty
        else pd.DataFrame()
    )
    stability_summary = (
        stability.groupby("family", sort=True)
        .agg(
            groups=("orbit", "count"),
            mean_rho_variant_std=("rho_mean_across_variant_std", "mean"),
            max_rho_variant_std=("rho_mean_across_variant_std", "max"),
            mean_mu_variant_std=("mu_mean_across_variant_std", "mean"),
            max_mu_variant_std=("mu_mean_across_variant_std", "max"),
        )
        .reset_index()
        if not stability.empty
        else pd.DataFrame()
    )

    def table(frame: pd.DataFrame) -> list[str]:
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

    lines = [
        "# Static Symmetry Audit",
        "",
        f"- checkpoint: `{checkpoint}`",
        "",
        "This audit measures whether the static GNN guidance assigns nearly",
        "identical `rho` and `mu` outputs to variables in the same hand-labelled",
        "symmetry orbit, and how stable orbit means are under variable renaming.",
        "",
        "## Orbit Collapse",
        "",
        *table(family_summary),
        "",
        "## Orbit Row Filter",
        "",
        *table(validity_summary),
        "",
        "## Permutation Stability",
        "",
        *table(stability_summary),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit static GNN behavior on symmetry stress instances.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/symmetry_stress/manifest.csv")
    parser.add_argument("--output-csv", type=Path, default=ROOT / "runs/analysis/symmetry_static_orbits.csv")
    parser.add_argument("--stability-csv", type=Path, default=ROOT / "runs/analysis/symmetry_static_permutation_stability.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_static_audit.md")
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--min-orbit-size", type=int, default=2)
    args = parser.parse_args()

    manifest = pd.read_csv(args.manifest)
    rows = []
    for _, instance in manifest.iterrows():
        rows.extend(
            orbit_summary(
                instance,
                checkpoint=args.checkpoint,
                device=args.device,
                min_orbit_size=int(args.min_orbit_size),
            )
        )
    orbit_frame = pd.DataFrame(rows)
    stability = permutation_stability_summary(orbit_frame)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    orbit_frame.to_csv(args.output_csv, index=False)
    args.stability_csv.parent.mkdir(parents=True, exist_ok=True)
    stability.to_csv(args.stability_csv, index=False)
    write_doc(args.doc, orbit_frame=orbit_frame, stability=stability, checkpoint=args.checkpoint)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.stability_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
