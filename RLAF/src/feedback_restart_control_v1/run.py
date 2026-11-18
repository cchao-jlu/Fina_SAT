"""One-cell evaluator. Ports supply prepare/decode/search/certify receipts.

No torch, CUDA, solver, filesystem, or network call is made here. A null
action never becomes a plain-DIMACS launch.
"""

from __future__ import annotations

from typing import Any

from .classify import resolve_search
from .contract import (
    BASELINE_ARMS,
    EVALUATOR_VERSION,
    LEGAL_TRANSITIONS,
    NAMESPACE,
    PROBE_ARMS,
    PROBE_POLICY_ID,
    PROTOCOL_STATUS,
    REQUIRED_RECEIPT_FIELDS,
    SCHEMA,
    SOLVER_FLAGS,
    STUDY_ID,
    ZERO_STATE,
    ContractError,
    ManualClock,
    ResourceLedger,
    StudyConfig,
    expected_checkpoint,
    new_work_allowed,
    validate_config,
)
from .guidance import (
    CellRequest,
    action_sha256,
    encode_probe_z,
    model_satisfies,
    validate_action,
    witness_sha256,
)


def _json_z(z: tuple[float, ...] | None) -> list[float] | None:
    if z is None:
        return None
    return [float(item) for item in z]


class _Cell:
    def __init__(
        self,
        config: StudyConfig,
        cell: CellRequest,
        ports: Any,
        clock: ManualClock,
        resources: ResourceLedger,
        t0: float,
    ) -> None:
        self.config = config
        self.cell = cell
        self.ports = ports
        self.clock = clock
        self.resources = resources
        self.t0 = float(t0)
        self.deadline = self.t0 + config.answer_deadline_seconds
        self.admitted = False
        self.rec: dict[str, Any] = {
            "schema": SCHEMA,
            "evaluator_version": EVALUATOR_VERSION,
            "study_id": STUDY_ID,
            "namespace": NAMESPACE,
            "protocol_status": PROTOCOL_STATUS,
            "protocol_authorized": False,
            "arm": cell.arm,
            "source_id": cell.source_id,
            "n": cell.cnf.n,
            "repeat": cell.repeat,
            "split": cell.split,
            "t0": self.t0,
            "deadline": self.deadline,
            "status": None,
            "terminal_reason": None,
            "terminal_answer_stage": "none",
            "answer": None,
            "answer_timestamp": None,
            "candidate_exit_timestamp": None,
            "par2": None,
            "verified": False,
            "technical_failure": False,
            "validation_failure": False,
            "timeout_kind": None,
            "probe_outcome": "none",
            "final_started": False,
            "final_launches": 0,
            "probe_launches": 0,
            "encoder_calls": 0,
            "initial_decode_calls": 0,
            "feedback_decode_calls": 0,
            "checker_launches": 0,
            "initial_action": None,
            "final_action": None,
            "initial_action_sha256": None,
            "final_action_sha256": None,
            "initial_z_source": None,
            "feedback_z_source": None,
            "probe_z": None,
            "unused_probe_z": None,
            "input_written": False,
            "plain_fallback": False,
            "checkpoint_sha256": cell.checkpoint_sha256,
            "fixed_state_sha256": cell.fixed_state_sha256,
            "source_sha256": cell.cnf.sha256,
            "transitions": ["start"],
            "stage_bounds": [],
            "probe": None,
            "final": None,
            "validation": {
                "attempted": False,
                "accepted": False,
                "kind": None,
                "validator_id": None,
                "validator_version": None,
                "started_at": None,
                "ended_at": None,
                "formula_sha256": cell.cnf.sha256,
                "witness_sha256": None,
                "excluded_from_answer_clock": True,
            },
            "archive": None,
            "resource": None,
            "overrun_recorded": False,
            "automatic_retry": False,
            "performance_aggregated": False,
            "stats_trusted": False,
        }

    def execute(self) -> dict[str, Any]:
        block = self.resources.admission_block()
        if block is not None:
            return self._end("incomplete", block, timeout_kind=None)
        if self.cell.arm not in PROBE_ARMS + BASELINE_ARMS:
            self.rec["technical_failure"] = True
            return self._end("invalid", "unknown_arm")
        if self.cell.cnf.n not in self.config.frozen_zbar:
            self.rec["technical_failure"] = True
            return self._end("invalid", "unsupported_n")
        pinned = expected_checkpoint(self.cell.arm)
        if self.cell.checkpoint_sha256 != pinned or self.cell.fixed_state_sha256 != self.config.fixed_state_sha256:
            self.rec["technical_failure"] = True
            reason = "stale_checkpoint" if self.cell.checkpoint_sha256 != pinned else "stale_fixed_state"
            return self._end("invalid", reason)
        if not new_work_allowed(self.clock.now(), self.deadline):
            return self._end("timeout", "deadline_before_inference", timeout_kind="deadline_before_work")
        self.resources.admit()
        self.admitted = True
        prepared = self._prepare()
        if prepared is not None:
            return prepared
        decoded = self._initial_decode()
        if not isinstance(decoded, list):
            return decoded
        if self.cell.arm in BASELINE_ARMS:
            return self._final(decoded)
        return self._probe(decoded)

    def _prepare(self) -> dict[str, Any] | None:
        start = self.clock.now()
        prepared = self.ports.prepare({"now": start, "arm": self.cell.arm, "role": "prepare", "source_id": self.cell.source_id})
        self.clock.advance_to(prepared["ended_at"])
        self.rec["encoder_calls"] = 1
        self._stage("prepare", start, prepared["ended_at"])
        self._goto("prepared")
        if prepared["ended_at"] >= self.deadline:
            self.rec["overrun_recorded"] = True
            return self._end("timeout", "nonpreemptible_overrun", timeout_kind="nonpreemptible_overrun")
        return None

    def _initial_decode(self) -> list | dict:
        if self.cell.arm == "fixed_direct":
            z: tuple[float, ...] | None = self.config.frozen_zbar[self.cell.cnf.n]
            source = "frozen_zbar"
        elif self.cell.arm == "rlaf_matched":
            z = None
            source = "stateless"
        else:
            z = ZERO_STATE
            source = "zero"
        self.rec["initial_z_source"] = source
        if not new_work_allowed(self.clock.now(), self.deadline):
            return self._end("timeout", "deadline_before_decode", timeout_kind="deadline_before_work")
        start = self.clock.now()
        decoded = self.ports.decode(
            {
                "now": start,
                "arm": self.cell.arm,
                "which": "initial",
                "z": z,
                "z_source": source,
                "num_vars": self.cell.cnf.num_vars,
                "source_sha256": self.cell.cnf.sha256,
            }
        )
        self.clock.advance_to(decoded["ended_at"])
        self.rec["initial_decode_calls"] = 1
        self._stage("initial_decode", start, decoded["ended_at"])
        self._goto("initial_guidance")
        action = validate_action(decoded.get("action"), self.cell.cnf.num_vars)
        if decoded["ended_at"] >= self.deadline:
            self.rec["overrun_recorded"] = True
            self.rec["initial_action"] = action
            if action is not None:
                self.rec["initial_action_sha256"] = action_sha256(self.cell.cnf, action)
            return self._end("timeout", "nonpreemptible_overrun", timeout_kind="nonpreemptible_overrun")
        if action is None:
            self.rec["input_written"] = False
            self.rec["technical_failure"] = True
            return self._end("invalid", "null_or_invalid_guidance")
        self.rec["initial_action"] = action
        self.rec["initial_action_sha256"] = action_sha256(self.cell.cnf, action)
        return action

    def _probe(self, action: list) -> dict[str, Any]:
        if not new_work_allowed(self.clock.now(), self.deadline):
            return self._end("timeout", "deadline_before_probe", timeout_kind="deadline_before_work")
        start = self.clock.now()
        grace_end = min(
            self.deadline,
            start + self.config.probe_soft_target_seconds + self.config.probe_grace_seconds,
        )
        request = self._search_request(
            role="probe",
            now=start,
            action=action,
            session_id="probe-1",
            grace_end=grace_end,
            policy_id=PROBE_POLICY_ID,
        )
        result = self.ports.search(request)
        end = result["ended_at"] if _has_time(result) else self.clock.now()
        if _has_time(result):
            self.clock.advance_to(result["ended_at"])
        self.rec["probe_launches"] = 1
        self._stage("probe", start, end)
        self._goto("probe_done")
        decision = resolve_search(request, result, deadline=self.deadline, config=self.config, role="probe")
        self.rec["probe"] = {"request": _public_request(request), "result": result, "outcome": decision.outcome}
        self.rec["probe_outcome"] = decision.outcome
        self.rec["stats_trusted"] = decision.stats_trusted
        self.rec["input_written"] = True
        if decision.outcome == "incomplete":
            return self._end("incomplete", decision.reason)
        if decision.outcome == "technical":
            self.rec["technical_failure"] = True
            return self._end("invalid", decision.reason)
        if decision.outcome in {"deadline", "unknown_exhausted", "late"}:
            if decision.outcome == "late":
                self.rec["candidate_exit_timestamp"] = result.get("ended_at")
            kind = {
                "deadline": "global_deadline",
                "unknown_exhausted": "unknown_exhausted",
                "late": "late_candidate",
            }[decision.outcome]
            return self._end("timeout", decision.reason, timeout_kind=kind)
        if decision.outcome == "sat":
            return self._certify_sat(result, "probe")
        if decision.outcome == "unsat":
            return self._certify_unsat(result, "probe")
        if decision.outcome == "unknown":
            return self._after_unknown(result)
        raise ContractError(f"unhandled probe outcome {decision.outcome}")

    def _after_unknown(self, result: dict) -> dict[str, Any]:
        if not new_work_allowed(self.clock.now(), self.deadline):
            return self._end("timeout", "unknown_at_or_after_deadline", timeout_kind="unknown_exhausted")
        probe_z = encode_probe_z(result["stats"])
        self.rec["probe_z"] = _json_z(probe_z)
        if self.cell.arm == "feedback_once":
            z: tuple[float, ...] = probe_z
            source = "probe"
            self.rec["unused_probe_z"] = None
        elif self.cell.arm == "probe_restart_fixed":
            z = self.config.frozen_zbar[self.cell.cnf.n]
            source = "frozen_zbar"
            self.rec["unused_probe_z"] = _json_z(probe_z)
        else:
            raise ContractError("unknown is only legal for probe arms")
        self.rec["feedback_z_source"] = source
        if not new_work_allowed(self.clock.now(), self.deadline):
            return self._end("timeout", "deadline_before_feedback_decode", timeout_kind="deadline_before_work")
        start = self.clock.now()
        decoded = self.ports.decode(
            {
                "now": start,
                "arm": self.cell.arm,
                "which": "feedback",
                "z": z,
                "z_source": source,
                "num_vars": self.cell.cnf.num_vars,
                "source_sha256": self.cell.cnf.sha256,
            }
        )
        self.clock.advance_to(decoded["ended_at"])
        self.rec["feedback_decode_calls"] = 1
        self._stage("feedback_decode", start, decoded["ended_at"])
        self._goto("feedback_guidance")
        action = validate_action(decoded.get("action"), self.cell.cnf.num_vars)
        if decoded["ended_at"] >= self.deadline:
            self.rec["overrun_recorded"] = True
            self.rec["final_action"] = action
            if action is not None:
                self.rec["final_action_sha256"] = action_sha256(self.cell.cnf, action)
            return self._end("timeout", "nonpreemptible_overrun", timeout_kind="nonpreemptible_overrun")
        if action is None:
            self.rec["technical_failure"] = True
            return self._end("invalid", "null_or_invalid_guidance")
        self.rec["final_action"] = action
        self.rec["final_action_sha256"] = action_sha256(self.cell.cnf, action)
        return self._final(action)

    def _final(self, action: list) -> dict[str, Any]:
        if action is None:
            self.rec["technical_failure"] = True
            self.rec["input_written"] = False
            return self._end("invalid", "null_guidance_final_forbidden")
        if not new_work_allowed(self.clock.now(), self.deadline):
            return self._end("timeout", "deadline_before_final", timeout_kind="deadline_before_work")
        start = self.clock.now()
        request = self._search_request(
            role="final",
            now=start,
            action=action,
            session_id="final-1",
            grace_end=None,
            policy_id="fresh-restart-v1" if self.cell.arm in PROBE_ARMS else "baseline-v1",
        )
        self.rec["final_started"] = True
        result = self.ports.search(request)
        if _has_time(result):
            self.clock.advance_to(result["ended_at"])
        self.rec["final_launches"] = 1
        self.rec["input_written"] = True
        self.rec["final_action"] = action
        self.rec["final_action_sha256"] = action_sha256(self.cell.cnf, action)
        end = result["ended_at"] if _has_time(result) else self.clock.now()
        self._stage("final", start, end)
        self._goto("final_done")
        decision = resolve_search(request, result, deadline=self.deadline, config=self.config, role="final")
        self.rec["final"] = {"request": _public_request(request), "result": result, "outcome": decision.outcome}
        if decision.outcome == "incomplete":
            return self._end("incomplete", decision.reason)
        if decision.outcome == "technical":
            self.rec["technical_failure"] = True
            return self._end("invalid", decision.reason)
        if decision.outcome in {"deadline", "late"}:
            if decision.outcome == "late":
                self.rec["candidate_exit_timestamp"] = result.get("ended_at")
            kind = "late_candidate" if decision.outcome == "late" else "global_deadline"
            return self._end("timeout", decision.reason, timeout_kind=kind)
        if decision.outcome == "sat":
            return self._certify_sat(result, "final")
        if decision.outcome == "unsat":
            return self._certify_unsat(result, "final")
        raise ContractError(f"unhandled final outcome {decision.outcome}")

    def _certify_sat(self, result: dict, stage: str) -> dict[str, Any]:
        self.rec["candidate_exit_timestamp"] = result["ended_at"]
        self.rec["validation"]["attempted"] = True
        self.rec["validation"]["kind"] = "sat_model"
        self.rec["validation"]["validator_id"] = "local-assignment-v1"
        self.rec["validation"]["validator_version"] = EVALUATOR_VERSION
        self.rec["validation"]["started_at"] = self.clock.now()
        model = result.get("model")
        if not model_satisfies(self.cell.cnf, model):
            self.rec["validation"]["accepted"] = False
            self.rec["validation"]["ended_at"] = self.clock.now()
            self.rec["validation_failure"] = True
            return self._end("invalid", "sat_witness_rejected")
        certificate = self.ports.certify_sat(
            {
                "now": self.clock.now(),
                "formula_sha256": self.cell.cnf.sha256,
                "model": list(model),
                "stage": stage,
            }
        )
        self.clock.advance_to(certificate["ended_at"])
        self.rec["validation"]["ended_at"] = certificate["ended_at"]
        if certificate.get("validator_version"):
            self.rec["validation"]["validator_version"] = certificate["validator_version"]
        if certificate.get("accepted") is not True:
            self.rec["validation"]["accepted"] = False
            self.rec["validation_failure"] = True
            return self._end("invalid", "sat_certifier_rejected")
        self.rec["validation"]["accepted"] = True
        self.rec["validation"]["witness_sha256"] = witness_sha256(list(model))
        archived = self._archive(self.rec["validation"]["witness_sha256"])
        if archived is not None:
            return archived
        self.rec["answer_timestamp"] = result["ended_at"]
        self.rec["answer"] = "SATISFIABLE"
        self.rec["verified"] = True
        self.rec["terminal_answer_stage"] = stage
        self._goto("certified")
        return self._end("solved", f"certified_{stage}_sat")

    def _certify_unsat(self, result: dict, stage: str) -> dict[str, Any]:
        self.rec["candidate_exit_timestamp"] = result["ended_at"]
        self.rec["validation"]["attempted"] = True
        self.rec["validation"]["kind"] = "unsat_proof"
        self.rec["validation"]["started_at"] = self.clock.now()
        proof = result.get("proof")
        structural = _proof_ok(proof, self.cell.cnf.sha256)
        if structural is not None:
            self.rec["validation"]["accepted"] = False
            self.rec["validation"]["ended_at"] = self.clock.now()
            self.rec["validation"]["validator_id"] = "unsat-proof-structure"
            self.rec["validation_failure"] = True
            return self._end("invalid", structural)
        start = self.clock.now()
        certificate = self.ports.check_unsat(
            {
                "now": start,
                "formula_sha256": self.cell.cnf.sha256,
                "proof_sha256": proof["raw_sha256"],
                "stage": stage,
                "timeout_seconds": self.config.checker_timeout_seconds,
            }
        )
        self.clock.advance_to(certificate["ended_at"])
        self.rec["checker_launches"] = 1
        self._stage("checker", start, certificate["ended_at"])
        self.rec["validation"]["ended_at"] = certificate["ended_at"]
        self.rec["validation"]["validator_id"] = certificate.get("validator_id") or "injected-drat"
        self.rec["validation"]["validator_version"] = certificate.get("validator_version")
        duration = certificate["ended_at"] - start
        timed_out = bool(certificate.get("timed_out")) or duration > self.config.checker_timeout_seconds
        if timed_out or certificate.get("accepted") is not True:
            self.rec["validation"]["accepted"] = False
            self.rec["validation_failure"] = True
            reason = "checker_timeout" if timed_out else "checker_rejected"
            return self._end("invalid", reason)
        self.rec["validation"]["accepted"] = True
        self.rec["validation"]["witness_sha256"] = proof["raw_sha256"]
        archived = self._archive(proof["raw_sha256"])
        if archived is not None:
            return archived
        self.rec["answer_timestamp"] = result["ended_at"]
        self.rec["answer"] = "UNSATISFIABLE"
        self.rec["verified"] = True
        self.rec["terminal_answer_stage"] = stage
        self._goto("certified")
        return self._end("solved", f"certified_{stage}_unsat")

    def _archive(self, raw_sha256: str) -> dict[str, Any] | None:
        start = self.clock.now()
        archived = self.ports.archive(
            {
                "now": start,
                "raw_sha256": raw_sha256,
                "formula_sha256": self.cell.cnf.sha256,
            }
        )
        self.clock.advance_to(archived["ended_at"])
        self.rec["archive"] = {
            "started_at": start,
            "ended_at": archived["ended_at"],
            "raw_sha256": archived.get("raw_sha256", raw_sha256),
            "archive_sha256": archived.get("archive_sha256"),
            "archive_bytes": archived.get("archive_bytes"),
            "roundtrip_ok": archived.get("roundtrip_ok") is True,
            "excluded_from_par2": True,
        }
        self._stage("archive", start, archived["ended_at"])
        if archived.get("roundtrip_ok") is not True:
            self.rec["validation_failure"] = True
            self.rec["validation"]["accepted"] = False
            return self._end("invalid", "archive_roundtrip_failed")
        return None

    def _search_request(
        self,
        *,
        role: str,
        now: float,
        action: list,
        session_id: str,
        grace_end: float | None,
        policy_id: str,
    ) -> dict[str, Any]:
        guidance = action_sha256(self.cell.cnf, action)
        return {
            "role": role,
            "arm": self.cell.arm,
            "now": now,
            "deadline": self.deadline,
            "grace_end": grace_end,
            "soft_target_seconds": self.config.probe_soft_target_seconds if role == "probe" else None,
            "grace_seconds": self.config.probe_grace_seconds if role == "probe" else None,
            "session_id": session_id,
            "resume": False,
            "learned_clauses_carried": False,
            "formula_sha256": self.cell.cnf.sha256,
            "formula_role": "original",
            "guidance_sha256": guidance,
            "proof_logging": True,
            "flags": dict(SOLVER_FLAGS),
            "policy_id": policy_id,
            "feedback_rounds": 1 if role == "probe" else 0,
        }

    def _stage(self, name: str, start: float, end: float) -> None:
        if end < start:
            raise ContractError(f"stage {name} ends before it starts")
        if self.rec["stage_bounds"] and start < self.rec["stage_bounds"][-1]["end"]:
            raise ContractError(f"stage {name} overlaps the previous stage")
        self.rec["stage_bounds"].append({"name": name, "start": start, "end": end})

    def _goto(self, state: str) -> None:
        previous = self.rec["transitions"][-1]
        if state not in LEGAL_TRANSITIONS.get(previous, ()):
            raise ContractError(f"illegal transition {previous} -> {state}")
        self.rec["transitions"].append(state)

    def _end(self, status: str, reason: str, timeout_kind: str | None = None) -> dict[str, Any]:
        self.rec["status"] = status
        self.rec["terminal_reason"] = reason
        if status == "timeout":
            self.rec["timeout_kind"] = timeout_kind
            self.rec["par2"] = self.config.par2_timeout_seconds
        elif status == "solved":
            answer_at = self.rec["answer_timestamp"]
            if answer_at is None:
                raise ContractError("solved receipt has no answer timestamp")
            self.rec["par2"] = answer_at - self.t0
            self.rec["timeout_kind"] = None
        else:
            self.rec["par2"] = None
            self.rec["timeout_kind"] = None
        if self.rec["transitions"][-1] != "terminal":
            self._goto("terminal")
        self._fill_resource()
        _seal(self.rec, self.config)
        if self.admitted:
            self.resources.charge(
                self.rec["resource"]["elapsed_wall_seconds"],
                self.rec["resource"]["cpu_seconds"],
            )
        return self.rec

    def _fill_resource(self) -> None:
        answer_at = self.rec["answer_timestamp"]
        validation_end = self.rec["validation"]["ended_at"]
        archive = self.rec["archive"]
        cpu = 0.0
        for stage in (self.rec["probe"], self.rec["final"]):
            if stage and isinstance(stage["result"], dict):
                extra = stage["result"].get("cpu_seconds")
                if isinstance(extra, (int, float)) and not isinstance(extra, bool):
                    cpu += float(extra)
        self.rec["resource"] = {
            "answer_wall_seconds": None if answer_at is None else answer_at - self.t0,
            "certification_inclusive_wall_seconds": None if validation_end is None else validation_end - self.t0,
            "archive_wall_seconds": 0.0 if archive is None else archive["ended_at"] - archive["started_at"],
            "elapsed_wall_seconds": self.clock.now() - self.t0,
            "cpu_seconds": cpu,
            "excluded_from_par2": ["certification", "archive", "digest"],
        }


