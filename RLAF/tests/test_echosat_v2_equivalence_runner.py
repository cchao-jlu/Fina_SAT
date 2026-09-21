from __future__ import annotations

import json
import fcntl
import os
import subprocess
import threading
from pathlib import Path

import pandas as pd
import pytest

import run_echosat_v2_weighted_equivalence as runner
from src.echosat.equivalence import audit_plain_neutral_equivalence


ROOT = Path(__file__).resolve().parents[1]


def write_cnf(path: Path, body: str = "p cnf 1 1\n1 0\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def write_manifest(path: Path, cnf_path: Path | str) -> Path:
    pd.DataFrame(
        [
            {
                "base_instance_id": "tiny_base",
                "variant": "base",
                "family": "tiny",
                "cnf_path": str(cnf_path),
                "extra_metadata": "kept",
            }
        ]
    ).to_csv(path, index=False)
    return path


def fake_solver_stdout(result: str = "SATISFIABLE") -> str:
    return "\n".join(
        [
            "c restarts              : 1",
            "c conflicts             : 2",
            "c decisions             : 3",
            "c propagations          : 4",
            "c CPU time              : 0.01 s",
            f"s {result}",
            "",
        ]
    )


@pytest.fixture
def fake_binaries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    plain = tmp_path / "plain_solver"
    weighted = tmp_path / "weighted_solver"
    plain.write_bytes(b"plain-binary")
    weighted.write_bytes(b"weighted-binary")
    monkeypatch.setattr(runner, "PLAIN_SOLVER", plain)
    monkeypatch.setattr(runner, "WEIGHTED_SOLVER", weighted)
    return plain, weighted


def run_args(manifest: Path, output: Path, *extra: str) -> list[str]:
    return [
        "--manifest",
        str(manifest),
        "--output",
        str(output),
        "--budget-type",
        "conflicts",
        "--budget-value",
        "20",
        "--repeats",
        "0",
        *extra,
    ]


@pytest.mark.parametrize(
    ("budget_type", "budget_flag"),
    [("conflicts", "-conf-lim=37"), ("cpu", "-cpu-lim=37")],
)
def test_plain_and_weighted_argv_match_protocol_flags(
    budget_type: str, budget_flag: str
) -> None:
    plain = runner.build_solver_argv(
        runner.PLAIN_SOLVER,
        seed=8,
        rnd_freq=0.0,
        K=0.1,
        budget_type=budget_type,
        budget_value=37,
    )
    weighted = runner.build_solver_argv(
        runner.WEIGHTED_SOLVER,
        seed=8,
        rnd_freq=0.0,
        K=0.1,
        budget_type=budget_type,
        budget_value=37,
    )

    assert plain[1:] == weighted[1:]
    assert plain[1:] == ["-rnd-seed=8", "-rnd-freq=0.0", "-K=0.1", budget_flag]
    assert "-no-pre" not in plain


def test_resolves_legacy_my_rlaf_path_relative_to_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cnf = write_cnf(tmp_path / "data" / "tiny.cnf")
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    legacy = "/home/old/user/my_rlaf/data/tiny.cnf"
    assert runner.resolve_manifest_cnf_path(legacy) == cnf.resolve()


def test_one_tiny_manifest_runs_exactly_two_model_free_rows(
    tmp_path: Path,
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"

    assert runner.main(run_args(manifest, output)) == 0

    rows = pd.read_csv(output)
    assert rows["method"].tolist() == [
        "plain_unguided_glucose",
        "neutral_weighted_glucose",
    ]
    assert rows["final_result"].tolist() == ["SATISFIABLE", "SATISFIABLE"]
    assert rows["final_solved"].tolist() == [True, True]
    assert rows["solver_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert rows["cnf_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert rows["input_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert rows["manifest_identity_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert rows["manifest_identity_sha256"].nunique() == 1
    assert rows["seed"].tolist() == [1, 1]
    assert rows["final_seed"].tolist() == [1, 1]
    assert rows["extra_metadata"].tolist() == ["kept", "kept"]
    assert not any("model" in arg.lower() or "checkpoint" in arg.lower() for value in rows["argv_json"] for arg in json.loads(value))
    assert set(runner.RESULT_COLUMNS).issubset(rows.columns)


def test_repeat_id_increments_seed_and_preserves_matching_argv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    calls: list[tuple[list[str], str]] = []

    def completed(argv, **kwargs):
        calls.append((argv, kwargs["input"]))
        return subprocess.CompletedProcess(argv, 10, fake_solver_stdout(), "")

    monkeypatch.setattr(runner.subprocess, "run", completed)
    args = run_args(manifest, output, "--seed", "5")
    args[args.index("0")] = "3"
    assert runner.main(args) == 0

    rows = pd.read_csv(output)
    assert rows["seed"].tolist() == [8, 8]
    assert calls[0][0][1:] == calls[1][0][1:]
    assert calls[0][1] == cnf.read_text(encoding="utf-8")
    assert "c weight -1.0000" in calls[1][1]


def test_external_timeout_preserves_partial_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            args[0], kwargs["timeout"], output="c conflicts : 7\nc decisions : 9\n"
        )

    monkeypatch.setattr(runner.subprocess, "run", timeout)

    assert runner.main(run_args(manifest, output, "--external-timeout", "0.01")) == 0
    rows = pd.read_csv(output)
    assert len(rows) == 2
    assert rows["external_timeout"].tolist() == [True, True]
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["final_conflicts"].tolist() == [7, 7]
    assert rows["final_decisions"].tolist() == [9, 9]
    assert rows["final_solver_returncode"].tolist() == [-9, -9]
    assert rows["solver_stdout"].str.contains("conflicts : 7").all()


def test_timeout_checkpoint_rows_resume_without_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(runner, "CHECKPOINT_PAIRS", 1)

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(
            argv,
            kwargs["timeout"],
            output="c conflicts : 7\nc decisions : 9\n",
            stderr="partial timeout stderr",
        )

    monkeypatch.setattr(runner.subprocess, "run", timeout)
    assert runner.main(run_args(manifest, output, "--external-timeout", "0.01")) == 0
    rows = pd.read_csv(output)
    assert rows["external_timeout"].tolist() == [True, True]
    assert rows["execution_error"].tolist() == [False, False]
    assert rows["outcome_error"].str.contains("external_timeout").all()
    assert not bool(audit_plain_neutral_equivalence(rows).iloc[0]["accepted"])

    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("timeout checkpoint rows reran"),
    )
    assert runner.main(run_args(manifest, output, "--external-timeout", "0.01")) == 0


@pytest.mark.parametrize("failure_mode", ["oserror", "incomplete_output"])
def test_self_produced_execution_error_rows_resume_without_rerun(
    failure_mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"

    def failed(argv, **kwargs):
        if failure_mode == "oserror":
            raise OSError("cannot execute solver")
        return subprocess.CompletedProcess(
            argv, 0, fake_solver_stdout().replace("s SATISFIABLE\n", ""), ""
        )

    monkeypatch.setattr(runner.subprocess, "run", failed)
    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["execution_error"].tolist() == [True, True]
    assert rows["outcome_error"].astype(str).str.len().gt(0).all()
    assert not bool(audit_plain_neutral_equivalence(rows).iloc[0]["accepted"])

    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("execution-error rows reran"),
    )
    assert runner.main(run_args(manifest, output)) == 0


def test_non_timeout_negative_nine_execution_error_resumes_without_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(runner, "CHECKPOINT_PAIRS", 1)
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, -9, "c conflicts : 4\n", "terminated by signal"
        ),
    )

    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["external_timeout"].tolist() == [False, False]
    assert rows["execution_error"].tolist() == [True, True]
    assert rows["final_solver_returncode"].tolist() == [-9, -9]
    assert rows["outcome_error"].str.contains("result_returncode_mismatch").all()

    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("rc=-9 execution-error rows reran"),
    )
    assert runner.main(run_args(manifest, output)) == 0


