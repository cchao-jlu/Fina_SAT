import unittest

import pandas as pd
import torch
from omegaconf import OmegaConf

from generate_counterfactual_outcome_traces import (
    CounterfactualLabelSpec,
    _disable_adapter_gates,
    _preserve_model_selector_names,
    _label_rows,
    _multi_point_frame,
    _result_is_solved,
    intervention_conflict_points,
)
from train_counterfactual_risk_selector import normalise_size_column


class CounterfactualOutcomeTraceTest(unittest.TestCase):
    def test_intervention_conflict_points_support_lists_and_legacy_scalar(self):
        cfg = OmegaConf.create({"warmup_conflicts": 500, "intervention_conflicts": [1000, 500, 1000]})
        self.assertEqual(intervention_conflict_points(cfg), [500, 1000])

        legacy_cfg = OmegaConf.create({"warmup_conflicts": "500,1000", "intervention_conflicts": None})
        self.assertEqual(intervention_conflict_points(legacy_cfg), [500, 1000])

    def test_result_is_solved_treats_unknown_outputs_as_unsolved(self):
        self.assertTrue(_result_is_solved("SATISFIABLE"))
        self.assertTrue(_result_is_solved("UNSATISFIABLE"))
        self.assertFalse(_result_is_solved("INDETERMINATE"))
        self.assertFalse(_result_is_solved("TIMEOUT"))
        self.assertFalse(_result_is_solved("UNKNOWN"))
        self.assertFalse(_result_is_solved(None))

    def test_counterfactual_labels_use_shared_warmup_intervention(self):
        frame = pd.DataFrame(
            [
                {
                    "cnf_id": 0,
                    "warmup_result": "INDETERMINATE",
                    "base_result": "INDETERMINATE",
                    "adapter_result": "SATISFIABLE",
                    "warmup_time": 0.1,
                    "base_time": 60.0,
                    "adapter_time": 10.0,
                },
                {
                    "cnf_id": 1,
                    "warmup_result": "INDETERMINATE",
                    "base_result": "SATISFIABLE",
                    "adapter_result": "INDETERMINATE",
                    "warmup_time": 0.1,
                    "base_time": 5.0,
                    "adapter_time": 60.0,
                },
                {
                    "cnf_id": 2,
                    "warmup_result": "INDETERMINATE",
                    "base_result": "SATISFIABLE",
                    "adapter_result": "SATISFIABLE",
                    "warmup_time": 0.1,
                    "base_time": 10.0,
                    "adapter_time": 7.0,
                },
                {
                    "cnf_id": 3,
                    "warmup_result": "INDETERMINATE",
                    "base_result": "SATISFIABLE",
                    "adapter_result": "SATISFIABLE",
                    "warmup_time": 0.1,
                    "base_time": 10.0,
                    "adapter_time": 12.0,
                },
                {
                    "cnf_id": 4,
                    "warmup_result": "SATISFIABLE",
                    "base_result": "INDETERMINATE",
                    "adapter_result": "SATISFIABLE",
                    "warmup_time": 0.1,
                    "base_time": 60.0,
                    "adapter_time": 1.0,
                },
            ]
        )

        labelled = _label_rows(frame, CounterfactualLabelSpec())

        self.assertEqual(labelled.loc[0, "counterfactual_class"], "positive")
        self.assertEqual(labelled.loc[1, "counterfactual_class"], "negative")
        self.assertEqual(labelled.loc[2, "counterfactual_class"], "positive")
        self.assertEqual(labelled.loc[2, "counterfactual_reason"], "hard_speedup")
        self.assertEqual(labelled.loc[3, "counterfactual_class"], "negative")
        self.assertEqual(labelled.loc[3, "counterfactual_reason"], "slowdown")
        self.assertEqual(labelled.loc[4, "counterfactual_class"], "warmup_solved")
        self.assertEqual(labelled.loc[4, "counterfactual_class_code"], -2)

    def test_risk_focused_labels_filter_easy_speedups_and_weight_risks(self):
        frame = pd.DataFrame(
            [
                {
                    "cnf_id": 0,
                    "warmup_result": "INDETERMINATE",
                    "base_result": "SATISFIABLE",
                    "adapter_result": "SATISFIABLE",
                    "warmup_time": 0.1,
                    "base_time": 5.0,
                    "adapter_time": 3.0,
                },
                {
                    "cnf_id": 1,
                    "warmup_result": "INDETERMINATE",
                    "base_result": "SATISFIABLE",
                    "adapter_result": "SATISFIABLE",
                    "warmup_time": 0.1,
                    "base_time": 30.0,
                    "adapter_time": 20.0,
                },
                {
                    "cnf_id": 2,
                    "warmup_result": "INDETERMINATE",
                    "base_result": "SATISFIABLE",
                    "adapter_result": "SATISFIABLE",
                    "warmup_time": 0.1,
                    "base_time": 4.0,
                    "adapter_time": 4.4,
                },
                {
                    "cnf_id": 3,
                    "warmup_result": "INDETERMINATE",
                    "base_result": "SATISFIABLE",
                    "adapter_result": "INDETERMINATE",
                    "warmup_time": 0.1,
                    "base_time": 15.0,
                    "adapter_time": 60.0,
                },
            ]
        )

        labelled = _label_rows(
            frame,
            CounterfactualLabelSpec(
                positive_speedup_ratio=0.75,
                positive_min_base_time=10.0,
                positive_min_delta_time=1.0,
                negative_slowdown_ratio=1.05,
                negative_min_delta_time=0.5,
                easy_base_time_cutoff=10.0,
                easy_negative_delta_time=0.25,
                speedup_weight=4.0,
                easy_slowdown_weight=16.0,
                lost_weight=24.0,
            ),
        )

        self.assertEqual(labelled.loc[0, "counterfactual_class"], "neutral")
        self.assertEqual(labelled.loc[0, "counterfactual_reason"], "neutral")
        self.assertEqual(labelled.loc[1, "counterfactual_class"], "positive")
        self.assertEqual(labelled.loc[1, "counterfactual_reason"], "hard_speedup")
        self.assertEqual(labelled.loc[1, "counterfactual_weight"], 4.0)
        self.assertEqual(labelled.loc[2, "counterfactual_class"], "negative")
        self.assertEqual(labelled.loc[2, "counterfactual_reason"], "easy_slowdown")
        self.assertEqual(labelled.loc[2, "counterfactual_weight"], 16.0)
        self.assertEqual(labelled.loc[3, "counterfactual_class"], "negative")
        self.assertEqual(labelled.loc[3, "counterfactual_reason"], "lost_solution")
        self.assertEqual(labelled.loc[3, "counterfactual_weight"], 24.0)

    def test_selector_training_preserves_multi_size_trace_rows(self):
        frame = pd.DataFrame({"size": ["300", "350", 300, 350]})
        size = normalise_size_column(frame)
        self.assertEqual(size.tolist(), [300, 350, 300, 350])

    def test_multi_point_frame_adds_prefixed_features_and_drifts(self):
        class Store(dict):
            def __getattr__(self, name):
                return self[name]

        graph = Store(
            {
                "lit": Store({"num_nodes": 4}),
                "var": Store({"num_nodes": 2}),
            }
        )
        graph.cnf_id = torch.tensor([7])
        graph.gpu_time = 0.0
        stats_500 = pd.DataFrame(
            [
                {
                    "cnf_id": 7,
                    "sample_id": 0,
                    "file": "3sat/300/a.cnf",
                    "Result": "INDETERMINATE",
                    "CPU time": 0.1,
                    "propagations": 10,
                }
            ]
        )
        stats_1000 = pd.DataFrame(
            [
                {
                    "cnf_id": 7,
                    "sample_id": 0,
                    "file": "3sat/300/a.cnf",
                    "Result": "SATISFIABLE",
                    "CPU time": 0.2,
                    "propagations": 30,
                }
            ]
        )
        features_500 = pd.DataFrame([{"cnf_id": 7, "event_entropy_norm": 0.8}])
        features_1000 = pd.DataFrame([{"cnf_id": 7, "event_entropy_norm": 0.5}])

        frame = _multi_point_frame(
            points=[500, 1000],
            stats_by_point={500: stats_500, 1000: stats_1000},
            graphs_by_point={500: [graph], 1000: [graph]},
            feature_frames_by_point={500: features_500, 1000: features_1000},
            feature_names=["event_entropy_norm"],
        )

        self.assertIn("warmup_c500_event_entropy_norm", frame.columns)
        self.assertIn("warmup_c1000_minus_warmup_c500_event_entropy_norm", frame.columns)
        self.assertIn("warmup_c1000_minus_warmup_c500_propagations", frame.columns)
        self.assertAlmostEqual(float(frame.loc[0, "warmup_c1000_minus_warmup_c500_event_entropy_norm"]), -0.3)
        self.assertAlmostEqual(float(frame.loc[0, "warmup_c1000_minus_warmup_c500_propagations"]), 20.0)
        self.assertTrue(bool(frame.loc[0, "warmup_c1000_solved"]))
        self.assertFalse(bool(frame.loc[0, "solved_before_final_intervention"]))

    def test_disable_adapter_gates_can_preserve_selector_feature_names_for_trace_evidence(self):
        class Model:
            event_adapter_selector_feature_names = ["warmup_c500_decisions"]
            event_adapter_base_rho_gate_threshold = 0.5
            event_adapter_graph_gate_indices = [0]
            event_adapter_graph_gate_threshold = 0.5

        cfg = OmegaConf.create(
            {
                "counterfactual": {
                    "disable_adapter_selector": True,
                    "preserve_selector_feature_names": True,
                    "disable_adapter_base_rho_gate": True,
                    "disable_adapter_graph_gate": True,
                }
            }
        )
        model = Model()

        _disable_adapter_gates(model, cfg)

        self.assertEqual(model.event_adapter_selector_feature_names, ["warmup_c500_decisions"])
        self.assertIsNone(model.event_adapter_base_rho_gate_threshold)
        self.assertEqual(model.event_adapter_graph_gate_indices, [])
        self.assertIsNone(model.event_adapter_graph_gate_threshold)

    def test_preserve_model_selector_names_temporarily_clears_prefixed_names(self):
        class Model:
            event_adapter_selector_feature_names = ["warmup_c500_solved"]

        model = Model()
        with _preserve_model_selector_names(model):
            self.assertEqual(model.event_adapter_selector_feature_names, [])
        self.assertEqual(model.event_adapter_selector_feature_names, ["warmup_c500_solved"])


if __name__ == "__main__":
    unittest.main()
