import sys
import subprocess
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from omegaconf import OmegaConf
from torch_geometric.data import HeteroData

from run_symmetry_solver_protocol_preflight import (
    graph_var_params,
    neutral_weighted_graphs,
    parse_args,
)
from src.solving.solver import cnf_to_dimacs, neutral_var_params
from src.echosat.equivalence import (
    EquivalenceInputError,
    audit_plain_neutral_equivalence,
    build_expected_pair_ids,
    build_pair_id,
    render_equivalence_markdown,
)
from train_rlaf import build_speedup_baseline_data_list


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAIN_SOLVER = REPO_ROOT / "solvers/glucose/simp/glucose_release"
WEIGHTED_SOLVER = REPO_ROOT / "solvers/glucose_weighted/simp/glucose_release"
AUDIT_SCRIPT = "audit_echosat_v2_weighted_equivalence.py"
TRAJECTORY_FIELDS = ("decisions", "conflicts", "propagations", "restarts")


def make_preflight_rows() -> pd.DataFrame:
    common = {
        "repeat_id": 0,
        "base_instance_id": "php_p4_h3",
        "variant": "base",
    }
    return pd.DataFrame(
        [
            {
                **common,
                "method": "plain_unguided_glucose",
                "final_result": "UNSATISFIABLE",
                "final_solved": True,
                "final_decisions": 10.0,
                "final_conflicts": 7.0,
                "final_cpu_time": 0.01,
            },
            {
                **common,
                "method": "neutral_weighted_glucose",
                "final_result": "UNSATISFIABLE",
                "final_solved": True,
                "final_decisions": 10.0,
                "final_conflicts": 7.0,
                "final_cpu_time": 0.25,
            },
            {
                **common,
                "method": "static_weighted_glucose",
                "final_result": "UNSATISFIABLE",
                "final_solved": True,
                "final_decisions": 9.0,
                "final_conflicts": 6.0,
                "final_cpu_time": 0.02,
            },
        ]
    )


def make_indeterminate_preflight_rows() -> pd.DataFrame:
    frame = make_preflight_rows()
    compared = frame["method"].isin(
        ["plain_unguided_glucose", "neutral_weighted_glucose"]
    )
    frame.loc[compared, "final_result"] = "INDETERMINATE"
    frame.loc[compared, "final_solved"] = False
    frame.loc[
        frame["method"] == "neutral_weighted_glucose", "final_decisions"
    ] = 11.0
    frame.loc[
        frame["method"] == "neutral_weighted_glucose", "final_conflicts"
    ] = 8.0
    return frame


def make_graph(num_vars: int = 3) -> HeteroData:
    graph = HeteroData()
    graph["var"].num_nodes = num_vars
    graph["lit"].num_nodes = num_vars * 2
    return graph


def write_expected_manifest(path: Path) -> None:
    pd.DataFrame(
        [{"base_instance_id": "php_p4_h3", "variant": "base"}]
    ).to_csv(path, index=False)


def assert_neutral_params(var_params: np.ndarray) -> None:
    np.testing.assert_array_equal(var_params[:, 0], np.zeros(var_params.shape[0]))
    np.testing.assert_array_equal(var_params[:, 1], np.ones(var_params.shape[0]))


def run_weighted_solver(dimacs: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [WEIGHTED_SOLVER, *args],
        input=dimacs,
        capture_output=True,
        text=True,
        check=False,
    )


def parse_solver_trajectory(output: str) -> tuple[str, dict[str, int]]:
    result = next(line for line in output.splitlines() if line.startswith("s "))
    metrics = {}
    for field in TRAJECTORY_FIELDS:
        match = re.search(rf"^c {field}\s*:\s*(\d+)", output, re.MULTILINE)
        assert match is not None, f"missing {field} in solver output"
        metrics[field] = int(match.group(1))
    return result, metrics


def test_neutral_weight_line_preserves_preprocessed_solver_trajectory() -> None:
    instance = REPO_ROOT / "data/symmetry_stress/complete_coloring/k5_color4.cnf"
    plain_dimacs = instance.read_text()
    header, clauses = plain_dimacs.split("\n", 1)
    num_vars = int(header.split()[2])
    weighted_dimacs = f"{header}\nc weight{' -1' * num_vars}\n{clauses}"

    plain = subprocess.run(
        [PLAIN_SOLVER],
        input=plain_dimacs,
        capture_output=True,
        text=True,
        check=False,
    )
    weighted = run_weighted_solver(weighted_dimacs)

    assert weighted.returncode == plain.returncode
    assert parse_solver_trajectory(weighted.stdout) == parse_solver_trajectory(
        plain.stdout
    )


