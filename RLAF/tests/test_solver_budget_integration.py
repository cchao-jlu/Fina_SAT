import re
import subprocess
import unittest
from pathlib import Path

import numpy as np

from src.solving.solver import cnf_to_dimacs, stdout_to_results_dict


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAIN_GLUCOSE = REPO_ROOT / "solvers/glucose/simp/glucose_release"
WEIGHTED_GLUCOSE = REPO_ROOT / "solvers/glucose_weighted/simp/glucose_release"
NEUTRAL_EQUIVALENCE_FIXTURE = (
    REPO_ROOT / "data/symmetry_stress/complete_coloring/k5_color4.cnf"
)
TRAJECTORY_FIELDS = ("decisions", "conflicts", "propagations", "restarts")
SOLVER_TIMEOUT_SECONDS = 5


def pigeonhole_cnf(pigeons: int, holes: int) -> tuple[list[list[int]], int]:
    clauses: list[list[int]] = []

    def var(pigeon: int, hole: int) -> int:
        return pigeon * holes + hole + 1

    for pigeon in range(pigeons):
        clauses.append([var(pigeon, hole) for hole in range(holes)])

    for hole in range(holes):
        for first in range(pigeons):
            for second in range(first + 1, pigeons):
                clauses.append([-var(first, hole), -var(second, hole)])

    return clauses, pigeons * holes


def neutral_weighted_dimacs(plain_dimacs: str) -> str:
    header, clauses = plain_dimacs.split("\n", 1)
    num_vars = int(header.split()[2])
    return f"{header}\nc weight{' -1' * num_vars}\n{clauses}"


def run_glucose(
    binary: Path,
    dimacs: str,
    conflict_limit: int,
    *extra_args: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            binary,
            f"-conf-lim={conflict_limit}",
            "-rnd-freq=0",
            "-rnd-seed=1",
            *extra_args,
        ],
        input=dimacs,
        capture_output=True,
        text=True,
        check=False,
        timeout=SOLVER_TIMEOUT_SECONDS,
    )


def parse_trajectory(output: str) -> tuple[str, dict[str, int]]:
    result_match = re.search(r"^s (\S+)$", output, re.MULTILINE)
    if result_match is None:
        raise AssertionError(f"missing solver result in output:\n{output}")

    metrics = {}
    for field in TRAJECTORY_FIELDS:
        match = re.search(rf"^c {field}\s*:\s*(\d+)", output, re.MULTILINE)
        if match is None:
            raise AssertionError(f"missing {field} in output:\n{output}")
        metrics[field] = int(match.group(1))
    return result_match.group(1), metrics


class SolverBudgetIntegrationTest(unittest.TestCase):
    def test_plain_and_neutral_weighted_glucose_match_conflict_budget_boundaries(self):
        plain_dimacs = NEUTRAL_EQUIVALENCE_FIXTURE.read_text()
        weighted_dimacs = neutral_weighted_dimacs(plain_dimacs)
        expected_by_budget = {
            0: (0, 0, 0, 1),
            1: (7, 1, 11, 1),
            10: (17, 10, 44, 1),
        }

        for conflict_limit, expected_metrics in expected_by_budget.items():
            with self.subTest(conflict_limit=conflict_limit):
                plain = run_glucose(
                    PLAIN_GLUCOSE, plain_dimacs, conflict_limit
                )
                weighted = run_glucose(
                    WEIGHTED_GLUCOSE, weighted_dimacs, conflict_limit
                )

                self.assertEqual(plain.returncode, 0, plain.stderr)
                self.assertEqual(weighted.returncode, 0, weighted.stderr)
                expected = (
                    "INDETERMINATE",
                    dict(zip(TRAJECTORY_FIELDS, expected_metrics)),
                )
                self.assertEqual(parse_trajectory(plain.stdout), expected)
                self.assertEqual(parse_trajectory(weighted.stdout), expected)

    def test_zero_conflict_budget_interrupts_conflict_free_sat_before_model(self):
        plain_dimacs = "p cnf 2 1\n1 2 0\n"
        weighted_dimacs = neutral_weighted_dimacs(plain_dimacs)
        expected = (
            "INDETERMINATE",
            {
                "decisions": 0,
                "conflicts": 0,
                "propagations": 0,
                "restarts": 1,
            },
        )

        plain = run_glucose(PLAIN_GLUCOSE, plain_dimacs, 0, "-no-pre")
        weighted = run_glucose(
            WEIGHTED_GLUCOSE, weighted_dimacs, 0, "-no-pre"
        )

        self.assertEqual(plain.returncode, 0, plain.stderr)
        self.assertEqual(weighted.returncode, 0, weighted.stderr)
        self.assertEqual(parse_trajectory(plain.stdout), expected)
        self.assertEqual(parse_trajectory(weighted.stdout), expected)

    def test_weighted_glucose_conflict_budget_stops_during_search(self):
        clauses, num_vars = pigeonhole_cnf(pigeons=5, holes=4)
        var_params = np.ones((num_vars, 2), dtype=float)
        result = run_glucose(
            WEIGHTED_GLUCOSE,
            cnf_to_dimacs(clauses, var_params=var_params),
            1,
            "-cpu-lim=5",
            "-K=0.1",
        )
        stats = stdout_to_results_dict(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stats.get("Result"), "INDETERMINATE")
        self.assertLessEqual(stats.get("conflicts", 0), 1)

    def test_weighted_glucose_emits_literal_polarity_events(self):
        clauses = [[1, 2], [-1, 2], [1, -2], [-1, -2]]
        var_params = np.ones((2, 2), dtype=float)
        result = run_glucose(
            WEIGHTED_GLUCOSE,
            cnf_to_dimacs(clauses, var_params=var_params),
            5,
            "-cpu-lim=5",
            "-K=0.1",
            "-collect-events",
        )
        stats = stdout_to_results_dict(result.stdout)

        self.assertEqual(result.returncode, 20, result.stderr)
        for key in [
            "event_var_pos_decisions",
            "event_var_neg_decisions",
            "event_var_pos_propagations",
            "event_var_neg_propagations",
            "event_var_pos_conflict_lits",
            "event_var_neg_conflict_lits",
            "event_var_pos_assignments",
            "event_var_neg_assignments",
        ]:
            self.assertIn(key, stats)
            self.assertEqual(len(stats[key]), 2)


if __name__ == "__main__":
    unittest.main()
