"""Shared search classification for the runner and the audit.

Outcomes are derived from the raw receipt. A caller-supplied timeout label is
not an input to this function.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contract import (
    SAT_RETURNCODE,
    UNKNOWN_RETURNCODE,
    UNSAT_RETURNCODE,
    StudyConfig,
    clipped_grace_end,
)
from .guidance import sha_ok, stats_complete


@dataclass(frozen=True)
class Decision:
    outcome: str
    reason: str
    stats_trusted: bool


def _proof_before_exit(result: dict, ended: float) -> bool:
    stamp = result.get("proof_completed_at")
    if stamp is None:
        return True
    if isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
        return False
    return float(stamp) <= ended


def _exit_time(result: dict) -> float | None:
    value = result.get("ended_at")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def contract_violation(request: dict, result: dict) -> str | None:
    stop = result.get("stop_reason")
    if not result.get("launched"):
        return None
    if stop in {"resource_guard", "operator", "launch_error", "global_deadline", "hard_kill"}:
        return None
    if result.get("hard_killed"):
        return None
    if result.get("formula_sha256") != request.get("formula_sha256"):
        return "formula_mismatch"
    if result.get("guidance_sha256") != request.get("guidance_sha256"):
        return "action_hash_mismatch"
    if result.get("learned_clauses_carried") is not False:
        return "learned_clauses_carried"
    if result.get("session_id") != request.get("session_id"):
        return "session_mismatch"
    if result.get("resume") is True:
        return "resume_forbidden"
    return None


def _request_violation(request: dict, deadline: float, role: str) -> str | None:
    if request.get("deadline") != deadline:
        return "deadline_reset"
    if request.get("formula_role") != "original":
        return "formula_role"
    if request.get("proof_logging") is not True:
        return "proof_logging_disabled"
    if request.get("resume") is not False or request.get("learned_clauses_carried") is not False:
        return "illegal_restart_request"
    if role == "final" and request.get("grace_end") is not None:
        return "final_soft_stop_forbidden"
    if role == "probe" and request.get("feedback_rounds") != 1:
        return "second_feedback_forbidden"
    return None


def _unbound(result: dict) -> bool:
    return not sha_ok(result.get("stdout_sha256")) or not sha_ok(result.get("stderr_sha256"))


def decide_probe(result: dict, *, deadline: float, grace_end: float) -> Decision:
    stop = result.get("stop_reason")
    if stop in {"resource_guard", "operator"}:
        return Decision("incomplete", str(stop), False)
    if not result.get("launched") or stop == "launch_error":
        return Decision("technical", "launch_error", False)
    if _unbound(result):
        return Decision("technical", "unbound_streams", False)
    ended = _exit_time(result)
    if ended is None:
        return Decision("technical", "missing_exit_timestamp", False)
    hard = bool(result.get("hard_killed")) or stop in {"hard_kill", "global_deadline"}
    if hard:
        if stop == "global_deadline" or ended >= deadline:
            return Decision("deadline", "global_deadline", False)
        return Decision("technical", "hard_kill_before_deadline", False)
    if stop == "grace_exceeded" and ended < deadline:
        return Decision("technical", "grace_stop_failed", False)
    if ended > grace_end and ended < deadline:
        return Decision("technical", "exceeded_grace_before_deadline", False)
    if result.get("proof_logging") is not True:
        return Decision("technical", "proof_logging_disabled", False)
    reported = result.get("reported_result")
    code = result.get("returncode")
    clean = result.get("clean_exit") is True
    if reported == "SATISFIABLE" and code == SAT_RETURNCODE and clean:
        if ended <= deadline and ended <= grace_end:
            if not _proof_before_exit(result, ended):
                return Decision("technical", "proof_after_answer_endpoint", False)
            return Decision("sat", "timely_sat", False)
        if ended > deadline:
            return Decision("late", "late_sat", False)
        return Decision("technical", "sat_outside_grace", False)
    if reported == "UNSATISFIABLE" and code == UNSAT_RETURNCODE and clean:
        if ended <= deadline and ended <= grace_end:
            if not _proof_before_exit(result, ended):
                return Decision("technical", "proof_after_answer_endpoint", False)
            return Decision("unsat", "timely_unsat", False)
        if ended > deadline:
            return Decision("late", "late_unsat", False)
        return Decision("technical", "unsat_outside_grace", False)
    if reported in {"UNKNOWN", "INDETERMINATE"} and code == UNKNOWN_RETURNCODE and clean:
        if ended >= deadline:
            return Decision("unknown_exhausted", "unknown_at_or_after_deadline", False)
        if not stats_complete(result.get("stats")):
            return Decision("technical", "incomplete_probe_stats", False)
        return Decision("unknown", "clean_unknown", True)
    return Decision("technical", "malformed_probe_result", False)


def decide_final(result: dict, *, deadline: float) -> Decision:
    stop = result.get("stop_reason")
    if stop in {"resource_guard", "operator"}:
        return Decision("incomplete", str(stop), False)
    if not result.get("launched") or stop == "launch_error":
        return Decision("technical", "launch_error", False)
    if _unbound(result):
        return Decision("technical", "unbound_streams", False)
    ended = _exit_time(result)
    if ended is None:
        return Decision("technical", "missing_exit_timestamp", False)
    hard = bool(result.get("hard_killed")) or stop in {"hard_kill", "global_deadline"}
    if hard:
        if stop == "global_deadline" or ended >= deadline:
            return Decision("deadline", "global_deadline", False)
        return Decision("technical", "hard_kill_before_deadline", False)
    if result.get("proof_logging") is not True:
        return Decision("technical", "proof_logging_disabled", False)
    reported = result.get("reported_result")
    code = result.get("returncode")
    clean = result.get("clean_exit") is True
    if reported == "SATISFIABLE" and code == SAT_RETURNCODE and clean:
        if ended <= deadline:
            if not _proof_before_exit(result, ended):
                return Decision("technical", "proof_after_answer_endpoint", False)
            return Decision("sat", "timely_sat", False)
        return Decision("late", "late_sat", False)
    if reported == "UNSATISFIABLE" and code == UNSAT_RETURNCODE and clean:
        if ended <= deadline:
            if not _proof_before_exit(result, ended):
                return Decision("technical", "proof_after_answer_endpoint", False)
            return Decision("unsat", "timely_unsat", False)
        return Decision("late", "late_unsat", False)
    if reported in {"UNKNOWN", "INDETERMINATE"} and code == UNKNOWN_RETURNCODE and clean:
        if ended >= deadline:
            return Decision("deadline", "final_unknown_at_deadline", False)
        return Decision("technical", "unexpected_unknown_before_deadline", False)
    return Decision("technical", "malformed_final_result", False)


def resolve_search(request: dict, result: dict, *, deadline: float, config: StudyConfig, role: str) -> Decision:
    request_problem = _request_violation(request, deadline, role)
    if request_problem:
        return Decision("technical", request_problem, False)
    if role == "probe":
        grace_end = clipped_grace_end(float(request["now"]), deadline, config)
        if request.get("grace_end") != grace_end:
            return Decision("technical", "tampered_grace_window", False)
    else:
        grace_end = None
    violation = contract_violation(request, result)
    if violation:
        return Decision("technical", violation, False)
    if role == "probe":
        assert grace_end is not None
        return decide_probe(result, deadline=deadline, grace_end=grace_end)
    return decide_final(result, deadline=deadline)
