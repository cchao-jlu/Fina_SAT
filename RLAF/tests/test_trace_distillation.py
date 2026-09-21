import math
import json
import tempfile
import unittest
from pathlib import Path

import torch
import pandas as pd
from torch_geometric.data import HeteroData
from torch_geometric.loader import DataLoader

from src.model.model import GNN
from src.solving.state import EVENT_VAR_STATE_DIM
from src.training.trace_distill import (
    PermutationConsistencyPair,
    TraceLabelConfig,
    align_new_to_old,
    attach_trace_pseudo_labels,
    build_permutation_consistency_pairs,
    build_trace_distillation_graphs,
    build_trace_pseudo_label,
    adapter_delta_magnitude_loss,
    freeze_non_adapter_parameters,
    negative_guard_loss,
    no_activity_variable_mask,
    permutation_consistency_loss,
    relabel_trace_distillation_graphs,
    trace_distillation_loss,
    train_trace_distillation_epoch,
)


def make_cached_adapter_graph(num_vars: int = 3) -> HeteroData:
    data = HeteroData()
    data["lit"].num_nodes = 2 * num_vars
    data["var"].num_nodes = num_vars
    data["var"].base_embedding = torch.ones((num_vars, 8), dtype=torch.float32)
    data["var"].base_y = torch.zeros((num_vars, 2), dtype=torch.float32)
    data["var"].event_state = torch.ones((num_vars, EVENT_VAR_STATE_DIM), dtype=torch.float32)
    data.cnf_id = torch.tensor([0], dtype=torch.long)
    return data


