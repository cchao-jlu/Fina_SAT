from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv"
DEFAULT_OUT = ROOT / "runs/analysis/echosat_v2_orbit_certification.csv"
DEFAULT_VARIABLE_OUT = ROOT / "runs/analysis/echosat_v2_orbit_variables.csv"
DEFAULT_DOC = ROOT / "docs/echosat_v2_orbit_certification.md"
VARIABLE_COLUMNS = [
    "family",
    "control_type",
    "symmetry_strength",
    "base_instance_id",
    "variant",
    "cnf_path",
    "variable_id",
    "orbit_id",
    "orbit_index",
    "orbit_size",
    "structure_type",
    "orbit_confidence",
    "valid_orbit_mask",
    "needs_refinement",
    "certification_source",
]


def resolve(path: Path | str) -> Path:
    path = Path(path)
    if not path.is_absolute():
        return ROOT / path
    if path.exists():
        return path
    marker = "/my_rlaf/"
    raw_path = str(path)
    if marker in raw_path:
        return ROOT / raw_path.split(marker, 1)[1]
    return path


def artifact_path(path: Path | str) -> str:
    resolved = resolve(path).resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


class JsonObjectPairs(list[tuple[str, Any]]):
    pass


class PositiveIntegerError(ValueError):
    def __init__(self, label: str, value: Any, reason: str) -> None:
        super().__init__(f"invalid {label}: {value!r}")
        self.reason = reason


def schema_error_row(common: dict[str, Any], source: str, notes: str) -> dict[str, Any]:
    return {
        **common,
        "orbit_id": source,
        "vars": "",
        "orbit_size": 0,
        "structure_type": "none" if common["control_type"] == "non_symmetric_control" else "unknown",
        "certification_source": source,
        "orbit_confidence": 0.0,
        "valid_for_training": False,
        "needs_refinement": common["control_type"] != "non_symmetric_control",
        "notes": notes,
    }


def read_orbit_table(path: str | Path, num_vars: int) -> tuple[dict[int, str] | None, str, str]:
    resolved = resolve(path)
    if not resolved.exists():
        return None, "missing_orbit_table", "missing orbits_path"
    try:
        text = resolved.read_text(encoding="utf-8")
        parsed = json.loads(text, object_pairs_hook=JsonObjectPairs)
    except json.JSONDecodeError as exc:
        return None, "orbit_json_schema_error_invalid_json", str(exc)
    except OSError as exc:
        return None, "missing_orbit_table", str(exc)
    if not isinstance(parsed, JsonObjectPairs):
        return None, "orbit_json_schema_error_invalid_table", "orbit JSON root must be an object"
    if not parsed:
        return None, "missing_orbit_table", "empty orbit table"

    seen_raw_keys: set[str] = set()
    orbit_map: dict[int, str] = {}
    for raw_key, raw_orbit_id in parsed:
        if raw_key in seen_raw_keys:
            return None, "orbit_json_schema_error_duplicate_key", f"duplicate variable key: {raw_key!r}"
        seen_raw_keys.add(raw_key)
        if re.fullmatch(r"-?\d+", raw_key):
            variable_id = int(raw_key)
            if variable_id <= 0:
                return None, "orbit_json_schema_error_nonpositive_variable_key", f"nonpositive variable key: {raw_key!r}"
            if str(variable_id) != raw_key:
                return None, "orbit_json_schema_error_variable_key_alias", f"noncanonical variable key: {raw_key!r}"
        else:
            return None, "orbit_json_schema_error_invalid_variable_key", f"invalid variable key: {raw_key!r}"
        if variable_id > num_vars:
            return None, "orbit_json_schema_error_out_of_range_variable_key", (
                f"variable key {variable_id} exceeds num_vars={num_vars}"
            )
        if not isinstance(raw_orbit_id, str) or not raw_orbit_id.strip():
            return None, "orbit_json_schema_error_invalid_orbit_id", (
                f"orbit ID for variable {variable_id} must be a nonempty string"
            )
        orbit_map[variable_id] = raw_orbit_id.strip()
    return orbit_map, "", ""


def positive_int(value: Any, label: str) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise PositiveIntegerError(label, value, "boolean")
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PositiveIntegerError(label, value, "malformed") from exc
    try:
        if float(value) != float(parsed):
            raise PositiveIntegerError(label, value, "nonintegral")
    except (TypeError, ValueError, OverflowError) as exc:
        if isinstance(exc, PositiveIntegerError):
            raise
        raise PositiveIntegerError(label, value, "malformed") from exc
    if parsed <= 0:
        raise PositiveIntegerError(label, value, "nonpositive")
    return parsed