def test_complete_indeterminate_budget_cutoff_resumes_without_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(runner, "CHECKPOINT_PAIRS", 1)
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, fake_solver_stdout("INDETERMINATE"), ""
        ),
    )

    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["external_timeout"].tolist() == [False, False]
    assert rows["execution_error"].tolist() == [False, False]
    assert rows["outcome_error"].fillna("").tolist() == ["", ""]
    assert rows["final_solver_returncode"].tolist() == [0, 0]
    assert rows["final_decisions"].tolist() == [3, 3]
    assert rows["final_conflicts"].tolist() == [2, 2]
    assert rows["final_propagations"].tolist() == [4, 4]
    assert rows["final_restarts"].tolist() == [1, 1]
    assert rows["final_cpu_time"].tolist() == [0.01, 0.01]

    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("valid budget-cutoff rows reran"),
    )
    assert runner.main(run_args(manifest, output)) == 0


@pytest.mark.parametrize("malformation", ["nonzero_returncode", "missing_stats"])
def test_invalid_indeterminate_outcomes_remain_execution_errors(
    malformation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    stdout = fake_solver_stdout("INDETERMINATE")
    returncode = 3
    if malformation == "missing_stats":
        returncode = 0
        stdout = "\n".join(
            line for line in stdout.splitlines() if "CPU time" not in line
        ) + "\n"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, returncode, stdout, ""
        ),
    )

    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["execution_error"].tolist() == [True, True]
    assert rows["outcome_error"].astype(str).str.len().gt(0).all()

    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("invalid INDETERMINATE rows reran"),
    )
    assert runner.main(run_args(manifest, output)) == 0


