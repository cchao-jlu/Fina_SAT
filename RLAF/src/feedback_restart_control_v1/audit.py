"""Read-only checks. Performance is not aggregated: the protocol is still a draft."""

from __future__ import annotations

from .classify import resolve_search
from .contract import (
    ARMS,
    CPU_GUARD_SECONDS,
    DISK_START_BYTES,
    DISK_STOP_BYTES,
    LEGAL_TRANSITIONS,
    MAIN_N300,
    MAIN_N350,
    MAIN_SOURCES,
    REPEAT_N300,
    REPEAT_N350,
    REPEAT_SOURCES,
    REQUIRED_DEPENDENCY_ROLES,
    REQUIRED_RECEIPT_FIELDS,
    SCHEDULE_SEED,
    SCHEMA,
    SMOKE_PER_N,
    SMOKE_SOURCES,
    WALL_GUARD_SECONDS,
    StudyConfig,
    validate_config,
)
from .guidance import action_sha256, sha256_bytes, sha_ok

_TIMEOUT_KINDS = {
    None,
    "deadline_before_work",
    "deadline_before_decode",
    "deadline_before_probe",
    "deadline_before_final",
    "nonpreemptible_overrun",
    "global_deadline",
    "unknown_exhausted",
    "late_candidate",
}


def _fail(reasons: list[str], code: str) -> None:
    if code not in reasons:
        reasons.append(code)


def audit_cell(receipt: dict, cnf=None, config: StudyConfig | None = None) -> dict:
    config = config or StudyConfig.create()
    validate_config(config)
    reasons: list[str] = []
    for field in REQUIRED_RECEIPT_FIELDS:
        if field not in receipt:
            _fail(reasons, f"missing_field:{field}")
    if reasons:
        return {"ok": False, "reasons": reasons}
    if receipt["schema"] != SCHEMA:
        _fail(reasons, "bad_schema")
    if receipt["protocol_authorized"] is not False:
        _fail(reasons, "protocol_authorized")
    if receipt["plain_fallback"] is not False:
        _fail(reasons, "plain_fallback")
    if receipt["automatic_retry"] is not False or receipt["performance_aggregated"] is not False:
        _fail(reasons, "aggregation_or_retry_bit")
    if not isinstance(receipt["technical_failure"], bool):
        _fail(reasons, "technical_failure_not_bool")
    if receipt["deadline"] != receipt["t0"] + config.answer_deadline_seconds:
        _fail(reasons, "deadline_not_t0_plus_60")
    _check_transitions(receipt, reasons)
    _check_stages(receipt, reasons)
    _check_counters(receipt, reasons)
    _check_status(receipt, config, reasons)
    if receipt["probe"] is not None:
        _check_probe(receipt, config, reasons)
    elif receipt["probe_launches"] != 0 or receipt["probe_outcome"] != "none":
        _fail(reasons, "probe_counter_mismatch")
    if receipt["final"] is not None:
        _check_final(receipt, config, reasons)
    elif receipt["final_launches"] != 0 or receipt["final_started"] is not False:
        _fail(reasons, "final_counter_mismatch")
    if receipt["final_launches"] and receipt["final_action"] is None:
        _fail(reasons, "null_guidance_final_launch")
    if receipt["terminal_reason"] == "null_or_invalid_guidance" and receipt["final_launches"] != 0:
        _fail(reasons, "null_guidance_final_launch")
    if (
        receipt["terminal_reason"] == "null_or_invalid_guidance"
        and receipt["probe_launches"] == 0
        and receipt["input_written"] is not False
    ):
        _fail(reasons, "null_guidance_wrote_input")
    if cnf is not None:
        _check_action_binding(receipt, cnf, reasons)
    if receipt["probe_outcome"] in {"sat", "unsat"} and receipt["status"] == "solved":
        if receipt["final_launches"] != 0 or receipt["feedback_decode_calls"] != 0:
            _fail(reasons, "solved_probe_continued")
        if receipt["terminal_answer_stage"] != "probe":
            _fail(reasons, "solved_probe_stage")
        if receipt["probe_outcome"] == "unsat" and receipt["checker_launches"] != 1:
            _fail(reasons, "unsat_checker_count")
        if receipt["probe_outcome"] == "sat" and receipt["checker_launches"] != 0:
            _fail(reasons, "sat_checker_count")
    if receipt["probe_outcome"] == "unknown" and receipt["status"] == "solved":
        if receipt["final_launches"] != 1 or receipt["feedback_decode_calls"] != 1:
            _fail(reasons, "unknown_path_search_count")
        if receipt["terminal_answer_stage"] != "final":
            _fail(reasons, "unknown_path_stage")
    return {"ok": not reasons, "reasons": reasons}


