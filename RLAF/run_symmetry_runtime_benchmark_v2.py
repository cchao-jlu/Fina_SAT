from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv"
EXPECTED_VARIANTS = ["base", "perm_seed1730", "perm_seed1731"]
LOCKED_OPTIONS = {
    "--manifest": "v2 full uses the labeled runtime benchmark v2 manifest",
    "--repeats": "v2 full repeats are fixed at 3",
    "--final-cpu-lim": "v2 full final CPU cap is fixed at 5 seconds",
    "--warmup-cpu-lim": "v2 full warmup CPU cap is fixed at 5 seconds",
    "--warmup-conflicts": "v2 full warmup conflict cap is fixed at 20",
    "--families": "v2 full must not filter families",
    "--control-types": "v2 full must not filter control types",
    "--scales": "v2 full must not filter scales",
    "--benchmark-roles": "v2 full must not filter benchmark roles",
    "--base-only": "v2 full includes base and permutation variants",
    "--include-static-only": "v2 full excludes static_only_stress rows",
    "--weighted-no-pre": "v2 full keeps solver_path_role=patched_pretrue_main",
}
DEFAULTS = [
    "--manifest",
    str(MANIFEST),
    "--per-instance-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_per_instance.csv"),
    "--phases-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_phases.csv"),
    "--by-family-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_by_family.csv"),
    "--by-base-instance-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_by_base_instance.csv"),
    "--attribution-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv"),
    "--attribution-by-base-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_attribution_by_base.csv"),
    "--loss-diagnostics-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_guided_loss_diagnostics.csv"),
    "--timeout-correctness-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_timeout_correctness.csv"),
    "--doc",
    str(ROOT / "docs/symmetry_runtime_benchmark_v2.md"),
    "--repeats",
    "3",
    "--final-cpu-lim",
    "5",
    "--warmup-cpu-lim",
    "5",
    "--warmup-conflicts",
    "20",
]


def option_name(raw: str) -> str:
    return raw.split("=", 1)[0]


def validate_args(argv: list[str]) -> None:
    locked = [option_name(arg) for arg in argv if option_name(arg) in LOCKED_OPTIONS]
    if locked:
        details = "; ".join(f"{option}: {LOCKED_OPTIONS[option]}" for option in locked)
        raise SystemExit(
            "run_symmetry_runtime_benchmark_v2.py is the locked full v2 entrypoint. "
            f"Do not override these options here: {details}. "
            "Use run_symmetry_solver_protocol_preflight.py for diagnostics or subsets."
        )


def validate_manifest(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            f"Missing v2 labeled manifest: {path}. "
            "Build runs/analysis/symmetry_runtime_benchmark_v2_manifest.csv first, then run "
            "label_random_3sat_controls.py with the v2 paths."
        )
    manifest = pd.read_csv(path)
    variants = sorted(set(manifest["variant"].astype(str)))
    if variants != EXPECTED_VARIANTS:
        raise SystemExit(
            "v2 full variant policy is fixed to base + perm_seed1730 + perm_seed1731. "
            f"Found variants: {variants}"
        )
    controls = manifest[manifest["family"].astype(str).eq("random_3sat_control")].copy()
    if controls.empty:
        raise SystemExit("v2 full manifest contains no random_3sat_control rows.")
    missing_label = controls["label_provenance"].fillna("").astype(str).eq("")
    missing_result = ~controls["expected_result"].astype(str).isin({"SATISFIABLE", "UNSATISFIABLE"})
    if bool((missing_label | missing_result).any()):
        bad = controls.loc[
            missing_label | missing_result,
            ["instance_id", "variant", "expected_result", "label_provenance"],
        ].head(10)
        raise SystemExit(
            "random_3sat_control rows must carry Glucose/CaDiCaL provenance labels before v2 full. "
            f"First bad rows:\n{bad.to_string(index=False)}"
        )


def main() -> None:
    validate_args(sys.argv[1:])
    validate_manifest(MANIFEST)
    import run_symmetry_solver_protocol_preflight as preflight

    sys.argv = [sys.argv[0], *DEFAULTS, *sys.argv[1:]]
    preflight.main()


if __name__ == "__main__":
    main()