@pytest.mark.parametrize(
    ("parsed_result", "returncode"),
    [("SATISFIABLE", 20), ("UNSATISFIABLE", 10), ("SATISFIABLE", 3)],
)
def test_contradictory_solver_outcomes_are_canonicalized_to_execution_error(
    parsed_result: str,
    returncode: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, returncode, fake_solver_stdout(parsed_result), ""
        ),
    )

    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["execution_error"].tolist() == [True, True]
    assert rows["outcome_error"].str.contains("result_returncode_mismatch").all()
    assert not bool(audit_plain_neutral_equivalence(rows).iloc[0]["accepted"])


@pytest.mark.parametrize(
    ("result", "returncode", "missing_stat"),
    [
        ("SATISFIABLE", 10, "decisions"),
        ("SATISFIABLE", 10, "CPU time"),
        ("UNSATISFIABLE", 20, "conflicts"),
        ("UNSATISFIABLE", 20, "CPU time"),
    ],
)
def test_solved_result_with_incomplete_required_stats_becomes_resumable_error(
    result: str,
    returncode: int,
    missing_stat: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    stdout = "\n".join(
        line
        for line in fake_solver_stdout(result).splitlines()
        if missing_stat not in line
    ) + "\n"
    monkeypatch.setattr(runner, "CHECKPOINT_PAIRS", 1)
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, returncode, stdout, ""
        ),
    )

    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["execution_error"].tolist() == [True, True]
    assert rows["external_timeout"].tolist() == [False, False]
    assert rows["final_solver_returncode"].tolist() == [returncode, returncode]
    assert rows["outcome_error"].str.contains("required_stats").all()
    assert rows["solver_stdout"].str.contains(f"s {result}").all()
    assert not bool(audit_plain_neutral_equivalence(rows).iloc[0]["accepted"])

    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("incomplete solved-result rows reran"),
    )
    assert runner.main(run_args(manifest, output)) == 0


def test_timeout_overrides_partial_solved_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: (_ for _ in ()).throw(
            subprocess.TimeoutExpired(
                argv, kwargs["timeout"], output=fake_solver_stdout("SATISFIABLE")
            )
        ),
    )

    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["external_timeout"].tolist() == [True, True]