def test_neutral_var_params_defaults_to_plain_initialization() -> None:
    params = neutral_var_params(3)

    assert params.shape == (3, 2)
    assert_neutral_params(params)


def test_neutral_graph_constructors_use_shared_plain_initialization() -> None:
    graph = make_graph()

    preflight_graph = neutral_weighted_graphs([graph])[0]
    assert_neutral_params(graph_var_params(preflight_graph))

    cfg = OmegaConf.create({"training": {"speedup_baseline": "neutral_weighted"}})
    training_graph = build_speedup_baseline_data_list([graph], cfg)[0]
    assert_neutral_params(graph_var_params(training_graph))


def test_neutral_dimacs_uses_signed_negative_unit_scales() -> None:
    dimacs = cnf_to_dimacs([[1, -2]], var_params=neutral_var_params(2))

    assert "c weight -1.0000 -1.0000" in dimacs


def test_dimacs_preserves_signed_scale_precision() -> None:
    params = np.asarray(
        [
            [1.0, 1.0e-12],
            [-1.0, 1.2345678901234567],
        ],
        dtype=np.float64,
    )

    dimacs = cnf_to_dimacs([[1, 2]], var_params=params)
    signed_scales = dimacs.splitlines()[1].split()[2:]

    assert float(signed_scales[0]) == params[0, 1]
    assert float(signed_scales[1]) == -params[1, 1]
    assert signed_scales[0] != "0.0000"


