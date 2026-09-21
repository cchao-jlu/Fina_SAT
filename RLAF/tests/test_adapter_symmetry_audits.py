from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd
import torch

from audit_adapter_permutation_consistency import build_consistency_frame
from audit_adapter_negative_cases import label_negative_cases
from audit_adapter_permutation_alignment import inverse_align_new_to_old
from build_symmetry_family_heldout_trace import cnf_id_to_manifest_row
from summarize_adapter_family_heldout_multiseed import summarize_multiseed, summarize_seed_runs


class AdapterPermutationConsistencyTests(unittest.TestCase):
    def test_consistency_groups_event_valid_renamed_orbits(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "family": "f",
                    "base_instance_id": "b0",
                    "instance_id": "b0",
                    "variant": "base",
                    "orbit": "o",
                    "orbit_valid": True,
                    "event_row_valid": True,
                    "event_identity_positive": True,
                    "event_identity_zero": False,
                    "static_mu_mean": 0.0,
                    "static_mu_range": 1.0e-8,
                    "event_feature_l2_range": 1.0,
                    "adapted_mu_mean": 0.5,
                    "adapted_mu_range": 0.2,
                    "adapter_identity_gain": 0.2,
                },
                {
                    "family": "f",
                    "base_instance_id": "b0",
                    "instance_id": "b0_perm",
                    "variant": "perm_seed1730",
                    "orbit": "o",
                    "orbit_valid": True,
                    "event_row_valid": True,
                    "event_identity_positive": True,
                    "event_identity_zero": False,
                    "static_mu_mean": 0.0,
                    "static_mu_range": 2.0e-8,
                    "event_feature_l2_range": 1.5,
                    "adapted_mu_mean": 0.7,
                    "adapted_mu_range": 0.4,
                    "adapter_identity_gain": 0.4,
                },
                {
                    "family": "f",
                    "base_instance_id": "b1",
                    "instance_id": "b1",
                    "variant": "base",
                    "orbit": "o",
                    "orbit_valid": True,
                    "event_row_valid": True,
                    "event_identity_positive": True,
                    "event_identity_zero": False,
                    "static_mu_mean": 0.0,
                    "static_mu_range": 1.0e-8,
                    "event_feature_l2_range": 2.0,
                    "adapted_mu_mean": 0.9,
                    "adapted_mu_range": 0.8,
                    "adapter_identity_gain": 0.8,
                },
            ]
        )
        consistency = build_consistency_frame(
            frame,
            metadata_available={"b0": True, "b0_perm": True},
            row_filter="event-valid",
        )
        self.assertEqual(len(consistency), 1)
        row = consistency.iloc[0]
        self.assertEqual(row["base_instance_id"], "b0")
        self.assertEqual(row["variants"], 2)
        self.assertTrue(bool(row["permutation_metadata_available"]))
        self.assertAlmostEqual(float(row["adapted_mu_range_variant_range"]), 0.2, places=6)


class FamilyHeldoutTraceMappingTests(unittest.TestCase):
    def test_cnf_id_mapping_prefers_solver_stats_file_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.cnf"
            b = root / "b.cnf"
            a.write_text("p cnf 1 0\n", encoding="utf-8")
            b.write_text("p cnf 1 0\n", encoding="utf-8")
            manifest = pd.DataFrame(
                [
                    {"family": "family_a", "cnf_path": str(a), "instance_id": "a"},
                    {"family": "family_b", "cnf_path": str(b), "instance_id": "b"},
                ]
            )
            payload = {
                "solver_stats": pd.DataFrame(
                    [
                        {"cnf_id": 0, "file": str(b)},
                        {"cnf_id": 1, "file": str(a)},
                    ]
                )
            }
            mapping = cnf_id_to_manifest_row(payload, manifest)
            self.assertEqual(str(mapping[0]["family"]), "family_b")
            self.assertEqual(str(mapping[1]["family"]), "family_a")


class VariablePermutationAlignmentTests(unittest.TestCase):
    def test_inverse_alignment_uses_old_to_new_permutation(self) -> None:
        permuted = torch.tensor([[30.0], [10.0], [20.0]])
        # old 1 -> new 2, old 2 -> new 3, old 3 -> new 1
        aligned = inverse_align_new_to_old(permuted, [2, 3, 1])
        self.assertEqual(aligned.view(-1).tolist(), [10.0, 20.0, 30.0])