def test_invalid_solver_output_is_recorded_as_indeterminate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 3, "c conflicts : 1\n", "PARSE ERROR"
        ),
    )

    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["final_result"].tolist() == ["INDETERMINATE", "INDETERMINATE"]
    assert rows["final_solved"].tolist() == [False, False]
    assert rows["final_solver_returncode"].tolist() == [3, 3]
    assert rows["solver_stderr"].tolist() == ["PARSE ERROR", "PARSE ERROR"]


def test_resume_skips_complete_pairs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    calls = 0

    def completed(*args, **kwargs):
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(args[0], 10, fake_solver_stdout(), "")

    monkeypatch.setattr(runner.subprocess, "run", completed)
    assert runner.main(run_args(manifest, output)) == 0
    assert calls == 2

    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("completed pair reran"),
    )
    assert runner.main(run_args(manifest, output)) == 0


@pytest.mark.parametrize(
    "mismatch", ["budget", "binary", "cnf", "provenance", "manifest_metadata"]
)
def test_resume_rejects_provenance_mismatch(
    mismatch: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 10, fake_solver_stdout(), ""
        ),
    )
    assert runner.main(run_args(manifest, output)) == 0

    args = run_args(manifest, output)
    if mismatch == "budget":
        args[args.index("20")] = "21"
    elif mismatch == "binary":
        fake_binaries[0].write_bytes(b"changed-plain-binary")
    elif mismatch == "cnf":
        cnf.write_text("p cnf 1 1\n-1 0\n", encoding="utf-8")
    else:
        rows = pd.read_csv(output)
        column = "argv_json" if mismatch == "provenance" else "family"
        rows.loc[0, column] = "[]" if mismatch == "provenance" else "changed"
        rows.to_csv(output, index=False)

    expected_error = "manifest identity" if mismatch == "cnf" else "resume provenance mismatch"
    with pytest.raises(runner.ResumeValidationError, match=expected_error):
        runner.main(args)


@pytest.mark.parametrize("corruption", ["duplicate", "incomplete", "incomplete_row"])
def test_resume_rejects_duplicate_or_incomplete_pairs(
    corruption: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 10, fake_solver_stdout(), ""
        ),
    )
    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    if corruption == "duplicate":
        rows = pd.concat([rows, rows.iloc[[0]]], ignore_index=True)
    elif corruption == "incomplete":
        rows = rows.iloc[[0]]
    else:
        rows.loc[0, "final_result"] = ""
    rows.to_csv(output, index=False)

    expected_error = {
        "duplicate": "duplicate",
        "incomplete": "incomplete",
        "incomplete_row": "invalid existing row",
    }[corruption]
    with pytest.raises(runner.ResumeValidationError, match=expected_error):
        runner.main(run_args(manifest, output))


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("final_result", "UNKNOWN"),
        ("final_solved", False),
        ("final_cpu_time", float("inf")),
        ("final_wall_time", -0.01),
        ("final_decisions", ""),
        ("final_conflicts", 1.5),
        ("final_propagations", -1),
        ("final_restarts", float("nan")),
    ],
)
def test_resume_rejects_malformed_completed_stats(
    column: str,
    value: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 10, fake_solver_stdout(), ""
        ),
    )
    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    rows[column] = rows[column].astype(object)
    rows.loc[0, column] = value
    rows.to_csv(output, index=False)

    with pytest.raises(runner.ResumeValidationError, match="invalid existing row"):
        runner.main(run_args(manifest, output))


@pytest.mark.parametrize(
    ("result", "solved", "returncode", "timed_out"),
    [
        ("SATISFIABLE", True, 20, False),
        ("UNSATISFIABLE", True, 10, False),
        ("INDETERMINATE", False, 10, False),
        ("SATISFIABLE", True, -9, True),
        ("INDETERMINATE", False, 3, True),
    ],
)
def test_resume_rejects_inconsistent_result_returncode_timeout(
    result: str,
    solved: bool,
    returncode: int,
    timed_out: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 10, fake_solver_stdout(), ""
        ),
    )
    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    rows.loc[0, [
        "final_result",
        "final_solved",
        "final_solver_returncode",
        "external_timeout",
    ]] = [result, solved, returncode, timed_out]
    rows.to_csv(output, index=False)

    with pytest.raises(runner.ResumeValidationError, match="invalid existing row"):
        runner.main(run_args(manifest, output))


