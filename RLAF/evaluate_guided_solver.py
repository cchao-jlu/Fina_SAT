import os

from omegaconf import DictConfig, OmegaConf
import hydra
import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from src.data.dataset import DimacsCNFDataset
from src.model.model import load_checkpoint
from src.policy import policy
from src.policy.evaluate import sample_var_params, compute_solver_stats, var_params_from_target_prediction
from src.solving.state import attach_global_state_batch


def print_solver_metrics(solver_stats: pd.DataFrame) -> None:
    keys = ["decisions", "conflicts", "propagations", "restarts", "CPU time", "GPU time", "time"]
    metrics = {key: solver_stats[key].mean() for key in keys if key in solver_stats.columns}
    print(
        f"Metrics: \n"
        + "\n".join(f"{key}: {val:.2f}" for key, val in metrics.items())
    )


def _cnf_id_value(data) -> int:
    cnf_id = data.cnf_id
    return int(cnf_id.item() if hasattr(cnf_id, "item") else cnf_id)


def _gpu_time_by_cnf(data_list: list) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cnf_id": [_cnf_id_value(data) for data in data_list],
            "GPU time": [float(getattr(data, "gpu_time", 0.0)) for data in data_list],
        }
    )


def _attach_selector_feature_overrides(
    data_list: list,
    selector_feature_names: list[str],
    final_point: int,
    feature_by_point: dict[int, pd.DataFrame],
    local_reopen_candidate_ids: set[int] | None = None,
) -> list:
    local_reopen_candidate_ids = set(local_reopen_candidate_ids or set())
    updated = []
    for data in data_list:
        cnf_id = _cnf_id_value(data)
        values = []
        for name in selector_feature_names:
            if name == "local_reopen_candidate":
                values.append(1.0 if cnf_id in local_reopen_candidate_ids else 0.0)
                continue
            value = 0.0
            if name.startswith("warmup_c"):
                rest = name[len("warmup_c") :]
                point_raw, sep, feature_name = rest.partition("_")
                try:
                    point = int(point_raw)
                except ValueError:
                    point = int(final_point)
                    feature_name = name
                if sep and point in feature_by_point and feature_name in feature_by_point[point].columns:
                    frame = feature_by_point[point]
                    if cnf_id in frame.index:
                        value = float(frame.loc[cnf_id, feature_name])
            elif final_point in feature_by_point and name in feature_by_point[final_point].columns:
                frame = feature_by_point[final_point]
                if cnf_id in frame.index:
                    value = float(frame.loc[cnf_id, name])
            values.append(value)
        data.event_adapter_selector_features = torch.tensor([values], dtype=torch.float32)
        updated.append(data)
    return updated


def add_total_time_columns(
    solver_stats: pd.DataFrame,
    data_list: list,
    refinement_stats: pd.DataFrame | None = None,
    refinement_data_list: list | None = None,
) -> pd.DataFrame:
    solver_stats = solver_stats.copy()
    final_gpu = _gpu_time_by_cnf(data_list).rename(columns={"GPU time": "final GPU time"})
    solver_stats = solver_stats.merge(final_gpu, on="cnf_id", how="left")
    solver_stats["final GPU time"] = solver_stats["final GPU time"].fillna(0.0)
    solver_stats["refinement CPU time"] = 0.0
    solver_stats["refinement GPU time"] = 0.0

    if refinement_stats is not None and "CPU time" in refinement_stats.columns:
        warmup_cpu = (
            refinement_stats[["cnf_id", "CPU time"]]
            .groupby("cnf_id", sort=False)["CPU time"]
            .sum()
            .rename("refinement CPU time")
            .reset_index()
        )
        solver_stats = solver_stats.drop(columns=["refinement CPU time"]).merge(
            warmup_cpu,
            on="cnf_id",
            how="left",
        )
        solver_stats["refinement CPU time"] = solver_stats["refinement CPU time"].fillna(0.0)

    if refinement_data_list is not None:
        warmup_gpu = (
            _gpu_time_by_cnf(refinement_data_list)
            .groupby("cnf_id", sort=False)["GPU time"]
            .sum()
            .rename("refinement GPU time")
            .reset_index()
        )
        solver_stats = solver_stats.drop(columns=["refinement GPU time"]).merge(
            warmup_gpu,
            on="cnf_id",
            how="left",
        )
        solver_stats["refinement GPU time"] = solver_stats["refinement GPU time"].fillna(0.0)

    solver_stats["GPU time"] = solver_stats["final GPU time"] + solver_stats["refinement GPU time"]
    solver_stats["time"] = (
        solver_stats["CPU time"]
        + solver_stats["refinement CPU time"]
        + solver_stats["GPU time"]
    )
    return solver_stats


