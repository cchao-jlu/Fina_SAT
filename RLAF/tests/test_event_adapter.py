import unittest

import pandas as pd
import torch
from omegaconf import OmegaConf
from torch_geometric.data import HeteroData
from torch_geometric.loader import DataLoader

from src.model.model import GNN, init_model
from src.policy.evaluate import sample_var_params
from src.solving.state import EVENT_VAR_STATE_DIM, EVENT_VAR_STATE_DIM_ENHANCED, EVENT_VAR_STATE_DIM_POLARITY
from src.training.trace_distill import freeze_non_adapter_parameters
from evaluate_guided_solver import _attach_selector_feature_overrides


def make_graph() -> HeteroData:
    data = HeteroData()
    data["lit"].x = torch.ones((4, 1), dtype=torch.float32)
    data["lit"].num_nodes = 4
    data["cls"].x = torch.ones((2, 1), dtype=torch.float32)
    data["cls"].num_nodes = 2
    data["cls", "lit"].edge_index = torch.tensor(
        [[0, 0, 1, 1], [0, 2, 1, 3]],
        dtype=torch.long,
    )
    data.cnf_id = torch.tensor([0])
    return data


def make_model() -> GNN:
    return GNN(
        channels=4,
        lit_feat_dim=1,
        cls_feat_dim=1,
        num_layers=1,
        out_dim=2,
        var_state_dim=EVENT_VAR_STATE_DIM,
        event_adapter_enabled=True,
        event_adapter_hidden_dim=8,
    )


def make_cached_adapter_graph(
    base_y: torch.Tensor,
    *,
    var_state_dim: int = EVENT_VAR_STATE_DIM,
) -> HeteroData:
    data = HeteroData()
    num_vars = base_y.shape[0]
    data["var"].num_nodes = num_vars
    data["var"].base_embedding = torch.zeros((num_vars, 8), dtype=torch.float32)
    data["var"].base_y = base_y.clone()
    data["var"].event_state = torch.ones((num_vars, var_state_dim), dtype=torch.float32)
    return data


class DummyTransform:
    def lit_dim(self) -> int:
        return 1

    def cls_dim(self) -> int:
        return 1


