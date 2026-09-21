from __future__ import annotations

import json
import math
import os
import stat
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
from omegaconf import OmegaConf
from torch_geometric.data import HeteroData

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_echosat_orbit_certification as orbit_cert


def certified_variable_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "base_instance_id": "case",
        "variant": "base",
        "variable_id": 1,
        "orbit_index": 0,
        "orbit_size": 2,
        "structure_type": "row_column",
        "orbit_confidence": 0.8,
        "valid_orbit_mask": True,
        "control_type": "strong_symmetry",
    }
    row.update(overrides)
    return row


def orbit_metadata_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "cnf_id": 7,
        "base_instance_id": "case",
        "variant": "base",
        "num_vars": 2,
        "control_type": "strong_symmetry",
    }
    row.update(overrides)
    return row


def orbit_graph(num_vars: int = 2, cnf_id: int = 7) -> HeteroData:
    data = HeteroData()
    data["var"].num_nodes = num_vars
    data["lit"].num_nodes = 2 * num_vars
    data.cnf_id = torch.tensor(cnf_id, dtype=torch.long)
    return data


def orbit_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "family": "php",
        "instance_id": "php-3",
        "base_instance_id": "php-3",
        "variant": "base",
        "cnf_path": "/tmp/php-3.cnf",
        "control_type": "strong_symmetry",
        "symmetry_strength": "strong",
        "num_vars": 3,
        "orbit_id": "pigeons",
        "vars": "1 2 3",
        "orbit_size": 3,
        "structure_type": "row_column",
        "orbit_confidence": 1.0,
        "valid_for_training": True,
        "needs_refinement": False,
        "certification_source": "generator_or_manual_orbit_json",
    }
    row.update(overrides)
    return row


def manifest_row(tmp_path: Path, orbit_text: str, **overrides: object) -> pd.Series:
    cnf = tmp_path / "case.cnf"
    orbits = tmp_path / "case.orbits.json"
    metadata = tmp_path / "case.metadata.json"
    cnf.write_text("p cnf 3 0\n", encoding="utf-8")
    orbits.write_text(orbit_text, encoding="utf-8")
    metadata.write_text("{}\n", encoding="utf-8")
    row: dict[str, object] = {
        "family": "php",
        "instance_id": "case",
        "base_instance_id": "case",
        "variant": "base",
        "num_vars": 3,
        "cnf_path": cnf,
        "orbits_path": orbits,
        "metadata_path": metadata,
        "control_type": "strong_symmetry",
        "symmetry_strength": "strong",
        "permutation_variant": False,
    }
    row.update(overrides)
    return pd.Series(row)


def test_expand_orbit_variables_expands_one_row_per_variable() -> None:
    variables = orbit_cert.expand_orbit_variables(pd.DataFrame([orbit_row(vars="3 1 2")]))

    assert variables["variable_id"].tolist() == [1, 2, 3]
    assert variables["orbit_index"].tolist() == [0, 0, 0]
    assert variables["orbit_id"].tolist() == ["pigeons"] * 3
    assert variables["valid_orbit_mask"].tolist() == [True] * 3


def test_expand_orbit_variables_covers_every_declared_variable_for_every_cnf() -> None:
    orbit_rows = pd.DataFrame(
        [
            orbit_row(cnf_path="/tmp/a.cnf", base_instance_id="a", num_vars=2, vars="1 2"),
            orbit_row(cnf_path="/tmp/b.cnf", base_instance_id="b", num_vars=4, vars="1 2 3 4"),
        ]
    )

    variables = orbit_cert.expand_orbit_variables(orbit_rows)

    assert list(zip(variables["cnf_path"], variables["variable_id"])) == [
        ("/tmp/a.cnf", 1),
        ("/tmp/a.cnf", 2),
        ("/tmp/b.cnf", 1),
        ("/tmp/b.cnf", 2),
        ("/tmp/b.cnf", 3),
        ("/tmp/b.cnf", 4),
    ]


def test_missing_orbit_table_emits_uncertified_rows_for_all_declared_variables(tmp_path: Path) -> None:
    instance = pd.Series(
        {
            "family": "php",
            "instance_id": "missing",
            "base_instance_id": "missing",
            "variant": "base",
            "cnf_path": tmp_path / "missing.cnf",
            "orbits_path": "",
            "control_type": "strong_symmetry",
            "symmetry_strength": "strong",
            "num_vars": 3,
        }
    )

    orbit_rows = pd.DataFrame(orbit_cert.rows_for_instance(instance))
    variables = orbit_cert.expand_orbit_variables(orbit_rows)

    assert orbit_rows.loc[0, "num_vars"] == 3
    assert variables["variable_id"].tolist() == [1, 2, 3]
    assert variables["orbit_confidence"].tolist() == [0.0, 0.0, 0.0]
    assert variables["valid_orbit_mask"].tolist() == [False, False, False]
    assert variables["certification_source"].tolist() == ["missing_orbit_table"] * 3


def test_uncovered_declared_variables_fail_closed_explicitly() -> None:
    variables = orbit_cert.expand_orbit_variables(
        pd.DataFrame([orbit_row(num_vars=4, vars="1 3", orbit_size=2)])
    )

    uncovered = variables[variables["variable_id"].isin([2, 4])]
    assert uncovered["orbit_id"].tolist() == ["uncovered_variable_2", "uncovered_variable_4"]
    assert uncovered["orbit_confidence"].tolist() == [0.0, 0.0]
    assert uncovered["valid_orbit_mask"].tolist() == [False, False]
    assert uncovered["needs_refinement"].tolist() == [True, True]
    assert uncovered["certification_source"].tolist() == ["uncovered_declared_variable"] * 2