@hydra.main(version_base=None, config_path="configs", config_name="config_eval_guided_solver")
def main(cfg: DictConfig):
    OmegaConf.resolve(cfg)

    if not cfg.is_supervised:
        model, transform, model_cfg = load_checkpoint(cfg.checkpoint, var_output=True)
    else:
        model, transform, model_cfg = load_checkpoint(cfg.checkpoint, var_output=False)

    dataset = DimacsCNFDataset(
        path=cfg.dataset.eval_path,
        transform=transform,
    )

    loader = DataLoader(
        dataset=dataset,
        batch_size=cfg.loader.batch_size,
        num_workers=cfg.loader.num_workers,
        shuffle=False,
    )

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model.to(device)
    global_state_dim = getattr(model, "global_state_dim", 0)
    if cfg.feedback_refinement.enabled and global_state_dim <= 0:
        raise ValueError("global feedback_refinement requires model.global_state_dim > 0")

    # warmup GPU for accurate time measurements
    warmup_steps = 4
    with torch.no_grad():
        for i, data in enumerate(loader):
            data.to(device)
            y_var = model(data)
            if not cfg.is_supervised:
                _ = policy.mode(y_var)
            if i >= warmup_steps:
                break

    current_loader = loader
    refinement_stats = None
    refinement_data_list = None
    if cfg.feedback_refinement.enabled:
        if cfg.is_supervised:
            raise ValueError("feedback_refinement is only implemented for var-output checkpoints")
        warmup_data_list = sample_var_params(
            model=model,
            loader=current_loader,
            device=device,
            use_mode=True,
            num_samples=1,
            scale_sigma=model_cfg.scale_sigma,
            add_timing=True,
        )
        warmup_params = dict(cfg.solver.params)
        warmup_params["cpu-lim"] = cfg.feedback_refinement.warmup_cpu_lim
        refinement_stats = compute_solver_stats(
            dataset=dataset,
            data_list=warmup_data_list,
            num_workers=cfg.solver.num_workers,
            solver=model_cfg.solver.solver if cfg.solver.solver is None else cfg.solver.solver,
            **warmup_params,
        )
        refinement_data_list = warmup_data_list
        refined_graphs = attach_global_state_batch(
            warmup_data_list,
            solver_stats=refinement_stats,
            global_state_dim=global_state_dim,
        )
        current_loader = DataLoader(
            dataset=refined_graphs,
            batch_size=cfg.loader.batch_size,
            num_workers=cfg.loader.num_workers,
            shuffle=False,
        )

    if not cfg.is_supervised:
        data_list = sample_var_params(
            model=model,
            loader=current_loader,
            device=device,
            use_mode=True,
            num_samples=1,
            scale_sigma=model_cfg.scale_sigma,
            add_timing=True,
        )
    else:
        data_list = var_params_from_target_prediction(
            model=model,
            loader=loader,
            device=device,
            target=model_cfg.dataset.target,
            pred_scale=cfg.pred_scale,
            add_timing=True,
        )

    solver = model_cfg.solver.solver if cfg.solver.solver is None else cfg.solver.solver
    solver_params = cfg.solver.params
    print(solver_params)

    solver_stats = compute_solver_stats(
        dataset=dataset,
        data_list=data_list,
        num_workers=cfg.solver.num_workers,
        solver=solver,
        **solver_params,
    )

    solver_stats = add_total_time_columns(
        solver_stats,
        data_list=data_list,
        refinement_stats=refinement_stats,
        refinement_data_list=refinement_data_list,
    )

    print_solver_metrics(solver_stats)

    if cfg.save_file is not None:
        save_file = os.path.join(os.path.dirname(cfg.checkpoint), cfg.save_file)
        solver_stats.to_csv(save_file)


if __name__ == '__main__':
    main()