def _has_time(result: dict) -> bool:
    return isinstance(result.get("ended_at"), (int, float)) and not isinstance(result.get("ended_at"), bool)


def _public_request(request: dict) -> dict[str, Any]:
    public = dict(request)
    public["flags"] = dict(request["flags"])
    return public


def _proof_ok(proof: object, formula_sha256: str) -> str | None:
    if not isinstance(proof, dict):
        return "missing_proof"
    if proof.get("complete") is not True:
        return "corrupt_proof"
    if proof.get("formula_sha256") != formula_sha256:
        return "proof_formula_mismatch"
    if not isinstance(proof.get("raw_sha256"), str) or len(proof["raw_sha256"]) != 64:
        return "unbound_proof"
    return None


def _seal(receipt: dict, config: StudyConfig) -> None:
    missing = [field for field in REQUIRED_RECEIPT_FIELDS if field not in receipt]
    if missing:
        raise ContractError("missing receipt fields: " + ",".join(missing))
    if receipt["protocol_authorized"] is not False or receipt["plain_fallback"] is not False:
        raise ContractError("draft receipt flipped an authorization bit")
    if receipt["deadline"] != receipt["t0"] + config.answer_deadline_seconds:
        raise ContractError("deadline moved")
    previous = receipt["transitions"][0]
    if previous != "start" or receipt["transitions"][-1] != "terminal":
        raise ContractError("transition list is not closed")
    for state in receipt["transitions"][1:]:
        if state not in LEGAL_TRANSITIONS.get(previous, ()):
            raise ContractError(f"illegal transition {previous} -> {state}")
        previous = state
    status = receipt["status"]
    if status == "solved":
        if not (
            receipt["verified"]
            and receipt["answer"] in {"SATISFIABLE", "UNSATISFIABLE"}
            and receipt["answer_timestamp"] is not None
            and receipt["answer_timestamp"] <= receipt["deadline"]
            and receipt["par2"] == receipt["answer_timestamp"] - receipt["t0"]
            and receipt["technical_failure"] is False
            and receipt["validation"]["accepted"] is True
            and receipt["terminal_answer_stage"] in {"probe", "final"}
            and receipt["timeout_kind"] is None
        ):
            raise ContractError("solved receipt breaks the answer contract")
    elif status == "timeout":
        if not (
            receipt["par2"] == config.par2_timeout_seconds
            and receipt["verified"] is False
            and receipt["answer"] is None
            and receipt["technical_failure"] is False
            and receipt["validation_failure"] is False
            and receipt["timeout_kind"] is not None
        ):
            raise ContractError("timeout receipt breaks the answer contract")
    elif status == "invalid":
        if receipt["par2"] is not None or receipt["verified"] or receipt["answer"] is not None:
            raise ContractError("invalid receipt has a performance number")
    elif status == "incomplete":
        if receipt["par2"] is not None or receipt["automatic_retry"] is not False or receipt["verified"]:
            raise ContractError("incomplete receipt is aggregable")
    else:
        raise ContractError(f"unknown status {status}")
    certified = "certified" in receipt["transitions"]
    if (status == "solved") != certified:
        raise ContractError("certification state does not match status")
    if receipt["final_launches"] and receipt["final_action"] is None:
        raise ContractError("null action launched a final search")
    if receipt["probe_launches"] > 1 or receipt["final_launches"] > 1 or receipt["feedback_decode_calls"] > 1:
        raise ContractError("second feedback or extra search")


def run_cell(
    config: StudyConfig,
    cell: CellRequest,
    ports: Any,
    clock: ManualClock,
    resources: ResourceLedger | None = None,
    t0: float | None = None,
) -> dict[str, Any]:
    """Evaluate one cell.

    ``t0`` is the monotonic instant immediately before the original CNF was
    read. When omitted, it is the clock value at entry. Admission uses the
    live clock, so a caller that already sits at or past ``t0 + 60`` launches
    nothing.
    """
    validate_config(config)
    if resources is None:
        resources = ResourceLedger()
    if t0 is None:
        t0 = clock.now()
    elif t0 > clock.now():
        raise ContractError("t0 is in the future")
    return _Cell(config, cell, ports, clock, resources, t0).execute()
