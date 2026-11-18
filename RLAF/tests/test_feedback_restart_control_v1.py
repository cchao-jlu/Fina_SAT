"""Mocked acceptance tests for the 2026-11-18 feedback/restart evaluator.

No solver, torch, GPU, or historical result directory is used. Receipt fixtures
under tests/fixtures are read-only copies.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

from src.feedback_restart_control_v1 import (
    FIXED_STATE_SHA256,
    FROZEN_ZBAR,
    MATCHED_CHECKPOINT_SHA256,
    PAPER_CHECKPOINT_SHA256,
    CellRequest,
    Cnf,
    ConfigError,
    ManualClock,
    ResourceLedger,
    StudyConfig,
    assess_legacy_balanced_cell,
    audit_cell,
    campaign_report,
    candidate_timely,
    new_work_allowed,
    preflight_dependencies,
    run_cell,
    validate_schedule,
)
from src.feedback_restart_control_v1.contract import (
    ARMS,
    CPU_GUARD_SECONDS,
    DISK_START_BYTES,
    DISK_STOP_BYTES,
    REQUIRED_DEPENDENCY_ROLES,
    WALL_GUARD_SECONDS,
    ZERO_STATE as CONTRACT_ZERO,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "feedback_restart_control_v1"
CELLS = FIXTURE / "historical_cells"
MANIFEST = FIXTURE / "historical_cells_sha256.json"
VALID_MODEL = [1, -2, -3]
BAD_MODEL = [1, 2, 3]
CLAUSES = ((1, 2, 3), (-1, -2))
SOURCE_SHA = "ab" * 32
PROOF_SHA = "cd" * 32
STREAM_OUT = "11" * 32
STREAM_ERR = "22" * 32
STATS = {
    "decisions": 3,
    "conflicts": 1,
    "propagations": 8,
    "restarts": 0,
    "CPU time": 0.25,
    "Result": "UNKNOWN",
}

# Locked to the uploaded snapshots. b_runtime is intentionally absent from the
# historical implementation map; its copied hash is not a frozen binding.
SNAPSHOT_HASHES = {
    "f_runner.py": "4bac6913f99520b79838ecb2ce807c4abd0bce8c5e60bca24b334135bcccd87f",
    "f_runtime.py": "c3ad862d2bbf1c52db649663170ed66807f8a11ed82069dc9fe506e8c6b0e100",
    "f_audit.py": "977a764d0d96000182778f47a2ca8d430d23028f742e3b561f5e5a4bbdc7e3d8",
    "b_runtime_current_copy.py": "14f1e47d5500a0493b40a4a1d6fc0aac5d2fd5732e3a9572d7cbe43e435e5b1c",
}
HISTORICAL_IMPLEMENTATION_MAP_HAS_NO_B_RUNTIME = True


def toy_cnf(size: int = 350) -> Cnf:
    return Cnf(num_vars=3, clauses=CLAUSES, sha256=SOURCE_SHA, n=size)


def make_cell(arm: str = "feedback_once", size: int = 350, **overrides) -> CellRequest:
    checkpoint = MATCHED_CHECKPOINT_SHA256 if arm == "rlaf_matched" else PAPER_CHECKPOINT_SHA256
    values = dict(
        arm=arm,
        cnf=toy_cnf(size),
        source_id=f"src-{arm}",
        checkpoint_sha256=checkpoint,
        fixed_state_sha256=FIXED_STATE_SHA256,
        repeat=0,
        split="formal",
    )
    values.update(overrides)
    return CellRequest(**values)


def proof_for(cnf: Cnf, raw: str = PROOF_SHA) -> dict:
    return {"complete": True, "formula_sha256": cnf.sha256, "raw_sha256": raw}


def decode_action(request: dict) -> dict:
    z = request["z"]
    if request["z_source"] == "stateless":
        weight = 2.0
    else:
        weight = 1.0 + (0.0 if z is None else float(z[0]) * 1e-4)
    action = [[1, weight] for _ in range(request["num_vars"])]
    return {"ended_at": request["now"] + 0.01, "action": action}


def echoed(request: dict, **overrides) -> dict:
    receipt = {
        "launched": True,
        "started_at": request["now"],
        "ended_at": request["now"] + 0.4,
        "session_id": request["session_id"],
        "formula_sha256": request["formula_sha256"],
        "guidance_sha256": request["guidance_sha256"],
        "proof_logging": True,
        "learned_clauses_carried": False,
        "resume": False,
        "returncode": 0,
        "reported_result": "UNKNOWN",
        "model": None,
        "proof": None,
        "stats": dict(STATS),
        "stdout_sha256": STREAM_OUT,
        "stderr_sha256": STREAM_ERR,
        "stop_reason": "soft_stop",
        "hard_killed": False,
        "clean_exit": True,
        "cpu_seconds": 0.1,
    }
    receipt.update(overrides)
    return receipt


def sat_result(request: dict, **overrides) -> dict:
    values = dict(
        ended_at=request["now"] + 0.3,
        returncode=10,
        reported_result="SATISFIABLE",
        model=list(VALID_MODEL),
        stop_reason=None,
        stats=None,
    )
    values.update(overrides)
    return echoed(request, **values)


def unsat_result(request: dict, cnf: Cnf, **overrides) -> dict:
    values = dict(
        ended_at=request["now"] + 0.3,
        returncode=20,
        reported_result="UNSATISFIABLE",
        model=None,
        proof=proof_for(cnf),
        stop_reason=None,
        stats=None,
    )
    values.update(overrides)
    return echoed(request, **values)


class Ports:
    def __init__(self, search):
        self.search_fn = search
        self.prepare_calls = []
        self.decode_calls = []
        self.search_calls = []
        self.sat_calls = []
        self.unsat_calls = []
        self.archive_calls = []
        self.prepare_delay = 0.02
        self.decode_fn = decode_action
        self.sat_delay = 0.05
        self.sat_accept = True
        self.unsat_delay = 0.05
        self.unsat_accept = True
        self.unsat_timeout = False
        self.archive_delay = 0.01
        self.archive_ok = True

    def prepare(self, request):
        self.prepare_calls.append(request)
        return {"ended_at": request["now"] + self.prepare_delay}

    def decode(self, request):
        self.decode_calls.append(request)
        return self.decode_fn(request)

    def search(self, request):
        self.search_calls.append(request)
        return self.search_fn(request)

    def certify_sat(self, request):
        self.sat_calls.append(request)
        return {
            "ended_at": request["now"] + self.sat_delay,
            "accepted": self.sat_accept,
            "validator_version": "mock-sat-1",
        }

    def check_unsat(self, request):
        self.unsat_calls.append(request)
        return {
            "ended_at": request["now"] + self.unsat_delay,
            "accepted": self.unsat_accept,
            "timed_out": self.unsat_timeout,
            "validator_id": "mock-drat",
            "validator_version": "mock-drat-1",
        }

    def archive(self, request):
        self.archive_calls.append(request)
        return {
            "ended_at": request["now"] + self.archive_delay,
            "roundtrip_ok": self.archive_ok,
            "raw_sha256": request["raw_sha256"],
            "archive_sha256": "ef" * 32,
            "archive_bytes": 4,
        }


class Boom:
    def __getattr__(self, name):
        def refuse(*_args, **_kwargs):
            raise AssertionError(f"{name} was called")

        return refuse


def run(arm="feedback_once", search=None, ports=None, clock=None, resources=None, t0=None, cell=None, config=None):
    ports = ports or Ports(search)
    clock = clock or ManualClock(1000.0)
    config = config or StudyConfig.create()
    cell = cell or make_cell(arm)
    receipt = run_cell(config, cell, ports, clock, resources=resources, t0=t0)
    return receipt, ports, clock


def assert_audited(test, receipt, cnf=None):
    report = audit_cell(receipt, cnf=cnf or toy_cnf(receipt["n"]))
    test.assertTrue(report["ok"], report["reasons"])
    return report


class FeedbackRestartControlV1Tests(unittest.TestCase):
    def test_01_timely_probe_sat_stops_before_final(self):
        cnf = toy_cnf()
        receipt, ports, _clock = run("feedback_once", lambda request: sat_result(request))
        self.assertEqual(receipt["status"], "solved")
        self.assertEqual(receipt["terminal_answer_stage"], "probe")
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(receipt["feedback_decode_calls"], 0)
        self.assertEqual(receipt["probe_launches"], 1)
        self.assertEqual(receipt["checker_launches"], 0)
        self.assertEqual(len(ports.search_calls), 1)
        self.assertEqual(len(ports.sat_calls), 1)
        probe_exit = ports.search_calls[0]["now"] + 0.3
        self.assertEqual(receipt["answer_timestamp"], probe_exit)
        self.assertEqual(receipt["par2"], probe_exit - receipt["t0"])
        self.assertTrue(receipt["validation"]["accepted"])
        self.assertEqual(receipt["validation"]["validator_id"], "local-assignment-v1")
        self.assertFalse(receipt["protocol_authorized"])
        assert_audited(self, receipt, cnf)

    def test_02_timely_probe_unsat_uses_one_checker_and_no_final(self):
        cnf = toy_cnf()
        receipt, ports, _clock = run("probe_restart_fixed", lambda request: unsat_result(request, cnf))
        self.assertEqual(receipt["status"], "solved")
        self.assertEqual(receipt["answer"], "UNSATISFIABLE")
        self.assertEqual(receipt["terminal_answer_stage"], "probe")
        self.assertEqual(receipt["checker_launches"], 1)
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(ports.search_calls[0]["proof_logging"], True)
        self.assertEqual(ports.unsat_calls[0]["formula_sha256"], cnf.sha256)
        self.assertEqual(receipt["validation"]["validator_id"], "mock-drat")
        assert_audited(self, receipt, cnf)

    def test_03_invalid_sat_model_is_not_a_timeout_or_fallback(self):
        def search(request):
            return sat_result(request, model=list(BAD_MODEL))

        receipt, ports, _clock = run(search=search)
        self.assertEqual(receipt["status"], "invalid")
        self.assertIsNone(receipt["par2"])
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(ports.sat_calls, [])
        self.assertTrue(receipt["validation_failure"])
        self.assertFalse(receipt["technical_failure"])
        self.assertEqual(len(ports.search_calls), 1)
        assert_audited(self, receipt)

    def test_04_unsat_proof_and_checker_failures_are_invalid(self):
        cnf = toy_cnf()

        def missing(request):
            return unsat_result(request, cnf, proof=None)

        receipt, ports, _clock = run(search=missing)
        self.assertEqual(receipt["status"], "invalid")
        self.assertEqual(receipt["terminal_reason"], "missing_proof")
        self.assertEqual(ports.unsat_calls, [])
        self.assertIsNone(receipt["par2"])
        assert_audited(self, receipt, cnf)

        def corrupt(request):
            return unsat_result(request, cnf, proof={"complete": False, "formula_sha256": cnf.sha256, "raw_sha256": PROOF_SHA})

        receipt, ports, _clock = run(search=corrupt)
        self.assertEqual(receipt["terminal_reason"], "corrupt_proof")
        self.assertEqual(ports.unsat_calls, [])

        ports = Ports(lambda request: unsat_result(request, cnf))
        ports.unsat_accept = False
        receipt, ports, _clock = run(ports=ports)
        self.assertEqual(receipt["terminal_reason"], "checker_rejected")
        self.assertEqual(len(ports.unsat_calls), 1)
        self.assertNotEqual(receipt["status"], "incomplete")

        ports = Ports(lambda request: unsat_result(request, cnf))
        ports.unsat_timeout = True
        ports.unsat_accept = True
        receipt, _ports, _clock = run(ports=ports)
        self.assertEqual(receipt["terminal_reason"], "checker_timeout")
        self.assertIsNone(receipt["par2"])

        ports = Ports(lambda request: unsat_result(request, cnf))
        ports.unsat_delay = 1801.0
        receipt, _ports, _clock = run(ports=ports)
        self.assertEqual(receipt["status"], "invalid")
        self.assertEqual(receipt["terminal_reason"], "checker_timeout")

    def test_05_unknown_feedback_and_fixed_restart_share_the_probe(self):
        def search(request):
            if request["role"] == "probe":
                return echoed(request, ended_at=request["now"] + 0.4)
            return sat_result(request, ended_at=request["now"] + 0.2)

        feedback, feedback_ports, _clock = run("feedback_once", search)
        control, control_ports, _clock = run("probe_restart_fixed", search)
        self.assertEqual(feedback["status"], "solved")
        self.assertEqual(control["status"], "solved")
        self.assertEqual(feedback["final_launches"], 1)
        self.assertEqual(control["final_launches"], 1)
        self.assertEqual(feedback["deadline"], feedback["t0"] + 60.0)
        self.assertEqual(control["deadline"], feedback["deadline"])
        probe_keys = ("flags", "policy_id", "proof_logging", "grace_seconds", "soft_target_seconds", "feedback_rounds", "formula_sha256", "guidance_sha256", "deadline")
        for key in probe_keys:
            self.assertEqual(feedback_ports.search_calls[0][key], control_ports.search_calls[0][key])
        self.assertIs(feedback_ports.decode_calls[0]["z"], CONTRACT_ZERO)
        self.assertIs(control_ports.decode_calls[0]["z"], CONTRACT_ZERO)
        self.assertEqual(feedback_ports.decode_calls[0]["z_source"], "zero")
        self.assertIs(control_ports.decode_calls[1]["z"], FROZEN_ZBAR[350])
        self.assertEqual(control["feedback_z_source"], "frozen_zbar")
        self.assertEqual(control["unused_probe_z"], feedback["probe_z"])
        self.assertNotEqual(control["unused_probe_z"], list(FROZEN_ZBAR[350]))
        self.assertEqual(feedback["feedback_z_source"], "probe")
        self.assertIsNot(feedback_ports.decode_calls[1]["z"], FROZEN_ZBAR[350])
        for ports in (feedback_ports, control_ports):
            final = ports.search_calls[1]
            self.assertEqual(final["deadline"], 1060.0)
            self.assertNotEqual(final["session_id"], ports.search_calls[0]["session_id"])
            self.assertFalse(final["learned_clauses_carried"])
            self.assertFalse(final["resume"])
            self.assertEqual(final["formula_role"], "original")
            self.assertEqual(final["formula_sha256"], SOURCE_SHA)
        assert_audited(self, feedback)
        assert_audited(self, control)

    def test_06_incomplete_unknown_stats_do_not_zero_fill(self):
        variants = [
            {"stats": {"conflicts": 1, "propagations": 1, "restarts": 0, "CPU time": 0.1, "Result": "UNKNOWN"}},
            {"stats": {**STATS, "decisions": float("nan")}},
            {"stats": {**STATS, "conflicts": -1}},
            {"returncode": 10, "reported_result": "UNKNOWN"},
        ]
        for overrides in variants:
            receipt, ports, _clock = run(search=lambda request, overrides=overrides: echoed(request, ended_at=request["now"] + 0.2, **overrides))
            self.assertEqual(receipt["status"], "invalid", overrides)
            self.assertTrue(receipt["technical_failure"])
            self.assertEqual(receipt["feedback_decode_calls"], 0)
            self.assertEqual(receipt["final_launches"], 0)
            self.assertEqual(len(ports.search_calls), 1)
            self.assertIsNone(receipt["probe_z"])
            assert_audited(self, receipt)

    def test_07_deadline_already_passed_launches_nothing(self):
        receipt, _ports, _clock = run(ports=Boom(), clock=ManualClock(1060.0), t0=1000.0)
        self.assertEqual(receipt["status"], "timeout")
        self.assertEqual(receipt["par2"], 120.0)
        self.assertEqual(receipt["timeout_kind"], "deadline_before_work")
        self.assertEqual(receipt["encoder_calls"], 0)
        self.assertEqual(receipt["probe_launches"], 0)
        self.assertEqual(receipt["initial_decode_calls"], 0)
        assert_audited(self, receipt)

    def test_08_deadline_in_the_gaps_does_not_reset_or_launch_final(self):
        def killed(request):
            return echoed(
                request,
                ended_at=request["deadline"] + 0.01,
                stop_reason="global_deadline",
                hard_killed=True,
                clean_exit=False,
                reported_result=None,
                returncode=None,
                stats=dict(STATS),
            )

        receipt, ports, _clock = run(search=killed)
        self.assertEqual(receipt["status"], "timeout")
        self.assertEqual(receipt["par2"], 120.0)
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(len(ports.search_calls), 1)
        self.assertFalse(receipt["stats_trusted"])
        assert_audited(self, receipt)

        def exhausted(request):
            return echoed(request, ended_at=request["deadline"], reported_result="UNKNOWN", returncode=0)

        receipt, ports, _clock = run(search=exhausted)
        self.assertEqual(receipt["timeout_kind"], "unknown_exhausted")
        self.assertEqual(len(ports.decode_calls), 1)
        self.assertEqual(receipt["final_launches"], 0)
        assert_audited(self, receipt)

        def late_readout(request):
            if request["which"] == "initial":
                return decode_action(request)
            return {"ended_at": 1060.0, "action": [[1, 1.0], [1, 1.0], [1, 1.0]]}

        ports = Ports(lambda request: echoed(request, ended_at=request["now"] + 0.2))
        ports.decode_fn = late_readout
        receipt, ports, _clock = run(ports=ports)
        self.assertEqual(receipt["status"], "timeout")
        self.assertEqual(receipt["timeout_kind"], "nonpreemptible_overrun")
        self.assertTrue(receipt["overrun_recorded"])
        self.assertEqual(len(ports.search_calls), 1)
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(receipt["deadline"], 1060.0)
        assert_audited(self, receipt)

        ports = Ports(lambda request: sat_result(request))
        ports.prepare_delay = 60.0
        receipt, ports, _clock = run(ports=ports)
        self.assertEqual(receipt["timeout_kind"], "nonpreemptible_overrun")
        self.assertEqual(ports.decode_calls, [])
        self.assertEqual(ports.search_calls, [])
        assert_audited(self, receipt)

    def test_09_exact_deadline_is_timely_and_a_later_exit_is_not(self):
        def at_deadline(request):
            return sat_result(request, ended_at=1060.0)

        receipt, ports, _clock = run("fixed_direct", at_deadline)
        self.assertEqual(receipt["status"], "solved")
        self.assertEqual(receipt["answer_timestamp"], 1060.0)
        self.assertEqual(receipt["terminal_answer_stage"], "final")
        self.assertEqual(len(ports.sat_calls), 1)
        assert_audited(self, receipt)

        def after_deadline(request):
            return sat_result(request, ended_at=1060.0 + 1e-9)

        ports = Ports(after_deadline)
        receipt, ports, _clock = run("fixed_direct", ports=ports)
        self.assertEqual(receipt["status"], "timeout")
        self.assertEqual(receipt["timeout_kind"], "late_candidate")
        self.assertEqual(receipt["par2"], 120.0)
        self.assertEqual(ports.sat_calls, [])
        self.assertFalse(receipt["verified"])
        assert_audited(self, receipt)

        def near_deadline_probe(request):
            return sat_result(request, ended_at=1060.0)

        ports = Ports(near_deadline_probe)
        ports.prepare_delay = 59.9
        ports.decode_fn = lambda request: {"ended_at": request["now"] + 0.01, "action": [[1, 1.0], [1, 1.0], [1, 1.0]]}
        receipt, ports, _clock = run("feedback_once", ports=ports)
        self.assertEqual(receipt["status"], "solved")
        self.assertEqual(receipt["answer_timestamp"], 1060.0)
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(ports.search_calls[0]["grace_end"], 1060.0)
        assert_audited(self, receipt)

    def test_10_certification_after_the_deadline_keeps_the_answer_timestamp(self):
        def search(request):
            return sat_result(request, ended_at=request["now"] + 0.2)

        ports = Ports(search)
        ports.sat_delay = 70.0
        receipt, ports, _clock = run(ports=ports)
        exit_at = ports.search_calls[0]["now"] + 0.2
        self.assertEqual(receipt["status"], "solved")
        self.assertEqual(receipt["answer_timestamp"], exit_at)
        self.assertGreater(receipt["resource"]["certification_inclusive_wall_seconds"], 60.0)
        self.assertEqual(receipt["par2"], exit_at - receipt["t0"])
        self.assertLess(receipt["par2"], 60.0)
        assert_audited(self, receipt)

    def test_11_unknown_inside_grace_continues_on_the_original_deadline(self):
        def search(request):
            if request["role"] == "probe":
                return echoed(request, ended_at=request["now"] + 1.2)
            return sat_result(request, ended_at=request["now"] + 0.25)

        receipt, ports, _clock = run(search=search)
        probe = ports.search_calls[0]
        self.assertLessEqual(probe["now"] + 1.2, probe["grace_end"])
        self.assertGreater(probe["now"] + 1.2, probe["now"] + probe["soft_target_seconds"])
        self.assertEqual(ports.search_calls[1]["deadline"], receipt["t0"] + 60.0)
        self.assertGreater(receipt["par2"], 1.2)
        self.assertEqual(receipt["status"], "solved")
        assert_audited(self, receipt)

    def test_12_failing_to_stop_inside_grace_before_the_deadline_is_technical(self):
        def search(request):
            return echoed(
                request,
                ended_at=request["now"] + 1.3,
                stop_reason="grace_exceeded",
                clean_exit=False,
                reported_result=None,
                returncode=None,
                stats=None,
            )

        receipt, ports, _clock = run(search=search)
        self.assertEqual(receipt["status"], "invalid")
        self.assertEqual(receipt["terminal_reason"], "grace_stop_failed")
        self.assertTrue(receipt["technical_failure"])
        self.assertNotEqual(receipt["status"], "timeout")
        self.assertIsNone(receipt["par2"])
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(len(ports.search_calls), 1)
        assert_audited(self, receipt)

    def test_13_global_deadline_kill_and_early_hard_kill_are_different(self):
        def global_kill(request):
            return echoed(
                request,
                ended_at=request["deadline"] + 0.02,
                stop_reason="global_deadline",
                hard_killed=True,
                clean_exit=False,
                reported_result=None,
                returncode=None,
                stats={"decisions": 9, "conflicts": 9, "propagations": 9, "restarts": 1, "CPU time": 1.0},
            )

        receipt, _ports, _clock = run(search=global_kill)
        self.assertEqual(receipt["status"], "timeout")
        self.assertEqual(receipt["terminal_reason"], "global_deadline")
        self.assertFalse(receipt["stats_trusted"])
        self.assertIsNone(receipt["probe_z"])
        self.assertEqual(receipt["final_launches"], 0)
        assert_audited(self, receipt)

        def early_kill(request):
            return echoed(
                request,
                ended_at=request["now"] + 0.2,
                stop_reason="hard_kill",
                hard_killed=True,
                clean_exit=False,
                reported_result=None,
                returncode=None,
                stats=None,
            )

        receipt, _ports, _clock = run(search=early_kill)
        self.assertEqual(receipt["status"], "invalid")
        self.assertEqual(receipt["terminal_reason"], "hard_kill_before_deadline")
        self.assertTrue(receipt["technical_failure"])
        self.assertIsNone(receipt["par2"])
        assert_audited(self, receipt)

    def test_14_null_guidance_does_not_launch_plain_or_weighted_search(self):
        def null_decode(request):
            return {"ended_at": request["now"] + 0.01, "action": None}

        ports = Ports(lambda request: sat_result(request))
        ports.decode_fn = null_decode
        receipt, ports, _clock = run("fixed_direct", ports=ports)
        self.assertEqual(receipt["status"], "invalid")
        self.assertEqual(receipt["terminal_reason"], "null_or_invalid_guidance")
        self.assertFalse(receipt["input_written"])
        self.assertFalse(receipt["plain_fallback"])
        self.assertEqual(ports.search_calls, [])
        self.assertEqual(receipt["final_launches"], 0)
        assert_audited(self, receipt)

        solved, _ports, _clock = run("fixed_direct", sat_result)
        forged = copy.deepcopy(solved)
        forged["final_action"] = None
        forged["final_launches"] = 1
        report = audit_cell(forged, cnf=toy_cnf())
        self.assertIn("null_guidance_final_launch", report["reasons"])

        self.assertTrue(CELLS.is_dir())
        rejected = 0
        for folder in sorted(path for path in CELLS.iterdir() if path.is_dir()):
            action = json.loads((folder / "action.json").read_text())
            result = json.loads((folder / "result.json").read_text())
            observation = json.loads((folder / "observation.json").read_text())
            stdout = (folder / "probe_stage" / "probe.stdout").read_text()
            assessment = assess_legacy_balanced_cell(action, result, observation, stdout)
            self.assertTrue(assessment["rejected"], folder.name)
            self.assertIn("null_action_with_final_launch", assessment["reasons"])
            self.assertIn("solved_probe_followed_by_final_launch", assessment["reasons"])
            self.assertIn("absent_technical_failure_field", assessment["reasons"])
            rejected += 1
        self.assertEqual(rejected, 13)

    def test_15_null_final_action_is_legal_after_a_certified_probe(self):
        receipt, _ports, _clock = run(search=sat_result)
        self.assertIsNone(receipt["final_action"])
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(receipt["status"], "solved")
        self.assertIsNotNone(receipt["initial_action"])
        assert_audited(self, receipt)

    def test_16_plain_or_fixed_fallback_and_a_second_round_are_rejected(self):
        with self.assertRaises(ConfigError) as raised:
            StudyConfig.create(fallback="plain")
        self.assertIn("fallback_not_in_protocol", raised.exception.reasons)
        with self.assertRaises(ConfigError):
            StudyConfig.create(fallback="fixed")
        with self.assertRaises(ConfigError):
            StudyConfig.create(feedback_rounds=2)
        with self.assertRaises(ConfigError):
            run_cell(StudyConfig(fallback="plain"), make_cell(), Boom(), ManualClock(0.0))

    def test_17_stale_bindings_and_the_wrong_formula_are_rejected(self):
        stale = make_cell(checkpoint_sha256="0" * 64)
        receipt, _ports, _clock = run(cell=stale, ports=Boom())
        self.assertEqual(receipt["terminal_reason"], "stale_checkpoint")
        self.assertEqual(receipt["encoder_calls"], 0)

        def wrong_formula(request):
            return sat_result(request, formula_sha256="ff" * 32)

        receipt, _ports, _clock = run(search=wrong_formula)
        self.assertEqual(receipt["terminal_reason"], "formula_mismatch")
        self.assertEqual(receipt["status"], "invalid")
        self.assertEqual(receipt["final_launches"], 0)

        cnf = toy_cnf()

        def wrong_proof(request):
            bad = proof_for(cnf)
            bad["formula_sha256"] = "ee" * 32
            return unsat_result(request, cnf, proof=bad)

        receipt, ports, _clock = run(search=wrong_proof)
        self.assertEqual(receipt["terminal_reason"], "proof_formula_mismatch")
        self.assertEqual(ports.unsat_calls, [])

        def wrong_action(request):
            if request["role"] == "final":
                return sat_result(request, guidance_sha256="ab" * 32)
            return echoed(request, ended_at=request["now"] + 0.2)

        receipt, _ports, _clock = run(search=wrong_action)
        self.assertEqual(receipt["terminal_reason"], "action_hash_mismatch")
        self.assertNotEqual(receipt["status"], "solved")

    def test_18_restart_sees_the_original_cnf_and_a_fresh_session(self):
        def search(request):
            if request["role"] == "probe":
                return echoed(request, ended_at=request["now"] + 0.2)
            return sat_result(request)

        receipt, ports, _clock = run(search=search)
        final = ports.search_calls[1]
        self.assertEqual(final["formula_sha256"], receipt["source_sha256"])
        self.assertEqual(final["formula_role"], "original")
        self.assertNotEqual(final["session_id"], ports.search_calls[0]["session_id"])
        self.assertFalse(final["learned_clauses_carried"])
        self.assertFalse(final["resume"])
        self.assertEqual(final["deadline"], receipt["deadline"])
        assert_audited(self, receipt)

        def carried(request):
            if request["role"] == "probe":
                return echoed(request, ended_at=request["now"] + 0.2)
            return sat_result(request, learned_clauses_carried=True)

        receipt, _ports, _clock = run(search=carried)
        self.assertEqual(receipt["terminal_reason"], "learned_clauses_carried")
        self.assertEqual(receipt["status"], "invalid")

    def test_19_probe_arms_share_early_exit_without_an_artificial_final(self):
        feedback, feedback_ports, _clock = run("feedback_once", sat_result)
        control, control_ports, _clock = run("probe_restart_fixed", sat_result)
        self.assertEqual(feedback["final_launches"], 0)
        self.assertEqual(control["final_launches"], 0)
        self.assertEqual(feedback["feedback_decode_calls"], 0)
        self.assertEqual(control["feedback_decode_calls"], 0)
        self.assertEqual(feedback["terminal_answer_stage"], "probe")
        self.assertEqual(control["terminal_answer_stage"], "probe")
        self.assertEqual(len(feedback_ports.search_calls), 1)
        self.assertEqual(len(control_ports.search_calls), 1)
        self.assertEqual(feedback_ports.search_calls[0]["policy_id"], control_ports.search_calls[0]["policy_id"])
        assert_audited(self, feedback)
        assert_audited(self, control)

    def test_20_ledger_counts_are_split_and_a_second_search_is_rejected(self):
        solved, _ports, _clock = run(search=sat_result)
        self.assertEqual(solved["encoder_calls"], 1)
        self.assertEqual(solved["initial_decode_calls"], 1)
        self.assertEqual(solved["feedback_decode_calls"], 0)
        self.assertEqual(solved["probe_launches"], 1)
        self.assertEqual(solved["final_launches"], 0)
        self.assertEqual(solved["checker_launches"], 0)
        assert_audited(self, solved)

        def both(request):
            if request["role"] == "probe":
                return echoed(request, ended_at=request["now"] + 0.2)
            return sat_result(request)

        unknown, ports, _clock = run(search=both)
        self.assertEqual(unknown["feedback_decode_calls"], 1)
        self.assertEqual(unknown["final_launches"], 1)
        self.assertEqual(unknown["probe_launches"], 1)
        self.assertEqual(len(ports.search_calls), 2)
        self.assertEqual(unknown["checker_launches"], 0)
        assert_audited(self, unknown)

        fixed, fixed_ports, _clock = run("fixed_direct", sat_result)
        self.assertEqual(fixed["probe_launches"], 0)
        self.assertIs(fixed_ports.decode_calls[0]["z"], FROZEN_ZBAR[350])
        self.assertEqual(fixed["final_launches"], 1)
        matched, matched_ports, _clock = run("rlaf_matched", sat_result)
        self.assertIsNone(matched_ports.decode_calls[0]["z"])
        self.assertEqual(matched["probe_launches"], 0)
        self.assertEqual(matched["checkpoint_sha256"], MATCHED_CHECKPOINT_SHA256)
        assert_audited(self, fixed)
        assert_audited(self, matched)

        forged = copy.deepcopy(unknown)
        forged["probe_launches"] = 2
        self.assertIn("second_feedback_or_search", audit_cell(forged, cnf=toy_cnf())["reasons"])

    def test_21_forged_timeout_label_loses_to_the_raw_probe(self):
        receipt, _ports, _clock = run(search=sat_result)
        forged = copy.deepcopy(receipt)
        forged["status"] = "timeout"
        forged["timeout_kind"] = "probe_failure"
        forged["par2"] = 120.0
        forged["verified"] = False
        forged["answer"] = None
        report = audit_cell(forged, cnf=toy_cnf())
        self.assertFalse(report["ok"])
        self.assertIn("forged_timeout_kind", report["reasons"])

    def test_22_missing_technical_failure_and_unbound_streams_are_schema_errors(self):
        receipt, _ports, _clock = run(search=sat_result)
        missing = copy.deepcopy(receipt)
        del missing["technical_failure"]
        report = audit_cell(missing, cnf=toy_cnf())
        self.assertFalse(report["ok"])
        self.assertIn("missing_field:technical_failure", report["reasons"])
        self.assertFalse(any(reason == "technical_failure_false" for reason in report["reasons"]))

        unbound = copy.deepcopy(receipt)
        unbound["probe"]["result"]["stdout_sha256"] = None
        report = audit_cell(unbound, cnf=toy_cnf())
        self.assertIn("unbound_probe_streams", report["reasons"])

    def test_23_valid_final_answer_does_not_repair_an_illegal_probe_transition(self):
        def both(request):
            if request["role"] == "probe":
                return echoed(request, ended_at=request["now"] + 0.2)
            return sat_result(request)

        receipt, _ports, _clock = run(search=both)
        self.assertEqual(receipt["status"], "solved")
        forged = copy.deepcopy(receipt)
        forged["probe"]["result"]["reported_result"] = "SATISFIABLE"
        forged["probe"]["result"]["returncode"] = 10
        forged["probe"]["result"]["model"] = list(VALID_MODEL)
        forged["probe"]["result"]["stats"] = None
        forged["probe"]["outcome"] = "sat"
        forged["probe_outcome"] = "sat"
        report = audit_cell(forged, cnf=toy_cnf())
        self.assertFalse(report["ok"])
        self.assertIn("illegal_probe_to_final", report["reasons"])

    def test_24_resource_guard_stops_incomplete_and_refuses_an_aggregate(self):
        resources = ResourceLedger(disk_free_bytes=DISK_STOP_BYTES - 1)
        receipt, _ports, _clock = run(ports=Boom(), resources=resources)
        self.assertEqual(receipt["status"], "incomplete")
        self.assertEqual(receipt["terminal_reason"], "disk_stop")
        self.assertIsNone(receipt["par2"])
        self.assertFalse(receipt["automatic_retry"])
        assert_audited(self, receipt)
        report = campaign_report([receipt])
        self.assertFalse(report["performance_aggregated"])
        self.assertIsNone(report["mean_par2"])
        self.assertIn("incomplete_blocks_aggregate", report["reasons"])

        start = ResourceLedger(disk_free_bytes=DISK_START_BYTES - 1)
        receipt, _ports, _clock = run(ports=Boom(), resources=start)
        self.assertEqual(receipt["terminal_reason"], "disk_start")

        walled = ResourceLedger(wall_seconds=WALL_GUARD_SECONDS)
        receipt, _ports, _clock = run(ports=Boom(), resources=walled)
        self.assertEqual(receipt["terminal_reason"], "wall_guard")
        cpus = ResourceLedger(cpu_seconds=CPU_GUARD_SECONDS)
        receipt, _ports, _clock = run(ports=Boom(), resources=cpus)
        self.assertEqual(receipt["terminal_reason"], "cpu_guard")

        def guard(request):
            return echoed(request, stop_reason="resource_guard", clean_exit=False, reported_result=None, returncode=None, stats=None)

        receipt, ports, _clock = run(search=guard)
        self.assertEqual(receipt["status"], "incomplete")
        self.assertIsNotNone(receipt["probe"])
        self.assertEqual(receipt["final_launches"], 0)
        self.assertEqual(len(ports.search_calls), 1)
        self.assertFalse(receipt["automatic_retry"])
        self.assertGreater(WALL_GUARD_SECONDS, 0)
        self.assertGreater(CPU_GUARD_SECONDS, 0)
        assert_audited(self, receipt)

    def test_25_answer_conflicts_are_not_resolved_by_a_vote(self):
        sat, _ports, _clock = run("fixed_direct", sat_result, cell=make_cell("fixed_direct", source_id="same-source"))
        cnf = toy_cnf()

        def unsat(request):
            return unsat_result(request, cnf)

        other, _ports, _clock = run("rlaf_matched", unsat, cell=make_cell("rlaf_matched", source_id="same-source"))
        report = campaign_report([sat, other])
        self.assertIn("answer_conflict", report["reasons"])
        self.assertIsNone(report["answers_not_voted"]["same-source"])
        self.assertIsNone(report["mean_par2"])
        self.assertFalse(report["performance_aggregated"])

    def test_26_schedule_matrix_keeps_smoke_and_repeats_out_of_the_main_aggregate(self):
        entries = _matrix()
        report = validate_schedule(entries)
        self.assertTrue(report["ok"], report["reasons"])
        self.assertEqual(report["formal_main_cells"], 768)
        self.assertEqual(report["formal_repeat_cells"], 48)
        self.assertEqual(report["formal_cells"], 816)
        self.assertEqual(report["smoke_cells"], 16)
        self.assertEqual(report["total_cells"], 832)

        duplicate = list(entries)
        duplicate.append(dict(entries[0]))
        self.assertIn("duplicate_cell", validate_schedule(duplicate)["reasons"])
        labeled = dict(entries[0])
        labeled["par2"] = 1.0
        self.assertIn("schedule_contains_outcomes", validate_schedule([labeled] + entries[1:])["reasons"])

        sat, _ports, _clock = run("fixed_direct", sat_result, cell=make_cell("fixed_direct", source_id="main-source"))
        repeat = copy.deepcopy(sat)
        repeat["repeat"] = 1
        repeat["source_id"] = "main-source"
        smoke = copy.deepcopy(sat)
        smoke["split"] = "smoke"
        smoke["source_id"] = "smoke-source"
        smoke["repeat"] = 0
        campaign = campaign_report([sat, repeat, smoke])
        self.assertEqual(campaign["eligible_repeat0_sources"], ["main-source"])
        self.assertNotIn("smoke-source", campaign["eligible_repeat0_sources"])
        self.assertIsNone(campaign["mean_par2"])
        self.assertTrue(campaign["cell_reports"][0]["ok"])

    def test_27_dependency_preflight_binds_the_shared_runtime_helper(self):
        blobs = {role: f"bytes-{role}".encode() for role in REQUIRED_DEPENDENCY_ROLES}
        expected = {role: hashlib.sha256(payload).hexdigest() for role, payload in blobs.items()}
        self.assertTrue(preflight_dependencies(expected, blobs)["ok"])
        self.assertIn("shared_runtime_helper", REQUIRED_DEPENDENCY_ROLES)

        missing = dict(expected)
        del missing["shared_runtime_helper"]
        report = preflight_dependencies(missing, blobs)
        self.assertIn("missing_binding:shared_runtime_helper", report["reasons"])

        changed = dict(blobs)
        changed["shared_runtime_helper"] = b"mutated"
        report = preflight_dependencies(expected, changed)
        self.assertIn("hash_mismatch:shared_runtime_helper", report["reasons"])
        self.assertTrue(HISTORICAL_IMPLEMENTATION_MAP_HAS_NO_B_RUNTIME)
        self.assertEqual(SNAPSHOT_HASHES["b_runtime_current_copy.py"], "14f1e47d5500a0493b40a4a1d6fc0aac5d2fd5732e3a9572d7cbe43e435e5b1c")
        self.assertNotIn("b_runtime.py", SNAPSHOT_HASHES)

    def test_28_proof_is_inside_the_answer_endpoint_and_archive_is_not_in_par2(self):
        def search(request):
            return sat_result(
                request,
                ended_at=1000.5,
                proof_completed_at=1000.4,
                started_at=1000.0,
            )

        ports = Ports(search)
        ports.prepare_delay = 0.0
        ports.sat_delay = 1.5
        ports.archive_delay = 0.25
        ports.decode_fn = lambda request: {"ended_at": request["now"], "action": [[1, 1.0], [1, 1.0], [1, 1.0]]}
        receipt, ports, clock = run(ports=ports)
        self.assertEqual(receipt["answer_timestamp"], 1000.5)
        self.assertLessEqual(receipt["probe"]["result"]["proof_completed_at"], receipt["answer_timestamp"])
        self.assertEqual(receipt["par2"], 0.5)
        self.assertEqual(receipt["resource"]["answer_wall_seconds"], 0.5)
        self.assertEqual(receipt["resource"]["certification_inclusive_wall_seconds"], 2.0)
        self.assertEqual(receipt["resource"]["archive_wall_seconds"], 0.25)
        self.assertEqual(receipt["resource"]["elapsed_wall_seconds"], 2.25)
        self.assertEqual(clock.now(), 1002.25)
        self.assertIn("archive", receipt["resource"]["excluded_from_par2"])
        self.assertIn("certification", receipt["resource"]["excluded_from_par2"])
        assert_audited(self, receipt)

        def late_proof(request):
            return sat_result(request, ended_at=request["now"] + 0.3, proof_completed_at=request["now"] + 0.4)

        receipt, _ports, _clock = run(search=late_proof)
        self.assertEqual(receipt["status"], "invalid")
        self.assertEqual(receipt["terminal_reason"], "proof_after_answer_endpoint")

        ports = Ports(sat_result)
        ports.archive_ok = False
        receipt, _ports, _clock = run(ports=ports)
        self.assertEqual(receipt["status"], "invalid")
        self.assertEqual(receipt["terminal_reason"], "archive_roundtrip_failed")
        self.assertIsNone(receipt["par2"])

    def test_29_launch_admission_and_candidate_equality_are_different(self):
        self.assertFalse(new_work_allowed(60.0, 60.0))
        self.assertTrue(new_work_allowed(59.999, 60.0))
        self.assertTrue(candidate_timely(60.0, 60.0))
        self.assertFalse(candidate_timely(60.0 + 1e-9, 60.0))
        receipt, _ports, _clock = run(ports=Boom(), clock=ManualClock(60.0), t0=0.0)
        self.assertEqual(receipt["encoder_calls"], 0)
        self.assertEqual(receipt["status"], "timeout")
        solved, ports, _clock = run("fixed_direct", lambda request: sat_result(request, ended_at=1060.0))
        self.assertEqual(solved["answer_timestamp"], 1060.0)
        self.assertEqual(len(ports.search_calls), 1)
        assert_audited(self, solved)

    def test_30_historical_fixture_bytes_stay_put(self):
        before = _tree_hashes(CELLS)
        stored = json.loads(MANIFEST.read_text())
        self.assertEqual(before, stored)
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / "cells"
            shutil.copytree(CELLS, copied)
            for folder in copied.iterdir():
                action = json.loads((folder / "action.json").read_text())
                result = json.loads((folder / "result.json").read_text())
                observation = json.loads((folder / "observation.json").read_text())
                stdout = (folder / "probe_stage" / "probe.stdout").read_text()
                self.assertTrue(assess_legacy_balanced_cell(action, result, observation, stdout)["rejected"])
        self.assertEqual(_tree_hashes(CELLS), before)
        self.assertEqual(_tree_hashes(CELLS), stored)
        root = Path(__file__).resolve().parents[2]
        names = {"f_runner.py", "f_runtime.py", "f_audit.py", "b_runtime.py", "feedback_protocol.py"}
        found = []
        for dirpath, dirnames, filenames in os_walk_without_data(root):
            for filename in filenames:
                if filename in names:
                    found.append(str(Path(dirpath) / filename))
        self.assertEqual(found, [])


def os_walk_without_data(root: Path):
    import os

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in {".git", "data", "__pycache__"}]
        yield dirpath, dirnames, filenames


def _tree_hashes(root: Path) -> dict[str, str]:
    hashes = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _matrix() -> list[dict]:
    main = [(300, f"n300-{index}") for index in range(64)] + [(350, f"n350-{index}") for index in range(128)]
    repeats = main[:4] + main[64:72]
    smoke = [(300, "smoke300-0"), (300, "smoke300-1"), (350, "smoke350-0"), (350, "smoke350-1")]
    rows = []
    for size, source in main:
        for arm in ARMS:
            rows.append(_row(size, source, arm, 0, "formal"))
    for size, source in repeats:
        for arm in ARMS:
            rows.append(_row(size, source, arm, 1, "formal"))
    for size, source in smoke:
        for arm in ARMS:
            rows.append(_row(size, source, arm, 0, "smoke"))
    return rows


def _row(size: int, source: str, arm: str, repeat: int, split: str) -> dict:
    return {
        "n": size,
        "source_id": source,
        "arm": arm,
        "repeat": repeat,
        "split": split,
        "selection_seed": 20261118,
    }


class ContractConstantTests(unittest.TestCase):
    def test_package_does_not_import_torch_or_subprocess(self):
        source_root = Path(__file__).resolve().parents[1] / "src" / "feedback_restart_control_v1"
        text = "\n".join(path.read_text() for path in source_root.glob("*.py"))
        self.assertNotIn("import torch", text)
        self.assertNotIn("import subprocess", text)
        self.assertNotIn("safe_log1p_stat", text)
        self.assertTrue(math.isclose(math.log1p(3), FROZEN_ZBAR[350][0]) is False)


if __name__ == "__main__":
    unittest.main()
