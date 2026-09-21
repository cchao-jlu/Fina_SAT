from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from src.echosat.equivalence import ALLOWED_RESULTS, SOLVED_RESULTS
from src.solving.solver import neutral_var_params


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv"
PLAIN_SOLVER = ROOT / "solvers/glucose/simp/glucose_release"
WEIGHTED_SOLVER = ROOT / "solvers/glucose_weighted/simp/glucose_release"

PLAIN_METHOD = "plain_unguided_glucose"
WEIGHTED_METHOD = "neutral_weighted_glucose"
METHODS = (PLAIN_METHOD, WEIGHTED_METHOD)
CHECKPOINT_PAIRS = 25
MAX_STREAM_EXCERPT_BYTES = 16 * 1024
REQUIRED_COUNTER_COLUMNS = (
    "final_decisions",
    "final_conflicts",
    "final_propagations",
    "final_restarts",
)

RESULT_COLUMNS = [
    "repeat_id",
    "base_instance_id",
    "variant",
    "family",
    "cnf_path",
    "method",
    "seed",
    "final_seed",
    "solver",
    "final_result",
    "final_solved",
    "final_decisions",
    "final_conflicts",
    "final_propagations",
    "final_restarts",
    "final_cpu_time",
    "final_wall_time",
    "final_solver_returncode",
    "external_timeout",
    "execution_error",
    "outcome_error",
    "budget_type",
    "budget_value",
    "resolved_binary_path",
    "solver_sha256",
    "cnf_sha256",
    "input_sha256",
    "argv_json",
    "seed_base",
    "rnd_freq",
    "K",
    "external_timeout_seconds",
    "manifest_row_sha256",
    "manifest_identity_sha256",
    "solver_stdout",
    "solver_stderr",
    "solver_stdout_bytes",
    "solver_stderr_bytes",
    "solver_stdout_truncated",
    "solver_stderr_truncated",
]

PROVENANCE_COLUMNS = (
    "repeat_id",
    "base_instance_id",
    "variant",
    "cnf_path",
    "method",
    "seed",
    "final_seed",
    "solver",
    "budget_type",
    "budget_value",
    "resolved_binary_path",
    "solver_sha256",
    "cnf_sha256",
    "input_sha256",
    "argv_json",
    "seed_base",
    "rnd_freq",
    "K",
    "external_timeout_seconds",
    "manifest_row_sha256",
    "manifest_identity_sha256",
)


class ResumeValidationError(ValueError):
    pass


class OutputLockError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunConfig:
    budget_type: str
    budget_value: int
    seed_base: int
    rnd_freq: float
    K: float
    external_timeout: float


@dataclass(frozen=True)
class PairSpec:
    repeat_id: int
    manifest_index: int
    manifest_row: dict[str, str]
    cnf_path: Path
    cnf_text: str
    cnf_sha256: str
    num_vars: int
    manifest_row_sha256: str


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a nonnegative integer")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return parsed


def probability(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def solver_K(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or not 0.0 < parsed < 1.0:
        raise argparse.ArgumentTypeError("must be finite and strictly between 0 and 1")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run model-free plain/neutral-weighted Glucose equivalence pairs."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget-type", choices=("conflicts", "cpu"), required=True)
    parser.add_argument("--budget-value", type=positive_int, required=True)
    parser.add_argument("--repeats", type=nonnegative_int, nargs="+", required=True)
    parser.add_argument("--workers", type=positive_int, default=1)
    parser.add_argument("--external-timeout", type=positive_float, default=60.0)
    parser.add_argument("--seed", type=positive_int, default=1)
    parser.add_argument("--rnd-freq", type=probability, default=0.0)
    parser.add_argument("-K", "--K", type=solver_K, default=0.1)
    args = parser.parse_args(argv)
    if len(set(args.repeats)) != len(args.repeats):
        parser.error("--repeats must contain unique repeat IDs")
    return args


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_manifest_cnf_path(
    raw_path: str | Path, *, manifest_dir: Path | None = None
) -> Path:
    path = Path(str(raw_path)).expanduser()
    if path.is_absolute() and path.exists():
        return path.resolve()
    marker = "/my_rlaf/"
    text = str(path)
    if marker in text:
        legacy = (ROOT / text.split(marker, 1)[1]).resolve()
        if legacy.exists():
            return legacy
    if not path.is_absolute():
        if manifest_dir is not None:
            manifest_candidate = (manifest_dir / path).resolve()
            if manifest_candidate.exists():
                return manifest_candidate
        repo_candidate = (ROOT / path).resolve()
        if repo_candidate.exists():
            return repo_candidate
    else:
        candidate = path.resolve()
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"manifest CNF path does not exist: {raw_path}")