def strict_bool(value: Any, label: str) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise ValueError(f"invalid {label}: expected true or false, got {value!r}")


def bounded_confidence(value: Any) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"invalid orbit_confidence: {value!r}")
    try:
        confidence = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"invalid orbit_confidence: {value!r}") from exc
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ValueError(f"invalid orbit_confidence: {value!r}")
    return confidence


def confidence_for(row: pd.Series, orbit_size: int) -> float:
    control_type = str(row.get("control_type", ""))
    strength = str(row.get("symmetry_strength", ""))
    if control_type == "non_symmetric_control" or strength == "none":
        return 0.0
    if orbit_size < 2:
        return 0.0
    if strength == "strong":
        return 1.0
    if strength == "weak":
        return 0.6
    if strength == "pseudo":
        return 0.3
    return 0.5


def structure_type_for(row: pd.Series, orbit_id: str) -> str:
    family = str(row.get("family", ""))
    if family in {"php", "php_exit_single", "php_exit_all"}:
        return "row_column"
    if family == "subset_cardinality":
        return "bandwidth_cardinality"
    if family in {"dominating_set_hex", "vertex_cover_torus", "even_colouring"}:
        return "grid_or_torus"
    if family == "complete_coloring":
        return "graph_coloring"
    if family == "tseitin_complete":
        return "complete_graph_parity"
    if family == "random_3sat_control":
        return "none"
    return "unknown"


def rows_for_instance(row: pd.Series) -> list[dict[str, Any]]:
    orbits_path = str(row.get("orbits_path", "") or "")
    num_vars = positive_int(row.get("num_vars"), "num_vars")
    base = str(row.get("base_instance_id", row.get("instance_id", "")))
    variant = str(row.get("variant", "base"))
    common = {
        "family": str(row.get("family", "")),
        "instance_id": str(row.get("instance_id", "")),
        "base_instance_id": base,
        "variant": variant,
        "cnf_path": artifact_path(str(row.get("cnf_path", ""))) if str(row.get("cnf_path", "")) else "",
        "orbits_path": artifact_path(orbits_path) if orbits_path else "",
        "metadata_path": artifact_path(str(row.get("metadata_path", ""))) if str(row.get("metadata_path", "")) else "",
        "control_type": str(row.get("control_type", "")),
        "symmetry_strength": str(row.get("symmetry_strength", "")),
        "num_vars": num_vars,
        "scale": str(row.get("scale", "")),
        "benchmark_role": str(row.get("benchmark_role", "")),
        "permutation_variant": strict_bool(row.get("permutation_variant", False), "permutation_variant"),
    }
    if not orbits_path:
        return [schema_error_row(common, "missing_orbit_table", "missing orbits_path")]
    orbit_map, schema_source, schema_notes = read_orbit_table(orbits_path, num_vars)
    if schema_source:
        return [schema_error_row(common, schema_source, schema_notes)]
    assert orbit_map is not None

    grouped: dict[str, list[int]] = {}
    for variable_id, orbit_id in orbit_map.items():
        grouped.setdefault(orbit_id, []).append(variable_id)

    rows = []
    for orbit_id, variables in sorted(grouped.items(), key=lambda item: (item[0], min(item[1]) if item[1] else 0)):
        variables = sorted(set(int(var) for var in variables))
        conf = confidence_for(row, len(variables))
        valid = conf >= 0.5 and len(variables) >= 2 and common["control_type"] != "non_symmetric_control"
        rows.append(
            {
                **common,
                "orbit_id": orbit_id,
                "vars": " ".join(map(str, variables)),
                "orbit_size": len(variables),
                "structure_type": structure_type_for(row, orbit_id),
                "certification_source": "generator_or_manual_orbit_json",
                "orbit_confidence": conf,
                "valid_for_training": bool(valid),
                "needs_refinement": bool(conf < 0.5 and common["control_type"] != "non_symmetric_control"),
                "notes": "",
            }
        )
    return rows


def parse_variable_ids(value: Any) -> list[int]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    tokens = value if isinstance(value, (list, tuple, set)) else str(value).split()
    parsed: list[int] = []
    for token in tokens:
        parsed.append(positive_int(token, "variable_id"))
    return parsed