def test_random_controls_are_invalidated_even_with_orbit_json() -> None:
    variables = orbit_cert.expand_orbit_variables(
        pd.DataFrame(
            [
                orbit_row(
                    family="random_3sat_control",
                    control_type="non_symmetric_control",
                    symmetry_strength="none",
                )
            ]
        )
    )

    assert variables["orbit_confidence"].tolist() == [0.0, 0.0, 0.0]
    assert variables["valid_orbit_mask"].tolist() == [False, False, False]
    assert variables["certification_source"].tolist() == ["non_symmetric_control"] * 3


def test_duplicate_variable_assignment_is_rejected() -> None:
    orbit_rows = pd.DataFrame(
        [
            orbit_row(orbit_id="first", vars="1 2", orbit_size=2),
            orbit_row(orbit_id="second", vars="2 3", orbit_size=2),
        ]
    )

    with pytest.raises(ValueError, match="duplicate variable assignment.*2"):
        orbit_cert.expand_orbit_variables(orbit_rows)


@pytest.mark.parametrize(
    ("orbit_text", "expected_source"),
    [
        ('{"1":"a","1":"b"}', "orbit_json_schema_error_duplicate_key"),
        ('{"1":"a","01":"a"}', "orbit_json_schema_error_variable_key_alias"),
        ('{"0":"a"}', "orbit_json_schema_error_nonpositive_variable_key"),
        ('{"-1":"a"}', "orbit_json_schema_error_nonpositive_variable_key"),
        ('{"4":"a"}', "orbit_json_schema_error_out_of_range_variable_key"),
        ('{"bad":"a"}', "orbit_json_schema_error_invalid_variable_key"),
        ('{"1":null}', "orbit_json_schema_error_invalid_orbit_id"),
        ('{"1":[]}', "orbit_json_schema_error_invalid_orbit_id"),
        ('{"1":{}}', "orbit_json_schema_error_invalid_orbit_id"),
        ('{"1":3}', "orbit_json_schema_error_invalid_orbit_id"),
        ('{"1":""}', "orbit_json_schema_error_invalid_orbit_id"),
        ('{"1":"   "}', "orbit_json_schema_error_invalid_orbit_id"),
        ('null', "orbit_json_schema_error_invalid_table"),
        ('[]', "orbit_json_schema_error_invalid_table"),
    ],
)
def test_orbit_json_schema_errors_fail_closed_without_aborting_build(
    tmp_path: Path, orbit_text: str, expected_source: str
) -> None:
    orbit_rows = pd.DataFrame(orbit_cert.rows_for_instance(manifest_row(tmp_path, orbit_text)))
    variables = orbit_cert.expand_orbit_variables(orbit_rows)

    assert orbit_rows["certification_source"].tolist() == [expected_source]
    assert variables["variable_id"].tolist() == [1, 2, 3]
    assert variables["valid_orbit_mask"].tolist() == [False, False, False]
    assert variables["orbit_confidence"].tolist() == [0.0, 0.0, 0.0]
    assert variables["certification_source"].tolist() == [expected_source] * 3


def test_orbit_json_accepts_only_canonical_unique_positive_integer_keys(tmp_path: Path) -> None:
    orbit_rows = pd.DataFrame(
        orbit_cert.rows_for_instance(manifest_row(tmp_path, '{"1":" a ","2":"a","3":"b"}'))
    )

    assert orbit_rows["orbit_id"].tolist() == ["a", "b"]
    assert orbit_rows["vars"].tolist() == ["1 2", "3"]


@pytest.mark.parametrize(
    "value",
    [None, pd.NA, 1, 0, "yes", "unknown", object(), [True], {"value": True}],
)
def test_invalid_nullable_boolean_values_are_rejected(value: object) -> None:
    with pytest.raises(ValueError, match="valid_for_training"):
        orbit_cert.expand_orbit_variables(
            pd.DataFrame([orbit_row(valid_for_training=value)])
        )


@pytest.mark.parametrize(
    ("valid_value", "refinement_value", "expected_valid", "expected_refinement"),
    [
        (True, False, True, False),
        (False, True, False, True),
        ("true", "false", True, False),
        (" TRUE ", " FALSE ", True, False),
    ],
)
def test_explicit_boolean_values_are_coerced_strictly(
    valid_value: object,
    refinement_value: object,
    expected_valid: bool,
    expected_refinement: bool,
) -> None:
    variables = orbit_cert.expand_orbit_variables(
        pd.DataFrame(
            [
                orbit_row(
                    valid_for_training=valid_value,
                    needs_refinement=refinement_value,
                )
            ]
        )
    )

    assert variables["valid_orbit_mask"].tolist() == [expected_valid] * 3
    assert variables["needs_refinement"].tolist() == [expected_refinement] * 3


@pytest.mark.parametrize(
    "value",
    [None, pd.NA, math.nan, math.inf, -math.inf, -0.01, 1.01, "bad", object()],
)
def test_invalid_orbit_confidence_is_rejected(value: object) -> None:
    with pytest.raises(ValueError, match="orbit_confidence"):
        orbit_cert.expand_orbit_variables(
            pd.DataFrame([orbit_row(orbit_confidence=value)])
        )


def test_numeric_string_orbit_confidence_is_accepted() -> None:
    variables = orbit_cert.expand_orbit_variables(
        pd.DataFrame([orbit_row(orbit_confidence="0.6")])
    )

    assert variables["orbit_confidence"].tolist() == [0.6, 0.6, 0.6]