def _check_transitions(receipt: dict, reasons: list[str]) -> None:
    states = receipt["transitions"]
    if not isinstance(states, list) or not states or states[0] != "start" or states[-1] != "terminal":
        _fail(reasons, "illegal_transition")
        return
    previous = states[0]
    for state in states[1:]:
        if state not in LEGAL_TRANSITIONS.get(previous, ()):
            _fail(reasons, "illegal_transition")
            return
        previous = state
    certified = "certified" in states
    if (receipt["status"] == "solved") != certified:
        _fail(reasons, "illegal_transition")


def _check_stages(receipt: dict, reasons: list[str]) -> None:
    previous_end = None
    for stage in receipt["stage_bounds"]:
        if stage["end"] < stage["start"] or (previous_end is not None and stage["start"] < previous_end):
            _fail(reasons, "stage_not_monotonic")
            return
        previous_end = stage["end"]


def _check_counters(receipt: dict, reasons: list[str]) -> None:
    if receipt["encoder_calls"] != (1 if "prepared" in receipt["transitions"] else 0):
        _fail(reasons, "counter_mismatch")
    if receipt["initial_decode_calls"] != (1 if "initial_guidance" in receipt["transitions"] else 0):
        _fail(reasons, "counter_mismatch")
    if receipt["feedback_decode_calls"] != (1 if "feedback_guidance" in receipt["transitions"] else 0):
        _fail(reasons, "counter_mismatch")
    if receipt["probe_launches"] > 1 or receipt["final_launches"] > 1 or receipt["feedback_decode_calls"] > 1:
        _fail(reasons, "second_feedback_or_search")


def _check_status(receipt: dict, config: StudyConfig, reasons: list[str]) -> None:
    status = receipt["status"]
    if status == "solved":
        answer_at = receipt["answer_timestamp"]
        if not (
            receipt["verified"]
            and receipt["answer"] in {"SATISFIABLE", "UNSATISFIABLE"}
            and answer_at is not None
            and answer_at <= receipt["deadline"]
            and receipt["par2"] == answer_at - receipt["t0"]
            and receipt["technical_failure"] is False
            and receipt["validation_failure"] is False
            and receipt["validation"]["accepted"] is True
            and receipt["timeout_kind"] is None
        ):
            _fail(reasons, "solved_contract")
        wall = receipt["resource"]["answer_wall_seconds"]
        if wall != receipt["par2"]:
            _fail(reasons, "par2_includes_postprocessing")
        inclusive = receipt["resource"]["certification_inclusive_wall_seconds"]
        if inclusive is None or inclusive < wall:
            _fail(reasons, "certification_ledger")
    elif status == "timeout":
        if receipt["par2"] != config.par2_timeout_seconds or receipt["verified"] or receipt["answer"] is not None:
            _fail(reasons, "timeout_contract")
        if receipt["technical_failure"] or receipt["validation_failure"] or receipt["timeout_kind"] is None:
            _fail(reasons, "timeout_contract")
    elif status == "invalid":
        if receipt["par2"] is not None or receipt["verified"] or receipt["answer"] is not None:
            _fail(reasons, "invalid_has_par2")
    elif status == "incomplete":
        if receipt["par2"] is not None or receipt["automatic_retry"] or receipt["verified"]:
            _fail(reasons, "incomplete_contract")
    else:
        _fail(reasons, "bad_status")


def _check_probe(receipt: dict, config: StudyConfig, reasons: list[str]) -> None:
    probe = receipt["probe"]
    request = probe["request"]
    result = probe["result"]
    decision = resolve_search(request, result, deadline=receipt["deadline"], config=config, role="probe")
    if probe["outcome"] != decision.outcome or receipt["probe_outcome"] != decision.outcome:
        _fail(reasons, "probe_outcome_disagrees_with_raw")
    launched = bool(result.get("launched"))
    bound = sha_ok(result.get("stdout_sha256")) and sha_ok(result.get("stderr_sha256"))
    if launched and receipt["status"] != "incomplete" and not bound:
        _fail(reasons, "unbound_probe_streams")
    if decision.outcome in {"sat", "unsat"} and receipt["status"] == "timeout":
        _fail(reasons, "forged_timeout_kind")
    if decision.outcome in {"sat", "unsat"} and receipt["final_launches"] != 0:
        _fail(reasons, "illegal_probe_to_final")
    if decision.outcome == "unknown" and receipt["final"] is not None:
        _check_fresh_restart(receipt, reasons)
    if receipt["timeout_kind"] not in _TIMEOUT_KINDS or receipt["timeout_kind"] == "probe_failure":
        _fail(reasons, "forged_timeout_kind")


