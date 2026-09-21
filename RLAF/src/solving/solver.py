import os
from typing import Any

import numpy as np
import subprocess
import tempfile

from src.data.io_utils import load_dimacs_cnf


SOLVER_BIN_PATHS = {
    "glucose": "solvers/glucose/simp/glucose_static",
    "glucose_weighted": "solvers/glucose_weighted/simp/glucose_static",
    "march": "solvers/march/march_nh",
    "march_weighted": "solvers/march_weighted/march_nh",
}


STATS = ["decisions", "conflicts", "propagations", "restarts", "CPU time"]


def neutral_var_params(num_vars: int, weight: float = 1.0, phase: float = 0.0) -> np.ndarray:
    return np.tile(
        np.asarray([float(phase), float(weight)], dtype=np.float32),
        (int(num_vars), 1),
    )


def subprocess_timeout(params: dict[str, Any], margin: float = 10.0) -> float | None:
    cpu_lim = params.get("cpu-lim")
    if cpu_lim is None:
        return None
    try:
        return max(1.0, float(cpu_lim) + float(margin))
    except (TypeError, ValueError):
        return None


def timeout_result(exc: subprocess.TimeoutExpired) -> dict[str, Any]:
    stdout = exc.stdout or ""
    stderr = exc.stderr or ""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    stats = stdout_to_results_dict(stdout)
    stats.setdefault("Result", "INDETERMINATE")
    stats["solver_returncode"] = -9
    stats["solver_timeout"] = True
    stats["solver_stdout_bytes"] = len(stdout.encode("utf-8", errors="replace"))
    stats["solver_stderr_bytes"] = len(stderr.encode("utf-8", errors="replace"))
    return stats


def _parse_event_values(raw: str) -> list[float]:
    values = []
    for part in raw.strip().split():
        try:
            value = float(part)
        except ValueError:
            continue
        values.append(value)
    return values


def stdout_to_results_dict(stdout: str) -> dict[str, Any]:
    """ Parse a string of solver outputs into a results dictionary """
    stats = {}

    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("c event "):
            parts = line.split(maxsplit=3)
            if len(parts) == 4:
                key = f"event_{parts[2]}"
                stats[key] = _parse_event_values(parts[3])
            continue
        for stat in STATS:
            if line.startswith(f"c {stat}") or line.startswith(stat):
                _, value_part = line.split(':', 1)
                value = float(value_part.strip().split()[0])
                stats[stat] = value
            elif line.startswith("s"):
                stats["Result"] = line.split()[1]

    return stats


def cnf_to_dimacs(f: list[list[int]], var_params: np.ndarray | None = None) -> str:
    """
    :param f: CNF formula formatted as a list of lists of signed integers. Each integer is one literal.
    :param var_params: Variable parameterization W. This is an array of shape [num_vars, 2], where
    var_params[i,0] is the polarity and var_params[i,1] is the variable weight.
    :return: The DIMACS string that represents the CNF formula. If `var_params` is `None`, then the
     polarities and weights are included in the string as a comment line starting with 'c weight'.
     Our extended solvers are built to parse polarities and weights from this line, if provided.
    """
    # Determine the maximum variable index
    variables = set(abs(lit) for clause in f for lit in clause)
    num_variables = max(variables)
    num_clauses = len(f)

    lines = [f"p cnf {num_variables} {num_clauses}"]
    if var_params is not None:
        assert num_variables == var_params.shape[0], f"{num_variables} != {var_params.shape}[0]"

        params = ["c weight"]
        for i in range(num_variables):
            weight = float(var_params[i, 1])
            sgn = 1 if var_params[i, 0] > 0 else -1
            signed_scale = sgn * weight
            if abs(signed_scale) == 1.0:
                params.append(f"{signed_scale:.4f}")
            else:
                params.append(f"{signed_scale:.17g}")
        lines.append(" ".join(params))

    for clause in f:
        clause_line = " ".join(map(str, clause)) + " 0"
        lines.append(clause_line)
    return "\n".join(lines)


def solve_cnf(
        f: list[list[int]],
        var_params: np.ndarray | None = None,
        seed: int | None = 1,
        solver: str = "glucose",
        **params: Any,
) -> dict[str, Any]:
    """
    Solves a given CNF formula with a specified solver. With weights and polarities are provided then the guided version of the solver is used.
    :param f: CNF formula formatted as a list of lists of signed integers. Each integer is one literal.
    :param var_params: Variable parameterization W. This is an array of shape [num_vars, 2], where
    var_params[i,0] is the polarity and var_params[i,1] is the variable weight.
    :param seed: Seed for random number generation passed to the glucose solver.
    :param solver: Solver to use. Either glucose or march,
    :param params: Solver CLI parameters. Only used with glucose.
    :return: A dictionary that with solver statistics, including the results, the runtime and the number of decisions required.
    """

    dimacs_str = cnf_to_dimacs(f, var_params=var_params)
    timeout = subprocess_timeout(params)

    if solver != "march":
        if var_params is None:
            bin_path = SOLVER_BIN_PATHS["glucose"]
        else:
            bin_path = SOLVER_BIN_PATHS["glucose_weighted"]

        call = [f"{bin_path}"]

        if seed is not None:
            assert seed > 0
            call.append(f"-rnd-seed={seed}")

        for key, val in params.items():
            if isinstance(val, bool):
                if val:
                    call.append(f"-{key}")
            else:
                call.append(f"-{key}={val}")

        # Write the DIMACS string to a temporary file and pass it as stdin
        with tempfile.TemporaryFile(mode='w+') as tmp_file:
            tmp_file.write(dimacs_str)
            tmp_file.seek(0)
            try:
                result = subprocess.run(
                    call,
                    capture_output=True,
                    text=True,
                    stdin=tmp_file,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as exc:
                return timeout_result(exc)
    else:

        if var_params is None:
            bin_path = SOLVER_BIN_PATHS["march"]
        else:
            bin_path = SOLVER_BIN_PATHS["march_weighted"]
        call = [f"{bin_path}"]

        tmp_dir = "./data/tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_file_name = os.path.join(tmp_dir, f"tmp_{abs(hash(dimacs_str))}.cnf")
        with open(tmp_file_name, "w") as f:
            f.write(dimacs_str)
        call.append(tmp_file_name)
        try:
            result = subprocess.run(
                call,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return timeout_result(exc)
        finally:
            if os.path.exists(tmp_file_name):
                os.remove(tmp_file_name)

    stats = stdout_to_results_dict(result.stdout)
    stats["solver_returncode"] = int(result.returncode)
    stats["solver_timeout"] = False
    stats["solver_stdout_bytes"] = len(result.stdout.encode("utf-8", errors="replace"))
    stats["solver_stderr_bytes"] = len(result.stderr.encode("utf-8", errors="replace"))
    return stats
