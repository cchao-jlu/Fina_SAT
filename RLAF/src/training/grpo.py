import time

import numpy as np
import pandas as pd
import torch
from torch import Tensor
from torch_geometric.loader import DataLoader

import wandb
from src.model.model import GNN
import src.policy.policy as policy


def get_grpo_advantage(
        solver_stats: pd.DataFrame,
        target_stat: str = "decisions",
) -> np.ndarray:
    values = pd.to_numeric(solver_stats[target_stat], errors="coerce")
    finite = np.isfinite(values.to_numpy(dtype=np.float64))
    max_cost = values[finite].max() if finite.any() else 0.0
    solver_stats[target_stat] = values.replace([np.inf, -np.inf], np.nan).fillna(max_cost)

    grouped = solver_stats[["cnf_id", target_stat]].groupby("cnf_id")

    mean = grouped.mean()
    target_mean = mean.loc[solver_stats["cnf_id"]]
    target_mean = target_mean[target_stat].to_numpy()

    std = grouped.std()
    target_std = std.loc[solver_stats["cnf_id"]]
    target_std = target_std[target_stat].to_numpy()

    target_val = solver_stats[target_stat].to_numpy()

    eps = 1e-8
    advantage = - (target_val - target_mean) / (target_std + eps)
    return np.nan_to_num(advantage, nan=0.0, posinf=0.0, neginf=0.0)


def objective(
        log_prob: Tensor,
        log_prob_ref: Tensor,
        advantage: Tensor,
        clip_ratio: float = 0.2
) -> tuple[Tensor, Tensor]:
    g = advantage.clone()
    g[advantage >= 0.0] *= 1 + clip_ratio
    g[advantage < 0.0] *= 1 - clip_ratio

    log_ratio = (log_prob - log_prob_ref).clamp(-20.0, 20.0)
    prob_ratio = torch.exp(log_ratio)
    L = torch.minimum(prob_ratio * advantage, g)

    return L.mean(), prob_ratio


def train_grpo(
        model: GNN,
        loader: DataLoader,
        optim: torch.optim.Optimizer,
        sched: torch.optim.lr_scheduler.LRScheduler,
        steps: int,
        clip_ratio: float = 0.2,
        kl_penalty: float = 1.0,
        global_step: int = 0,
        scale_sigma: float = 0.1,
        device: torch.device | str = "cpu",
        use_amp: bool = True,
) -> int:
    scaler = torch.amp.GradScaler() if use_amp else None
    model.to(device)
    model.train()
    trainable_params = [param for param in model.parameters() if param.requires_grad]
    steps = int(steps)
    if steps <= 0:
        raise ValueError("GRPO training requires steps > 0")
    if not trainable_params:
        raise ValueError("GRPO training has no trainable parameters")

    L_all = []
    prob_ratio_all = []
    kl_div_all = []
    entropy_all = []
    num_steps = 0

    start_time = time.time()
    while num_steps < steps:
        for data in loader:
            if num_steps >= steps:
                break
            with torch.amp.autocast(device_type="cuda", enabled=use_amp):
                optim.zero_grad()
                data.to(device)
                y_var = model(data)

            with torch.amp.autocast(device_type="cuda", enabled=False):
                y_var = y_var.float()
                y_var = torch.nan_to_num(y_var, nan=0.0, posinf=8.0, neginf=-8.0)
                var_params = data["var"].var_params.transpose(0, 1).float()
                var_params = torch.nan_to_num(var_params, nan=1.0, posinf=1.0e3, neginf=1.0e-6)
                var_params[:, :, 1].clamp_(min=1.0e-6, max=1.0e3)
                log_prob_ref = data.log_prob.transpose(0, 1).float()
                log_prob_ref = torch.nan_to_num(log_prob_ref, nan=0.0, posinf=0.0, neginf=0.0)
                y_var_ref = data["var"].y_var_ref.float()
                y_var_ref = torch.nan_to_num(y_var_ref, nan=0.0, posinf=8.0, neginf=-8.0)
                advantage = data.stats.transpose(0, 1).float()
                advantage = torch.nan_to_num(advantage, nan=0.0, posinf=0.0, neginf=0.0).clamp(-10.0, 10.0)
                var_batch = data["lit"].batch[0::2]

                log_prob = policy.log_prob(y_var, var_params, var_batch, scale_sigma=scale_sigma)
                L, prob_ratio = objective(log_prob, log_prob_ref, advantage, clip_ratio)

                kl_div = policy.kl_div(y_var, y_var_ref, var_batch, scale_sigma=scale_sigma)

                kl_div_mean = kl_div.mean()
                if not torch.isfinite(kl_div_mean):
                    kl_div_mean = torch.zeros((), dtype=L.dtype, device=L.device)
                kl_div_all.append(kl_div_mean.item())
                L_total = L - kl_penalty * kl_div_mean
                if not torch.isfinite(L_total):
                    continue

                entropy = policy.entropy(y_var, var_batch, scale_sigma=scale_sigma)
                if not torch.isfinite(entropy):
                    entropy = torch.zeros((), dtype=L.dtype, device=L.device)
                entropy_all.append(entropy.item())

                if use_amp:
                    scaler.scale(L_total).backward()
                    scaler.unscale_(optim)
                    grad_norm = torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
                    if not torch.isfinite(grad_norm):
                        optim.zero_grad(set_to_none=True)
                        scaler.update()
                        continue
                    scaler.step(optim)
                    scaler.update()
                else:
                    L_total.backward()
                    grad_norm = torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
                    if not torch.isfinite(grad_norm):
                        optim.zero_grad(set_to_none=True)
                        continue
                    optim.step()

                L_all.append(L.item())
                prob_ratio_all.append(prob_ratio.detach().cpu().numpy().reshape(-1))

                global_step += 1
                num_steps += 1

    metrics = {
        "train/L": np.mean(L_all),
        "train/prob_ratio": wandb.Histogram(np.concatenate(prob_ratio_all)),
        "train/lr": sched.get_last_lr()[0],
        "train/kl_div": np.mean(kl_div_all),
        "train/entropy": np.mean(entropy_all),
    }
    wandb.log(metrics, step=global_step)

    end_time = time.time()
    print(f"Optimized model for {num_steps} steps ({end_time - start_time:.2f} seconds)")

    sched.step()
    return global_step
