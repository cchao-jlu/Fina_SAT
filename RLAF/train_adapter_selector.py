import argparse
import os
import shutil

import pandas as pd
import torch
from omegaconf import OmegaConf
from torch_geometric.loader import DataLoader

from src.data.dataset import DimacsCNFDataset
from src.model.model import load_checkpoint
from src.policy.evaluate import compute_solver_stats, sample_var_params
from src.solving.budget import apply_rollout_budget
from src.solving.state import attach_var_event_state_batch
from src.training.adapter_selector import (
    DEFAULT_SELECTOR_FEATURES,
    choose_threshold_for_time,
    fit_linear_selector,
    selector_training_frame,
    selected_time,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a lightweight graph-level adapter selector.")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--dataset", action="append", required=True)
    parser.add_argument("--base-eval-csv", action="append", required=True)
    parser.add_argument("--adapter-eval-csv", action="append", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--features", default=",".join(DEFAULT_SELECTOR_FEATURES))
    parser.add_argument("--label-margin", type=float, default=0.0)
    parser.add_argument("--epochs", type=int, default=1000)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-3)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--num-workers", type=int, default=8)
    parser.add_argument("--rollout-conflicts", type=int, default=500)
    parser.add_argument("--warmup-cpu-lim", type=float, default=10.0)
    parser.add_argument("--state-momentum", type=float, default=0.5)
    parser.add_argument("--event-state-features", default="enhanced")
    return parser.parse_args()


def selector_specs_from_args(
    datasets: list[str] | str,
    base_eval_csvs: list[str] | str,
    adapter_eval_csvs: list[str] | str,
) -> list[tuple[str, str, str]]:
    if isinstance(datasets, str):
        datasets = [datasets]
    if isinstance(base_eval_csvs, str):
        base_eval_csvs = [base_eval_csvs]
    if isinstance(adapter_eval_csvs, str):
        adapter_eval_csvs = [adapter_eval_csvs]
    if not (len(datasets) == len(base_eval_csvs) == len(adapter_eval_csvs)):
        raise ValueError(
            "--dataset, --base-eval-csv, and --adapter-eval-csv must be provided "
            "the same number of times"
        )
    return list(zip(datasets, base_eval_csvs, adapter_eval_csvs))


def cnf_ids_from_batch(batch) -> list[int]:
    cnf_id = batch.cnf_id
    if hasattr(cnf_id, "view"):
        return [int(value) for value in cnf_id.view(-1).tolist()]
    if isinstance(cnf_id, list):
        return [int(value.item() if hasattr(value, "item") else value) for value in cnf_id]
    return [int(cnf_id)]


