import json
import tempfile
import threading
import unittest
import os
import inspect
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import torch
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from replay_echosat_v2_objective import build_checks, main as replay_main
from train_rlaf import (
    REPLAY_ONLY_LOG,
    _remove_owned_run_marker,
    build_validation_runtime,
    build_training_optimizer_scheduler,
    completed_iteration_checkpoint_name,
    dataset_path_from_config,
    dataset_metadata,
    load_manifest_from_path,
    load_orbit_certification_summary,
    load_training_manifest,
    load_training_model,
    model_updates_enabled,
    replay_artifacts_before_update,
    run_training_update_after_replay_artifacts,
    save_model,
    main as train_main,
    resolve_manifest_artifact_path,
    validate_replay_only_config,
    validate_training_output_directory,
    write_echosat_reward_replay_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC_CHECK_NAMES = [
    "blocked_rows_non_positive",
    "eligible_positive_exists",
    "all_v2_stage4_checks",
]


def _rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "base_instance_id": ["base-a", "base-a"],
            "variant": ["base", "perm"],
            "v2_positive_eligible": [True, False],
            "grpo_final_advantage": [0.5, 0.0],
        }
    )


def _attribution_rows() -> pd.DataFrame:
    rows = pd.DataFrame(
        {
            "base_instance_id": ["base-b", "base-a", "base-a", "base-a"],
            "variant": ["zeta", "beta", "alpha", "beta"],
            "v2_positive_eligible": [False, True, False, False],
            "v2_variant_positive_capable": [False, True, False, True],
            "v2_variant_hard_blocked": [True, False, False, False],
            "worst_variant_score": [-1.5, -0.25, -0.25, -0.25],
            "grpo_final_advantage": [0.0, 0.5, 0.0, 0.0],
            "v2_control_blocked": [True, False, False, False],
            "v2_plain_result_mismatch": [False, False, False, False],
            "v2_static_result_mismatch": [False, False, False, False],
            "v2_plain_solved_guided_unsolved": [False, False, False, False],
            "v2_static_solved_guided_unsolved": [False, False, False, False],
            "v2_plain_unsolved": [False, False, False, False],
            "v2_static_unsolved": [False, False, False, False],
            "v2_missing_plain_baseline": [False, False, False, False],
            "v2_missing_static_baseline": [False, False, False, False],
            "v2_invalid_static_baseline": [False, False, False, False],
            "v2_near_cap": [False, False, False, False],
            "v2_weighted_risk": [True, False, True, False],
            "v2_valid_symmetry_orbit_evidence": [True, True, True, True],
            "v2_hard_safety_blocked": [True, False, False, False],
        }
    )
    return rows


def _replay_cfg(*, replay_only: bool = True, save_replay: bool = True, steps: int = 0):
    return OmegaConf.create(
        {
            "method": "grpo",
            "ckpt_interval": None,
            "skip_initial_val": True,
            "model_dir": "runs/test",
            "training": {
                "echosat_replay_only": replay_only,
                "echosat_target_mode": "symmetry_grpo_v2",
                "save_echosat_reward_replay": save_replay,
                "steps_per_iter": steps,
            }
        }
    )


def _core_model() -> Mock:
    model = Mock()
    model.state_dict.return_value = {
        "lit_enc.mlp.0.weight": torch.zeros(1),
        "cls_enc.mlp.0.weight": torch.zeros(1),
        "layers.0.mlp.weight": torch.zeros(1),
        "out_lin1.weight": torch.zeros(1),
        "out_lin2.weight": torch.zeros(1),
        "event_adapter.0.weight": torch.zeros(1),
    }
    return model


