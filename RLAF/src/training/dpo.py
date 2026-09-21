import time

import numpy as np
import torch
from torch.nn import functional as F
from torch_geometric.loader import DataLoader

import wandb
from src.model.model import GNN
import src.policy.policy as policy


def train_dpo(
        model: GNN,
        loader: DataLoader,
        optim: torch.optim.Optimizer,
        sched: torch.optim.lr_scheduler.LRScheduler,
        steps: int,
        beta: float = 1.0,
        kl_penalty: float = 1.0,
        global_step: int = 0,
        scale_sigma: float = 0.1,
        device: torch.device | str = "cpu",
        use_amp: bool = True,
) -> int:
    scaler = torch.amp.GradScaler() if use_amp else None
    model.to(device)
    model.train()
    steps = int(steps)
    if steps <= 0:
        raise ValueError("DPO training requires steps > 0")

    L_all = []
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
                var_batch = data["lit"].batch[0::2]

                log_prob = policy.log_prob(y_var, var_params, var_batch, scale_sigma=scale_sigma)

                log_prob_ratio = log_prob - log_prob_ref
                log_prob_ratio = log_prob_ratio.transpose(0, 1)
                B, N = log_prob_ratio.shape
                score = log_prob_ratio[:, 1:].view(B, N-1, 1) - log_prob_ratio[:, :-1].view(B, 1, N-1)

                tril_idx = torch.tril_indices(N-1, N-1, device=log_prob.device)
                score = score[:, tril_idx[0], tril_idx[1]]

                L = F.logsigmoid(beta * score).mean()

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
                    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    if not torch.isfinite(grad_norm):
                        optim.zero_grad(set_to_none=True)
                        scaler.update()
                        continue
                    scaler.step(optim)
                    scaler.update()
                else:
                    L_total.backward()
                    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    if not torch.isfinite(grad_norm):
                        optim.zero_grad(set_to_none=True)
                        continue
                    optim.step()

                L_all.append(L.item())

                global_step += 1
                num_steps += 1

    metrics = {
        "train/L": np.mean(L_all),
        "train/lr": sched.get_last_lr()[0],
        "train/kl_div": np.mean(kl_div_all),
        "train/entropy": np.mean(entropy_all),
    }
    wandb.log(metrics, step=global_step)

    end_time = time.time()
    print(f"Optimized model for {num_steps} steps ({end_time - start_time:.2f} seconds)")

    sched.step()
    return global_step
