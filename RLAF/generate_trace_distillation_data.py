import os

import hydra
import pandas as pd
import torch
from omegaconf import DictConfig, OmegaConf
from torch_geometric.loader import DataLoader
from torch_geometric.seed import seed_everything

from src.data.dataset import DimacsCNFDataset
from src.model.model import init_model, init_transform, load_checkpoint
from src.policy.evaluate import compute_solver_stats, sample_var_params
from src.solving.budget import apply_rollout_budget
from src.solving.state import event_state_dim
from src.training.trace_distill import (
    build_trace_distillation_graphs,
    trace_label_config_from_mapping,
    trace_label_config_to_dict,
)


def resolve_path(path: str, work_dir: str) -> str:
    return path if os.path.isabs(path) else os.path.join(work_dir, path)


def load_slow_model_and_transform(cfg: DictConfig):
    if cfg.from_checkpoint is not None:
        model, transform, _ = load_checkpoint(resolve_path(cfg.from_checkpoint, cfg.work_dir))
        return model, transform
    transform = init_transform(cfg)
    return init_model(cfg, transform), transform


def make_dimacs_dataset(path, transform, lazy: bool) -> DimacsCNFDataset:
    try:
        return DimacsCNFDataset(
            path=path,
            transform=transform,
            lazy=lazy,
        )
    except TypeError:
        return DimacsCNFDataset(
            path=path,
            transform=transform,
        )


@hydra.main(version_base=None, config_path="configs", config_name="config_generate_trace_distillation")
def main(cfg: DictConfig) -> None:
    OmegaConf.resolve(cfg)
    print(OmegaConf.to_yaml(cfg))
    seed_everything(cfg.seed)

    work_dir = cfg.work_dir
    output_path = resolve_path(cfg.trace.output_path, work_dir)
    stats_path = resolve_path(cfg.trace.stats_path, work_dir)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)

    slow_model, transform = load_slow_model_and_transform(cfg)
    dataset_path = resolve_path(cfg.dataset.path, work_dir)
    if "manifest" in cfg.dataset and cfg.dataset.manifest is not None:
        manifest = pd.read_csv(resolve_path(cfg.dataset.manifest, work_dir))
        if "event_audit_role" in manifest.columns:
            manifest = manifest[manifest["event_audit_role"].fillna("event").astype(str) != "static_only"].copy()
        paths = manifest["cnf_path"].astype(str).tolist()
        dataset_path = paths
    dataset = make_dimacs_dataset(
        path=dataset_path,
        transform=transform,
        lazy=bool(cfg.dataset.lazy),
    )
    loader = DataLoader(
        dataset=dataset,
        batch_size=cfg.loader.batch_size,
        num_workers=cfg.loader.num_workers,
        shuffle=False,
    )

    device = "cuda:0" if torch.cuda.is_available() and bool(cfg.trace.use_cuda) else "cpu"
    warmup_graphs = sample_var_params(
        model=slow_model,
        loader=loader,
        num_samples=cfg.trace.num_samples,
        max_num_batches=cfg.trace.max_num_batches,
        device=device,
        use_mode=bool(cfg.trace.use_mode),
        scale_sigma=cfg.scale_sigma,
        add_timing=True,
        cache_var_features=True,
    )

    rollout_params = apply_rollout_budget(
        dict(cfg.solver.params),
        budget_type=cfg.trace.rollout_budget_type,
        cpu_lim=cfg.trace.rollout_cpu_lim,
        conflicts=cfg.trace.rollout_conflicts,
    )
    rollout_params["collect-events"] = True
    if "trace_lbd_threshold" in cfg.trace:
        rollout_params["trace-lbd"] = int(cfg.trace.trace_lbd_threshold)

    solver_stats = compute_solver_stats(
        dataset=dataset,
        data_list=warmup_graphs,
        num_workers=cfg.solver.num_workers,
        solver=cfg.solver.solver,
        **rollout_params,
    )
    solver_stats.to_csv(stats_path, index=False)

    label_config = trace_label_config_from_mapping(cfg.trace.label)
    var_state_dim = int(cfg.model.var_state_dim) if "var_state_dim" in cfg.model else event_state_dim(cfg.trace.event_state_features)
    trace_graphs = build_trace_distillation_graphs(
        data_list=warmup_graphs,
        solver_stats=solver_stats,
        var_state_dim=var_state_dim,
        event_state_feature_mode=cfg.trace.event_state_features,
        state_momentum=float(cfg.trace.state_momentum),
        label_config=label_config,
    )
    torch.save(
        {
            "graphs": trace_graphs,
            "solver_stats": solver_stats,
            "label_config": trace_label_config_to_dict(label_config),
            "config": OmegaConf.to_container(cfg, resolve=True),
        },
        output_path,
    )
    print(f"Saved {len(trace_graphs)} trace distillation graphs to {output_path}")
    print(f"Saved rollout stats to {stats_path}")


if __name__ == "__main__":
    main()
