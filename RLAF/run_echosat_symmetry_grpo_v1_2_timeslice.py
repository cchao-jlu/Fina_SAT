from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN_DIR = ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full"
PREFIX = "echosat_symmetry_grpo_v1_2_timeslice"
CHECKPOINTS = [
    "iter=0",
    "iter=5",
    "iter=10",
    "iter=15",
    "iter=20",
    "iter=25",
    "iter=50",
    "iter=80",
    "iter=85",
    "iter=90",
    "iter=120",
    "iter=160",
    "iter=200",
    "iter=235",
    "best",
]


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
    parser = argparse.ArgumentParser(description="Run v1.2 hard-negative checkpoint time-slice acceptance.")
    parser.add_argument("--checkpoints", nargs="*", default=CHECKPOINTS)
    parser.add_argument("--budgets", nargs="*", type=int, default=[1, 3])
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected = list(args.checkpoints)
    for label in selected:
        checkpoint = checkpoint_path(label)
        if not checkpoint.exists():
            raise FileNotFoundError(checkpoint)
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
            *[str(budget) for budget in args.budgets],
        ]
        if args.skip_existing:
            command.append("--skip-existing")
        run(command, dry_run=bool(args.dry_run))

    summary_command = [
        sys.executable,
        str(ROOT / "summarize_echosat_symmetry_grpo_timeslice.py"),
        "--prefix",
        PREFIX,
        "--checkpoints",
        *selected,
    ]
    run(summary_command, dry_run=bool(args.dry_run))


if __name__ == "__main__":
    main()
