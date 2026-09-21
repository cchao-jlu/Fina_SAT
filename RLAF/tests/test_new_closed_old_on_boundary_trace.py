import unittest

import pandas as pd

from summarize_new_closed_old_on_boundary_trace import (
    FEATURE_COLUMNS,
    build_focus_frame,
    build_summary,
    local_reopen_labels,
    merge_manifest_and_trace,
)


class NewClosedOldOnBoundaryTraceTest(unittest.TestCase):
    def test_local_trace_labels_override_stale_manifest_label(self):
        manifest = pd.DataFrame(
            [
                {
                    "file_key": "3sat_188.cnf",
                    "local_closed_old_label": 0,
                    "local_closed_old_reason": "keep_closed",
                    "new_risk_prob": 0.4,
                    "new_recovery_prob": 0.3,
                    "new_slowdown_prob": 0.1,
                },
                {
                    "file_key": "3sat_82.cnf",
                    "local_closed_old_label": 0,
                    "local_closed_old_reason": "keep_closed",
                    "new_risk_prob": 0.2,
                    "new_recovery_prob": 0.2,
                    "new_slowdown_prob": 0.1,
                },
            ]
        )
        trace = pd.DataFrame(
            [
                {
                    "file": "/tmp/3sat_188.cnf",
                    "base_result": "INDETERMINATE",
                    "adapter_result": "SATISFIABLE",
                    "base_pipeline_time": 60.0,
                    "adapter_pipeline_time": 25.0,
                    "adapter_minus_base_time": -35.0,
                    "counterfactual_class": "positive",
                    "counterfactual_reason": "recovered_timeout",
                },
                {
                    "file": "/tmp/3sat_82.cnf",
                    "base_result": "SATISFIABLE",
                    "adapter_result": "SATISFIABLE",
                    "base_pipeline_time": 21.0,
                    "adapter_pipeline_time": 35.0,
                    "adapter_minus_base_time": 14.0,
                    "counterfactual_class": "negative",
                    "counterfactual_reason": "slowdown",
                },
            ]
        )

        merged = merge_manifest_and_trace(manifest, trace)
        labelled = local_reopen_labels(merged).set_index("file_key")

        self.assertEqual(labelled.loc["3sat_188.cnf", "trace_reopen_label"], 1)
        self.assertEqual(labelled.loc["3sat_188.cnf", "trace_reopen_reason"], "reopen_by_current_trace")
        self.assertEqual(labelled.loc["3sat_82.cnf", "trace_reopen_label"], 0)
        self.assertEqual(labelled.loc["3sat_82.cnf", "trace_reopen_reason"], "keep_closed_by_current_trace")

    def test_summary_and_focus_frame_report_positive_negative_boundary(self):
        frame = pd.DataFrame(
            [
                {
                    "file_key": "3sat_46.cnf",
                    "counterfactual_class": "positive",
                    "counterfactual_reason": "hard_speedup",
                    "base_pipeline_time": 31.0,
                    "adapter_pipeline_time": 0.5,
                    "adapter_minus_base_time": -30.5,
                    "trace_reopen_label": 1,
                    "trace_reopen_reason": "reopen_by_current_trace",
                    **{name: 0.0 for name in FEATURE_COLUMNS},
                },
                {
                    "file_key": "3sat_82.cnf",
                    "counterfactual_class": "negative",
                    "counterfactual_reason": "slowdown",
                    "base_pipeline_time": 21.0,
                    "adapter_pipeline_time": 35.0,
                    "adapter_minus_base_time": 14.0,
                    "trace_reopen_label": 0,
                    "trace_reopen_reason": "keep_closed_by_current_trace",
                    **{name: 1.0 for name in FEATURE_COLUMNS},
                },
                {
                    "file_key": "3sat_106.cnf",
                    "counterfactual_class": "neutral",
                    "counterfactual_reason": "neutral",
                    "base_pipeline_time": 60.0,
                    "adapter_pipeline_time": 60.0,
                    "adapter_minus_base_time": 0.0,
                    "trace_reopen_label": pd.NA,
                    "trace_reopen_reason": "neutral",
                    **{name: 2.0 for name in FEATURE_COLUMNS},
                },
            ]
        )

        summary = build_summary(frame)
        focus = build_focus_frame(frame, focus_keys=["3sat_46.cnf", "3sat_82.cnf"])

        self.assertEqual(summary.loc[0, "positive"], 1)
        self.assertEqual(summary.loc[0, "negative"], 1)
        self.assertEqual(summary.loc[0, "neutral"], 1)
        self.assertEqual(focus["file_key"].tolist(), ["3sat_46.cnf", "3sat_82.cnf"])
        self.assertIn("feature_profile", focus.columns)


if __name__ == "__main__":
    unittest.main()