def deterministic_sort_value(value: Any) -> str:
    if isinstance(value, set):
        return f"set:{sorted(str(item) for item in value)!r}"
    if isinstance(value, (list, tuple)):
        return f"sequence:{[str(item) for item in value]!r}"
    return f"{type(value).__name__}:{value!r}"


def expand_orbit_variables(orbit_rows: pd.DataFrame) -> pd.DataFrame:
    if orbit_rows.empty:
        return pd.DataFrame(columns=VARIABLE_COLUMNS)

    expanded: list[dict[str, Any]] = []
    for cnf_path, instance_rows in orbit_rows.groupby("cnf_path", sort=True, dropna=False):
        for _, candidate in instance_rows.iterrows():
            bounded_confidence(candidate.get("orbit_confidence"))
            strict_bool(candidate.get("valid_for_training"), "valid_for_training")
            strict_bool(candidate.get("needs_refinement"), "needs_refinement")
        ordered_rows = instance_rows.copy()
        tie_breakers: list[str] = []
        for column in sorted(ordered_rows.columns):
            if column == "cnf_path":
                continue
            tie_breaker = f"__sort_{column}"
            ordered_rows[tie_breaker] = ordered_rows[column].map(deterministic_sort_value)
            tie_breakers.append(tie_breaker)
        ordered_rows = (
            ordered_rows.sort_values(tie_breakers, kind="mergesort")
            .drop(columns=tie_breakers)
            .reset_index(drop=True)
        )
        num_vars_values = {positive_int(value, "num_vars") for value in ordered_rows["num_vars"]}
        if len(num_vars_values) != 1:
            raise ValueError(f"conflicting num_vars for cnf_path={cnf_path!r}")
        num_vars = next(iter(num_vars_values))
        first = ordered_rows.iloc[0]
        common = {
            "family": str(first.get("family", "")),
            "control_type": str(first.get("control_type", "")),
            "symmetry_strength": str(first.get("symmetry_strength", "")),
            "base_instance_id": str(first.get("base_instance_id", "")),
            "variant": str(first.get("variant", "base")),
            "cnf_path": str(cnf_path),
        }
        random_control = (
            common["control_type"] == "non_symmetric_control"
            or common["symmetry_strength"] == "none"
        )
        orbit_ids = sorted({str(value) for value in ordered_rows["orbit_id"]})
        orbit_indices = {orbit_id: index for index, orbit_id in enumerate(orbit_ids)}
        assignments: dict[int, dict[str, Any]] = {}
        failure_source = ""

        for _, orbit_row in ordered_rows.iterrows():
            row_source = str(orbit_row.get("certification_source", ""))
            row_orbit_id = str(orbit_row.get("orbit_id", ""))
            if row_source in {
                "missing",
                "missing_orbit_table",
                "malformed_orbit_variables",
                "out_of_range_orbit_variable",
            } or row_source.startswith("orbit_json_schema_error_") or row_orbit_id in {
                "missing_orbit_table",
                "malformed_orbit_variables",
                "out_of_range_orbit_variable",
            }:
                failure_source = {
                    "missing": "missing_orbit_table",
                }.get(row_source, row_source or row_orbit_id)
                break
            try:
                variable_ids = parse_variable_ids(orbit_row.get("vars", ""))
            except PositiveIntegerError as exc:
                if exc.reason != "malformed":
                    raise
                failure_source = "malformed_orbit_variables"
                break
            if any(variable_id > num_vars for variable_id in variable_ids):
                failure_source = "out_of_range_orbit_variable"
                break
            sorted_variables = sorted(variable_ids)
            for variable_id in sorted_variables:
                if variable_id in assignments:
                    raise ValueError(
                        f"duplicate variable assignment for cnf_path={cnf_path!r}: {variable_id}"
                    )
                assignments[variable_id] = {
                    "orbit_id": row_orbit_id,
                    "orbit_index": orbit_indices[row_orbit_id],
                    "orbit_size": len(sorted_variables),
                    "structure_type": str(orbit_row.get("structure_type", "unknown")),
                    "orbit_confidence": bounded_confidence(orbit_row.get("orbit_confidence")),
                    "valid_orbit_mask": strict_bool(
                        orbit_row.get("valid_for_training"), "valid_for_training"
                    ),
                    "needs_refinement": strict_bool(
                        orbit_row.get("needs_refinement"), "needs_refinement"
                    ),
                    "certification_source": row_source or "generator_or_manual_orbit_json",
                }

        next_uncertified_index = 0 if failure_source else len({row["orbit_id"] for row in assignments.values()})
        for variable_id in range(1, num_vars + 1):
            if failure_source:
                variable = {
                    "orbit_id": f"{failure_source}_variable_{variable_id}",
                    "orbit_index": next_uncertified_index,
                    "orbit_size": 0,
                    "structure_type": "none" if random_control else "unknown",
                    "orbit_confidence": 0.0,
                    "valid_orbit_mask": False,
                    "needs_refinement": not random_control,
                    "certification_source": failure_source,
                }
            elif variable_id not in assignments:
                variable = {
                    "orbit_id": f"uncovered_variable_{variable_id}",
                    "orbit_index": next_uncertified_index,
                    "orbit_size": 0,
                    "structure_type": "none" if random_control else "unknown",
                    "orbit_confidence": 0.0,
                    "valid_orbit_mask": False,
                    "needs_refinement": not random_control,
                    "certification_source": (
                        "non_symmetric_control" if random_control else "uncovered_declared_variable"
                    ),
                }
            else:
                variable = assignments[variable_id].copy()
                if random_control:
                    variable.update(
                        orbit_confidence=0.0,
                        valid_orbit_mask=False,
                        needs_refinement=False,
                        certification_source="non_symmetric_control",
                    )
            expanded.append({**common, "variable_id": variable_id, **variable})
            if failure_source or variable_id not in assignments:
                next_uncertified_index += 1

    return (
        pd.DataFrame(expanded, columns=VARIABLE_COLUMNS)
        .sort_values(["cnf_path", "variable_id"], kind="mergesort")
        .reset_index(drop=True)
    )


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return lines


