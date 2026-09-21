from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

from build_symmetry_family_heldout_trace import slug


ROOT = Path(__file__).resolve().parent
DEFAULT_SEEDS = [1729, 1730, 1731]


def parse_csv_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def pascal_from_slug(value: str) -> str:
    return "".join(part.capitalize() for part in slug(value).split("_") if part)


def load_split_summary(path: Path, families: list[str] | None = None) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if families:
        known = set(frame["heldout_family"].astype(str))
        unknown = sorted(set(families).difference(known))
        if unknown:
            raise ValueError(f"Unknown heldout families: {unknown}")
        frame = frame[frame["heldout_family"].astype(str).isin(families)].copy()
    return frame.reset_index(drop=True)


def command_to_text(command: list[str]) -> str:
    return " ".join(command)


def run_command(command: list[str], log_path: Path, dry_run: bool = False) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(command_to_text(command))
        return
    with log_path.open("w", encoding="utf-8") as log:
        log.write(command_to_text(command) + "\n\n")
        log.flush()
        subprocess.run(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )


def add_seed_column(path: Path, seed: int) -> None:
    frame = pd.read_csv(path)
    if "train_seed" not in frame.columns:
        frame.insert(0, "train_seed", int(seed))
    else:
        frame["train_seed"] = int(seed)
    frame.to_csv(path, index=False)


def train_checkpoint(
    python: Path,
    family: str,
    seed: int,
    train_trace: Path,
    model_prefix: str,
    permutation_consistency_weight: float | None,
    use_cuda: bool,
    force: bool,
    dry_run: bool,
    log_dir: Path,
) -> Path:
    family_slug = slug(family)
    model_name = f"{model_prefix}{pascal_from_slug(family)}_Seed{seed}"
    model_dir = ROOT / "runs" / model_name
    checkpoint = model_dir / "best.pt"
    if checkpoint.exists() and not force:
        print(f"skip train existing {checkpoint}")
        return checkpoint
    command = [
        str(python),
        "train_trace_distill.py",
        "--config-name",
        "config_train_trace_distill_symmetry",
        f"seed={int(seed)}",
        f"model_name={model_name}",
        f"model_dir=runs/{model_name}",
        f"trace.data_path={train_trace}",
        f"training.use_cuda={'true' if use_cuda else 'false'}",
        f"training.use_amp={'true' if use_cuda else 'false'}",
    ]
    if permutation_consistency_weight is not None:
        command.append(f"trace.label.permutation_consistency_weight={float(permutation_consistency_weight)}")
    log_path = log_dir / f"train_{family_slug}_seed{seed}.log"
    print(f"train heldout={family} seed={seed}")
    run_command(command, log_path=log_path, dry_run=dry_run)
    return checkpoint


def audit_checkpoint(
    python: Path,
    family: str,
    seed: int,
    checkpoint: Path,
    trace: Path,
    manifest: Path,
    device: str,
    output_prefix: str,
    event_state_features: str,
    force: bool,
    dry_run: bool,
    log_dir: Path,
) -> Path:
    family_slug = slug(family)
    orbit_csv = ROOT / "runs/analysis" / f"{output_prefix}_{family_slug}_seed{seed}_orbits.csv"
    stats_csv = ROOT / "runs/analysis" / f"{output_prefix}_{family_slug}_seed{seed}_stats.csv"
    doc = ROOT / "docs" / f"{output_prefix}_{family_slug}_seed{seed}_audit.md"
    if orbit_csv.exists() and stats_csv.exists() and doc.exists() and not force:
        print(f"skip audit existing {orbit_csv}")
        return orbit_csv
    command = [
        str(python),
        "audit_cached_adapter_symmetry.py",
        "--checkpoint",
        str(checkpoint),
        "--trace",
        str(trace),
        "--manifest",
        str(manifest),
        "--output-csv",
        str(orbit_csv),
        "--stats-csv",
        str(stats_csv),
        "--doc",
        str(doc),
        "--heldout-family",
        family,
        "--event-state-features",
        event_state_features,
        "--device",
        device,
    ]
    log_path = log_dir / f"audit_{family_slug}_seed{seed}.log"
    print(f"audit heldout={family} seed={seed}")
    run_command(command, log_path=log_path, dry_run=dry_run)
    if not dry_run:
        add_seed_column(orbit_csv, seed=seed)
        add_seed_column(stats_csv, seed=seed)
    return orbit_csv


