from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_AdapterDelta_v2_Full/iter=235.pt"
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_runtime_v12_canonical_manifest.csv"
DEFAULT_OUT_PREFIX = ROOT / "runs/analysis/echosat_runtime_v12_canonical_low_warmup"
DEFAULT_DOC_PREFIX = ROOT / "docs/echosat_runtime_v12_canonical_low_warmup"
DEFAULT_BUDGETS = [1, 3, 5]
DEFAULT_FAMILIES = ["complete_coloring", "php", "random_3sat_control", "subset_cardinality"]


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def budget_prefix(prefix: Path, budget: int) -> Path:
    return prefix.with_name(f"{prefix.name}_wc{int(budget)}")


def protocol_command(args: argparse.Namespace, budget: int) -> tuple[list[str], Path]:
    out = budget_prefix(resolve(args.out_prefix), budget)
    doc = budget_prefix(resolve(args.doc_prefix), budget).with_suffix(".md")
    per_instance = out.with_name(f"{out.name}_per_instance.csv")
    command = [
        sys.executable,
        str(ROOT / "run_symmetry_solver_protocol_preflight.py"),
        "--checkpoint",
        str(resolve(args.checkpoint)),
        "--manifest",
        str(resolve(args.manifest)),
        "--per-instance-csv",
        str(per_instance),
        "--phases-csv",
        str(out.with_name(f"{out.name}_phases.csv")),
        "--by-family-csv",
        str(out.with_name(f"{out.name}_by_family.csv")),
        "--by-base-instance-csv",
        str(out.with_name(f"{out.name}_by_base_instance.csv")),
        "--attribution-csv",
        str(out.with_name(f"{out.name}_attribution.csv")),
        "--attribution-by-base-csv",
        str(out.with_name(f"{out.name}_attribution_by_base.csv")),
        "--loss-diagnostics-csv",
        str(out.with_name(f"{out.name}_guided_loss_diagnostics.csv")),
        "--timeout-correctness-csv",
        str(out.with_name(f"{out.name}_timeout_correctness.csv")),
        "--doc",
        str(doc),
        "--families",
        *args.families,
        "--repeats",
        str(int(args.repeats)),
        "--final-cpu-lim",
        str(float(args.final_cpu_lim)),
        "--warmup-cpu-lim",
        str(float(args.warmup_cpu_lim)),
        "--warmup-conflicts",
        str(int(budget)),
        "--trace-lbd",
        str(int(args.trace_lbd)),
        "--seed",
        str(int(args.seed)),
        "--num-workers",
        str(int(args.num_workers)),
        "--batch-size",
        str(int(args.batch_size)),
        "--loader-workers",
        str(int(args.loader_workers)),
        "--device",
        str(args.device),
        "--event-state-features",
        str(args.event_state_features),
        "--solver",
        str(args.solver),
    ]
    return command, per_instance


def analysis_command(args: argparse.Namespace, per_instance_paths: list[Path]) -> list[str]:
    out_prefix = resolve(args.out_prefix)
    doc_prefix = resolve(args.doc_prefix)
    return [
        sys.executable,
        str(ROOT / "analyze_echosat_runtime_v12_canonical.py"),
        "--per-instance-csvs",
        *[str(path) for path in per_instance_paths],
        "--observations-csv",
        str(out_prefix.with_name(f"{out_prefix.name}_observations.csv")),
        "--overall-csv",
        str(out_prefix.with_name(f"{out_prefix.name}_overall.csv")),
        "--by-family-csv",
        str(out_prefix.with_name(f"{out_prefix.name}_by_family.csv")),
        "--by-base-csv",
        str(out_prefix.with_name(f"{out_prefix.name}_by_base.csv")),
        "--doc",
        str(doc_prefix.with_name("echosat_runtime_v12_canonical_low_warmup.md")),
        "--families",
        *args.families,
    ]


def run_or_print(command: list[str], dry_run: bool) -> None:
    print(shlex.join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=str(ROOT), check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EchoSAT runtime protocol v1.2 canonical low-warmup sweep.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-prefix", type=Path, default=DEFAULT_OUT_PREFIX)
    parser.add_argument("--doc-prefix", type=Path, default=DEFAULT_DOC_PREFIX)
    parser.add_argument("--families", nargs="*", default=DEFAULT_FAMILIES)
    parser.add_argument("--budgets", nargs="*", type=int, default=DEFAULT_BUDGETS)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--final-cpu-lim", type=float, default=10.0)
    parser.add_argument("--warmup-cpu-lim", type=float, default=5.0)
    parser.add_argument("--trace-lbd", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--num-workers", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--loader-workers", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--event-state-features", default="enhanced", choices=["legacy", "enhanced", "polarity"])
    parser.add_argument("--solver", default="glucose")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--skip-analysis", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if "--weighted-no-pre" in sys.argv[1:]:
        raise SystemExit("Runtime v1.2 canonical protocol is locked to patched_pretrue_main; do not pass --weighted-no-pre.")
    if not resolve(args.manifest).exists():
        raise SystemExit(
            f"Canonical v1.2 manifest does not exist: {resolve(args.manifest)}. "
            "Run build_echosat_runtime_v12_canonical_manifest.py first."
        )
    per_instance_paths: list[Path] = []
    for budget in args.budgets:
        command, per_instance = protocol_command(args, int(budget))
        per_instance_paths.append(per_instance)
        if bool(args.skip_existing) and per_instance.exists():
            print(f"skip existing {per_instance}", flush=True)
            continue
        run_or_print(command, dry_run=bool(args.dry_run))
    if not bool(args.skip_analysis):
        run_or_print(analysis_command(args, per_instance_paths), dry_run=bool(args.dry_run))


if __name__ == "__main__":
    main()
