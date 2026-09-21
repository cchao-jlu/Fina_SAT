from __future__ import annotations

import unittest

import pandas as pd

from analyze_echosat_symmetry_grpo_v1_7_failure_attribution import (
    bool_series,
    compare_against_reference,
    load_observation_frame,
    summarize_candidate,
    target_role,
    warmup_disagreement,
)


class EchoSATSymmetryGRPOV17FailureAttributionTests(unittest.TestCase):
    def test_bool_series_treats_float_one_as_true_for_csv_flags(self) -> None:
        flags = bool_series(pd.Series([1.0, 0.0, "1.0", "0.0", "true", "false"]))

        self.assertEqual(flags.tolist(), [True, False, True, False, True, False])

    def test_target_role_marks_required_audit_slices(self) -> None:
        rows = [
            ({"base_instance_id": "k9_color8"}, "anchor"),
            ({"base_instance_id": "php_p9_h8"}, "anchor"),
            ({"base_instance_id": "k10_color9"}, "hard_negative"),
            ({"base_instance_id": "php_p10_h9"}, "hard_negative"),
            (
                {
                    "base_instance_id": "subset_cardinality_bw12",
                    "variant": "perm_seed1730",
                },
                "subset_perm_failure",
            ),
            (
                {
                    "base_instance_id": "subset_cardinality_bw12",
                    "variant": "perm_seed1731",
                },
                "subset_other_variant",
            ),
            (
                {
                    "family": "random_3sat_control",
                    "control_type": "non_symmetric_control",
                    "base_instance_id": "random_3sat_control_v1",
                },
                "random_control",
            ),
            ({"base_instance_id": "other"}, "other"),
        ]

        for row, expected in rows:
            with self.subTest(row=row):
                self.assertEqual(target_role(pd.Series(row)), expected)

    def test_load_observation_frame_derives_search_flags(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "warmup_conflicts": 1,
                    "base_instance_id": "k9_color8",
                    "variant": "base",
                    "repeat_id": 0,
                    "family": "complete_coloring",
                    "control_type": "strong_symmetry",
                    "checkpoint": "/tmp/iter=50.pt",
                    "adapter_cached_decisions_delta": -2.0,
                    "adapter_cached_conflicts_delta": -1.0,
                    "adapter_cached_final_cpu_delta": 0.4,
                },
                {
                    "warmup_conflicts": 1,
                    "base_instance_id": "random_3sat_control_v1",
                    "variant": "base",
                    "repeat_id": 0,
                    "family": "random_3sat_control",
                    "control_type": "non_symmetric_control",
                    "checkpoint": "/tmp/iter=50.pt",
                    "adapter_cached_decisions_delta": 3.0,
                    "adapter_cached_conflicts_delta": -1.0,
                    "adapter_cached_final_cpu_delta": -0.2,
                },
            ]
        )

        loaded = load_observation_frame(frame, candidate_label="iter=50")

        self.assertTrue(bool(loaded.loc[0, "search_ok"]))
        self.assertFalse(bool(loaded.loc[0, "search_blowup"]))
        self.assertFalse(bool(loaded.loc[0, "cpu_only_win"]))
        self.assertEqual(loaded.loc[0, "target_role"], "anchor")
        self.assertFalse(bool(loaded.loc[0, "random_control"]))
        self.assertFalse(bool(loaded.loc[1, "search_ok"]))
        self.assertTrue(bool(loaded.loc[1, "search_blowup"]))
        self.assertTrue(bool(loaded.loc[1, "cpu_only_win"]))
        self.assertTrue(bool(loaded.loc[1, "random_control"]))

    def test_compare_against_reference_keeps_candidate_and_delta_columns(self) -> None:
        reference = load_observation_frame(
            pd.DataFrame(
                [
                    {
                        "warmup_conflicts": 1,
                        "base_instance_id": "k10_color9",
                        "variant": "base",
                        "repeat_id": 0,
                        "family": "complete_coloring",
                        "control_type": "strong_symmetry",
                        "checkpoint": "/tmp/v1_2/iter=15.pt",
                        "adapter_cached_decisions_delta": -10.0,
                        "adapter_cached_conflicts_delta": -8.0,
                        "adapter_cached_final_cpu_delta": -0.1,
                    }
                ]
            ),
            candidate_label="v1_2_iter15",
        )
        candidate = load_observation_frame(
            pd.DataFrame(
                [
                    {
                        "warmup_conflicts": 1,
                        "base_instance_id": "k10_color9",
                        "variant": "base",
                        "repeat_id": 0,
                        "family": "complete_coloring",
                        "control_type": "strong_symmetry",
                        "checkpoint": "/tmp/v1_7/iter=50.pt",
                        "adapter_cached_decisions_delta": 5.0,
                        "adapter_cached_conflicts_delta": 3.0,
                        "adapter_cached_final_cpu_delta": -0.3,
                    }
                ]
            ),
            candidate_label="iter=50",
        )

        paired = compare_against_reference(reference, candidate)

        self.assertEqual(len(paired), 1)
        row = paired.iloc[0]
        self.assertEqual(row["candidate_label"], "iter=50")
        self.assertEqual(row["target_role"], "hard_negative")
        self.assertTrue(bool(row["reference_search_ok"]))
        self.assertFalse(bool(row["candidate_search_ok"]))
        self.assertTrue(bool(row["search_ok_lost_vs_reference"]))
        self.assertEqual(float(row["adapter_cached_decisions_delta_change_vs_reference"]), 15.0)
        self.assertEqual(float(row["adapter_cached_conflicts_delta_change_vs_reference"]), 11.0)

    def test_summarize_candidate_reports_key_fraction_constraints(self) -> None:
        rows = [
            {
                "candidate_label": "iter=50",
                "warmup_conflicts": 1,
                "family": "complete_coloring",
                "base_instance_id": "k9_color8",
                "variant": "base",
                "repeat_id": 0,
                "target_role": "anchor",
                "random_control": False,
                "candidate_search_ok": True,
                "candidate_search_blowup": False,
                "candidate_cpu_only_win": False,
                "reference_search_ok": True,
                "adapter_cached_decisions_delta_candidate": -2.0,
                "adapter_cached_conflicts_delta_candidate": -1.0,
                "adapter_cached_final_cpu_delta_candidate": 0.1,
            },
            {
                "candidate_label": "iter=50",
                "warmup_conflicts": 1,
                "family": "complete_coloring",
                "base_instance_id": "k10_color9",
                "variant": "base",
                "repeat_id": 0,
                "target_role": "hard_negative",
                "random_control": False,
                "candidate_search_ok": False,
                "candidate_search_blowup": True,
                "candidate_cpu_only_win": True,
                "reference_search_ok": True,
                "adapter_cached_decisions_delta_candidate": 4.0,
                "adapter_cached_conflicts_delta_candidate": 2.0,
                "adapter_cached_final_cpu_delta_candidate": -0.2,
            },
            {
                "candidate_label": "iter=50",
                "warmup_conflicts": 1,
                "family": "random_3sat_control",
                "base_instance_id": "random_3sat_control_v1",
                "variant": "base",
                "repeat_id": 0,
                "target_role": "random_control",
                "random_control": True,
                "candidate_search_ok": True,
                "candidate_search_blowup": False,
                "candidate_cpu_only_win": False,
                "reference_search_ok": False,
                "adapter_cached_decisions_delta_candidate": -5.0,
                "adapter_cached_conflicts_delta_candidate": -3.0,
                "adapter_cached_final_cpu_delta_candidate": -0.3,
            },
        ]

        summary = summarize_candidate(pd.DataFrame(rows))
        row = summary.iloc[0]

        self.assertEqual(row["candidate_label"], "iter=50")
        self.assertEqual(int(row["rows"]), 3)
        self.assertEqual(float(row["anchor_search_ok_frac"]), 1.0)
        self.assertEqual(float(row["hard_negative_search_ok_frac"]), 0.0)
        self.assertEqual(float(row["random_control_search_ok_frac"]), 1.0)
        self.assertEqual(float(row["cpu_only_win_frac"]), 1.0 / 3.0)

    def test_warmup_disagreement_detects_wc1_wc3_instability(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "candidate_label": "iter=50",
                    "warmup_conflicts": 1,
                    "base_instance_id": "k10_color9",
                    "variant": "base",
                    "repeat_id": 0,
                    "candidate_search_ok": True,
                },
                {
                    "candidate_label": "iter=50",
                    "warmup_conflicts": 3,
                    "base_instance_id": "k10_color9",
                    "variant": "base",
                    "repeat_id": 0,
                    "candidate_search_ok": False,
                },
                {
                    "candidate_label": "iter=50",
                    "warmup_conflicts": 1,
                    "base_instance_id": "k9_color8",
                    "variant": "base",
                    "repeat_id": 0,
                    "candidate_search_ok": True,
                },
                {
                    "candidate_label": "iter=50",
                    "warmup_conflicts": 3,
                    "base_instance_id": "k9_color8",
                    "variant": "base",
                    "repeat_id": 0,
                    "candidate_search_ok": True,
                },
            ]
        )

        disagreement = warmup_disagreement(frame)

        self.assertEqual(len(disagreement), 1)
        self.assertEqual(disagreement.iloc[0]["base_instance_id"], "k10_color9")
        self.assertTrue(bool(disagreement.iloc[0]["wc1_search_ok"]))
        self.assertFalse(bool(disagreement.iloc[0]["wc3_search_ok"]))


if __name__ == "__main__":
    unittest.main()
