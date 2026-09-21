from __future__ import annotations

import argparse
import shlex
import subprocess
import sys

from echosat_iter15_acceptance_common import (
    DEFAULT_BUDGETS,
    DEFAULT_FAMILIES,
    ROOT,
    candidate_by_label,
    existing_per_instance_path,
    targeted_doc_prefix,
    targeted_prefix,
    targeted_per_instance_path,
)


def run(command: list[str], *, dry_run: bool) -> None:
    print(shlex.join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=str(ROOT), check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run iter=15 targeted acceptance without training.")
    parser.add_argument("--candidates", nargs="*", default=None)
    parser.add_argument("--budgets", nargs="*", type=int, default=DEFAULT_BUDGETS)
    parser.add_argument("--families", nargs="*", default=DEFAULT_FAMILIES)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates = candidate_by_label(args.candidates)
    budgets = [int(budget) for budget in args.budgets]

    for candidate in candidates:
        if not candidate.checkpoint_path.exists():
            raise FileNotFoundError(candidate.checkpoint_path)

        missing_budgets: list[int] = []
        for budget in budgets:
            existing, source = existing_per_instance_path(candidate, budget)
            if existing is not None and bool(args.skip_existing):
                print(f"reuse {source} {existing}", flush=True)
                continue
            if existing is None or not bool(args.skip_existing):
                target = targeted_per_instance_path(candidate, budget)
                if bool(args.skip_existing) and target.exists():
                    print(f"skip existing {target}", flush=True)
                else:
                    missing_budgets.append(int(budget))

        if missing_budgets:
            command = [
                sys.executable,
                str(ROOT / "run_echosat_runtime_v12_canonical_low_warmup.py"),
                "--checkpoint",
                str(candidate.checkpoint_path),
                "--out-prefix",
                str(targeted_prefix(candidate)),
                "--doc-prefix",
                str(targeted_doc_prefix(candidate)),
                "--families",
                *args.families,
                "--budgets",
                *[str(budget) for budget in missing_budgets],
                "--skip-analysis",
            ]
            if args.skip_existing:
                command.append("--skip-existing")
            run(command, dry_run=bool(args.dry_run))

    summary_command = [
        sys.executable,
        str(ROOT / "summarize_echosat_iter15_targeted_acceptance.py"),
        "--budgets",
        *[str(budget) for budget in budgets],
    ]
    if args.candidates:
        summary_command += ["--candidates", *args.candidates]
    run(summary_command, dry_run=bool(args.dry_run))


if __name__ == "__main__":
    main()
