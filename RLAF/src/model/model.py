import os

import torch
import torch.nn as nn
from torch import Tensor
from torch_geometric.data import HeteroData
from omegaconf import DictConfig, OmegaConf

from src.data.transform import AddNodeFeatures
from src.model.modules import GNNLayer, FeatureEncoder, SinusoidalNumericalEncoder


class GNN(nn.Module):

    def __init__(
            self,
            channels: int,
            lit_feat_dim: int,
            cls_feat_dim: int,
            num_layers: int,
            out_dim: int = 2,
            global_state_dim: int = 0,
            aggr: str | list[str] = "mean",
            feature_encoder: str = "mlp",
            dropout: float = 0.0,
            var_output: bool = True,
            separate_encoders: bool = False,
            var_state_dim: int = 0,
            orbit_feature_dim: int = 0,
            orbit_event_state_dim: int = 0,
            event_adapter_enabled: bool = False,
            event_adapter_hidden_dim: int = 128,
            event_adapter_fusion: str = "residual",
            event_adapter_delta_scale: float = 1.0,
            event_adapter_delta_clip: float | None = None,
            event_adapter_gate_indices: list[int] | None = None,
            event_adapter_graph_gate_indices: list[int] | None = None,
            event_adapter_graph_gate_threshold: float | None = None,
            event_adapter_base_rho_gate_threshold: float | None = None,
            event_adapter_selector_mode: str = "linear",
            event_adapter_selector_feature_names: list[str] | None = None,
            event_adapter_selector_weights: list[float] | None = None,
            event_adapter_selector_bias: float = 0.0,
            event_adapter_selector_threshold: float = 0.5,
            event_adapter_selector_feature_mean: list[float] | None = None,
            event_adapter_selector_feature_std: list[float] | None = None,
            event_adapter_risk_selector_feature_names: list[str] | None = None,
            event_adapter_risk_selector_weights: list[float] | None = None,
            event_adapter_risk_selector_threshold: float = 0.5,
            event_adapter_risk_selector_feature_mean: list[float] | None = None,
            event_adapter_risk_selector_feature_std: list[float] | None = None,
            event_adapter_risk_selector_mlp_weights: list | None = None,
            event_adapter_risk_selector_mlp_biases: list | None = None,
            event_adapter_recovery_selector_feature_names: list[str] | None = None,
            event_adapter_recovery_selector_weights: list[float] | None = None,
            event_adapter_recovery_selector_threshold: float = 0.5,
            event_adapter_recovery_selector_feature_mean: list[float] | None = None,
            event_adapter_recovery_selector_feature_std: list[float] | None = None,
            event_adapter_recovery_selector_mlp_weights: list | None = None,
            event_adapter_recovery_selector_mlp_biases: list | None = None,
            event_adapter_slowdown_selector_feature_names: list[str] | None = None,
            event_adapter_slowdown_selector_weights: list[float] | None = None,
            event_adapter_slowdown_selector_threshold: float = 0.5,
            event_adapter_local_reopen_enabled: bool = False,
            event_adapter_local_reopen_feature_names: list[str] | None = None,
            event_adapter_local_reopen_ops: list[str] | None = None,
            event_adapter_local_reopen_values: list[float] | None = None,
            event_adapter_residual_state_dim: int | None = None,
            event_adapter_polarity_gate_indices: list[int] | None = None,
            event_adapter_polarity_gate_bias_init: float = 0.0,
            event_adapter_polarity_gate_min: float = 0.0,
            event_adapter_min_orbit_event_variance: float = 0.0,
            event_adapter_require_valid_orbit: bool = False,
    ):
        """
        A message-passing Graph Neural Network
        :param channels: Hidden model dimension
        :param lit_feat_dim: Dimension of literal node features
        :param cls_feat_dim: Dimension of clause node features
        :param num_layers: Number of message passing layers
        :param out_dim: node-level output dimension
        :param global_state_dim: Optional graph-level solver feedback state dimension.
        :param aggr: Message aggregation function either mean, max, or sum. If a list is provided, than multiple types of aggregation are performed in parallel.
        :param feature_encoder: Type of node feature encoder. Either "mlp" for a simple perceptron or "sin" for a sinusoidal numerical encoder.
        :param dropout: Dropout probability
        :param var_output: If true, the output will be per variable. If false, the output will be per literal, which is useful for our supervised tasks like backbone prediction.
        """
        super(GNN, self).__init__()
        self.channels = channels
        self.out_dim = int(out_dim)
        self.separate_encoders = separate_encoders
        self.global_state_dim = int(global_state_dim)
        self.var_state_dim = int(var_state_dim)
        self.orbit_feature_dim = int(orbit_feature_dim)
        self.orbit_event_state_dim = int(orbit_event_state_dim)
        self.event_adapter_enabled = bool(event_adapter_enabled)
        self.event_adapter_fusion = str(event_adapter_fusion)
        self.event_adapter_delta_scale = float(event_adapter_delta_scale)
        self.event_adapter_delta_clip = event_adapter_delta_clip
        self.event_adapter_gate_indices = list(event_adapter_gate_indices or [])
        self.event_adapter_graph_gate_indices = list(event_adapter_graph_gate_indices or [])
        self.event_adapter_graph_gate_threshold = event_adapter_graph_gate_threshold
        self.event_adapter_base_rho_gate_threshold = event_adapter_base_rho_gate_threshold
        self.event_adapter_selector_mode = str(event_adapter_selector_mode)
        self.event_adapter_selector_feature_names = list(event_adapter_selector_feature_names or [])
        self.event_adapter_selector_weights = list(event_adapter_selector_weights or [])
        self.event_adapter_selector_bias = float(event_adapter_selector_bias)
        self.event_adapter_selector_threshold = float(event_adapter_selector_threshold)
        self.event_adapter_selector_feature_mean = list(event_adapter_selector_feature_mean or [])
        self.event_adapter_selector_feature_std = list(event_adapter_selector_feature_std or [])
        self.event_adapter_risk_selector_feature_names = list(event_adapter_risk_selector_feature_names or [])
        self.event_adapter_risk_selector_weights = list(event_adapter_risk_selector_weights or [])
        self.event_adapter_risk_selector_threshold = float(event_adapter_risk_selector_threshold)
        self.event_adapter_risk_selector_feature_mean = list(event_adapter_risk_selector_feature_mean or [])
        self.event_adapter_risk_selector_feature_std = list(event_adapter_risk_selector_feature_std or [])
        self.event_adapter_risk_selector_mlp_weights = event_adapter_risk_selector_mlp_weights or []
        self.event_adapter_risk_selector_mlp_biases = event_adapter_risk_selector_mlp_biases or []
        self.event_adapter_recovery_selector_feature_names = list(event_adapter_recovery_selector_feature_names or [])
        self.event_adapter_recovery_selector_weights = list(event_adapter_recovery_selector_weights or [])
        self.event_adapter_recovery_selector_threshold = float(event_adapter_recovery_selector_threshold)
        self.event_adapter_recovery_selector_feature_mean = list(event_adapter_recovery_selector_feature_mean or [])
        self.event_adapter_recovery_selector_feature_std = list(event_adapter_recovery_selector_feature_std or [])
        self.event_adapter_recovery_selector_mlp_weights = event_adapter_recovery_selector_mlp_weights or []
        self.event_adapter_recovery_selector_mlp_biases = event_adapter_recovery_selector_mlp_biases or []
        self.event_adapter_slowdown_selector_feature_names = list(event_adapter_slowdown_selector_feature_names or [])
        self.event_adapter_slowdown_selector_weights = list(event_adapter_slowdown_selector_weights or [])
        self.event_adapter_slowdown_selector_threshold = float(event_adapter_slowdown_selector_threshold)
        self.event_adapter_local_reopen_enabled = bool(event_adapter_local_reopen_enabled)
        self.event_adapter_local_reopen_feature_names = list(event_adapter_local_reopen_feature_names or [])
        self.event_adapter_local_reopen_ops = list(event_adapter_local_reopen_ops or [])
        self.event_adapter_local_reopen_values = list(event_adapter_local_reopen_values or [])
        self.event_adapter_residual_state_dim = int(event_adapter_residual_state_dim or self.var_state_dim)
        self.event_adapter_polarity_gate_indices = list(event_adapter_polarity_gate_indices or [])
        self.event_adapter_polarity_gate_bias_init = float(event_adapter_polarity_gate_bias_init)
        self.event_adapter_polarity_gate_min = float(event_adapter_polarity_gate_min)
        self.event_adapter_min_orbit_event_variance = float(event_adapter_min_orbit_event_variance)
        self.event_adapter_require_valid_orbit = bool(event_adapter_require_valid_orbit)

        if self.orbit_feature_dim < 0 or self.orbit_event_state_dim < 0:
            raise ValueError("orbit feature dimensions must be nonnegative")
        if self.event_adapter_min_orbit_event_variance < 0.0:
            raise ValueError("event_adapter_min_orbit_event_variance must be nonnegative")

        if feature_encoder not in {"mlp", "sin"}:
            raise ValueError(f"Unknown feature encoder type {feature_encoder}")
        encoder_cls = FeatureEncoder if feature_encoder == "mlp" else SinusoidalNumericalEncoder

        if not separate_encoders and lit_feat_dim != cls_feat_dim:
            raise ValueError("Shared literal/clause encoder requires matching feature dimensions")

        self.lit_enc = encoder_cls(
            channels_in=lit_feat_dim,
            channels_out=channels,
            dropout=dropout,
        )
        if separate_encoders:
            self.cls_enc = encoder_cls(
                channels_in=cls_feat_dim,
                channels_out=channels,
                dropout=dropout,
            )
        else:
            self.cls_enc = self.lit_enc

        self.layers = nn.ModuleList([
            GNNLayer(channels=channels, aggr=aggr, dropout=dropout) for _ in range(num_layers)
        ])

        self.var_output = var_output
        if self.var_output:
            # output mlp with last layer initialized with zeros
            self.var_embedding_dim = 2 * channels + self.global_state_dim
            self.out_lin1 = nn.Linear(self.var_embedding_dim, 2 * channels)
            self.out_lin2 = nn.Linear(2 * channels, out_dim)
            nn.init.zeros_(self.out_lin2.weight)
            self.out_act = nn.SiLU(inplace=True)
        else:
            # output mlp with last layer initialized with zeros
            self.var_embedding_dim = channels + self.global_state_dim
            self.out_lin1 = nn.Linear(channels + self.global_state_dim, 2 * channels)
            self.out_lin2 = nn.Linear(2 * channels, out_dim)
            self.out_act = nn.SiLU(inplace=True)

        if self.event_adapter_enabled:
            if not self.var_output:
                raise ValueError("event_adapter requires var_output=True")
            if self.var_state_dim <= 0:
                raise ValueError("event_adapter requires var_state_dim > 0")
            self.event_adapter = nn.Sequential(
                nn.Linear(
                    self.var_embedding_dim
                    + self.var_state_dim
                    + self.orbit_feature_dim
                    + self.orbit_event_state_dim,
                    int(event_adapter_hidden_dim),
                ),
                nn.SiLU(inplace=True),
                nn.Linear(int(event_adapter_hidden_dim), out_dim),
            )
            nn.init.zeros_(self.event_adapter[-1].weight)
            nn.init.zeros_(self.event_adapter[-1].bias)
            polarity_dim = max(len(self.event_adapter_polarity_gate_indices), 1)
            self.event_adapter_polarity_gate = nn.Linear(polarity_dim, 1)
            nn.init.zeros_(self.event_adapter_polarity_gate.weight)
            nn.init.constant_(self.event_adapter_polarity_gate.bias, self.event_adapter_polarity_gate_bias_init)

    def _get_global_state(self, data: HeteroData, num_graphs: int) -> Tensor | None:
        if self.global_state_dim <= 0:
            return None
        if hasattr(data, "global_state"):
            global_state = data.global_state
            if global_state.dim() == 1:
                if global_state.numel() == num_graphs * self.global_state_dim:
                    global_state = global_state.view(num_graphs, self.global_state_dim)
                elif global_state.numel() == self.global_state_dim:
                    global_state = global_state.unsqueeze(0)
                else:
                    raise ValueError(
                        f"Invalid global_state shape {tuple(global_state.shape)} for "
                        f"{num_graphs} graphs and global_state_dim={self.global_state_dim}"
                    )
            return global_state.to(dtype=torch.float32, device=data["lit"].x.device)
        return torch.zeros(
            (num_graphs, self.global_state_dim),
            dtype=torch.float32,
            device=data["lit"].x.device,
        )

    def _var_batch(self, data: HeteroData, num_vars: int, device: torch.device) -> Tensor:
        if "var" in data.node_types and hasattr(data["var"], "batch"):
            batch = data["var"].batch
        elif hasattr(data["lit"], "batch"):
            batch = data["lit"].batch[0::2]
        else:
            batch = torch.zeros(num_vars, dtype=torch.long, device=device)
        if not isinstance(batch, Tensor):
            raise TypeError("batch must be a tensor")
        if batch.ndim != 1:
            raise ValueError("batch must be one-dimensional")
        if batch.dtype != torch.long:
            raise TypeError("batch must have dtype torch.long")
        if batch.numel() != num_vars:
            raise ValueError(f"batch length must equal num_vars={num_vars}")
        if batch.device != device:
            raise ValueError(f"batch must be on device {device}, got {batch.device}")
        if batch.numel() and bool((batch < 0).any()):
            raise ValueError("batch IDs must be nonnegative")
        if batch.numel():
            unique_ids = torch.unique(batch, sorted=True)
            expected_ids = torch.arange(int(unique_ids[-1].item()) + 1, device=device, dtype=batch.dtype)
            if not torch.equal(unique_ids, expected_ids):
                raise ValueError("batch IDs must be contiguous starting at 0")
        batch_num_graphs = int(batch.max().item()) + 1 if batch.numel() else 1
        if hasattr(data, "num_graphs") and int(data.num_graphs) != batch_num_graphs:
            raise ValueError(
                f"declared num_graphs={int(data.num_graphs)} does not match batch graph count={batch_num_graphs}"
            )
        if "var" in data.node_types and hasattr(data["var"], "ptr"):
            ptr = data["var"].ptr
            if not isinstance(ptr, Tensor) or ptr.ndim != 1:
                raise ValueError("var.ptr must be a one-dimensional tensor")
            if ptr.dtype != torch.long:
                raise TypeError("var.ptr must have dtype torch.long")
            if ptr.device != device:
                raise ValueError(f"var.ptr must be on device {device}, got {ptr.device}")
            counts = torch.bincount(batch.to(dtype=torch.long), minlength=batch_num_graphs)
            expected_ptr = torch.cat(
                [
                    torch.zeros(1, dtype=torch.long, device=device),
                    counts.cumsum(dim=0),
                ]
            )
            if not torch.equal(ptr, expected_ptr):
                raise ValueError("var.ptr must exactly match batch graph segments")
        return batch

    def _compute_base_var_output(self, data: HeteroData) -> tuple[Tensor, Tensor, Tensor, int]:
        x_lit = data["lit"].x
        h_lit = self.lit_enc(x_lit)

        x_cls = data["cls"].x
        h_cls = self.cls_enc(x_cls)

        for layer in self.layers:
            h_lit, h_cls = layer(h_lit, h_cls, data)

        lit_batch = data["lit"].batch
        num_graphs = int(lit_batch.max().item()) + 1 if lit_batch.numel() > 0 else 1
        global_state = self._get_global_state(data, num_graphs=num_graphs)

        if self.var_output:
            # concatenate interleaved embeddings and apply an mlp
            h_var = torch.cat([h_lit[0::2], h_lit[1::2]], dim=1)
            if global_state is not None:
                h_var = torch.cat([h_var, global_state[lit_batch[0::2]]], dim=1)
            y_var = self.out_lin2(self.out_act(self.out_lin1(h_var)))
            var_batch = lit_batch[0::2]
            return y_var, h_var, var_batch, num_graphs
        else:
            if global_state is not None:
                h_lit = torch.cat([h_lit, global_state[lit_batch]], dim=1)
            y_lit = self.out_lin2(self.out_act(self.out_lin1(h_lit)))
            return y_lit, h_lit, lit_batch, num_graphs

    def _event_score(self, var_state: Tensor) -> Tensor:
        if var_state.numel() == 0:
            return torch.zeros(var_state.shape[0], dtype=var_state.dtype, device=var_state.device)
        if var_state.shape[1] >= 14:
            columns = [idx for idx in [12, 13] if idx < var_state.shape[1]]
        else:
            columns = list(range(var_state.shape[1]))
        return var_state[:, columns].clamp_min(0.0).sum(dim=1)

    def _aggregate_by_graph(self, values: Tensor, var_batch: Tensor, num_graphs: int, op: str) -> Tensor:
        out = torch.zeros(num_graphs, dtype=values.dtype, device=values.device)
        for graph_id in range(num_graphs):
            mask = var_batch == graph_id
            if not bool(mask.any()):
                continue
            graph_values = values[mask]
            if op == "mean":
                out[graph_id] = graph_values.mean()
            elif op == "max":
                out[graph_id] = graph_values.max()
            elif op == "range":
                out[graph_id] = graph_values.max() - graph_values.min()
            elif op == "count_log":
                out[graph_id] = torch.log1p(mask.sum().to(dtype=values.dtype))
            else:
                raise ValueError(f"Unknown graph aggregation {op}")
        return out

    def _event_adapter_selector_feature(
        self,
        name: str,
        base_y: Tensor,
        var_state: Tensor,
        delta: Tensor,
        var_batch: Tensor,
        num_graphs: int,
    ) -> Tensor:
        if name == "num_vars_log":
            return self._aggregate_by_graph(torch.ones_like(var_batch, dtype=base_y.dtype), var_batch, num_graphs, "count_log")
        if name == "base_rho_mean":
            return self._aggregate_by_graph(base_y[:, 0], var_batch, num_graphs, "mean")
        if name == "base_rho_range":
            return self._aggregate_by_graph(base_y[:, 0], var_batch, num_graphs, "range")
        if name == "delta_abs_max":
            return self._aggregate_by_graph(delta.abs().mean(dim=1), var_batch, num_graphs, "max")
        if name == "event_conf_learnt_log_max":
            cols = [idx for idx in [2, 3] if idx < var_state.shape[1]]
            values = var_state[:, cols].max(dim=1).values if cols else torch.zeros(var_state.shape[0], dtype=var_state.dtype, device=var_state.device)
            return self._aggregate_by_graph(values, var_batch, num_graphs, "max")
        if name == "event_gate_mean":
            values = self._event_gate_values(var_state)
            return self._aggregate_by_graph(values, var_batch, num_graphs, "mean")
        if name == "local_reopen_candidate":
            return torch.zeros(num_graphs, dtype=base_y.dtype, device=base_y.device)
        if name in {"event_entropy_norm", "event_top10_mass", "rho_event_corr", "rho_event_top10_overlap"}:
            score = self._event_score(var_state)
            out = torch.zeros(num_graphs, dtype=base_y.dtype, device=base_y.device)
            for graph_id in range(num_graphs):
                mask = var_batch == graph_id
                graph_score = score[mask]
                graph_rho = base_y[mask, 0]
                if graph_score.numel() == 0:
                    continue
                total = graph_score.sum()
                if name == "event_entropy_norm":
                    if total <= 1.0e-9:
                        out[graph_id] = 1.0
                    elif graph_score.numel() <= 1:
                        out[graph_id] = 0.0
                    else:
                        prob = graph_score / total.clamp_min(1.0e-9)
                        entropy = -(prob * torch.log(prob.clamp_min(1.0e-9))).sum()
                        out[graph_id] = entropy / torch.log(torch.tensor(float(graph_score.numel()), dtype=base_y.dtype, device=base_y.device))
                elif name == "event_top10_mass":
                    if total > 1.0e-9:
                        k = max(1, int(0.10 * graph_score.numel()))
                        out[graph_id] = graph_score.topk(k).values.sum() / total
                elif name == "rho_event_corr":
                    if total > 1.0e-9 and graph_score.numel() > 1:
                        rho_centered = graph_rho - graph_rho.mean()
                        score_centered = graph_score - graph_score.mean()
                        denom = rho_centered.norm() * score_centered.norm()
                        if denom > 1.0e-9:
                            out[graph_id] = (rho_centered * score_centered).sum() / denom
                elif name == "rho_event_top10_overlap":
                    if total > 1.0e-9 and graph_score.numel() > 0:
                        k = max(1, int(0.10 * graph_score.numel()))
                        rho_top = set(torch.topk(graph_rho, k).indices.detach().cpu().tolist())
                        event_top = set(torch.topk(graph_score, k).indices.detach().cpu().tolist())
                        out[graph_id] = len(rho_top.intersection(event_top)) / float(k)
            return out
        return torch.zeros(num_graphs, dtype=base_y.dtype, device=base_y.device)

    def _selector_features(
        self,
        feature_names: list[str],
        base_y: Tensor,
        var_state: Tensor,
        delta: Tensor,
        var_batch: Tensor,
        num_graphs: int,
        feature_override: Tensor | None = None,
    ) -> Tensor:
        if feature_override is not None:
            override = feature_override.to(dtype=base_y.dtype, device=base_y.device)
            if override.dim() == 1:
                override = override.view(num_graphs, -1)
            return override
        if not feature_names:
            return torch.zeros((num_graphs, 0), dtype=base_y.dtype, device=base_y.device)
        columns = [
            self._event_adapter_selector_feature(
                name,
                base_y=base_y,
                var_state=var_state,
                delta=delta,
                var_batch=var_batch,
                num_graphs=num_graphs,
            )
            for name in feature_names
        ]
        return torch.stack(columns, dim=1)

    def _feature_override_for_names(self, features: Tensor, names: list[str]) -> Tensor | None:
        if not names:
            return None
        if not self.event_adapter_selector_feature_names:
            return None
        columns = []
        for name in names:
            if name not in self.event_adapter_selector_feature_names:
                return None
            columns.append(self.event_adapter_selector_feature_names.index(name))
        return features[:, columns]

    def _linear_selector_score(
        self,
        features: Tensor,
        weights: list[float],
        bias: float,
        mean: list[float] | None = None,
        std: list[float] | None = None,
    ) -> Tensor:
        if features.shape[1] == 0:
            return torch.zeros(features.shape[0], dtype=features.dtype, device=features.device)
        x = features
        if mean and std and len(mean) == x.shape[1] and len(std) == x.shape[1]:
            mean_t = torch.tensor(mean, dtype=x.dtype, device=x.device).view(1, -1)
            std_t = torch.tensor(std, dtype=x.dtype, device=x.device).view(1, -1).clamp_min(1.0e-6)
            x = (x - mean_t) / std_t
        weight = torch.tensor(weights or [1.0] * x.shape[1], dtype=x.dtype, device=x.device)
        if weight.numel() < x.shape[1]:
            weight = torch.cat([weight, torch.zeros(x.shape[1] - weight.numel(), dtype=x.dtype, device=x.device)])
        return x.matmul(weight[: x.shape[1]]) + float(bias)

    def _mlp_selector_score(self, features: Tensor, weights: list, biases: list) -> Tensor:
        x = features
        if not weights:
            return torch.zeros(features.shape[0], dtype=features.dtype, device=features.device)
        for layer_id, raw_weight in enumerate(weights):
            weight = torch.tensor(raw_weight, dtype=features.dtype, device=features.device)
            bias_values = biases[layer_id] if layer_id < len(biases) else [0.0] * weight.shape[0]
            bias = torch.tensor(bias_values, dtype=features.dtype, device=features.device)
            x = x.matmul(weight.t()) + bias
            if layer_id + 1 < len(weights):
                x = torch.relu(x)
        return x.view(features.shape[0], -1)[:, 0]

    def _event_adapter_local_reopen_mask(self, features: Tensor) -> Tensor:
        if not self.event_adapter_local_reopen_enabled or not self.event_adapter_local_reopen_feature_names:
            return torch.zeros(features.shape[0], dtype=torch.bool, device=features.device)
        feature_names = self.event_adapter_selector_feature_names
        mask = torch.ones(features.shape[0], dtype=torch.bool, device=features.device)
        if "local_reopen_candidate" in feature_names:
            idx = feature_names.index("local_reopen_candidate")
            mask = mask & (features[:, idx] > 0.5)
        for name, op, value in zip(
            self.event_adapter_local_reopen_feature_names,
            self.event_adapter_local_reopen_ops,
            self.event_adapter_local_reopen_values,
        ):
            if name not in feature_names:
                continue
            idx = feature_names.index(name)
            threshold = float(value)
            if op == ">=":
                mask = mask & (features[:, idx] >= threshold)
            elif op == ">":
                mask = mask & (features[:, idx] > threshold)
            elif op == "<=":
                mask = mask & (features[:, idx] <= threshold)
            elif op == "<":
                mask = mask & (features[:, idx] < threshold)
            else:
                raise ValueError(f"Unknown local reopen op {op!r}")
        return mask

    def _event_adapter_selector_gate(
        self,
        base_y: Tensor,
        var_state: Tensor,
        delta: Tensor,
        var_batch: Tensor,
        num_graphs: int,
        feature_override: Tensor | None = None,
    ) -> Tensor:
        if not self.event_adapter_selector_feature_names:
            return torch.ones(num_graphs, dtype=base_y.dtype, device=base_y.device)
        features = self._selector_features(
            self.event_adapter_selector_feature_names,
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=num_graphs,
            feature_override=feature_override,
        )
        if self.event_adapter_selector_mode in {"two_stage", "two_stage_mlp"}:
            risk_features = self._selector_features(
                self.event_adapter_risk_selector_feature_names,
                base_y,
                var_state,
                delta,
                var_batch,
                num_graphs,
                feature_override=self._feature_override_for_names(features, self.event_adapter_risk_selector_feature_names),
            )
            recovery_features = self._selector_features(
                self.event_adapter_recovery_selector_feature_names,
                base_y,
                var_state,
                delta,
                var_batch,
                num_graphs,
                feature_override=self._feature_override_for_names(features, self.event_adapter_recovery_selector_feature_names),
            )
            if self.event_adapter_selector_mode == "two_stage_mlp":
                risk_score = self._mlp_selector_score(risk_features, self.event_adapter_risk_selector_mlp_weights, self.event_adapter_risk_selector_mlp_biases)
                recovery_score = self._mlp_selector_score(recovery_features, self.event_adapter_recovery_selector_mlp_weights, self.event_adapter_recovery_selector_mlp_biases)
            else:
                risk_score = self._linear_selector_score(risk_features, self.event_adapter_risk_selector_weights, 0.0)
                recovery_score = self._linear_selector_score(recovery_features, self.event_adapter_recovery_selector_weights, 0.0)
            risk = torch.sigmoid(risk_score) >= self.event_adapter_risk_selector_threshold
            recovery = torch.sigmoid(recovery_score) >= self.event_adapter_recovery_selector_threshold
            slowdown = torch.zeros(num_graphs, dtype=torch.bool, device=base_y.device)
            if self.event_adapter_slowdown_selector_feature_names:
                slowdown_features = self._selector_features(
                    self.event_adapter_slowdown_selector_feature_names,
                    base_y,
                    var_state,
                    delta,
                    var_batch,
                    num_graphs,
                    feature_override=self._feature_override_for_names(features, self.event_adapter_slowdown_selector_feature_names),
                )
                slowdown_score = self._linear_selector_score(slowdown_features, self.event_adapter_slowdown_selector_weights, 0.0)
                slowdown = torch.sigmoid(slowdown_score) >= self.event_adapter_slowdown_selector_threshold
            gate = recovery & ~risk & ~slowdown
            gate = gate | self._event_adapter_local_reopen_mask(features)
            return gate.to(dtype=base_y.dtype)

        score = self._linear_selector_score(
            features,
            self.event_adapter_selector_weights,
            self.event_adapter_selector_bias,
            self.event_adapter_selector_feature_mean,
            self.event_adapter_selector_feature_std,
        )
        return (torch.sigmoid(score) >= self.event_adapter_selector_threshold).to(dtype=base_y.dtype)

    def _event_gate_values(self, var_state: Tensor) -> Tensor:
        if not self.event_adapter_gate_indices:
            return torch.ones(var_state.shape[0], dtype=var_state.dtype, device=var_state.device)
        indices = [idx for idx in self.event_adapter_gate_indices if idx < var_state.shape[1]]
        if not indices:
            return torch.zeros(var_state.shape[0], dtype=var_state.dtype, device=var_state.device)
        return var_state[:, indices].clamp_min(0.0).max(dim=1).values.clamp(0.0, 1.0)

    def _graph_gate_values(self, base_y: Tensor, var_state: Tensor, var_batch: Tensor, num_graphs: int) -> Tensor:
        graph_gate = torch.ones(num_graphs, dtype=base_y.dtype, device=base_y.device)
        if self.event_adapter_graph_gate_indices and self.event_adapter_graph_gate_threshold is not None:
            indices = [idx for idx in self.event_adapter_graph_gate_indices if idx < var_state.shape[1]]
            values = var_state[:, indices].clamp_min(0.0).max(dim=1).values if indices else torch.zeros(var_state.shape[0], dtype=var_state.dtype, device=base_y.device)
            graph_values = self._aggregate_by_graph(values, var_batch, num_graphs, "mean")
            graph_gate = graph_gate * (graph_values >= float(self.event_adapter_graph_gate_threshold)).to(dtype=base_y.dtype)
        if self.event_adapter_base_rho_gate_threshold is not None:
            rho_mean = self._aggregate_by_graph(base_y[:, 0], var_batch, num_graphs, "mean")
            graph_gate = graph_gate * (rho_mean >= float(self.event_adapter_base_rho_gate_threshold)).to(dtype=base_y.dtype)
        return graph_gate

    def _event_adapter_input_tensor(
        self,
        data: HeteroData,
        name: str,
        expected_dim: int,
        num_vars: int,
        device: torch.device,
        dtype: torch.dtype,
    ) -> tuple[Tensor, Tensor]:
        fallback = (
            torch.zeros((num_vars, max(expected_dim, 0)), dtype=dtype, device=device),
            torch.zeros((num_vars, 1), dtype=dtype, device=device),
        )
        if expected_dim <= 0:
            return (
                torch.zeros((num_vars, 0), dtype=dtype, device=device),
                torch.ones((num_vars, 1), dtype=dtype, device=device),
            )
        if not hasattr(data["var"], name):
            return fallback
        value = getattr(data["var"], name)
        if not isinstance(value, Tensor):
            return fallback
        if value.ndim != 2:
            return fallback
        if value.shape[0] != num_vars:
            return fallback
        if value.shape[1] != expected_dim:
            return fallback
        if not value.is_floating_point():
            return fallback
        if value.device != device:
            return fallback
        if not torch.isfinite(value).all():
            return fallback
        converted = value.to(dtype=dtype)
        if not torch.isfinite(converted).all():
            return fallback
        return converted, torch.ones((num_vars, 1), dtype=dtype, device=device)

    def _event_adapter_orbit_mask(
        self,
        data: HeteroData,
        num_vars: int,
        device: torch.device,
        dtype: torch.dtype,
    ) -> Tensor:
        mask = torch.ones((num_vars, 1), dtype=dtype, device=device)
        if self.event_adapter_require_valid_orbit:
            if not hasattr(data["var"], "valid_orbit_mask"):
                mask.zero_()
            else:
                valid_mask = data["var"].valid_orbit_mask
                if not isinstance(valid_mask, Tensor):
                    return torch.zeros_like(mask)
                if valid_mask.ndim != 1 or valid_mask.shape[0] != num_vars:
                    return torch.zeros_like(mask)
                if valid_mask.dtype != torch.bool:
                    return torch.zeros_like(mask)
                if valid_mask.device != device:
                    return torch.zeros_like(mask)
                mask = mask * valid_mask.to(dtype=dtype).unsqueeze(1)

        if self.event_adapter_min_orbit_event_variance > 0.0:
            if not hasattr(data["var"], "orbit_event_variance"):
                mask.zero_()
            else:
                variance = data["var"].orbit_event_variance
                if not isinstance(variance, Tensor):
                    return torch.zeros_like(mask)
                if variance.ndim == 1:
                    variance = variance.unsqueeze(1)
                if variance.ndim != 2 or variance.shape[0] != num_vars or variance.shape[1] <= 0:
                    return torch.zeros_like(mask)
                if not variance.is_floating_point():
                    return torch.zeros_like(mask)
                if variance.device != device:
                    return torch.zeros_like(mask)
                if not torch.isfinite(variance).all():
                    return torch.zeros_like(mask)
                variance_value = variance.mean(dim=1, keepdim=True)
                mask = mask * (variance_value >= self.event_adapter_min_orbit_event_variance).to(dtype=dtype)
        return mask

    def _apply_event_adapter(self, base_y: Tensor, base_embedding: Tensor, data: HeteroData, var_batch: Tensor, num_graphs: int) -> Tensor:
        num_vars = base_y.shape[0]
        if base_embedding.ndim != 2 or base_embedding.shape[0] != num_vars:
            raise ValueError("base_embedding rows must match base_y rows")
        event_state = data["var"].event_state
        if not isinstance(event_state, Tensor):
            raise TypeError("event_state must be a tensor")
        if event_state.ndim != 2 or event_state.shape[0] != num_vars:
            raise ValueError(f"event_state must have shape [{num_vars}, {self.var_state_dim}]")
        if not event_state.is_floating_point():
            raise TypeError("event_state must have a floating dtype")
        adapter_dtype = self.event_adapter[0].weight.dtype
        if event_state.dtype != adapter_dtype:
            raise TypeError(f"event_state dtype must match event_adapter dtype {adapter_dtype}")
        if event_state.device != base_y.device:
            raise ValueError(f"event_state must be on device {base_y.device}, got {event_state.device}")
        if not torch.isfinite(event_state).all():
            raise ValueError("event_state contains nonfinite values")
        var_state = event_state
        if var_state.shape[1] != self.var_state_dim:
            raise ValueError(f"event adapter expected var_state_dim={self.var_state_dim}, got {var_state.shape[1]}")
        orbit_features, orbit_feature_mask = self._event_adapter_input_tensor(
            data, "orbit_features", self.orbit_feature_dim, num_vars, base_y.device, adapter_dtype
        )
        orbit_event_state, orbit_event_state_mask = self._event_adapter_input_tensor(
            data, "orbit_event_state", self.orbit_event_state_dim, num_vars, base_y.device, adapter_dtype
        )
        evidence_mask = orbit_feature_mask * orbit_event_state_mask
        evidence_mask = evidence_mask * self._event_adapter_orbit_mask(
            data, num_vars, base_y.device, adapter_dtype
        )
        delta = self.event_adapter(
            torch.cat([base_embedding, var_state, orbit_features, orbit_event_state], dim=1)
        )
        if self.event_adapter_delta_clip is not None:
            delta = delta.clamp(-abs(float(self.event_adapter_delta_clip)), abs(float(self.event_adapter_delta_clip)))
        delta = delta * self.event_adapter_delta_scale

        var_gate = self._event_gate_values(var_state).view(-1, 1)
        graph_gate = self._graph_gate_values(base_y, var_state, var_batch, num_graphs)
        selector_override = getattr(data, "event_adapter_selector_features", None)
        selector_gate = self._event_adapter_selector_gate(
            base_y=base_y,
            var_state=var_state,
            delta=delta,
            var_batch=var_batch,
            num_graphs=num_graphs,
            feature_override=selector_override,
        )
        graph_gate = graph_gate * selector_gate
        delta = delta * var_gate * graph_gate[var_batch].view(-1, 1)

        if self.event_adapter_fusion == "weight_only_residual":
            weight_delta = torch.zeros_like(delta)
            if delta.shape[1] > 1:
                weight_delta[:, 1:2] = delta[:, 1:2]
            delta = weight_delta
        elif self.event_adapter_fusion == "polarity_gated_residual":
            polarity_delta = torch.zeros_like(delta)
            if delta.shape[1] > 1:
                if self.event_adapter_polarity_gate_indices:
                    indices = [idx for idx in self.event_adapter_polarity_gate_indices if idx < var_state.shape[1]]
                    evidence = var_state[:, indices].clamp(0.0, 1.0).mean(dim=1, keepdim=True) if indices else torch.zeros((var_state.shape[0], 1), dtype=delta.dtype, device=base_y.device)
                else:
                    evidence = torch.zeros((var_state.shape[0], 1), dtype=delta.dtype, device=base_y.device)
                gate = self.event_adapter_polarity_gate_min + (1.0 - self.event_adapter_polarity_gate_min) * 0.5 * evidence
                polarity_delta[:, 1:2] = delta[:, 1:2] * gate
            delta = polarity_delta
        elif self.event_adapter_fusion not in {"residual", "sbe"}:
            raise ValueError(f"Unknown event adapter fusion {self.event_adapter_fusion!r}")
        delta = delta * evidence_mask
        if self.event_adapter_delta_clip is not None:
            delta = delta.clamp(-abs(float(self.event_adapter_delta_clip)), abs(float(self.event_adapter_delta_clip)))
        return base_y + delta

    def forward(self, data: HeteroData, return_cache: bool = False) -> Tensor | tuple[Tensor, dict[str, Tensor]]:
        if self.event_adapter_enabled and "var" in data.node_types and hasattr(data["var"], "base_embedding") and hasattr(data["var"], "base_y") and hasattr(data["var"], "event_state"):
            cached_base_y = data["var"].base_y
            cached_base_embedding = data["var"].base_embedding
            if not isinstance(cached_base_y, Tensor) or cached_base_y.ndim != 2:
                raise ValueError("base_y must be a two-dimensional tensor")
            if not cached_base_y.is_floating_point():
                raise TypeError("base_y must have a floating dtype")
            if cached_base_y.shape[1] != self.out_dim:
                raise ValueError(f"base_y expected dim={self.out_dim}, got {cached_base_y.shape[1]}")
            if not torch.isfinite(cached_base_y).all():
                raise ValueError("base_y contains nonfinite values")
            num_vars = cached_base_y.shape[0]
            if "num_nodes" in data["var"] and int(data["var"].num_nodes) != num_vars:
                raise ValueError(
                    f"var.num_nodes={int(data['var'].num_nodes)} does not match cache rows={num_vars}"
                )
            if not isinstance(cached_base_embedding, Tensor) or cached_base_embedding.ndim != 2:
                raise ValueError("base_embedding must be a two-dimensional tensor")
            if cached_base_embedding.shape[0] != num_vars:
                raise ValueError("base_embedding rows must match base_y rows")
            if cached_base_embedding.shape[1] != self.var_embedding_dim:
                raise ValueError(
                    f"base_embedding expected dim={self.var_embedding_dim}, got {cached_base_embedding.shape[1]}"
                )
            if not cached_base_embedding.is_floating_point():
                raise TypeError("base_embedding must have a floating dtype")
            adapter_parameter = self.event_adapter[0].weight
            if cached_base_y.dtype != adapter_parameter.dtype:
                raise TypeError(
                    f"base_y dtype must match event_adapter dtype {adapter_parameter.dtype}"
                )
            if cached_base_embedding.dtype != adapter_parameter.dtype:
                raise TypeError(
                    f"base_embedding dtype must match event_adapter dtype {adapter_parameter.dtype}"
                )
            if cached_base_y.device != adapter_parameter.device:
                raise ValueError(
                    f"base_y must be on event_adapter device {adapter_parameter.device}, got {cached_base_y.device}"
                )
            if cached_base_embedding.device != cached_base_y.device:
                raise ValueError(
                    f"base_embedding must be on device {cached_base_y.device}, got {cached_base_embedding.device}"
                )
            if not torch.isfinite(cached_base_embedding).all():
                raise ValueError("base_embedding contains nonfinite values")
            event_state = data["var"].event_state
            if isinstance(event_state, Tensor) and event_state.ndim == 2 and event_state.shape[0] != num_vars:
                raise ValueError(f"event_state rows must equal num_vars={num_vars}")
            base_y = cached_base_y
            base_embedding = cached_base_embedding
            var_batch = self._var_batch(data, num_vars, base_y.device)
            num_graphs = int(var_batch.max().item()) + 1 if var_batch.numel() > 0 else 1
            y_var = self._apply_event_adapter(base_y, base_embedding, data, var_batch, num_graphs)
            if return_cache:
                return y_var, {"base_embedding": base_embedding, "base_y": base_y}
            return y_var

        y, embedding, batch, num_graphs = self._compute_base_var_output(data)
        base_y = y
        if self.event_adapter_enabled and self.var_output and "var" in data.node_types and hasattr(data["var"], "event_state"):
            y = self._apply_event_adapter(y, embedding, data, batch, num_graphs)
        if return_cache:
            return y, {"base_embedding": embedding, "base_y": base_y}
        return y


