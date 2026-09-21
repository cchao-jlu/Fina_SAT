from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from build_symmetry_family_heldout_trace import build_splits, event_manifest


ROOT = Path(__file__).resolve().parent


def slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower()


def camel_slug(value: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def run_command(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def selected_families(manifest_path: Path, families_raw: str) -> list[str]:
    manifest = event_manifest(manifest_path)
    all_families = sorted(manifest["family"].astype(str).unique())
    if not families_raw.strip():
        return all_families
    requested = [part.strip() for part in families_raw.split(",") if part.strip()]
    unknown = sorted(set(requested).difference(all_families))
    if unknown:
        raise ValueError(f"Unknown heldout families: {unknown}")
    return requested


def main() -> None:
    parser = argparse.ArgumentParser(description="Run leave-one-family-out symmetry adapter audits.")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--trace", type=Path, default=ROOT / "data/trace_distill/symmetry_event_trace.pt")
    parser.add_argument("--manifest", type=Path, default=ROOT / "runs/analysis/symmetry_stress_manifest.csv")
    parser.add_argument("--split-dir", type=Path, default=ROOT / "data/trace_distill/symmetry_family_heldout")
    parser.add_argument("--split-summary-csv", type=Path, default=ROOT / "runs/analysis/symmetry_family_heldout_trace_splits.csv")
    parser.add_argument("--analysis-dir", type=Path, default=ROOT / "runs/analysis")
    parser.add_argument("--docs-dir", type=Path, default=ROOT / "docs")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "runs")
    parser.add_argument("--config-name", default="config_train_trace_distill_symmetry")
    parser.add_argument("--families", default="")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--event-state-features", choices=["legacy", "enhanced", "polarity"], default="enhanced")
    parser.add_argument("--baseline-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_event_orbits.csv")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-audit", action="store_true")
    args = parser.parse_args()

    families = selected_families(args.manifest, args.families)
    split_summary = build_splits(
        trace_path=args.trace,
        manifest_path=args.manifest,
        output_dir=args.split_dir,
        heldout_families=families,
    )
    args.split_summary_csv.parent.mkdir(parents=True, exist_ok=True)
    split_summary.to_csv(args.split_summary_csv, index=False)
    print(f"wrote {args.split_summary_csv}", flush=True)

    audit_csvs: list[Path] = []
    for family in families:
        family_slug = slug(family)
        model_name = f"GNN_Glucose_3SAT_SymmetryTraceAdapter_Heldout{camel_slug(family)}"
        model_dir = args.runs_dir / model_name
        train_trace = args.split_dir / f"symmetry_event_trace_train_without_{family_slug}.pt"
        checkpoint = model_dir / "best.pt"
        if not args.skip_train and (args.force or not checkpoint.exists()):
            run_command(
                [
                    args.python,
                    "train_trace_distill.py",
                    "--config-name",
                    args.config_name,
                    f"trace.data_path={train_trace.relative_to(ROOT)}",
                    f"model_name={model_name}",
                    f"model_dir={model_dir.relative_to(ROOT)}",
                    f"training.epochs={int(args.epochs)}",
                    "training.use_cuda=false",
                    "training.use_amp=false",
                ]
            )
        if not checkpoint.exists():
            raise FileNotFoundError(f"missing heldout checkpoint: {checkpoint}")

        orbit_csv = args.analysis_dir / f"symmetry_adapter_heldout_{family_slug}_orbits.csv"
        stats_csv = args.analysis_dir / f"symmetry_adapter_heldout_{family_slug}_stats.csv"
        doc_path = args.docs_dir / f"symmetry_adapter_heldout_{family_slug}_audit.md"
        audit_csvs.append(orbit_csv)
        if not args.skip_audit and (args.force or not orbit_csv.exists()):
            run_command(
                [
                    args.python,
                    "audit_cached_adapter_symmetry.py",
                    "--checkpoint",
                    str(checkpoint),
                    "--trace",
                    str(args.trace),
                    "--manifest",
                    str(args.manifest),
                    "--output-csv",
                    str(orbit_csv),
                    "--stats-csv",
                    str(stats_csv),
                    "--doc",
                    str(doc_path),
                    "--heldout-family",
                    family,
                    "--event-state-features",
                    args.event_state_features,
                    "--device",
                    args.device,
                ]
            )

    summary_cmd = [
        args.python,
        "summarize_adapter_family_heldout.py",
        "--baseline-csv",
        str(args.baseline_csv),
        "--output-csv",
        str(args.analysis_dir / "symmetry_adapter_family_heldout_by_family.csv"),
        "--summary-csv",
        str(args.analysis_dir / "symmetry_adapter_family_heldout_summary.csv"),
        "--doc",
        str(args.docs_dir / "symmetry_adapter_family_heldout_audit.md"),
    ]
    for csv_path in audit_csvs:
        summary_cmd.extend(["--input-csv", str(csv_path)])
    run_command(summary_cmd)


if __name__ == "__main__":
    main()
