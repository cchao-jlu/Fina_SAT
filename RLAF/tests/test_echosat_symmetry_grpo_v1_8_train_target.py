from __future__ import annotations

import unittest

import pandas as pd
from omegaconf import OmegaConf

from train_rlaf import add_echosat_target, attach_grpo_advantage_columns, echosat_replay_role


def _cfg(target_mode: str = "symmetry_grpo_v1_8", pressure_multiplier: float = 1.5):
    return OmegaConf.create(
        {
            "training": {
                "target_stat": "echosat_cost",
                "echosat_target_mode": target_mode,
                "echosat_hard_negative_base_ids": ["k10_color9"],
                "echosat_anchor_base_ids": ["k9_color8"],
                "echosat_subset_failure_base_id": "subset_cardinality_bw12",
                "echosat_subset_failure_variant": "perm_seed1730",
                "echosat_decisions_weight": 0.55,
                "echosat_conflicts_weight": 0.45,
                "echosat_final_cpu_weight": 0.2,
                "echosat_cpu_reduction_clip": 0.5,
                "echosat_search_eps_decisions": 0.0,
                "echosat_search_eps_conflicts": 0.0,
                "echosat_weighted_risk_positive_threshold": 0.0,
                "echosat_near_cap_fraction": 0.8,
                "echosat_random_control_penalty_weight": 4.0,
                "echosat_control_penalty_weight": 2.0,
                "echosat_weighted_risk_weight": 1.25,
                "echosat_near_cap_penalty_weight": 1.0,
                "echosat_hard_negative_penalty_weight": 8.0,
                "echosat_anchor_failure_penalty_weight": 8.0,
                "echosat_subset_failure_penalty_weight": 8.0,
                "echosat_v18_hard_negative_pressure_multiplier": pressure_multiplier,
            },
            "solver": {"params": {"cpu-lim": 100.0}},
        }
    )


def _sym_row(cnf_id: int, sample_id: int, **overrides) -> dict:
    if "CPU_time" in overrides:
        overrides["CPU time"] = overrides.pop("CPU_time")
    row = {
        "cnf_id": cnf_id,
        "sample_id": sample_id,
        "family": "complete_coloring",
        "control_type": "symmetric",
        "symmetry_strength": "strong",
        "base_instance_id": f"sym_case_{cnf_id}",
        "variant": "base",
        "Result": "SATISFIABLE",
        "expected_result": "SATISFIABLE",
        "CPU time": 9.0,
        "decisions": 80.0,
        "conflicts": 80.0,
        "valid_orbit_count": 4.0,
        "orbit_confidence_mean": 1.0,
        "event_state_l2_sum_train": 1.0,
        "event_state_nonzero_vars_train": 4.0,
    }
    row.update(overrides)
    return row


def _baselines() -> dict[str, pd.DataFrame]:
    static_rows = [
        {"cnf_id": 1, "sample_id": 0, "CPU time": 10.0, "decisions": 100.0, "conflicts": 100.0},
        {"cnf_id": 2, "sample_id": 0, "CPU time": 10.0, "decisions": 100.0, "conflicts": 100.0},
        {"cnf_id": 3, "sample_id": 0, "CPU time": 90.0, "decisions": 100.0, "conflicts": 100.0},
    ]
    neutral_rows = [
        {"cnf_id": 1, "sample_id": 0, "CPU time": 10.0, "decisions": 100.0, "conflicts": 100.0},
        {"cnf_id": 2, "sample_id": 0, "CPU time": 5.0, "decisions": 100.0, "conflicts": 100.0},
        {"cnf_id": 3, "sample_id": 0, "CPU time": 90.0, "decisions": 100.0, "conflicts": 100.0},
    ]
    return {
        "static_weighted": pd.DataFrame(static_rows),
        "neutral_weighted": pd.DataFrame(neutral_rows),
    }