def test_scalar_validation_applies_to_empty_orbit_rows() -> None:
    with pytest.raises(ValueError, match="orbit_confidence"):
        orbit_cert.expand_orbit_variables(
            pd.DataFrame([orbit_row(vars="", orbit_size=0, orbit_confidence=pd.NA)])
        )


@pytest.mark.parametrize("bad_vars", ["1 bad 3", "1 4"])
def test_malformed_or_out_of_range_variables_fail_closed(bad_vars: str) -> None:
    variables = orbit_cert.expand_orbit_variables(
        pd.DataFrame([orbit_row(vars=bad_vars, orbit_size=3)])
    )

    assert variables["variable_id"].tolist() == [1, 2, 3]
    assert variables["orbit_confidence"].tolist() == [0.0, 0.0, 0.0]
    assert variables["valid_orbit_mask"].tolist() == [False, False, False]
    assert variables["needs_refinement"].tolist() == [True, True, True]
    assert variables["certification_source"].nunique() == 1
    assert variables["certification_source"].iloc[0] in {
        "malformed_orbit_variables",
        "out_of_range_orbit_variable",
    }


@pytest.mark.parametrize(
    ("num_vars", "vars_value"),
    [(0, ""), (-1, ""), ("bad", ""), (3, "0 1"), (3, "-1 1")],
)
def test_invalid_num_vars_and_nonpositive_variable_ids_are_rejected(
    num_vars: object, vars_value: str
) -> None:
    with pytest.raises(ValueError):
        orbit_cert.expand_orbit_variables(
            pd.DataFrame([orbit_row(num_vars=num_vars, vars=vars_value)])
        )


@pytest.mark.parametrize(
    "value",
    [True, np.bool_(True), np.float64(1.5), np.float64(np.nan), pd.NA],
)
def test_num_vars_rejects_boolean_nonintegral_and_missing_scalars(value: object) -> None:
    with pytest.raises(ValueError, match="num_vars"):
        orbit_cert.positive_int(value, "num_vars")


def test_num_vars_accepts_numpy_integer_scalar() -> None:
    assert orbit_cert.positive_int(np.int64(3), "num_vars") == 3


@pytest.mark.parametrize(
    "value",
    [True, np.bool_(True), np.float64(1.5), np.float64(np.nan), pd.NA],
)
def test_parse_variable_ids_rejects_boolean_nonintegral_and_missing_tokens(value: object) -> None:
    with pytest.raises(ValueError, match="variable_id"):
        orbit_cert.parse_variable_ids([value])


def test_parse_variable_ids_accepts_numpy_integer_and_integral_float_scalars() -> None:
    assert orbit_cert.parse_variable_ids([np.int64(1), np.float64(2.0), "3"]) == [1, 2, 3]


def test_orbit_indices_and_output_order_are_deterministic() -> None:
    orbit_rows = pd.DataFrame(
        [
            orbit_row(
                family="z_family",
                cnf_path="/tmp/z.cnf",
                base_instance_id="z",
                orbit_id="orbit-b",
                vars="3 1",
                orbit_size=2,
            ),
            orbit_row(
                family="a_family",
                cnf_path="/tmp/a.cnf",
                base_instance_id="a",
                orbit_id="orbit-a",
                vars="2",
                orbit_size=1,
            ),
        ]
    )

    first = orbit_cert.expand_orbit_variables(orbit_rows.sample(frac=1, random_state=1))
    second = orbit_cert.expand_orbit_variables(orbit_rows.sample(frac=1, random_state=2))

    pd.testing.assert_frame_equal(first, second)
    assert list(zip(first["cnf_path"], first["variable_id"])) == [
        ("/tmp/a.cnf", 1),
        ("/tmp/a.cnf", 2),
        ("/tmp/a.cnf", 3),
        ("/tmp/z.cnf", 1),
        ("/tmp/z.cnf", 2),
        ("/tmp/z.cnf", 3),
    ]
    z_rows = first[first["cnf_path"].eq("/tmp/z.cnf")]
    assert z_rows.loc[z_rows["variable_id"].isin([1, 3]), "orbit_index"].tolist() == [0, 0]


def test_orbit_id_and_orbit_index_are_bijective_with_uncertified_singletons() -> None:
    variables = orbit_cert.expand_orbit_variables(
        pd.DataFrame(
            [
                orbit_row(orbit_id="orbit-b", vars="3 4", orbit_size=2, num_vars=6),
                orbit_row(orbit_id="orbit-a", vars="1 2", orbit_size=2, num_vars=6),
            ]
        )
    )

    by_orbit = variables.groupby(["cnf_path", "orbit_id"])["orbit_index"].nunique()
    by_index = variables.groupby(["cnf_path", "orbit_index"])["orbit_id"].nunique()
    assert by_orbit.max() == 1
    assert by_index.max() == 1
    assert variables.loc[variables["orbit_id"].eq("orbit-a"), "orbit_index"].unique().tolist() == [0]
    assert variables.loc[variables["orbit_id"].eq("orbit-b"), "orbit_index"].unique().tolist() == [1]
    assert variables.loc[variables["variable_id"].isin([5, 6]), "orbit_index"].tolist() == [2, 3]


def test_complete_orbit_row_tie_breakers_make_schema_failure_deterministic() -> None:
    orbit_rows = pd.DataFrame(
        [
            orbit_row(orbit_id="same", vars="bad"),
            orbit_row(orbit_id="same", vars="4"),
        ]
    )

    first = orbit_cert.expand_orbit_variables(orbit_rows.sample(frac=1, random_state=1))
    second = orbit_cert.expand_orbit_variables(orbit_rows.sample(frac=1, random_state=2))

    pd.testing.assert_frame_equal(first, second)
    assert first["certification_source"].tolist() == ["out_of_range_orbit_variable"] * 3