def build_solver_argv(
    binary: Path,
    *,
    seed: int,
    rnd_freq: float,
    K: float,
    budget_type: str,
    budget_value: int,
) -> list[str]:
    if not math.isfinite(float(K)) or not 0.0 < float(K) < 1.0:
        raise ValueError("K must be finite and strictly between 0 and 1")
    budget_flag = "conf-lim" if budget_type == "conflicts" else "cpu-lim"
    return [
        str(binary.resolve()),
        f"-rnd-seed={seed}",
        f"-rnd-freq={rnd_freq}",
        f"-K={K}",
        f"-{budget_flag}={budget_value}",
    ]


def _read_manifest(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        required = {"base_instance_id", "variant", "cnf_path"}
        missing = sorted(required.difference(columns))
        if missing:
            raise ValueError(f"manifest missing required columns: {missing}")
        rows = [{key: "" if value is None else str(value) for key, value in row.items()} for row in reader]
    if not rows:
        raise ValueError("manifest contains no rows")
    return rows, columns


def _num_vars_from_dimacs(text: str) -> int:
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 4 and parts[:2] == ["p", "cnf"]:
            num_vars = int(parts[2])
            if num_vars < 0:
                break
            return num_vars
    raise ValueError("CNF is missing a valid 'p cnf' header")


def _weighted_dimacs(cnf_text: str, num_vars: int) -> str:
    params = neutral_var_params(num_vars, weight=1.0, phase=0.0)
    signed_scales = []
    for phase, weight in params:
        signed_scale = float(weight) if float(phase) > 0 else -float(weight)
        signed_scales.append(f"{signed_scale:.4f}")
    weight_line = "c weight" + (" " + " ".join(signed_scales) if signed_scales else "")
    lines = cnf_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("p cnf "):
            lines.insert(index + 1, weight_line)
            return "\n".join(lines) + "\n"
    raise ValueError("CNF is missing a valid 'p cnf' header")


def _canonical_manifest_row(row: dict[str, str], resolved_cnf: Path) -> str:
    payload = dict(sorted(row.items()))
    payload["cnf_path"] = str(resolved_cnf)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _build_pair_specs(
    rows: list[dict[str, str]], repeats: Iterable[int], *, manifest_dir: Path
) -> list[PairSpec]:
    source_rows: dict[tuple[str, str], list[int]] = {}
    for source_row, row in enumerate(rows, start=2):
        key = (row["base_instance_id"], row["variant"])
        source_rows.setdefault(key, []).append(source_row)
    duplicates = [
        (key, row_numbers)
        for key, row_numbers in source_rows.items()
        if len(row_numbers) > 1
    ]
    if duplicates:
        details = "; ".join(
            f"{key!r} rows {', '.join(map(str, row_numbers))}"
            for key, row_numbers in duplicates
        )
        raise ValueError(f"duplicate manifest (base_instance_id, variant) keys: {details}")
    base_specs = []
    for manifest_index, row in enumerate(rows):
        cnf_path = resolve_manifest_cnf_path(
            row["cnf_path"], manifest_dir=manifest_dir
        )
        cnf_bytes = cnf_path.read_bytes()
        cnf_text = cnf_bytes.decode("utf-8")
        canonical_row = _canonical_manifest_row(row, cnf_path)
        base_specs.append(
            {
                "manifest_index": manifest_index,
                "manifest_row": row,
                "cnf_path": cnf_path,
                "cnf_text": cnf_text,
                "cnf_sha256": sha256_bytes(cnf_bytes),
                "num_vars": _num_vars_from_dimacs(cnf_text),
                "manifest_row_sha256": sha256_bytes(canonical_row.encode("utf-8")),
            }
        )
    return [
        PairSpec(repeat_id=int(repeat_id), **base)
        for repeat_id in repeats
        for base in base_specs
    ]


def _manifest_identity_sha256(pair_specs: list[PairSpec]) -> str:
    normalized_rows = []
    seen_manifest_indices: set[int] = set()
    for spec in pair_specs:
        if spec.manifest_index in seen_manifest_indices:
            continue
        seen_manifest_indices.add(spec.manifest_index)
        normalized_rows.append(
            json.dumps(
                {
                    "row": json.loads(
                        _canonical_manifest_row(spec.manifest_row, spec.cnf_path)
                    ),
                    "cnf_sha256": spec.cnf_sha256,
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        )
    payload = json.dumps(sorted(normalized_rows), separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def _method_inputs(
    spec: PairSpec,
    config: RunConfig,
    binary_hashes: dict[str, str],
    manifest_identity_sha256: str,
) -> list[dict[str, Any]]:
    seed = config.seed_base + spec.repeat_id
    weighted_text = _weighted_dimacs(spec.cnf_text, spec.num_vars)
    method_data = (
        (PLAIN_METHOD, "glucose", PLAIN_SOLVER.resolve(), spec.cnf_text),
        (WEIGHTED_METHOD, "glucose_weighted", WEIGHTED_SOLVER.resolve(), weighted_text),
    )
    inputs = []
    for method, solver, binary, input_text in method_data:
        argv = build_solver_argv(
            binary,
            seed=seed,
            rnd_freq=config.rnd_freq,
            K=config.K,
            budget_type=config.budget_type,
            budget_value=config.budget_value,
        )
        metadata = dict(spec.manifest_row)
        metadata.update(
            {
                "repeat_id": spec.repeat_id,
                "base_instance_id": spec.manifest_row["base_instance_id"],
                "variant": spec.manifest_row["variant"],
                "family": spec.manifest_row.get("family", ""),
                "cnf_path": str(spec.cnf_path),
                "method": method,
                "seed": seed,
                "final_seed": seed,
                "solver": solver,
                "budget_type": config.budget_type,
                "budget_value": config.budget_value,
                "resolved_binary_path": str(binary),
                "solver_sha256": binary_hashes[method],
                "cnf_sha256": spec.cnf_sha256,
                "input_sha256": sha256_bytes(input_text.encode("utf-8")),
                "argv_json": json.dumps(argv, separators=(",", ":")),
                "seed_base": config.seed_base,
                "rnd_freq": config.rnd_freq,
                "K": config.K,
                "external_timeout_seconds": config.external_timeout,
                "manifest_row_sha256": spec.manifest_row_sha256,
                "manifest_identity_sha256": manifest_identity_sha256,
            }
        )
        inputs.append({"metadata": metadata, "argv": argv, "input_text": input_text})
    return inputs


def _decode_timeout_stream(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def _parse_solver_stdout(stdout: str) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    labels = {
        "decisions": "final_decisions",
        "conflicts": "final_conflicts",
        "propagations": "final_propagations",
        "restarts": "final_restarts",
        "CPU time": "final_cpu_time",
    }
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if line.startswith("s "):
            parts = line.split()
            if len(parts) >= 2:
                stats["final_result"] = parts[1]
        for label, column in labels.items():
            prefixes = (f"c {label}", label)
            if line.startswith(prefixes) and ":" in line:
                try:
                    number = float(line.split(":", 1)[1].strip().split()[0])
                except (IndexError, ValueError):
                    pass
                else:
                    if column == "final_cpu_time":
                        stats[column] = number
                    elif math.isfinite(number) and number.is_integer():
                        stats[column] = int(number)
                break
    return stats


def _bounded_stream(text: str) -> tuple[str, int, bool]:
    encoded = text.encode("utf-8", errors="replace")
    byte_count = len(encoded)
    truncated = byte_count > MAX_STREAM_EXCERPT_BYTES
    excerpt = encoded[:MAX_STREAM_EXCERPT_BYTES].decode("utf-8", errors="ignore")
    return excerpt, byte_count, truncated


def _canonical_outcome(
    parsed_result: str,
    returncode: int,
    *,
    timed_out: bool,
    execution_error_message: str,
    required_stats_error: str,
) -> tuple[str, bool, bool, str]:
    if timed_out:
        return "INDETERMINATE", False, False, "external_timeout"
    if execution_error_message:
        return "INDETERMINATE", False, True, execution_error_message
    if parsed_result == "INDETERMINATE" and returncode == 0:
        if required_stats_error:
            return "INDETERMINATE", False, True, required_stats_error
        return "INDETERMINATE", False, False, ""
    expected_result = {10: "SATISFIABLE", 20: "UNSATISFIABLE"}.get(returncode)
    if parsed_result == expected_result and expected_result is not None:
        if required_stats_error:
            return "INDETERMINATE", False, True, required_stats_error
        return expected_result, True, False, ""
    return (
        "INDETERMINATE",
        False,
        True,
        f"result_returncode_mismatch: parsed={parsed_result!r}, returncode={returncode}",
    )


def _required_stats_error(stats: dict[str, Any]) -> str:
    invalid = []
    for column in REQUIRED_COUNTER_COLUMNS:
        value = stats.get(column)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            invalid.append(column)
    cpu_time = stats.get("final_cpu_time")
    if (
        not isinstance(cpu_time, (int, float))
        or isinstance(cpu_time, bool)
        or not math.isfinite(float(cpu_time))
        or float(cpu_time) < 0
    ):
        invalid.append("final_cpu_time")
    if not invalid:
        return ""
    return f"invalid_or_missing_required_stats: {','.join(invalid)}"


def _safe_counter(stats: dict[str, Any], column: str) -> int | str:
    value = stats.get(column)
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return ""


def _run_method(item: dict[str, Any], external_timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    timed_out = False
    execution_error_message = ""
    try:
        completed = subprocess.run(
            item["argv"],
            input=item["input_text"],
            capture_output=True,
            text=True,
            timeout=external_timeout,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = int(completed.returncode)
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout = _decode_timeout_stream(error.stdout if error.stdout is not None else error.output)
        stderr = _decode_timeout_stream(error.stderr)
        returncode = -9
    except OSError as error:
        stdout = ""
        stderr = f"{type(error).__name__}: {error}"
        returncode = -1
        execution_error_message = stderr
    wall_time = time.perf_counter() - started
    stats = _parse_solver_stdout(stdout)
    parsed_result = str(stats.get("final_result", ""))
    result, solved, execution_error, outcome_error = _canonical_outcome(
        parsed_result,
        returncode,
        timed_out=timed_out,
        execution_error_message=execution_error_message,
        required_stats_error=_required_stats_error(stats),
    )
    stdout_excerpt, stdout_bytes, stdout_truncated = _bounded_stream(stdout)
    stderr_excerpt, stderr_bytes, stderr_truncated = _bounded_stream(stderr)
    row = dict(item["metadata"])
    row.update(stats)
    row.update(
        {
            "final_result": result,
            "final_solved": solved,
            "final_decisions": _safe_counter(stats, "final_decisions"),
            "final_conflicts": _safe_counter(stats, "final_conflicts"),
            "final_propagations": _safe_counter(stats, "final_propagations"),
            "final_restarts": _safe_counter(stats, "final_restarts"),
            "final_cpu_time": (
                stats.get("final_cpu_time", "")
                if solved or (result == "INDETERMINATE" and not outcome_error)
                else ""
            ),
            "final_wall_time": wall_time,
            "final_solver_returncode": returncode,
            "external_timeout": timed_out,
            "execution_error": execution_error,
            "outcome_error": outcome_error,
            "solver_stdout": stdout_excerpt,
            "solver_stderr": stderr_excerpt,
            "solver_stdout_bytes": stdout_bytes,
            "solver_stderr_bytes": stderr_bytes,
            "solver_stdout_truncated": stdout_truncated,
            "solver_stderr_truncated": stderr_truncated,
        }
    )
    return row


def _run_pair(
    spec: PairSpec,
    config: RunConfig,
    binary_hashes: dict[str, str],
    manifest_identity_sha256: str,
) -> list[dict[str, Any]]:
    return [
        _run_method(item, config.external_timeout)
        for item in _method_inputs(
            spec, config, binary_hashes, manifest_identity_sha256
        )
    ]


def _row_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        int(row["repeat_id"]),
        str(row["base_instance_id"]),
        str(row["variant"]),
        str(row["method"]),
    )


def _pair_key(row: dict[str, Any]) -> tuple[int, str, str]:
    return _row_key(row)[:3]


def _normalized(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if text in {"True", "False"}:
        return text.lower()
    try:
        number = float(text)
    except ValueError:
        return text
    if math.isfinite(number):
        return format(number, ".17g")
    return text


def _resume_bool(value: Any) -> tuple[bool, bool]:
    normalized = str(value).strip().lower()
    if normalized in {"true", "1"}:
        return True, True
    if normalized in {"false", "0"}:
        return False, True
    return False, False


def _resume_nonnegative_integer(value: Any) -> bool:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number >= 0 and number.is_integer()


def _resume_nonnegative_float(value: Any) -> bool:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number >= 0


def _resume_integer(value: Any) -> tuple[int, bool]:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return 0, False
    if not math.isfinite(number) or not number.is_integer():
        return 0, False
    return int(number), True


def _validate_completed_row(row: dict[str, str], key: tuple[int, str, str, str]) -> None:
    result = row.get("final_result", "")
    if result not in ALLOWED_RESULTS:
        raise ResumeValidationError(f"invalid existing row for {key}: final_result")
    solved, solved_valid = _resume_bool(row.get("final_solved", ""))
    if not solved_valid or solved != (result in SOLVED_RESULTS):
        raise ResumeValidationError(
            f"invalid existing row for {key}: final_result/final_solved"
        )
    timed_out, timeout_valid = _resume_bool(row.get("external_timeout", ""))
    execution_error, execution_error_valid = _resume_bool(
        row.get("execution_error", "")
    )
    if not timeout_valid or not execution_error_valid:
        raise ResumeValidationError(f"invalid existing row for {key}: outcome flags")
    outcome_error = str(row.get("outcome_error", "")).strip()
    returncode, returncode_valid = _resume_integer(
        row.get("final_solver_returncode", "")
    )
    if not returncode_valid:
        raise ResumeValidationError(
            f"invalid existing row for {key}: final_solver_returncode"
        )
    if solved:
        for column in REQUIRED_COUNTER_COLUMNS:
            if not _resume_nonnegative_integer(row.get(column, "")):
                raise ResumeValidationError(
                    f"invalid existing row for {key}: {column}"
                )
        if not _resume_nonnegative_float(row.get("final_cpu_time", "")):
            raise ResumeValidationError(
                f"invalid existing row for {key}: final_cpu_time"
            )
        expected_returncode = 10 if result == "SATISFIABLE" else 20
        consistent = (
            returncode == expected_returncode
            and not timed_out
            and not execution_error
            and not outcome_error
        )
    else:
        complete_required_stats = all(
            _resume_nonnegative_integer(row.get(column, ""))
            for column in REQUIRED_COUNTER_COLUMNS
        ) and _resume_nonnegative_float(row.get("final_cpu_time", ""))
        for column in REQUIRED_COUNTER_COLUMNS:
            value = str(row.get(column, "")).strip()
            if value and not _resume_nonnegative_integer(value):
                raise ResumeValidationError(
                    f"invalid existing row for {key}: {column}"
                )
        cpu_value = str(row.get("final_cpu_time", "")).strip()
        if cpu_value and not _resume_nonnegative_float(cpu_value):
            raise ResumeValidationError(
                f"invalid existing row for {key}: final_cpu_time"
            )
        if not timed_out and not execution_error:
            consistent = (
                result == "INDETERMINATE"
                and returncode == 0
                and not outcome_error
                and complete_required_stats
            )
        else:
            consistent = (
                result == "INDETERMINATE"
                and bool(outcome_error)
                and timed_out != execution_error
                and ((timed_out and returncode == -9) or execution_error)
            )
    if not _resume_nonnegative_float(row.get("final_wall_time", "")):
        raise ResumeValidationError(f"invalid existing row for {key}: final_wall_time")
    if not consistent:
        raise ResumeValidationError(
            f"invalid existing row for {key}: result/returncode/timeout"
        )


def _load_resume_rows(
    output: Path,
    expected: dict[tuple[int, str, str, str], dict[str, Any]],
) -> list[dict[str, str]]:
    if not output.exists():
        return []
    with output.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = sorted(set(RESULT_COLUMNS).difference(reader.fieldnames or []))
        if missing_columns:
            raise ResumeValidationError(
                f"incomplete existing output: missing columns {missing_columns}"
            )
        rows = list(reader)
    seen: set[tuple[int, str, str, str]] = set()
    pair_methods: dict[tuple[int, str, str], set[str]] = {}
    for row in rows:
        key = _row_key(row)
        if key in seen:
            raise ResumeValidationError(f"duplicate existing row for {key}")
        seen.add(key)
        _validate_completed_row(row, key)
        pair_methods.setdefault(_pair_key(row), set()).add(str(row["method"]))
        expected_row = expected.get(key)
        if expected_row is None:
            raise ResumeValidationError(f"resume provenance mismatch: unexpected row {key}")
        if row.get("manifest_identity_sha256") != expected_row.get(
            "manifest_identity_sha256"
        ):
            raise ResumeValidationError(
                f"resume manifest identity mismatch for {key}"
            )
        expected_columns = tuple(dict.fromkeys((*PROVENANCE_COLUMNS, *expected_row.keys())))
        for column in expected_columns:
            if column not in row or _normalized(row[column]) != _normalized(expected_row[column]):
                raise ResumeValidationError(
                    f"resume provenance mismatch for {key}: column {column}"
                )
    for pair, methods in pair_methods.items():
        if methods != set(METHODS):
            raise ResumeValidationError(f"incomplete existing pair {pair}: methods={sorted(methods)}")
    return rows


def _fieldnames(rows: list[dict[str, Any]], manifest_columns: list[str]) -> list[str]:
    ordered = list(RESULT_COLUMNS)
    for column in manifest_columns:
        if column not in ordered:
            ordered.append(column)
    for row in rows:
        for column in row:
            if column not in ordered:
                ordered.append(column)
    return ordered


def _sort_rows(rows: list[dict[str, Any]], pair_order: dict[tuple[int, str, str], int]) -> list[dict[str, Any]]:
    method_order = {method: index for index, method in enumerate(METHODS)}
    return sorted(
        rows,
        key=lambda row: (
            pair_order[_pair_key(row)],
            method_order[str(row["method"])],
        ),
    )


def output_lock_path(output: Path) -> Path:
    return output.with_name(f"{output.name}.lock")


@contextmanager
def _exclusive_output_lock(output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    lock_path = output_lock_path(output)
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise OutputLockError(
                f"another writer holds the output lock: {lock_path}"
            ) from error
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_write_csv(
    output: Path, rows: list[dict[str, Any]], manifest_columns: list[str]
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _fieldnames(rows, manifest_columns)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output)
        parent_descriptor = os.open(output.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = args.manifest.expanduser().resolve()
    output = args.output.expanduser().resolve()
    with _exclusive_output_lock(output):
        manifest_rows, manifest_columns = _read_manifest(manifest_path)
        pair_specs = _build_pair_specs(
            manifest_rows, args.repeats, manifest_dir=manifest_path.parent
        )
        manifest_identity_sha256 = _manifest_identity_sha256(pair_specs)
        config = RunConfig(
            budget_type=args.budget_type,
            budget_value=args.budget_value,
            seed_base=args.seed,
            rnd_freq=args.rnd_freq,
            K=args.K,
            external_timeout=args.external_timeout,
        )
        binary_hashes = {
            PLAIN_METHOD: sha256_file(PLAIN_SOLVER.resolve()),
            WEIGHTED_METHOD: sha256_file(WEIGHTED_SOLVER.resolve()),
        }
        expected = {
            _row_key(item["metadata"]): item["metadata"]
            for spec in pair_specs
            for item in _method_inputs(
                spec, config, binary_hashes, manifest_identity_sha256
            )
        }
        existing_rows = _load_resume_rows(output, expected)
        completed_pairs = {_pair_key(row) for row in existing_rows}
        pending = [
            spec
            for spec in pair_specs
            if (
                spec.repeat_id,
                spec.manifest_row["base_instance_id"],
                spec.manifest_row["variant"],
            )
            not in completed_pairs
        ]
        pair_order = {
            (
                spec.repeat_id,
                spec.manifest_row["base_instance_id"],
                spec.manifest_row["variant"],
            ): index
            for index, spec in enumerate(pair_specs)
        }
        all_rows: list[dict[str, Any]] = list(existing_rows)
        completed_since_checkpoint = 0
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(
                    _run_pair,
                    spec,
                    config,
                    binary_hashes,
                    manifest_identity_sha256,
                )
                for spec in pending
            ]
            for future in as_completed(futures):
                all_rows.extend(future.result())
                completed_since_checkpoint += 1
                if completed_since_checkpoint >= CHECKPOINT_PAIRS:
                    all_rows = _sort_rows(all_rows, pair_order)
                    _atomic_write_csv(output, all_rows, manifest_columns)
                    completed_since_checkpoint = 0
        all_rows = _sort_rows(all_rows, pair_order)
        _atomic_write_csv(output, all_rows, manifest_columns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