def _write_file(path: Path, text: str = "artifact") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class ManifestPortablePathTests(unittest.TestCase):
    def test_manifest_artifact_path_relocates_only_existing_data_or_runs_suffix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            data_candidate = _write_file(project_root / "data" / "suite" / "sample.cnf")
            runs_candidate = _write_file(project_root / "runs" / "analysis" / "audit.csv")
            existing_absolute = _write_file(project_root / "external" / "keep.cnf")
            old_data = "/home/legacy/my_rlaf/data/suite/sample.cnf"
            old_runs = "/home/legacy/my_rlaf/runs/analysis/audit.csv"
            missing = "/home/legacy/my_rlaf/data/suite/missing.cnf"

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                self.assertEqual(
                    resolve_manifest_artifact_path("data/suite/sample.cnf"),
                    data_candidate.resolve(),
                )
                self.assertEqual(
                    resolve_manifest_artifact_path(old_data),
                    data_candidate.resolve(),
                )
                self.assertEqual(
                    resolve_manifest_artifact_path(old_runs),
                    runs_candidate.resolve(),
                )
                self.assertEqual(
                    resolve_manifest_artifact_path(existing_absolute),
                    Path(os.path.normpath(existing_absolute)),
                )
                self.assertEqual(
                    resolve_manifest_artifact_path(missing),
                    Path(os.path.normpath(missing)),
                )

    def test_manifest_artifact_path_does_not_relocate_repeated_anchor_or_escape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_file(project_root / "data" / "suite" / "sample.cnf")
            repeated = "/home/data/archive/data/suite/sample.cnf"
            escaping = "/home/legacy/data/../data/suite/sample.cnf"

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                self.assertEqual(
                    resolve_manifest_artifact_path(repeated),
                    Path(os.path.normpath(repeated)),
                )
                self.assertEqual(
                    resolve_manifest_artifact_path(escaping),
                    Path(os.path.normpath(escaping)),
                )

    def test_manifest_relocation_does_not_stat_each_missing_legacy_leaf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            first = _write_file(project_root / "data" / "suite" / "first.cnf")
            second = _write_file(project_root / "data" / "suite" / "second.cnf")
            legacy_root = Path("/home/portable-test-root/my_rlaf")
            old_first = legacy_root / "data" / "suite" / "first.cnf"
            old_second = legacy_root / "data" / "suite" / "second.cnf"
            original_exists = Path.exists
            original_resolve = Path.resolve
            legacy_root_checks = []

            def guarded_exists(path):
                if path in {old_first, old_second}:
                    raise AssertionError("legacy leaf path must not be stat'ed")
                if path == legacy_root:
                    legacy_root_checks.append(path)
                    return False
                return original_exists(path)

            def guarded_resolve(path, *args, **kwargs):
                if path in {old_first, old_second}:
                    raise AssertionError("legacy leaf path must not be resolved through filesystem")
                return original_resolve(path, *args, **kwargs)

            with (
                patch("train_rlaf.PROJECT_ROOT", project_root),
                patch.object(Path, "exists", guarded_exists),
                patch.object(Path, "resolve", guarded_resolve),
            ):
                local_cache = {}
                self.assertEqual(
                    resolve_manifest_artifact_path(old_first, local_cache),
                    first.resolve(),
                )
                self.assertEqual(
                    resolve_manifest_artifact_path(old_second, local_cache),
                    second.resolve(),
                )

            self.assertEqual(legacy_root_checks, [legacy_root])

    def test_manifest_load_cache_does_not_survive_across_loads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "project"
            legacy_root = root / "legacy"
            candidate = _write_file(project_root / "data" / "suite" / "sample.cnf")
            old_path = legacy_root / "data" / "suite" / "sample.cnf"
            manifest_path = project_root / "runs" / "manifest.csv"
            manifest_path.parent.mkdir(parents=True)
            pd.DataFrame({"cnf_path": [str(old_path)]}).to_csv(manifest_path, index=False)

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                first = load_manifest_from_path(manifest_path)
                _write_file(old_path)
                second = load_manifest_from_path(manifest_path)

            self.assertEqual(first.loc[0, "cnf_path_resolved"], str(candidate.resolve()))
            self.assertEqual(second.loc[0, "cnf_path_resolved"], str(old_path.resolve()))

    def test_manifest_candidate_directory_is_not_relocated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            candidate = project_root / "data" / "suite" / "sample.cnf"
            candidate.mkdir(parents=True)
            old_path = Path("/home/legacy/my_rlaf/data/suite/sample.cnf")

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                resolved = resolve_manifest_artifact_path(old_path, {})

            self.assertEqual(resolved, Path(os.path.normpath(old_path)))

    def test_existing_absolute_directory_does_not_override_regular_candidate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "project"
            candidate = _write_file(project_root / "data" / "suite" / "sample.cnf")
            old_path = root / "legacy" / "data" / "suite" / "sample.cnf"
            old_path.mkdir(parents=True)

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                resolved = resolve_manifest_artifact_path(old_path, {})

            self.assertEqual(resolved, candidate.resolve())

    def test_manifest_candidate_broken_or_external_symlink_is_not_relocated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "project"
            old_path = root / "legacy" / "data" / "suite" / "sample.cnf"
            candidate = project_root / "data" / "suite" / "sample.cnf"
            candidate.parent.mkdir(parents=True)
            try:
                candidate.symlink_to(project_root / "data" / "suite" / "missing.cnf")
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                broken = resolve_manifest_artifact_path(old_path, {})
            self.assertEqual(broken, Path(os.path.normpath(old_path)))

            candidate.unlink()
            external = _write_file(root / "external" / "sample.cnf")
            candidate.symlink_to(external)
            with patch("train_rlaf.PROJECT_ROOT", project_root):
                escaped = resolve_manifest_artifact_path(old_path, {})
            self.assertEqual(escaped, Path(os.path.normpath(old_path)))

    def test_manifest_candidate_fifo_is_not_relocated(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "project"
            old_path = root / "legacy" / "data" / "suite" / "sample.cnf"
            candidate = project_root / "data" / "suite" / "sample.cnf"
            candidate.parent.mkdir(parents=True)
            try:
                os.mkfifo(candidate)
            except OSError as exc:
                self.skipTest(f"FIFO unavailable: {exc}")

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                fifo = resolve_manifest_artifact_path(old_path, {})
            self.assertEqual(fifo, Path(os.path.normpath(old_path)))

    def test_manifest_candidate_socket_is_not_relocated(self):
        if not hasattr(socket, "AF_UNIX"):
            self.skipTest("Unix sockets unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "project"
            old_path = root / "legacy" / "data" / "suite" / "sample.cnf"
            candidate = project_root / "data" / "suite" / "sample.cnf"
            candidate.parent.mkdir(parents=True)
            unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                try:
                    unix_socket.bind(str(candidate))
                except OSError as exc:
                    self.skipTest(f"Unix socket bind unavailable: {exc}")
                with patch("train_rlaf.PROJECT_ROOT", project_root):
                    socket_path = resolve_manifest_artifact_path(old_path, {})
                self.assertEqual(socket_path, Path(os.path.normpath(old_path)))
            finally:
                unix_socket.close()

    def test_manifest_four_artifact_columns_relocate_and_cover_portable_dataset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cnf = _write_file(
                project_root / "data" / "canonical" / "cnf" / "family" / "sample.cnf",
                "p cnf 1 1\n1 0\n",
            )
            split_cnf = _write_file(
                project_root / "data" / "canonical" / "train" / "family" / "sample.cnf",
                "p cnf 1 1\n1 0\n",
            )
            orbits = _write_file(
                project_root / "data" / "canonical" / "cnf" / "family" / "sample.orbits.json"
            )
            metadata = _write_file(
                project_root / "data" / "canonical" / "cnf" / "family" / "sample.metadata.json"
            )
            manifest_path = project_root / "runs" / "manifest.csv"
            manifest_path.parent.mkdir(parents=True)
            old_root = "/home/legacy/my_rlaf/data/canonical"
            pd.DataFrame(
                {
                    "family": ["family"],
                    "instance_id": ["sample"],
                    "base_instance_id": ["sample"],
                    "variant": ["base"],
                    "cnf_path": [f"{old_root}/cnf/family/sample.cnf"],
                    "split_cnf_path": [f"{old_root}/train/family/sample.cnf"],
                    "orbits_path": [f"{old_root}/cnf/family/sample.orbits.json"],
                    "metadata_path": [f"{old_root}/cnf/family/sample.metadata.json"],
                }
            ).to_csv(manifest_path, index=False)
            dataset = Mock(id_to_file={0: str(cnf)})

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                manifest = load_manifest_from_path(manifest_path)
                covered = dataset_metadata(dataset, manifest, required=True)

            self.assertEqual(manifest.loc[0, "cnf_path_resolved"], str(cnf.resolve()))
            self.assertEqual(manifest.loc[0, "split_cnf_path_resolved"], str(split_cnf.resolve()))
            self.assertEqual(manifest.loc[0, "orbits_path_resolved"], str(orbits.resolve()))
            self.assertEqual(manifest.loc[0, "metadata_path_resolved"], str(metadata.resolve()))
            self.assertEqual(covered.loc[0, "base_instance_id"], "sample")

    def test_orbit_certification_old_absolute_cnf_path_relocates_for_merge(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cnf = _write_file(project_root / "data" / "suite" / "sample.cnf")
            cert_path = project_root / "runs" / "cert.csv"
            cert_path.parent.mkdir(parents=True)
            pd.DataFrame(
                {
                    "cnf_path": ["/home/legacy/my_rlaf/data/suite/sample.cnf"],
                    "valid_for_training": [False],
                    "orbit_size": [0],
                    "orbit_confidence": [0.0],
                }
            ).to_csv(cert_path, index=False)

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                summary = load_orbit_certification_summary(cert_path)

            self.assertEqual(summary["cnf_path_resolved"].tolist(), [str(cnf.resolve())])

    def test_orbit_certification_summary_keeps_invalid_only_keys_at_zero(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            valid_cnf = _write_file(project_root / "data" / "suite" / "valid.cnf")
            invalid_cnf = _write_file(project_root / "data" / "suite" / "invalid.cnf")
            cert_path = project_root / "runs" / "cert.csv"
            cert_path.parent.mkdir(parents=True)
            pd.DataFrame(
                {
                    "cnf_path": [
                        "data/suite/valid.cnf",
                        "data/suite/valid.cnf",
                        "data/suite/invalid.cnf",
                        "data/suite/invalid.cnf",
                    ],
                    "valid_for_training": [True, False, False, False],
                    "orbit_id": ["valid-orbit", "invalid-extra", "invalid-only", "invalid-only"],
                    "orbit_size": [4, 100, 50, 50],
                    "orbit_confidence": [0.8, 1.0, 0.9, 0.9],
                }
            ).to_csv(cert_path, index=False)

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                summary = load_orbit_certification_summary(cert_path)

            self.assertEqual(summary["cnf_path_resolved"].nunique(), 2)
            self.assertFalse(bool(summary["cnf_path_resolved"].duplicated().any()))
            indexed = summary.set_index("cnf_path_resolved")
            valid = indexed.loc[str(valid_cnf.resolve())]
            invalid = indexed.loc[str(invalid_cnf.resolve())]
            self.assertEqual(int(valid["valid_orbit_count"]), 1)
            self.assertEqual(float(valid["valid_orbit_vars"]), 4.0)
            self.assertEqual(float(valid["orbit_confidence_mean"]), 0.8)
            self.assertEqual(float(valid["orbit_confidence_max"]), 0.8)
            self.assertEqual(int(invalid["valid_orbit_count"]), 0)
            self.assertEqual(float(invalid["valid_orbit_vars"]), 0.0)
            self.assertEqual(float(invalid["orbit_confidence_mean"]), 0.0)
            self.assertEqual(float(invalid["orbit_confidence_max"]), 0.0)

    def test_orbit_certification_rejects_missing_required_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cases = [
                (pd.DataFrame({"valid_for_training": [False]}), "cnf_path"),
                (pd.DataFrame({"cnf_path": ["data/a.cnf"]}), "valid_for_training"),
                (
                    pd.DataFrame(
                        {
                            "cnf_path": ["data/a.cnf"],
                            "valid_for_training": [True],
                            "orbit_size": [1],
                            "orbit_confidence": [0.5],
                        }
                    ),
                    "orbit_id",
                ),
                (
                    pd.DataFrame(
                        {
                            "cnf_path": ["data/a.cnf"],
                            "valid_for_training": [True],
                            "orbit_id": ["orbit-1"],
                            "orbit_confidence": [0.5],
                        }
                    ),
                    "orbit_size",
                ),
                (
                    pd.DataFrame(
                        {
                            "cnf_path": ["data/a.cnf"],
                            "valid_for_training": [True],
                            "orbit_id": ["orbit-1"],
                            "orbit_size": [1],
                        }
                    ),
                    "orbit_confidence",
                ),
            ]
            for index, (frame, missing_column) in enumerate(cases):
                with self.subTest(missing_column=missing_column):
                    cert_path = root / f"missing-{index}.csv"
                    frame.to_csv(cert_path, index=False)
                    with self.assertRaisesRegex(ValueError, missing_column):
                        load_orbit_certification_summary(cert_path)

    def test_orbit_certification_rejects_null_or_blank_cnf_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for index, value in enumerate([None, "", "   "]):
                with self.subTest(value=value):
                    cert_path = root / f"invalid-path-{index}.csv"
                    pd.DataFrame(
                        {
                            "cnf_path": [value],
                            "valid_for_training": [False],
                        }
                    ).to_csv(cert_path, index=False)
                    with self.assertRaisesRegex(ValueError, "cnf_path"):
                        load_orbit_certification_summary(cert_path)

    def test_orbit_certification_rejects_invalid_declared_valid_orbit_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cases = [
                ({"orbit_id": "", "orbit_size": 1, "orbit_confidence": 0.5}, "orbit_id"),
                ({"orbit_id": "orbit-1", "orbit_size": np.nan, "orbit_confidence": 0.5}, "orbit_size"),
                ({"orbit_id": "orbit-1", "orbit_size": np.inf, "orbit_confidence": 0.5}, "orbit_size"),
                ({"orbit_id": "orbit-1", "orbit_size": -1, "orbit_confidence": 0.5}, "orbit_size"),
                ({"orbit_id": "orbit-1", "orbit_size": 1, "orbit_confidence": np.nan}, "orbit_confidence"),
                ({"orbit_id": "orbit-1", "orbit_size": 1, "orbit_confidence": np.inf}, "orbit_confidence"),
                ({"orbit_id": "orbit-1", "orbit_size": 1, "orbit_confidence": -0.1}, "orbit_confidence"),
                ({"orbit_id": "orbit-1", "orbit_size": 1, "orbit_confidence": 1.1}, "orbit_confidence"),
            ]
            for index, (orbit_values, error_column) in enumerate(cases):
                with self.subTest(index=index, error_column=error_column):
                    cert_path = root / f"invalid-valid-orbit-{index}.csv"
                    pd.DataFrame(
                        {
                            "cnf_path": ["data/a.cnf"],
                            "valid_for_training": [True],
                            **{key: [value] for key, value in orbit_values.items()},
                        }
                    ).to_csv(cert_path, index=False)
                    with self.assertRaisesRegex(ValueError, error_column):
                        load_orbit_certification_summary(cert_path)

    def test_orbit_certification_rejects_duplicate_valid_orbit_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_path = Path(temp_dir) / "duplicate-valid-orbit.csv"
            pd.DataFrame(
                {
                    "cnf_path": ["data/a.cnf", "data/a.cnf"],
                    "valid_for_training": [True, True],
                    "orbit_id": ["orbit-1", "orbit-1"],
                    "orbit_size": [2, 2],
                    "orbit_confidence": [0.8, 0.8],
                }
            ).to_csv(cert_path, index=False)

            with self.assertRaisesRegex(ValueError, "duplicate.*orbit"):
                load_orbit_certification_summary(cert_path)

    def test_invalid_only_certification_may_omit_orbit_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_path = Path(temp_dir) / "invalid-only.csv"
            pd.DataFrame(
                {
                    "cnf_path": ["data/a.cnf"],
                    "valid_for_training": [False],
                }
            ).to_csv(cert_path, index=False)

            summary = load_orbit_certification_summary(cert_path)

            self.assertEqual(len(summary), 1)
            self.assertEqual(
                summary[
                    [
                        "valid_orbit_count",
                        "valid_orbit_vars",
                        "orbit_confidence_mean",
                        "orbit_confidence_max",
                    ]
                ].to_numpy().tolist(),
                [[0, 0.0, 0.0, 0.0]],
            )


class ManifestOrbitCertificationMergeTests(unittest.TestCase):
    def test_v2_cert_overrides_standard_orbit_columns_without_suffixes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            files = [_write_file(root / f"{name}.cnf") for name in ["a", "b", "control"]]
            manifest_path = _write_file(root / "manifest.csv", "placeholder")
            manifest = pd.DataFrame(
                {
                    "cnf_path_resolved": [str(path.resolve()) for path in files],
                    "family": ["structured", "structured", "random_3sat_control"],
                    "instance_id": ["a", "b", "control"],
                    "base_instance_id": ["a", "b", "control"],
                    "variant": ["base", "base", "base"],
                    "valid_orbit_count": [1, 3, 7],
                    "valid_orbit_vars": [2.0, 6.0, 14.0],
                    "orbit_confidence_mean": [0.1, 0.4, 0.7],
                    "orbit_confidence_max": [0.2, 0.5, 0.8],
                }
            )
            cert = pd.DataFrame(
                {
                    "cnf_path_resolved": [str(files[0].resolve()), str(files[2].resolve())],
                    "valid_orbit_count": [5, 0],
                    "valid_orbit_vars": [10.0, 0.0],
                    "orbit_confidence_mean": [0.9, 0.0],
                    "orbit_confidence_max": [1.0, 0.0],
                }
            )
            cfg = OmegaConf.create(
                {
                    "training": {
                        "echosat_manifest_path": str(manifest_path),
                        "echosat_orbit_certification_path": str(root / "cert.csv"),
                        "target_stat": "echosat_cost",
                    }
                }
            )

            with (
                patch("train_rlaf.load_manifest_from_path", return_value=manifest),
                patch("train_rlaf.load_orbit_certification_summary", return_value=cert),
            ):
                merged = load_training_manifest(cfg)
            metadata = dataset_metadata(
                Mock(id_to_file={index: str(path) for index, path in enumerate(files)}),
                merged,
                required=True,
            )

            self.assertFalse(any(column.endswith(("_x", "_y", "_cert")) for column in merged.columns))
            self.assertEqual(merged["valid_orbit_count"].tolist(), [5, 3, 0])
            self.assertEqual(merged["valid_orbit_vars"].tolist(), [10.0, 6.0, 0.0])
            self.assertEqual(merged["orbit_confidence_mean"].tolist(), [0.9, 0.4, 0.0])
            self.assertEqual(merged["orbit_confidence_max"].tolist(), [1.0, 0.5, 0.0])
            self.assertEqual(metadata["valid_orbit_count"].tolist(), [5, 3, 0])
            self.assertEqual(metadata["orbit_confidence_mean"].tolist(), [0.9, 0.4, 0.0])

    def test_duplicate_certification_summary_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cnf = _write_file(root / "a.cnf")
            manifest_path = _write_file(root / "manifest.csv", "placeholder")
            manifest = pd.DataFrame({"cnf_path_resolved": [str(cnf.resolve())]})
            duplicate_cert = pd.DataFrame(
                {
                    "cnf_path_resolved": [str(cnf.resolve()), str(cnf.resolve())],
                    "valid_orbit_count": [1, 2],
                }
            )
            cfg = OmegaConf.create(
                {
                    "training": {
                        "echosat_manifest_path": str(manifest_path),
                        "echosat_orbit_certification_path": str(root / "cert.csv"),
                        "target_stat": "echosat_cost",
                    }
                }
            )

            with (
                patch("train_rlaf.load_manifest_from_path", return_value=manifest),
                patch(
                    "train_rlaf.load_orbit_certification_summary",
                    return_value=duplicate_cert,
                ),
                self.assertRaisesRegex(ValueError, "duplicate cnf_path_resolved"),
            ):
                load_training_manifest(cfg)


class ReplayChecksTests(unittest.TestCase):
    def test_build_checks_passes_with_positive_eligible_and_nonpositive_blocked(self):
        checks = build_checks(_rows())

        self.assertEqual(checks["check"].tolist(), SPEC_CHECK_NAMES)
        self.assertEqual(checks["passed"].tolist(), [True, True, True])
        self.assertEqual(checks.attrs["eligible_count"], 1)
        self.assertEqual(checks.attrs["blocked_count"], 1)

    def test_build_checks_fail_closed_for_invalid_eligibility_and_blocked_positive(self):
        rows = pd.DataFrame(
            {
                "base_instance_id": ["same", "same", "same"],
                "v2_positive_eligible": ["False", "True", 1],
                "grpo_final_advantage": [0.25, 0.0, 0.0],
            }
        )

        checks = build_checks(rows)

        self.assertEqual(checks["check"].tolist(), SPEC_CHECK_NAMES)
        self.assertEqual(checks["passed"].tolist(), [False, False, False])
        self.assertEqual(checks.attrs["invalid_eligibility_count"], 3)

    def test_build_checks_rejects_missing_or_nonfinite_advantage(self):
        cases = [
            pd.DataFrame({"v2_positive_eligible": [True]}),
            pd.DataFrame({"v2_positive_eligible": [True], "grpo_final_advantage": [np.nan]}),
            pd.DataFrame({"v2_positive_eligible": [True], "grpo_final_advantage": [np.inf]}),
        ]
        for rows in cases:
            with self.subTest(columns=rows.columns.tolist()):
                checks = build_checks(rows)
                self.assertEqual(checks["passed"].tolist(), [False, False, False])

    def test_missing_eligibility_fails_global_stage4_check(self):
        checks = build_checks(pd.DataFrame({"grpo_final_advantage": [0.0]}))

        self.assertEqual(checks["check"].tolist(), SPEC_CHECK_NAMES)
        self.assertEqual(checks["passed"].tolist(), [False, False, False])
        self.assertEqual(checks.attrs["invalid_eligibility_count"], 1)

    def test_build_checks_empty_rows_has_fixed_order_and_no_eligible_positive(self):
        checks = build_checks(
            pd.DataFrame(columns=["v2_positive_eligible", "grpo_final_advantage"])
        )

        self.assertEqual(checks["check"].tolist(), SPEC_CHECK_NAMES)
        self.assertEqual(checks["passed"].tolist(), [True, False, False])

    def test_duplicate_rows_do_not_change_check_schema(self):
        duplicated = pd.concat([_rows(), _rows(), _rows()], ignore_index=True)

        checks = build_checks(duplicated)

        self.assertEqual(len(checks), 3)
        self.assertEqual(checks["check"].tolist(), SPEC_CHECK_NAMES)
        self.assertTrue(bool(checks["passed"].all()))


class ReplayCliTests(unittest.TestCase):
    def test_cli_audit_doc_escapes_markdown_table_cell_metacharacters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "rows.csv"
            checks_path = root / "checks.csv"
            doc_path = root / "report.md"
            rows = _attribution_rows().iloc[[1]].copy()
            rows["base_instance_id"] = "base|`\r\nforged| row"
            rows["variant"] = "variant`\n| next"
            rows.to_csv(rows_path, index=False)

            exit_code = replay_main(
                [
                    "--rows",
                    str(rows_path),
                    "--checks",
                    str(checks_path),
                    "--doc",
                    str(doc_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(pd.read_csv(checks_path)["check"].tolist(), SPEC_CHECK_NAMES)
            doc = doc_path.read_text(encoding="utf-8")
            escaped_base = "base&#124;&#96; forged&#124; row"
            escaped_variant = "variant&#96; &#124; next"
            self.assertIn(
                f"| `{escaped_base}` | `{escaped_variant}` | 1 | True | False |",
                doc,
            )
            self.assertIn(f"| `{escaped_base}` | 1 | 1 | -0.25 |", doc)
            self.assertNotIn("\r", doc)
            self.assertNotIn("\nforged", doc)
            self.assertNotIn("\n| next", doc)

    def test_cli_audit_doc_reports_deterministic_variant_base_and_rejections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "rows.csv"
            checks_path = root / "checks.csv"
            doc_path = root / "report.md"
            _attribution_rows().to_csv(rows_path, index=False)

            exit_code = replay_main(
                [
                    "--rows",
                    str(rows_path),
                    "--checks",
                    str(checks_path),
                    "--doc",
                    str(doc_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(pd.read_csv(checks_path)["check"].tolist(), SPEC_CHECK_NAMES)
            doc = doc_path.read_text(encoding="utf-8")
            self.assertIn("## Variant Summary", doc)
            self.assertIn("eligible rows: `1`", doc)
            self.assertIn("positive-capable variants: `1`", doc)
            self.assertIn("hard-blocked variants: `1`", doc)
            alpha = "| `base-a` | `alpha` | 0 | False | False |"
            beta = "| `base-a` | `beta` | 1 | True | False |"
            zeta = "| `base-b` | `zeta` | 0 | False | True |"
            self.assertLess(doc.index(alpha), doc.index(beta))
            self.assertLess(doc.index(beta), doc.index(zeta))

            self.assertIn("## Base Summary", doc)
            base_a = "| `base-a` | 1 | 1 | -0.25 |"
            base_b = "| `base-b` | 0 | 0 | -1.5 |"
            self.assertLess(doc.index(base_a), doc.index(base_b))

            self.assertIn("## Hard-Safety Rejections", doc)
            self.assertIn("| `control` | 1 |", doc)
            self.assertIn("| `weighted_risk` | 2 |", doc)
            self.assertIn("| `invalid_symmetry_orbit_evidence` | 0 |", doc)
            self.assertIn("missing diagnostics: `none`", doc)
            self.assertIn("invalid diagnostic values: `0`", doc)

    def test_cli_audit_attribution_fails_closed_for_missing_or_nonboolean_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "rows.csv"
            checks_path = root / "checks.csv"
            doc_path = root / "report.md"
            rows = _attribution_rows().iloc[:1].copy()
            rows["v2_variant_positive_capable"] = "yes"
            rows["v2_variant_hard_blocked"] = 0
            rows = rows.drop(columns=["v2_near_cap", "worst_variant_score"])
            rows.to_csv(rows_path, index=False)

            replay_main(
                [
                    "--rows",
                    str(rows_path),
                    "--checks",
                    str(checks_path),
                    "--doc",
                    str(doc_path),
                ]
            )

            doc = doc_path.read_text(encoding="utf-8")
            self.assertIn("positive-capable variants: `0`", doc)
            self.assertIn("hard-blocked variants: `0`", doc)
            self.assertIn("missing diagnostics: `v2_near_cap, worst_variant_score`", doc)
            self.assertIn("invalid diagnostic values: `2`", doc)
            self.assertNotIn("| `base-b` | 0 | 0 | 0 |", doc)

    def test_cli_writes_atomic_checks_and_doc_on_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "input" / "rows.csv"
            checks_path = root / "audit" / "checks.csv"
            doc_path = root / "audit" / "report.md"
            rows_path.parent.mkdir(parents=True)
            _rows().to_csv(rows_path, index=False)

            with patch("replay_echosat_v2_objective.os.replace", wraps=__import__("os").replace) as replace:
                exit_code = replay_main([
                    "--rows", str(rows_path),
                    "--checks", str(checks_path),
                    "--doc", str(doc_path),
                ])

            self.assertEqual(exit_code, 0)
            self.assertGreaterEqual(replace.call_count, 2)
            self.assertEqual(pd.read_csv(checks_path)["passed"].tolist(), [True, True, True])
            doc = doc_path.read_text(encoding="utf-8")
            self.assertIn("rows: `2`", doc)
            self.assertIn("eligible: `1`", doc)
            self.assertIn("blocked: `1`", doc)

    def test_cli_failure_still_writes_audit_before_exit_two(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "rows.csv"
            checks_path = root / "nested" / "checks.csv"
            doc_path = root / "nested" / "report.md"
            pd.DataFrame(
                {
                    "v2_positive_eligible": ["False", "invalid"],
                    "grpo_final_advantage": [0.5, 0.0],
                }
            ).to_csv(rows_path, index=False)

            exit_code = replay_main([
                "--input-rows", str(rows_path),
                "--checks", str(checks_path),
                "--doc", str(doc_path),
            ])

            self.assertEqual(exit_code, 2)
            self.assertTrue(checks_path.exists())
            self.assertTrue(doc_path.exists())
            self.assertFalse(bool(pd.read_csv(checks_path)["passed"].all()))
            self.assertIn("invalid eligibility: `2`", doc_path.read_text(encoding="utf-8"))

    def test_cli_missing_advantage_column_reports_failure_and_writes_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "rows.csv"
            checks_path = root / "checks.csv"
            doc_path = root / "report.md"
            pd.DataFrame({"v2_positive_eligible": [True]}).to_csv(rows_path, index=False)

            exit_code = replay_main([
                "--input-rows", str(rows_path),
                "--checks", str(checks_path),
                "--doc", str(doc_path),
            ])

            self.assertEqual(exit_code, 2)
            checks = pd.read_csv(checks_path)
            self.assertIn("missing grpo_final_advantage", " ".join(checks["evidence"].astype(str)))
            self.assertIn("grpo_final_advantage", doc_path.read_text(encoding="utf-8"))

    def test_cli_read_error_writes_failure_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checks_path = root / "checks.csv"
            doc_path = root / "report.md"

            exit_code = replay_main([
                "--input-rows", str(root / "missing.csv"),
                "--checks", str(checks_path),
                "--doc", str(doc_path),
            ])

            self.assertEqual(exit_code, 2)
            self.assertTrue(checks_path.exists())
            self.assertIn("read error", doc_path.read_text(encoding="utf-8").lower())

    def test_cli_rejects_same_canonical_path_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "rows.csv"
            doc_path = root / "doc.md"
            _rows().to_csv(rows_path, index=False)
            original = rows_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "rows.*checks.*distinct"):
                replay_main([
                    "--rows", str(rows_path),
                    "--checks", str(root / "." / "rows.csv"),
                    "--doc", str(doc_path),
                ])

            self.assertEqual(rows_path.read_bytes(), original)
            self.assertFalse(doc_path.exists())

    def test_cli_rejects_symlink_alias_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "rows.csv"
            checks_path = root / "checks-link.csv"
            doc_path = root / "doc.md"
            _rows().to_csv(rows_path, index=False)
            try:
                checks_path.symlink_to(rows_path)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            original = rows_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "rows.*checks.*distinct"):
                replay_main([
                    "--rows", str(rows_path),
                    "--checks", str(checks_path),
                    "--doc", str(doc_path),
                ])

            self.assertEqual(rows_path.read_bytes(), original)
            self.assertFalse(doc_path.exists())

    def test_cli_rejects_hardlink_alias_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rows_path = root / "rows.csv"
            checks_path = root / "checks-hardlink.csv"
            doc_path = root / "doc.md"
            _rows().to_csv(rows_path, index=False)
            try:
                os.link(rows_path, checks_path)
            except OSError as exc:
                self.skipTest(f"hardlinks unavailable: {exc}")
            original = rows_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "rows.*checks.*distinct"):
                replay_main([
                    "--rows", str(rows_path),
                    "--checks", str(checks_path),
                    "--doc", str(doc_path),
                ])

            self.assertEqual(rows_path.read_bytes(), original)
            self.assertFalse(doc_path.exists())


class Stage4ConfigTests(unittest.TestCase):
    def test_stage4_replay_config_composes_with_required_keys(self):
        with initialize_config_dir(version_base=None, config_dir=str(ROOT / "configs")):
            cfg = compose(config_name="config_train_rlaf_echosat_v2_stage4_replay")

        self.assertEqual(cfg.training.echosat_target_mode, "symmetry_grpo_v2")
        self.assertTrue(bool(cfg.training.echosat_replay_only))
        self.assertEqual(int(cfg.training.iterations), 1)
        self.assertEqual(int(cfg.training.steps_per_iter), 0)
        self.assertTrue(bool(cfg.training.save_echosat_reward_replay))
        self.assertTrue(bool(cfg.skip_initial_val))
        self.assertIsNone(cfg.ckpt_interval)
        self.assertEqual(cfg.wandb.mode, "disabled")
        self.assertEqual(cfg.model.event_adapter.fusion, "weight_only_residual")
        self.assertEqual(int(cfg.model.global_state_dim), 6)
        self.assertEqual(int(cfg.model.event_adapter.orbit_feature_dim), 10)
        self.assertEqual(int(cfg.model.event_adapter.orbit_event_state_dim), 100)
        self.assertTrue(bool(cfg.model.event_adapter.require_valid_orbit))
        self.assertEqual(float(cfg.model.event_adapter.min_orbit_event_variance), 1.0e-6)
        self.assertIsNotNone(cfg.model.event_adapter.delta_clip)
        self.assertEqual(
            cfg.training.echosat_orbit_certification_path,
            "runs/analysis/echosat_v2_orbit_certification.csv",
        )
        self.assertEqual(
            cfg.training.echosat_orbit_variable_path,
            "runs/analysis/echosat_v2_orbit_variables.csv",
        )
        self.assertEqual(
            cfg.training.echosat_reward_replay_dir,
            "runs/analysis/echosat_v2_stage4_reward_replay",
        )


class Stage5ConfigTests(unittest.TestCase):
    def test_legacy_absolute_dimacs_list_entries_relocate_to_project_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cnf = _write_file(
                project_root / "data" / "canonical" / "cnf" / "family" / "sample.cnf",
                "p cnf 1 1\n1 0\n",
            )
            file_list = _write_file(
                project_root / "runs" / "analysis" / "val_files.txt",
                "/home/legacy/project/data/canonical/cnf/family/sample.cnf\n",
            )

            with patch("train_rlaf.PROJECT_ROOT", project_root):
                resolved = dataset_path_from_config(f"@{file_list}")

            self.assertEqual(resolved, [str(cnf.resolve())])

    def test_stage5_short_config_composes_with_training_lifecycle_enabled(self):
        with initialize_config_dir(version_base=None, config_dir=str(ROOT / "configs")):
            cfg = compose(config_name="config_train_rlaf_echosat_v2_stage5_short")

        self.assertEqual(cfg.training.echosat_target_mode, "symmetry_grpo_v2")
        self.assertFalse(bool(cfg.training.echosat_replay_only))
        self.assertTrue(bool(cfg.training.echosat_compatible_checkpoint_init))
        self.assertEqual(int(cfg.training.iterations), 20)
        self.assertEqual(int(cfg.training.cnf_per_iter), 48)
        self.assertEqual(int(cfg.training.steps_per_iter), 48)
        self.assertEqual(int(cfg.training.num_samples), 16)
        self.assertFalse(bool(cfg.skip_initial_val))
        self.assertEqual(int(cfg.val_interval), 5)
        self.assertEqual(int(cfg.ckpt_interval), 5)
        self.assertEqual(
            cfg.from_checkpoint,
            "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt",
        )
        self.assertEqual(
            cfg.model_dir,
            "runs/GNN_Glucose_3SAT_EchoSAT_v2_Stage5_Short_Retry1",
        )
        self.assertEqual(
            cfg.training.echosat_reward_replay_dir,
            "runs/GNN_Glucose_3SAT_EchoSAT_v2_Stage5_Short_Retry1/reward_replay",
        )
        self.assertTrue(bool(cfg.training.save_echosat_reward_replay))
        self.assertEqual(cfg.model.event_adapter.fusion, "weight_only_residual")
        self.assertEqual(int(cfg.model.event_adapter.orbit_feature_dim), 10)
        self.assertEqual(int(cfg.model.event_adapter.orbit_event_state_dim), 100)
        self.assertTrue(bool(cfg.model.event_adapter.require_valid_orbit))
        self.assertEqual(float(cfg.model.event_adapter.min_orbit_event_variance), 1.0e-6)
        self.assertEqual(float(cfg.model.event_adapter.delta_clip), 0.25)
        self.assertEqual(
            cfg.training.echosat_orbit_certification_path,
            "runs/analysis/echosat_v2_orbit_certification.csv",
        )
        self.assertEqual(
            cfg.training.echosat_orbit_variable_path,
            "runs/analysis/echosat_v2_orbit_variables.csv",
        )
        self.assertTrue(model_updates_enabled(cfg))

        parameter = torch.nn.Parameter(torch.ones(1))
        optim, sched = build_training_optimizer_scheduler([parameter], cfg)
        self.assertIsNotNone(optim)
        self.assertIsNotNone(sched)

        dataset = Mock()
        loader = Mock()
        metadata_frame = pd.DataFrame({"cnf_id": [0]})
        orbit_store = Mock()
        with (
            patch("train_rlaf.dataset_path_from_config", return_value="val") as path_from_cfg,
            patch("train_rlaf.DimacsCNFDataset", return_value=dataset) as dataset_cls,
            patch("train_rlaf.load_manifest_from_path", return_value=pd.DataFrame()) as load_manifest,
            patch("train_rlaf.dataset_metadata", return_value=metadata_frame) as metadata,
            patch("train_rlaf.load_echosat_v2_orbit_store", return_value=orbit_store),
            patch("train_rlaf.DataLoader", return_value=loader) as loader_cls,
        ):
            runtime = build_validation_runtime(
                cfg,
                transform="transform",
                training_manifest=pd.DataFrame(),
                allow_model_updates=model_updates_enabled(cfg),
            )

        self.assertEqual(runtime, (dataset, metadata_frame, orbit_store, loader))
        path_from_cfg.assert_called_once_with(cfg.dataset.val_path)
        dataset_cls.assert_called_once()
        load_manifest.assert_called_once()
        metadata.assert_called_once()
        loader_cls.assert_called_once()


class TrainingOutputLifecycleTests(unittest.TestCase):
    def test_owned_marker_cleanup_does_not_delete_replacement_inode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            marker = Path(temp_dir) / ".echosat-run-owner"
            marker.write_text("owned", encoding="utf-8")
            owned = marker.lstat()
            identity = (owned.st_dev, owned.st_ino)
            marker.unlink()
            marker.write_text("foreign", encoding="utf-8")

            removed = _remove_owned_run_marker(marker, identity)

            self.assertFalse(removed)
            self.assertEqual(marker.read_text(encoding="utf-8"), "foreign")

    def test_owned_marker_cleanup_removes_matching_inode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            marker = Path(temp_dir) / ".echosat-run-owner"
            marker.write_text("owned", encoding="utf-8")
            owned = marker.lstat()

            removed = _remove_owned_run_marker(
                marker,
                (owned.st_dev, owned.st_ino),
            )

            self.assertTrue(removed)
            self.assertFalse(marker.exists())

    def test_completed_iteration_checkpoint_sequence_preserves_initial_checkpoint(self):
        names = ["iter=0"]
        names.extend(
            checkpoint
            for iteration in range(20)
            if (
                checkpoint := completed_iteration_checkpoint_name(
                    iteration,
                    checkpoint_interval=5,
                )
            )
            is not None
        )

        self.assertEqual(names, ["iter=0", "iter=5", "iter=10", "iter=15", "iter=20"])
        self.assertEqual(len(names), len(set(names)))
        self.assertIsNone(completed_iteration_checkpoint_name(0, checkpoint_interval=None))

    def test_training_output_directory_rejects_nonempty_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir) / "model"
            _write_file(model_dir / "existing.pt")
            cfg = _replay_cfg(replay_only=False, steps=48)
            cfg.model_dir = str(model_dir)

            with self.assertRaisesRegex(ValueError, "model_dir.*non-empty"):
                validate_training_output_directory(cfg)

    def test_training_output_directory_rejects_file_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = _write_file(Path(temp_dir) / "model")
            cfg = _replay_cfg(replay_only=False, steps=48)
            cfg.model_dir = str(model_path)

            with self.assertRaisesRegex(ValueError, "model_dir.*directory"):
                validate_training_output_directory(cfg)

    def test_training_output_directory_allows_empty_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir) / "model"
            model_dir.mkdir()
            cfg = _replay_cfg(replay_only=False, steps=48)
            cfg.model_dir = str(model_dir)

            validate_training_output_directory(cfg)

            marker = model_dir / ".echosat-run-owner"
            self.assertEqual(list(model_dir.iterdir()), [marker])
            owner = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(owner["pid"], os.getpid())
            self.assertIn("timestamp", owner)
            self.assertEqual(owner["model_name"], "")
            self.assertEqual(marker.stat().st_mode & 0o777, 0o600)

    def test_training_output_directory_claim_is_atomic_across_concurrent_callers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir) / "model"
            cfg = _replay_cfg(replay_only=False, steps=48)
            cfg.model_dir = str(model_dir)
            cfg.model_name = "concurrent-test"
            barrier = threading.Barrier(2)

            def claim():
                barrier.wait()
                try:
                    validate_training_output_directory(cfg)
                    return "claimed"
                except ValueError:
                    return "rejected"

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: claim(), range(2)))

            self.assertEqual(sorted(results), ["claimed", "rejected"])
            marker = model_dir / ".echosat-run-owner"
            self.assertTrue(marker.is_file())
            owner = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(owner["model_name"], "concurrent-test")
            self.assertEqual(owner["pid"], os.getpid())

    def test_iter_checkpoint_is_immutable_and_duplicate_does_not_modify_original(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cfg = _replay_cfg(replay_only=False, steps=48)
            cfg.model_dir = str(Path(temp_dir) / "model")
            model = _core_model()

            save_model(model, cfg, "iter=5", model_cfg=cfg)
            checkpoint = Path(cfg.model_dir) / "iter=5.pt"
            original = checkpoint.read_bytes()
            model.state_dict.return_value = {"changed.weight": torch.ones(3)}

            with self.assertRaisesRegex(ValueError, "checkpoint already exists"):
                save_model(model, cfg, "iter=5", model_cfg=cfg)

            self.assertEqual(checkpoint.read_bytes(), original)
            self.assertEqual(list(Path(cfg.model_dir).glob("*.tmp")), [])

    def test_config_and_replaceable_checkpoint_writes_are_atomic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cfg = _replay_cfg(replay_only=False, steps=48)
            cfg.model_dir = str(Path(temp_dir) / "model")
            model = _core_model()

            with patch("train_rlaf.os.replace", wraps=os.replace) as replace:
                save_model(model, cfg, "best", model_cfg=cfg)

            model_dir = Path(cfg.model_dir)
            self.assertTrue((model_dir / "config.yaml").is_file())
            self.assertTrue((model_dir / "training_config.yaml").is_file())
            self.assertTrue((model_dir / "best.pt").is_file())
            self.assertGreaterEqual(replace.call_count, 3)
            self.assertEqual(list(model_dir.glob("*.tmp")), [])

    def test_replay_only_bypasses_training_output_directory_guard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = _write_file(Path(temp_dir) / "occupied-model-path")
            cfg = _replay_cfg(replay_only=True, steps=0)
            cfg.model_dir = str(model_path)

            validate_training_output_directory(cfg)

    def test_production_main_validates_output_before_model_or_checkpoint_activity(self):
        source = inspect.getsource(train_main.__wrapped__)

        validation = source.index("validate_training_output_directory(cfg)")
        self.assertLess(validation, source.index("load_training_model(cfg)"))
        self.assertLess(validation, source.index("save_model("))
        self.assertIn("completed_iteration_checkpoint_name(", source)


class Stage5CompatibleCheckpointInitTests(unittest.TestCase):
    @staticmethod
    def _formal_cfg():
        cfg = _replay_cfg(replay_only=False, steps=48)
        cfg.training.echosat_compatible_checkpoint_init = True
        cfg.training.echosat_target_mode = "symmetry_grpo_v2"
        cfg.from_checkpoint = "checkpoint.pt"
        return cfg

    def test_formal_compatible_init_builds_current_model_before_loading_checkpoint(self):
        cfg = self._formal_cfg()
        transform = object()
        model = _core_model()
        loaded = [
            "lit_enc.mlp.0.weight",
            "cls_enc.mlp.0.weight",
            "layers.0.mlp.weight",
            "out_lin1.weight",
            "out_lin2.weight",
        ]
        events = []

        with (
            patch(
                "train_rlaf.init_transform",
                side_effect=lambda current_cfg: events.append("transform") or transform,
            ) as init_transform,
            patch(
                "train_rlaf.init_model",
                side_effect=lambda current_cfg, current_transform: events.append("model") or model,
            ) as init_model,
            patch(
                "train_rlaf.load_compatible_checkpoint",
                side_effect=lambda current_model, path: events.append("compatible")
                or (loaded, ["event_adapter.0.weight"]),
            ) as compatible,
            patch("train_rlaf.load_checkpoint") as legacy,
        ):
            loaded_model, loaded_transform, model_cfg = load_training_model(cfg)

        self.assertEqual(events, ["transform", "model", "compatible"])
        self.assertIs(loaded_model, model)
        self.assertIs(loaded_transform, transform)
        self.assertIs(model_cfg, cfg)
        init_transform.assert_called_once_with(cfg)
        init_model.assert_called_once_with(cfg, transform)
        compatible.assert_called_once_with(model, "checkpoint.pt")
        legacy.assert_not_called()

    def test_formal_compatible_init_requires_checkpoint_and_v2_target(self):
        missing_checkpoint = self._formal_cfg()
        missing_checkpoint.from_checkpoint = None
        with self.assertRaisesRegex(ValueError, "compatible_checkpoint_init requires from_checkpoint"):
            load_training_model(missing_checkpoint)

        wrong_target = self._formal_cfg()
        wrong_target.training.echosat_target_mode = "symmetry_grpo_v1_8"
        with self.assertRaisesRegex(ValueError, "compatible_checkpoint_init requires.*symmetry_grpo_v2"):
            load_training_model(wrong_target)

    def test_formal_compatible_init_enforces_core_coverage_and_skipped_keys(self):
        cfg = self._formal_cfg()
        cases = [
            ([], list(_core_model().state_dict()), "loaded zero core model parameters"),
            (["lit_enc.mlp.0.weight"], [], "missing core checkpoint prefixes"),
            (
                [
                    "lit_enc.mlp.0.weight",
                    "cls_enc.mlp.0.weight",
                    "layers.0.mlp.weight",
                    "out_lin1.weight",
                    "out_lin2.weight",
                ],
                ["unrelated_head.weight"],
                "unsupported skipped checkpoint parameters",
            ),
        ]
        for loaded, skipped, message in cases:
            with (
                self.subTest(message=message),
                patch("train_rlaf.init_transform", return_value=object()),
                patch("train_rlaf.init_model", return_value=_core_model()),
                patch(
                    "train_rlaf.load_compatible_checkpoint",
                    return_value=(loaded, skipped),
                ),
                self.assertRaisesRegex(ValueError, message),
            ):
                load_training_model(cfg)

    def test_replay_and_formal_compatible_init_reject_orbit_named_skipped_keys(self):
        replay_cfg = _replay_cfg()
        replay_cfg.from_checkpoint = "checkpoint.pt"
        configs = [("replay", replay_cfg), ("formal", self._formal_cfg())]
        loaded = [
            "lit_enc.mlp.0.weight",
            "cls_enc.mlp.0.weight",
            "layers.0.mlp.weight",
            "out_lin1.weight",
            "out_lin2.weight",
        ]
        skipped_cases = [
            "unrelated_orbit_probe.weight",
            "UNRELATED_ORBIT_PROBE.weight",
            "event_adapter_probe.weight",
        ]

        for mode, cfg in configs:
            for skipped in skipped_cases:
                with (
                    self.subTest(mode=mode, skipped=skipped),
                    patch("train_rlaf.init_transform", return_value=object()),
                    patch("train_rlaf.init_model", return_value=_core_model()),
                    patch(
                        "train_rlaf.load_compatible_checkpoint",
                        return_value=(loaded, [skipped]),
                    ),
                    self.assertRaisesRegex(
                        ValueError,
                        "unsupported skipped checkpoint parameters",
                    ),
                ):
                    load_training_model(cfg)

    def test_legacy_nonreplay_checkpoint_still_uses_legacy_loader(self):
        cfg = _replay_cfg(replay_only=False, steps=48)
        cfg.from_checkpoint = "legacy.pt"
        expected = (Mock(), object(), Mock())
        with (
            patch("train_rlaf.load_checkpoint", return_value=expected) as legacy,
            patch("train_rlaf.init_transform") as init_transform,
            patch("train_rlaf.init_model") as init_model,
            patch("train_rlaf.load_compatible_checkpoint") as compatible,
        ):
            result = load_training_model(cfg)

        self.assertIs(result, expected)
        legacy.assert_called_once_with("legacy.pt")
        init_transform.assert_not_called()
        init_model.assert_not_called()
        compatible.assert_not_called()


class ReplayOnlyGuardTests(unittest.TestCase):
    def test_replay_only_rejects_missing_checkpoint_instead_of_random_model(self):
        with self.assertRaisesRegex(ValueError, "replay_only requires from_checkpoint"):
            load_training_model(_replay_cfg())

    def test_replay_only_checkpoint_uses_composed_model_configuration(self):
        cfg = _replay_cfg()
        cfg.from_checkpoint = "checkpoint.pt"
        transform = object()
        model = _core_model()
        loaded_keys = [
            "lit_enc.mlp.0.weight",
            "cls_enc.mlp.0.weight",
            "layers.0.mlp.weight",
            "out_lin1.weight",
            "out_lin2.weight",
        ]
        with (
            patch("train_rlaf.init_transform", return_value=transform) as init_transform,
            patch("train_rlaf.init_model", return_value=model) as init_model,
            patch(
                "train_rlaf.load_compatible_checkpoint",
                return_value=(loaded_keys, ["event_adapter.0.weight"]),
            ) as load_compatible,
            patch("train_rlaf.load_checkpoint") as load_legacy,
        ):
            loaded_model, loaded_transform, model_cfg = load_training_model(cfg)

        self.assertIs(loaded_model, model)
        self.assertIs(loaded_transform, transform)
        self.assertIs(model_cfg, cfg)
        init_transform.assert_called_once_with(cfg)
        init_model.assert_called_once_with(cfg, transform)
        load_compatible.assert_called_once_with(model, "checkpoint.pt")
        load_legacy.assert_not_called()

    def test_replay_only_requires_artifact_saving_and_accepts_zero_steps(self):
        validate_replay_only_config(_replay_cfg(steps=0))
        with self.assertRaisesRegex(ValueError, "replay_only requires save_echosat_reward_replay=true"):
            validate_replay_only_config(_replay_cfg(save_replay=False))

    def test_replay_only_requires_strict_stage4_lifecycle_configuration(self):
        cases = [
            ("method", "dpo", "method='grpo'"),
            ("training.echosat_target_mode", "symmetry_grpo_v1_8", "symmetry_grpo_v2"),
            ("training.steps_per_iter", 1, "steps_per_iter=0"),
            ("ckpt_interval", 1, "ckpt_interval=None"),
            ("skip_initial_val", False, "skip_initial_val=true"),
        ]
        for key, value, message in cases:
            cfg = _replay_cfg()
            OmegaConf.update(cfg, key, value, merge=False)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, message):
                validate_replay_only_config(cfg)

    def test_canonical_replay_key_conflict_is_rejected(self):
        cfg = _replay_cfg(replay_only=True)
        cfg.training.replay_only = False

        with self.assertRaisesRegex(ValueError, "conflicting replay-only keys"):
            validate_replay_only_config(cfg)

    def test_legacy_replay_key_remains_supported_without_canonical_key(self):
        cfg = OmegaConf.create(
            {
                "training": {
                    "replay_only": True,
                    "echosat_target_mode": "symmetry_grpo_v2",
                    "save_echosat_reward_replay": True,
                    "steps_per_iter": 0,
                },
                "method": "grpo",
                "ckpt_interval": None,
                "skip_initial_val": True,
            }
        )

        validate_replay_only_config(cfg)
        self.assertTrue(replay_artifacts_before_update(cfg, lambda: None))

    def test_artifact_writer_runs_before_replay_only_skip(self):
        events = []
        cfg = _replay_cfg()

        skip_update = replay_artifacts_before_update(
            cfg,
            lambda: events.append("artifact"),
        )
        if not skip_update:
            events.append("train_grpo")

        self.assertTrue(skip_update)
        self.assertEqual(events, ["artifact"])

    def test_replay_iteration_runs_writer_but_not_training_or_save(self):
        events = []

        def training_update():
            events.extend(["dataset", "train", "save"])

        result = run_training_update_after_replay_artifacts(
            _replay_cfg(),
            lambda: events.append("artifact"),
            training_update,
        )

        self.assertIsNone(result)
        self.assertEqual(events, ["artifact"])

    def test_non_replay_iteration_runs_artifact_then_training(self):
        events = []

        result = run_training_update_after_replay_artifacts(
            _replay_cfg(replay_only=False, steps=4),
            lambda: events.append("artifact"),
            lambda: events.append("train") or 11,
        )

        self.assertEqual(result, 11)
        self.assertEqual(events, ["artifact", "train"])

    def test_production_main_routes_training_through_lifecycle_helper(self):
        source = inspect.getsource(train_main.__wrapped__)

        self.assertIn("run_training_update_after_replay_artifacts(", source)
        self.assertNotIn("replay_artifacts_before_update(", source)
        self.assertIn("build_validation_runtime(", source)
        self.assertLess(
            source.index("allow_model_updates = model_updates_enabled(cfg)"),
            source.index("build_validation_runtime("),
        )

    def test_replay_only_does_not_build_optimizer_or_scheduler(self):
        with (
            patch("train_rlaf.torch.optim.AdamW") as adamw,
            patch("train_rlaf.torch.optim.lr_scheduler.LambdaLR") as scheduler,
        ):
            optim, sched = build_training_optimizer_scheduler([], _replay_cfg())

        self.assertIsNone(optim)
        self.assertIsNone(sched)
        adamw.assert_not_called()
        scheduler.assert_not_called()
        self.assertFalse(model_updates_enabled(_replay_cfg()))

    def test_replay_only_skips_all_validation_runtime_initialization(self):
        cfg = _replay_cfg()
        dataset = Mock()
        loader = Mock()
        with (
            patch("train_rlaf.DimacsCNFDataset", return_value=dataset) as dataset_cls,
            patch("train_rlaf.load_manifest_from_path") as load_manifest,
            patch("train_rlaf.dataset_metadata") as metadata,
            patch("train_rlaf.load_echosat_v2_orbit_store") as orbit_store,
            patch("train_rlaf.DataLoader", return_value=loader) as loader_cls,
        ):
            runtime = build_validation_runtime(
                cfg,
                transform=object(),
                training_manifest=object(),
                allow_model_updates=False,
            )

        self.assertEqual(runtime, (None, None, None, None))
        dataset_cls.assert_not_called()
        load_manifest.assert_not_called()
        metadata.assert_not_called()
        orbit_store.assert_not_called()
        loader_cls.assert_not_called()

    def test_normal_training_builds_validation_runtime(self):
        cfg = OmegaConf.create(
            {
                "dataset": {"val_path": "validation/*.cnf", "lazy": False},
                "loader": {"batch_size": 2, "num_workers": 0},
                "training": {
                    "target_stat": "composite",
                    "echosat_val_manifest_path": "",
                },
            }
        )
        dataset = Mock()
        metadata_frame = pd.DataFrame({"cnf_id": [1]})
        orbit_store_value = Mock()
        loader = Mock()
        training_manifest = object()
        with (
            patch("train_rlaf.DimacsCNFDataset", return_value=dataset) as dataset_cls,
            patch("train_rlaf.dataset_metadata", return_value=metadata_frame) as metadata,
            patch(
                "train_rlaf.load_echosat_v2_orbit_store",
                return_value=orbit_store_value,
            ) as orbit_store,
            patch("train_rlaf.DataLoader", return_value=loader) as loader_cls,
        ):
            runtime = build_validation_runtime(
                cfg,
                transform="transform",
                training_manifest=training_manifest,
                allow_model_updates=True,
            )

        self.assertEqual(runtime, (dataset, metadata_frame, orbit_store_value, loader))
        dataset_cls.assert_called_once()
        metadata.assert_called_once_with(dataset, training_manifest, required=False)
        orbit_store.assert_called_once_with(cfg, metadata_frame)
        loader_cls.assert_called_once_with(
            dataset=dataset,
            batch_size=2,
            num_workers=0,
            shuffle=False,
        )

    def test_replay_checkpoint_rejects_empty_or_wrong_core_coverage(self):
        cfg = _replay_cfg()
        cfg.from_checkpoint = "checkpoint.pt"
        for loaded, skipped, message in [
            ([], list(_core_model().state_dict()), "loaded zero core model parameters"),
            (["lit_enc.mlp.0.weight"], [], "missing core checkpoint prefixes"),
        ]:
            with (
                self.subTest(loaded=loaded),
                patch("train_rlaf.init_transform", return_value=object()),
                patch("train_rlaf.init_model", return_value=_core_model()),
                patch("train_rlaf.load_compatible_checkpoint", return_value=(loaded, skipped)),
                self.assertRaisesRegex(ValueError, message),
            ):
                load_training_model(cfg)

    def test_replay_checkpoint_rejects_unrelated_skipped_parameters(self):
        cfg = _replay_cfg()
        cfg.from_checkpoint = "checkpoint.pt"
        loaded = [
            "lit_enc.mlp.0.weight",
            "cls_enc.mlp.0.weight",
            "layers.0.mlp.weight",
            "out_lin1.weight",
            "out_lin2.weight",
        ]
        with (
            patch("train_rlaf.init_transform", return_value=object()),
            patch("train_rlaf.init_model", return_value=_core_model()),
            patch(
                "train_rlaf.load_compatible_checkpoint",
                return_value=(loaded, ["unrelated_head.weight"]),
            ),
            self.assertRaisesRegex(ValueError, "unsupported skipped checkpoint parameters"),
        ):
            load_training_model(cfg)

    def test_non_replay_mode_writes_artifact_then_allows_update(self):
        events = []
        cfg = _replay_cfg(replay_only=False, steps=4)

        skip_update = replay_artifacts_before_update(cfg, lambda: events.append("artifact"))
        if not skip_update:
            events.append("train_grpo")

        self.assertFalse(skip_update)
        self.assertEqual(events, ["artifact", "train_grpo"])

    def test_replay_only_log_is_stable(self):
        self.assertEqual(
            REPLAY_ONLY_LOG,
            "Replay-only mode: reward replay artifacts written; skipping optimizer and training updates.",
        )


class ReplayArtifactWriterTests(unittest.TestCase):
    def test_replay_writer_is_atomic_and_summary_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cfg = _replay_cfg()
            cfg.training.echosat_reward_replay_dir = temp_dir

            with patch("train_rlaf.os.replace", wraps=os.replace) as replace:
                write_echosat_reward_replay_artifacts(_rows(), cfg, iteration=3, global_step=7)
                write_echosat_reward_replay_artifacts(_rows(), cfg, iteration=3, global_step=7)

            iteration_path = Path(temp_dir) / "iter=000003_solver_stats.csv"
            summary_path = Path(temp_dir) / "summary.csv"
            self.assertTrue(iteration_path.exists())
            self.assertTrue(summary_path.exists())
            summary = pd.read_csv(summary_path)
            self.assertEqual(summary[["iteration", "global_step"]].drop_duplicates().shape[0], 1)
            self.assertEqual(len(summary), 1)
            self.assertGreaterEqual(replace.call_count, 4)
            self.assertEqual(list(Path(temp_dir).glob("*.tmp")), [])

    def test_replay_writer_replace_failure_leaves_no_partial_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cfg = _replay_cfg()
            cfg.training.echosat_reward_replay_dir = temp_dir

            with (
                patch("train_rlaf.os.replace", side_effect=OSError("replace failed")),
                self.assertRaisesRegex(OSError, "replace failed"),
            ):
                write_echosat_reward_replay_artifacts(_rows(), cfg, iteration=4, global_step=8)

            self.assertFalse((Path(temp_dir) / "iter=000004_solver_stats.csv").exists())
            self.assertFalse((Path(temp_dir) / "summary.csv").exists())
            self.assertEqual(list(Path(temp_dir).glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