def test_resolve_maps_missing_legacy_my_rlaf_paths_to_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(orbit_cert, "ROOT", tmp_path)
    local = tmp_path / "data" / "case.cnf"
    local.parent.mkdir()
    local.write_text("p cnf 1 0\n", encoding="utf-8")
    existing_absolute = tmp_path / "already-local.cnf"
    existing_absolute.write_text("p cnf 1 0\n", encoding="utf-8")

    assert orbit_cert.resolve("/home/old/my_rlaf/data/case.cnf") == local
    assert orbit_cert.resolve(existing_absolute) == existing_absolute
    assert orbit_cert.resolve("data/case.cnf") == local


def test_rows_for_instance_emits_repo_relative_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(orbit_cert, "ROOT", tmp_path)
    row = manifest_row(tmp_path, '{"1":"all","2":"all","3":"all"}')

    orbit_rows = pd.DataFrame(orbit_cert.rows_for_instance(row))

    assert orbit_rows["cnf_path"].tolist() == ["case.cnf"]
    assert orbit_rows["orbits_path"].tolist() == ["case.orbits.json"]
    assert orbit_rows["metadata_path"].tolist() == ["case.metadata.json"]


def test_cli_defaults_are_consistently_v2() -> None:
    assert orbit_cert.DEFAULT_MANIFEST == orbit_cert.ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv"
    assert orbit_cert.DEFAULT_OUT == orbit_cert.ROOT / "runs/analysis/echosat_v2_orbit_certification.csv"
    assert orbit_cert.DEFAULT_VARIABLE_OUT == orbit_cert.ROOT / "runs/analysis/echosat_v2_orbit_variables.csv"
    assert orbit_cert.DEFAULT_DOC == orbit_cert.ROOT / "docs/echosat_v2_orbit_certification.md"


@pytest.mark.parametrize("failure_phase", ["expansion", "validation", "documentation"])
def test_build_failure_preserves_all_preexisting_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_phase: str,
) -> None:
    row = manifest_row(tmp_path, '{"1":"all","2":"all","3":"all"}')
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([row]).to_csv(manifest, index=False)
    orbit_csv = tmp_path / "orbit.csv"
    variable_csv = tmp_path / "variables.csv"
    doc = tmp_path / "certification.md"
    originals = {
        orbit_csv: b"old orbit\n",
        variable_csv: b"old variables\n",
        doc: b"old doc\n",
    }
    for path, content in originals.items():
        path.write_bytes(content)

    target = {
        "expansion": "expand_orbit_variables",
        "validation": "validate_outputs",
        "documentation": "render_doc",
    }[failure_phase]

    def fail(*args: object, **kwargs: object) -> object:
        raise RuntimeError(f"forced {failure_phase} failure")

    monkeypatch.setattr(orbit_cert, target, fail)

    with pytest.raises(RuntimeError, match=failure_phase):
        orbit_cert.build_and_publish(manifest, orbit_csv, variable_csv, doc)

    assert {path: path.read_bytes() for path in originals} == originals
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("failed_replace", [2, 3])
def test_publication_replace_failure_restores_all_existing_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_replace: int,
) -> None:
    row = manifest_row(tmp_path, '{"1":"all","2":"all","3":"all"}')
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([row]).to_csv(manifest, index=False)
    orbit_csv = tmp_path / "orbit.csv"
    variable_csv = tmp_path / "variables.csv"
    doc = tmp_path / "certification.md"
    originals = {
        orbit_csv: (b"old orbit\n", 0o640),
        variable_csv: (b"old variables\n", 0o600),
        doc: (b"old doc\n", 0o644),
    }
    for path, (content, mode) in originals.items():
        path.write_bytes(content)
        path.chmod(mode)

    real_replace = os.replace
    replace_count = 0

    def injected_replace(source: Path | str, target: Path | str) -> None:
        nonlocal replace_count
        replace_count += 1
        if replace_count == failed_replace:
            raise OSError(f"forced replace {failed_replace} failure")
        real_replace(source, target)

    monkeypatch.setattr(orbit_cert.os, "replace", injected_replace)

    with pytest.raises(OSError, match=f"replace {failed_replace}"):
        orbit_cert.build_and_publish(manifest, orbit_csv, variable_csv, doc)

    for path, (content, mode) in originals.items():
        assert path.read_bytes() == content
        assert stat.S_IMODE(path.stat().st_mode) == mode
    assert not list(tmp_path.glob(".*.tmp"))
    assert not list(tmp_path.glob(".*.bak"))


def test_duplicate_output_paths_are_rejected_before_publication(tmp_path: Path) -> None:
    row = manifest_row(tmp_path, '{"1":"all","2":"all","3":"all"}')
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([row]).to_csv(manifest, index=False)
    shared = tmp_path / "shared.out"
    doc = tmp_path / "certification.md"
    shared.write_bytes(b"unchanged shared\n")
    doc.write_bytes(b"unchanged doc\n")

    with pytest.raises(ValueError, match="distinct"):
        orbit_cert.build_and_publish(manifest, shared, shared, doc)

    assert shared.read_bytes() == b"unchanged shared\n"
    assert doc.read_bytes() == b"unchanged doc\n"


def test_successful_publication_sets_all_artifacts_to_mode_0644(tmp_path: Path) -> None:
    row = manifest_row(tmp_path, '{"1":"all","2":"all","3":"all"}')
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([row]).to_csv(manifest, index=False)
    outputs = [tmp_path / "orbit.csv", tmp_path / "variables.csv", tmp_path / "certification.md"]

    orbit_cert.build_and_publish(manifest, *outputs)

    assert [stat.S_IMODE(path.stat().st_mode) for path in outputs] == [0o644, 0o644, 0o644]


