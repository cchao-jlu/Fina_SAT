"""Guidance, strict probe-state encoding, and a local SAT witness check.

The witness check evaluates a supplied assignment against the original clauses.
It does not search. Historical ``solver_stats_to_global_state`` zero-fills
missing counters; this encoder rejects them instead.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from .contract import COUNTER_KEYS, SCHEMA


@dataclass(frozen=True)
class Cnf:
    num_vars: int
    clauses: tuple[tuple[int, ...], ...]
    sha256: str
    n: int


@dataclass(frozen=True)
class CellRequest:
    arm: str
    cnf: Cnf
    source_id: str
    checkpoint_sha256: str
    fixed_state_sha256: str
    repeat: int = 0
    split: str = "formal"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _as_action(action: object, num_vars: int) -> list[list[float]] | None:
    if not isinstance(action, (list, tuple)) or len(action) != num_vars:
        return None
    normalized: list[list[float]] = []
    for item in action:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return None
        polarity, weight = item
        if isinstance(polarity, bool) or not isinstance(polarity, (int, float)):
            return None
        if polarity not in (0, 1, 0.0, 1.0):
            return None
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            return None
        weight = float(weight)
        if not math.isfinite(weight) or weight <= 0.0:
            return None
        normalized.append([int(polarity), weight])
    return normalized


def validate_action(action: object, num_vars: int) -> list[list[float]] | None:
    """Return a normalized action, or None when guidance is null or unusable."""
    if action is None:
        return None
    return _as_action(action, num_vars)


def canonical_guided(cnf: Cnf, action: list[list[float]]) -> str:
    lines = [f"c {SCHEMA} guided", f"p cnf {cnf.num_vars} {len(cnf.clauses)}"]
    for index, (polarity, weight) in enumerate(action, start=1):
        lines.append(f"c w {index} {polarity} {weight:.17g}")
    for clause in cnf.clauses:
        lines.append(" ".join(str(literal) for literal in clause) + " 0")
    return "\n".join(lines) + "\n"


def action_sha256(cnf: Cnf, action: list[list[float]]) -> str:
    return sha256_text(canonical_guided(cnf, action))


def stats_complete(stats: object) -> bool:
    if not isinstance(stats, dict):
        return False
    for key in COUNTER_KEYS:
        if key not in stats:
            return False
        value = stats[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(float(value)) or float(value) < 0.0:
            return False
    if "Result" in stats and stats["Result"] not in ("UNKNOWN", "INDETERMINATE", None):
        return False
    return True


def encode_probe_z(stats: dict) -> tuple[float, ...]:
    """One log1p pass over a complete UNKNOWN counter vector. No zero-fill."""
    if not stats_complete(stats):
        raise ValueError("probe counters are incomplete")
    return (
        math.log1p(float(stats["decisions"])),
        math.log1p(float(stats["conflicts"])),
        math.log1p(float(stats["propagations"])),
        math.log1p(float(stats["restarts"])),
        math.log1p(float(stats["CPU time"])),
        0.0,
    )


def model_satisfies(cnf: Cnf, model: object) -> bool:
    if not isinstance(model, (list, tuple)):
        return False
    assignment: dict[int, bool] = {}
    for literal in model:
        if isinstance(literal, bool) or not isinstance(literal, int) or literal == 0:
            return False
        variable = abs(literal)
        if variable < 1 or variable > cnf.num_vars or variable in assignment:
            return False
        assignment[variable] = literal > 0
    if len(assignment) != cnf.num_vars:
        return False
    for clause in cnf.clauses:
        satisfied = False
        for literal in clause:
            variable = abs(int(literal))
            if variable not in assignment:
                return False
            value = assignment[variable]
            if (literal > 0 and value) or (literal < 0 and not value):
                satisfied = True
                break
        if not satisfied:
            return False
    return True


def witness_sha256(model: list[int] | tuple[int, ...]) -> str:
    return sha256_text(" ".join(str(literal) for literal in model))


def sha_ok(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)
