"""Draft contract for EchoSAT-Feedback-Restart-Control-20261118-v1.

This package is a new evaluator. It does not replace, import, or rewrite the
historical balanced-feedback runner. The study protocol is a draft: receipts
keep ``protocol_authorized`` false, and nothing here starts a solver.
"""

from __future__ import annotations

from dataclasses import dataclass

SCHEMA = "echosat-feedback-restart-control-v1.cell/1"
EVALUATOR_VERSION = "1.0.0"
STUDY_ID = "feedback_restart_control_20261118"
NAMESPACE = "EchoSAT-Feedback-Restart-Control-20261118-v1"
PROTOCOL_STATUS = "draft_not_authorized"

ANSWER_DEADLINE_SECONDS = 60.0
PAR2_TIMEOUT_SECONDS = 120.0
CHECKER_TIMEOUT_SECONDS = 1800.0
PROBE_SOFT_TARGET_SECONDS = 1.0
PROBE_GRACE_SECONDS = 0.25

WALL_GUARD_SECONDS = 24 * 3600
CPU_GUARD_SECONDS = 30 * 3600
DISK_START_BYTES = 35 * 1024**3
DISK_STOP_BYTES = 15 * 1024**3

PAPER_CHECKPOINT_SHA256 = "cdbd1b3ce595ed30a32fa38c55bc1c535a8499227ba4c00063742d62c0debecf"
MATCHED_CHECKPOINT_SHA256 = "554726ecb4d7ab74647e031f9b33ef181d43cb952c17027b2a1e2f11d808d82a"
FIXED_STATE_SHA256 = "0e81d9ae412173b08070b30e580572bb2c484a2acfe21aedb55831e6e77e3cf9"

# Already in model log1p space. Do not transform these again.
FROZEN_ZBAR = {
    300: (
        11.01235294342041,
        10.893117904663086,
        14.708498001098633,
        0.6931471824645996,
        0.48569291830062866,
        0.0,
    ),
    350: (
        10.95370864868164,
        10.825160026550293,
        14.745651245117188,
        0.6931471824645996,
        0.4864697754383087,
        0.0,
    ),
}
ZERO_STATE = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

ARMS = ("fixed_direct", "rlaf_matched", "feedback_once", "probe_restart_fixed")
PROBE_ARMS = ("feedback_once", "probe_restart_fixed")
BASELINE_ARMS = ("fixed_direct", "rlaf_matched")
PAPER_ARMS = ("fixed_direct", "feedback_once", "probe_restart_fixed")
SOLVER_FLAGS = {"rnd_freq": 0, "seed": 1, "K": 0.1, "model": True, "certified": True}
PROBE_POLICY_ID = "shared-probe-v1"
SCHEDULE_SEED = 20261118

MAIN_SOURCES = 192
MAIN_N350 = 128
MAIN_N300 = 64
REPEAT_SOURCES = 12
REPEAT_N350 = 8
REPEAT_N300 = 4
SMOKE_SOURCES = 4
SMOKE_PER_N = 2

SAT_RETURNCODE = 10
UNSAT_RETURNCODE = 20
UNKNOWN_RETURNCODE = 0

COUNTER_KEYS = ("decisions", "conflicts", "propagations", "restarts", "CPU time")

REQUIRED_DEPENDENCY_ROLES = (
    "evaluator",
    "shared_runtime_helper",
    "sat_witness_checker",
    "unsat_checker",
    "probe_solver",
    "final_solver",
    "checkpoint_paper",
    "checkpoint_matched",
    "fixed_state",
    "serializer",
)

REQUIRED_RECEIPT_FIELDS = (
    "schema",
    "evaluator_version",
    "study_id",
    "protocol_status",
    "protocol_authorized",
    "arm",
    "source_id",
    "n",
    "repeat",
    "split",
    "t0",
    "deadline",
    "status",
    "terminal_reason",
    "terminal_answer_stage",
    "answer",
    "answer_timestamp",
    "candidate_exit_timestamp",
    "par2",
    "verified",
    "technical_failure",
    "validation_failure",
    "timeout_kind",
    "probe_outcome",
    "final_started",
    "final_launches",
    "probe_launches",
    "encoder_calls",
    "initial_decode_calls",
    "feedback_decode_calls",
    "checker_launches",
    "initial_action",
    "final_action",
    "initial_action_sha256",
    "final_action_sha256",
    "initial_z_source",
    "feedback_z_source",
    "probe_z",
    "unused_probe_z",
    "input_written",
    "plain_fallback",
    "checkpoint_sha256",
    "fixed_state_sha256",
    "source_sha256",
    "transitions",
    "stage_bounds",
    "probe",
    "final",
    "validation",
    "archive",
    "resource",
    "overrun_recorded",
    "automatic_retry",
    "performance_aggregated",
    "stats_trusted",
)

