"""Reject the 2026-11-04 probe-SAT pattern. This does not rewrite those receipts."""

from __future__ import annotations


def _solved_line(probe_stdout: str) -> str | None:
    for line in probe_stdout.splitlines():
        if line == "s SATISFIABLE" or line.startswith("s SATISFIABLE"):
            return "SATISFIABLE"
        if line == "s UNSATISFIABLE" or line.startswith("s UNSATISFIABLE"):
            return "UNSATISFIABLE"
    return None


def assess_legacy_balanced_cell(action: dict, result: dict, observation: dict, probe_stdout: str) -> dict:
    """Return rejection reasons for one historical Balanced cell.

    An empty reason list is not a certification. The historical audit accepted
    byte-identical inputs and a valid final model without a legal probe transition.
    """
    reasons: list[str] = []
    if "probe_technical_failure" not in action and "probe_technical_failure" not in observation:
        reasons.append("absent_technical_failure_field")
    probe_answer = _solved_line(probe_stdout)
    process = result.get("process") or {}
    launched = bool(process.get("launched"))
    if probe_answer is not None and launched:
        reasons.append("solved_probe_followed_by_final_launch")
    if action.get("action") is None and launched:
        reasons.append("null_action_with_final_launch")
    if action.get("probe_succeeded") is False and probe_answer is not None and result.get("status") == "solved":
        reasons.append("probe_succeeded_false_on_solved_stdout")
    if (
        action.get("action") is None
        and launched
        and result.get("input_sha256") is not None
        and result.get("input_sha256") == result.get("source_sha256")
    ):
        reasons.append("plain_input_hash_matches_source")
    if result.get("verified") is True and probe_answer is not None and launched:
        reasons.append("valid_final_answer_does_not_excuse_transition")
    return {
        "ok": False,
        "rejected": bool(reasons),
        "reasons": reasons,
        "historical_audit_was_not_transition_aware": True,
    }