def _check_final(receipt: dict, config: StudyConfig, reasons: list[str]) -> None:
    final = receipt["final"]
    decision = resolve_search(
        final["request"], final["result"], deadline=receipt["deadline"], config=config, role="final"
    )
    if final["outcome"] != decision.outcome:
        _fail(reasons, "final_outcome_disagrees_with_raw")
    if decision.outcome in {"sat", "unsat"} and receipt["status"] == "timeout":
        _fail(reasons, "forged_timeout_kind")
    request = final["request"]
    if request.get("formula_role") != "original" or request.get("formula_sha256") != receipt["source_sha256"]:
        _fail(reasons, "final_formula_not_original")
    if request.get("learned_clauses_carried") is not False or request.get("resume") is not False:
        _fail(reasons, "learned_clauses_in_final")
    if request.get("deadline") != receipt["deadline"]:
        _fail(reasons, "final_deadline_reset")
    probe = receipt["probe"]
    if probe is not None and request.get("session_id") == probe["request"].get("session_id"):
        _fail(reasons, "session_not_fresh")


def _check_fresh_restart(receipt: dict, reasons: list[str]) -> None:
    request = receipt["final"]["request"]
    if request.get("formula_sha256") != receipt["source_sha256"] or request.get("formula_role") != "original":
        _fail(reasons, "final_formula_not_original")
    if request.get("learned_clauses_carried") is not False or request.get("resume") is not False:
        _fail(reasons, "learned_clauses_in_final")
    if request.get("deadline") != receipt["deadline"]:
        _fail(reasons, "final_deadline_reset")
    if request.get("session_id") == receipt["probe"]["request"].get("session_id"):
        _fail(reasons, "session_not_fresh")
    if receipt["final_launches"] != 1:
        _fail(reasons, "unknown_path_search_count")


def _check_action_binding(receipt: dict, cnf, reasons: list[str]) -> None:
    if receipt["initial_action"] is not None:
        if action_sha256(cnf, receipt["initial_action"]) != receipt["initial_action_sha256"]:
            _fail(reasons, "stale_action_hash")
    if receipt["final_action"] is not None:
        if action_sha256(cnf, receipt["final_action"]) != receipt["final_action_sha256"]:
            _fail(reasons, "stale_action_hash")
    probe = receipt["probe"]
    if probe is not None and receipt["initial_action_sha256"] is not None:
        if probe["request"].get("guidance_sha256") != receipt["initial_action_sha256"]:
            _fail(reasons, "stale_action_hash")
    final = receipt["final"]
    if final is not None and receipt["final_action_sha256"] is not None:
        if final["request"].get("guidance_sha256") != receipt["final_action_sha256"]:
            _fail(reasons, "stale_action_hash")


def preflight_dependencies(expected_sha256: dict[str, str], blobs: dict[str, bytes]) -> dict:
    reasons: list[str] = []
    for role in REQUIRED_DEPENDENCY_ROLES:
        if role not in expected_sha256:
            _fail(reasons, f"missing_binding:{role}")
            continue
        if role not in blobs:
            _fail(reasons, f"missing_bytes:{role}")
            continue
        if sha256_bytes(blobs[role]) != expected_sha256[role]:
            _fail(reasons, f"hash_mismatch:{role}")
    return {"ok": not reasons, "reasons": reasons, "roles": list(REQUIRED_DEPENDENCY_ROLES)}