@pytest.mark.parametrize("mutation", ["expanded", "reduced", "metadata", "path"])
def test_resume_rejects_changed_source_manifest_identity(
    mutation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    first_cnf = write_cnf(tmp_path / "first.cnf")
    second_cnf = write_cnf(tmp_path / "second.cnf", "p cnf 1 1\n-1 0\n")
    source_rows = [
        {
            "base_instance_id": "first",
            "variant": "base",
            "family": "tiny",
            "cnf_path": str(first_cnf),
            "extra_metadata": "original",
        }
    ]
    if mutation == "reduced":
        source_rows.append(
            {
                "base_instance_id": "second",
                "variant": "base",
                "family": "tiny",
                "cnf_path": str(second_cnf),
                "extra_metadata": "original",
            }
        )
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(source_rows).to_csv(manifest, index=False)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 10, fake_solver_stdout(), ""
        ),
    )
    assert runner.main(run_args(manifest, output)) == 0

    changed = list(source_rows)
    if mutation == "expanded":
        changed.append(
            {
                "base_instance_id": "second",
                "variant": "base",
                "family": "tiny",
                "cnf_path": str(second_cnf),
                "extra_metadata": "original",
            }
        )
    elif mutation == "reduced":
        changed = changed[:1]
    elif mutation == "metadata":
        changed[0] = {**changed[0], "extra_metadata": "changed"}
    else:
        changed[0] = {**changed[0], "cnf_path": str(second_cnf)}
    pd.DataFrame(changed).to_csv(manifest, index=False)

    with pytest.raises(runner.ResumeValidationError, match="manifest identity"):
        runner.main(run_args(manifest, output))


def test_manifest_identity_is_order_independent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    first_cnf = write_cnf(tmp_path / "first.cnf")
    second_cnf = write_cnf(tmp_path / "second.cnf", "p cnf 1 1\n-1 0\n")
    rows = [
        {
            "base_instance_id": "first",
            "variant": "base",
            "family": "tiny",
            "cnf_path": str(first_cnf),
        },
        {
            "base_instance_id": "second",
            "variant": "base",
            "family": "tiny",
            "cnf_path": str(second_cnf),
        },
    ]
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(rows).to_csv(manifest, index=False)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 10, fake_solver_stdout(), ""
        ),
    )
    assert runner.main(run_args(manifest, output)) == 0
    identity = pd.read_csv(output)["manifest_identity_sha256"].iloc[0]
    pd.DataFrame(list(reversed(rows))).to_csv(manifest, index=False)
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("reordered manifest reran completed pairs"),
    )

    assert runner.main(run_args(manifest, output)) == 0
    assert pd.read_csv(output)["manifest_identity_sha256"].eq(identity).all()


def test_checkpoints_after_every_25_completed_pairs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    manifest_rows = []
    for index in range(26):
        cnf = write_cnf(tmp_path / f"tiny-{index}.cnf")
        manifest_rows.append(
            {
                "base_instance_id": f"tiny-{index}",
                "variant": "base",
                "family": "tiny",
                "cnf_path": str(cnf),
            }
        )
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(manifest_rows).to_csv(manifest, index=False)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 10, fake_solver_stdout(), ""
        ),
    )
    writes = 0
    real_write = runner._atomic_write_csv

    def counted_write(*args, **kwargs):
        nonlocal writes
        writes += 1
        return real_write(*args, **kwargs)

    monkeypatch.setattr(runner, "_atomic_write_csv", counted_write)
    assert runner.main(run_args(manifest, output)) == 0
    assert writes == 2
    assert len(pd.read_csv(output)) == 52


