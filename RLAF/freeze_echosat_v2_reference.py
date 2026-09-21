from pathlib import Path

from src.echosat.reference import freeze_reference_artifacts


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "runs/analysis/echosat_v2_reference/reference.json"
ARTIFACTS = [
    ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt",
    ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv",
    ROOT / "runs/analysis/echosat_orbit_certification.csv",
    ROOT / "docs/echosat_runtime_v12_canonical_low_warmup.md",
]


def main() -> None:
    payload = freeze_reference_artifacts(
        root=ROOT,
        artifacts=ARTIFACTS,
        output_path=OUTPUT,
        metadata={
            "schema_version": 1,
            "reference_checkpoint": "v1.2_iter15_wc1",
            "purpose": "EchoSAT v2 Stage 0-4 frozen reference",
        },
    )
    print(f"wrote {OUTPUT} artifacts={len(payload['artifacts'])}")


if __name__ == "__main__":
    main()
