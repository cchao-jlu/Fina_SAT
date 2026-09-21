from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import torch
from torch import Tensor


DEFAULT_SELECTOR_FEATURES = [
    "base_rho_mean",
    "base_mu_abs_mean",
    "base_mu_std",
    "delta_mu_abs_mean",
    "event_gate_mean",
    "event_conf_learnt_log_mean",
    "event_conf_learnt_rate_mean",
    "event_conf_learnt_rank_mean",
]


@dataclass
class LinearSelector:
    feature_names: list[str]
    weights: list[float]
    bias: float
    threshold: float
    feature_mean: list[float]
    feature_std: list[float]


def fit_linear_selector(
    features: Tensor,
    labels: Tensor,
    feature_names: list[str],
    epochs: int = 1000,
    lr: float = 0.1,
    l2: float = 1.0e-3,
) -> tuple[LinearSelector, Tensor]:
    """Fit a small logistic selector over graph-level adapter features."""
    features = features.to(dtype=torch.float32)
    labels = labels.to(dtype=torch.float32).view(-1)
    if features.dim() != 2:
        raise ValueError(f"Expected features with shape [n, d], got {tuple(features.shape)}")
    if features.shape[0] != labels.numel():
        raise ValueError("features and labels must have the same number of rows")
    if features.shape[1] != len(feature_names):
        raise ValueError("feature_names length must match feature dimension")

    mean = features.mean(dim=0)
    std = features.std(dim=0, unbiased=False).clamp_min(1.0e-6)
    x = (features - mean) / std

    weights = torch.zeros(features.shape[1], dtype=torch.float32, requires_grad=True)
    bias = torch.zeros((), dtype=torch.float32, requires_grad=True)
    optimizer = torch.optim.AdamW([weights, bias], lr=lr, weight_decay=0.0)
    pos_weight = ((labels.numel() - labels.sum()) / labels.sum().clamp_min(1.0)).clamp_min(1.0)

    for _ in range(int(epochs)):
        optimizer.zero_grad(set_to_none=True)
        logits = x.matmul(weights) + bias
        loss = torch.nn.functional.binary_cross_entropy_with_logits(
            logits,
            labels,
            pos_weight=pos_weight,
        )
        if l2 > 0:
            loss = loss + float(l2) * weights.pow(2).mean()
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        probs = torch.sigmoid(x.matmul(weights) + bias)
    selector = LinearSelector(
        feature_names=list(feature_names),
        weights=[float(value) for value in weights.detach().tolist()],
        bias=float(bias.detach().item()),
        threshold=0.5,
        feature_mean=[float(value) for value in mean.tolist()],
        feature_std=[float(value) for value in std.tolist()],
    )
    return selector, probs


def selected_time(
    base_time: Tensor,
    adapter_time: Tensor,
    probabilities: Tensor,
    threshold: float,
) -> Tensor:
    use_adapter = probabilities >= float(threshold)
    return torch.where(use_adapter, adapter_time, base_time)


def choose_threshold_for_time(
    base_time: Tensor,
    adapter_time: Tensor,
    probabilities: Tensor,
) -> tuple[float, float]:
    """Choose the probability threshold that minimizes mean selected runtime."""
    base_time = base_time.to(dtype=torch.float32)
    adapter_time = adapter_time.to(dtype=torch.float32)
    probabilities = probabilities.to(dtype=torch.float32)
    candidates = torch.unique(probabilities).tolist()
    candidates.extend([0.0, 0.5, 1.0])
    best_threshold = 0.5
    best_time = float("inf")
    for threshold in sorted(float(value) for value in candidates):
        mean_time = float(selected_time(base_time, adapter_time, probabilities, threshold).mean().item())
        if mean_time < best_time:
            best_time = mean_time
            best_threshold = threshold
    return best_threshold, best_time


def selector_training_frame(
    feature_frame: pd.DataFrame,
    base_eval: pd.DataFrame,
    adapter_eval: pd.DataFrame,
    label_margin: float = 0.0,
) -> pd.DataFrame:
    """Join extracted selector features with baseline/adapter runtimes."""
    required = {"cnf_id", "time"}
    for name, frame in [("base_eval", base_eval), ("adapter_eval", adapter_eval)]:
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{name} missing required columns: {sorted(missing)}")
    merged = (
        feature_frame
        .merge(base_eval[["cnf_id", "time"]].rename(columns={"time": "base_time"}), on="cnf_id")
        .merge(adapter_eval[["cnf_id", "time"]].rename(columns={"time": "adapter_time"}), on="cnf_id")
    )
    merged["gain"] = merged["base_time"] - merged["adapter_time"]
    merged["label"] = (merged["gain"] > float(label_margin)).astype("float32")
    return merged
