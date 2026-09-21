from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULTS = [
    "--manifest",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_manifest.csv"),
    "--per-instance-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_per_instance.csv"),
    "--phases-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_phases.csv"),
    "--by-family-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_by_family.csv"),
    "--by-base-instance-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_by_base_instance.csv"),
    "--attribution-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_attribution.csv"),
    "--attribution-by-base-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_attribution_by_base.csv"),
    "--loss-diagnostics-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_guided_loss_diagnostics.csv"),
    "--timeout-correctness-csv",
    str(ROOT / "runs/analysis/symmetry_runtime_protocol_v1_timeout_correctness.csv"),
    "--doc",
    str(ROOT / "docs/symmetry_runtime_protocol_v1.md"),
]


def main() -> None:
    if "--weighted-no-pre" in sys.argv[1:]:
        raise SystemExit(
            "runtime_protocol_v1 is locked to solver_path_role=patched_pretrue_main. "
            "Use run_symmetry_solver_protocol_preflight.py --weighted-no-pre only for diagnostic appendix runs."
        )
    import run_symmetry_solver_protocol_preflight as preflight

    sys.argv = [sys.argv[0], *DEFAULTS, *sys.argv[1:]]
    preflight.main()


if __name__ == "__main__":
    main()
