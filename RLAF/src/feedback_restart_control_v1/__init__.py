"""Separately versioned evaluator for the 2026-11-18 feedback/restart draft.

Historical ``balanced_feedback_check_20261104`` scripts are not in this
repository and are not imported. Passing these mocked tests does not show that
an admin Glucose, DRAT, or GPU path behaves.

Spec adaptations relative to STATE_MACHINE.md / TEST_PLAN.md:

- Checker failure, a missing or corrupt proof, and the 1800s checker budget
  are status ``invalid`` with no PAR2. Status ``incomplete`` is only a
  resource-guard or operator stop.
- A solved candidate is timely at exit == D. A clean UNKNOWN can continue
  only when its exit is strictly before D, because a readout or final launch
  is new work and is refused at D.
- A probe solution is accepted only inside the grace window clipped to D.
  Equality at D does not waive an earlier soft-stop miss.
- Launched probe/final receipts must carry stdout and stderr hashes before a
  timeout or solved status is auditable. A global-deadline kill without those
  hashes is an invalid receipt, not a scientific timeout.
- SAT witnesses use the local assignment checker in this package
  (``local-assignment-v1``). UNSAT proofs use the injected checker port.
  Neither path shells out. Archive round-trip failure is ``invalid``.
- Probe-state encoding rejects missing, NaN, or negative counters. It does
  not call the published zero-filling ``solver_stats_to_global_state``.
- Frozen z-bar is passed through as the already-log1p vector. Probe counters
  are log1p-encoded once. The six components follow the published layout:
  decisions, conflicts, propagations, restarts, CPU time, result code 0.
- ``technical_failure`` is a required boolean. Audit does not default a
  missing field to false. ``probe_succeeded`` is not a status.
- The schedule validator checks the draft matrix (192 x 4, 12 x 4, smoke
  4 x 4). It does not draw the repeat subset; generation is not authorized.
- Campaign audit never emits a mean PAR2. ``protocol_authorized`` stays false.
"""

from .audit import audit_cell, campaign_report, preflight_dependencies, validate_schedule
from .contract import (
    EVALUATOR_VERSION,
    FIXED_STATE_SHA256,
    FROZEN_ZBAR,
    MATCHED_CHECKPOINT_SHA256,
    NAMESPACE,
    PAPER_CHECKPOINT_SHA256,
    PROTOCOL_STATUS,
    SCHEMA,
    STUDY_ID,
    ConfigError,
    ContractError,
    ManualClock,
    ResourceLedger,
    StudyConfig,
    candidate_timely,
    new_work_allowed,
)
from .guidance import CellRequest, Cnf, encode_probe_z, model_satisfies, stats_complete
from .legacy import assess_legacy_balanced_cell
from .run import run_cell

__all__ = [
    "EVALUATOR_VERSION",
    "FIXED_STATE_SHA256",
    "FROZEN_ZBAR",
    "MATCHED_CHECKPOINT_SHA256",
    "NAMESPACE",
    "PAPER_CHECKPOINT_SHA256",
    "PROTOCOL_STATUS",
    "SCHEMA",
    "STUDY_ID",
    "CellRequest",
    "Cnf",
    "ConfigError",
    "ContractError",
    "ManualClock",
    "ResourceLedger",
    "StudyConfig",
    "assess_legacy_balanced_cell",
    "audit_cell",
    "campaign_report",
    "candidate_timely",
    "encode_probe_z",
    "model_satisfies",
    "new_work_allowed",
    "preflight_dependencies",
    "run_cell",
    "stats_complete",
    "validate_schedule",
]