def test_out_of_order_completion_checkpoints_25_finished_pairs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    manifest_rows = []
    for index in range(26):
        cnf = write_cnf(tmp_path / f"tiny-{index}.cnf")
        manifest_rows.append(
            {
                "base_instance_id": f"tiny-{index}",
                "variant": "base",
                "family": "tiny",
                "cnf_path": str(cnf),
            }
        )
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(manifest_rows).to_csv(manifest, index=False)
    output = tmp_path / "results.csv"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 10, fake_solver_stdout(), ""
        ),
    )
    first_release = threading.Event()
    checkpoint_written = threading.Event()
    real_run_pair = runner._run_pair
    real_atomic_write = runner._atomic_write_csv
    checkpoint_sizes: list[int] = []

    def delayed_run_pair(spec, *args, **kwargs):
        if spec.manifest_index == 0:
            assert first_release.wait(5)
        return real_run_pair(spec, *args, **kwargs)

    def observed_write(path, rows, columns):
        checkpoint_sizes.append(len(rows))
        real_atomic_write(path, rows, columns)
        if len(rows) == 50:
            checkpoint_written.set()

    monkeypatch.setattr(runner, "_run_pair", delayed_run_pair)
    monkeypatch.setattr(runner, "_atomic_write_csv", observed_write)
    errors: list[BaseException] = []

    def invoke() -> None:
        try:
            runner.main(run_args(manifest, output, "--workers", "26"))
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=invoke)
    thread.start()
    try:
        assert checkpoint_written.wait(3), "checkpoint waited for the first submitted pair"
    finally:
        first_release.set()
        thread.join(5)

    assert not errors
    assert not thread.is_alive()
    assert checkpoint_sizes[0] == 50
    rows = pd.read_csv(output)
    assert len(rows) == 52
    assert rows[["repeat_id", "base_instance_id", "variant", "method"]].to_dict("records") == sorted(
        rows[["repeat_id", "base_instance_id", "variant", "method"]].to_dict("records"),
        key=lambda row: (
            int(row["base_instance_id"].split("-")[1]),
            0 if row["method"] == runner.PLAIN_METHOD else 1,
        ),
    )


def test_output_lock_rejects_concurrent_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    lock_path = runner.output_lock_path(output)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(runner.OutputLockError, match="another writer"):
            runner.main(run_args(manifest, output))


def test_duplicate_manifest_pair_keys_report_source_rows_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(
        [
            {
                "base_instance_id": "duplicate",
                "variant": "base",
                "cnf_path": str(cnf),
            },
            {
                "base_instance_id": "duplicate",
                "variant": "base",
                "cnf_path": str(cnf),
            },
        ]
    ).to_csv(manifest, index=False)
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("solver executed for duplicate manifest"),
    )

    with pytest.raises(ValueError, match=r"duplicate.*rows 2, 3"):
        runner.main(run_args(manifest, tmp_path / "results.csv"))


def test_relative_cnf_path_prefers_manifest_directory_then_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    manifest_dir = tmp_path / "manifests"
    manifest_local = write_cnf(manifest_dir / "data" / "tiny.cnf")
    repo_local = write_cnf(repo_root / "repo-data" / "tiny.cnf")
    monkeypatch.setattr(runner, "ROOT", repo_root)

    assert runner.resolve_manifest_cnf_path(
        "data/tiny.cnf", manifest_dir=manifest_dir
    ) == manifest_local.resolve()
    assert runner.resolve_manifest_cnf_path(
        "repo-data/tiny.cnf", manifest_dir=manifest_dir
    ) == repo_local.resolve()


def test_solver_stats_use_integer_counters_and_float_cpu() -> None:
    stats = runner._parse_solver_stdout(fake_solver_stdout())

    assert isinstance(stats["final_decisions"], int)
    assert isinstance(stats["final_conflicts"], int)
    assert isinstance(stats["final_propagations"], int)
    assert isinstance(stats["final_restarts"], int)
    assert isinstance(stats["final_cpu_time"], float)