def extract_selector_features(model, loader, feature_names: list[str]) -> pd.DataFrame:
    rows = []
    model.eval()
    with torch.no_grad():
        for batch in loader:
            y = model(batch)
            base_y = batch["var"].base_y.to(dtype=torch.float32)
            var_state = batch["var"].event_state.to(dtype=torch.float32)
            delta = y.to(dtype=torch.float32) - base_y
            var_batch = batch["var"].batch if hasattr(batch["var"], "batch") else batch["lit"].batch[0::2]
            var_batch = var_batch.to(device=base_y.device)
            num_graphs = int(var_batch.max().item()) + 1 if var_batch.numel() > 0 else 1
            feature_values = torch.stack(
                [
                    model._event_adapter_selector_feature(
                        name,
                        base_y=base_y,
                        var_state=var_state,
                        delta=delta,
                        var_batch=var_batch,
                        num_graphs=num_graphs,
                    )
                    for name in feature_names
                ],
                dim=1,
            )
            for cnf_id, values in zip(cnf_ids_from_batch(batch), feature_values.cpu()):
                row = {"cnf_id": int(cnf_id)}
                row.update({name: float(value) for name, value in zip(feature_names, values.tolist())})
                rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    feature_names = [name.strip() for name in args.features.split(",") if name.strip()]
    if not feature_names:
        raise ValueError("At least one selector feature is required")
    selector_specs = selector_specs_from_args(
        datasets=args.dataset,
        base_eval_csvs=args.base_eval_csv,
        adapter_eval_csvs=args.adapter_eval_csv,
    )

    model, transform, model_cfg = load_checkpoint(args.checkpoint, var_output=True)
    if not getattr(model, "event_adapter_enabled", False):
        raise ValueError("The selector requires an event-adapter checkpoint")

    # The selector is trained from ungated adapter behavior; keep per-variable residual gating.
    model.event_adapter_selector_feature_names = []
    model.event_adapter_base_rho_gate_threshold = None
    model.event_adapter_graph_gate_indices = []
    model.event_adapter_graph_gate_threshold = None

    train_frames = []
    for spec_id, (dataset_path, base_eval_csv, adapter_eval_csv) in enumerate(selector_specs):
        dataset = DimacsCNFDataset(path=dataset_path, transform=transform, lazy=True)
        loader = DataLoader(dataset=dataset, batch_size=args.batch_size, num_workers=0, shuffle=False)
        warmup_data = sample_var_params(
            model=model,
            loader=loader,
            device="cpu",
            use_mode=True,
            num_samples=1,
            scale_sigma=model_cfg.scale_sigma,
            add_timing=True,
            cache_var_features=True,
        )
        warmup_params = apply_rollout_budget(
            dict(model_cfg.solver.params),
            budget_type="conflicts",
            cpu_lim=args.warmup_cpu_lim,
            conflicts=args.rollout_conflicts,
        )
        warmup_params["collect-events"] = True
        warmup_stats = compute_solver_stats(
            dataset=dataset,
            data_list=warmup_data,
            num_workers=args.num_workers,
            solver=model_cfg.solver.solver,
            **warmup_params,
        )
        refined_graphs = attach_var_event_state_batch(
            warmup_data,
            warmup_stats,
            var_state_dim=model.var_state_dim,
            momentum=args.state_momentum,
            feature_mode=args.event_state_features,
        )
        feature_loader = DataLoader(dataset=refined_graphs, batch_size=args.batch_size, num_workers=0, shuffle=False)
        feature_frame = extract_selector_features(model, feature_loader, feature_names)

        base_eval = pd.read_csv(base_eval_csv)
        adapter_eval = pd.read_csv(adapter_eval_csv)
        train_frame = selector_training_frame(
            feature_frame,
            base_eval=base_eval,
            adapter_eval=adapter_eval,
            label_margin=args.label_margin,
        )
        train_frame["selector_spec_id"] = spec_id
        train_frame["selector_dataset"] = dataset_path
        train_frames.append(train_frame)
    train_frame = pd.concat(train_frames, ignore_index=True)
    features = torch.tensor(train_frame[feature_names].to_numpy(), dtype=torch.float32)
    labels = torch.tensor(train_frame["label"].to_numpy(), dtype=torch.float32)
    selector, probs = fit_linear_selector(
        features,
        labels,
        feature_names=feature_names,
        epochs=args.epochs,
        lr=args.lr,
        l2=args.l2,
    )
    base_time = torch.tensor(train_frame["base_time"].to_numpy(), dtype=torch.float32)
    adapter_time = torch.tensor(train_frame["adapter_time"].to_numpy(), dtype=torch.float32)
    threshold, mean_time = choose_threshold_for_time(base_time, adapter_time, probs)
    selector.threshold = float(threshold)
    train_frame["selector_prob"] = probs.detach().cpu().numpy()
    train_frame["selector_use_adapter"] = (train_frame["selector_prob"] >= selector.threshold).astype("int64")
    train_frame["selector_time"] = selected_time(base_time, adapter_time, probs, selector.threshold).cpu().numpy()

    os.makedirs(args.output_dir, exist_ok=True)
    shutil.copy2(args.checkpoint, os.path.join(args.output_dir, "best.pt"))
    cfg_path = os.path.join(os.path.dirname(args.checkpoint), "config.yaml")
    cfg = OmegaConf.load(cfg_path)
    cfg.model.event_adapter.selector_feature_names = selector.feature_names
    cfg.model.event_adapter.selector_weights = selector.weights
    cfg.model.event_adapter.selector_bias = selector.bias
    cfg.model.event_adapter.selector_threshold = selector.threshold
    cfg.model.event_adapter.selector_feature_mean = selector.feature_mean
    cfg.model.event_adapter.selector_feature_std = selector.feature_std
    cfg.model.event_adapter.base_rho_gate_threshold = None
    cfg.model.event_adapter.graph_gate_indices = None
    cfg.model.event_adapter.graph_gate_threshold = None
    OmegaConf.save(cfg, os.path.join(args.output_dir, "config.yaml"))
    train_frame.to_csv(os.path.join(args.output_dir, "selector_training.csv"), index=False)

    print(f"selector features: {selector.feature_names}")
    print(f"selector weights: {selector.weights}")
    print(f"selector bias: {selector.bias:.6f}")
    print(f"selector threshold: {selector.threshold:.6f}")
    print(f"selected fraction: {train_frame['selector_use_adapter'].mean():.4f}")
    print(f"baseline mean time: {base_time.mean().item():.6f}")
    print(f"adapter mean time: {adapter_time.mean().item():.6f}")
    print(f"selector offline mean time: {mean_time:.6f}")
    print(f"saved selector checkpoint dir: {args.output_dir}")


if __name__ == "__main__":
    main()