def test_neutral_phase_cli_default_is_zero(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_symmetry_solver_protocol_preflight.py"])

    assert parse_args().neutral_phase == 0.0


@pytest.mark.parametrize(
    "weight_line",
    [
        "c weight -1 -1",
        "c weight -1 -1 -1 -1",
        "c weight -1 nan -1",
        "c weight -1 inf -1",
    ],
)
def test_weighted_solver_rejects_malformed_weight_lines(weight_line: str) -> None:
    dimacs = f"p cnf 3 1\n{weight_line}\n1 2 3 0\n"

    result = run_weighted_solver(dimacs, "-no-pre")
    output = result.stdout + result.stderr

    assert result.returncode == 3
    assert "PARSE ERROR! c weight" in output
    assert "s SATISFIABLE" not in output


@pytest.mark.parametrize(
    ("signed_scales", "expected_model"),
    [
        ("1 -1", "v 1 -2 0"),
        ("-1 1", "v -1 2 0"),
    ],
)
def test_weighted_solver_maps_signed_scales_to_phases(
    signed_scales: str,
    expected_model: str,
) -> None:
    dimacs = f"p cnf 2 0\nc weight {signed_scales}\n"

    result = run_weighted_solver(dimacs, "-no-pre", "-model")

    assert result.returncode == 10
    assert expected_model in result.stdout


def test_weighted_solver_accepts_tiny_nonzero_scales() -> None:
    params = np.asarray([[1.0, 1.0e-12], [-1.0, 1.0e-12]], dtype=np.float64)
    dimacs = cnf_to_dimacs([[1, -1], [2, -2]], var_params=params)

    result = run_weighted_solver(dimacs, "-no-pre", "-model")

    assert result.returncode == 10
    assert "v 1 -2 0" in result.stdout


def test_weighted_benchmark_comment_remains_an_ordinary_comment() -> None:
    result = run_weighted_solver("p cnf 1 1\nc weighted benchmark comment\n1 0\n")

    assert result.returncode == 10
    assert "s SATISFIABLE" in result.stdout


@pytest.mark.parametrize(
    "dimacs",
    [
        "c weight -1\np cnf 1 0\n",
        "p cnf 1 0\nc weight -1\nc weight -1\n",
        "p cnf 1 1\n1 0\nc weight -1\n",
    ],
)
def test_weighted_solver_rejects_invalid_weight_line_ordering(dimacs: str) -> None:
    result = run_weighted_solver(dimacs)
    output = result.stdout + result.stderr

    assert result.returncode == 3
    assert "PARSE ERROR!" in output


def test_weighted_solver_rejects_literals_outside_declared_range() -> None:
    result = run_weighted_solver("p cnf 1 1\nc weight -1\n1 2 0\n")
    output = result.stdout + result.stderr

    assert result.returncode == 3
    assert "PARSE ERROR!" in output


def test_weighted_solver_rejects_duplicate_problem_headers() -> None:
    result = run_weighted_solver("p cnf 1 0\np cnf 1 0\n")
    output = result.stdout + result.stderr

    assert result.returncode == 3
    assert "PARSE ERROR!" in output


def test_pair_id_uses_repeat_base_and_variant() -> None:
    frame = make_preflight_rows().iloc[:1]

    pair_ids = build_pair_id(frame)

    assert pair_ids.tolist() == ["repeat=0|base=php_p4_h3|variant=base"]


def test_equivalence_accepts_exact_search_metrics_with_cpu_delta() -> None:
    audit = audit_plain_neutral_equivalence(make_preflight_rows())

    assert len(audit) == 1
    row = audit.iloc[0]
    assert bool(row["accepted"])
    assert row["plain_final_result"] == "UNSATISFIABLE"
    assert row["neutral_final_result"] == "UNSATISFIABLE"
    assert bool(row["plain_final_solved"])
    assert bool(row["neutral_final_solved"])
    assert row["final_cpu_time_delta"] == pytest.approx(0.24)
    assert row["rejection_reason"] == ""


@pytest.mark.parametrize(
    ("column", "neutral_value", "reason"),
    [
        ("final_result", "SATISFIABLE", "result_mismatch"),
        ("final_decisions", 11.0, "decisions_mismatch"),
        ("final_conflicts", 8.0, "conflicts_mismatch"),
    ],
)
def test_equivalence_rejects_exact_metric_mismatches(
    column: str,
    neutral_value: object,
    reason: str,
) -> None:
    frame = make_preflight_rows()
    frame.loc[frame["method"] == "neutral_weighted_glucose", column] = neutral_value

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert not bool(row["accepted"])
    assert reason in row["rejection_reason"]


def test_deterministic_gate_rejects_decision_and_conflict_mismatch() -> None:
    frame = make_indeterminate_preflight_rows()

    row = audit_plain_neutral_equivalence(
        frame, gate_mode="deterministic"
    ).iloc[0]

    assert not bool(row["accepted"])
    assert not bool(row["decisions_match"])
    assert not bool(row["conflicts_match"])
    assert "decisions_mismatch" in row["rejection_reason"]
    assert "conflicts_mismatch" in row["rejection_reason"]


def test_cpu_gate_accepts_valid_indeterminate_metric_mismatch_as_diagnostic() -> None:
    row = audit_plain_neutral_equivalence(
        make_indeterminate_preflight_rows(), gate_mode="cpu"
    ).iloc[0]

    assert bool(row["accepted"])
    assert bool(row["result_match"])
    assert bool(row["solved_match"])
    assert not bool(row["decisions_match"])
    assert not bool(row["conflicts_match"])
    assert row["rejection_reason"] == ""


def test_cpu_gate_rejects_plain_solved_to_neutral_unsolved() -> None:
    frame = make_preflight_rows()
    neutral = frame["method"] == "neutral_weighted_glucose"
    frame.loc[neutral, "final_result"] = "INDETERMINATE"
    frame.loc[neutral, "final_solved"] = False

    row = audit_plain_neutral_equivalence(frame, gate_mode="cpu").iloc[0]

    assert not bool(row["accepted"])
    assert "result_mismatch" in row["rejection_reason"]
    assert "solved_mismatch" in row["rejection_reason"]


def test_cpu_gate_rejects_any_result_mismatch() -> None:
    frame = make_preflight_rows()
    frame.loc[
        frame["method"] == "neutral_weighted_glucose", "final_result"
    ] = "SATISFIABLE"

    row = audit_plain_neutral_equivalence(frame, gate_mode="cpu").iloc[0]

    assert not bool(row["accepted"])
    assert bool(row["solved_match"])
    assert "result_mismatch" in row["rejection_reason"]


def test_invalid_gate_mode_is_rejected() -> None:
    with pytest.raises(EquivalenceInputError, match="gate_mode"):
        audit_plain_neutral_equivalence(
            make_preflight_rows(), gate_mode="nondeterministic"
        )


@pytest.mark.parametrize(
    ("gate_mode", "acceptance_rule"),
    [
        (
            "deterministic",
            "exact equality of final result, input final_solved status, decisions, and conflicts",
        ),
        (
            "cpu",
            "exact equality of final result and input final_solved status; decisions and conflicts are diagnostic-only",
        ),
    ],
)
def test_markdown_states_gate_mode_and_acceptance_rule(
    gate_mode: str,
    acceptance_rule: str,
) -> None:
    audit = audit_plain_neutral_equivalence(
        make_preflight_rows(), gate_mode=gate_mode
    )

    report = render_equivalence_markdown(
        audit, "input.csv", gate_mode=gate_mode
    )

    assert f"- Gate mode: `{gate_mode}`" in report
    assert acceptance_rule in report


def test_identical_results_with_different_solved_status_are_rejected() -> None:
    frame = make_preflight_rows()
    frame.loc[frame["method"] == "neutral_weighted_glucose", "final_solved"] = False

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert bool(row["plain_final_solved"])
    assert not bool(row["neutral_final_solved"])
    assert bool(row["result_match"])
    assert "solved_mismatch" in row["rejection_reason"]


def test_solved_status_strings_are_normalized_safely() -> None:
    frame = make_preflight_rows()
    frame["final_solved"] = frame["final_solved"].astype(object)
    frame.loc[frame["method"].isin(
        ["plain_unguided_glucose", "neutral_weighted_glucose"]
    ), "final_result"] = "INDETERMINATE"
    frame.loc[frame["method"] == "plain_unguided_glucose", "final_solved"] = "False"
    frame.loc[frame["method"] == "neutral_weighted_glucose", "final_solved"] = "false"

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert not bool(row["plain_final_solved"])
    assert not bool(row["neutral_final_solved"])
    assert bool(row["solved_match"])
    assert bool(row["accepted"])


@pytest.mark.parametrize("malformation", ["missing_plain", "duplicate_neutral"])
def test_equivalence_rejects_missing_or_duplicate_methods(malformation: str) -> None:
    frame = make_preflight_rows()
    if malformation == "missing_plain":
        frame = frame.loc[frame["method"] != "plain_unguided_glucose"]
        expected_reason = "plain_method_count=0"
    else:
        neutral = frame.loc[frame["method"] == "neutral_weighted_glucose"]
        frame = pd.concat([frame, neutral], ignore_index=True)
        expected_reason = "neutral_method_count=2"

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert not bool(row["accepted"])
    assert expected_reason in row["rejection_reason"]


def test_equivalence_validates_required_columns() -> None:
    frame = make_preflight_rows().drop(columns=["final_conflicts"])

    with pytest.raises(EquivalenceInputError, match="final_conflicts"):
        audit_plain_neutral_equivalence(frame)


def test_equivalence_requires_final_solved_column() -> None:
    frame = make_preflight_rows().drop(columns=["final_solved"])

    with pytest.raises(EquivalenceInputError, match="final_solved"):
        audit_plain_neutral_equivalence(frame)


@pytest.mark.parametrize(
    ("column", "value", "reason"),
    [
        ("final_result", "UNKNOWN", "invalid_final_result"),
        ("final_decisions", 1.5, "invalid_final_decisions"),
        ("final_decisions", -1, "invalid_final_decisions"),
        ("final_conflicts", float("inf"), "invalid_final_conflicts"),
        ("final_cpu_time", -0.1, "invalid_final_cpu_time"),
        ("final_cpu_time", float("nan"), "invalid_final_cpu_time"),
    ],
)
def test_equal_malformed_rows_are_rejected(
    column: str,
    value: object,
    reason: str,
) -> None:
    frame = make_preflight_rows()
    frame.loc[frame["method"].isin(
        ["plain_unguided_glucose", "neutral_weighted_glucose"]
    ), column] = value

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert not bool(row["accepted"])
    assert f"plain_{reason}" in row["rejection_reason"]
    assert f"neutral_{reason}" in row["rejection_reason"]


def test_result_and_solved_inconsistency_is_explicit_rejection() -> None:
    frame = make_preflight_rows()
    frame.loc[frame["method"].isin(
        ["plain_unguided_glucose", "neutral_weighted_glucose"]
    ), "final_solved"] = False

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert not bool(row["accepted"])
    assert "plain_final_solved_inconsistent_with_result" in row["rejection_reason"]
    assert "neutral_final_solved_inconsistent_with_result" in row["rejection_reason"]


def test_invalid_boolean_is_explicit_rejection_not_exception() -> None:
    frame = make_preflight_rows()
    frame["final_solved"] = frame["final_solved"].astype(object)
    frame.loc[frame["method"] == "plain_unguided_glucose", "final_solved"] = "maybe"

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert not bool(row["accepted"])
    assert "plain_invalid_final_solved" in row["rejection_reason"]


def test_huge_boolean_number_is_explicit_rejection_not_overflow() -> None:
    frame = make_preflight_rows()
    frame["final_solved"] = frame["final_solved"].astype(object)
    frame.loc[frame["method"] == "plain_unguided_glucose", "final_solved"] = 10**1000

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert not bool(row["accepted"])
    assert "plain_invalid_final_solved" in row["rejection_reason"]


def test_huge_nonnegative_integer_search_metrics_remain_valid() -> None:
    frame = make_preflight_rows()
    frame["final_decisions"] = frame["final_decisions"].astype(object)
    huge_integer = 10**1000
    frame.loc[frame["method"].isin(
        ["plain_unguided_glucose", "neutral_weighted_glucose"]
    ), "final_decisions"] = huge_integer

    row = audit_plain_neutral_equivalence(frame).iloc[0]

    assert bool(row["accepted"])
    assert row["plain_final_decisions"] == huge_integer
    assert row["neutral_final_decisions"] == huge_integer


def test_expected_pair_ids_cross_manifest_with_repeats() -> None:
    manifest = pd.DataFrame(
        [
            {"base_instance_id": "base-a", "variant": "base"},
            {"base_instance_id": "base-a", "variant": "perm_seed1"},
        ]
    )

    expected = build_expected_pair_ids(manifest, repeats=[0, 2])

    assert expected == [
        "repeat=0|base=base-a|variant=base",
        "repeat=0|base=base-a|variant=perm_seed1",
        "repeat=2|base=base-a|variant=base",
        "repeat=2|base=base-a|variant=perm_seed1",
    ]


def test_missing_expected_pair_is_emitted_as_rejection() -> None:
    expected = [
        "repeat=0|base=php_p4_h3|variant=base",
        "repeat=1|base=php_p4_h3|variant=base",
    ]

    audit = audit_plain_neutral_equivalence(
        make_preflight_rows(), expected_pair_ids=expected
    )

    missing = audit.loc[audit["pair_id"] == expected[1]].iloc[0]
    assert not bool(missing["accepted"])
    assert missing["rejection_reason"] == "missing_pair"
    assert missing["repeat_id"] == 1


def test_explicit_empty_expected_pair_set_is_coverage_rejection() -> None:
    audit = audit_plain_neutral_equivalence(
        make_preflight_rows(), expected_pair_ids=[]
    )

    coverage = audit.loc[audit["pair_id"] == "__coverage__"].iloc[0]
    assert not bool(coverage["accepted"])
    assert coverage["rejection_reason"] == "expected_pair_set_empty"


def test_audit_cli_writes_csv_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "preflight.csv"
    manifest_path = tmp_path / "manifest.csv"
    csv_path = tmp_path / "audit.csv"
    markdown_path = tmp_path / "audit.md"
    make_preflight_rows().to_csv(input_path, index=False)
    write_expected_manifest(manifest_path)

    result = subprocess.run(
        [
            sys.executable,
            AUDIT_SCRIPT,
            "--input",
            str(input_path),
            "--output-csv",
            str(csv_path),
            "--output-markdown",
            str(markdown_path),
            "--expected-manifest",
            str(manifest_path),
            "--expected-repeats",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "FutureWarning" not in result.stderr
    saved = pd.read_csv(csv_path)
    assert saved["accepted"].tolist() == [True]
    assert saved["plain_final_decisions"].tolist() == [10.0]
    assert saved["neutral_final_decisions"].tolist() == [10.0]
    assert "ACCEPT" in markdown_path.read_text(encoding="utf-8")


def test_audit_cli_exits_two_on_any_rejection(tmp_path: Path) -> None:
    input_path = tmp_path / "preflight.csv"
    manifest_path = tmp_path / "manifest.csv"
    csv_path = tmp_path / "audit.csv"
    markdown_path = tmp_path / "audit.md"
    frame = make_preflight_rows()
    frame.loc[frame["method"] == "neutral_weighted_glucose", "final_conflicts"] = 8.0
    frame.to_csv(input_path, index=False)
    write_expected_manifest(manifest_path)

    result = subprocess.run(
        [
            sys.executable,
            AUDIT_SCRIPT,
            "--input",
            str(input_path),
            "--output-csv",
            str(csv_path),
            "--output-markdown",
            str(markdown_path),
            "--expected-manifest",
            str(manifest_path),
            "--expected-repeats",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert pd.read_csv(csv_path)["accepted"].tolist() == [False]
    report = markdown_path.read_text(encoding="utf-8")
    assert "REJECT" in report
    assert "conflicts_mismatch" in report


def test_cli_gate_mode_routes_and_defaults_to_deterministic(tmp_path: Path) -> None:
    input_path = tmp_path / "preflight.csv"
    manifest_path = tmp_path / "manifest.csv"
    make_indeterminate_preflight_rows().to_csv(input_path, index=False)
    write_expected_manifest(manifest_path)

    results = {}
    for gate_mode in (None, "cpu"):
        label = "default" if gate_mode is None else gate_mode
        csv_path = tmp_path / f"{label}.csv"
        markdown_path = tmp_path / f"{label}.md"
        command = [
            sys.executable,
            AUDIT_SCRIPT,
            "--input",
            str(input_path),
            "--output-csv",
            str(csv_path),
            "--output-markdown",
            str(markdown_path),
            "--expected-manifest",
            str(manifest_path),
            "--expected-repeats",
            "0",
        ]
        if gate_mode is not None:
            command.extend(["--gate-mode", gate_mode])
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        results[label] = (
            result,
            pd.read_csv(csv_path),
            markdown_path.read_text(encoding="utf-8"),
        )

    default_result, default_audit, default_report = results["default"]
    assert default_result.returncode == 2
    assert default_audit["accepted"].tolist() == [False]
    assert "- Gate mode: `deterministic`" in default_report

    cpu_result, cpu_audit, cpu_report = results["cpu"]
    assert cpu_result.returncode == 0, cpu_result.stderr
    assert cpu_audit["accepted"].tolist() == [True]
    assert cpu_audit["decisions_match"].tolist() == [False]
    assert cpu_audit["conflicts_match"].tolist() == [False]
    assert "- Gate mode: `cpu`" in cpu_report


def test_cli_reports_missing_manifest_pairs(tmp_path: Path) -> None:
    input_path = tmp_path / "preflight.csv"
    manifest_path = tmp_path / "manifest.csv"
    csv_path = tmp_path / "audit.csv"
    markdown_path = tmp_path / "audit.md"
    make_preflight_rows().to_csv(input_path, index=False)
    write_expected_manifest(manifest_path)

    result = subprocess.run(
        [
            sys.executable,
            AUDIT_SCRIPT,
            "--input",
            str(input_path),
            "--expected-manifest",
            str(manifest_path),
            "--expected-repeats",
            "0",
            "1",
            "--output-csv",
            str(csv_path),
            "--output-markdown",
            str(markdown_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    saved = pd.read_csv(csv_path)
    assert saved.loc[saved["rejection_reason"] == "missing_pair", "pair_id"].tolist() == [
        "repeat=1|base=php_p4_h3|variant=base"
    ]


def test_markdown_paths_are_repo_relative_and_invocation_stable(tmp_path: Path) -> None:
    input_path = tmp_path / "preflight.csv"
    manifest_path = tmp_path / "manifest.csv"
    make_preflight_rows().to_csv(input_path, index=False)
    write_expected_manifest(manifest_path)
    reports = []
    for invocation, input_arg, manifest_arg in [
        ("absolute", str(input_path.resolve()), str(manifest_path.resolve())),
        (
            "relative",
            os.path.relpath(input_path.resolve(), Path.cwd()),
            os.path.relpath(manifest_path.resolve(), Path.cwd()),
        ),
    ]:
        csv_path = tmp_path / f"{invocation}.csv"
        markdown_path = tmp_path / f"{invocation}.md"
        result = subprocess.run(
            [
                sys.executable,
                AUDIT_SCRIPT,
                "--input",
                input_arg,
                "--expected-manifest",
                manifest_arg,
                "--expected-repeats",
                "0",
                "--output-csv",
                str(csv_path),
                "--output-markdown",
                str(markdown_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        reports.append(markdown_path.read_text(encoding="utf-8"))

    assert reports[0] == reports[1]
    input_line = next(line for line in reports[0].splitlines() if line.startswith("- Input:"))
    manifest_line = next(
        line for line in reports[0].splitlines() if line.startswith("- Expected manifest:")
    )
    assert not input_line.split("`", 2)[1].startswith("/")
    assert not manifest_line.split("`", 2)[1].startswith("/")