def render_doc(
    rows: pd.DataFrame,
    variable_rows: pd.DataFrame,
    out_csv: Path,
    out_variable_csv: Path,
    manifest: Path,
) -> str:
    summary = (
        rows.groupby(["family", "control_type", "symmetry_strength"], sort=True)
        .agg(
            instances=("instance_id", "nunique"),
            bases=("base_instance_id", "nunique"),
            orbit_rows=("orbit_id", "count"),
            valid_orbit_rows=("valid_for_training", lambda values: int(pd.Series(values).astype(bool).sum())),
            valid_orbit_vars=("orbit_size", lambda values: int(rows.loc[values.index, "orbit_size"][rows.loc[values.index, "valid_for_training"].astype(bool)].sum())),
            mean_orbit_confidence=("orbit_confidence", "mean"),
            needs_refinement_rows=("needs_refinement", lambda values: int(pd.Series(values).astype(bool).sum())),
        )
        .reset_index()
    )
    control = rows[rows["control_type"].astype(str).eq("non_symmetric_control")].copy()
    control_high = int((pd.to_numeric(control["orbit_confidence"], errors="coerce").fillna(0.0) > 0.0).sum()) if not control.empty else 0
    duplicate_count = int(variable_rows.duplicated(["cnf_path", "variable_id"]).sum())
    uncertified_count = int((~variable_rows["valid_orbit_mask"].astype(bool)).sum())
    random_valid_count = int(
        variable_rows.loc[
            variable_rows["control_type"].astype(str).eq("non_symmetric_control"),
            "valid_orbit_mask",
        ].astype(bool).sum()
    )
    expected_pairs = {
        (str(cnf_path), variable_id)
        for cnf_path, group in rows.groupby("cnf_path", sort=False, dropna=False)
        for variable_id in range(1, positive_int(group["num_vars"].iloc[0], "num_vars") + 1)
    }
    actual_pairs = set(zip(variable_rows["cnf_path"].astype(str), variable_rows["variable_id"].astype(int)))
    full_coverage = duplicate_count == 0 and actual_pairs == expected_pairs
    lines = [
        "# EchoSAT Orbit Certification",
        "",
        "This expands manifest orbit JSON files into an auditable orbit table for EchoSAT training boundaries. It is not a runtime benchmark and does not train a model.",
        "",
        "## Inputs",
        "",
        f"- manifest: `{manifest}`",
        f"- output CSV: `{out_csv}`",
        f"- variable output CSV: `{out_variable_csv}`",
        "",
        "## Sanity",
        "",
        f"- orbit rows: `{len(rows)}`",
        f"- variable rows: `{len(variable_rows)}`",
        f"- base instances: `{rows['base_instance_id'].nunique() if not rows.empty else 0}`",
        f"- random-control rows with nonzero confidence: `{control_high}`",
        f"- full variable coverage: `{full_coverage}`",
        f"- duplicate variable rows: `{duplicate_count}`",
        f"- uncovered/uncertified variable rows: `{uncertified_count}`",
        f"- random-control valid-variable count: `{random_valid_count}`",
        "",
        "## Family Summary",
        "",
        *markdown_table(summary, max_rows=80),
        "",
        "## Usage",
        "",
        "High-confidence rows with `valid_for_training=True` are eligible for symmetry-positive reward. Random controls keep `orbit_confidence=0` and must not enter the symmetry-positive denominator.",
    ]
    return "\n".join(lines) + "\n"


