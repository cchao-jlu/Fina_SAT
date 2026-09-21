import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
import torch
from omegaconf import OmegaConf
from pandas.testing import assert_frame_equal
from torch_geometric.data import HeteroData

from src.echosat.objective_v2 import (
    attach_masked_grpo_advantage,
    build_symmetry_grpo_v2_target,
    worst_variant_scores,
)
from src.policy.evaluate import compute_plain_solver_stats
from train_rlaf import attach_grpo_advantage_columns, ensure_plain_unguided_baseline


def _cached_samples(cnf_id: int, num_samples: int) -> HeteroData:
    data = HeteroData()
    data.cnf_id = torch.tensor(cnf_id)
    data["var"].var_params = torch.ones((2, num_samples, 2), dtype=torch.float32)
    return data


def _v2_cfg(target_mode: str = "symmetry_grpo_v2"):
    return OmegaConf.create(
        {
            "method": "grpo",
            "training": {
                "target_stat": "echosat_cost",
                "echosat_target_mode": target_mode,
            },
            "solver": {
                "num_workers": 1,
                "solver": "glucose",
                "params": {"cpu-lim": 10.0},
            },
        }
    )


def _guided_row(cnf_id: int, **overrides) -> dict:
    row = {
        "cnf_id": cnf_id,
        "sample_id": 0,
        "base_instance_id": f"base-{cnf_id}",
        "variant": "base",
        "family": "structured",
        "control_type": "",
        "symmetry_strength": "strong",
        "Result": "SATISFIABLE",
        "CPU time": 6.0,
        "decisions": 80.0,
        "conflicts": 70.0,
        "valid_orbit_count": 2.0,
        "mean_orbit_confidence": 0.9,
        "echosat_weighted_risk": 0.0,
    }
    row.update(overrides)
    return row


def _plain_row(cnf_id: int, **overrides) -> dict:
    row = {
        "cnf_id": cnf_id,
        "sample_id": 0,
        "file": f"{cnf_id}.cnf",
        "Result": "SATISFIABLE",
        "CPU time": 5.0,
        "decisions": 100.0,
        "conflicts": 100.0,
    }
    row.update(overrides)
    return row


def _static_row(cnf_id: int, **overrides) -> dict:
    row = _plain_row(cnf_id)
    row["file"] = f"static-{cnf_id}.cnf"
    row.update(overrides)
    return row


class WorstVariantScoresTests(unittest.TestCase):
    def test_worst_variant_score_broadcasts_conservative_variant_mean(self):
        frame = pd.DataFrame(
            [
                {"base_instance_id": "a", "variant": "base", "score": 4.0},
                {"base_instance_id": "a", "variant": "perm-good", "score": 2.0},
                {"base_instance_id": "a", "variant": "perm-bad", "score": -6.0},
                {"base_instance_id": "a", "variant": "perm-bad", "score": -2.0},
                {"base_instance_id": "b", "variant": "base", "score": np.nan},
                {"base_instance_id": "b", "variant": "perm", "score": np.inf},
            ]
        )

        result = worst_variant_scores(frame, "score")
        permuted = worst_variant_scores(frame.sample(frac=1.0, random_state=7), "score")

        self.assertTrue(np.allclose(result.iloc[:4].to_numpy(), -4.0))
        self.assertTrue(bool((result.iloc[4:] <= 0.0).all()))
        self.assertEqual(result.attrs["invalid_score_count"], 2)
        self.assertEqual(result.attrs["invalid_score_indices"], [4, 5])
        self.assertEqual(
            dict(zip(frame.index, result)),
            dict(zip(permuted.index, permuted)),
        )

    def test_worst_variant_score_validates_columns_and_duplicate_index(self):
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            worst_variant_scores(pd.DataFrame({"score": [1.0]}), "score")
        duplicate_index = pd.DataFrame(
            {
                "base_instance_id": ["a", "a"],
                "variant": ["base", "perm"],
                "score": [1.0, -1.0],
            },
            index=[0, 0],
        )
        with self.assertRaisesRegex(ValueError, "unique index"):
            worst_variant_scores(duplicate_index, "score")

    def test_worst_variant_score_requires_str_grouping_keys_without_coercion(self):
        invalid_frames = [
            pd.DataFrame(
                {"base_instance_id": [1], "variant": ["base"], "score": [1.0]}
            ),
            pd.DataFrame(
                {"base_instance_id": ["a"], "variant": [True], "score": [1.0]}
            ),
            pd.DataFrame(
                {
                    "base_instance_id": pd.Series([1, "1"], dtype=object),
                    "variant": ["base", "base"],
                    "score": [1.0, -1.0],
                }
            ),
        ]
        for frame in invalid_frames:
            with self.subTest(values=frame[["base_instance_id", "variant"]].to_dict("list")):
                with self.assertRaisesRegex(ValueError, "string base_instance_id and variant"):
                    worst_variant_scores(frame, "score")

        valid = pd.DataFrame(
            {
                "base_instance_id": pd.Series([np.str_("a")], dtype=object),
                "variant": pd.Series([np.str_("base")], dtype=object),
                "score": [1.0],
            }
        )
        self.assertEqual(worst_variant_scores(valid, "score").tolist(), [1.0])


