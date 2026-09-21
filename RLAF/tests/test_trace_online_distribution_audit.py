import unittest

import pandas as pd

from audit_trace_online_distribution import (
    feature_distribution_summary,
    instance_feature_audit,
    policy_outcome_label,
)


class TraceOnlineDistributionAuditTest(unittest.TestCase):
    def test_feature_distribution_summary_marks_online_tail_mass(self):
        train = pd.DataFrame({"f1": [0.0, 1.0, 2.0, 3.0], "f2": [10.0, 10.0, 10.0, 10.0]})
        online = pd.DataFrame({"f1": [2.0, 5.0], "f2": [10.0, 12.0]})

        summary = feature_distribution_summary(train, online, ["f1", "f2"]).set_index("feature")

        self.assertAlmostEqual(summary.loc["f1", "train_mean"], 1.5)
        self.assertEqual(summary.loc["f1", "online_outside_p05_p95"], 1)
        self.assertEqual(summary.loc["f2", "online_outside_p05_p95"], 1)
        self.assertEqual(summary.loc["f2", "mean_shift_z"], 0.0)

    def test_policy_outcome_label_prioritises_lost_and_recovered(self):
        self.assertEqual(policy_outcome_label(True, False), "lost_solution")
        self.assertEqual(policy_outcome_label(False, True), "recovered_timeout")
        self.assertEqual(policy_outcome_label(True, True), "kept_solved")
        self.assertEqual(policy_outcome_label(False, False), "kept_timeout")

    def test_instance_feature_audit_reports_largest_abs_z(self):
        train = pd.DataFrame({"f1": [0.0, 1.0, 2.0, 3.0], "f2": [10.0, 10.0, 10.0, 10.0]})
        online = pd.DataFrame(
            {
                "file_key": ["a.cnf", "b.cnf"],
                "f1": [1.5, 5.0],
                "f2": [10.0, 12.0],
                "base_solved": [1, 0],
                "selected_solved": [1, 1],
            }
        )

        audit = instance_feature_audit(train, online, ["f1", "f2"]).set_index("file_key")

        self.assertEqual(audit.loc["a.cnf", "outcome_group"], "kept_solved")
        self.assertEqual(audit.loc["b.cnf", "outcome_group"], "recovered_timeout")
        self.assertGreater(audit.loc["b.cnf", "max_abs_train_z"], audit.loc["a.cnf", "max_abs_train_z"])
        self.assertEqual(audit.loc["b.cnf", "max_abs_feature"], "f1")


if __name__ == "__main__":
    unittest.main()