def validate_outputs(rows: pd.DataFrame, variable_rows: pd.DataFrame, document: str | None = None) -> None:
    required_orbit_columns = {
        "family",
        "instance_id",
        "base_instance_id",
        "variant",
        "cnf_path",
        "num_vars",
        "orbit_id",
        "vars",
        "orbit_confidence",
        "valid_for_training",
        "needs_refinement",
        "certification_source",
    }
    missing_orbit_columns = required_orbit_columns.difference(rows.columns)
    if missing_orbit_columns:
        raise ValueError(f"missing orbit columns: {sorted(missing_orbit_columns)}")
    missing_variable_columns = set(VARIABLE_COLUMNS).difference(variable_rows.columns)
    if missing_variable_columns:
        raise ValueError(f"missing variable columns: {sorted(missing_variable_columns)}")
    if rows.empty:
        raise ValueError("orbit certification is empty")

    expected_pairs: set[tuple[str, int]] = set()
    for cnf_path, group in rows.groupby("cnf_path", sort=False, dropna=False):
        num_vars_values = {positive_int(value, "num_vars") for value in group["num_vars"]}
        if len(num_vars_values) != 1:
            raise ValueError(f"conflicting num_vars for cnf_path={cnf_path!r}")
        expected_pairs.update(
            (str(cnf_path), variable_id)
            for variable_id in range(1, next(iter(num_vars_values)) + 1)
        )
    duplicate_count = int(variable_rows.duplicated(["cnf_path", "variable_id"]).sum())
    if duplicate_count:
        raise ValueError(f"duplicate variable rows: {duplicate_count}")
    actual_pairs = set(
        zip(variable_rows["cnf_path"].astype(str), variable_rows["variable_id"].astype(int))
    )
    if actual_pairs != expected_pairs or len(variable_rows) != len(expected_pairs):
        raise ValueError("variable coverage does not match declared num_vars")

    for label in ["valid_for_training", "needs_refinement"]:
        for value in rows[label]:
            strict_bool(value, label)
    for value in rows["orbit_confidence"]:
        bounded_confidence(value)
    for label in ["valid_orbit_mask", "needs_refinement"]:
        for value in variable_rows[label]:
            strict_bool(value, label)
    for value in variable_rows["orbit_confidence"]:
        bounded_confidence(value)

    by_orbit = variable_rows.groupby(["cnf_path", "orbit_id"], dropna=False)["orbit_index"].nunique()
    by_index = variable_rows.groupby(["cnf_path", "orbit_index"], dropna=False)["orbit_id"].nunique()
    if (not by_orbit.empty and int(by_orbit.max()) != 1) or (
        not by_index.empty and int(by_index.max()) != 1
    ):
        raise ValueError("orbit_id and orbit_index are not bijective per CNF")
    random_valid = variable_rows.loc[
        variable_rows["control_type"].astype(str).eq("non_symmetric_control"),
        "valid_orbit_mask",
    ]
    if any(strict_bool(value, "valid_orbit_mask") for value in random_valid):
        raise ValueError("random controls contain valid variable masks")
    if document is not None:
        if not isinstance(document, str) or not document.endswith("\n"):
            raise ValueError("invalid Markdown document")
        required_lines = [
            f"- variable rows: `{len(variable_rows)}`",
            "- full variable coverage: `True`",
            "- duplicate variable rows: `0`",
            "- random-control valid-variable count: `0`",
        ]
        if any(line not in document for line in required_lines):
            raise ValueError("Markdown document is missing certification sanity metrics")