def test_cli_writes_orbit_and_variable_csvs(tmp_path: Path) -> None:
    cnf = tmp_path / "case.cnf"
    orbit_json = tmp_path / "case.orbits.json"
    metadata = tmp_path / "case.metadata.json"
    manifest = tmp_path / "manifest.csv"
    orbit_csv = tmp_path / "orbit.csv"
    variable_csv = tmp_path / "variables.csv"
    doc = tmp_path / "certification.md"
    cnf.write_text("p cnf 3 0\n", encoding="utf-8")
    orbit_json.write_text(json.dumps({"1": "all", "2": "all", "3": "all"}), encoding="utf-8")
    metadata.write_text("{}\n", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "family": "php",
                "instance_id": "case",
                "base_instance_id": "case",
                "variant": "base",
                "num_vars": 3,
                "cnf_path": cnf,
                "orbits_path": orbit_json,
                "metadata_path": metadata,
                "control_type": "strong_symmetry",
                "symmetry_strength": "strong",
            }
        ]
    ).to_csv(manifest, index=False)

    result = subprocess.run(
        [
            sys.executable,
            str(Path(orbit_cert.__file__)),
            "--manifest",
            str(manifest),
            "--out-csv",
            str(orbit_csv),
            "--out-variable-csv",
            str(variable_csv),
            "--doc",
            str(doc),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert len(pd.read_csv(orbit_csv)) == 1
    assert len(pd.read_csv(variable_csv)) == 3
    assert "variable rows: `3`" in doc.read_text(encoding="utf-8")
    assert orbit_csv.read_text(encoding="utf-8").splitlines()[0] == (
        "family,instance_id,base_instance_id,variant,cnf_path,orbits_path,metadata_path,"
        "control_type,symmetry_strength,num_vars,scale,benchmark_role,permutation_variant,"
        "orbit_id,vars,orbit_size,structure_type,certification_source,orbit_confidence,"
        "valid_for_training,needs_refinement,notes"
    )
    assert variable_csv.read_text(encoding="utf-8").splitlines()[0] == ",".join(
        orbit_cert.VARIABLE_COLUMNS
    )

    first_bytes = {
        orbit_csv: orbit_csv.read_bytes(),
        variable_csv: variable_csv.read_bytes(),
        doc: doc.read_bytes(),
    }
    second = subprocess.run(result.args, check=False, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    assert {path: path.read_bytes() for path in first_bytes} == first_bytes


def test_orbit_feature_store_validates_and_returns_deterministic_rows() -> None:
    from src.echosat.orbit_features import OrbitFeatureStore

    variable_rows = pd.DataFrame(
        [certified_variable_row(variable_id=2), certified_variable_row(variable_id=1)]
    )
    store = OrbitFeatureStore.from_tables(variable_rows, pd.DataFrame([orbit_metadata_row()]))

    rows = store.rows_for(7)

    assert rows is not None
    assert rows["variable_id"].tolist() == [1, 2]
    assert rows["cnf_id"].tolist() == [7, 7]
    assert store.rows_for(999) is None


@pytest.mark.parametrize(
    ("variable_rows", "metadata", "message"),
    [
        (pd.DataFrame([certified_variable_row()]), pd.DataFrame([orbit_metadata_row(), orbit_metadata_row(cnf_id=8)]), "duplicate metadata key"),
        (pd.DataFrame([certified_variable_row()]), pd.DataFrame([orbit_metadata_row(), orbit_metadata_row(base_instance_id="other")]), "duplicate cnf_id"),
        (pd.DataFrame([certified_variable_row(), certified_variable_row()]), pd.DataFrame([orbit_metadata_row(num_vars=1)]), "duplicate variable_id"),
        (pd.DataFrame([certified_variable_row()]).drop(columns=["orbit_size"]), pd.DataFrame([orbit_metadata_row(num_vars=1)]), "missing required columns"),
        (pd.DataFrame([certified_variable_row(variable_id=1)]), pd.DataFrame([orbit_metadata_row(num_vars=2)]), "cover variable IDs 1..2"),
        (pd.DataFrame([certified_variable_row(orbit_size=1)]), pd.DataFrame([orbit_metadata_row(num_vars=1), orbit_metadata_row(cnf_id=8, base_instance_id="missing", num_vars=1)]), "cnf_id=8"),
    ],
)
def test_orbit_feature_store_rejects_invalid_tables(variable_rows: pd.DataFrame, metadata: pd.DataFrame, message: str) -> None:
    from src.echosat.orbit_features import OrbitFeatureStore

    with pytest.raises(ValueError, match=message):
        OrbitFeatureStore.from_tables(variable_rows, metadata)


def test_orbit_feature_store_keeps_random_controls_invalid() -> None:
    from src.echosat.orbit_features import OrbitFeatureStore

    variable_rows = pd.DataFrame([certified_variable_row(variable_id=1, control_type="non_symmetric_control", orbit_confidence=1.0, valid_orbit_mask=True, structure_type="none")])
    metadata = pd.DataFrame([orbit_metadata_row(num_vars=1, control_type="non_symmetric_control")])

    rows = OrbitFeatureStore.from_tables(variable_rows, metadata).rows_for(7)

    assert rows is not None
    assert rows["valid_orbit_mask"].tolist() == [False]
    assert rows["orbit_confidence"].tolist() == [0.0]


def test_orbit_feature_store_rejects_uncovered_metadata_without_num_vars() -> None:
    from src.echosat.orbit_features import OrbitFeatureStore

    variable_rows = pd.DataFrame([certified_variable_row(orbit_size=1)])
    metadata = pd.DataFrame(
        [
            orbit_metadata_row(num_vars=None),
            orbit_metadata_row(cnf_id=8, base_instance_id="missing", num_vars=None),
        ]
    ).drop(columns=["num_vars"])

    with pytest.raises(ValueError, match="cnf_id=8"):
        OrbitFeatureStore.from_tables(variable_rows, metadata)


@pytest.mark.parametrize("structure_type", ["unknown", "row_column", "bandwidth_cardinality", "grid_or_torus", "graph_coloring", "complete_graph_parity", "none"])
def test_actual_structure_categories_have_stable_one_hot_mapping(structure_type: str) -> None:
    from src.echosat.orbit_features import STRUCTURE_CATEGORIES, attach_orbit_features

    rows = pd.DataFrame([certified_variable_row(variable_id=1, orbit_size=1, structure_type=structure_type)])
    attached = attach_orbit_features(orbit_graph(num_vars=1), rows)

    expected_index = STRUCTURE_CATEGORIES.index(structure_type)
    assert attached["var"].structure_one_hot.shape == (1, len(STRUCTURE_CATEGORIES))
    assert attached["var"].structure_one_hot[0, expected_index].item() == 1.0
    assert attached["var"].structure_one_hot.sum().item() == 1.0


def test_unknown_structure_value_emits_diagnostic_before_mapping_to_unknown() -> None:
    from src.echosat.orbit_features import attach_orbit_features

    rows = pd.DataFrame([certified_variable_row(variable_id=1, orbit_size=1, structure_type="legacy_name")])

    with pytest.warns(UserWarning, match="unknown structure_type"):
        attached = attach_orbit_features(orbit_graph(num_vars=1), rows)

    assert attached["var"].structure_one_hot[0, 0].item() == 1.0


def test_attach_orbit_features_attaches_complete_certified_features_without_mutation() -> None:
    from src.echosat.orbit_features import attach_orbit_features

    data = orbit_graph(num_vars=2)
    rows = pd.DataFrame([certified_variable_row(variable_id=2, orbit_index=0, orbit_size=2, orbit_confidence=0.8), certified_variable_row(variable_id=1, orbit_index=0, orbit_size=2, orbit_confidence=0.8)])

    attached = attach_orbit_features(data, rows)

    assert attached is not data
    assert not hasattr(data["var"], "orbit_features")
    assert attached["var"].orbit_index.tolist() == [0, 0]
    assert torch.allclose(attached["var"].log1p_orbit_size, torch.full((2,), math.log(3.0)))
    assert torch.equal(attached["var"].orbit_size_log1p, attached["var"].log1p_orbit_size)
    assert torch.allclose(attached["var"].orbit_confidence, torch.tensor([0.8, 0.8]))
    assert attached["var"].valid_orbit_mask.tolist() == [True, True]
    assert torch.equal(attached["var"].orbit_structure_one_hot, attached["var"].structure_one_hot)
    assert attached["var"].orbit_features.shape == (2, 10)


def test_attach_orbit_features_missing_rows_fails_closed() -> None:
    from src.echosat.orbit_features import attach_orbit_features

    attached = attach_orbit_features(orbit_graph(num_vars=3), None)

    assert attached["var"].valid_orbit_mask.tolist() == [False, False, False]
    assert attached["var"].orbit_confidence.tolist() == [0.0, 0.0, 0.0]
    assert attached["var"].structure_one_hot[:, 0].tolist() == [1.0, 1.0, 1.0]
    assert attached.valid_orbit_count.item() == 0.0
    assert attached.valid_orbit_variable_fraction.item() == 0.0


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (pd.DataFrame([certified_variable_row(variable_id=1)]), "cover variable IDs 1..2"),
        (pd.DataFrame([certified_variable_row(variable_id=1), certified_variable_row(variable_id=1)]), "duplicate variable_id"),
        (pd.DataFrame([certified_variable_row(variable_id=1), certified_variable_row(variable_id=3)]), "out of range"),
        (pd.DataFrame([certified_variable_row(variable_id=1), certified_variable_row(variable_id=2, orbit_confidence=float("nan"))]), "nonfinite"),
        (pd.DataFrame([certified_variable_row(variable_id=1, orbit_size=3), certified_variable_row(variable_id=2, orbit_size=3)]), "orbit_size"),
    ],
)
def test_attach_orbit_features_rejects_uncertified_partial_rows(rows: pd.DataFrame, message: str) -> None:
    from src.echosat.orbit_features import attach_orbit_features

    with pytest.raises(ValueError, match=message):
        attach_orbit_features(orbit_graph(num_vars=2), rows)


def test_attach_orbit_features_rejects_inconsistent_confidence_within_valid_orbit() -> None:
    from src.echosat.orbit_features import attach_orbit_features

    rows = pd.DataFrame(
        [
            certified_variable_row(variable_id=1, orbit_index=0, orbit_size=2, orbit_confidence=0.6),
            certified_variable_row(variable_id=2, orbit_index=0, orbit_size=2, orbit_confidence=0.8),
        ]
    )

    with pytest.raises(ValueError, match="inconsistent orbit_confidence"):
        attach_orbit_features(orbit_graph(num_vars=2), rows)


def test_orbit_relative_ranks_are_tie_aware_and_permutation_equivariant() -> None:
    from src.echosat.orbit_features import orbit_relative_event_features

    event_state = torch.tensor([[1.0], [1.0], [3.0], [9.0]])
    orbit_index = torch.tensor([4, 4, 4, 8])
    valid_mask = torch.tensor([True, True, True, False])
    features = orbit_relative_event_features(event_state, orbit_index, valid_mask)

    assert torch.allclose(features[:3, 0], torch.tensor([0.25, 0.25, 1.0]))
    assert torch.equal(features[3], torch.zeros(5))

    permutation = torch.tensor([2, 0, 3, 1])
    inverse = torch.argsort(permutation)
    permuted = orbit_relative_event_features(event_state[permutation], orbit_index[permutation], valid_mask[permutation])
    assert torch.allclose(permuted[inverse], features)


def test_orbit_relative_event_features_support_multiple_channels() -> None:
    from src.echosat.orbit_features import orbit_relative_event_features

    event_state = torch.tensor([[0.0, 2.0], [2.0, -2.0]])
    features = orbit_relative_event_features(event_state, torch.tensor([0, 0]), torch.tensor([True, True]))

    assert features.shape == (2, 10)
    assert torch.allclose(features[:, 0:5], torch.tensor([[0.0, -1.0, 0.0, 1.0, 0.5], [1.0, 1.0, 1.0, 1.0, 0.5]]))
    assert torch.allclose(features[:, 5:10], torch.tensor([[1.0, 1.0, 0.5, 4.0, 1.0], [0.0, -1.0, -0.5, 4.0, 1.0]]))


def test_orbit_relative_event_share_preserves_sign_and_device() -> None:
    from src.echosat.orbit_features import orbit_relative_event_features

    event_state = torch.tensor([[-2.0], [1.0]])
    features = orbit_relative_event_features(
        event_state,
        torch.tensor([0, 0]),
        torch.tensor([True, True]),
    )

    assert features.device == event_state.device
    assert torch.allclose(features[:, 2], torch.tensor([-2.0 / 3.0, 1.0 / 3.0]))


def test_orbit_relative_event_features_define_singletons_and_zero_orbits() -> None:
    from src.echosat.orbit_features import orbit_relative_event_features

    features = orbit_relative_event_features(torch.tensor([[5.0], [0.0], [0.0]]), torch.tensor([0, 1, 1]), torch.tensor([True, True, True]))

    assert torch.allclose(features[0], torch.tensor([0.0, 0.0, 1.0, 0.0, 1.0]))
    assert torch.equal(features[1:, 0:4], torch.zeros((2, 4)))
    assert torch.equal(features[1:, 4], torch.zeros(2))


@pytest.mark.parametrize(
    ("event_state", "orbit_index", "valid_mask", "message"),
    [
        (torch.ones(2), torch.tensor([0, 0]), torch.tensor([True, True]), "two-dimensional"),
        (torch.ones((2, 1), dtype=torch.long), torch.tensor([0, 0]), torch.tensor([True, True]), "floating"),
        (torch.tensor([[float("nan")], [0.0]]), torch.tensor([0, 0]), torch.tensor([True, True]), "nonfinite"),
        (torch.ones((2, 1)), torch.tensor([0.0, 0.0]), torch.tensor([True, True]), "integer"),
        (torch.ones((2, 1)), torch.tensor([0, 0]), torch.tensor([1, 1]), "bool"),
        (torch.ones((2, 1)), torch.tensor([0]), torch.tensor([True, True]), "length"),
    ],
)
def test_orbit_relative_event_features_validate_inputs(event_state: torch.Tensor, orbit_index: torch.Tensor, valid_mask: torch.Tensor, message: str) -> None:
    from src.echosat.orbit_features import orbit_relative_event_features

    with pytest.raises((TypeError, ValueError), match=message):
        orbit_relative_event_features(event_state, orbit_index, valid_mask)


def test_attach_orbit_features_exposes_graph_and_event_evidence() -> None:
    from src.echosat.orbit_features import attach_orbit_features

    data = orbit_graph(num_vars=4)
    data["var"].event_state = torch.tensor([[0.0], [2.0], [3.0], [9.0]])
    rows = pd.DataFrame([
        certified_variable_row(variable_id=1, orbit_index=0, orbit_size=2, orbit_confidence=0.6),
        certified_variable_row(variable_id=2, orbit_index=0, orbit_size=2, orbit_confidence=0.6),
        certified_variable_row(variable_id=3, orbit_index=1, orbit_size=1, orbit_confidence=1.0),
        certified_variable_row(variable_id=4, orbit_index=2, orbit_size=1, orbit_confidence=0.0, valid_orbit_mask=False),
    ])

    attached = attach_orbit_features(data, rows)

    assert attached.valid_orbit_count.item() == 2.0
    assert attached.valid_orbit_variable_fraction.item() == pytest.approx(0.75)
    assert attached.mean_orbit_confidence.item() == pytest.approx((0.6 + 1.0) / 2.0)
    assert attached.event_active_orbit_fraction.item() == 1.0
    assert attached.mean_orbit_event_variance.item() == pytest.approx(0.5)
    assert attached["var"].orbit_event_state.shape == (4, 5)
    assert torch.allclose(attached["var"].orbit_event_variance[:, 0], torch.tensor([1.0, 1.0, 0.0, 0.0]))
    assert torch.equal(attached["var"].orbit_event_state[3], torch.zeros(5))


def test_attach_echosat_v2_orbits_updates_each_graph_and_missing_store_fails_closed() -> None:
    from src.echosat.orbit_features import OrbitFeatureStore
    from train_rlaf import attach_echosat_v2_orbits

    store = OrbitFeatureStore.from_tables(pd.DataFrame([certified_variable_row(variable_id=1), certified_variable_row(variable_id=2)]), pd.DataFrame([orbit_metadata_row()]))

    attached = attach_echosat_v2_orbits([orbit_graph()], store)
    missing = attach_echosat_v2_orbits([orbit_graph(cnf_id=99)], store)

    assert attached[0]["var"].valid_orbit_mask.tolist() == [True, True]
    assert missing[0]["var"].valid_orbit_mask.tolist() == [False, False]


def test_orbit_store_configuration_is_opt_in_and_legacy_mode_is_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import train_rlaf

    metadata = pd.DataFrame([orbit_metadata_row()])
    blank_cfg = OmegaConf.create({"training": {"echosat_orbit_variable_path": ""}})
    monkeypatch.setattr(pd, "read_csv", lambda *_args, **_kwargs: pytest.fail("must not read"))
    assert train_rlaf.load_echosat_v2_orbit_store(blank_cfg, metadata) is None

    loader = object()
    legacy_cfg = OmegaConf.create({"training": {"feedback_input_mode": "none"}})
    assert train_rlaf.build_feedback_state_loader(model=object(), dataset=object(), loader=loader, cfg=legacy_cfg, device="cpu", orbit_store=object()) is loader


def test_configured_orbit_store_loads_variable_rows_and_merges_dataset_metadata(tmp_path: Path) -> None:
    import train_rlaf

    variable_path = tmp_path / "orbit_variables.csv"
    pd.DataFrame([certified_variable_row(variable_id=1), certified_variable_row(variable_id=2), certified_variable_row(base_instance_id="unused", variable_id=1)]).to_csv(variable_path, index=False)
    cfg = OmegaConf.create({"training": {"echosat_orbit_variable_path": str(variable_path)}})

    store = train_rlaf.load_echosat_v2_orbit_store(cfg, pd.DataFrame([orbit_metadata_row()]))

    assert store is not None
    assert store.rows_for(7)["variable_id"].tolist() == [1, 2]


def test_configured_orbit_store_rejects_uncovered_dataset_metadata_without_num_vars(tmp_path: Path) -> None:
    import train_rlaf

    variable_path = tmp_path / "orbit_variables.csv"
    pd.DataFrame([certified_variable_row(orbit_size=1)]).to_csv(variable_path, index=False)
    cfg = OmegaConf.create({"training": {"echosat_orbit_variable_path": str(variable_path)}})
    metadata = pd.DataFrame(
        [
            orbit_metadata_row(num_vars=None),
            orbit_metadata_row(cnf_id=8, base_instance_id="missing", num_vars=None),
        ]
    ).drop(columns=["num_vars"])

    with pytest.raises(ValueError, match="uncovered dataset metadata"):
        train_rlaf.load_echosat_v2_orbit_store(cfg, metadata)


@pytest.mark.parametrize(
    ("stats", "expected"),
    [
        (
            {"CPU time": 2.0, "conflicts": 4.0, "propagations": 10.0, "decisions": 3.0},
            {"cpu": 2.0, "conflicts": 4.0, "propagations": 10.0, "decisions": 3.0, "conflict_rate": 2.0, "propagation_rate": 5.0},
        ),
        (
            {"CPU time": 0.0, "conflicts": 4.0, "propagations": 10.0},
            {"cpu": 0.0, "conflicts": 4.0, "propagations": 10.0, "decisions": 0.0, "conflict_rate": 0.0, "propagation_rate": 0.0},
        ),
        (
            {"CPU time": 5.0e-7, "conflicts": 4.0, "propagations": 10.0},
            {"cpu": 5.0e-7, "conflicts": 4.0, "propagations": 10.0, "decisions": 0.0, "conflict_rate": 0.0, "propagation_rate": 0.0},
        ),
        (
            {},
            {"cpu": 0.0, "conflicts": 0.0, "propagations": 0.0, "decisions": 0.0, "conflict_rate": 0.0, "propagation_rate": 0.0},
        ),
        (
            {"CPU time": float("nan"), "conflicts": float("inf"), "propagations": -1.0, "decisions": float("nan")},
            {"cpu": 0.0, "conflicts": 0.0, "propagations": 0.0, "decisions": 0.0, "conflict_rate": 0.0, "propagation_rate": 0.0},
        ),
    ],
)
def test_attach_warmup_graph_evidence_is_finite_and_fail_closed(
    stats: dict[str, float],
    expected: dict[str, float],
) -> None:
    from src.echosat.orbit_features import attach_orbit_features
    from train_rlaf import attach_warmup_graph_evidence

    graph = attach_orbit_features(orbit_graph(num_vars=1), None)
    attached = attach_warmup_graph_evidence(graph, stats)

    assert attached.warmup_cpu_time.item() == pytest.approx(expected["cpu"])
    assert attached.warmup_conflicts.item() == pytest.approx(expected["conflicts"])
    assert attached.warmup_propagations.item() == pytest.approx(expected["propagations"])
    assert attached.warmup_decisions.item() == pytest.approx(expected["decisions"])
    assert attached.warmup_conflict_rate.item() == pytest.approx(expected["conflict_rate"])
    assert attached.warmup_propagation_rate.item() == pytest.approx(expected["propagation_rate"])
    evidence_names = [
        "valid_orbit_count",
        "valid_orbit_variable_fraction",
        "mean_orbit_confidence",
        "event_active_orbit_fraction",
        "mean_orbit_event_variance",
        "warmup_conflict_rate",
        "warmup_propagation_rate",
    ]
    assert all(hasattr(attached, name) for name in evidence_names)
    assert all(torch.isfinite(getattr(attached, name)).all() for name in evidence_names)
