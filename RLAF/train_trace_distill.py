import os

import hydra
import pandas as pd
import torch
from omegaconf import DictConfig, OmegaConf
from torch_geometric.loader import DataLoader
from torch_geometric.seed import seed_everything

from src.model.checkpoint import load_compatible_state_dict
from src.model.model import GNN, init_model, init_transform
from src.training.trace_distill import (
    build_permutation_consistency_pairs,
    freeze_non_adapter_parameters,
    relabel_trace_distillation_graphs,
    trace_label_config_from_mapping,
    train_trace_distillation_epoch,
)


def resolve_path(path: str, work_dir: str) -> str:
    return path if os.path.isabs(path) else os.path.join(work_dir, path)


def save_model(model: GNN, cfg: DictConfig, checkpoint_name: str = "last") -> None:
    model_dir = resolve_path(cfg.model_dir, cfg.work_dir)
    os.makedirs(model_dir, exist_ok=True)
    with open(os.path.join(model_dir, "config.yaml"), "w") as f:
        OmegaConf.save(cfg, f)
    torch.save(model.state_dict(), os.path.join(model_dir, f"{checkpoint_name}.pt"))


def load_compatible_checkpoint(model: torch.nn.Module, ckpt_path: str) -> tuple[list[str], list[str]]:
    return load_compatible_state_dict(model, ckpt_path)


def load_trace_payload(path: str) -> tuple[list, object | None]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(payload, dict) and "graphs" in payload:
        return payload["graphs"], payload.get("solver_stats")
    if isinstance(payload, list):
        return payload, None
    raise ValueError(f"Trace distillation file must contain a graph list or a dict with key 'graphs': {path}")


@hydra.main(version_base=None, config_path="configs", config_name="config_train_trace_distill")
def main(cfg: DictConfig) -> None:
    OmegaConf.resolve(cfg)
    print(OmegaConf.to_yaml(cfg))
    seed_everything(cfg.seed)

    transform = init_transform(cfg)
    model = init_model(cfg, transform)
    if cfg.from_checkpoint is not None:
        loaded, skipped = load_compatible_checkpoint(model, resolve_path(cfg.from_checkpoint, cfg.work_dir))
        print(
            f"Loaded {len(loaded)} compatible tensors from {cfg.from_checkpoint}; "
            f"skipped {len(skipped)} tensors with missing or mismatched shapes."
        )
    if bool(cfg.training.freeze_backbone):
        adapter_train_mode = (
            str(cfg.training.adapter_train_mode)
            if "adapter_train_mode" in cfg.training
            else "adapter"
        )
        freeze_non_adapter_parameters(model, adapter_train_mode=adapter_train_mode)

    trace_graphs, solver_stats = load_trace_payload(resolve_path(cfg.trace.data_path, cfg.work_dir))
    if not trace_graphs:
        raise ValueError(f"No trace distillation graphs found in {cfg.trace.data_path}")
    label_config = trace_label_config_from_mapping(cfg.trace.label)
    relabel = bool(cfg.trace.relabel) if "relabel" in cfg.trace else True
    if relabel and solver_stats is not None:
        trace_graphs = relabel_trace_distillation_graphs(
            trace_graphs,
            solver_stats=solver_stats,
            label_config=label_config,
        )
    permutation_pairs = []
    permutation_manifest_path = (
        resolve_path(str(cfg.trace.permutation_manifest_path), cfg.work_dir)
        if "permutation_manifest_path" in cfg.trace and cfg.trace.permutation_manifest_path is not None
        else None
    )
    if float(label_config.permutation_consistency_weight) > 0.0:
        if solver_stats is None:
            raise ValueError("Permutation consistency loss requires solver_stats in the trace payload")
        if permutation_manifest_path is None:
            raise ValueError("Permutation consistency loss requires trace.permutation_manifest_path")
        manifest = pd.read_csv(permutation_manifest_path)
        permutation_pairs = build_permutation_consistency_pairs(
            trace_graphs=trace_graphs,
            solver_stats=solver_stats,
            manifest=manifest,
        )
        if not permutation_pairs:
            raise ValueError("Permutation consistency loss found no base/permuted graph pairs")
        print(f"Built {len(permutation_pairs)} permutation-consistency pairs.")
    loader = DataLoader(
        dataset=trace_graphs,
        batch_size=cfg.loader.batch_size,
        num_workers=cfg.loader.num_workers,
        shuffle=True,
    )

    trainable_params = [param for param in model.parameters() if param.requires_grad]
    if not trainable_params:
        raise ValueError("Trace distillation has no trainable parameters")
    optimizer = torch.optim.AdamW(
        trainable_params,
        lr=cfg.optim.lr,
        weight_decay=cfg.optim.weight_decay,
    )
    device = "cuda:0" if torch.cuda.is_available() and bool(cfg.training.use_cuda) else "cpu"

    best_loss = float("inf")
    for epoch in range(int(cfg.training.epochs)):
        metrics = train_trace_distillation_epoch(
            model=model,
            loader=loader,
            optimizer=optimizer,
            device=device,
            config=label_config,
            permutation_pairs=permutation_pairs,
            use_amp=bool(cfg.training.use_amp),
        )
        print(
            f"epoch={epoch} loss={metrics['loss']:.6f} "
            f"perm_loss={metrics.get('permutation_consistency_loss', 0.0):.6f} "
            f"batches={int(metrics['batches'])}"
        )
        if metrics["loss"] < best_loss:
            best_loss = metrics["loss"]
            save_model(model, cfg, "best")
        if cfg.training.ckpt_interval is not None and epoch % int(cfg.training.ckpt_interval) == 0:
            save_model(model, cfg, f"epoch={epoch}")
        save_model(model, cfg, "last")


if __name__ == "__main__":
    main()
