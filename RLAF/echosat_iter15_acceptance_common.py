from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TARGET_PREFIX = "echosat_iter15_targeted_acceptance"
DEFAULT_BUDGETS = [1, 3, 5]
DEFAULT_FAMILIES = ["complete_coloring", "php", "random_3sat_control", "subset_cardinality"]


@dataclass(frozen=True)
class Candidate:
    label: str
    display_name: str
    role: str
    checkpoint_path: Path
    reuse_prefix: str


CANDIDATES = [
    Candidate(
        label="v1_2_iter15",
        display_name="v1.2 iter=15.pt",
        role="main_candidate",
        checkpoint_path=ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt",
        reuse_prefix="echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup",
    ),
    Candidate(
        label="v1_2_best",
        display_name="v1.2 best.pt",
        role="control",
        checkpoint_path=ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/best.pt",
        reuse_prefix="echosat_symmetry_grpo_v1_2_timeslice_best_canonical_low_warmup",
    ),
    Candidate(
        label="v1_2_iter235",
        display_name="v1.2 iter=235.pt",
        role="control",
        checkpoint_path=ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=235.pt",
        reuse_prefix="echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup",
    ),
    Candidate(
        label="v1_1_iter85",
        display_name="v1.1 iter=85.pt",
        role="control",
        checkpoint_path=ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_1_Full/iter=85.pt",
        reuse_prefix="echosat_symmetry_grpo_v1_1_timeslice_iter=85_canonical_low_warmup",
    ),
    Candidate(
        label="v1_2_iter50",
        display_name="v1.2 iter=50.pt",
        role="wc3_diagnostic",
        checkpoint_path=ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=50.pt",
        reuse_prefix="echosat_symmetry_grpo_v1_2_timeslice_iter=50_canonical_low_warmup",
    ),
]


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def candidate_by_label(labels: list[str] | None = None) -> list[Candidate]:
    if not labels:
        return list(CANDIDATES)
    lookup = {candidate.label: candidate for candidate in CANDIDATES}
    missing = [label for label in labels if label not in lookup]
    if missing:
        raise KeyError(f"unknown candidates: {missing}")
    return [lookup[label] for label in labels]


def budget_prefix(prefix: Path, budget: int) -> Path:
    return prefix.with_name(f"{prefix.name}_wc{int(budget)}")


def targeted_prefix(candidate: Candidate) -> Path:
    return ROOT / "runs/analysis" / f"{TARGET_PREFIX}_{candidate.label}_canonical_low_warmup"


def targeted_doc_prefix(candidate: Candidate) -> Path:
    return ROOT / "docs" / f"{TARGET_PREFIX}_{candidate.label}_canonical_low_warmup"


def per_instance_path(prefix: Path, budget: int) -> Path:
    out = budget_prefix(prefix, budget)
    return out.with_name(f"{out.name}_per_instance.csv")


def reusable_per_instance_path(candidate: Candidate, budget: int) -> Path:
    return per_instance_path(ROOT / "runs/analysis" / candidate.reuse_prefix, budget)


def targeted_per_instance_path(candidate: Candidate, budget: int) -> Path:
    return per_instance_path(targeted_prefix(candidate), budget)


def existing_per_instance_path(candidate: Candidate, budget: int) -> tuple[Path | None, str]:
    reusable = reusable_per_instance_path(candidate, budget)
    if reusable.exists():
        return reusable, "reused_timeslice"
    targeted = targeted_per_instance_path(candidate, budget)
    if targeted.exists():
        return targeted, "targeted_acceptance"
    return None, "missing"
