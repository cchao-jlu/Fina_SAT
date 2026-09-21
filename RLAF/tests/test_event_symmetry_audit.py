import unittest

import pandas as pd
import torch

from audit_event_symmetry import (
    add_identity_gain_columns,
    annotate_event_row_validity,
    event_state_orbit_rows,
    solver_stats_has_events,
    normalized_orbit_entropy,
    orbit_entropy,
    tensor_orbit_rows,
)


class EventSymmetryAuditTest(unittest.TestCase):
    def test_orbit_entropy_is_normalized_by_variable_count(self):
        orbits = {1: "a", 2: "a", 3: "b", 4: "b"}

        self.assertAlmostEqual(orbit_entropy(orbits), 0.6931471805599453)
        self.assertAlmostEqual(normalized_orbit_entropy(orbits), 0.5)

    def test_tensor_orbit_rows_reports_static_guidance_ranges(self):
        values = torch.tensor(
            [
                [0.0, 1.0],
                [0.0, 1.0],
                [2.0, 3.0],
                [4.0, 7.0],
            ],
            dtype=torch.float32,
        )
        orbits = {1: "same", 2: "same", 3: "split", 4: "split"}

        rows = {row["orbit"]: row for row in tensor_orbit_rows(values, orbits, prefix="static")}

        self.assertEqual(rows["same"]["orbit_size"], 2)
        self.assertAlmostEqual(rows["same"]["static_rho_range"], 0.0)
        self.assertAlmostEqual(rows["same"]["static_mu_range"], 0.0)
        self.assertAlmostEqual(rows["split"]["static_rho_range"], 2.0)
        self.assertAlmostEqual(rows["split"]["static_mu_range"], 4.0)

    def test_event_state_orbit_rows_reports_event_identity(self):
        event_state = torch.tensor(
            [
                [0.0, 0.0, 0.0],
                [0.0, 3.0, 4.0],
                [1.0, 1.0, 1.0],
            ],
            dtype=torch.float32,
        )
        orbits = {1: "a", 2: "a", 3: "b"}

        rows = {row["orbit"]: row for row in event_state_orbit_rows(event_state, orbits)}

        self.assertEqual(rows["a"]["event_nonzero_variables"], 1)
        self.assertAlmostEqual(rows["a"]["event_feature_l2_range"], 5.0)
        self.assertAlmostEqual(rows["b"]["event_feature_l2_range"], 0.0)

    def test_solver_stats_has_events_requires_event_var_columns(self):
        self.assertFalse(solver_stats_has_events(pd.DataFrame({"Result": ["INDETERMINATE"]})))
        self.assertTrue(solver_stats_has_events(pd.DataFrame({"event_var_decisions": [[0, 1]]})))

    def test_identity_gain_columns_compare_adapted_and_static_ranges(self):
        frame = pd.DataFrame(
            {
                "orbit": ["a"],
                "orbit_size": [2],
                "static_mu_range": [0.1],
                "adapted_mu_range": [0.6],
                "static_rho_range": [0.2],
                "adapted_rho_range": [0.5],
                "event_feature_l2_range": [2.0],
            }
        )

        updated = add_identity_gain_columns(frame)

        self.assertAlmostEqual(float(updated.loc[0, "adapter_mu_identity_gain"]), 0.5)
        self.assertAlmostEqual(float(updated.loc[0, "adapter_rho_identity_gain"]), 0.3)
        self.assertAlmostEqual(float(updated.loc[0, "adapter_identity_gain"]), 0.5)
        self.assertAlmostEqual(float(updated.loc[0, "event_identity_gain"]), 2.0)

    def test_event_row_validity_splits_positive_and_zero_identity(self):
        frame = pd.DataFrame(
            {
                "orbit": ["positive", "zero"],
                "orbit_size": [2, 2],
                "orbit_valid": [True, True],
                "orbit_valid_reason": ["valid", "valid"],
                "audit_status": ["ok", "ok"],
                "static_mu_range": [1.0e-8, 1.0e-8],
                "event_feature_l2_range": [0.25, 0.0],
            }
        )
        stats = pd.DataFrame({"decisions": [1], "conflicts": [0]})

        updated = annotate_event_row_validity(
            frame,
            solver_stats=stats,
            static_collapse_threshold=1.0e-4,
            event_identity_eps=1.0e-6,
        )

        self.assertTrue(bool(updated.loc[0, "event_row_valid"]))
        self.assertTrue(bool(updated.loc[0, "event_identity_positive"]))
        self.assertFalse(bool(updated.loc[0, "event_identity_zero"]))
        self.assertTrue(bool(updated.loc[1, "event_row_valid"]))
        self.assertFalse(bool(updated.loc[1, "event_identity_positive"]))
        self.assertTrue(bool(updated.loc[1, "event_identity_zero"]))


if __name__ == "__main__":
    unittest.main()
