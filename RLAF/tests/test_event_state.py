import math
import unittest

import torch
from torch_geometric.data import HeteroData

from src.solving import state


class EventStateTest(unittest.TestCase):
    def test_legacy_event_state_keeps_five_log_features(self):
        stats = {
            "event_var_decisions": [0, 3],
            "event_var_propagations": [1, 0],
            "event_var_conflict_lits": [2, 0],
            "event_var_learnt_lits": [0, 4],
            "event_var_activity": [9, 0],
        }

        encoded = state.solver_stats_to_var_event_state(stats, num_vars=2)

        self.assertEqual(encoded.shape, (2, state.EVENT_VAR_STATE_DIM))
        self.assertEqual(encoded[0, 0].item(), 0.0)
        self.assertTrue(math.isclose(encoded[1, 0].item(), math.log1p(3), rel_tol=1e-6))
        self.assertTrue(math.isclose(encoded[0, 4].item(), math.log1p(9), rel_tol=1e-6))

    def test_enhanced_event_state_adds_delta_rate_and_rank_features(self):
        stats = {
            "event_var_decisions": [0, 3],
            "event_var_propagations": [1, 0],
            "event_var_conflict_lits": [2, 0],
            "event_var_learnt_lits": [0, 4],
            "event_var_activity": [9, 0],
        }

        encoded = state.solver_stats_to_var_event_state(
            stats,
            num_vars=2,
            feature_mode="enhanced",
        )

        self.assertEqual(encoded.shape, (2, state.EVENT_VAR_STATE_DIM_ENHANCED))
        self.assertTrue(math.isclose(encoded[1, 0].item(), math.log1p(3), rel_tol=1e-6))
        self.assertTrue(math.isclose(encoded[1, 5].item(), math.log1p(3), rel_tol=1e-6))
        self.assertEqual(encoded[0, 10].item(), 0.0)
        self.assertEqual(encoded[1, 10].item(), 1.0)
        self.assertEqual(encoded[0, 15].item(), 0.0)
        self.assertEqual(encoded[1, 15].item(), 1.0)

    def test_polarity_event_state_adds_literal_bias_features(self):
        stats = {
            "event_var_decisions": [0, 3],
            "event_var_propagations": [1, 0],
            "event_var_conflict_lits": [2, 0],
            "event_var_learnt_lits": [0, 4],
            "event_var_activity": [9, 0],
            "event_var_pos_conflict_lits": [3, 1],
            "event_var_neg_conflict_lits": [1, 1],
            "event_var_pos_propagations": [0, 4],
            "event_var_neg_propagations": [2, 0],
            "event_var_pos_assignments": [3, 0],
            "event_var_neg_assignments": [1, 2],
        }

        encoded = state.solver_stats_to_var_event_state(
            stats,
            num_vars=2,
            feature_mode="polarity",
        )

        self.assertEqual(encoded.shape, (2, state.EVENT_VAR_STATE_DIM_POLARITY))
        self.assertTrue(math.isclose(encoded[0, 20].item(), 0.75, rel_tol=1e-6))
        self.assertTrue(math.isclose(encoded[0, 21].item(), 0.5, rel_tol=1e-6))
        self.assertTrue(math.isclose(encoded[0, 22].item(), 0.5, rel_tol=1e-6))
        self.assertTrue(math.isclose(encoded[1, 25].item(), 1.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(encoded[1, 28].item(), -1.0, rel_tol=1e-6))

    def test_attach_var_event_state_applies_momentum_and_exposes_event_memory(self):
        data = HeteroData()
        data["lit"].num_nodes = 4
        data["var"].num_nodes = 2
        data["var"].event_state = torch.full((2, state.EVENT_VAR_STATE_DIM), 10.0)
        stats = {
            "event_var_decisions": [0, 0],
            "event_var_propagations": [0, 0],
            "event_var_conflict_lits": [0, 0],
            "event_var_learnt_lits": [0, 0],
            "event_var_activity": [0, 0],
        }

        updated = state.attach_var_event_state(
            data,
            stats,
            var_state_dim=state.EVENT_VAR_STATE_DIM,
            momentum=0.5,
        )

        self.assertTrue(torch.allclose(updated["var"].event_state, torch.full((2, 5), 5.0)))
        self.assertTrue(torch.allclose(updated["var"].event_memory, updated["var"].event_state))


if __name__ == "__main__":
    unittest.main()