def build_outputs(
    manifest_path: Path,
    out_path: Path,
    variable_out_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    manifest = pd.read_csv(manifest_path)
    all_rows: list[dict[str, Any]] = []
    for _, row in manifest.iterrows():
        all_rows.extend(rows_for_instance(row))
    orbit_sort_columns = [
        "family",
        "base_instance_id",
        "variant",
        "cnf_path",
        "orbit_id",
        "vars",
        "structure_type",
        "certification_source",
        "instance_id",
        "control_type",
        "symmetry_strength",
        "orbits_path",
        "metadata_path",
        "num_vars",
        "scale",
        "benchmark_role",
        "permutation_variant",
        "orbit_size",
        "orbit_confidence",
        "valid_for_training",
        "needs_refinement",
        "notes",
    ]
    rows = pd.DataFrame(all_rows).sort_values(orbit_sort_columns, kind="mergesort").reset_index(drop=True)
    variable_rows = expand_orbit_variables(rows)
    validate_outputs(rows, variable_rows)
    display_out = Path(artifact_path(out_path))
    display_variable_out = Path(artifact_path(variable_out_path))
    display_manifest = Path(artifact_path(manifest_path))
    document = render_doc(
        rows,
        variable_rows,
        display_out,
        display_variable_out,
        display_manifest,
    )
    validate_outputs(rows, variable_rows, document)
    return rows, variable_rows, document


def write_fsynced_temp(target: Path, content: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(content)
        os.fchmod(handle.fileno(), 0o644)
        handle.flush()
        os.fsync(handle.fileno())
        return Path(handle.name)


def create_fsynced_backup(target: Path) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".bak",
        delete=False,
    ) as handle:
        backup = Path(handle.name)
    try:
        shutil.copy2(target, backup)
        with backup.open("rb") as handle:
            os.fsync(handle.fileno())
        return backup
    except BaseException:
        if backup.exists():
            backup.unlink()
        raise


def fsync_directories(paths: list[Path]) -> None:
    for parent in sorted({path.parent for path in paths}, key=lambda path: path.as_posix()):
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


def build_and_publish(
    manifest: Path | str,
    out_csv: Path | str,
    out_variable_csv: Path | str,
    doc: Path | str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    manifest_path = resolve(manifest)
    out_path = resolve(out_csv)
    variable_out_path = resolve(out_variable_csv)
    doc_path = resolve(doc)
    targets = [out_path, variable_out_path, doc_path]
    canonical_targets = [target.resolve() for target in targets]
    if len(set(canonical_targets)) != len(canonical_targets):
        raise ValueError("output paths must be distinct")
    rows, variable_rows, document = build_outputs(manifest_path, out_path, variable_out_path)
    payloads = [
        (out_path, rows.to_csv(index=False, lineterminator="\n").encode("utf-8")),
        (variable_out_path, variable_rows.to_csv(index=False, lineterminator="\n").encode("utf-8")),
        (doc_path, document.encode("utf-8")),
    ]
    temporary_paths: list[tuple[Path, Path]] = []
    backups: dict[Path, Path] = {}
    replaced_targets: set[Path] = set()
    try:
        for target, content in payloads:
            temporary_paths.append((write_fsynced_temp(target, content), target))
        for _, target in temporary_paths:
            if target.exists():
                backups[target] = create_fsynced_backup(target)
        try:
            for temporary, target in temporary_paths:
                os.replace(temporary, target)
                replaced_targets.add(target)
            fsync_directories(targets)
        except BaseException:
            rollback_errors: list[BaseException] = []
            for target in reversed(targets):
                try:
                    backup = backups.get(target)
                    if backup is not None and backup.exists():
                        os.replace(backup, target)
                    elif target in replaced_targets and target.exists():
                        target.unlink()
                except BaseException as rollback_error:
                    rollback_errors.append(rollback_error)
            try:
                fsync_directories(targets)
            except BaseException as rollback_error:
                rollback_errors.append(rollback_error)
            if rollback_errors:
                raise RuntimeError("artifact publication failed and rollback was incomplete") from rollback_errors[0]
            raise
        for backup in backups.values():
            if backup.exists():
                backup.unlink()
    finally:
        for temporary, _ in temporary_paths:
            if temporary.exists():
                temporary.unlink()
        for backup in backups.values():
            if backup.exists():
                backup.unlink()
    return rows, variable_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build EchoSAT orbit certification table from symmetry manifests.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--out-variable-csv", type=Path, default=DEFAULT_VARIABLE_OUT)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows, variable_rows = build_and_publish(
        args.manifest,
        args.out_csv,
        args.out_variable_csv,
        args.doc,
    )
    out_path = resolve(args.out_csv)
    variable_out_path = resolve(args.out_variable_csv)
    print(f"wrote {out_path} rows={len(rows)} bases={rows['base_instance_id'].nunique()}")
    print(f"wrote {variable_out_path} rows={len(variable_rows)}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