def validate_schedule(entries: list[dict]) -> dict:
    reasons: list[str] = []
    seen: set[tuple] = set()
    formal_main: dict[str, set[str]] = {}
    formal_n: dict[str, int] = {}
    repeat_rows: dict[str, set[str]] = {}
    repeat_n: dict[str, int] = {}
    smoke: dict[str, set[str]] = {}
    smoke_n: dict[str, int] = {}
    for entry in entries:
        if any(key in entry for key in ("par2", "answer", "status", "difficulty", "label")):
            _fail(reasons, "schedule_contains_outcomes")
        if entry.get("selection_seed") != SCHEDULE_SEED:
            _fail(reasons, "selection_seed")
        if entry.get("arm") not in ARMS:
            _fail(reasons, "bad_arm")
        key = (entry.get("split"), entry.get("source_id"), entry.get("arm"), entry.get("repeat"))
        if key in seen:
            _fail(reasons, "duplicate_cell")
        seen.add(key)
        split = entry.get("split")
        source = entry.get("source_id")
        arm = entry.get("arm")
        repeat = entry.get("repeat")
        size = entry.get("n")
        if split == "formal" and repeat == 0:
            formal_main.setdefault(source, set()).add(arm)
            formal_n[source] = size
        elif split == "formal" and repeat == 1:
            repeat_rows.setdefault(source, set()).add(arm)
            repeat_n[source] = size
        elif split == "smoke" and repeat == 0:
            smoke.setdefault(source, set()).add(arm)
            smoke_n[source] = size
        else:
            _fail(reasons, "unexpected_row")
    if len(formal_main) != MAIN_SOURCES:
        _fail(reasons, "main_source_count")
    if sum(1 for value in formal_n.values() if value == 350) != MAIN_N350:
        _fail(reasons, "main_n350_count")
    if sum(1 for value in formal_n.values() if value == 300) != MAIN_N300:
        _fail(reasons, "main_n300_count")
    if any(arms != set(ARMS) for arms in formal_main.values()):
        _fail(reasons, "main_arm_coverage")
    if len(repeat_rows) != REPEAT_SOURCES:
        _fail(reasons, "repeat_source_count")
    if any(
        source not in formal_main or arms != set(ARMS) or repeat_n[source] != formal_n[source]
        for source, arms in repeat_rows.items()
    ):
        _fail(reasons, "repeat_not_subset")
    if sum(1 for value in repeat_n.values() if value == 350) != REPEAT_N350:
        _fail(reasons, "repeat_n350_count")
    if sum(1 for value in repeat_n.values() if value == 300) != REPEAT_N300:
        _fail(reasons, "repeat_n300_count")
    if len(smoke) != SMOKE_SOURCES:
        _fail(reasons, "smoke_source_count")
    if any(source in formal_main or arms != set(ARMS) for source, arms in smoke.items()):
        _fail(reasons, "smoke_collision")
    if any(value not in (300, 350) for value in smoke_n.values()):
        _fail(reasons, "smoke_n_count")
    if sum(1 for value in smoke_n.values() if value == 350) != SMOKE_PER_N:
        _fail(reasons, "smoke_n_count")
    if sum(1 for value in smoke_n.values() if value == 300) != SMOKE_PER_N:
        _fail(reasons, "smoke_n_count")
    formal_cells = len(formal_main) * len(ARMS) + len(repeat_rows) * len(ARMS)
    smoke_cells = len(smoke) * len(ARMS)
    return {
        "ok": not reasons,
        "reasons": reasons,
        "formal_main_cells": len(formal_main) * len(ARMS),
        "formal_repeat_cells": len(repeat_rows) * len(ARMS),
        "formal_cells": formal_cells,
        "smoke_cells": smoke_cells,
        "total_cells": formal_cells + smoke_cells,
    }


_MISSING = object()


def campaign_report(receipts: list[dict], config: StudyConfig | None = None) -> dict:
    """Audit receipts. A passing mock campaign still has no mean PAR2."""
    config = config or StudyConfig.create()
    reasons: list[str] = []
    cell_reports = []
    answers: dict[str, str] = {}
    eligible: list[str] = []
    smoke_ids = {item.get("source_id") for item in receipts if item.get("split") == "smoke"}
    for receipt in receipts:
        report = audit_cell(receipt, config=config)
        cell_reports.append(report)
        if not report["ok"]:
            _fail(reasons, "cell_audit_failed")
        if receipt.get("split") == "smoke" or receipt.get("repeat") != 0:
            if receipt.get("split") == "smoke" and receipt.get("source_id") in eligible:
                _fail(reasons, "smoke_in_aggregate")
            continue
        if receipt.get("source_id") in smoke_ids:
            _fail(reasons, "smoke_in_aggregate")
        answer = receipt.get("answer")
        source = receipt.get("source_id")
        if answer in {"SATISFIABLE", "UNSATISFIABLE"} and source is not None:
            previous = answers.get(source, _MISSING)
            if previous is _MISSING:
                answers[source] = answer
            elif previous != answer:
                _fail(reasons, "answer_conflict")
                answers[source] = None
            elif previous is None:
                answers[source] = None
        if receipt.get("status") in {"solved", "timeout"} and receipt.get("split") == "formal":
            eligible.append(source)
        if receipt.get("status") in {"invalid", "incomplete"} and receipt.get("split") == "formal":
            _fail(reasons, "incomplete_blocks_aggregate")
    return {
        "ok": not reasons and all(item["ok"] for item in cell_reports),
        "reasons": reasons,
        "performance_aggregated": False,
        "protocol_authorized": False,
        "mean_par2": None,
        "aggregate_refused": True,
        "eligible_repeat0_sources": eligible,
        "answers_not_voted": answers,
        "cell_reports": cell_reports,
        "guards": {
            "wall_seconds": WALL_GUARD_SECONDS,
            "cpu_seconds": CPU_GUARD_SECONDS,
            "disk_start_bytes": DISK_START_BYTES,
            "disk_stop_bytes": DISK_STOP_BYTES,
        },
    }