def _solver_stats() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _sym_row(1, 0, base_instance_id="k10_color9"),
            _sym_row(
                1,
                1,
                family="random_3sat_control",
                control_type="non_symmetric_control",
                symmetry_strength="none",
                base_instance_id="random_3sat_control_v1",
            ),
            _sym_row(1, 2, base_instance_id="subset_cardinality_bw12", variant="perm_seed1730"),
            _sym_row(1, 3, CPU_time=5.0, decisions=100.0, conflicts=100.0),
            _sym_row(1, 4, base_instance_id="k10_color9", variant="perm_seed9999", CPU_time=12.0, decisions=130.0, conflicts=130.0),
            _sym_row(2, 0, base_instance_id="weighted_risk_case"),
            _sym_row(2, 1, base_instance_id="weighted_risk_blowup", CPU_time=12.0, decisions=130.0, conflicts=130.0),
            _sym_row(3, 0, base_instance_id="near_cap_case", CPU_time=70.0),
            _sym_row(3, 1, base_instance_id="near_cap_blowup", CPU_time=95.0, decisions=130.0, conflicts=130.0),
        ]
    )


class EchoSATSymmetryGRPOV18TrainTargetTests(unittest.TestCase):
    def test_v18_formal_target_clamps_all_blocked_positive_signals(self) -> None:
        targeted = add_echosat_target(_solver_stats(), _cfg(), _baselines(), None, None, None)
        with_advantage = attach_grpo_advantage_columns(targeted, _cfg())
        roles = echosat_replay_role(with_advantage, _cfg())
        blocked = with_advantage["echosat_v18_blocked_positive_signal"].astype(bool)

        self.assertIn("symmetry_grpo_v1_8", set(with_advantage["echosat_target_mode"]))
        self.assertTrue(bool(with_advantage.loc[roles.eq("random_control"), "echosat_v18_blocked_positive_signal"].all()))
        self.assertTrue(bool(with_advantage.loc[roles.eq("subset_failure"), "echosat_v18_blocked_positive_signal"].all()))
        self.assertTrue(bool(with_advantage.loc[3:3, "echosat_v18_cpu_only_search_bad"].iloc[0]))
        self.assertTrue(bool(with_advantage.loc[5:5, "echosat_v18_weighted_risk_blocked"].iloc[0]))
        self.assertTrue(bool(with_advantage.loc[7:7, "echosat_v18_near_cap_blocked"].iloc[0]))
        self.assertFalse(bool((with_advantage.loc[blocked, "echosat_advantage_raw_upper_bound"] > 0.0).any()))
        self.assertFalse(bool((with_advantage.loc[blocked, "echosat_advantage_upper_bound"] > 0.0).any()))
        self.assertFalse(bool((with_advantage.loc[blocked, "grpo_raw_advantage"] > 1.0e-12).any()))
        self.assertFalse(bool((with_advantage.loc[blocked, "grpo_final_advantage"] > 1.0e-12).any()))

    def test_v18_formal_target_adds_hard_negative_pressure_to_search_ok_rows(self) -> None:
        v17 = attach_grpo_advantage_columns(
            add_echosat_target(_solver_stats(), _cfg("symmetry_grpo_v1_7"), _baselines(), None, None, None),
            _cfg("symmetry_grpo_v1_7"),
        )
        v18 = attach_grpo_advantage_columns(
            add_echosat_target(_solver_stats(), _cfg("symmetry_grpo_v1_8", pressure_multiplier=1.5), _baselines(), None, None, None),
            _cfg("symmetry_grpo_v1_8", pressure_multiplier=1.5),
        )

        success = v18["base_instance_id"].eq("k10_color9") & v18["variant"].eq("base")
        failure = v18["base_instance_id"].eq("k10_color9") & v18["variant"].eq("perm_seed9999")

        self.assertGreater(float(v18.loc[success, "echosat_v18_hard_negative_pressure"].iloc[0]), 0.0)
        self.assertGreater(float(v18.loc[success, "echosat_advantage_weight"].iloc[0]), float(v17.loc[success, "echosat_advantage_weight"].iloc[0]))
        self.assertGreater(float(v18.loc[success, "grpo_final_advantage"].iloc[0]), float(v17.loc[success, "grpo_final_advantage"].iloc[0]))
        self.assertEqual(float(v18.loc[failure, "echosat_v18_hard_negative_pressure"].iloc[0]), 0.0)
        self.assertLessEqual(float(v18.loc[failure, "grpo_raw_advantage"].iloc[0]), 0.0)
        self.assertLessEqual(float(v18.loc[failure, "grpo_final_advantage"].iloc[0]), 0.0)


if __name__ == "__main__":
    unittest.main()
