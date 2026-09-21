import unittest

import pandas as pd

from build_new_closed_old_on_trace_subset import add_local_boundary_labels, select_new_closed_old_on


class NewClosedOldOnTraceSubsetTest(unittest.TestCase):
    def test_selects_only_new_closed_old_on_rows(self):
        frame = pd.DataFrame(
            [
                {"file_key": "a.cnf", "decision_change": "new_closed_old_on"},
                {"file_key": "b.cnf", "decision_change": "both_on"},
                {"file_key": "c.cnf", "decision_change": "new_closed_old_on"},
            ]
        )

        subset = select_new_closed_old_on(frame)

        self.assertEqual(subset["file_key"].tolist(), ["a.cnf", "c.cnf"])

    def test_local_labels_distinguish_reopen_and_keep_closed(self):
        frame = pd.DataFrame(
            [
                {
                    "file_key": "reopen.cnf",
                    "decision_change": "new_closed_old_on",
                    "base_solved": True,
                    "old_solved": True,
                    "new_solved": True,
                    "base_time": 30.0,
                    "old_time": 1.0,
                    "new_time": 29.0,
                    "delta_time_vs_old": 28.0,
                    "outcome_vs_old": "slower_both_solved",
                },
                {
                    "file_key": "closed.cnf",
                    "decision_change": "new_closed_old_on",
                    "base_solved": True,
                    "old_solved": True,
                    "new_solved": True,
                    "base_time": 21.0,
                    "old_time": 36.0,
                    "new_time": 22.0,
                    "delta_time_vs_old": -14.0,
                    "outcome_vs_old": "faster_both_solved",
                },
            ]
        )

        labelled = add_local_boundary_labels(frame).set_index("file_key")

        self.assertEqual(labelled.loc["reopen.cnf", "local_closed_old_label"], 1)
        self.assertEqual(labelled.loc["reopen.cnf", "local_closed_old_reason"], "reopen_old_adapter")
        self.assertEqual(labelled.loc["closed.cnf", "local_closed_old_label"], 0)
        self.assertEqual(labelled.loc["closed.cnf", "local_closed_old_reason"], "keep_closed")


if __name__ == "__main__":
    unittest.main()