class TraceDistillationTest(unittest.TestCase):
    def test_trace_pseudo_label_prefers_low_lbd_and_useful_decision_variables(self):
        stats = {
            "event_var_low_lbd_learnt_lits": [0, 5, 1],
            "event_var_useful_decisions": [0, 2, 0],
            "event_var_conflict_lits": [0, 1, 3],
            "event_var_propagations": [2, 4, 0],
            "event_var_activity": [0, 1, 9],
        }
        base_y = torch.zeros((3, 2), dtype=torch.float32)
        config = TraceLabelConfig(
            low_lbd_weight=1.0,
            useful_decision_weight=1.0,
            conflict_rank_weight=0.0,
            propagation_rank_weight=0.0,
            activity_rank_weight=0.0,
            target_scale=2.0,
        )

        label = build_trace_pseudo_label(stats, num_vars=3, base_y=base_y, config=config)

        self.assertEqual(label.target_y.shape, (3, 2))
        self.assertTrue(torch.allclose(label.target_y[:, 0], base_y[:, 0]))
        self.assertGreater(label.target_y[1, 1].item(), label.target_y[2, 1].item())
        self.assertGreater(label.target_y[2, 1].item(), label.target_y[0, 1].item())
        self.assertGreater(label.confidence[1].item(), label.confidence[0].item())
        self.assertIn("low_lbd_rank", label.components)
        self.assertIn("useful_decision_rank", label.components)

    def test_trace_pseudo_label_exposes_conflict_and_propagation_ranks(self):
        stats = {
            "event_var_learnt_lits": [0, 0, 8],
            "event_var_decisions": [4, 0, 0],
            "event_var_conflict_lits": [0, 2, 0],
            "event_var_propagations": [0, 0, 6],
            "event_var_activity": [0, 1, 0],
        }

        label = build_trace_pseudo_label(stats, num_vars=3)

        self.assertTrue(math.isclose(label.components["conflict_rank"][1].item(), 1.0))
        self.assertTrue(math.isclose(label.components["propagation_rank"][2].item(), 1.0))
        self.assertEqual(label.target_y.shape, (3, 2))
        self.assertEqual(label.confidence.shape, (3,))

    def test_trace_pseudo_label_can_clip_mu_delta_around_base_prediction(self):
        stats = {
            "event_var_low_lbd_learnt_lits": [0, 100, 0],
            "event_var_useful_decisions": [0, 0, 100],
            "event_var_conflict_lits": [0, 0, 0],
            "event_var_propagations": [0, 0, 0],
            "event_var_activity": [0, 0, 0],
        }
        base_y = torch.tensor([[0.0, 2.0], [0.0, 2.0], [0.0, 2.0]], dtype=torch.float32)
        config = TraceLabelConfig(
            low_lbd_weight=1.0,
            useful_decision_weight=1.0,
            conflict_rank_weight=0.0,
            propagation_rank_weight=0.0,
            activity_rank_weight=0.0,
            target_scale=10.0,
            target_delta_clip=0.5,
        )

        label = build_trace_pseudo_label(stats, num_vars=3, base_y=base_y, config=config)
        delta_mu = label.target_y[:, 1] - base_y[:, 1]

        self.assertLessEqual(delta_mu.max().item(), 0.5)
        self.assertGreaterEqual(delta_mu.min().item(), -0.5)
        self.assertTrue(torch.allclose(label.target_y[:, 0], base_y[:, 0]))

    def test_focus_gated_trace_label_downweights_unfocused_events(self):
        stats = {
            "event_var_low_lbd_learnt_lits": [1, 1, 1, 1],
            "event_var_useful_decisions": [0, 0, 1, 0],
            "event_var_conflict_lits": [1, 1, 1, 1],
            "event_var_propagations": [0, 0, 0, 0],
            "event_var_activity": [0, 0, 0, 0],
        }
        base_y = torch.zeros((4, 2), dtype=torch.float32)
        ungated = build_trace_pseudo_label(
            stats,
            num_vars=4,
            base_y=base_y,
            config=TraceLabelConfig(
                low_lbd_weight=0.0,
                useful_decision_weight=1.0,
                conflict_rank_weight=0.0,
                propagation_rank_weight=0.0,
                activity_rank_weight=0.0,
                target_scale=1.0,
            ),
        )
        gated = build_trace_pseudo_label(
            stats,
            num_vars=4,
            base_y=base_y,
            config=TraceLabelConfig(
                low_lbd_weight=0.0,
                useful_decision_weight=1.0,
                conflict_rank_weight=0.0,
                propagation_rank_weight=0.0,
                activity_rank_weight=0.0,
                target_scale=1.0,
                focus_gate_enabled=True,
                focus_topk_ratio=0.25,
                focus_min_topk_mass=0.5,
                focus_min_multiplier=0.25,
            ),
        )

        ungated_delta = (ungated.target_y[:, 1] - base_y[:, 1]).abs().max()
        gated_delta = (gated.target_y[:, 1] - base_y[:, 1]).abs().max()
        self.assertLess(gated_delta.item(), ungated_delta.item())
        self.assertTrue(torch.allclose(gated.components["focus_multiplier"], torch.full((4,), 0.625)))
        self.assertLess(gated.confidence.max().item(), ungated.confidence.max().item())

    def test_attach_trace_pseudo_labels_adds_targets_to_graph(self):
        data = make_cached_adapter_graph(num_vars=2)
        stats = {
            "event_var_low_lbd_learnt_lits": [0, 3],
            "event_var_useful_decisions": [0, 1],
            "event_var_conflict_lits": [0, 2],
            "event_var_propagations": [1, 0],
            "event_var_activity": [0, 2],
        }

        updated = attach_trace_pseudo_labels(data, stats)

        self.assertEqual(updated["var"].trace_target_y.shape, (2, 2))
        self.assertEqual(updated["var"].trace_confidence.shape, (2,))
        self.assertGreater(updated["var"].trace_confidence[1].item(), updated["var"].trace_confidence[0].item())

    def test_build_trace_distillation_graphs_expands_solver_samples(self):
        data = make_cached_adapter_graph(num_vars=2)
        data["var"].var_params = torch.zeros((2, 2, 2), dtype=torch.float32)
        solver_stats = pd.DataFrame(
            [
                {
                    "cnf_id": 0,
                    "sample_id": 0,
                    "event_var_decisions": [1, 0],
                    "event_var_propagations": [2, 0],
                    "event_var_conflict_lits": [0, 3],
                    "event_var_learnt_lits": [0, 4],
                    "event_var_activity": [0, 1],
                },
                {
                    "cnf_id": 0,
                    "sample_id": 1,
                    "event_var_decisions": [0, 1],
                    "event_var_propagations": [0, 2],
                    "event_var_conflict_lits": [3, 0],
                    "event_var_learnt_lits": [5, 0],
                    "event_var_activity": [1, 0],
                },
            ]
        )

        graphs = build_trace_distillation_graphs(
            [data],
            solver_stats,
            var_state_dim=EVENT_VAR_STATE_DIM,
        )

        self.assertEqual(len(graphs), 2)
        self.assertEqual(graphs[0].sample_id.item(), 0)
        self.assertEqual(graphs[1].sample_id.item(), 1)
        self.assertEqual(graphs[0]["var"].var_params.shape, (2, 1, 2))
        self.assertEqual(graphs[0]["var"].event_state.shape, (2, EVENT_VAR_STATE_DIM))
        self.assertEqual(graphs[0]["var"].trace_target_y.shape, (2, 2))

    def test_trace_distillation_loss_uses_confidence_weights(self):
        pred = torch.tensor([[0.0, 1.0], [0.0, 3.0]], dtype=torch.float32)
        target = torch.tensor([[0.0, 2.0], [10.0, 10.0]], dtype=torch.float32)
        confidence = torch.tensor([1.0, 0.0], dtype=torch.float32)

        loss = trace_distillation_loss(pred, target, confidence)

        self.assertTrue(torch.isclose(loss, torch.tensor(1.0)))

    def test_no_activity_negative_loss_pulls_adapter_to_base(self):
        pred = torch.tensor([[0.0, 1.0], [0.0, 3.0]], dtype=torch.float32)
        target = torch.tensor([[0.0, 1.0], [0.0, 3.0]], dtype=torch.float32)
        confidence = torch.ones(2, dtype=torch.float32)
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        event_state = torch.zeros((2, EVENT_VAR_STATE_DIM), dtype=torch.float32)
        event_state[:, 1] = torch.tensor([5.0, 7.0], dtype=torch.float32)

        loss = trace_distillation_loss(
            pred,
            target,
            confidence,
            base_y=base_y,
            event_state=event_state,
            config=TraceLabelConfig(
                no_activity_negative_weight=2.0,
                no_activity_gate_indices=[0, 2],
                no_activity_negative_mu_loss_weight=1.0,
            ),
        )

        self.assertTrue(torch.isclose(loss, torch.tensor(10.0)))

    def test_no_activity_mask_uses_graph_level_decision_conflict_evidence(self):
        event_state = torch.zeros((4, EVENT_VAR_STATE_DIM), dtype=torch.float32)
        event_state[2, 0] = 1.0
        batch = torch.tensor([0, 0, 1, 1], dtype=torch.long)

        mask = no_activity_variable_mask(event_state, var_batch=batch, gate_indices=[0, 2])

        self.assertEqual(mask.tolist(), [True, True, False, False])

    def test_negative_guard_no_valid_orbit_pulls_adapter_to_base(self):
        pred = torch.tensor([[0.0, 2.0], [0.0, -1.0], [0.0, 4.0]], dtype=torch.float32)
        target = pred.clone()
        confidence = torch.ones(3, dtype=torch.float32)
        base_y = torch.zeros((3, 2), dtype=torch.float32)
        valid_orbit_mask = torch.zeros(3, dtype=torch.bool)

        loss = trace_distillation_loss(
            pred,
            target,
            confidence,
            base_y=base_y,
            valid_orbit_mask=valid_orbit_mask,
            config=TraceLabelConfig(
                negative_guard_weight=0.5,
                negative_guard_mu_loss_weight=1.0,
            ),
        )

        self.assertTrue(torch.isclose(loss, torch.tensor(0.5 * ((4.0 + 1.0 + 16.0) / 3.0))))

    def test_explicit_negative_guard_mask_only_penalizes_marked_variables(self):
        pred = torch.tensor([[0.0, 2.0], [0.0, -1.0], [0.0, 4.0]], dtype=torch.float32)
        base_y = torch.zeros((3, 2), dtype=torch.float32)
        mask = torch.tensor([False, True, True])

        loss = negative_guard_loss(
            pred_y=pred,
            base_y=base_y,
            negative_guard_mask=mask,
            valid_orbit_mask=None,
            var_batch=None,
            config=TraceLabelConfig(
                negative_guard_weight=2.0,
                negative_guard_mu_loss_weight=1.0,
                negative_guard_no_valid_orbit=False,
            ),
        )

        self.assertTrue(torch.isclose(loss, torch.tensor(2.0 * ((1.0 + 16.0) / 2.0))))

    def test_adapter_delta_magnitude_loss_penalizes_large_delta_after_margin(self):
        pred = torch.tensor([[0.0, 0.5], [0.0, 2.0]], dtype=torch.float32)
        base_y = torch.zeros((2, 2), dtype=torch.float32)

        loss = adapter_delta_magnitude_loss(
            pred_y=pred,
            base_y=base_y,
            config=TraceLabelConfig(
                adapter_delta_magnitude_weight=3.0,
                adapter_delta_magnitude_mu_loss_weight=1.0,
                adapter_delta_magnitude_margin=1.0,
            ),
        )

        self.assertTrue(torch.isclose(loss, torch.tensor(3.0 * 0.5)))

    def test_align_new_to_old_uses_old_to_new_permutation(self):
        values = torch.tensor([[30.0], [10.0], [20.0]], dtype=torch.float32)
        # old 1 -> new 2, old 2 -> new 3, old 3 -> new 1
        aligned = align_new_to_old(values, torch.tensor([1, 2, 0], dtype=torch.long))

        self.assertEqual(aligned.view(-1).tolist(), [10.0, 20.0, 30.0])

    def test_build_permutation_consistency_pairs_from_manifest_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_cnf = root / "base.cnf"
            perm_cnf = root / "perm.cnf"
            metadata = root / "perm.metadata.json"
            base_cnf.write_text("p cnf 3 0\n", encoding="utf-8")
            perm_cnf.write_text("p cnf 3 0\n", encoding="utf-8")
            metadata.write_text(json.dumps({"permutation": [2, 3, 1]}), encoding="utf-8")
            manifest = pd.DataFrame(
                [
                    {
                        "family": "f",
                        "instance_id": "base",
                        "base_instance_id": "base",
                        "variant": "base",
                        "cnf_path": str(base_cnf),
                        "metadata_path": str(root / "base.metadata.json"),
                    },
                    {
                        "family": "f",
                        "instance_id": "perm",
                        "base_instance_id": "base",
                        "variant": "perm_seed",
                        "cnf_path": str(perm_cnf),
                        "metadata_path": str(metadata),
                    },
                ]
            )
            base = make_cached_adapter_graph(num_vars=3)
            base.cnf_id = torch.tensor([0], dtype=torch.long)
            base.sample_id = torch.tensor(0, dtype=torch.long)
            perm = make_cached_adapter_graph(num_vars=3)
            perm.cnf_id = torch.tensor([1], dtype=torch.long)
            perm.sample_id = torch.tensor(0, dtype=torch.long)
            solver_stats = pd.DataFrame(
                [
                    {"cnf_id": 0, "sample_id": 0, "file": str(base_cnf)},
                    {"cnf_id": 1, "sample_id": 0, "file": str(perm_cnf)},
                ]
            )

            pairs = build_permutation_consistency_pairs([base, perm], solver_stats=solver_stats, manifest=manifest)

            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0].permutation_old_to_new.tolist(), [1, 2, 0])
            self.assertEqual(pairs[0].base_instance_id, "base")
            self.assertEqual(pairs[0].variant, "perm_seed")

    def test_build_permutation_pairs_fallback_keeps_manifest_cnf_indices_after_static_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = root / "perm.metadata.json"
            metadata.write_text(json.dumps({"permutation": [2, 3, 1]}), encoding="utf-8")
            manifest = pd.DataFrame(
                [
                    {
                        "family": "ignored",
                        "instance_id": "static",
                        "base_instance_id": "static",
                        "variant": "base",
                        "metadata_path": str(root / "static.metadata.json"),
                        "event_audit_role": "static_only",
                    },
                    {
                        "family": "f",
                        "instance_id": "base",
                        "base_instance_id": "base",
                        "variant": "base",
                        "metadata_path": str(root / "base.metadata.json"),
                        "event_audit_role": "event",
                    },
                    {
                        "family": "f",
                        "instance_id": "perm",
                        "base_instance_id": "base",
                        "variant": "perm_seed",
                        "metadata_path": str(metadata),
                        "event_audit_role": "event",
                    },
                ]
            )
            base = make_cached_adapter_graph(num_vars=3)
            base.cnf_id = torch.tensor([1], dtype=torch.long)
            base.sample_id = torch.tensor(0, dtype=torch.long)
            perm = make_cached_adapter_graph(num_vars=3)
            perm.cnf_id = torch.tensor([2], dtype=torch.long)
            perm.sample_id = torch.tensor(0, dtype=torch.long)
            solver_stats = pd.DataFrame(
                [
                    {"cnf_id": 1, "sample_id": 0},
                    {"cnf_id": 2, "sample_id": 0},
                ]
            )

            pairs = build_permutation_consistency_pairs([base, perm], solver_stats=solver_stats, manifest=manifest)

            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0].base_instance_id, "base")
            self.assertEqual(pairs[0].permuted_instance_id, "perm")

    def test_permutation_consistency_loss_penalizes_aligned_mu_difference(self):
        class StaticModel(torch.nn.Module):
            def forward(self, data):
                return data["var"].base_y

        base = make_cached_adapter_graph(num_vars=3)
        base["var"].base_y = torch.tensor([[0.0, 1.0], [0.0, 2.0], [0.0, 3.0]], dtype=torch.float32)
        perm = make_cached_adapter_graph(num_vars=3)
        perm["var"].base_y = torch.tensor([[0.0, 3.0], [0.0, 1.5], [0.0, 2.0]], dtype=torch.float32)
        pairs = PermutationConsistencyPair(
            base_graph=base,
            permuted_graph=perm,
            permutation_old_to_new=torch.tensor([1, 2, 0], dtype=torch.long),
            family="f",
            base_instance_id="base",
            permuted_instance_id="perm",
            variant="perm",
            sample_id=0,
        )

        loss = permutation_consistency_loss(
            model=StaticModel(),
            pairs=[pairs],
            device="cpu",
            config=TraceLabelConfig(
                permutation_consistency_weight=2.0,
                permutation_consistency_rho_loss_weight=0.0,
                permutation_consistency_mu_loss_weight=1.0,
            ),
        )

        self.assertTrue(torch.isclose(loss, torch.tensor(2.0 * ((0.5**2) / 3.0))))

    def test_permutation_delta_consistency_loss_penalizes_adapter_delta_mismatch(self):
        class DeltaModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.scale = torch.nn.Parameter(torch.tensor(1.0))

            def forward(self, data):
                return data["var"].base_y + self.scale * data["var"].delta_template

        base = make_cached_adapter_graph(num_vars=3)
        base["var"].base_y = torch.zeros((3, 2), dtype=torch.float32)
        base["var"].delta_template = torch.tensor([[0.0, 1.0], [0.0, 2.0], [0.0, 3.0]], dtype=torch.float32)
        perm = make_cached_adapter_graph(num_vars=3)
        perm["var"].base_y = torch.zeros((3, 2), dtype=torch.float32)
        perm["var"].delta_template = torch.tensor([[0.0, 3.0], [0.0, 1.5], [0.0, 2.0]], dtype=torch.float32)
        pairs = PermutationConsistencyPair(
            base_graph=base,
            permuted_graph=perm,
            permutation_old_to_new=torch.tensor([1, 2, 0], dtype=torch.long),
            family="f",
            base_instance_id="base",
            permuted_instance_id="perm",
            variant="perm",
            sample_id=0,
        )

        loss = permutation_consistency_loss(
            model=DeltaModel(),
            pairs=[pairs],
            device="cpu",
            config=TraceLabelConfig(
                permutation_consistency_weight=0.0,
                permutation_delta_consistency_weight=2.0,
                permutation_delta_consistency_rho_loss_weight=0.0,
                permutation_delta_consistency_mu_loss_weight=1.0,
            ),
        )

        self.assertTrue(torch.isclose(loss, torch.tensor(2.0 * ((0.5**2) / 3.0))))

    def test_valid_orbit_only_distillation_ignores_invalid_rows(self):
        pred = torch.tensor([[0.0, 1.0], [0.0, 100.0]], dtype=torch.float32)
        target = torch.tensor([[0.0, 3.0], [0.0, -100.0]], dtype=torch.float32)
        confidence = torch.ones(2, dtype=torch.float32)
        valid_orbit_mask = torch.tensor([True, False])

        loss = trace_distillation_loss(
            pred,
            target,
            confidence,
            valid_orbit_mask=valid_orbit_mask,
            config=TraceLabelConfig(valid_orbit_only_distillation=True),
        )

        self.assertTrue(torch.isclose(loss, torch.tensor(4.0)))

    def test_relabel_trace_distillation_graphs_uses_current_label_config(self):
        data = make_cached_adapter_graph(num_vars=2)
        data.sample_id = torch.tensor(0, dtype=torch.long)
        data["var"].trace_target_y = torch.zeros((2, 2), dtype=torch.float32)
        data["var"].trace_confidence = torch.zeros(2, dtype=torch.float32)
        solver_stats = pd.DataFrame(
            [
                {
                    "cnf_id": 0,
                    "sample_id": 0,
                    "event_var_low_lbd_learnt_lits": [0, 5],
                    "event_var_useful_decisions": [5, 0],
                    "event_var_conflict_lits": [0, 0],
                    "event_var_propagations": [0, 0],
                    "event_var_activity": [0, 0],
                }
            ]
        )

        relabelled = relabel_trace_distillation_graphs(
            [data],
            solver_stats,
            label_config=TraceLabelConfig(
                low_lbd_weight=1.0,
                useful_decision_weight=0.0,
                conflict_rank_weight=0.0,
                propagation_rank_weight=0.0,
                activity_rank_weight=0.0,
                target_scale=2.0,
            ),
        )

        self.assertEqual(len(relabelled), 1)
        self.assertGreater(
            relabelled[0]["var"].trace_target_y[1, 1].item(),
            relabelled[0]["var"].trace_target_y[0, 1].item(),
        )
        self.assertGreater(relabelled[0]["var"].trace_confidence[1].item(), 0.0)

    def test_train_trace_distillation_epoch_updates_adapter_only(self):
        model = GNN(
            channels=4,
            lit_feat_dim=1,
            cls_feat_dim=1,
            num_layers=1,
            out_dim=2,
            var_state_dim=EVENT_VAR_STATE_DIM,
            event_adapter_enabled=True,
            event_adapter_hidden_dim=8,
        )
        freeze_non_adapter_parameters(model)
        data = make_cached_adapter_graph(num_vars=2)
        data["var"].trace_target_y = torch.tensor([[0.0, 2.0], [0.0, -1.0]], dtype=torch.float32)
        data["var"].trace_confidence = torch.ones(2, dtype=torch.float32)
        loader = DataLoader([data], batch_size=1)
        optimizer = torch.optim.AdamW(
            [param for param in model.parameters() if param.requires_grad],
            lr=1e-2,
        )
        before = [param.detach().clone() for param in model.event_adapter.parameters()]

        metrics = train_trace_distillation_epoch(model, loader, optimizer, device="cpu")

        after = [param.detach().clone() for param in model.event_adapter.parameters()]
        self.assertGreater(metrics["loss"], 0.0)
        self.assertTrue(any(not torch.allclose(old, new) for old, new in zip(before, after)))
        self.assertTrue(all(not param.requires_grad for name, param in model.named_parameters() if "event_adapter" not in name))

    def test_tiny_negative_guard_batch_can_reduce_loss(self):
        pred = torch.nn.Parameter(torch.tensor([[0.0, 2.0], [0.0, -2.0]], dtype=torch.float32))
        target = pred.detach().clone()
        confidence = torch.ones(2, dtype=torch.float32)
        base_y = torch.zeros((2, 2), dtype=torch.float32)
        valid_orbit_mask = torch.zeros(2, dtype=torch.bool)
        optimizer = torch.optim.SGD([pred], lr=0.1)

        def compute_loss():
            return trace_distillation_loss(
                pred,
                target,
                confidence,
                base_y=base_y,
                valid_orbit_mask=valid_orbit_mask,
                config=TraceLabelConfig(
                    negative_guard_weight=1.0,
                    negative_guard_mu_loss_weight=1.0,
                ),
            )

        before = compute_loss().detach()
        optimizer.zero_grad()
        compute_loss().backward()
        optimizer.step()
        after = compute_loss().detach()

        self.assertLess(after.item(), before.item())


if __name__ == "__main__":
    unittest.main()
