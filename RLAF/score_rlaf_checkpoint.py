from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import torch
from omegaconf import OmegaConf
from torch_geometric.loader import DataLoader

from src.data.dataset import DimacsCNFDataset
from src.model.model import load_checkpoint
from src.policy.evaluate import compute_solver_stats, sample_var_params
from train_rlaf import add_composite_target, add_sample_diversity_target, save_best_score_state


def solver_params(cfg) -> dict:
    return {
        str(key): value
        for key, value in dict(cfg.solver.params).items()
        if value is not None
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score an RLAF checkpoint with the training validation protocol.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--val-path", default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--write-best-score", action="store_true")
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    model, transform, cfg = load_checkpoint(str(args.checkpoint))
    if args.val_path is not None:
        cfg.dataset.val_path = args.val_path
    if args.workers is not None:
        cfg.solver.num_workers = int(args.workers)
    OmegaConf.resolve(cfg)

    dataset = DimacsCNFDataset(
        path=cfg.dataset.val_path,
        transform=transform,
        lazy=bool(cfg.dataset.lazy_val) if "lazy_val" in cfg.dataset else False,
    )
    loader = DataLoader(
        dataset=dataset,
        batch_size=cfg.loader.batch_size,
        num_workers=cfg.loader.num_workers,
        shuffle=False,
    )
    data_list = sample_var_params(
        model=model,
        loader=loader,
        num_samples=1,
        device=args.device,
        use_mode=True,
        scale_sigma=cfg.scale_sigma,
    )
    stats = compute_solver_stats(
        dataset=dataset,
        data_list=data_list,
        num_workers=cfg.solver.num_workers,
        solver=cfg.solver.solver,
        **solver_params(cfg),
    )
    stats = add_composite_target(stats, cfg)
    stats = add_sample_diversity_target(stats, data_list, cfg)
    score = float(pd.to_numeric(stats[cfg.training.target_stat], errors="raise").mean())

    if args.output_csv is not None:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        stats.to_csv(args.output_csv, index=False)
    if args.write_best_score:
        save_best_score_state(cfg, score, iteration=-1, global_step=0)

    print(f"checkpoint={args.checkpoint}")
    print(f"target_stat={cfg.training.target_stat}")
    print(f"validation_instances={len(dataset)}")
    print(f"score={score:.12g}")
    if args.output_csv is not None:
        print(args.output_csv)


if __name__ == "__main__":
    main()