def summarize(
    python: Path,
    orbit_csvs: list[Path],
    baseline_csv: Path,
    summary_prefix: str,
    doc: Path,
    log_dir: Path,
    dry_run: bool,
) -> None:
    command = [
        str(python),
        "summarize_adapter_family_heldout_multiseed.py",
        "--baseline-csv",
        str(baseline_csv),
        "--output-csv",
        str(ROOT / "runs/analysis" / f"{summary_prefix}_by_family.csv"),
        "--seed-summary-csv",
        str(ROOT / "runs/analysis" / f"{summary_prefix}_seed_summary.csv"),
        "--eval-family-csv",
        str(ROOT / "runs/analysis" / f"{summary_prefix}_eval_family.csv"),
        "--doc",
        str(doc),
    ]
    for path in orbit_csvs:
        command.extend(["--input-csv", str(path)])
    log_path = log_dir / "summarize.log"
    print("summarize multiseed heldout")
    run_command(command, log_path=log_path, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-seed leave-one-family-out NegGate adapter audits.")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--split-summary", type=Path, default=ROOT / "runs/analysis/symmetry_family_heldout_trace_splits.csv")
    parser.add_argument("--trace", type=Path, default=ROOT / "data/trace_distill/symmetry_event_trace.pt")
    parser.add_argument("--manifest", type=Path, default=ROOT / "runs/analysis/symmetry_stress_manifest.csv")
    parser.add_argument("--baseline-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_neggate_event_orbits.csv")
    parser.add_argument("--families", default="")
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--use-cuda", action="store_true")
    parser.add_argument("--model-prefix", default="GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGate_Heldout")
    parser.add_argument("--output-prefix", default="symmetry_adapter_neggate_heldout")
    parser.add_argument("--summary-prefix", default="symmetry_adapter_neggate_family_heldout_multiseed")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_adapter_neggate_family_heldout_multiseed_audit.md")
    parser.add_argument("--log-dir", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_neggate_family_heldout_multiseed/logs")
    parser.add_argument("--event-state-features", default="enhanced")
    parser.add_argument("--permutation-consistency-weight", type=float, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    families = parse_csv_list(args.families) if args.families else None
    seeds = [int(seed) for seed in parse_csv_list(args.seeds)]
    if not seeds:
        raise ValueError("At least one seed is required")
    split_summary = load_split_summary(args.split_summary, families=families)

    orbit_csvs: list[Path] = []
    for _, row in split_summary.iterrows():
        family = str(row["heldout_family"])
        train_trace = Path(str(row["train_trace_path"]))
        for seed in seeds:
            checkpoint = train_checkpoint(
                python=args.python,
                family=family,
                seed=seed,
                train_trace=train_trace,
                model_prefix=str(args.model_prefix),
                permutation_consistency_weight=args.permutation_consistency_weight,
                use_cuda=bool(args.use_cuda),
                force=bool(args.force),
                dry_run=bool(args.dry_run),
                log_dir=args.log_dir,
            )
            orbit_csv = audit_checkpoint(
                python=args.python,
                family=family,
                seed=seed,
                checkpoint=checkpoint,
                trace=args.trace,
                manifest=args.manifest,
                device=str(args.device),
                output_prefix=str(args.output_prefix),
                event_state_features=str(args.event_state_features),
                force=bool(args.force),
                dry_run=bool(args.dry_run),
                log_dir=args.log_dir,
            )
            orbit_csvs.append(orbit_csv)

    summarize(
        python=args.python,
        orbit_csvs=orbit_csvs,
        baseline_csv=args.baseline_csv,
        summary_prefix=str(args.summary_prefix),
        doc=args.doc,
        log_dir=args.log_dir,
        dry_run=bool(args.dry_run),
    )


if __name__ == "__main__":
    main()