class MaskedGRPOTests(unittest.TestCase):
    def test_masked_grpo_accepts_only_real_boolean_eligibility(self):
        invalid_object = object()
        frame = pd.DataFrame(
            {
                "cnf_id": [1] * 8,
                "sample_id": list(range(8)),
                "echosat_cost": [0.0, 2.0, -100.0, -100.0, -100.0, -100.0, -100.0, -100.0],
                "v2_positive_eligible": [
                    True,
                    np.bool_(True),
                    "False",
                    "True",
                    0,
                    1,
                    None,
                    invalid_object,
                ],
                "v2_blocked_penalty": [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            }
        )

        result = attach_masked_grpo_advantage(frame)

        self.assertEqual(result["v2_positive_eligible"].tolist(), [True, True, False, False, False, False, False, False])
        self.assertEqual(int(result["v2_invalid_eligibility"].sum()), 6)
        self.assertEqual(result.attrs["invalid_eligibility_count"], 6)
        self.assertGreater(float(result.loc[0, "advantage"]), 0.0)
        self.assertTrue(bool((result.loc[2:, "advantage"] <= 0.0).all()))

    def test_masked_grpo_missing_eligibility_column_fails_closed(self):
        frame = pd.DataFrame(
            {
                "cnf_id": [1, 1],
                "sample_id": [0, 1],
                "echosat_cost": [0.0, 2.0],
                "v2_blocked_penalty": [1.0, 1.0],
            }
        )

        result = attach_masked_grpo_advantage(frame)

        self.assertFalse(bool(result["v2_positive_eligible"].any()))
        self.assertTrue(bool(result["v2_invalid_eligibility"].all()))
        self.assertEqual(result.attrs["invalid_eligibility_count"], 2)
        self.assertTrue(bool((result["advantage"] <= 0.0).all()))

    def test_blocked_extreme_values_do_not_change_eligible_normalization(self):
        frame = pd.DataFrame(
            {
                "cnf_id": [1, 1, 1],
                "sample_id": [0, 1, 2],
                "echosat_cost": [0.0, 2.0, -1.0e12],
                "v2_positive_eligible": [True, True, False],
                "v2_blocked_penalty": [0.0, 0.0, 3.0],
                "echosat_advantage_weight": [1.0, 1.0, -100.0],
            },
            index=[8, 2, 5],
        )
        original = frame.copy(deep=True)

        result = attach_masked_grpo_advantage(frame)

        assert_frame_equal(frame, original)
        self.assertEqual(result.index.tolist(), [8, 2, 5])
        self.assertGreater(float(result.loc[8, "advantage"]), 0.0)
        self.assertLess(float(result.loc[2, "advantage"]), 0.0)
        self.assertLessEqual(float(result.loc[5, "advantage"]), 0.0)
        self.assertAlmostEqual(float(result.loc[8, "grpo_group_mean_cost"]), 1.0)

    def test_masked_grpo_handles_all_blocked_singleton_and_nonfinite_rows(self):
        frame = pd.DataFrame(
            {
                "cnf_id": [1, 1, 2, 3, 3],
                "sample_id": [0, 1, 0, 0, 1],
                "echosat_cost": [np.nan, np.inf, 4.0, 1.0, 2.0],
                "v2_positive_eligible": [True, False, True, False, False],
                "v2_blocked_penalty": [0.0, np.nan, 0.0, 2.0, 1.0],
            }
        )

        result = attach_masked_grpo_advantage(frame)

        self.assertTrue(bool(np.isfinite(result["advantage"]).all()))
        self.assertFalse(bool(result.loc[0, "v2_positive_eligible"]))
        self.assertEqual(float(result.loc[2, "advantage"]), 0.0)
        self.assertTrue(bool((result.loc[[0, 1, 3, 4], "advantage"] <= 0.0).all()))

    def test_masked_grpo_validates_required_columns_and_duplicate_keys(self):
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            attach_masked_grpo_advantage(pd.DataFrame({"cnf_id": [1]}))
        duplicate = pd.DataFrame(
            {
                "cnf_id": [1, 1],
                "sample_id": [0, 0],
                "echosat_cost": [1.0, 2.0],
                "v2_positive_eligible": [True, True],
                "v2_blocked_penalty": [0.0, 0.0],
            }
        )
        with self.assertRaisesRegex(ValueError, "duplicate cnf_id/sample_id"):
            attach_masked_grpo_advantage(duplicate)


class PlainSolverStatsTests(unittest.TestCase):
    def test_plain_solver_passes_none_and_preserves_rows(self):
        dataset = SimpleNamespace(
            cnf_list=[SimpleNamespace(clauses=[[1]]), SimpleNamespace(clauses=[[-1]])],
            id_to_file={0: "zero.cnf", 1: "one.cnf"},
        )
        calls = []

        def fake_solver(args):
            cnf_id, sample_id, _cnf, var_params, _solver_params = args
            calls.append((cnf_id, sample_id, var_params))
            return {"cnf_id": cnf_id, "sample_id": sample_id, "Result": "SATISFIABLE"}

        with patch("src.policy.evaluate.solver_pool_fn", side_effect=fake_solver):
            result = compute_plain_solver_stats(
                dataset,
                [_cached_samples(1, 2), _cached_samples(0, 1)],
                num_workers=1,
                solver="glucose",
            )

        self.assertEqual(calls, [(1, 0, None), (0, 0, None)])
        self.assertEqual(result[["cnf_id", "sample_id", "file"]].to_dict("records"), [
            {"cnf_id": 1, "sample_id": 0, "file": "one.cnf"},
            {"cnf_id": 1, "sample_id": 1, "file": "one.cnf"},
            {"cnf_id": 0, "sample_id": 0, "file": "zero.cnf"},
        ])

    def test_plain_solver_deduplicates_matching_layout_and_rejects_conflicts(self):
        dataset = SimpleNamespace(
            cnf_list=[SimpleNamespace(clauses=[[1]])],
            id_to_file={0: "zero.cnf"},
        )
        calls = []

        def fake_solver(args):
            calls.append(args[:2])
            return {"cnf_id": 0, "sample_id": 0, "Result": "SATISFIABLE"}

        with patch("src.policy.evaluate.solver_pool_fn", side_effect=fake_solver):
            result = compute_plain_solver_stats(
                dataset,
                [_cached_samples(0, 2), _cached_samples(0, 2)],
                num_workers=1,
            )
        self.assertEqual(calls, [(0, 0)])
        self.assertEqual(result["sample_id"].tolist(), [0, 1])

        with self.assertRaisesRegex(ValueError, "conflicting sample counts for cnf_id=0"):
            compute_plain_solver_stats(
                dataset,
                [_cached_samples(0, 1), _cached_samples(0, 2)],
                num_workers=1,
            )

    def test_plain_solver_empty_and_exception_behavior(self):
        dataset = SimpleNamespace(cnf_list=[], id_to_file={})
        empty = compute_plain_solver_stats(dataset, [], num_workers=1)
        self.assertEqual(empty.columns.tolist(), ["cnf_id", "sample_id", "file"])
        with patch("src.policy.evaluate.solver_pool_fn", side_effect=RuntimeError("solver failed")):
            with self.assertRaisesRegex(RuntimeError, "solver failed"):
                compute_plain_solver_stats(
                    SimpleNamespace(
                        cnf_list=[SimpleNamespace(clauses=[[1]])],
                        id_to_file={0: "zero.cnf"},
                    ),
                    [_cached_samples(0, 1)],
                    num_workers=1,
                )


class SymmetryGRPOV2TargetTests(unittest.TestCase):
    def test_variant_eligibility_does_not_broadcast_stochastic_failure_across_base(self):
        guided = pd.DataFrame(
            [
                _guided_row(1, sample_id=0, base_instance_id="shared", variant="safe"),
                _guided_row(
                    1,
                    sample_id=1,
                    base_instance_id="shared",
                    variant="safe",
                    decisions=75.0,
                    conflicts=65.0,
                ),
                _guided_row(2, sample_id=0, base_instance_id="shared", variant="mixed"),
                _guided_row(
                    2,
                    sample_id=1,
                    base_instance_id="shared",
                    variant="mixed",
                    decisions=180.0,
                    conflicts=180.0,
                ),
            ]
        )
        plain = pd.DataFrame(
            [
                _plain_row(1, sample_id=0),
                _plain_row(1, sample_id=1),
                _plain_row(2, sample_id=0),
                _plain_row(2, sample_id=1),
            ]
        )
        static = pd.DataFrame([_static_row(1), _static_row(2)])

        result = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

        safe = result["variant"].eq("safe")
        mixed = result["variant"].eq("mixed")
        self.assertTrue(bool(result.loc[safe, "v2_positive_eligible"].all()))
        self.assertFalse(bool(result.loc[mixed, "v2_positive_eligible"].any()))
        self.assertFalse(bool(result.loc[mixed, "v2_variant_hard_blocked"].any()))
        self.assertTrue(bool(result.loc[safe, "v2_variant_positive_capable"].all()))
        self.assertFalse(bool(result.loc[mixed, "v2_variant_positive_capable"].any()))
        self.assertLess(float(result["worst_variant_score"].max()), 0.0)

    def test_hard_failure_blocks_its_whole_variant_only(self):
        guided = pd.DataFrame(
            [
                _guided_row(1, sample_id=0, base_instance_id="shared", variant="safe"),
                _guided_row(1, sample_id=1, base_instance_id="shared", variant="safe"),
                _guided_row(2, sample_id=0, base_instance_id="shared", variant="risk"),
                _guided_row(
                    2,
                    sample_id=1,
                    base_instance_id="shared",
                    variant="risk",
                    echosat_weighted_risk=1.0,
                ),
            ]
        )
        plain = pd.DataFrame(
            [
                _plain_row(1, sample_id=0),
                _plain_row(1, sample_id=1),
                _plain_row(2, sample_id=0),
                _plain_row(2, sample_id=1),
            ]
        )
        static = pd.DataFrame([_static_row(1), _static_row(2)])

        result = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

        safe = result["variant"].eq("safe")
        risk = result["variant"].eq("risk")
        self.assertFalse(bool(result.loc[safe, "v2_variant_hard_blocked"].any()))
        self.assertTrue(bool(result.loc[risk, "v2_variant_hard_blocked"].all()))
        self.assertTrue(bool(result.loc[safe, "v2_positive_eligible"].all()))
        self.assertFalse(bool(result.loc[risk, "v2_positive_eligible"].any()))
        self.assertTrue(
            result["v2_base_blocked"].equals(result["v2_variant_hard_blocked"])
        )
        self.assertTrue(bool(result["v2_base_hard_blocked"].all()))

    def test_positive_mean_variant_keeps_only_row_candidates(self):
        guided = pd.DataFrame(
            [
                _guided_row(1, sample_id=0, base_instance_id="shared", variant="mixed"),
                _guided_row(
                    1,
                    sample_id=1,
                    base_instance_id="shared",
                    variant="mixed",
                    decisions=101.0,
                    conflicts=70.0,
                ),
            ]
        )
        plain = pd.DataFrame([_plain_row(1, sample_id=0), _plain_row(1, sample_id=1)])
        static = pd.DataFrame([_static_row(1)])

        result = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

        self.assertTrue(bool(result["v2_variant_positive_capable"].all()))
        self.assertEqual(result["v2_row_positive_candidate"].tolist(), [True, False])
        self.assertEqual(result["v2_positive_eligible"].tolist(), [True, False])

    def test_variant_eligibility_validates_keys_finite_scores_and_order(self):
        guided = pd.DataFrame(
            [
                _guided_row(1, sample_id=0, base_instance_id="shared", variant="safe"),
                _guided_row(1, sample_id=1, base_instance_id="shared", variant="safe"),
                _guided_row(
                    2,
                    sample_id=0,
                    base_instance_id="shared",
                    variant="invalid",
                    decisions=np.inf,
                ),
            ],
            index=[7, 3, 9],
        )
        plain = pd.DataFrame(
            [
                _plain_row(1, sample_id=0),
                _plain_row(1, sample_id=1),
                _plain_row(2, sample_id=0),
            ]
        )
        static = pd.DataFrame([_static_row(1), _static_row(2)])

        result = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)
        shuffled = guided.sample(frac=1.0, random_state=17)
        shuffled_result = build_symmetry_grpo_v2_target(
            shuffled,
            plain,
            static,
            cpu_cap=10.0,
        )

        self.assertEqual(result.index.tolist(), guided.index.tolist())
        diagnostic_columns = [
            "v2_hard_safety_blocked",
            "v2_row_positive_candidate",
            "v2_variant_hard_blocked",
            "v2_variant_mean_search_score",
            "v2_variant_positive_capable",
            "v2_positive_eligible",
        ]
        keyed = result.set_index(["cnf_id", "sample_id"])[diagnostic_columns].sort_index()
        shuffled_keyed = shuffled_result.set_index(["cnf_id", "sample_id"])[diagnostic_columns].sort_index()
        assert_frame_equal(keyed, shuffled_keyed)
        invalid = result["variant"].eq("invalid")
        self.assertTrue(bool(result.loc[invalid, "v2_hard_safety_blocked"].all()))
        self.assertFalse(bool(result.loc[invalid, "v2_variant_positive_capable"].any()))
        self.assertTrue(np.isfinite(result["v2_variant_mean_search_score"]).all())

        for column, value in [("base_instance_id", None), ("base_instance_id", " "), ("variant", None), ("variant", "")]:
            with self.subTest(column=column, value=value):
                malformed = guided.iloc[:1].copy()
                malformed.loc[malformed.index[0], column] = value
                with self.assertRaisesRegex(ValueError, "base_instance_id and variant"):
                    build_symmetry_grpo_v2_target(
                        malformed,
                        plain.iloc[:1],
                        static.iloc[:1],
                        cpu_cap=10.0,
                    )

        invalid_key_frames = [
            pd.DataFrame([_guided_row(1, base_instance_id=1)]),
            pd.DataFrame([_guided_row(1, variant=True)]),
            pd.DataFrame(
                [
                    _guided_row(1, sample_id=0, base_instance_id=1),
                    _guided_row(1, sample_id=1, base_instance_id="1"),
                ]
            ),
        ]
        for malformed in invalid_key_frames:
            with self.subTest(
                values=malformed[["base_instance_id", "variant"]].to_dict("list")
            ):
                matching_plain = pd.DataFrame(
                    [_plain_row(1, sample_id=int(sample_id)) for sample_id in malformed["sample_id"]]
                )
                with self.assertRaisesRegex(ValueError, "string base_instance_id and variant"):
                    build_symmetry_grpo_v2_target(
                        malformed,
                        matching_plain,
                        static.iloc[:1],
                        cpu_cap=10.0,
                    )

    def test_v2_target_rejects_invalid_objective_parameters(self):
        guided = pd.DataFrame([_guided_row(1)])
        plain = pd.DataFrame([_plain_row(1)])
        static = pd.DataFrame([_static_row(1)])
        invalid_cases = [
            ("cpu_cap", np.nan),
            ("cpu_cap", np.inf),
            ("cpu_cap", -np.inf),
            ("cpu_cap", 0.0),
            ("cpu_cap", -1.0),
            ("near_cap_fraction", np.nan),
            ("near_cap_fraction", np.inf),
            ("near_cap_fraction", -np.inf),
            ("near_cap_fraction", 0.0),
            ("near_cap_fraction", -0.1),
            ("near_cap_fraction", 1.1),
            ("weighted_risk_threshold", np.nan),
            ("weighted_risk_threshold", np.inf),
            ("weighted_risk_threshold", -np.inf),
            ("eps_decisions", np.nan),
            ("eps_decisions", np.inf),
            ("eps_decisions", -np.inf),
            ("eps_decisions", -0.1),
            ("eps_conflicts", np.nan),
            ("eps_conflicts", np.inf),
            ("eps_conflicts", -np.inf),
            ("eps_conflicts", -0.1),
        ]
        defaults = {
            "cpu_cap": 10.0,
            "near_cap_fraction": 0.8,
            "weighted_risk_threshold": 0.0,
            "eps_decisions": 0.0,
            "eps_conflicts": 0.0,
        }
        for parameter, value in invalid_cases:
            with self.subTest(parameter=parameter, value=value):
                arguments = {**defaults, parameter: value}
                with self.assertRaisesRegex(ValueError, parameter):
                    build_symmetry_grpo_v2_target(
                        guided,
                        plain,
                        static,
                        **arguments,
                    )

        result = build_symmetry_grpo_v2_target(
            guided,
            plain,
            static,
            cpu_cap=10.0,
            near_cap_fraction=1.0,
            weighted_risk_threshold=-1.0,
            eps_decisions=0.0,
            eps_conflicts=0.0,
        )
        self.assertEqual(len(result), 1)

    def test_static_baseline_single_row_broadcasts_to_all_guided_samples(self):
        guided = pd.DataFrame([
            _guided_row(1, sample_id=sample_id)
            for sample_id in range(16)
        ])
        plain = pd.DataFrame([
            _plain_row(1, sample_id=sample_id)
            for sample_id in range(16)
        ])
        static = pd.DataFrame([_static_row(1, sample_id=0)])

        result = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

        self.assertEqual(len(result), 16)
        self.assertFalse(bool(result["v2_missing_static_baseline"].any()))
        self.assertTrue(bool(result["v2_positive_eligible"].all()))
        self.assertEqual(result["baseline_static_decisions"].tolist(), [100.0] * 16)
        self.assertEqual(result["baseline_static_conflicts"].tolist(), [100.0] * 16)

    def test_static_baseline_deduplicates_identical_rows_and_rejects_conflicts(self):
        guided = pd.DataFrame([_guided_row(1, sample_id=0), _guided_row(1, sample_id=1)])
        plain = pd.DataFrame([_plain_row(1, sample_id=0), _plain_row(1, sample_id=1)])
        identical = pd.DataFrame([
            _static_row(1, sample_id=0),
            _static_row(1, sample_id=1),
        ])

        result = build_symmetry_grpo_v2_target(guided, plain, identical, cpu_cap=10.0)
        self.assertFalse(bool(result["v2_missing_static_baseline"].any()))

        conflicting = identical.copy()
        conflicting.loc[1, "decisions"] = 101.0
        with self.assertRaisesRegex(ValueError, "conflicting static baseline rows for cnf_id=1"):
            build_symmetry_grpo_v2_target(guided, plain, conflicting, cpu_cap=10.0)

    def test_repaired_orbit_and_event_evidence_allows_symmetry_but_not_control(self):
        symmetry = _guided_row(
            1,
            mean_orbit_confidence=0.0,
            orbit_confidence_mean=0.9,
            event_active_orbit_fraction=0.5,
            mean_orbit_event_variance=0.2,
        )
        control = _guided_row(
            2,
            family="random_3sat_control",
            mean_orbit_confidence=0.0,
            orbit_confidence_mean=0.9,
            event_active_orbit_fraction=0.5,
            mean_orbit_event_variance=0.2,
        )

        result = build_symmetry_grpo_v2_target(
            pd.DataFrame([symmetry, control]),
            pd.DataFrame([_plain_row(1), _plain_row(2)]),
            pd.DataFrame([_static_row(1), _static_row(2)]),
            cpu_cap=10.0,
        )

        self.assertTrue(bool(result.loc[0, "v2_valid_symmetry_orbit_evidence"]))
        self.assertTrue(bool(result.loc[0, "v2_positive_eligible"]))
        self.assertTrue(bool(result.loc[1, "v2_valid_symmetry_orbit_evidence"]))
        self.assertTrue(bool(result.loc[1, "v2_control_blocked"]))
        self.assertFalse(bool(result.loc[1, "v2_positive_eligible"]))

    def test_v2_positive_requires_dual_search_improvement_and_all_evidence(self):
        guided = pd.DataFrame(
            [
                _guided_row(1),
                _guided_row(2, decisions=100.0, conflicts=100.0, **{"CPU time": 1.0}),
                _guided_row(3, family="random_3sat_control"),
                _guided_row(4, Result="UNSATISFIABLE"),
                _guided_row(5, Result="UNKNOWN"),
                _guided_row(6, **{"CPU time": 9.0}),
                _guided_row(7, echosat_weighted_risk=0.1),
                _guided_row(8, valid_orbit_count=0.0),
                _guided_row(9, decisions=120.0, conflicts=90.0),
            ]
        )
        plain = pd.DataFrame([
            _plain_row(cnf_id, decisions=200.0, conflicts=200.0)
            for cnf_id in range(1, 10)
        ])
        static = pd.DataFrame([_static_row(cnf_id) for cnf_id in range(1, 10)])

        result = build_symmetry_grpo_v2_target(
            guided,
            plain,
            static,
            cpu_cap=10.0,
            near_cap_fraction=0.8,
        )

        self.assertTrue(bool(result.loc[0, "v2_positive_eligible"]))
        self.assertTrue(bool((~result.loc[1:, "v2_positive_eligible"]).all()))
        self.assertGreater(float(result.loc[0, "search_score"]), 0.0)
        self.assertFalse(bool(result.loc[1, "v2_positive_eligible"]))
        self.assertTrue(bool((result.loc[1:, "v2_blocked_penalty"] > 0.0).all()))

    def test_v2_missing_plain_coverage_fails_closed_and_duplicate_plain_rejected(self):
        guided = pd.DataFrame([_guided_row(1), _guided_row(2)])
        incomplete = pd.DataFrame([_plain_row(1)])
        static = pd.DataFrame([_static_row(1), _static_row(2)])

        result = build_symmetry_grpo_v2_target(guided, incomplete, static, cpu_cap=10.0)

        self.assertTrue(bool(result.loc[1, "v2_missing_plain_baseline"]))
        self.assertFalse(bool(result.loc[1, "v2_positive_eligible"]))
        self.assertGreater(float(result.loc[1, "v2_blocked_penalty"]), 0.0)
        self.assertGreaterEqual(float(result.loc[1, "echosat_cost"]), 0.0)
        duplicate = pd.concat([incomplete, incomplete], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "duplicate plain cnf_id/sample_id"):
            build_symmetry_grpo_v2_target(guided.iloc[:1], duplicate, static.iloc[:1], cpu_cap=10.0)

    def test_v2_nonempty_baselines_with_missing_columns_are_rejected(self):
        guided = pd.DataFrame([_guided_row(1)])
        plain = pd.DataFrame([_plain_row(1)]).drop(columns="conflicts")
        static = pd.DataFrame([_static_row(1)])
        with self.assertRaisesRegex(ValueError, "plain missing required columns"):
            build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

        plain = pd.DataFrame([_plain_row(1)])
        static = pd.DataFrame([_static_row(1)]).drop(columns="Result")
        with self.assertRaisesRegex(ValueError, "static missing required columns"):
            build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

    def test_v2_static_baseline_missing_invalid_unsolved_or_mismatch_fails_closed(self):
        guided = pd.DataFrame([
            _guided_row(1),
            _guided_row(2),
            _guided_row(3),
            _guided_row(4),
            _guided_row(5),
        ])
        plain = pd.DataFrame([_plain_row(cnf_id) for cnf_id in range(1, 6)])
        static = pd.DataFrame([
            _static_row(1),
            _static_row(2, decisions=np.nan),
            _static_row(3, Result="UNKNOWN"),
            _static_row(4, Result="UNSATISFIABLE"),
        ])

        result = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

        self.assertTrue(bool(result.loc[0, "v2_positive_eligible"]))
        self.assertTrue(bool((~result.loc[1:, "v2_positive_eligible"]).all()))
        self.assertTrue(bool(result.loc[1, "v2_invalid_static_baseline"]))
        self.assertTrue(bool(result.loc[2, "v2_static_unsolved"]))
        self.assertTrue(bool(result.loc[3, "v2_static_result_mismatch"]))
        self.assertTrue(bool(result.loc[4, "v2_missing_static_baseline"]))

    def test_v2_search_eps_is_strictly_relative_to_static(self):
        guided = pd.DataFrame([
            _guided_row(1, decisions=99.0, conflicts=99.0, **{"CPU time": 5.0})
        ])
        plain = pd.DataFrame([_plain_row(1, decisions=1000.0, conflicts=1000.0)])
        static = pd.DataFrame([_static_row(1, decisions=100.0, conflicts=100.0)])

        default_eps = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)
        unit_eps = build_symmetry_grpo_v2_target(
            guided,
            plain,
            static,
            cpu_cap=10.0,
            eps_decisions=1.0,
            eps_conflicts=1.0,
        )

        self.assertTrue(bool(default_eps.loc[0, "v2_positive_eligible"]))
        self.assertFalse(bool(unit_eps.loc[0, "v2_positive_eligible"]))

    def test_worst_variant_negative_score_penalizes_entire_base(self):
        guided = pd.DataFrame(
            [
                _guided_row(1, base_instance_id="shared", variant="base"),
                _guided_row(2, base_instance_id="shared", variant="perm", decisions=140.0, conflicts=140.0),
            ]
        )
        plain = pd.DataFrame([_plain_row(1), _plain_row(2)])
        static = pd.DataFrame([_static_row(1), _static_row(2)])

        result = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

        self.assertLess(float(result.loc[0, "worst_variant_score"]), 0.0)
        self.assertGreater(float(result.loc[0, "worst_variant_penalty"]), 0.0)
        self.assertEqual(
            float(result.loc[0, "v2_objective_search_score"]),
            float(result.loc[0, "search_score"]),
        )
        self.assertNotEqual(
            float(result.loc[0, "v2_objective_search_score"]),
            float(result.loc[0, "worst_variant_score"]),
        )
        self.assertFalse(bool(result["v2_base_blocked"].any()))
        self.assertFalse(bool(result["v2_variant_hard_blocked"].any()))
        self.assertTrue(bool(result.loc[result["variant"].eq("base"), "v2_positive_eligible"].all()))
        self.assertFalse(bool(result.loc[result["variant"].eq("perm"), "v2_positive_eligible"].any()))
        self.assertEqual(float(result.loc[0, "v2_blocked_penalty"]), 0.0)
        self.assertLess(float(result.loc[0, "echosat_cost"]), 0.0)

    def test_row_objective_preserves_eligible_grpo_variation_and_masks_base_pressure(self):
        guided = pd.DataFrame(
            [
                _guided_row(
                    1,
                    sample_id=0,
                    base_instance_id="shared",
                    variant="safe",
                    decisions=80.0,
                    conflicts=70.0,
                    **{"CPU time": 5.0},
                ),
                _guided_row(
                    1,
                    sample_id=1,
                    base_instance_id="shared",
                    variant="safe",
                    decisions=60.0,
                    conflicts=50.0,
                    **{"CPU time": 5.0},
                ),
                _guided_row(
                    2,
                    sample_id=0,
                    base_instance_id="shared",
                    variant="bad",
                    decisions=80.0,
                    conflicts=70.0,
                    **{"CPU time": 5.0},
                ),
                _guided_row(
                    2,
                    sample_id=1,
                    base_instance_id="shared",
                    variant="bad",
                    decisions=180.0,
                    conflicts=180.0,
                    **{"CPU time": 5.0},
                ),
            ]
        )
        plain = pd.DataFrame(
            [
                _plain_row(1, sample_id=0),
                _plain_row(1, sample_id=1),
                _plain_row(2, sample_id=0),
                _plain_row(2, sample_id=1),
            ]
        )
        static = pd.DataFrame([_static_row(1), _static_row(2)])

        target = build_symmetry_grpo_v2_target(
            guided,
            plain,
            static,
            cpu_cap=10.0,
        )
        result = attach_masked_grpo_advantage(target)

        safe = result["variant"].eq("safe")
        bad = result["variant"].eq("bad")
        self.assertTrue(bool(result.loc[safe, "v2_positive_eligible"].all()))
        self.assertFalse(bool(result.loc[bad, "v2_positive_eligible"].any()))
        self.assertLess(float(result["worst_variant_score"].max()), 0.0)
        self.assertGreater(result.loc[safe, "v2_objective_search_score"].nunique(), 1)
        self.assertGreater(float(result.loc[safe, "grpo_group_std_cost"].min()), 0.0)
        self.assertTrue(bool((result.loc[safe, "advantage"] > 0.0).any()))
        self.assertTrue(bool((result.loc[~result["v2_positive_eligible"], "advantage"] <= 0.0).all()))
        bad_candidate = bad & result["v2_row_positive_candidate"]
        self.assertTrue(bool(bad_candidate.any()))
        self.assertTrue(bool((result.loc[bad_candidate, "v2_blocked_penalty"] > 0.0).all()))
        self.assertTrue(bool((result.loc[bad_candidate, "advantage"] < 0.0).all()))