class AdapterNegativeCaseTests(unittest.TestCase):
    def test_negative_case_labels_distinguish_zero_and_nonzero_events(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "orbit": "o",
                    "family": "f",
                    "instance_id": "i0",
                    "orbit_valid": True,
                    "event_row_valid": False,
                    "event_row_valid_reason": "no_solver_activity",
                    "audit_status": "ok",
                    "event_feature_l2_range": 0.0,
                    "static_mu_range": 1.0e-8,
                    "adapted_mu_range": 1.0e-7,
                },
                {
                    "orbit": "o",
                    "family": "f",
                    "instance_id": "i1",
                    "orbit_valid": True,
                    "event_row_valid": False,
                    "event_row_valid_reason": "no_solver_activity",
                    "audit_status": "ok",
                    "event_feature_l2_range": 0.2,
                    "static_mu_range": 1.0e-8,
                    "adapted_mu_range": 0.01,
                },
            ]
        )
        labelled = label_negative_cases(frame, event_eps=1.0e-6, adapter_eps=1.0e-4)
        self.assertEqual(labelled.loc[0, "negative_case_type"], "no_activity_zero_event")
        self.assertFalse(bool(labelled.loc[0, "adapter_negative_violation"]))
        self.assertEqual(labelled.loc[1, "negative_case_type"], "no_activity_event_nonzero")
        self.assertTrue(bool(labelled.loc[1, "adapter_negative_violation"]))


class AdapterHeldoutMultiseedSummaryTests(unittest.TestCase):
    def test_multiseed_summary_uses_valid_heldout_rows(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "heldout_family": "family_a",
                    "train_seed": 1,
                    "family": "family_a",
                    "adapter_train_split": "heldout",
                    "instance_id": "held_1",
                    "orbit": "o",
                    "event_row_valid": True,
                    "orbit_valid": True,
                    "adapter_identity_gain": 0.2,
                    "adapted_mu_range": 0.2,
                },
                {
                    "heldout_family": "family_a",
                    "train_seed": 1,
                    "family": "family_a",
                    "adapter_train_split": "heldout",
                    "instance_id": "held_invalid",
                    "orbit": "o",
                    "event_row_valid": False,
                    "orbit_valid": True,
                    "adapter_identity_gain": 99.0,
                    "adapted_mu_range": 99.0,
                },
                {
                    "heldout_family": "family_a",
                    "train_seed": 1,
                    "family": "family_b",
                    "adapter_train_split": "train",
                    "instance_id": "train_1",
                    "orbit": "o",
                    "event_row_valid": True,
                    "orbit_valid": True,
                    "adapter_identity_gain": 0.5,
                    "adapted_mu_range": 0.5,
                },
                {
                    "heldout_family": "family_a",
                    "train_seed": 2,
                    "family": "family_a",
                    "adapter_train_split": "heldout",
                    "instance_id": "held_1",
                    "orbit": "o",
                    "event_row_valid": True,
                    "orbit_valid": True,
                    "adapter_identity_gain": 0.4,
                    "adapted_mu_range": 0.4,
                },
                {
                    "heldout_family": "family_a",
                    "train_seed": 2,
                    "family": "family_b",
                    "adapter_train_split": "train",
                    "instance_id": "train_1",
                    "orbit": "o",
                    "event_row_valid": True,
                    "orbit_valid": True,
                    "adapter_identity_gain": 0.6,
                    "adapted_mu_range": 0.6,
                },
            ]
        )
        baseline = pd.DataFrame(
            [
                {
                    "family": "family_a",
                    "event_row_valid": True,
                    "orbit_valid": True,
                    "adapter_identity_gain": 0.3,
                }
            ]
        )

        seed_summary = summarize_seed_runs(frame, baseline=baseline)
        multiseed = summarize_multiseed(seed_summary, bootstrap_seed=7, bootstrap_samples=100)

        self.assertEqual(len(seed_summary), 2)
        self.assertEqual(seed_summary["heldout_valid_rows"].tolist(), [1, 1])
        self.assertAlmostEqual(seed_summary.loc[0, "heldout_mean_adapter_gain_valid"], 0.2)
        self.assertAlmostEqual(seed_summary.loc[1, "heldout_mean_adapter_gain_valid"], 0.4)
        self.assertEqual(len(multiseed), 1)
        self.assertAlmostEqual(multiseed.loc[0, "heldout_gain_mean"], 0.3)
        self.assertEqual(int(multiseed.loc[0, "positive_gain_seeds"]), 2)


if __name__ == "__main__":
    unittest.main()