LEGAL_TRANSITIONS = {
    "start": {"prepared", "terminal"},
    "prepared": {"initial_guidance", "terminal"},
    "initial_guidance": {"probe_done", "final_done", "terminal"},
    "probe_done": {"feedback_guidance", "certified", "terminal"},
    "feedback_guidance": {"final_done", "terminal"},
    "final_done": {"certified", "terminal"},
    "certified": {"terminal"},
}


class ConfigError(Exception):
    def __init__(self, reasons: list[str]):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


class ContractError(Exception):
    """Runner or fixture bug. Scientific outcomes are receipt statuses, not this error."""


def new_work_allowed(now: float, deadline: float) -> bool:
    """A new encoder, readout, probe, or solver may start only before D."""
    return now < deadline


def candidate_timely(exit_time: float, deadline: float) -> bool:
    """An already-running process may exit at D. Later exits are not timely."""
    return exit_time <= deadline


def clipped_grace_end(start: float, deadline: float, config: "StudyConfig") -> float:
    return min(deadline, start + config.probe_soft_target_seconds + config.probe_grace_seconds)


@dataclass(frozen=True)
class StudyConfig:
    answer_deadline_seconds: float = ANSWER_DEADLINE_SECONDS
    par2_timeout_seconds: float = PAR2_TIMEOUT_SECONDS
    checker_timeout_seconds: float = CHECKER_TIMEOUT_SECONDS
    probe_soft_target_seconds: float = PROBE_SOFT_TARGET_SECONDS
    probe_grace_seconds: float = PROBE_GRACE_SECONDS
    feedback_rounds: int = 1
    fallback: str | None = None
    proof_logging: bool = True
    fixed_state_sha256: str = FIXED_STATE_SHA256
    solver_seed: int = 1
    schedule_seed: int = SCHEDULE_SEED

    @staticmethod
    def create(**overrides: object) -> "StudyConfig":
        config = StudyConfig(**overrides)  # type: ignore[arg-type]
        validate_config(config)
        return config

    @property
    def frozen_zbar(self) -> dict[int, tuple[float, ...]]:
        return FROZEN_ZBAR


def validate_config(config: StudyConfig) -> None:
    reasons: list[str] = []
    if config.fallback is not None:
        reasons.append("fallback_not_in_protocol")
    if config.feedback_rounds != 1:
        reasons.append("feedback_rounds_must_be_one")
    if config.proof_logging is not True:
        reasons.append("proof_logging_required")
    if config.answer_deadline_seconds != ANSWER_DEADLINE_SECONDS:
        reasons.append("answer_deadline_must_be_60s")
    if config.par2_timeout_seconds != PAR2_TIMEOUT_SECONDS:
        reasons.append("par2_must_be_120")
    if config.checker_timeout_seconds != CHECKER_TIMEOUT_SECONDS:
        reasons.append("checker_timeout_must_be_1800s")
    if config.probe_soft_target_seconds != PROBE_SOFT_TARGET_SECONDS:
        reasons.append("probe_soft_target_must_be_1s")
    if not 0 < config.probe_grace_seconds <= PROBE_GRACE_SECONDS:
        reasons.append("probe_grace_must_be_positive_and_at_most_0.25s")
    if config.fixed_state_sha256 != FIXED_STATE_SHA256:
        reasons.append("fixed_state_pin_mismatch")
    if config.schedule_seed != SCHEDULE_SEED:
        reasons.append("schedule_seed_mismatch")
    if reasons:
        raise ConfigError(reasons)


def expected_checkpoint(arm: str) -> str:
    if arm == "rlaf_matched":
        return MATCHED_CHECKPOINT_SHA256
    if arm in PAPER_ARMS:
        return PAPER_CHECKPOINT_SHA256
    raise ConfigError([f"unknown_arm:{arm}"])


class ManualClock:
    """Deterministic clock. Tests advance it only through recorded receipts."""

    def __init__(self, start: float = 0.0) -> None:
        self.t = float(start)

    def now(self) -> float:
        return self.t

    def advance_to(self, instant: float) -> None:
        instant = float(instant)
        if instant < self.t:
            raise ContractError(f"time reversal {instant} < {self.t}")
        self.t = instant


@dataclass
class ResourceLedger:
    wall_seconds: float = 0.0
    cpu_seconds: float = 0.0
    disk_free_bytes: int = 40 * 1024**3
    cells_admitted: int = 0
    automatic_retry: bool = False

    def admission_block(self) -> str | None:
        if self.automatic_retry:
            return "automatic_retry_forbidden"
        if self.wall_seconds >= WALL_GUARD_SECONDS:
            return "wall_guard"
        if self.cpu_seconds >= CPU_GUARD_SECONDS:
            return "cpu_guard"
        if self.disk_free_bytes < DISK_STOP_BYTES:
            return "disk_stop"
        if self.cells_admitted == 0 and self.disk_free_bytes < DISK_START_BYTES:
            return "disk_start"
        return None

    def admit(self) -> None:
        self.cells_admitted += 1

    def charge(self, wall_seconds: float, cpu_seconds: float) -> None:
        self.wall_seconds += float(wall_seconds)
        self.cpu_seconds += float(cpu_seconds)
