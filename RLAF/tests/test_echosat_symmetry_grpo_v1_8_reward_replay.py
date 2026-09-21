from __future__ import annotations

import unittest

import pandas as pd

from replay_echosat_symmetry_grpo_v1_8_reward import (
    apply_v18_objective_repair,
    build_checks,
    bool_series,
    summarize,
)


class EchoSATSymmetryGRPOV18RewardReplayTests(unittest.TestCase):
    def test_bool_series_accepts_float_flags_from_csv(self) -> None:
        flags = bool_series(pd.Series([1.0, 0.0, "1.0", "0.0", "true", "false"]))

        self.assertEqual(flags.tolist(), [True, False, True, False, True, False])

    def test_v18_clamps_blocked_training_raw_and_final_advantage(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "cnf_id": 1,
                    "family": "random_3sat_control",
                    "base_instance_id": "random_3sat_control_v1",
                    "variant": "base",
                    "echosat_replay_role": "random_control",
                    "echosat_search_ok": True,
                    "echosat_search_blowup": False,
                    "echosat_positive_allowed": False,
                    "echosat_r_cpu_clipped": 0.0,
                    "echosat_weighted_path_risk_penalty": 0.0,
                    "echosat_near_cap_penalty": 0.0,
                    "grpo_raw_advantage": 0.8,
                    "grpo_weighted_advantage_before_clamp": 0.8,
                    "grpo_final_advantage": 0.8,
                    "advantage": 0.8,
                },
                {
                    "cnf_id": 1,
                    "family": "subset_cardinality",
                    "base_instance_id": "subset_cardinality_bw12",
                    "variant": "perm_seed1730",
                    "echosat_replay_role": "subset_failure",
                    "echosat_search_ok": True,
                    "echosat_search_blowup": False,
                    "echosat_positive_allowed": False,
                    "echosat_positive_blocked_subset_failure": True,
                    "echosat_r_cpu_clipped": 0.0,
                    "echosat_weighted_path_risk_penalty": 0.0,
                    "echosat_near_cap_penalty": 0.0,
                    "grpo_raw_advantage": 0.6,
                    "grpo_weighted_advantage_before_clamp": 0.6,
                    "grpo_final_advantage": 0.6,
                    "advantage": 0.6,
                },
                {
                    "cnf_id": 1,
                    "family": "complete_coloring",
                    "base_instance_id": "k8_color7",
                    "variant": "base",
                    "echosat_replay_role": "other",
                    "echosat_search_ok": False,
                    "echosat_search_blowup": False,
                    "echosat_positive_allowed": False,
                    "echosat_r_cpu_clipped": 0.2,
                    "echosat_weighted_path_risk_penalty": 0.0,
                    "echosat_near_cap_penalty": 0.0,
                    "grpo_raw_advantage": 0.5,
                    "grpo_weighted_advantage_before_clamp": 0.5,
                    "grpo_final_advantage": 0.5,
                    "advantage": 0.5,
                },
            ]
        )

        repaired = apply_v18_objective_repair(frame)

        self.assertTrue(bool(repaired["echosat_v18_blocked_positive_signal"].all()))
        self.assertFalse(bool((repaired["grpo_raw_advantage"] > 1.0e-12).any()))
        self.assertFalse(bool((repaired["grpo_final_advantage"] > 1.0e-12).any()))
        self.assertTrue(bool(repaired["grpo_positive_raw_advantage_clamped"].all()))
        self.assertTrue(bool(repaired["grpo_positive_advantage_clamped"].all()))

    def test_v18_boosts_hard_negative_search_ok_without_boosting_failures(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "cnf_id": 1,
                    "family": "complete_coloring",
                    "base_instance_id": "k10_color9",
                    "variant": "base",
                    "echosat_replay_role": "hard_negative",
                    "echosat_search_ok": True,
                    "echosat_search_blowup": False,
                    "echosat_positive_allowed": True,
                    "echosat_r_search_decisions": 0.2,
                    "echosat_r_search_conflicts": 0.3,
                    "echosat_r_cpu_clipped": 0.0,
                    "echosat_weighted_path_risk_penalty": 0.0,
                    "echosat_near_cap_penalty": 0.0,
                    "echosat_symmetry_reward": 0.1,
                    "echosat_cost": -0.1,
                    "grpo_raw_advantage": 0.4,
                    "grpo_weighted_advantage_before_clamp": 0.4,
                    "grpo_final_advantage": 0.4,
                    "advantage": 0.4,
                },
                {
                    "cnf_id": 1,
                    "family": "complete_coloring",
                    "base_instance_id": "k10_color9",
                    "variant": "perm_seed1730",
                    "echosat_replay_role": "hard_negative_failure",
                    "echosat_search_ok": False,
                    "echosat_search_blowup": True,
                    "echosat_positive_allowed": False,
                    "echosat_r_search_decisions": 0.0,
                    "echosat_r_search_conflicts": 0.0,
                    "echosat_r_cpu_clipped": 0.0,
                    "echosat_weighted_path_risk_penalty": 0.0,
                    "echosat_near_cap_penalty": 0.0,
                    "grpo_raw_advantage": 0.7,
                    "grpo_weighted_advantage_before_clamp": 0.7,
                    "grpo_final_advantage": 0.7,
                    "advantage": 0.7,
                },
            ]
        )

        repaired = apply_v18_objective_repair(frame, hard_negative_pressure_multiplier=1.5)

        positive = repaired[repaired["echosat_replay_role"].eq("hard_negative")].iloc[0]
        failure = repaired[repaired["echosat_replay_role"].eq("hard_negative_failure")].iloc[0]
        self.assertGreater(float(positive["grpo_final_advantage"]), float(positive["v17_grpo_final_advantage"]))
        self.assertGreater(float(positive["echosat_v18_hard_negative_pressure"]), 0.0)
        self.assertLessEqual(float(failure["grpo_raw_advantage"]), 0.0)
        self.assertLessEqual(float(failure["grpo_final_advantage"]), 0.0)
        self.assertEqual(float(failure["echosat_v18_hard_negative_pressure"]), 0.0)

    def test_build_checks_requires_no_blocked_raw_or_final_positive(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "echosat_replay_role": "anchor",
                    "echosat_search_ok": True,
                    "echosat_v18_blocked_positive_signal": False,
                    "echosat_v18_cpu_only_search_bad": False,
                    "echosat_v18_weighted_risk_blocked": False,
                    "echosat_v18_near_cap_blocked": False,
                    "grpo_raw_advantage": 0.3,
                    "grpo_final_advantage": 0.3,
                    "v17_grpo_final_advantage": 0.2,
                },
                {
                    "echosat_replay_role": "hard_negative",
                    "echosat_search_ok": True,
                    "echosat_v18_blocked_positive_signal": False,
                    "echosat_v18_cpu_only_search_bad": False,
                    "echosat_v18_weighted_risk_blocked": False,
                    "echosat_v18_near_cap_blocked": False,
                    "grpo_raw_advantage": 0.5,
                    "grpo_final_advantage": 0.5,
                    "v17_grpo_final_advantage": 0.4,
                },
                {
                    "echosat_replay_role": "random_control",
                    "echosat_search_ok": True,
                    "echosat_v18_blocked_positive_signal": True,
                    "echosat_v18_cpu_only_search_bad": False,
                    "echosat_v18_weighted_risk_blocked": False,
                    "echosat_v18_near_cap_blocked": False,
                    "grpo_raw_advantage": 0.0,
                    "grpo_final_advantage": 0.0,
                    "v17_grpo_final_advantage": 0.4,
                },
            ]
        )

        role, base, checks_frame = summarize(frame)
        checks = build_checks(frame, role, base, checks_frame)

        self.assertTrue(bool(checks.loc[checks["check"].eq("random_control_no_raw_or_final_positive"), "passed"].iloc[0]))
        self.assertTrue(bool(checks.loc[checks["check"].eq("blocked_rows_no_raw_or_final_positive"), "passed"].iloc[0]))
        self.assertTrue(
            bool(checks.loc[checks["check"].eq("hard_negative_final_pressure_not_weaker_than_v1_7"), "passed"].iloc[0])
        )


if __name__ == "__main__":
    unittest.main()