class EventAdapterTest(unittest.TestCase):
    def test_gnn_returns_cache_for_slow_fast_adapter(self):
        model = make_model()
        batch = next(iter(DataLoader([make_graph()], batch_size=1)))

        y_var, cache = model(batch, return_cache=True)

        self.assertEqual(y_var.shape, (2, 2))
        self.assertEqual(cache["base_embedding"].shape, (2, 8))
        self.assertEqual(cache["base_y"].shape, (2, 2))

    def test_event_adapter_fast_path_uses_cached_base_logits_with_zero_residual(self):
        model = make_model()
        batch = next(iter(DataLoader([make_graph()], batch_size=1)))
        base_y, cache = model(batch, return_cache=True)

        batch["var"].num_nodes = 2
        batch["var"].base_embedding = cache["base_embedding"]
        batch["var"].base_y = cache["base_y"]
        batch["var"].event_state = torch.ones((2, EVENT_VAR_STATE_DIM), dtype=torch.float32)

        adapted_y = model(batch)

        self.assertTrue(torch.allclose(adapted_y, base_y))

    def test_event_adapter_can_clip_and_scale_residual_delta(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_delta_scale=0.5,
            event_adapter_delta_clip=1.0,
        )
        batch = next(iter(DataLoader([make_graph()], batch_size=1)))
        base_y, cache = model(batch, return_cache=True)

        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([4.0, -4.0]))

        batch["var"].num_nodes = 2
        batch["var"].base_embedding = cache["base_embedding"]
        batch["var"].base_y = cache["base_y"]
        batch["var"].event_state = torch.ones((2, EVENT_VAR_STATE_DIM), dtype=torch.float32)

        adapted_y = model(batch)

        expected_delta = torch.tensor([[0.5, -0.5], [0.5, -0.5]], dtype=torch.float32)
        self.assertTrue(torch.allclose(adapted_y, base_y + expected_delta))

    def test_event_adapter_can_gate_residual_by_event_evidence(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_gate_indices=[2],
        )
        batch = next(iter(DataLoader([make_graph()], batch_size=1)))
        base_y, cache = model(batch, return_cache=True)

        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([1.0, -1.0]))

        event_state = torch.zeros((2, EVENT_VAR_STATE_DIM), dtype=torch.float32)
        event_state[1, 2] = 0.5
        batch["var"].num_nodes = 2
        batch["var"].base_embedding = cache["base_embedding"]
        batch["var"].base_y = cache["base_y"]
        batch["var"].event_state = event_state

        adapted_y = model(batch)

        expected_delta = torch.tensor([[0.0, 0.0], [0.5, -0.5]], dtype=torch.float32)
        self.assertTrue(torch.allclose(adapted_y, base_y + expected_delta))

    def test_event_adapter_can_disable_residual_for_low_evidence_graphs(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_graph_gate_indices=[2],
            event_adapter_graph_gate_threshold=0.1,
        )
        batch = next(iter(DataLoader([make_graph(), make_graph()], batch_size=2)))
        base_y, cache = model(batch, return_cache=True)

        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([1.0, -1.0]))

        event_state = torch.zeros((4, EVENT_VAR_STATE_DIM), dtype=torch.float32)
        event_state[2:, 2] = 0.5
        batch["var"].num_nodes = 4
        batch["var"].base_embedding = cache["base_embedding"]
        batch["var"].base_y = cache["base_y"]
        batch["var"].event_state = event_state

        adapted_y = model(batch)

        expected_delta = torch.tensor(
            [[0.0, 0.0], [0.0, 0.0], [1.0, -1.0], [1.0, -1.0]],
            dtype=torch.float32,
        )
        self.assertTrue(torch.allclose(adapted_y, base_y + expected_delta))

    def test_event_adapter_can_disable_residual_for_low_base_rho_graphs(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_base_rho_gate_threshold=0.0,
        )
        batch = next(iter(DataLoader([make_graph(), make_graph()], batch_size=2)))
        _, cache = model(batch, return_cache=True)

        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([1.0, -1.0]))

        base_y = torch.tensor(
            [[-0.5, 0.0], [-0.5, 0.0], [0.5, 0.0], [0.5, 0.0]],
            dtype=torch.float32,
        )
        batch["var"].num_nodes = 4
        batch["var"].base_embedding = cache["base_embedding"]
        batch["var"].base_y = base_y
        batch["var"].event_state = torch.ones((4, EVENT_VAR_STATE_DIM), dtype=torch.float32)

        adapted_y = model(batch)

        expected_delta = torch.tensor(
            [[0.0, 0.0], [0.0, 0.0], [1.0, -1.0], [1.0, -1.0]],
            dtype=torch.float32,
        )
        self.assertTrue(torch.allclose(adapted_y, base_y + expected_delta))

    def test_event_adapter_can_use_linear_graph_selector(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_selector_feature_names=["base_rho_mean"],
            event_adapter_selector_weights=[10.0],
            event_adapter_selector_bias=0.0,
            event_adapter_selector_threshold=0.5,
        )
        batch = next(iter(DataLoader([make_graph(), make_graph()], batch_size=2)))
        _, cache = model(batch, return_cache=True)

        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([1.0, -1.0]))

        base_y = torch.tensor(
            [[-0.5, 0.0], [-0.5, 0.0], [0.5, 0.0], [0.5, 0.0]],
            dtype=torch.float32,
        )
        batch["var"].num_nodes = 4
        batch["var"].base_embedding = cache["base_embedding"]
        batch["var"].base_y = base_y
        batch["var"].event_state = torch.ones((4, EVENT_VAR_STATE_DIM), dtype=torch.float32)

        adapted_y = model(batch)

        expected_delta = torch.tensor(
            [[0.0, 0.0], [0.0, 0.0], [1.0, -1.0], [1.0, -1.0]],
            dtype=torch.float32,
        )
        self.assertTrue(torch.allclose(adapted_y, base_y + expected_delta))

    def test_event_adapter_selector_can_use_graph_size_feature(self):
        model = make_model()
        base_y = torch.zeros((4, 2), dtype=torch.float32)
        var_state = torch.ones((4, EVENT_VAR_STATE_DIM), dtype=torch.float32)
        delta = torch.zeros((4, 2), dtype=torch.float32)
        var_batch = torch.tensor([0, 0, 1, 1], dtype=torch.long)

        value = model._event_adapter_selector_feature(
            "num_vars_log",
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=2,
        )

        expected = torch.log1p(torch.tensor([2.0, 2.0], dtype=torch.float32))
        self.assertTrue(torch.allclose(value, expected))

    def test_event_adapter_selector_can_use_micro_event_features(self):
        model = make_model()
        base_y = torch.tensor(
            [[2.0, 0.0], [1.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
            dtype=torch.float32,
        )
        var_state = torch.zeros((4, EVENT_VAR_STATE_DIM_ENHANCED), dtype=torch.float32)
        var_state[0, 12] = 0.6
        var_state[0, 13] = 0.2
        var_state[1, 12] = 0.2
        delta = torch.zeros((4, 2), dtype=torch.float32)
        var_batch = torch.tensor([0, 0, 1, 1], dtype=torch.long)

        entropy = model._event_adapter_selector_feature(
            "event_entropy_norm",
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=2,
        )
        top10 = model._event_adapter_selector_feature(
            "event_top10_mass",
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=2,
        )
        corr = model._event_adapter_selector_feature(
            "rho_event_corr",
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=2,
        )
        overlap = model._event_adapter_selector_feature(
            "rho_event_top10_overlap",
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=2,
        )

        expected_entropy = -(
            torch.tensor(0.8) * torch.log(torch.tensor(0.8))
            + torch.tensor(0.2) * torch.log(torch.tensor(0.2))
        ) / torch.log(torch.tensor(2.0))
        self.assertTrue(torch.allclose(entropy, torch.tensor([expected_entropy, 1.0])))
        self.assertTrue(torch.allclose(top10, torch.tensor([0.8, 0.0])))
        self.assertTrue(torch.allclose(corr, torch.tensor([1.0, 0.0])))
        self.assertTrue(torch.allclose(overlap, torch.tensor([1.0, 0.0])))

    def test_event_adapter_selector_can_use_tail_risk_features(self):
        model = make_model()
        base_y = torch.tensor(
            [[1.0, -0.5], [3.0, 2.0], [2.0, 0.0], [6.0, -4.0]],
            dtype=torch.float32,
        )
        var_state = torch.zeros((4, EVENT_VAR_STATE_DIM_ENHANCED), dtype=torch.float32)
        var_state[0, 2] = 0.7
        var_state[1, 3] = 0.4
        var_state[2, 2] = 0.1
        var_state[3, 3] = 0.9
        delta = torch.tensor(
            [[0.2, -0.1], [0.6, 0.3], [-0.4, 0.2], [1.0, -0.5]],
            dtype=torch.float32,
        )
        var_batch = torch.tensor([0, 0, 1, 1], dtype=torch.long)

        rho_range = model._event_adapter_selector_feature(
            "base_rho_range",
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=2,
        )
        delta_max = model._event_adapter_selector_feature(
            "delta_abs_max",
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=2,
        )
        event_log_max = model._event_adapter_selector_feature(
            "event_conf_learnt_log_max",
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=2,
        )

        self.assertTrue(torch.allclose(rho_range, torch.tensor([2.0, 4.0])))
        self.assertTrue(torch.allclose(delta_max, torch.tensor([0.45, 0.75])))
        self.assertTrue(torch.allclose(event_log_max, torch.tensor([0.7, 0.9])))

    def test_event_adapter_can_use_two_stage_mlp_selector(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_selector_mode="two_stage_mlp",
            event_adapter_selector_feature_names=["base_rho_mean"],
            event_adapter_risk_selector_feature_names=["base_rho_mean"],
            event_adapter_risk_selector_threshold=0.5,
            event_adapter_risk_selector_feature_mean=[0.0],
            event_adapter_risk_selector_feature_std=[1.0],
            event_adapter_risk_selector_mlp_weights=[[[-10.0]]],
            event_adapter_risk_selector_mlp_biases=[[0.0]],
            event_adapter_recovery_selector_feature_names=["base_rho_mean"],
            event_adapter_recovery_selector_threshold=0.5,
            event_adapter_recovery_selector_feature_mean=[0.0],
            event_adapter_recovery_selector_feature_std=[1.0],
            event_adapter_recovery_selector_mlp_weights=[[[10.0]]],
            event_adapter_recovery_selector_mlp_biases=[[0.0]],
        )

        gate = model._event_adapter_selector_gate(
            base_y=torch.zeros((4, 2), dtype=torch.float32),
            var_state=torch.ones((4, EVENT_VAR_STATE_DIM), dtype=torch.float32),
            delta=torch.zeros((4, 2), dtype=torch.float32),
            var_batch=torch.tensor([0, 0, 1, 1], dtype=torch.long),
            num_graphs=2,
            feature_override=torch.tensor([[1.0], [-1.0]], dtype=torch.float32),
        )

        self.assertTrue(torch.allclose(gate, torch.tensor([1.0, 0.0])))

    def test_event_adapter_two_stage_selector_can_use_slowdown_veto(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_selector_mode="two_stage",
            event_adapter_selector_feature_names=["risk_score", "recovery_score", "slowdown_score"],
            event_adapter_risk_selector_feature_names=["risk_score"],
            event_adapter_risk_selector_weights=[1.0],
            event_adapter_risk_selector_threshold=0.5,
            event_adapter_recovery_selector_feature_names=["recovery_score"],
            event_adapter_recovery_selector_weights=[1.0],
            event_adapter_recovery_selector_threshold=0.5,
            event_adapter_slowdown_selector_feature_names=["slowdown_score"],
            event_adapter_slowdown_selector_weights=[1.0],
            event_adapter_slowdown_selector_threshold=0.5,
        )

        gate = model._event_adapter_selector_gate(
            base_y=torch.zeros((4, 2), dtype=torch.float32),
            var_state=torch.ones((4, EVENT_VAR_STATE_DIM), dtype=torch.float32),
            delta=torch.zeros((4, 2), dtype=torch.float32),
            var_batch=torch.tensor([0, 0, 1, 1], dtype=torch.long),
            num_graphs=2,
            feature_override=torch.tensor(
                [
                    [-10.0, 10.0, -10.0],
                    [-10.0, 10.0, 10.0],
                ],
                dtype=torch.float32,
            ),
        )

        self.assertTrue(torch.allclose(gate, torch.tensor([1.0, 0.0])))

    def test_event_adapter_two_stage_selector_can_locally_reopen_closed_boundary_cases(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_selector_mode="two_stage",
            event_adapter_selector_feature_names=[
                "risk_score",
                "recovery_score",
                "warmup_c1000_minus_warmup_c750_decisions",
                "warmup_c2000_rho_event_corr",
            ],
            event_adapter_risk_selector_feature_names=["risk_score"],
            event_adapter_risk_selector_weights=[1.0],
            event_adapter_risk_selector_threshold=0.5,
            event_adapter_recovery_selector_feature_names=["recovery_score"],
            event_adapter_recovery_selector_weights=[1.0],
            event_adapter_recovery_selector_threshold=0.5,
            event_adapter_local_reopen_enabled=True,
            event_adapter_local_reopen_feature_names=[
                "warmup_c1000_minus_warmup_c750_decisions",
                "warmup_c2000_rho_event_corr",
            ],
            event_adapter_local_reopen_ops=[">=", ">="],
            event_adapter_local_reopen_values=[294.0, 0.036501],
        )

        gate = model._event_adapter_selector_gate(
            base_y=torch.zeros((6, 2), dtype=torch.float32),
            var_state=torch.ones((6, EVENT_VAR_STATE_DIM), dtype=torch.float32),
            delta=torch.zeros((6, 2), dtype=torch.float32),
            var_batch=torch.tensor([0, 0, 1, 1, 2, 2], dtype=torch.long),
            num_graphs=3,
            feature_override=torch.tensor(
                [
                    [10.0, 10.0, 294.0, 0.036501],
                    [10.0, 10.0, 293.0, 0.036501],
                    [-10.0, 10.0, 100.0, -1.0],
                ],
                dtype=torch.float32,
            ),
        )

        self.assertTrue(torch.allclose(gate, torch.tensor([1.0, 0.0, 1.0])))

    def test_local_reopen_mask_requires_candidate_guard_when_present(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_selector_weights=[0.0, 0.0],
            event_adapter_selector_bias=0.0,
            event_adapter_selector_threshold=0.5,
            event_adapter_selector_feature_names=[
                "local_reopen_candidate",
                "warmup_c1000_minus_warmup_c750_decisions",
            ],
            event_adapter_local_reopen_enabled=True,
            event_adapter_local_reopen_feature_names=[
                "warmup_c1000_minus_warmup_c750_decisions",
            ],
            event_adapter_local_reopen_ops=[">="],
            event_adapter_local_reopen_values=[294.0],
        )
        features = torch.tensor(
            [
                [1.0, 300.0],
                [0.0, 300.0],
            ],
            dtype=torch.float32,
        )

        mask = model._event_adapter_local_reopen_mask(features)

        self.assertTrue(torch.equal(mask, torch.tensor([True, False])))

    def test_local_reopen_candidate_feature_defaults_to_closed(self):
        model = make_model()
        value = model._event_adapter_selector_feature(
            "local_reopen_candidate",
            base_y=torch.zeros((4, 2), dtype=torch.float32),
            var_state=torch.ones((4, EVENT_VAR_STATE_DIM), dtype=torch.float32),
            delta=torch.zeros((4, 2), dtype=torch.float32),
            var_batch=torch.tensor([0, 0, 1, 1], dtype=torch.long),
            num_graphs=2,
        )

        self.assertTrue(torch.allclose(value, torch.zeros(2, dtype=torch.float32)))

    def test_selector_feature_override_can_inject_local_reopen_candidate(self):
        graph_a = make_graph()
        graph_b = make_graph()
        graph_a.cnf_id = torch.tensor(0, dtype=torch.long)
        graph_b.cnf_id = torch.tensor(1, dtype=torch.long)
        feature_by_point = {
            2000: pd.DataFrame(
                [
                    {"cnf_id": 0, "rho_event_corr": 0.1},
                    {"cnf_id": 1, "rho_event_corr": 0.2},
                ]
            ).set_index("cnf_id"),
        }

        updated = _attach_selector_feature_overrides(
            [graph_a, graph_b],
            selector_feature_names=["local_reopen_candidate", "warmup_c2000_rho_event_corr"],
            final_point=2000,
            feature_by_point=feature_by_point,
            local_reopen_candidate_ids={1},
        )

        self.assertTrue(
            torch.allclose(
                updated[0].event_adapter_selector_features,
                torch.tensor([[0.0, 0.1]], dtype=torch.float32),
            )
        )
        self.assertTrue(
            torch.allclose(
                updated[1].event_adapter_selector_features,
                torch.tensor([[1.0, 0.2]], dtype=torch.float32),
            )
        )

    def test_event_adapter_sbe_fusion_uses_cached_base_logits_with_zero_residual(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="sbe",
        )
        batch = next(iter(DataLoader([make_graph()], batch_size=1)))
        base_y, cache = model(batch, return_cache=True)

        batch["var"].num_nodes = 2
        batch["var"].base_embedding = cache["base_embedding"]
        batch["var"].base_y = cache["base_y"]
        batch["var"].event_state = torch.ones((2, EVENT_VAR_STATE_DIM), dtype=torch.float32)

        adapted_y = model(batch)

        self.assertTrue(torch.allclose(adapted_y, base_y))

    def test_polarity_gated_residual_only_updates_weight_logit(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=3,
            var_state_dim=EVENT_VAR_STATE_DIM_POLARITY,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="polarity_gated_residual",
            event_adapter_residual_state_dim=20,
            event_adapter_polarity_gate_indices=list(range(20, 29)),
            event_adapter_polarity_gate_min=0.5,
        )
        batch = next(iter(DataLoader([make_graph()], batch_size=1)))
        base_y, cache = model(batch, return_cache=True)

        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([1.0, -1.0, 2.0]))

        batch["var"].num_nodes = 2
        batch["var"].base_embedding = cache["base_embedding"]
        batch["var"].base_y = cache["base_y"]
        batch["var"].event_state = torch.ones((2, EVENT_VAR_STATE_DIM_POLARITY), dtype=torch.float32)

        adapted_y = model(batch)

        expected_delta = torch.tensor([[0.0, -0.75, 0.0], [0.0, -0.75, 0.0]], dtype=torch.float32)
        self.assertTrue(torch.allclose(adapted_y, base_y + expected_delta))

    def test_weight_only_residual_changes_only_weight_logit_after_mask_and_clip(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=3,
            var_state_dim=EVENT_VAR_STATE_DIM,
            orbit_feature_dim=2,
            orbit_event_state_dim=5,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
            event_adapter_delta_clip=0.25,
            event_adapter_require_valid_orbit=True,
            event_adapter_min_orbit_event_variance=0.5,
        )
        base_y = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        data = make_cached_adapter_graph(base_y)
        data["var"].orbit_features = torch.ones((2, 2), dtype=torch.float32)
        data["var"].orbit_event_state = torch.ones((2, 5), dtype=torch.float32)
        data["var"].valid_orbit_mask = torch.tensor([True, True])
        data["var"].orbit_event_variance = torch.tensor([[0.5], [0.75]])
        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([4.0, -4.0, 3.0]))

        adapted_y = model(data)

        self.assertTrue(torch.equal(adapted_y[:, 0], base_y[:, 0]))
        self.assertTrue(torch.equal(adapted_y[:, 2], base_y[:, 2]))
        self.assertTrue(torch.allclose(adapted_y[:, 1], base_y[:, 1] - 0.25))

    def test_weight_only_residual_applies_valid_and_variance_hard_masks(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            orbit_feature_dim=1,
            orbit_event_state_dim=5,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
            event_adapter_require_valid_orbit=True,
            event_adapter_min_orbit_event_variance=0.5,
        )
        base_y = torch.zeros((4, 2), dtype=torch.float32)
        data = make_cached_adapter_graph(base_y)
        data["var"].orbit_features = torch.ones((4, 1), dtype=torch.float32)
        data["var"].orbit_event_state = torch.ones((4, 5), dtype=torch.float32)
        data["var"].valid_orbit_mask = torch.tensor([True, False, True, False])
        data["var"].orbit_event_variance = torch.tensor([[0.5], [1.0], [0.499], [0.75]])
        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([2.0, 1.0]))

        adapted_y = model(data)

        self.assertTrue(torch.equal(adapted_y[:, 0], base_y[:, 0]))
        self.assertTrue(torch.allclose(adapted_y[:, 1], torch.tensor([1.0, 0.0, 0.0, 0.0])))

    def test_weight_only_residual_missing_orbit_evidence_fails_closed(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            orbit_feature_dim=1,
            orbit_event_state_dim=5,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
            event_adapter_require_valid_orbit=True,
            event_adapter_min_orbit_event_variance=0.5,
        )
        base_y = torch.tensor([[1.25, -2.5], [3.75, 4.5]], dtype=torch.float32)
        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([2.0, 1.0]))

        missing_inputs = make_cached_adapter_graph(base_y)
        missing_mask = make_cached_adapter_graph(base_y)
        missing_mask["var"].orbit_features = torch.ones((2, 1), dtype=torch.float32)
        missing_mask["var"].orbit_event_state = torch.ones((2, 5), dtype=torch.float32)
        missing_mask["var"].orbit_event_variance = torch.ones((2, 1), dtype=torch.float32)
        missing_variance = make_cached_adapter_graph(base_y)
        missing_variance["var"].orbit_features = torch.ones((2, 1), dtype=torch.float32)
        missing_variance["var"].orbit_event_state = torch.ones((2, 5), dtype=torch.float32)
        missing_variance["var"].valid_orbit_mask = torch.ones(2, dtype=torch.bool)

        for data in [missing_inputs, missing_mask, missing_variance]:
            adapted_y = model(data)
            self.assertEqual(adapted_y.shape, base_y.shape)
            self.assertEqual(adapted_y.dtype, base_y.dtype)
            self.assertTrue(torch.equal(adapted_y, base_y))

    def test_weight_only_residual_malformed_orbit_evidence_fails_closed(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            orbit_feature_dim=2,
            orbit_event_state_dim=5,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
            event_adapter_require_valid_orbit=True,
            event_adapter_min_orbit_event_variance=0.5,
        )
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([0.0, 1.0]))

        def valid_data() -> HeteroData:
            data = make_cached_adapter_graph(base_y)
            data["var"].orbit_features = torch.ones((2, 2), dtype=torch.float32)
            data["var"].orbit_event_state = torch.ones((2, 5), dtype=torch.float32)
            data["var"].valid_orbit_mask = torch.ones(2, dtype=torch.bool)
            data["var"].orbit_event_variance = torch.ones((2, 1), dtype=torch.float32)
            return data

        cases = []
        for name, value in [
            ("orbit_features_rows", torch.ones((1, 2), dtype=torch.float32)),
            ("orbit_features_dtype", torch.ones((2, 2), dtype=torch.long)),
            ("orbit_features_device", torch.ones((2, 2), device="meta")),
            ("orbit_features_nonfinite", torch.tensor([[1.0, float("nan")], [1.0, 1.0]])),
        ]:
            data = valid_data()
            data["var"].orbit_features = value
            cases.append((name, data))
        for name, value in [
            ("orbit_event_state_shape", torch.ones((2, 4), dtype=torch.float32)),
            ("orbit_event_state_dtype", torch.ones((2, 5), dtype=torch.long)),
            ("orbit_event_state_device", torch.ones((2, 5), device="meta")),
            ("orbit_event_state_nonfinite", torch.tensor([[1.0, 1.0, 1.0, 1.0, float("inf")], [1.0] * 5])),
        ]:
            data = valid_data()
            data["var"].orbit_event_state = value
            cases.append((name, data))
        for name, value in [
            ("valid_mask_shape", torch.ones((2, 1), dtype=torch.bool)),
            ("valid_mask_dtype", torch.ones(2, dtype=torch.float32)),
            ("valid_mask_device", torch.ones(2, dtype=torch.bool, device="meta")),
        ]:
            data = valid_data()
            data["var"].valid_orbit_mask = value
            cases.append((name, data))
        for name, value in [
            ("variance_shape", torch.ones((1, 1), dtype=torch.float32)),
            ("variance_dtype", torch.ones((2, 1), dtype=torch.long)),
            ("variance_device", torch.ones((2, 1), device="meta")),
            ("variance_nonfinite", torch.tensor([[float("nan")], [1.0]])),
        ]:
            data = valid_data()
            data["var"].orbit_event_variance = value
            cases.append((name, data))

        for name, data in cases:
            with self.subTest(name=name):
                self.assertTrue(torch.equal(model(data), base_y))

    def test_weight_only_residual_strictly_validates_cached_base_embedding(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        wrong_dtype = make_cached_adapter_graph(base_y)
        wrong_dtype["var"].base_embedding = torch.zeros((2, 8), dtype=torch.long)
        wrong_width = make_cached_adapter_graph(base_y)
        wrong_width["var"].base_embedding = torch.zeros((2, 7), dtype=torch.float32)
        wrong_device = make_cached_adapter_graph(base_y)
        wrong_device["var"].base_embedding = torch.zeros((2, 8), device="meta")

        with self.assertRaisesRegex(TypeError, "base_embedding.*floating"):
            model(wrong_dtype)
        with self.assertRaisesRegex(ValueError, "base_embedding expected dim=8"):
            model(wrong_width)
        with self.assertRaisesRegex(ValueError, "base_embedding must be on device"):
            model(wrong_device)

    def test_weight_only_residual_rejects_nonfinite_cached_base_tensors(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        finite_base_y = torch.zeros((2, 2), dtype=torch.float32)

        for name, value in [
            ("nan", float("nan")),
            ("inf", float("inf")),
        ]:
            data = make_cached_adapter_graph(finite_base_y)
            data["var"].base_y[0, 0] = value
            with self.subTest(tensor="base_y", value=name):
                with self.assertRaisesRegex(ValueError, "base_y contains nonfinite values"):
                    model(data)

        for name, value in [
            ("nan", float("nan")),
            ("inf", float("inf")),
        ]:
            data = make_cached_adapter_graph(finite_base_y)
            data["var"].base_embedding[0, 0] = value
            with self.subTest(tensor="base_embedding", value=name):
                with self.assertRaisesRegex(ValueError, "base_embedding contains nonfinite values"):
                    model(data)

    def test_weight_only_residual_rejects_inconsistent_cached_variable_cardinality(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        wrong_width = make_cached_adapter_graph(base_y[:, :1])
        wrong_num_nodes = make_cached_adapter_graph(base_y)
        wrong_num_nodes["var"].num_nodes = 3
        wrong_event_rows = make_cached_adapter_graph(base_y)
        wrong_event_rows["var"].event_state = torch.ones((3, EVENT_VAR_STATE_DIM), dtype=torch.float32)

        with self.assertRaisesRegex(ValueError, "base_y expected dim=2"):
            model(wrong_width)
        with self.assertRaisesRegex(ValueError, "var.num_nodes=3 does not match cache rows=2"):
            model(wrong_num_nodes)
        with self.assertRaisesRegex(ValueError, "event_state rows must equal num_vars=2"):
            model(wrong_event_rows)

    def test_weight_only_residual_rejects_cached_dtype_mismatch(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        wrong_base_y = make_cached_adapter_graph(base_y.to(dtype=torch.float64))
        wrong_embedding = make_cached_adapter_graph(base_y)
        wrong_embedding["var"].base_embedding = wrong_embedding["var"].base_embedding.to(dtype=torch.float64)
        wrong_event_state = make_cached_adapter_graph(base_y)
        wrong_event_state["var"].event_state = wrong_event_state["var"].event_state.to(dtype=torch.float64)

        with self.assertRaisesRegex(TypeError, "base_y dtype must match event_adapter dtype torch.float32"):
            model(wrong_base_y)
        with self.assertRaisesRegex(TypeError, "base_embedding dtype must match event_adapter dtype torch.float32"):
            model(wrong_embedding)
        with self.assertRaisesRegex(TypeError, "event_state dtype must match event_adapter dtype torch.float32"):
            model(wrong_event_state)

    def test_weight_only_residual_rejects_malformed_cached_var_batch(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        cases = [
            ("negative", torch.tensor([0, -1]), ValueError, "batch IDs must be nonnegative"),
            ("wrong_length", torch.tensor([0]), ValueError, "batch length must equal num_vars=2"),
            ("int8", torch.tensor([0, 0], dtype=torch.int8), TypeError, "batch must have dtype torch.long"),
            ("int16", torch.tensor([0, 0], dtype=torch.int16), TypeError, "batch must have dtype torch.long"),
            ("int32", torch.tensor([0, 0], dtype=torch.int32), TypeError, "batch must have dtype torch.long"),
            ("uint8", torch.tensor([0, 0], dtype=torch.uint8), TypeError, "batch must have dtype torch.long"),
            ("bool", torch.tensor([False, False]), TypeError, "batch must have dtype torch.long"),
            ("floating", torch.tensor([0.0, 0.0]), TypeError, "batch must have dtype torch.long"),
            ("wrong_device", torch.tensor([0, 0], device="meta"), ValueError, "batch must be on device"),
            ("noncontiguous", torch.tensor([0, 2]), ValueError, "batch IDs must be contiguous"),
        ]

        for name, batch, error_type, message in cases:
            data = make_cached_adapter_graph(base_y)
            data["var"].batch = batch
            with self.subTest(name=name):
                with self.assertRaisesRegex(error_type, message):
                    model(data)

    def test_weight_only_residual_rejects_inconsistent_declared_num_graphs(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        data = next(iter(DataLoader([
            make_cached_adapter_graph(base_y[:1]),
            make_cached_adapter_graph(base_y[1:]),
        ], batch_size=2)))
        data._num_graphs = 3

        with self.assertRaisesRegex(ValueError, "declared num_graphs=3 does not match batch graph count=2"):
            model(data)

    def test_weight_only_residual_rejects_ptr_with_wrong_graph_segments(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        data = next(iter(DataLoader([
            make_cached_adapter_graph(base_y),
            make_cached_adapter_graph(base_y),
        ], batch_size=2)))
        self.assertTrue(torch.equal(data["var"].batch, torch.tensor([0, 0, 1, 1])))
        data["var"].ptr = torch.tensor([0, 1, 4], dtype=torch.long)

        with self.assertRaisesRegex(ValueError, "var.ptr must exactly match batch graph segments"):
            model(data)

    def test_weight_only_residual_requires_torch_long_var_ptr(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        base_y = torch.zeros((130, 2), dtype=torch.float32)
        cases = [
            ("int8_overflow", torch.tensor([0, 130], dtype=torch.long).to(dtype=torch.int8)),
            ("int16", torch.tensor([0, 130], dtype=torch.int16)),
            ("int32", torch.tensor([0, 130], dtype=torch.int32)),
            ("uint8", torch.tensor([0, 130], dtype=torch.uint8)),
            ("bool", torch.tensor([False, True], dtype=torch.bool)),
            ("floating", torch.tensor([0.0, 130.0], dtype=torch.float32)),
        ]

        for name, ptr in cases:
            data = make_cached_adapter_graph(base_y)
            data["var"].batch = torch.zeros(130, dtype=torch.long)
            data["var"].ptr = ptr
            with self.subTest(name=name):
                with self.assertRaisesRegex(TypeError, "var.ptr must have dtype torch.long"):
                    model(data)

    def test_weight_only_residual_mixed_precision_optional_evidence_is_dtype_safe(self):
        for dtype in [torch.float16, torch.bfloat16]:
            with self.subTest(dtype=str(dtype)):
                model = GNN(
                    channels=4,
                    lit_feat_dim=1,
                    cls_feat_dim=1,
                    num_layers=1,
                    out_dim=2,
                    var_state_dim=EVENT_VAR_STATE_DIM,
                    orbit_feature_dim=1,
                    orbit_event_state_dim=5,
                    event_adapter_enabled=True,
                    event_adapter_hidden_dim=8,
                    event_adapter_fusion="weight_only_residual",
                    event_adapter_require_valid_orbit=True,
                    event_adapter_min_orbit_event_variance=0.5,
                ).to(dtype=dtype)
                base_y = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=dtype)
                with torch.no_grad():
                    model.event_adapter[-1].bias.copy_(torch.tensor([0.0, 1.0], dtype=dtype))

                def cache_graph() -> HeteroData:
                    data = make_cached_adapter_graph(base_y)
                    data["var"].base_embedding = data["var"].base_embedding.to(dtype=dtype)
                    data["var"].event_state = data["var"].event_state.to(dtype=dtype)
                    return data

                missing = cache_graph()
                missing_y = model(missing)
                self.assertEqual(missing_y.shape, base_y.shape)
                self.assertEqual(missing_y.dtype, dtype)
                self.assertTrue(torch.equal(missing_y, base_y))

                malformed = cache_graph()
                malformed["var"].orbit_features = torch.tensor([[float("nan")], [1.0]])
                malformed["var"].orbit_event_state = torch.ones((2, 5), dtype=torch.float32)
                malformed["var"].valid_orbit_mask = torch.ones(2, dtype=torch.bool)
                malformed["var"].orbit_event_variance = torch.ones((2, 1), dtype=torch.float32)
                malformed_y = model(malformed)
                self.assertEqual(malformed_y.shape, base_y.shape)
                self.assertEqual(malformed_y.dtype, dtype)
                self.assertTrue(torch.equal(malformed_y, base_y))

                valid = cache_graph()
                valid["var"].orbit_features = torch.ones((2, 1), dtype=torch.float32)
                valid["var"].orbit_event_state = torch.ones((2, 5), dtype=torch.float32)
                valid["var"].valid_orbit_mask = torch.ones(2, dtype=torch.bool)
                valid["var"].orbit_event_variance = torch.ones((2, 1), dtype=torch.float32)
                valid_y = model(valid)
                self.assertEqual(valid_y.dtype, dtype)
                self.assertTrue(torch.equal(valid_y[:, 0], base_y[:, 0]))
                self.assertTrue(torch.equal(valid_y[:, 1], base_y[:, 1] + 1.0))

    def test_weight_only_residual_optional_evidence_conversion_overflow_fails_closed(self):
        cases = [
            (torch.float16, torch.float32, 1.0e20),
            (torch.bfloat16, torch.float64, 1.0e300),
        ]
        for adapter_dtype, evidence_dtype, large_value in cases:
            with self.subTest(adapter_dtype=str(adapter_dtype), evidence_dtype=str(evidence_dtype)):
                model = GNN(
                    channels=4,
                    lit_feat_dim=1,
                    cls_feat_dim=1,
                    num_layers=1,
                    out_dim=2,
                    var_state_dim=EVENT_VAR_STATE_DIM,
                    orbit_feature_dim=1,
                    orbit_event_state_dim=5,
                    event_adapter_enabled=True,
                    event_adapter_hidden_dim=8,
                    event_adapter_fusion="weight_only_residual",
                    event_adapter_require_valid_orbit=True,
                    event_adapter_min_orbit_event_variance=0.5,
                ).to(dtype=adapter_dtype)
                base_y = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=adapter_dtype)
                with torch.no_grad():
                    model.event_adapter[-1].bias.copy_(torch.tensor([0.0, 1.0], dtype=adapter_dtype))
                data = make_cached_adapter_graph(base_y)
                data["var"].base_embedding = data["var"].base_embedding.to(dtype=adapter_dtype)
                data["var"].event_state = data["var"].event_state.to(dtype=adapter_dtype)
                data["var"].orbit_features = torch.full(
                    (2, 1), large_value, dtype=evidence_dtype
                )
                data["var"].orbit_event_state = torch.ones((2, 5), dtype=evidence_dtype)
                data["var"].valid_orbit_mask = torch.ones(2, dtype=torch.bool)
                data["var"].orbit_event_variance = torch.ones((2, 1), dtype=evidence_dtype)

                result = model(data)

                self.assertEqual(result.dtype, adapter_dtype)
                self.assertTrue(torch.equal(result, base_y))

    def test_weight_only_residual_out_dim_one_has_zero_delta(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=1,
            var_state_dim=EVENT_VAR_STATE_DIM,
            orbit_feature_dim=1,
            orbit_event_state_dim=5,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
        )
        base_y = torch.tensor([[2.0], [3.0]])
        data = make_cached_adapter_graph(base_y)
        data["var"].orbit_features = torch.ones((2, 1), dtype=torch.float32)
        data["var"].orbit_event_state = torch.ones((2, 5), dtype=torch.float32)
        with torch.no_grad():
            model.event_adapter[-1].bias.fill_(4.0)

        self.assertTrue(torch.equal(model(data), base_y))

    def test_weight_only_residual_permutation_aligned_evidence_aligns_delta(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            orbit_feature_dim=1,
            orbit_event_state_dim=5,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="weight_only_residual",
            event_adapter_require_valid_orbit=True,
            event_adapter_min_orbit_event_variance=0.5,
        )
        base_y = torch.zeros((3, 2), dtype=torch.float32)
        data = make_cached_adapter_graph(base_y)
        data["var"].orbit_features = torch.ones((3, 1), dtype=torch.float32)
        data["var"].orbit_event_state = torch.ones((3, 5), dtype=torch.float32)
        data["var"].valid_orbit_mask = torch.tensor([True, False, True])
        data["var"].orbit_event_variance = torch.tensor([[0.5], [1.0], [0.75]])
        with torch.no_grad():
            model.event_adapter[-1].bias.copy_(torch.tensor([0.0, 1.0]))
        original_delta = model(data) - base_y

        permutation = torch.tensor([2, 0, 1])
        permuted = make_cached_adapter_graph(base_y[permutation])
        permuted["var"].orbit_features = data["var"].orbit_features[permutation]
        permuted["var"].orbit_event_state = data["var"].orbit_event_state[permutation]
        permuted["var"].valid_orbit_mask = data["var"].valid_orbit_mask[permutation]
        permuted["var"].orbit_event_variance = data["var"].orbit_event_variance[permutation]
        permuted_delta = model(permuted) - base_y[permutation]

        self.assertTrue(torch.equal(permuted_delta, original_delta[permutation]))

    def test_trace_distillation_can_train_only_polarity_gate(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=3,
            var_state_dim=EVENT_VAR_STATE_DIM_POLARITY,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
            event_adapter_fusion="polarity_gated_residual",
            event_adapter_residual_state_dim=20,
            event_adapter_polarity_gate_indices=list(range(20, 29)),
        )

        freeze_non_adapter_parameters(model, adapter_train_mode="polarity_gate")

        trainable_names = [name for name, param in model.named_parameters() if param.requires_grad]
        self.assertTrue(trainable_names)
        self.assertTrue(all("event_adapter_polarity_gate" in name for name in trainable_names))

    def test_init_model_reads_event_adapter_gate_indices_from_config(self):
        cfg = OmegaConf.create({
            "model": {
                "channels": 4,
                "num_layers": 1,
                "global_state_dim": 0,
                "var_state_dim": EVENT_VAR_STATE_DIM_POLARITY,
                "aggr": ["mean"],
                "feature_encoder": "mlp",
                "dropout": 0.0,
                "separate_encoders": False,
                "learnable_sigma": False,
                "event_adapter": {
                    "enabled": True,
                    "hidden_dim": 8,
                    "fusion": "sbe",
                    "min_orbit_event_variance": 0.125,
                    "require_valid_orbit": True,
                    "delta_scale": 0.25,
                    "delta_clip": 0.5,
                    "gate_indices": [2, 3],
                    "residual_state_dim": 20,
                    "polarity_gate_indices": [20, 21, 22],
                    "polarity_gate_bias_init": 5.0,
                    "polarity_gate_min": 0.95,
                    "graph_gate_indices": [7, 8],
                    "graph_gate_threshold": 0.25,
                    "base_rho_gate_threshold": -0.1,
                    "selector_feature_names": ["base_rho_mean", "event_gate_mean"],
                    "selector_weights": [1.5, -0.5],
                    "selector_bias": 0.25,
                    "selector_threshold": 0.4,
                    "selector_feature_mean": [0.1, 0.2],
                    "selector_feature_std": [0.3, 0.4],
                    "risk_selector_mlp_weights": [[[1.0, -1.0]]],
                    "risk_selector_mlp_biases": [[0.0]],
                    "local_reopen_enabled": True,
                    "local_reopen_feature_names": ["warmup_c1000_minus_warmup_c750_decisions"],
                    "local_reopen_ops": [">="],
                    "local_reopen_values": [294.0],
                },
                "orbit_feature_dim": 10,
                "orbit_event_state_dim": 20,
            }
        })

        model = init_model(cfg, DummyTransform())

        self.assertEqual(model.event_adapter_gate_indices, [2, 3])
        self.assertEqual(model.event_adapter_fusion, "sbe")
        self.assertEqual(model.orbit_feature_dim, 10)
        self.assertEqual(model.orbit_event_state_dim, 20)
        self.assertEqual(model.event_adapter_min_orbit_event_variance, 0.125)
        self.assertTrue(model.event_adapter_require_valid_orbit)
        self.assertEqual(model.event_adapter_delta_scale, 0.25)
        self.assertEqual(model.event_adapter_delta_clip, 0.5)
        self.assertEqual(model.event_adapter_residual_state_dim, 20)
        self.assertEqual(model.event_adapter_polarity_gate_indices, [20, 21, 22])
        self.assertEqual(model.event_adapter_polarity_gate_bias_init, 5.0)
        self.assertEqual(model.event_adapter_polarity_gate_min, 0.95)
        self.assertEqual(model.event_adapter_graph_gate_indices, [7, 8])
        self.assertEqual(model.event_adapter_graph_gate_threshold, 0.25)
        self.assertEqual(model.event_adapter_base_rho_gate_threshold, -0.1)
        self.assertEqual(model.event_adapter_selector_feature_names, ["base_rho_mean", "event_gate_mean"])
        self.assertEqual(model.event_adapter_selector_weights, [1.5, -0.5])
        self.assertEqual(model.event_adapter_selector_bias, 0.25)
        self.assertEqual(model.event_adapter_selector_threshold, 0.4)
        self.assertEqual(model.event_adapter_selector_feature_mean, [0.1, 0.2])
        self.assertEqual(model.event_adapter_selector_feature_std, [0.3, 0.4])
        self.assertEqual(model.event_adapter_risk_selector_mlp_weights, [[[1.0, -1.0]]])
        self.assertEqual(model.event_adapter_risk_selector_mlp_biases, [[0.0]])
        self.assertTrue(model.event_adapter_local_reopen_enabled)
        self.assertEqual(
            model.event_adapter_local_reopen_feature_names,
            ["warmup_c1000_minus_warmup_c750_decisions"],
        )
        self.assertEqual(model.event_adapter_local_reopen_ops, [">="])
        self.assertEqual(model.event_adapter_local_reopen_values, [294.0])

    def test_orbit_dimension_config_prefers_nested_event_adapter_values(self):
        cfg = OmegaConf.create({
            "model": {
                "channels": 4,
                "num_layers": 1,
                "global_state_dim": 0,
                "var_state_dim": EVENT_VAR_STATE_DIM,
                "orbit_feature_dim": 99,
                "orbit_event_state_dim": 98,
                "aggr": ["mean"],
                "feature_encoder": "mlp",
                "dropout": 0.0,
                "separate_encoders": False,
                "learnable_sigma": False,
                "event_adapter": {
                    "enabled": True,
                    "hidden_dim": 8,
                    "fusion": "weight_only_residual",
                    "orbit_feature_dim": 3,
                    "orbit_event_state_dim": 5,
                },
            }
        })

        model = init_model(cfg, DummyTransform())

        self.assertEqual(model.orbit_feature_dim, 3)
        self.assertEqual(model.orbit_event_state_dim, 5)
        self.assertEqual(model.event_adapter[0].in_features, 8 + EVENT_VAR_STATE_DIM + 3 + 5)

    def test_sample_var_params_can_cache_base_adapter_features(self):
        model = make_model()
        loader = DataLoader([make_graph()], batch_size=1)

        data_list = sample_var_params(
            model=model,
            loader=loader,
            num_samples=1,
            cache_var_features=True,
        )

        graph = data_list[0]
        self.assertEqual(graph["var"].base_embedding.shape, (2, 8))
        self.assertEqual(graph["var"].base_y.shape, (2, 2))


if __name__ == "__main__":
    unittest.main()
