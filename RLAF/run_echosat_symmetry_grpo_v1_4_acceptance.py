from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN_DIR = ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest"
PREFIX = "echosat_symmetry_grpo_v1_4_acceptance"
CHECKPOINTS = ["iter=0", "iter=15", "iter=50", "iter=115", "best"]
DEFAULT_BUDGETS = [1, 3, 5]


def checkpoint_path(label: str) -> Path:
    return RUN_DIR / f"{label}.pt"


def out_prefix(label: str) -> Path:
    return ROOT / "runs/analysis" / f"{PREFIX}_{label}_canonical_low_warmup"


def doc_prefix(label: str) -> Path:
    return ROOT / "docs" / f"{PREFIX}_{label}_canonical_low_warmup"


def run(command: list[str], dry_run: bool) -> None:
    print(shlex.join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=str(ROOT), check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1.4 targeted checkpoint acceptance without training.")
    parser.add_argument("--checkpoints", nargs="*", default=CHECKPOINTS)
    parser.add_argument("--budgets", nargs="*", type=int, default=DEFAULT_BUDGETS)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected = list(args.checkpoints)
    budgets = [int(budget) for budget in args.budgets]
    existing: list[str] = []
    for label in selected:
        checkpoint = checkpoint_path(label)
        if not checkpoint.exists():
            if bool(args.dry_run):
                print(f"Dry-run uses future checkpoint path: {checkpoint}", flush=True)
            elif label == "best":
                print(f"Skipping missing optional checkpoint: {checkpoint}", flush=True)
                continue
            else:
                raise FileNotFoundError(checkpoint)
        existing.append(label)
        command = [
            sys.executable,
            str(ROOT / "run_echosat_runtime_v12_canonical_low_warmup.py"),
            "--checkpoint",
            str(checkpoint),
            "--out-prefix",
            str(out_prefix(label)),
            "--doc-prefix",
            str(doc_prefix(label)),
            "--budgets",
            *[str(budget) for budget in budgets],
        ]
        if args.skip_existing:
            command.append("--skip-existing")
        run(command, dry_run=bool(args.dry_run))

    if not existing:
        raise ValueError("no existing checkpoints were selected")
    summary_command = [
        sys.executable,
        str(ROOT / "summarize_echosat_symmetry_grpo_timeslice.py"),
        "--prefix",
        PREFIX,
        "--checkpoints",
        *existing,
        "--out-observations",
        str(ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_observations.csv"),
        "--out-family",
        str(ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_summary_by_family.csv"),
        "--out-base",
        str(ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_summary_by_base.csv"),
        "--out-strict",
        str(ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_strict_acceptance.csv"),
        "--doc",
        str(ROOT / "docs/echosat_symmetry_grpo_v1_4_acceptance.md"),
        "--title",
        "EchoSAT Symmetry GRPO v1.4 Targeted Acceptance",
        "--description",
        (
            "This is a targeted checkpoint acceptance audit for the v1.4 WC1 strict-best run. "
            "It reuses the canonical low-warmup runtime protocol and does not train a model, "
            "expand the benchmark, or add a gate/selector."
        ),
    ]
    run(summary_command, dry_run=bool(args.dry_run))


if __name__ == "__main__":
    main()