class Task7IntegrationTests(unittest.TestCase):
    def test_plain_baseline_is_v2_only(self):
        dataset = SimpleNamespace()
        data_list = [_cached_samples(1, 1)]
        v2_baselines = {}
        with patch("train_rlaf.compute_plain_solver_stats", return_value=pd.DataFrame({"cnf_id": [1]})) as compute:
            cfg = _v2_cfg()
            cfg.solver.solver = "glucose_weighted"
            ensure_plain_unguided_baseline(v2_baselines, dataset, data_list, cfg)
        self.assertIn("plain_unguided", v2_baselines)
        compute.assert_called_once()
        self.assertEqual(compute.call_args.kwargs["solver"], "glucose")

        legacy_baselines = {}
        with patch("train_rlaf.compute_plain_solver_stats") as compute:
            ensure_plain_unguided_baseline(
                legacy_baselines,
                dataset,
                data_list,
                _v2_cfg("symmetry_grpo_v1_8"),
            )
        self.assertEqual(legacy_baselines, {})
        compute.assert_not_called()

    def test_plain_baseline_cache_hits_misses_and_returns_copies(self):
        dataset = SimpleNamespace()
        data_list = [_cached_samples(0, 2)]
        cfg = _v2_cfg()
        computed = pd.DataFrame(
            {
                "cnf_id": [0, 0],
                "sample_id": [0, 1],
                "file": ["zero.cnf", "zero.cnf"],
                "decisions": [10.0, 10.0],
            }
        )
        with patch("train_rlaf.compute_plain_solver_stats", return_value=computed) as compute:
            first = {}
            ensure_plain_unguided_baseline(first, dataset, data_list, cfg)
            first["plain_unguided"].loc[0, "decisions"] = 999.0
            second = {}
            ensure_plain_unguided_baseline(second, dataset, data_list, cfg)
            self.assertEqual(float(second["plain_unguided"].loc[0, "decisions"]), 10.0)
            self.assertEqual(compute.call_count, 1)

            cfg.solver.params["cpu-lim"] = 20.0
            third = {}
            ensure_plain_unguided_baseline(third, dataset, data_list, cfg)
            self.assertEqual(compute.call_count, 2)

    def test_plain_baseline_cache_falls_back_when_dataset_disallows_attributes(self):
        class SlotDataset:
            __slots__ = ()

        dataset = SlotDataset()
        data_list = [_cached_samples(0, 1)]
        cfg = _v2_cfg()
        computed = pd.DataFrame({"cnf_id": [0], "sample_id": [0], "file": ["zero.cnf"]})
        with patch("train_rlaf.compute_plain_solver_stats", return_value=computed) as compute:
            ensure_plain_unguided_baseline({}, dataset, data_list, cfg)
            ensure_plain_unguided_baseline({}, dataset, data_list, cfg)
        self.assertEqual(compute.call_count, 1)

    def test_v18_grpo_normalization_remains_numerically_unchanged(self):
        frame = pd.DataFrame(
            {
                "cnf_id": [1, 1],
                "sample_id": [0, 1],
                "echosat_cost": [1.0, 3.0],
                "echosat_advantage_weight": [1.0, 2.0],
            }
        )

        result = attach_grpo_advantage_columns(frame, _v2_cfg("symmetry_grpo_v1_8"))

        expected_raw = 1.0 / np.sqrt(2.0)
        self.assertAlmostEqual(float(result.loc[0, "grpo_raw_advantage"]), expected_raw)
        self.assertAlmostEqual(float(result.loc[1, "grpo_raw_advantage"]), -expected_raw)
        self.assertAlmostEqual(float(result.loc[1, "advantage"]), -2.0 * expected_raw)


if __name__ == "__main__":
    unittest.main()