def init_transform(cfg: DictConfig | None = None) -> AddNodeFeatures:
    feature_set = "legacy"
    if cfg is not None and "model" in cfg and "feature_set" in cfg.model:
        feature_set = cfg.model.feature_set
    return AddNodeFeatures(feature_set=feature_set)


def init_model(cfg: DictConfig, transform: AddNodeFeatures, **model_kwargs) -> GNN:
    var_output = model_kwargs.get("var_output", True)
    if "out_dim" not in model_kwargs:
        if var_output:
            learnable_sigma = bool(cfg.model.learnable_sigma) if "learnable_sigma" in cfg.model else False
            model_kwargs["out_dim"] = 3 if learnable_sigma else 2
        else:
            model_kwargs["out_dim"] = 1

    def cfg_value(section, key: str, default=None):
        return section[key] if section is not None and key in section else default

    adapter_cfg = cfg.model.event_adapter if "event_adapter" in cfg.model else None
    adapter_kwargs = {}
    if "var_state_dim" in cfg.model:
        adapter_kwargs["var_state_dim"] = int(cfg.model.var_state_dim)
    if "orbit_feature_dim" in cfg.model:
        adapter_kwargs["orbit_feature_dim"] = int(cfg.model.orbit_feature_dim)
    if "orbit_event_state_dim" in cfg.model:
        adapter_kwargs["orbit_event_state_dim"] = int(cfg.model.orbit_event_state_dim)
    if adapter_cfg is not None:
        adapter_kwargs.update(
            {
                "orbit_feature_dim": int(cfg_value(adapter_cfg, "orbit_feature_dim", adapter_kwargs.get("orbit_feature_dim", 0))),
                "orbit_event_state_dim": int(cfg_value(adapter_cfg, "orbit_event_state_dim", adapter_kwargs.get("orbit_event_state_dim", 0))),
                "event_adapter_enabled": bool(cfg_value(adapter_cfg, "enabled", False)),
                "event_adapter_hidden_dim": int(cfg_value(adapter_cfg, "hidden_dim", 128)),
                "event_adapter_fusion": str(cfg_value(adapter_cfg, "fusion", "residual")),
                "event_adapter_delta_scale": float(cfg_value(adapter_cfg, "delta_scale", 1.0)),
                "event_adapter_delta_clip": cfg_value(adapter_cfg, "delta_clip", None),
                "event_adapter_gate_indices": cfg_value(adapter_cfg, "gate_indices", None),
                "event_adapter_graph_gate_indices": cfg_value(adapter_cfg, "graph_gate_indices", None),
                "event_adapter_graph_gate_threshold": cfg_value(adapter_cfg, "graph_gate_threshold", None),
                "event_adapter_base_rho_gate_threshold": cfg_value(adapter_cfg, "base_rho_gate_threshold", None),
                "event_adapter_selector_mode": str(cfg_value(adapter_cfg, "selector_mode", "linear")),
                "event_adapter_selector_feature_names": cfg_value(adapter_cfg, "selector_feature_names", None),
                "event_adapter_selector_weights": cfg_value(adapter_cfg, "selector_weights", None),
                "event_adapter_selector_bias": float(cfg_value(adapter_cfg, "selector_bias", 0.0)),
                "event_adapter_selector_threshold": float(cfg_value(adapter_cfg, "selector_threshold", 0.5)),
                "event_adapter_selector_feature_mean": cfg_value(adapter_cfg, "selector_feature_mean", None),
                "event_adapter_selector_feature_std": cfg_value(adapter_cfg, "selector_feature_std", None),
                "event_adapter_risk_selector_feature_names": cfg_value(adapter_cfg, "risk_selector_feature_names", None),
                "event_adapter_risk_selector_weights": cfg_value(adapter_cfg, "risk_selector_weights", None),
                "event_adapter_risk_selector_threshold": float(cfg_value(adapter_cfg, "risk_selector_threshold", 0.5)),
                "event_adapter_risk_selector_feature_mean": cfg_value(adapter_cfg, "risk_selector_feature_mean", None),
                "event_adapter_risk_selector_feature_std": cfg_value(adapter_cfg, "risk_selector_feature_std", None),
                "event_adapter_risk_selector_mlp_weights": cfg_value(adapter_cfg, "risk_selector_mlp_weights", None),
                "event_adapter_risk_selector_mlp_biases": cfg_value(adapter_cfg, "risk_selector_mlp_biases", None),
                "event_adapter_recovery_selector_feature_names": cfg_value(adapter_cfg, "recovery_selector_feature_names", None),
                "event_adapter_recovery_selector_weights": cfg_value(adapter_cfg, "recovery_selector_weights", None),
                "event_adapter_recovery_selector_threshold": float(cfg_value(adapter_cfg, "recovery_selector_threshold", 0.5)),
                "event_adapter_recovery_selector_feature_mean": cfg_value(adapter_cfg, "recovery_selector_feature_mean", None),
                "event_adapter_recovery_selector_feature_std": cfg_value(adapter_cfg, "recovery_selector_feature_std", None),
                "event_adapter_recovery_selector_mlp_weights": cfg_value(adapter_cfg, "recovery_selector_mlp_weights", None),
                "event_adapter_recovery_selector_mlp_biases": cfg_value(adapter_cfg, "recovery_selector_mlp_biases", None),
                "event_adapter_slowdown_selector_feature_names": cfg_value(adapter_cfg, "slowdown_selector_feature_names", None),
                "event_adapter_slowdown_selector_weights": cfg_value(adapter_cfg, "slowdown_selector_weights", None),
                "event_adapter_slowdown_selector_threshold": float(cfg_value(adapter_cfg, "slowdown_selector_threshold", 0.5)),
                "event_adapter_local_reopen_enabled": bool(cfg_value(adapter_cfg, "local_reopen_enabled", False)),
                "event_adapter_local_reopen_feature_names": cfg_value(adapter_cfg, "local_reopen_feature_names", None),
                "event_adapter_local_reopen_ops": cfg_value(adapter_cfg, "local_reopen_ops", None),
                "event_adapter_local_reopen_values": cfg_value(adapter_cfg, "local_reopen_values", None),
                "event_adapter_residual_state_dim": cfg_value(adapter_cfg, "residual_state_dim", None),
                "event_adapter_polarity_gate_indices": cfg_value(adapter_cfg, "polarity_gate_indices", None),
                "event_adapter_polarity_gate_bias_init": float(cfg_value(adapter_cfg, "polarity_gate_bias_init", 0.0)),
                "event_adapter_polarity_gate_min": float(cfg_value(adapter_cfg, "polarity_gate_min", 0.0)),
                "event_adapter_min_orbit_event_variance": float(cfg_value(adapter_cfg, "min_orbit_event_variance", 0.0)),
                "event_adapter_require_valid_orbit": bool(cfg_value(adapter_cfg, "require_valid_orbit", False)),
            }
        )

    model = GNN(
        channels=cfg.model.channels,
        lit_feat_dim=transform.lit_dim(),
        cls_feat_dim=transform.cls_dim(),
        num_layers=cfg.model.num_layers,
        global_state_dim=int(cfg.model.global_state_dim) if "global_state_dim" in cfg.model else 0,
        aggr=OmegaConf.to_container(cfg.model.aggr),
        feature_encoder=cfg.model.feature_encoder,
        dropout=cfg.model.dropout if "dropout" in cfg.model else 0.0,
        separate_encoders=bool(cfg.model.separate_encoders) if "separate_encoders" in cfg.model else False,
        **adapter_kwargs,
        **model_kwargs,
    )
    return model


def load_checkpoint(ckpt_path: str, **model_kwargs) -> tuple[GNN, AddNodeFeatures, DictConfig]:
    cfg_path = os.path.join(os.path.dirname(ckpt_path), "config.yaml")
    cfg = OmegaConf.load(cfg_path)

    transform = init_transform(cfg)

    model = init_model(cfg, transform, **model_kwargs)

    state_dict = torch.load(ckpt_path, map_location="cpu")
    model.load_state_dict(state_dict)
    return model, transform, cfg