def test_solver_output_excerpts_are_bounded_with_full_byte_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_binaries: tuple[Path, Path],
) -> None:
    cnf = write_cnf(tmp_path / "tiny.cnf")
    manifest = write_manifest(tmp_path / "manifest.csv", cnf)
    output = tmp_path / "results.csv"
    stdout = fake_solver_stdout() + ("x" * (runner.MAX_STREAM_EXCERPT_BYTES * 2))
    stderr = "y" * (runner.MAX_STREAM_EXCERPT_BYTES * 2)
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(argv, 10, stdout, stderr),
    )

    assert runner.main(run_args(manifest, output)) == 0
    rows = pd.read_csv(output)
    assert rows["solver_stdout_bytes"].eq(len(stdout.encode())).all()
    assert rows["solver_stderr_bytes"].eq(len(stderr.encode())).all()
    assert rows["solver_stdout_truncated"].tolist() == [True, True]
    assert rows["solver_stderr_truncated"].tolist() == [True, True]
    assert rows["solver_stdout"].str.encode("utf-8").str.len().le(runner.MAX_STREAM_EXCERPT_BYTES).all()
    assert rows["solver_stderr"].str.encode("utf-8").str.len().le(runner.MAX_STREAM_EXCERPT_BYTES).all()


def test_atomic_write_fsyncs_parent_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "results.csv"
    opened_paths: list[Path] = []
    fsynced: list[int] = []
    real_open = runner.os.open
    real_fsync = runner.os.fsync

    def observed_open(path, flags, *args):
        opened_paths.append(Path(path))
        return real_open(path, flags, *args)

    def observed_fsync(descriptor):
        fsynced.append(descriptor)
        return real_fsync(descriptor)

    monkeypatch.setattr(runner.os, "open", observed_open)
    monkeypatch.setattr(runner.os, "fsync", observed_fsync)
    runner._atomic_write_csv(output, [], [])

    assert output.parent in opened_paths
    assert len(fsynced) >= 2


@pytest.mark.parametrize(
    "argv",
    [
        ["--output", "x.csv", "--budget-type", "conflicts", "--budget-value", "0", "--repeats", "0"],
        ["--output", "x.csv", "--budget-type", "cpu", "--budget-value", "1", "--repeats"],
        ["--output", "x.csv", "--budget-type", "cpu", "--budget-value", "1", "--repeats", "-1"],
        ["--output", "x.csv", "--budget-type", "cpu", "--budget-value", "1", "--repeats", "0", "--workers", "0"],
        ["--output", "x.csv", "--budget-type", "cpu", "--budget-value", "1", "--repeats", "0", "--external-timeout", "0"],
        ["--output", "x.csv", "--budget-type", "cpu", "--budget-value", "1", "--repeats", "0", "0"],
        ["--output", "x.csv", "--budget-type", "wat", "--budget-value", "1", "--repeats", "0"],
    ],
)
def test_cli_argument_validation(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        runner.parse_args(argv)


@pytest.mark.parametrize("value", ["0", "1", "-0.1", "1.1", "nan", "inf", "-inf"])
def test_cli_rejects_invalid_K_boundaries(value: str) -> None:
    argv = [
        "--output",
        "x.csv",
        "--budget-type",
        "conflicts",
        "--budget-value",
        "1",
        "--repeats",
        "0",
        "--K",
        value,
    ]
    with pytest.raises(SystemExit):
        runner.parse_args(argv)


@pytest.mark.parametrize(
    "value", [0.0, 1.0, -0.1, 1.1, float("nan"), float("inf"), float("-inf")]
)
def test_build_solver_argv_rejects_invalid_K(value: float) -> None:
    with pytest.raises(ValueError, match="K"):
        runner.build_solver_argv(
            runner.PLAIN_SOLVER,
            seed=1,
            rnd_freq=0.0,
            K=value,
            budget_type="conflicts",
            budget_value=1,
        )
