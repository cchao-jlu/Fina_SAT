import json
import math
import os
import tempfile
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import pandas as pd
import torch

import wandb
from omegaconf import DictConfig, OmegaConf
from torch_geometric.loader import DataLoader
from torch_geometric.seed import seed_everything
from torch.utils.data import Subset

from evaluate_guided_solver import load_checkpoint
from src.data.dataset import DimacsCNFDataset, RLTrainingDataset
from src.echosat.objective_v2 import attach_masked_grpo_advantage, build_symmetry_grpo_v2_target
from src.echosat.orbit_features import OrbitFeatureStore, attach_orbit_features
from src.model.checkpoint import load_compatible_state_dict
from src.policy.evaluate import compute_plain_solver_stats, compute_solver_stats, sample_random_var_params, sample_var_params
from src.model.model import GNN, init_model, init_transform
from src.solving.solver import neutral_var_params
from src.solving.state import attach_global_state_batch, attach_var_event_state_batch

from src.training.dpo import train_dpo
from src.training.grpo import train_grpo, get_grpo_advantage

import warnings
warnings.filterwarnings("ignore", category=UserWarning)


PROJECT_ROOT = Path(__file__).resolve().parent
COMPOSITE_TARGETS = {"composite"}
SPEEDUP_TARGETS = {"speedup_cost"}
ECHOSAT_TARGETS = {"echosat_cost"}
WARMUP_RATE_EPSILON = 1.0e-6
PLAIN_BASELINE_CACHE_ATTR = "_echosat_plain_unguided_cache"
PLAIN_BASELINE_FALLBACK_CACHE_MAX_SIZE = 16
_PLAIN_BASELINE_FALLBACK_CACHE: OrderedDict[int, tuple[object, dict[tuple, pd.DataFrame]]] = OrderedDict()
REPLAY_ONLY_LOG = "Replay-only mode: reward replay artifacts written; skipping optimizer and training updates."
REPLAY_CORE_MODEL_PREFIXES = (
    "lit_enc.",
    "cls_enc.",
    "layers.",
    "out_lin1.",
    "out_lin2.",
)


def load_compatible_checkpoint(model: torch.nn.Module, ckpt_path: str) -> tuple[list[str], list[str]]:
    return load_compatible_state_dict(model, ckpt_path)


def cfg_get(cfg: DictConfig, key: str, default):
    return cfg[key] if key in cfg else default


def cfg_string_set(cfg: DictConfig, key: str) -> set[str]:
    value = cfg_get(cfg, key, [])
    if value is None:
        return set()
    if isinstance(value, str):
        return {item.strip() for item in value.split(",") if item.strip()}
    return {str(item).strip() for item in value if str(item).strip()}


def _echosat_replay_only_enabled(cfg: DictConfig) -> bool:
    training = cfg.training
    has_canonical = "echosat_replay_only" in training
    has_legacy = "replay_only" in training
    canonical = bool(training.echosat_replay_only) if has_canonical else False
    legacy = bool(training.replay_only) if has_legacy else False
    if has_canonical and has_legacy and canonical != legacy:
        raise ValueError(
            "conflicting replay-only keys: training.echosat_replay_only and training.replay_only"
        )
    return canonical if has_canonical else legacy


def validate_replay_only_config(cfg: DictConfig) -> None:
    if not _echosat_replay_only_enabled(cfg):
        return
    if str(cfg_get(cfg, "method", "")) != "grpo":
        raise ValueError("replay_only requires method='grpo'")
    if str(cfg_get(cfg.training, "echosat_target_mode", "")) != "symmetry_grpo_v2":
        raise ValueError("replay_only requires echosat_target_mode='symmetry_grpo_v2'")
    if not bool(cfg_get(cfg.training, "save_echosat_reward_replay", False)):
        raise ValueError("replay_only requires save_echosat_reward_replay=true")
    if int(cfg_get(cfg.training, "steps_per_iter", -1)) != 0:
        raise ValueError("replay_only requires steps_per_iter=0")
    if cfg_get(cfg, "ckpt_interval", None) is not None:
        raise ValueError("replay_only requires ckpt_interval=None")
    if not bool(cfg_get(cfg, "skip_initial_val", False)):
        raise ValueError("replay_only requires skip_initial_val=true")


def model_updates_enabled(cfg: DictConfig) -> bool:
    return not _echosat_replay_only_enabled(cfg)


def _remove_owned_run_marker(
        marker: Path,
        owner_identity: tuple[int, int],
) -> bool:
    try:
        current = marker.lstat()
    except FileNotFoundError:
        return False
    if (current.st_dev, current.st_ino) != owner_identity:
        return False
    marker.unlink()
    return True


def validate_training_output_directory(cfg: DictConfig) -> None:
    if not model_updates_enabled(cfg):
        return
    model_dir_value = cfg_get(cfg, "model_dir", None)
    if model_dir_value is None or str(model_dir_value).strip() == "":
        raise ValueError("model_dir must be configured for model updates")
    model_dir = Path(str(model_dir_value)).expanduser()
    if not model_dir.exists() and not model_dir.is_symlink():
        model_dir.mkdir(parents=True, exist_ok=True)
    if not model_dir.is_dir():
        raise ValueError(f"model_dir must be a directory: {model_dir}")
    if any(model_dir.iterdir()):
        raise ValueError(f"model_dir is non-empty; refusing a new training run: {model_dir}")
    marker = model_dir / ".echosat-run-owner"
    owner = {
        "pid": os.getpid(),
        "timestamp": time.time(),
        "model_name": str(cfg_get(cfg, "model_name", "")),
    }
    try:
        descriptor = os.open(
            marker,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        raise ValueError(
            f"model_dir is already claimed by another training run: {model_dir}"
        ) from exc
    marker_stat = os.fstat(descriptor)
    owner_identity = (marker_stat.st_dev, marker_stat.st_ino)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(owner, handle, sort_keys=True)
            handle.write("\n")
    except Exception:
        _remove_owned_run_marker(marker, owner_identity)
        raise
    unexpected = [path for path in model_dir.iterdir() if path != marker]
    if unexpected:
        _remove_owned_run_marker(marker, owner_identity)
        raise ValueError(f"model_dir is non-empty; refusing a new training run: {model_dir}")


def completed_iteration_checkpoint_name(
        iteration: int,
        checkpoint_interval: int | None,
) -> str | None:
    if checkpoint_interval is None:
        return None
    interval = int(checkpoint_interval)
    if interval <= 0:
        raise ValueError("checkpoint_interval must be positive or None")
    completed_iteration = int(iteration) + 1
    if completed_iteration <= 0:
        raise ValueError("iteration must be nonnegative")
    if completed_iteration % interval != 0:
        return None
    return f"iter={completed_iteration}"


def replay_artifacts_before_update(cfg: DictConfig, artifact_writer) -> bool:
    artifact_writer()
    if not _echosat_replay_only_enabled(cfg):
        return False
    validate_replay_only_config(cfg)
    print(REPLAY_ONLY_LOG)
    return True


def run_training_update_after_replay_artifacts(cfg, artifact_writer, training_update):
    if replay_artifacts_before_update(cfg, artifact_writer):
        return None
    return training_update()


def build_training_optimizer_scheduler(trainable_parameters, cfg: DictConfig):
    if not model_updates_enabled(cfg):
        return None, None
    optim = torch.optim.AdamW(
        params=trainable_parameters,
        lr=cfg.optim.lr,
        weight_decay=cfg.optim.weight_decay,
        maximize=True,
    )
    warmup_iterations = 5

    def lr_lambda(step):
        if step < warmup_iterations:
            return float(step + 1) / float(warmup_iterations)
        return 1.0

    return optim, torch.optim.lr_scheduler.LambdaLR(optim, lr_lambda)


def build_validation_runtime(
        cfg: DictConfig,
        transform,
        training_manifest,
        allow_model_updates: bool,
):
    if not allow_model_updates:
        return None, None, None, None
    dataset_val = DimacsCNFDataset(
        path=dataset_path_from_config(cfg.dataset.val_path),
        transform=transform,
        lazy=bool(cfg_get(cfg.dataset, "lazy_val", cfg_get(cfg.dataset, "lazy", False))),
    )
    val_manifest_path = str(cfg_get(cfg.training, "echosat_val_manifest_path", ""))
    val_manifest = load_manifest_from_path(val_manifest_path) if val_manifest_path else training_manifest
    val_metadata = dataset_metadata(dataset_val, val_manifest, required=uses_echosat_target(cfg))
    val_orbit_store = load_echosat_v2_orbit_store(cfg, val_metadata)
    loader_val = DataLoader(
        dataset=dataset_val,
        batch_size=cfg.loader.batch_size,
        num_workers=cfg.loader.num_workers,
        shuffle=False,
    )
    return dataset_val, val_metadata, val_orbit_store, loader_val


def _validate_compatible_checkpoint_coverage(
        model: torch.nn.Module,
        loaded: list[str],
        skipped: list[str],
        context: str,
) -> None:
    model_keys = tuple(model.state_dict())
    loaded_keys = set(loaded)
    loaded_core = [
        key for key in loaded_keys
        if any(key.startswith(prefix) for prefix in REPLAY_CORE_MODEL_PREFIXES)
    ]
    if not loaded_core:
        raise ValueError(f"{context} checkpoint loaded zero core model parameters")
    required_prefixes = [
        prefix for prefix in REPLAY_CORE_MODEL_PREFIXES
        if any(key.startswith(prefix) for key in model_keys)
    ]
    missing_prefixes = [
        prefix for prefix in required_prefixes
        if not any(key.startswith(prefix) for key in loaded_keys)
    ]
    if missing_prefixes:
        raise ValueError(
            f"{context} checkpoint missing core checkpoint prefixes: "
            + ", ".join(missing_prefixes)
        )
    skipped_core = sorted(
        key for key in skipped
        if any(key.startswith(prefix) for prefix in REPLAY_CORE_MODEL_PREFIXES)
    )
    if skipped_core:
        raise ValueError(
            f"{context} checkpoint skipped core model parameters: "
            + ", ".join(skipped_core)
        )
    unsupported_skipped = sorted(
        key for key in skipped
        if not key.startswith("event_adapter.")
    )
    if unsupported_skipped:
        raise ValueError(
            f"{context} checkpoint has unsupported skipped checkpoint parameters: "
            + ", ".join(unsupported_skipped)
        )


def _validate_replay_checkpoint_coverage(
        model: torch.nn.Module,
        loaded: list[str],
        skipped: list[str],
) -> None:
    _validate_compatible_checkpoint_coverage(
        model,
        loaded,
        skipped,
        context="replay",
    )


def _echosat_compatible_checkpoint_init_enabled(cfg: DictConfig) -> bool:
    value = cfg_get(cfg.training, "echosat_compatible_checkpoint_init", False)
    if not isinstance(value, (bool, np.bool_)):
        raise ValueError(
            "training.echosat_compatible_checkpoint_init must be a boolean"
        )
    return bool(value)


def load_training_model(cfg: DictConfig):
    checkpoint = cfg_get(cfg, "from_checkpoint", None)
    replay_only = _echosat_replay_only_enabled(cfg)
    compatible_init = _echosat_compatible_checkpoint_init_enabled(cfg)
    if compatible_init:
        if checkpoint is None or str(checkpoint).strip() == "":
            raise ValueError(
                "compatible_checkpoint_init requires from_checkpoint"
            )
        if str(cfg_get(cfg.training, "echosat_target_mode", "")) != "symmetry_grpo_v2":
            raise ValueError(
                "compatible_checkpoint_init requires "
                "training.echosat_target_mode='symmetry_grpo_v2'"
            )
    if checkpoint is None:
        if replay_only:
            raise ValueError("replay_only requires from_checkpoint to avoid random-model evidence")
        transform = init_transform(cfg)
        return init_model(cfg, transform), transform, cfg
    if replay_only or compatible_init:
        transform = init_transform(cfg)
        model = init_model(cfg, transform)
        loaded, skipped = load_compatible_checkpoint(model, str(checkpoint))
        context = "replay" if replay_only else "formal v2"
        _validate_compatible_checkpoint_coverage(
            model,
            loaded,
            skipped,
            context=context,
        )
        print(
            f"{context} compatible checkpoint load: "
            f"loaded={len(loaded)} skipped={len(skipped)} "
            f"loaded_keys={loaded} skipped_keys={skipped}"
        )
        return model, transform, cfg
    return load_checkpoint(checkpoint)


def attach_echosat_v2_orbits(
        data_list: list,
        store: OrbitFeatureStore | None,
) -> list:
    attached = []
    for data in data_list:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        rows = None if store is None else store.rows_for(cnf_id)
        attached.append(attach_orbit_features(data, rows))
    return attached


def _finite_nonnegative_warmup_stat(stats: dict | pd.Series, key: str) -> float:
    try:
        value = float(stats.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value) or value < 0.0:
        return 0.0
    return value


def attach_warmup_graph_evidence(data, stats: dict | pd.Series):
    warmup_cpu = _finite_nonnegative_warmup_stat(stats, "CPU time")
    warmup_conflicts = _finite_nonnegative_warmup_stat(stats, "conflicts")
    warmup_propagations = _finite_nonnegative_warmup_stat(stats, "propagations")
    warmup_decisions = _finite_nonnegative_warmup_stat(stats, "decisions")
    rates_are_valid = warmup_cpu >= WARMUP_RATE_EPSILON
    warmup_conflict_rate = warmup_conflicts / warmup_cpu if rates_are_valid else 0.0
    warmup_propagation_rate = warmup_propagations / warmup_cpu if rates_are_valid else 0.0
    data.warmup_cpu_time = torch.tensor(warmup_cpu, dtype=torch.float32)
    data.warmup_conflicts = torch.tensor(warmup_conflicts, dtype=torch.float32)
    data.warmup_propagations = torch.tensor(warmup_propagations, dtype=torch.float32)
    data.warmup_decisions = torch.tensor(warmup_decisions, dtype=torch.float32)
    data.warmup_conflict_rate = torch.tensor(warmup_conflict_rate, dtype=torch.float32)
    data.warmup_propagation_rate = torch.tensor(warmup_propagation_rate, dtype=torch.float32)
    return data


def solver_params(cfg: DictConfig) -> dict:
    return {
        str(key): value
        for key, value in dict(cfg.solver.params).items()
        if value is not None
    }


def ensure_plain_unguided_baseline(
        baseline_stats_by_name: dict[str, pd.DataFrame],
        dataset: DimacsCNFDataset,
        data_list: list,
        cfg: DictConfig,
) -> None:
    if str(cfg_get(cfg.training, "echosat_target_mode", "full")).lower() != "symmetry_grpo_v2":
        return

    layout: dict[int, int] = {}
    for data in data_list:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        num_samples = int(data["var"].var_params.shape[1])
        existing = layout.get(cnf_id)
        if existing is not None and existing != num_samples:
            raise ValueError(
                f"ensure_plain_unguided_baseline found conflicting sample counts for cnf_id={cnf_id}: "
                f"{existing} and {num_samples}"
            )
        if existing is None:
            layout[cnf_id] = num_samples

    plain_solver_params = solver_params(cfg)
    cache_key = (
        tuple(layout.items()),
        "glucose",
        json.dumps(plain_solver_params, sort_keys=True, default=str),
    )
    try:
        cache = getattr(dataset, PLAIN_BASELINE_CACHE_ATTR, None)
        if not isinstance(cache, dict):
            cache = {}
            setattr(dataset, PLAIN_BASELINE_CACHE_ATTR, cache)
    except (AttributeError, TypeError):
        dataset_id = id(dataset)
        fallback_entry = _PLAIN_BASELINE_FALLBACK_CACHE.get(dataset_id)
        if fallback_entry is None or fallback_entry[0] is not dataset:
            cache = {}
            _PLAIN_BASELINE_FALLBACK_CACHE[dataset_id] = (dataset, cache)
        else:
            cache = fallback_entry[1]
        _PLAIN_BASELINE_FALLBACK_CACHE.move_to_end(dataset_id)
        while len(_PLAIN_BASELINE_FALLBACK_CACHE) > PLAIN_BASELINE_FALLBACK_CACHE_MAX_SIZE:
            _PLAIN_BASELINE_FALLBACK_CACHE.popitem(last=False)

    cached = cache.get(cache_key)
    if cached is None:
        cached = compute_plain_solver_stats(
            dataset=dataset,
            data_list=data_list,
            num_workers=cfg.solver.num_workers,
            solver="glucose",
            **plain_solver_params,
        ).copy(deep=True)
        cache[cache_key] = cached
    baseline_stats_by_name["plain_unguided"] = cached.copy(deep=True)


def configure_trainable_parameters(model: GNN, cfg: DictConfig) -> list[torch.nn.Parameter]:
    scope = str(cfg_get(cfg.training, "trainable_scope", cfg_get(cfg.training, "freeze_trainable_scope", "all"))).lower()
    aliases = {
        "full": "all",
        "adapter": "event_adapter",
        "adapter_only": "event_adapter",
        "event_adapter_only": "event_adapter",
        "polarity": "event_adapter_polarity_gate",
        "polarity_gate": "event_adapter_polarity_gate",
    }
    scope = aliases.get(scope, scope)
    if scope not in {"all", "event_adapter", "event_adapter_mlp", "event_adapter_polarity_gate"}:
        raise ValueError(f"Unsupported training.trainable_scope={scope!r}")

    trainable_names = []
    total_params = 0
    trainable_params = 0
    for name, param in model.named_parameters():
        total_params += int(param.numel())
        if scope == "all":
            trainable = True
        elif scope == "event_adapter":
            trainable = "event_adapter" in name
        elif scope == "event_adapter_mlp":
            trainable = name.startswith("event_adapter.")
        else:
            trainable = "event_adapter_polarity_gate" in name
        param.requires_grad = bool(trainable)
        if trainable:
            trainable_names.append(name)
            trainable_params += int(param.numel())

    if not trainable_names:
        raise ValueError(f"training.trainable_scope={scope!r} selected no trainable parameters")
    print(
        f"Trainable scope: {scope}; "
        f"{trainable_params}/{total_params} parameters trainable across {len(trainable_names)} tensors"
    )
    print("Trainable parameter prefixes: " + ", ".join(trainable_names[:12]) + (" ..." if len(trainable_names) > 12 else ""))
    return [param for param in model.parameters() if param.requires_grad]


def log_solver_metrics(
        solver_stats: pd.DataFrame,
        iteration: int,
        global_step: int,
        prefix: str = "train",
        add_target_histogram: bool = False,
        target_stat: str = "decisions",
) -> None:
    keys = ["decisions", "conflicts", "propagations", "restarts", "CPU time"]
    metrics = {f"{prefix}/{key}": solver_stats[key].mean() for key in keys if key in solver_stats.columns}

    print(
        f"Solver metrics at iteration {iteration} ({prefix}): \n"
        + "\n".join(f"{key}: {val:.2f}" for key, val in metrics.items())
    )

    metrics[f"iteration"] = iteration
    metrics[f"global_step"] = global_step

    for key in keys:
        if key in metrics:
            metrics[f"{prefix}/{key}_histogram"] = wandb.Histogram(solver_stats[key])

    if add_target_histogram:
        grouped = solver_stats[["cnf_id", target_stat]].groupby("cnf_id")
        target_mean = grouped.mean().loc[solver_stats["cnf_id"]]
        target_mean = target_mean[target_stat].to_numpy()
        if not np.any(np.isnan(target_mean)):
            metrics[f"{prefix}/{target_stat}_histogram_mean"] = wandb.Histogram(target_mean)
        target_std = grouped.std().loc[solver_stats["cnf_id"]]
        target_std = target_std[target_stat].to_numpy()
        if not np.any(np.isnan(target_std)):
            metrics[f"{prefix}/{target_stat}_histogram_std"] = wandb.Histogram(target_std)
        if target_stat in solver_stats.columns:
            metrics[f"{prefix}/{target_stat}"] = solver_stats[target_stat].mean()
    for key in [
        "baseline_cpu_time",
        "baseline_conflicts",
        "baseline_decisions",
        "speedup_cpu_log_ratio",
        "speedup_conflicts_log_ratio",
        "speedup_decisions_log_ratio",
        "speedup_result_mismatch",
        "baseline_static_cpu_time",
        "baseline_static_conflicts",
        "baseline_static_decisions",
        "baseline_neutral_cpu_time",
        "echosat_final_cpu_cost",
        "echosat_search_cost",
        "echosat_overhead_cost",
        "echosat_weighted_risk",
        "echosat_perturbation_penalty",
        "echosat_perm_delta_penalty",
        "echosat_e_sym",
        "echosat_advantage_weight",
        "echosat_result_mismatch",
        "echosat_decision_reduction",
        "echosat_conflict_reduction",
        "echosat_cpu_reduction",
        "echosat_search_reward",
        "echosat_symmetry_reward",
        "echosat_random_control_penalty",
        "echosat_direction_consistency_penalty",
        "echosat_near_cap_penalty",
        "echosat_static_weighted_risk_raw",
        "echosat_r_search_decisions",
        "echosat_r_search_conflicts",
        "echosat_r_cpu_clipped",
        "echosat_search_blowup_penalty",
        "echosat_weighted_path_risk_penalty",
        "echosat_large_weight_phase_shift_penalty",
        "echosat_group_mixed_direction",
        "echosat_hard_negative_candidate",
        "echosat_hard_negative_penalty",
        "echosat_hard_negative_failure",
        "echosat_anchor_candidate",
        "echosat_anchor_failure",
        "echosat_anchor_failure_penalty",
        "echosat_subset_failure_candidate",
        "echosat_subset_failure_penalty",
        "echosat_pair_rank_penalty",
        "echosat_search_ok",
        "echosat_search_blowup",
        "echosat_positive_allowed_search",
        "echosat_positive_allowed",
        "echosat_positive_blocked_control",
        "echosat_positive_blocked_subset_failure",
        "echosat_positive_blocked_weighted_risk",
        "echosat_positive_blocked_near_cap",
        "echosat_positive_blocked_pair_inconsistency",
        "echosat_positive_blocked_anchor_failure",
        "echosat_positive_blocked_hard_negative_failure",
        "echosat_v18_blocked_positive_signal",
        "echosat_v18_cpu_only_search_bad",
        "echosat_v18_weighted_risk_blocked",
        "echosat_v18_near_cap_blocked",
        "echosat_v18_unclamped_positive_blocked",
        "echosat_v18_hard_negative_pressure",
        "echosat_event_nonzero_vars",
        "echosat_graph_gate_evidence_proxy",
        "grpo_raw_advantage",
        "grpo_weighted_advantage_before_clamp",
        "grpo_final_advantage",
        "grpo_positive_raw_advantage_clamped",
        "grpo_positive_advantage_clamped",
    ]:
        if key in solver_stats.columns:
            metrics[f"{prefix}/{key}"] = solver_stats[key].mean()

    wandb.log(metrics, step=global_step)


def solved_mask(solver_stats: pd.DataFrame) -> pd.Series:
    if "Result" not in solver_stats.columns:
        return pd.Series(False, index=solver_stats.index)
    return solver_stats["Result"].astype(str).isin({"SATISFIABLE", "UNSATISFIABLE"})


def add_composite_target(solver_stats: pd.DataFrame, cfg: DictConfig) -> pd.DataFrame:
    if str(cfg.training.target_stat) not in COMPOSITE_TARGETS:
        return solver_stats

    solver_stats = solver_stats.copy()

    def stat_values(column: str) -> np.ndarray:
        if column not in solver_stats.columns:
            return np.zeros(len(solver_stats), dtype=np.float64)
        values = pd.to_numeric(solver_stats[column], errors="coerce")
        fill_value = values.max()
        if pd.isna(fill_value):
            fill_value = 0.0
        return values.fillna(fill_value).to_numpy(dtype=np.float64)

    composite = np.zeros(len(solver_stats), dtype=np.float64)
    composite += float(cfg.training.composite_cpu_weight) * np.log1p(stat_values("CPU time"))
    composite += float(cfg.training.composite_conflicts_weight) * np.log1p(stat_values("conflicts"))
    composite += float(cfg.training.composite_decisions_weight) * np.log1p(stat_values("decisions"))
    if "composite_unsolved_penalty" in cfg.training:
        composite += float(cfg.training.composite_unsolved_penalty) * (~solved_mask(solver_stats)).to_numpy()
    solver_stats["composite"] = composite
    return solver_stats


def uses_speedup_target(cfg: DictConfig) -> bool:
    return str(cfg.training.target_stat) in SPEEDUP_TARGETS


def uses_echosat_target(cfg: DictConfig) -> bool:
    return str(cfg.training.target_stat) in ECHOSAT_TARGETS


def best_checkpoint_mode(cfg: DictConfig) -> str:
    return str(cfg_get(cfg.training, "best_checkpoint_metric", "target_stat_mean")).lower()


def bounded_log_ratio(
        value: np.ndarray,
        baseline: np.ndarray,
        eps: float,
        clip: float,
) -> np.ndarray:
    ratio = np.log((np.maximum(value, 0.0) + eps) / (np.maximum(baseline, 0.0) + eps))
    return np.clip(ratio, -float(clip), float(clip))


def numeric_stat(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=np.float64)
    values = pd.to_numeric(frame[column], errors="coerce")
    fill_value = values.max()
    if pd.isna(fill_value):
        fill_value = default
    return values.fillna(fill_value).astype(np.float64)


def numeric_column(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=np.float64)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(np.float64)


def bool_column(frame: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=bool)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(default).astype(bool)
    numeric = pd.to_numeric(values, errors="coerce")
    text = values.where(values.notna(), default).astype(str).str.strip().str.lower()
    return (numeric.notna() & numeric.ne(0.0)) | text.isin({"true", "t", "1", "yes", "y"})


def strict_search_work_validation_score(solver_stats: pd.DataFrame, cfg: DictConfig) -> tuple[float, dict[str, float]]:
    if solver_stats.empty:
        return float("-inf"), {}
    frame = solver_stats.copy()
    search_ok = bool_column(frame, "echosat_search_ok")
    search_blowup = bool_column(frame, "echosat_search_blowup")
    family = frame.get("family", pd.Series("", index=frame.index)).fillna("").astype(str)
    base = frame.get("base_instance_id", pd.Series("", index=frame.index)).fillna("").astype(str)
    control_type = frame.get("control_type", pd.Series("", index=frame.index)).fillna("").astype(str)
    symmetry_strength = frame.get("symmetry_strength", pd.Series("", index=frame.index)).fillna("").astype(str)
    random_control = family.eq("random_3sat_control") | control_type.eq("non_symmetric_control")
    strong = symmetry_strength.eq("strong")

    anchor_bases = list(cfg_get(cfg.training, "best_checkpoint_anchor_base_ids", ["k9_color8", "php_p9_h8"]))
    hard_bases = list(cfg_get(cfg.training, "best_checkpoint_hard_recovery_base_ids", ["k10_color9", "php_p10_h9"]))
    subset_base = str(cfg_get(cfg.training, "best_checkpoint_subset_failure_base_id", "subset_cardinality_bw12"))
    subset_variant = str(cfg_get(cfg.training, "best_checkpoint_subset_failure_variant", "perm_seed1730"))
    variant = frame.get("variant", pd.Series("", index=frame.index)).fillna("").astype(str)

    def base_frac(base_id: str) -> float:
        rows = search_ok[base.eq(str(base_id))]
        return float(rows.mean()) if len(rows) else 0.0

    anchor_values = [base_frac(base_id) for base_id in anchor_bases]
    hard_values = [base_frac(base_id) for base_id in hard_bases]
    anchor_min = min(anchor_values) if anchor_values else 0.0
    hard_min = min(hard_values) if hard_values else 0.0
    random_ok = float(search_ok[random_control].mean()) if bool(random_control.any()) else 0.0
    strong_ok = float(search_ok[strong].mean()) if bool(strong.any()) else 0.0
    subset_rows = search_ok[base.eq(subset_base) & variant.eq(subset_variant)]
    subset_ok = float(subset_rows.mean()) if len(subset_rows) else 0.0
    blowup = float(search_blowup.mean()) if len(search_blowup) else 0.0

    score = 0.0
    score += float(cfg_get(cfg.training, "best_checkpoint_anchor_weight", 3.0)) * anchor_min
    score += float(cfg_get(cfg.training, "best_checkpoint_hard_recovery_weight", 2.0)) * hard_min
    score += float(cfg_get(cfg.training, "best_checkpoint_strong_symmetry_weight", 1.0)) * strong_ok
    score -= float(cfg_get(cfg.training, "best_checkpoint_random_control_penalty_weight", 2.0)) * random_ok
    score -= float(cfg_get(cfg.training, "best_checkpoint_subset_failure_penalty_weight", 1.0)) * subset_ok
    score -= float(cfg_get(cfg.training, "best_checkpoint_search_blowup_penalty_weight", 1.0)) * blowup

    mismatch = bool_column(frame, "echosat_result_mismatch")
    unsolved = ~solved_mask(frame)
    score -= float(cfg_get(cfg.training, "best_checkpoint_result_mismatch_penalty", 20.0)) * float(mismatch.mean())
    score -= float(cfg_get(cfg.training, "best_checkpoint_unsolved_penalty", 8.0)) * float(unsolved.mean())

    metrics = {
        "strict_search_work_score": float(score),
        "anchor_min_search_ok_frac": float(anchor_min),
        "hard_recovery_min_search_ok_frac": float(hard_min),
        "strong_symmetry_search_ok_frac": float(strong_ok),
        "random_control_search_ok_frac": float(random_ok),
        "subset_failure_search_ok_frac": float(subset_ok),
        "search_blowup_frac": float(blowup),
    }
    return float(score), metrics


def strict_search_work_validation_score_v2(solver_stats: pd.DataFrame, cfg: DictConfig) -> tuple[float, dict[str, float]]:
    score, metrics = strict_search_work_validation_score(solver_stats, cfg)
    if not metrics:
        return score, metrics

    anchor_min = float(metrics.get("anchor_min_search_ok_frac", 0.0))
    hard_min = float(metrics.get("hard_recovery_min_search_ok_frac", 0.0))
    random_ok = float(metrics.get("random_control_search_ok_frac", 0.0))
    subset_ok = float(metrics.get("subset_failure_search_ok_frac", 0.0))
    blowup = float(metrics.get("search_blowup_frac", 0.0))

    anchor_required = float(cfg_get(cfg.training, "best_checkpoint_anchor_required_min", 1.0))
    hard_required = float(cfg_get(cfg.training, "best_checkpoint_hard_recovery_required_min", 2.0 / 3.0))
    random_max = float(cfg_get(cfg.training, "best_checkpoint_random_control_max", 0.05))
    subset_max = float(cfg_get(cfg.training, "best_checkpoint_subset_failure_max", 0.0))
    blowup_max = float(cfg_get(cfg.training, "best_checkpoint_search_blowup_max", 1.0))
    gate_penalty_weight = float(cfg_get(cfg.training, "best_checkpoint_gate_penalty_weight", 100.0))

    anchor_shortfall = max(anchor_required - anchor_min, 0.0)
    hard_shortfall = max(hard_required - hard_min, 0.0)
    random_excess = max(random_ok - random_max, 0.0)
    subset_excess = max(subset_ok - subset_max, 0.0)
    blowup_excess = max(blowup - blowup_max, 0.0)
    gate_violation = anchor_shortfall + hard_shortfall + random_excess + subset_excess + blowup_excess
    gate_penalty = gate_penalty_weight * gate_violation
    gated_score = score - gate_penalty

    gate_pass = gate_violation <= 1.0e-12
    metrics.update(
        {
            "strict_search_work_v2_score": float(gated_score),
            "best_checkpoint_gate_pass": float(gate_pass),
            "best_checkpoint_gate_violation": float(gate_violation),
            "best_checkpoint_gate_penalty": float(gate_penalty),
            "best_checkpoint_anchor_shortfall": float(anchor_shortfall),
            "best_checkpoint_hard_recovery_shortfall": float(hard_shortfall),
            "best_checkpoint_random_control_excess": float(random_excess),
            "best_checkpoint_subset_failure_excess": float(subset_excess),
            "best_checkpoint_search_blowup_excess": float(blowup_excess),
            "best_checkpoint_anchor_required_min": float(anchor_required),
            "best_checkpoint_hard_recovery_required_min": float(hard_required),
            "best_checkpoint_random_control_max": float(random_max),
            "best_checkpoint_subset_failure_max": float(subset_max),
            "best_checkpoint_search_blowup_max": float(blowup_max),
        }
    )
    return float(gated_score), metrics


def resolve_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def resolve_manifest_artifact_path(
        path: str | Path,
        legacy_root_exists_cache: dict[str, bool] | None = None,
) -> Path:
    artifact_path = Path(path)
    project_root = PROJECT_ROOT.resolve()
    if not artifact_path.is_absolute():
        if ".." in artifact_path.parts:
            raise ValueError(f"manifest artifact relative path may not contain '..': {path}")
        candidate = (project_root / artifact_path).resolve(strict=False)
        if not candidate.is_relative_to(project_root):
            raise ValueError(f"manifest artifact path escapes PROJECT_ROOT: {path}")
        return candidate

    normalized = Path(os.path.normpath(os.fspath(artifact_path)))
    if ".." in artifact_path.parts:
        return normalized

    anchor_indexes = [
        index
        for index, part in enumerate(artifact_path.parts)
        if part in {"data", "runs"}
    ]
    if len(anchor_indexes) != 1:
        return normalized
    anchor_index = anchor_indexes[0]
    candidate = (project_root / Path(*artifact_path.parts[anchor_index:])).resolve(strict=False)
    if not candidate.is_relative_to(project_root) or not candidate.is_file():
        return normalized
    legacy_root = Path(*artifact_path.parts[:anchor_index])
    cache = {} if legacy_root_exists_cache is None else legacy_root_exists_cache
    cache_key = str(legacy_root)
    legacy_root_exists = cache.get(cache_key)
    if legacy_root_exists is None:
        legacy_root_exists = legacy_root.exists()
        cache[cache_key] = legacy_root_exists
    if legacy_root_exists and artifact_path.is_file():
        return artifact_path.resolve(strict=True)
    return candidate


def read_bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values
    return values.fillna(False).astype(str).str.lower().isin({"true", "1", "yes", "y"})


def load_orbit_certification_summary(path: str | Path | None) -> pd.DataFrame:
    if path is None or str(path) == "":
        return pd.DataFrame()
    cert_path = resolve_path(path)
    if not cert_path.exists():
        return pd.DataFrame()
    cert = pd.read_csv(cert_path)
    if cert.empty:
        return pd.DataFrame()
    required_columns = {"cnf_path", "valid_for_training"}
    missing_columns = sorted(required_columns.difference(cert.columns))
    if missing_columns:
        raise ValueError(
            "EchoSAT orbit certification missing required columns: "
            f"{missing_columns}"
        )
    cert = cert.copy()
    invalid_paths = cert["cnf_path"].isna() | cert["cnf_path"].astype(str).str.strip().eq("")
    if invalid_paths.any():
        raise ValueError("EchoSAT orbit certification cnf_path must be non-empty")
    cert["valid_for_training"] = read_bool_series(cert["valid_for_training"])
    valid_mask = cert["valid_for_training"]
    valid_required_columns = {"orbit_id", "orbit_size", "orbit_confidence"}
    missing_valid_columns = sorted(valid_required_columns.difference(cert.columns))
    if valid_mask.any() and missing_valid_columns:
        raise ValueError(
            "EchoSAT orbit certification declared-valid rows require columns: "
            f"{missing_valid_columns}"
        )
    if valid_mask.any():
        valid_orbit_ids = cert.loc[valid_mask, "orbit_id"]
        invalid_orbit_ids = (
            valid_orbit_ids.isna()
            | valid_orbit_ids.astype(str).str.strip().eq("")
        )
        if invalid_orbit_ids.any():
            raise ValueError(
                "EchoSAT orbit certification declared-valid orbit_id must be non-empty"
            )
        valid_orbit_sizes = pd.to_numeric(
            cert.loc[valid_mask, "orbit_size"], errors="coerce"
        )
        if (~np.isfinite(valid_orbit_sizes) | valid_orbit_sizes.lt(0)).any():
            raise ValueError(
                "EchoSAT orbit certification declared-valid orbit_size must be finite and nonnegative"
            )
        valid_orbit_confidence = pd.to_numeric(
            cert.loc[valid_mask, "orbit_confidence"], errors="coerce"
        )
        if (
            ~np.isfinite(valid_orbit_confidence)
            | valid_orbit_confidence.lt(0)
            | valid_orbit_confidence.gt(1)
        ).any():
            raise ValueError(
                "EchoSAT orbit certification declared-valid orbit_confidence must be finite and within [0, 1]"
            )
        cert.loc[valid_mask, "orbit_size"] = valid_orbit_sizes
        cert.loc[valid_mask, "orbit_confidence"] = valid_orbit_confidence
    legacy_root_exists_cache: dict[str, bool] = {}
    cert["cnf_path_resolved"] = cert["cnf_path"].map(
        lambda value: str(
            resolve_manifest_artifact_path(str(value), legacy_root_exists_cache)
        )
    )
    if valid_mask.any():
        duplicate_valid_orbits = cert.loc[valid_mask].duplicated(
            ["cnf_path_resolved", "orbit_id"], keep=False
        )
        if duplicate_valid_orbits.any():
            raise ValueError(
                "EchoSAT orbit certification has duplicate declared-valid orbit keys"
            )
    valid = cert[cert["valid_for_training"]].copy()
    all_paths = pd.DataFrame(
        {"cnf_path_resolved": sorted(cert["cnf_path_resolved"].unique())}
    )
    if valid.empty:
        valid_summary = pd.DataFrame(
            columns=[
                "cnf_path_resolved",
                "valid_orbit_count",
                "valid_orbit_vars",
                "orbit_confidence_mean",
                "orbit_confidence_max",
            ]
        )
    else:
        valid_summary = (
            valid.groupby("cnf_path_resolved", sort=True)
            .agg(
                valid_orbit_count=("orbit_id", "nunique"),
                valid_orbit_vars=("orbit_size", "sum"),
                orbit_confidence_mean=("orbit_confidence", "mean"),
                orbit_confidence_max=("orbit_confidence", "max"),
            )
            .reset_index()
        )
    summary = all_paths.merge(
        valid_summary,
        on="cnf_path_resolved",
        how="left",
        sort=True,
        validate="one_to_one",
    )
    summary["valid_orbit_count"] = pd.to_numeric(
        summary["valid_orbit_count"], errors="coerce"
    ).fillna(0).astype(np.int64)
    for column in ["valid_orbit_vars", "orbit_confidence_mean", "orbit_confidence_max"]:
        summary[column] = pd.to_numeric(summary[column], errors="coerce").fillna(0.0)
    return summary


def load_training_manifest(cfg: DictConfig) -> pd.DataFrame:
    manifest_path = str(cfg_get(cfg.training, "echosat_manifest_path", ""))
    if not manifest_path:
        if uses_echosat_target(cfg):
            raise ValueError("echosat_cost requires training.echosat_manifest_path")
        return pd.DataFrame()
    path = resolve_path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"EchoSAT manifest not found: {path}")
    manifest = load_manifest_from_path(path)
    cert = load_orbit_certification_summary(cfg_get(cfg.training, "echosat_orbit_certification_path", ""))
    if not cert.empty and "cnf_path_resolved" in manifest.columns:
        if cert.duplicated("cnf_path_resolved").any():
            duplicates = sorted(
                cert.loc[cert.duplicated("cnf_path_resolved", keep=False), "cnf_path_resolved"]
                .astype(str)
                .unique()
                .tolist()
            )
            raise ValueError(
                "EchoSAT orbit certification summary has duplicate cnf_path_resolved: "
                f"{duplicates[:5]}"
            )
        orbit_columns = [
            "valid_orbit_count",
            "valid_orbit_vars",
            "orbit_confidence_mean",
            "orbit_confidence_max",
        ]
        present_cert_columns = [column for column in orbit_columns if column in cert.columns]
        cert_columns = cert[["cnf_path_resolved", *present_cert_columns]].rename(
            columns={column: f"__cert_{column}" for column in present_cert_columns}
        )
        manifest = manifest.merge(
            cert_columns,
            on="cnf_path_resolved",
            how="left",
            sort=False,
            validate="many_to_one",
        )
        for column in present_cert_columns:
            cert_column = f"__cert_{column}"
            if column not in manifest.columns:
                manifest[column] = np.nan
            manifest[column] = manifest[cert_column].where(
                manifest[cert_column].notna(),
                manifest[column],
            )
            manifest = manifest.drop(columns=cert_column)
    return manifest


def dataset_metadata(dataset: DimacsCNFDataset, manifest: pd.DataFrame, *, required: bool) -> pd.DataFrame:
    if manifest.empty:
        if required:
            raise ValueError("EchoSAT metadata requested but manifest is empty")
        return pd.DataFrame({"cnf_id": list(dataset.id_to_file.keys())})

    lookup: dict[str, pd.Series] = {}
    for _, row in manifest.iterrows():
        for column in ["cnf_path_resolved", "split_cnf_path_resolved"]:
            value = str(row.get(column, ""))
            if value:
                lookup[value] = row

    rows = []
    missing = []
    metadata_columns = [
        "family",
        "instance_id",
        "base_instance_id",
        "variant",
        "num_vars",
        "expected_result",
        "control_type",
        "symmetry_strength",
        "scale",
        "benchmark_role",
        "family_scale",
        "permutation_variant",
        "event_audit_role",
        "valid_orbit_count",
        "valid_orbit_vars",
        "orbit_confidence_mean",
        "orbit_confidence_max",
        "formula_equivalence_group",
        "echosat_sampling_group_id",
        "training_priority",
        "canonical_order_training_v1",
        "orbits_path_resolved",
        "metadata_path_resolved",
    ]
    for cnf_id, file_name in dataset.id_to_file.items():
        resolved = str(Path(file_name).resolve())
        row = lookup.get(resolved)
        if row is None:
            missing.append(resolved)
            out = {"cnf_id": int(cnf_id), "cnf_path_resolved": resolved}
        else:
            out = {"cnf_id": int(cnf_id), "cnf_path_resolved": resolved}
            for column in metadata_columns:
                if column in row.index:
                    out[column] = row[column]
        rows.append(out)
    if missing and required:
        raise ValueError(f"EchoSAT manifest does not cover dataset files, first missing: {missing[:5]}")
    meta = pd.DataFrame(rows)
    if "permutation_variant" in meta.columns:
        meta["permutation_variant"] = read_bool_series(meta["permutation_variant"])
    return meta


def load_echosat_v2_orbit_store(
        cfg: DictConfig,
        metadata: pd.DataFrame,
) -> OrbitFeatureStore | None:
    path_value = str(cfg_get(cfg.training, "echosat_orbit_variable_path", "")).strip()
    if not path_value:
        return None
    path = resolve_path(path_value)
    if not path.exists():
        raise FileNotFoundError(f"EchoSAT v2 orbit variable table not found: {path}")
    variable_rows = pd.read_csv(path)
    required_keys = {"base_instance_id", "variant"}
    missing_metadata = sorted(required_keys.difference(metadata.columns))
    if missing_metadata:
        raise ValueError(f"dataset metadata missing required columns: {missing_metadata}")
    missing_variables = sorted(required_keys.difference(variable_rows.columns))
    if missing_variables:
        raise ValueError(f"variable_rows missing required columns: {missing_variables}")
    metadata_keys = set(
        metadata[["base_instance_id", "variant"]].itertuples(index=False, name=None)
    )
    variable_keys = set(
        variable_rows[["base_instance_id", "variant"]].itertuples(index=False, name=None)
    )
    uncovered_keys = metadata_keys.difference(variable_keys)
    if uncovered_keys:
        raise ValueError(
            "EchoSAT v2 orbit variable table has uncovered dataset metadata keys: "
            f"{sorted(uncovered_keys, key=repr)}"
        )
    row_keys = pd.MultiIndex.from_frame(variable_rows[["base_instance_id", "variant"]])
    selected_rows = variable_rows.loc[row_keys.isin(pd.MultiIndex.from_tuples(metadata_keys))].copy()
    return OrbitFeatureStore.from_tables(selected_rows, metadata)


def dataset_path_from_config(value):
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    value_str = str(value)
    if value_str.startswith("@"):
        list_path = resolve_path(value_str[1:])
        if not list_path.exists():
            raise FileNotFoundError(f"DIMACS file list not found: {list_path}")
        legacy_root_exists_cache: dict[str, bool] = {}
        files = [
            str(resolve_manifest_artifact_path(line.strip(), legacy_root_exists_cache))
            for line in list_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not files:
            raise ValueError(f"DIMACS file list is empty: {list_path}")
        return files
    return value_str


def load_manifest_from_path(path_value: str | Path) -> pd.DataFrame:
    path = resolve_path(path_value)
    if not path.exists():
        raise FileNotFoundError(f"EchoSAT manifest not found: {path}")
    manifest = pd.read_csv(path)
    if manifest.empty:
        raise ValueError(f"EchoSAT manifest is empty: {path}")
    manifest = manifest.copy()
    legacy_root_exists_cache: dict[str, bool] = {}
    for column in ["cnf_path", "split_cnf_path", "orbits_path", "metadata_path"]:
        if column in manifest.columns:
            manifest[f"{column}_resolved"] = manifest[column].fillna("").astype(str).map(
                lambda value: str(
                    resolve_manifest_artifact_path(value, legacy_root_exists_cache)
                ) if value else ""
            )
    for column, default in [
        ("valid_orbit_count", 0),
        ("valid_orbit_vars", 0.0),
        ("orbit_confidence_mean", np.nan),
        ("orbit_confidence_max", np.nan),
    ]:
        if column not in manifest.columns:
            manifest[column] = default
    strength_confidence = {
        "strong": 1.0,
        "weak": 0.6,
        "pseudo": 0.3,
        "none": 0.0,
    }
    fallback_conf = manifest.get("symmetry_strength", pd.Series("", index=manifest.index)).astype(str).map(strength_confidence).fillna(0.2)
    manifest["orbit_confidence_mean"] = pd.to_numeric(manifest["orbit_confidence_mean"], errors="coerce").fillna(fallback_conf)
    manifest["orbit_confidence_max"] = pd.to_numeric(manifest["orbit_confidence_max"], errors="coerce").fillna(fallback_conf)
    return manifest


def build_base_group_iteration_loader(
        dataset: DimacsCNFDataset,
        metadata: pd.DataFrame,
        cfg: DictConfig,
        iteration: int,
) -> tuple[DataLoader, int]:
    group_column = str(cfg_get(cfg.training, "echosat_group_column", "base_instance_id"))
    if group_column not in metadata.columns:
        group_column = "base_instance_id"
    if metadata.empty or group_column not in metadata.columns:
        raise ValueError(f"base-group sampling requires EchoSAT metadata with {group_column}")
    group_count = int(cfg_get(cfg.training, "echosat_base_groups_per_iter", 3))
    control_count = int(cfg_get(cfg.training, "echosat_control_base_groups_per_iter", 1))
    priority_count = int(cfg_get(cfg.training, "echosat_priority_groups_per_iter", 0))
    if group_count <= 0:
        raise ValueError("training.echosat_base_groups_per_iter must be positive")
    control_count = max(0, min(control_count, group_count))
    priority_count = max(0, min(priority_count, group_count - control_count))

    meta = metadata.copy()
    meta[group_column] = meta[group_column].fillna("").astype(str)
    meta = meta[meta[group_column] != ""].copy()
    if meta.empty:
        raise ValueError(f"base-group sampling found no non-empty {group_column} rows")
    meta["control_type"] = meta.get("control_type", pd.Series("", index=meta.index)).fillna("").astype(str)
    meta["training_priority"] = pd.to_numeric(
        meta.get("training_priority", pd.Series(0.0, index=meta.index)),
        errors="coerce",
    ).fillna(0.0)

    base_control = (
        meta.groupby(group_column, sort=True)["control_type"]
        .apply(lambda values: bool(values.astype(str).eq("non_symmetric_control").any()))
    )
    base_priority = meta.groupby(group_column, sort=True)["training_priority"].max().reindex(base_control.index).fillna(0.0)
    control_bases = list(base_control[base_control].index)
    priority_bases = list(base_priority[(~base_control) & (base_priority > 0.0)].index)
    symmetry_bases = list(base_control[(~base_control) & ~(base_priority > 0.0)].index)
    all_bases = list(base_control.index)

    seed = int(cfg_get(cfg.training, "echosat_base_group_seed", cfg_get(cfg, "seed", 0)))
    rng = np.random.default_rng(seed + int(iteration))

    def choose(values: list[str], count: int) -> list[str]:
        if count <= 0 or not values:
            return []
        count = min(count, len(values))
        return list(rng.choice(np.asarray(values, dtype=object), size=count, replace=False))

    selected = choose(control_bases, control_count)
    selected += choose([base for base in priority_bases if base not in set(selected)], priority_count)
    selected += choose([base for base in symmetry_bases if base not in set(selected)], group_count - len(selected))
    if len(selected) < group_count:
        remaining = [base for base in all_bases if base not in set(selected)]
        selected += choose(remaining, group_count - len(selected))
    if not selected:
        raise ValueError("base-group sampling selected no bases")

    selected_set = set(map(str, selected))
    indices = (
        meta[meta[group_column].isin(selected_set)]["cnf_id"]
        .astype(int)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    if not indices:
        raise ValueError(f"base-group sampling selected bases without CNF rows: {selected}")
    print(f"Iteration {iteration}: selected {len(selected)} {group_column} groups / {len(indices)} CNFs")
    subset = Subset(dataset, indices)
    loader = DataLoader(
        dataset=subset,
        batch_size=int(cfg.loader.batch_size),
        num_workers=int(cfg.loader.num_workers),
        shuffle=True,
    )
    return loader, -1


def build_speedup_baseline_data_list(data_list: list, cfg: DictConfig) -> list | None:
    mode = str(cfg_get(cfg.training, "speedup_baseline", "neutral_weighted"))
    if mode == "none":
        return None
    if mode != "neutral_weighted":
        raise ValueError(f"Unsupported speedup_baseline={mode!r}")

    weight = float(cfg_get(cfg.training, "speedup_baseline_weight", 1.0))
    baseline = []
    for data in data_list:
        item = data.clone()
        num_vars = int(getattr(item["var"], "num_nodes", item["lit"].num_nodes // 2))
        item["var"].num_nodes = num_vars
        item["var"].var_params = torch.from_numpy(
            neutral_var_params(num_vars, weight=weight)
        ).unsqueeze(1)
        if hasattr(item, "log_prob"):
            delattr(item, "log_prob")
        baseline.append(item)
    return baseline


def strip_event_state_data_list(data_list: list) -> list:
    stripped = []
    for data in data_list:
        item = data.clone()
        for attr in ["event_state", "event_memory", "base_embedding", "base_y"]:
            if hasattr(item["var"], attr):
                delattr(item["var"], attr)
        for attr in ["log_prob", "gpu_time"]:
            if hasattr(item, attr):
                delattr(item, attr)
        stripped.append(item)
    return stripped


def build_static_baseline_data_list(
        model: GNN,
        data_list: list,
        cfg: DictConfig,
        device: torch.device | str,
) -> list:
    stripped = strip_event_state_data_list(data_list)
    loader = DataLoader(
        dataset=stripped,
        batch_size=cfg.loader.batch_size,
        num_workers=cfg.loader.num_workers,
        shuffle=False,
    )
    return sample_var_params(
        model=model,
        loader=loader,
        num_samples=1,
        device=device,
        use_mode=True,
        scale_sigma=cfg.scale_sigma,
    )


def data_list_param_diagnostics(data_list: list, static_data_list: list | None) -> pd.DataFrame:
    static_params_by_cnf: dict[int, np.ndarray] = {}
    for data in static_data_list or []:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        params = data["var"].var_params.detach().cpu().numpy()
        if params.ndim == 3:
            params = params[:, 0, :]
        static_params_by_cnf[cnf_id] = params

    rows = []
    for data in data_list:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        params_all = data["var"].var_params.detach().cpu().numpy()
        if params_all.ndim == 2:
            params_all = params_all[:, None, :]
        num_vars = int(params_all.shape[0])
        static_params = static_params_by_cnf.get(cnf_id)
        if static_params is None or static_params.shape[0] != num_vars:
            static_params = np.stack([np.ones(num_vars, dtype=np.float64), np.ones(num_vars, dtype=np.float64)], axis=1)
        event_state = getattr(data["var"], "event_state", None)
        if event_state is None:
            event_l2_sum = 0.0
            event_l2_max = 0.0
            event_nonzero = 0
        else:
            event_l2 = event_state.detach().cpu().to(dtype=torch.float32).norm(dim=1).numpy().astype(np.float64)
            event_l2_sum = float(event_l2.sum())
            event_l2_max = float(event_l2.max()) if event_l2.size else 0.0
            event_nonzero = int((event_l2 > 1.0e-9).sum())
        warmup_cpu = float(getattr(data, "warmup_cpu_time", torch.tensor(0.0)))
        warmup_conflicts = float(getattr(data, "warmup_conflicts", torch.tensor(0.0)))
        warmup_decisions = float(getattr(data, "warmup_decisions", torch.tensor(0.0)))
        for sample_id in range(params_all.shape[1]):
            params = params_all[:, sample_id, :]
            phase_delta = params[:, 0] - static_params[:, 0]
            weight_delta = params[:, 1] - static_params[:, 1]
            static_weight = np.clip(static_params[:, 1], 1.0e-12, None)
            rank_corr = pd.Series(static_params[:, 1]).corr(pd.Series(params[:, 1]), method="spearman")
            if pd.isna(rank_corr):
                rank_corr = 1.0
            rows.append(
                {
                    "cnf_id": cnf_id,
                    "sample_id": sample_id,
                    "phase_flip_frac": float((np.abs(phase_delta) > 0.0).mean()) if num_vars else 0.0,
                    "weight_delta_abs_mean": float(np.abs(weight_delta).mean()) if num_vars else 0.0,
                    "weight_delta_abs_max": float(np.abs(weight_delta).max()) if num_vars else 0.0,
                    "weight_relative_abs_mean": float((np.abs(weight_delta) / static_weight).mean()) if num_vars else 0.0,
                    "weight_rank_change_penalty": float(max(0.0, 1.0 - float(rank_corr))),
                    "event_state_l2_sum_train": event_l2_sum,
                    "event_state_l2_max_train": event_l2_max,
                    "event_state_nonzero_vars_train": event_nonzero,
                    "warmup_cpu_time_train": warmup_cpu,
                    "warmup_conflicts_train": warmup_conflicts,
                    "warmup_decisions_train": warmup_decisions,
                }
            )
    return pd.DataFrame(rows)


def read_permutation_from_metadata(path: str | Path, expected_num_vars: int) -> list[int] | None:
    if not path or str(path) == "nan":
        return None
    try:
        with resolve_path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    permutation = payload.get("permutation")
    if not isinstance(permutation, list) or len(permutation) != int(expected_num_vars):
        return None
    try:
        return [int(value) for value in permutation]
    except (TypeError, ValueError):
        return None


def permutation_delta_penalties(
        data_list: list | None,
        static_data_list: list | None,
        metadata: pd.DataFrame | None,
) -> pd.DataFrame:
    if not data_list or static_data_list is None or metadata is None or metadata.empty:
        return pd.DataFrame(columns=["cnf_id", "sample_id", "echosat_perm_delta_penalty"])

    static_params_by_cnf: dict[int, np.ndarray] = {}
    for data in static_data_list:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        params = data["var"].var_params.detach().cpu().numpy()
        if params.ndim == 3:
            params = params[:, 0, :]
        static_params_by_cnf[cnf_id] = params

    meta_by_cnf = metadata.set_index("cnf_id").to_dict("index")
    delta_by_key: dict[tuple[str, str], tuple[int, np.ndarray, dict[str, Any]]] = {}
    for data in data_list:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        meta = meta_by_cnf.get(cnf_id, {})
        base = str(meta.get("base_instance_id", ""))
        variant = str(meta.get("variant", ""))
        if not base or not variant:
            continue
        params = data["var"].var_params.detach().cpu().numpy()
        if params.ndim == 2:
            params = params[:, None, :]
        static_params = static_params_by_cnf.get(cnf_id)
        if static_params is None or static_params.shape[0] != params.shape[0]:
            continue
        delta = params - static_params[:, None, :]
        delta_by_key[(base, variant)] = (cnf_id, delta, meta)

    rows = []
    for (base, variant), (cnf_id, delta, meta) in delta_by_key.items():
        if variant == "base":
            continue
        base_item = delta_by_key.get((base, "base"))
        if base_item is None:
            continue
        _, base_delta, _ = base_item
        if base_delta.shape != delta.shape:
            continue
        permutation = read_permutation_from_metadata(str(meta.get("metadata_path_resolved", "")), expected_num_vars=delta.shape[0])
        if permutation is None:
            continue
        indices = np.asarray([value - 1 for value in permutation], dtype=np.int64)
        if indices.min(initial=0) < 0 or indices.max(initial=-1) >= delta.shape[0]:
            continue
        aligned_perm_delta = delta[indices, :, :]
        per_sample = np.abs(aligned_perm_delta - base_delta).mean(axis=(0, 2))
        for sample_id, penalty in enumerate(per_sample):
            rows.append(
                {
                    "cnf_id": int(cnf_id),
                    "sample_id": int(sample_id),
                    "echosat_perm_delta_penalty": float(penalty),
                }
            )
    return pd.DataFrame(rows)


def baseline_values_for(
        baseline_stats_by_name: dict[str, pd.DataFrame],
        name: str,
        cnf_ids: np.ndarray,
        column: str,
        default: float = 0.0,
) -> np.ndarray:
    frame = baseline_stats_by_name.get(name)
    if frame is None or frame.empty or column not in frame.columns:
        return np.full(len(cnf_ids), default, dtype=np.float64)
    base = frame.sort_values(["cnf_id", "sample_id"], ascending=[True, True]).drop_duplicates("cnf_id").set_index("cnf_id")
    values = pd.to_numeric(base[column], errors="coerce")
    fill_value = values.max()
    if pd.isna(fill_value):
        fill_value = default
    return values.reindex(cnf_ids).fillna(fill_value).to_numpy(dtype=np.float64)


def add_echosat_target(
        solver_stats: pd.DataFrame,
        cfg: DictConfig,
        baseline_stats_by_name: dict[str, pd.DataFrame] | None,
        metadata: pd.DataFrame | None,
        data_list: list | None,
        static_data_list: list | None,
) -> pd.DataFrame:
    if not uses_echosat_target(cfg):
        return solver_stats
    baseline_stats_by_name = baseline_stats_by_name or {}
    if "static_weighted" not in baseline_stats_by_name:
        raise ValueError("echosat_cost requires static_weighted baseline stats")

    out = solver_stats.copy()
    if metadata is not None and not metadata.empty:
        meta_cols = [column for column in metadata.columns if column != "cnf_path_resolved"]
        out = out.merge(metadata[meta_cols], on="cnf_id", how="left")
    diagnostics = data_list_param_diagnostics(data_list or [], static_data_list)
    if not diagnostics.empty:
        out = out.merge(diagnostics, on=["cnf_id", "sample_id"], how="left")
    perm_penalties = permutation_delta_penalties(data_list, static_data_list, metadata)
    if not perm_penalties.empty:
        out = out.merge(perm_penalties, on=["cnf_id", "sample_id"], how="left")

    cnf_ids = out["cnf_id"].to_numpy()
    eps = float(cfg_get(cfg.training, "echosat_ratio_eps", 1.0e-6))
    clip = float(cfg_get(cfg.training, "echosat_delta_clip", 1.0))
    cpu = numeric_stat(out, "CPU time").to_numpy(dtype=np.float64)
    conflicts = numeric_stat(out, "conflicts").to_numpy(dtype=np.float64)
    decisions = numeric_stat(out, "decisions").to_numpy(dtype=np.float64)
    static_cpu = baseline_values_for(baseline_stats_by_name, "static_weighted", cnf_ids, "CPU time")
    static_conflicts = baseline_values_for(baseline_stats_by_name, "static_weighted", cnf_ids, "conflicts")
    static_decisions = baseline_values_for(baseline_stats_by_name, "static_weighted", cnf_ids, "decisions")
    neutral_cpu = baseline_values_for(baseline_stats_by_name, "neutral_weighted", cnf_ids, "CPU time", default=np.nan)
    target_mode = str(cfg_get(cfg.training, "echosat_target_mode", "full")).lower()
    if target_mode not in {
        "full",
        "adapter_delta",
        "symmetry_grpo_v1",
        "symmetry_grpo_v1_1",
        "symmetry_grpo_v1_2",
        "symmetry_grpo_v1_3",
        "symmetry_grpo_v1_4",
        "symmetry_grpo_v1_5",
        "symmetry_grpo_v1_6",
        "symmetry_grpo_v1_7",
        "symmetry_grpo_v1_8",
        "symmetry_grpo_v2",
    }:
        raise ValueError(f"Unsupported training.echosat_target_mode={target_mode!r}")

    final_cpu_cost = np.clip((cpu - static_cpu) / np.maximum(static_cpu, eps), -clip, clip)
    conflict_cost = np.clip((conflicts - static_conflicts) / np.maximum(static_conflicts, 1.0), -clip, clip)
    decision_cost = np.clip((decisions - static_decisions) / np.maximum(static_decisions, 1.0), -clip, clip)
    search_cost = (
        float(cfg_get(cfg.training, "echosat_decisions_weight", 0.4)) * decision_cost
        + float(cfg_get(cfg.training, "echosat_conflicts_weight", 0.6)) * conflict_cost
    )

    control_type = out.get("control_type", pd.Series("", index=out.index)).fillna("").astype(str)
    symmetry_strength = out.get("symmetry_strength", pd.Series("", index=out.index)).fillna("").astype(str)
    family = out.get("family", pd.Series("", index=out.index)).fillna("").astype(str)
    is_control = control_type.eq("non_symmetric_control") | symmetry_strength.eq("none") | family.eq("random_3sat_control")
    valid_orbits = numeric_column(out, "valid_orbit_count", 0.0).to_numpy(dtype=np.float64)
    orbit_conf = numeric_column(out, "orbit_confidence_mean", 0.0).to_numpy(dtype=np.float64)
    event_l2 = numeric_column(out, "event_state_l2_sum_train", 0.0).to_numpy(dtype=np.float64)
    event_nonzero = numeric_column(out, "event_state_nonzero_vars_train", 0.0).to_numpy(dtype=np.float64)
    graph_gate_evidence = np.log1p(event_nonzero)
    tau_event = float(cfg_get(cfg.training, "echosat_event_tau", 0.0))
    event_gate = 1.0 / (1.0 + np.exp(-(np.log1p(event_l2) - tau_event)))
    explicit_event_gate = ((event_l2 > 0.0) | (event_nonzero > 0.0)).astype(np.float64)
    e_sym = (~is_control).to_numpy(dtype=np.float64) * (valid_orbits > 0.0).astype(np.float64) * orbit_conf * event_gate * explicit_event_gate
    e_sym = np.clip(e_sym, 0.0, 1.0)

    phase_flip = numeric_column(out, "phase_flip_frac", 0.0).to_numpy(dtype=np.float64)
    weight_delta = numeric_column(out, "weight_relative_abs_mean", 0.0).to_numpy(dtype=np.float64)
    rank_change = numeric_column(out, "weight_rank_change_penalty", 0.0).to_numpy(dtype=np.float64)
    perturbation = (
        float(cfg_get(cfg.training, "echosat_control_weight_delta_weight", 1.0)) * weight_delta
        + float(cfg_get(cfg.training, "echosat_control_phase_flip_weight", 1.0)) * phase_flip
        + float(cfg_get(cfg.training, "echosat_control_rank_change_weight", 0.5)) * rank_change
    )
    perm_delta_penalty = numeric_column(out, "echosat_perm_delta_penalty", 0.0).to_numpy(dtype=np.float64)

    cap = float(dict(cfg.solver.params).get("cpu-lim", cfg_get(cfg.training, "echosat_cpu_cap", 5.0)))
    static_threshold = float(cfg_get(cfg.training, "echosat_static_risk_threshold", 0.1))
    if np.all(np.isnan(neutral_cpu)):
        static_weighted_risk = np.zeros(len(out), dtype=np.float64)
    else:
        static_weighted_risk = np.maximum(0.0, ((static_cpu - neutral_cpu) / np.maximum(neutral_cpu, eps)) - static_threshold)
    near_cap = np.maximum.reduce(
        [
            cpu / max(cap, eps),
            static_cpu / max(cap, eps),
            np.nan_to_num(neutral_cpu / max(cap, eps), nan=0.0),
        ]
    )
    cap_risk = np.maximum(0.0, near_cap - float(cfg_get(cfg.training, "echosat_near_cap_fraction", 0.8)))
    weighted_risk = static_weighted_risk + cap_risk

    warmup_cpu = numeric_column(out, "warmup_cpu_time_train", 0.0).to_numpy(dtype=np.float64)
    overhead = np.clip(warmup_cpu / np.maximum(static_cpu, eps), 0.0, 1.0)

    known_expected = out.get("expected_result", pd.Series("UNKNOWN", index=out.index)).astype(str).isin({"SATISFIABLE", "UNSATISFIABLE"})
    result = out.get("Result", pd.Series("", index=out.index)).astype(str)
    expected = out.get("expected_result", pd.Series("UNKNOWN", index=out.index)).astype(str)
    solved = solved_mask(out).to_numpy(dtype=bool)
    result_mismatch = known_expected.to_numpy(dtype=bool) & solved & (result.to_numpy() != expected.to_numpy())

    mechanism_cost = (
        float(cfg_get(cfg.training, "echosat_final_cpu_weight", 0.4)) * final_cpu_cost
        + float(cfg_get(cfg.training, "echosat_search_weight", 1.0)) * search_cost
    )
    sym_mask = (~is_control).to_numpy(dtype=np.float64)
    control_mask = is_control.to_numpy(dtype=np.float64)
    cost = np.zeros(len(out), dtype=np.float64)
    cost += sym_mask * float(cfg_get(cfg.training, "echosat_sym_weight", 1.0)) * e_sym * mechanism_cost
    cost += control_mask * float(cfg_get(cfg.training, "echosat_portfolio_weight", 0.15)) * final_cpu_cost
    cost += float(cfg_get(cfg.training, "echosat_overhead_weight", 0.2)) * overhead
    cost += float(cfg_get(cfg.training, "echosat_weighted_risk_weight", 0.5)) * weighted_risk * (1.0 + perturbation)
    cost += control_mask * float(cfg_get(cfg.training, "echosat_control_penalty_weight", 0.3)) * perturbation
    cost += sym_mask * float(cfg_get(cfg.training, "echosat_delta_magnitude_weight", 0.1)) * (1.0 - e_sym) * perturbation
    cost += sym_mask * float(cfg_get(cfg.training, "echosat_permutation_delta_weight", 0.25)) * perm_delta_penalty
    cost += float(cfg_get(cfg.training, "echosat_unsolved_penalty", 8.0)) * (~solved)
    cost += float(cfg_get(cfg.training, "echosat_result_mismatch_penalty", 20.0)) * result_mismatch

    strong_weight = float(cfg_get(cfg.training, "echosat_strong_advantage_weight", 1.0))
    weak_weight = float(cfg_get(cfg.training, "echosat_weak_advantage_weight", 0.6))
    control_weight = float(cfg_get(cfg.training, "echosat_control_advantage_weight", 0.25))
    other_weight = float(cfg_get(cfg.training, "echosat_other_advantage_weight", 0.35))
    advantage_weight = np.full(len(out), other_weight, dtype=np.float64)
    advantage_weight[symmetry_strength.eq("strong").to_numpy()] = strong_weight
    advantage_weight[symmetry_strength.eq("weak").to_numpy()] = weak_weight
    advantage_weight[is_control.to_numpy()] = control_weight
    advantage_weight = advantage_weight * np.clip(np.maximum(e_sym, other_weight), 0.0, 1.0)
    advantage_weight[is_control.to_numpy()] = control_weight

    if target_mode == "adapter_delta":
        static_reference_cost = (
            float(cfg_get(cfg.training, "echosat_static_reference_cpu_weight", 0.4)) * np.clip(
                (static_cpu - neutral_cpu) / np.maximum(neutral_cpu, eps),
                -clip,
                clip,
            )
            if not np.all(np.isnan(neutral_cpu))
            else np.zeros(len(out), dtype=np.float64)
        )
        adapter_delta_cost = (
            float(cfg_get(cfg.training, "echosat_final_cpu_weight", 0.4)) * final_cpu_cost
            + float(cfg_get(cfg.training, "echosat_search_weight", 1.0)) * search_cost
        )
        cost = np.zeros(len(out), dtype=np.float64)
        cost += sym_mask * float(cfg_get(cfg.training, "echosat_sym_weight", 1.0)) * e_sym * adapter_delta_cost
        cost += sym_mask * float(cfg_get(cfg.training, "echosat_static_reference_weight", 0.0)) * static_reference_cost
        cost += float(cfg_get(cfg.training, "echosat_overhead_weight", 0.0)) * overhead
        cost += float(cfg_get(cfg.training, "echosat_weighted_risk_weight", 0.5)) * weighted_risk * (1.0 + perturbation)
        cost += control_mask * float(cfg_get(cfg.training, "echosat_control_penalty_weight", 0.5)) * perturbation
        cost += control_mask * float(cfg_get(cfg.training, "echosat_control_portfolio_weight", 0.0)) * final_cpu_cost
        cost += sym_mask * float(cfg_get(cfg.training, "echosat_delta_magnitude_weight", 0.1)) * (1.0 - e_sym) * perturbation
        cost += sym_mask * float(cfg_get(cfg.training, "echosat_permutation_delta_weight", 0.5)) * perm_delta_penalty
        cost += float(cfg_get(cfg.training, "echosat_unsolved_penalty", 8.0)) * (~solved)
        cost += float(cfg_get(cfg.training, "echosat_result_mismatch_penalty", 20.0)) * result_mismatch
        advantage_weight = np.zeros(len(out), dtype=np.float64)
        advantage_weight[symmetry_strength.eq("strong").to_numpy()] = strong_weight
        advantage_weight[symmetry_strength.eq("weak").to_numpy()] = weak_weight
        advantage_weight[~is_control.to_numpy()] *= np.clip(e_sym[~is_control.to_numpy()], 0.0, 1.0)
        advantage_weight[is_control.to_numpy()] = control_weight

    if target_mode == "symmetry_grpo_v1":
        decision_reduction = np.clip(
            (static_decisions - decisions) / np.maximum(static_decisions, 1.0),
            -clip,
            clip,
        )
        conflict_reduction = np.clip(
            (static_conflicts - conflicts) / np.maximum(static_conflicts, 1.0),
            -clip,
            clip,
        )
        cpu_reduction = np.clip(
            (static_cpu - cpu) / np.maximum(static_cpu, eps),
            -float(cfg_get(cfg.training, "echosat_cpu_reduction_clip", 0.25)),
            float(cfg_get(cfg.training, "echosat_cpu_reduction_clip", 0.25)),
        )
        search_reward = (
            float(cfg_get(cfg.training, "echosat_decisions_weight", 0.55)) * decision_reduction
            + float(cfg_get(cfg.training, "echosat_conflicts_weight", 0.45)) * conflict_reduction
            + float(cfg_get(cfg.training, "echosat_final_cpu_weight", 0.15)) * cpu_reduction
        )
        positive_search = np.maximum(search_reward, 0.0)
        negative_search = np.minimum(search_reward, 0.0)

        formula_group = out.get("formula_equivalence_group", pd.Series("", index=out.index)).fillna("").astype(str)
        sampling_group = out.get("echosat_sampling_group_id", pd.Series("", index=out.index)).fillna("").astype(str)
        if sampling_group.eq("").all():
            sampling_group = out.get("base_instance_id", pd.Series("", index=out.index)).fillna("").astype(str)
        direction_penalty = np.zeros(len(out), dtype=np.float64)
        direction_signal = decision_reduction + conflict_reduction
        for group_values in [out.get("base_instance_id", pd.Series("", index=out.index)).fillna("").astype(str), formula_group, sampling_group]:
            temp = pd.DataFrame({"group": group_values.to_numpy(), "signal": direction_signal, "idx": np.arange(len(out))})
            temp = temp[temp["group"].astype(str).ne("")]
            for _, group in temp.groupby("group", sort=False):
                if len(group) < 2:
                    continue
                signs = np.sign(group["signal"].to_numpy(dtype=np.float64))
                nonzero = signs[signs != 0]
                if len(nonzero) == 0:
                    continue
                majority = 1.0 if np.sum(nonzero > 0) >= np.sum(nonzero < 0) else -1.0
                direction_mismatch = (signs != 0) & (signs != majority)
                direction_penalty[group["idx"].to_numpy(dtype=np.int64)] += direction_mismatch.astype(np.float64) * np.abs(group["signal"].to_numpy(dtype=np.float64))

        near_cap_mask = np.maximum.reduce(
            [
                cpu / max(cap, eps),
                static_cpu / max(cap, eps),
                np.nan_to_num(neutral_cpu / max(cap, eps), nan=0.0),
            ]
        ) >= float(cfg_get(cfg.training, "echosat_near_cap_fraction", 0.8))
        static_weighted_risk_raw = static_weighted_risk
        near_cap_penalty = near_cap_mask.astype(np.float64) * positive_search
        random_control_penalty = is_control.to_numpy(dtype=np.float64) * np.maximum(positive_search, perturbation)
        unsupported_positive_penalty = ((e_sym <= 0.0).astype(np.float64) * positive_search)
        evidence_gated_reward = positive_search * e_sym + negative_search

        cost = -evidence_gated_reward
        cost += float(cfg_get(cfg.training, "echosat_random_control_penalty_weight", 2.0)) * random_control_penalty
        cost += float(cfg_get(cfg.training, "echosat_control_penalty_weight", 1.0)) * is_control.to_numpy(dtype=np.float64) * perturbation
        cost += float(cfg_get(cfg.training, "echosat_permutation_delta_weight", 0.75)) * (perm_delta_penalty + direction_penalty)
        cost += float(cfg_get(cfg.training, "echosat_weighted_risk_weight", 0.75)) * weighted_risk * (1.0 + perturbation)
        cost += float(cfg_get(cfg.training, "echosat_near_cap_penalty_weight", 0.25)) * near_cap_penalty
        cost += float(cfg_get(cfg.training, "echosat_delta_magnitude_weight", 0.15)) * unsupported_positive_penalty
        cost += float(cfg_get(cfg.training, "echosat_large_weight_phase_shift_penalty_weight", 0.2)) * perturbation * (1.0 - e_sym)
        cost += float(cfg_get(cfg.training, "echosat_unsolved_penalty", 8.0)) * (~solved)
        cost += float(cfg_get(cfg.training, "echosat_result_mismatch_penalty", 20.0)) * result_mismatch

        advantage_weight = np.zeros(len(out), dtype=np.float64)
        advantage_weight[symmetry_strength.eq("strong").to_numpy()] = strong_weight
        advantage_weight[symmetry_strength.eq("weak").to_numpy()] = weak_weight
        non_control_mask = ~is_control.to_numpy(dtype=bool)
        advantage_weight[non_control_mask] *= np.clip(np.maximum(e_sym[non_control_mask], 0.05), 0.0, 1.0)
        advantage_weight[is_control.to_numpy(dtype=bool)] = control_weight

        out["echosat_decision_reduction"] = decision_reduction
        out["echosat_conflict_reduction"] = conflict_reduction
        out["echosat_cpu_reduction"] = cpu_reduction
        out["echosat_search_reward"] = search_reward
        out["echosat_symmetry_reward"] = evidence_gated_reward
        out["echosat_random_control_penalty"] = random_control_penalty
        out["echosat_direction_consistency_penalty"] = direction_penalty
        out["echosat_near_cap_penalty"] = near_cap_penalty
        out["echosat_static_weighted_risk_raw"] = static_weighted_risk_raw
        out["echosat_event_nonzero_vars"] = event_nonzero
        out["echosat_graph_gate_evidence_proxy"] = graph_gate_evidence

    if target_mode in {
        "symmetry_grpo_v1_1",
        "symmetry_grpo_v1_2",
        "symmetry_grpo_v1_3",
        "symmetry_grpo_v1_4",
        "symmetry_grpo_v1_5",
        "symmetry_grpo_v1_6",
        "symmetry_grpo_v1_7",
        "symmetry_grpo_v1_8",
    }:
        decision_delta = decisions - static_decisions
        conflict_delta = conflicts - static_conflicts
        decision_reduction = np.clip(
            -decision_delta / np.maximum(static_decisions, 1.0),
            -clip,
            clip,
        )
        conflict_reduction = np.clip(
            -conflict_delta / np.maximum(static_conflicts, 1.0),
            -clip,
            clip,
        )
        cpu_reduction = np.clip(
            (static_cpu - cpu) / np.maximum(static_cpu, eps),
            -float(cfg_get(cfg.training, "echosat_cpu_reduction_clip", 0.05)),
            float(cfg_get(cfg.training, "echosat_cpu_reduction_clip", 0.05)),
        )

        eps_dec = float(cfg_get(cfg.training, "echosat_search_eps_decisions", 0.0))
        eps_conf = float(cfg_get(cfg.training, "echosat_search_eps_conflicts", 0.0))
        search_ok = (decision_delta < -eps_dec) & (conflict_delta < -eps_conf)
        search_blowup = (decision_delta > eps_dec) | (conflict_delta > eps_conf)

        decision_positive = np.maximum(decision_reduction, 0.0)
        conflict_positive = np.maximum(conflict_reduction, 0.0)
        cpu_tiebreaker = np.maximum(cpu_reduction, 0.0)
        r_search_decisions = float(cfg_get(cfg.training, "echosat_decisions_weight", 0.55)) * decision_positive
        r_search_conflicts = float(cfg_get(cfg.training, "echosat_conflicts_weight", 0.45)) * conflict_positive
        r_cpu_clipped = float(cfg_get(cfg.training, "echosat_final_cpu_weight", 0.02)) * cpu_tiebreaker

        decision_blowup = np.maximum(decision_delta, 0.0) / np.maximum(static_decisions, 1.0)
        conflict_blowup = np.maximum(conflict_delta, 0.0) / np.maximum(static_conflicts, 1.0)
        search_blowup_penalty = (
            float(cfg_get(cfg.training, "echosat_decision_blowup_penalty_weight", 1.25)) * np.clip(decision_blowup, 0.0, clip)
            + float(cfg_get(cfg.training, "echosat_conflict_blowup_penalty_weight", 1.25)) * np.clip(conflict_blowup, 0.0, clip)
        )

        near_cap_mask = np.maximum.reduce(
            [
                cpu / max(cap, eps),
                static_cpu / max(cap, eps),
                np.nan_to_num(neutral_cpu / max(cap, eps), nan=0.0),
            ]
        ) >= float(cfg_get(cfg.training, "echosat_near_cap_fraction", 0.8))
        weighted_risk_ok = weighted_risk <= float(cfg_get(cfg.training, "echosat_weighted_risk_positive_threshold", 0.0))
        non_control_mask = ~is_control.to_numpy(dtype=bool)
        positive_allowed = search_ok & non_control_mask & (e_sym > 0.0) & (~near_cap_mask) & weighted_risk_ok
        positive_reward = positive_allowed.astype(np.float64) * e_sym * (r_search_decisions + r_search_conflicts + r_cpu_clipped)

        formula_group = out.get("formula_equivalence_group", pd.Series("", index=out.index)).fillna("").astype(str)
        sampling_group = out.get("echosat_sampling_group_id", pd.Series("", index=out.index)).fillna("").astype(str)
        if sampling_group.eq("").all():
            sampling_group = out.get("base_instance_id", pd.Series("", index=out.index)).fillna("").astype(str)
        base_group = out.get("base_instance_id", pd.Series("", index=out.index)).fillna("").astype(str)
        direction_penalty = np.zeros(len(out), dtype=np.float64)
        pair_rank_penalty = np.zeros(len(out), dtype=np.float64)
        mixed_group_mask = np.zeros(len(out), dtype=bool)
        search_sign = np.where(search_ok, 1.0, np.where(search_blowup, -1.0, 0.0))
        inconsistency_magnitude = (
            search_blowup_penalty
            + np.abs(decision_reduction)
            + np.abs(conflict_reduction)
            + positive_reward
        )
        for group_values in [
            base_group,
            formula_group,
            sampling_group,
        ]:
            temp = pd.DataFrame({"group": group_values.to_numpy(), "sign": search_sign, "idx": np.arange(len(out))})
            temp = temp[temp["group"].astype(str).ne("")]
            for _, group in temp.groupby("group", sort=False):
                signs = group["sign"].to_numpy(dtype=np.float64)
                if not ((signs > 0).any() and (signs < 0).any()):
                    continue
                idx = group["idx"].to_numpy(dtype=np.int64)
                row_scale = np.where(search_sign[idx] < 0.0, 1.0, 0.5)
                if target_mode in {
                    "symmetry_grpo_v1_2",
                    "symmetry_grpo_v1_3",
                    "symmetry_grpo_v1_4",
                    "symmetry_grpo_v1_5",
                    "symmetry_grpo_v1_6",
                    "symmetry_grpo_v1_7",
                    "symmetry_grpo_v1_8",
                }:
                    row_scale = np.where(
                        search_sign[idx] < 0.0,
                        float(cfg_get(cfg.training, "echosat_mixed_group_negative_scale", 2.0)),
                        float(cfg_get(cfg.training, "echosat_mixed_group_positive_scale", 1.0)),
                    )
                    mixed_group_mask[idx] = True
                direction_penalty[idx] += row_scale * inconsistency_magnitude[idx]
                if target_mode in {"symmetry_grpo_v1_5", "symmetry_grpo_v1_6", "symmetry_grpo_v1_7", "symmetry_grpo_v1_8"}:
                    positive_count = max(float((signs > 0.0).sum()), 1.0)
                    negative_count = max(float((signs < 0.0).sum()), 1.0)
                    imbalance = abs(positive_count - negative_count) / float(len(signs))
                    pair_rank_penalty[idx] += (
                        row_scale
                        * (1.0 + imbalance)
                        * (
                            inconsistency_magnitude[idx]
                            + np.abs(decision_delta[idx]) / np.maximum(static_decisions[idx], 1.0)
                            + np.abs(conflict_delta[idx]) / np.maximum(static_conflicts[idx], 1.0)
                        )
                    )

        hard_negative_ids = cfg_string_set(cfg.training, "echosat_hard_negative_base_ids")
        hard_negative_mask = base_group.isin(hard_negative_ids).to_numpy(dtype=bool) if hard_negative_ids else np.zeros(len(out), dtype=bool)
        hard_negative_penalty = np.zeros(len(out), dtype=np.float64)
        anchor_ids = cfg_string_set(cfg.training, "echosat_anchor_base_ids")
        anchor_mask = base_group.isin(anchor_ids).to_numpy(dtype=bool) if anchor_ids else np.zeros(len(out), dtype=bool)
        anchor_failure_penalty = np.zeros(len(out), dtype=np.float64)
        subset_failure_base = str(cfg_get(cfg.training, "echosat_subset_failure_base_id", ""))
        subset_failure_variant = str(cfg_get(cfg.training, "echosat_subset_failure_variant", ""))
        variant_group = out.get("variant", pd.Series("", index=out.index)).fillna("").astype(str)
        subset_failure_mask = (
            base_group.eq(subset_failure_base).to_numpy(dtype=bool)
            & variant_group.eq(subset_failure_variant).to_numpy(dtype=bool)
            if subset_failure_base and subset_failure_variant
            else np.zeros(len(out), dtype=bool)
        )
        subset_failure_penalty = np.zeros(len(out), dtype=np.float64)
        hard_negative_failure_mask = hard_negative_mask & (~search_ok)
        anchor_failure_mask = anchor_mask & (~search_ok)
        positive_allowed_search = search_ok & non_control_mask & (e_sym > 0.0)
        positive_blocked_control = search_ok & is_control.to_numpy(dtype=bool)
        positive_blocked_subset_failure = positive_allowed_search & subset_failure_mask
        positive_blocked_weighted_risk = positive_allowed_search & (~weighted_risk_ok)
        positive_blocked_near_cap = positive_allowed_search & near_cap_mask
        positive_blocked_pair_inconsistency = positive_allowed_search & mixed_group_mask
        positive_blocked_anchor_failure = anchor_failure_mask
        positive_blocked_hard_negative_failure = hard_negative_failure_mask

        if target_mode in {
            "symmetry_grpo_v1_2",
            "symmetry_grpo_v1_3",
            "symmetry_grpo_v1_4",
            "symmetry_grpo_v1_5",
            "symmetry_grpo_v1_6",
            "symmetry_grpo_v1_7",
            "symmetry_grpo_v1_8",
        }:
            suppress_mixed_positive = bool(cfg_get(cfg.training, "echosat_suppress_mixed_group_positive", True))
            if target_mode in {"symmetry_grpo_v1_6", "symmetry_grpo_v1_7", "symmetry_grpo_v1_8"}:
                suppress_mixed_positive = bool(cfg_get(cfg.training, "echosat_v16_hard_block_mixed_positive", False))
            if suppress_mixed_positive:
                positive_allowed = positive_allowed & (~mixed_group_mask)
                positive_reward = positive_allowed.astype(np.float64) * e_sym * (
                    r_search_decisions + r_search_conflicts + r_cpu_clipped
                )
            hard_negative_penalty = hard_negative_mask.astype(np.float64) * search_blowup.astype(np.float64) * (
                search_blowup_penalty
                + direction_penalty
                + np.abs(decision_reduction)
                + np.abs(conflict_reduction)
            )
        if target_mode in {
            "symmetry_grpo_v1_3",
            "symmetry_grpo_v1_4",
            "symmetry_grpo_v1_5",
            "symmetry_grpo_v1_6",
            "symmetry_grpo_v1_7",
            "symmetry_grpo_v1_8",
        }:
            if bool(cfg_get(cfg.training, "echosat_suppress_subset_failure_positive", True)):
                positive_allowed = positive_allowed & (~subset_failure_mask)
                positive_reward = positive_allowed.astype(np.float64) * e_sym * (
                    r_search_decisions + r_search_conflicts + r_cpu_clipped
                )
            anchor_failure_penalty = anchor_mask.astype(np.float64) * (~search_ok).astype(np.float64) * (
                search_blowup_penalty
                + np.maximum(0.0, -decision_reduction)
                + np.maximum(0.0, -conflict_reduction)
                + float(cfg_get(cfg.training, "echosat_anchor_failure_floor", 0.25))
            )
            subset_failure_penalty = subset_failure_mask.astype(np.float64) * search_ok.astype(np.float64) * (
                r_search_decisions
                + r_search_conflicts
                + r_cpu_clipped
                + search_blowup_penalty
                + float(cfg_get(cfg.training, "echosat_subset_failure_floor", 1.0))
            )
        if target_mode in {"symmetry_grpo_v1_5", "symmetry_grpo_v1_6", "symmetry_grpo_v1_7", "symmetry_grpo_v1_8"}:
            hard_negative_penalty = hard_negative_failure_mask.astype(np.float64) * (
                search_blowup_penalty
                + direction_penalty
                + pair_rank_penalty
                + np.maximum(0.0, -decision_reduction)
                + np.maximum(0.0, -conflict_reduction)
                + float(cfg_get(cfg.training, "echosat_hard_negative_failure_floor", 0.75))
            )
            anchor_failure_penalty = anchor_failure_mask.astype(np.float64) * (
                search_blowup_penalty
                + direction_penalty
                + pair_rank_penalty
                + np.maximum(0.0, -decision_reduction)
                + np.maximum(0.0, -conflict_reduction)
                + float(cfg_get(cfg.training, "echosat_anchor_catastrophic_failure_floor", 1.5))
            )
            if target_mode == "symmetry_grpo_v1_5" and bool(cfg_get(cfg.training, "echosat_v15_suppress_mixed_group_positive", True)):
                positive_allowed = positive_allowed & (~mixed_group_mask)
            if target_mode in {"symmetry_grpo_v1_6", "symmetry_grpo_v1_7", "symmetry_grpo_v1_8"} and bool(
                cfg_get(cfg.training, "echosat_v16_hard_block_mixed_positive", False)
            ):
                positive_allowed = positive_allowed & (~mixed_group_mask)
            if bool(cfg_get(cfg.training, "echosat_v15_suppress_anchor_failure_positive", True)):
                positive_allowed = positive_allowed & (~anchor_failure_mask)
            if bool(cfg_get(cfg.training, "echosat_v15_suppress_hard_negative_failure_positive", True)):
                positive_allowed = positive_allowed & (~hard_negative_failure_mask)
            positive_reward = positive_allowed.astype(np.float64) * e_sym * (
                r_search_decisions + r_search_conflicts + r_cpu_clipped
            )

        random_control_penalty = is_control.to_numpy(dtype=np.float64) * np.maximum(
            search_blowup_penalty + positive_reward,
            perturbation,
        )
        unsupported_positive_penalty = ((e_sym <= 0.0).astype(np.float64) * (r_search_decisions + r_search_conflicts + r_cpu_clipped))
        weighted_path_risk_penalty = weighted_risk * (1.0 + perturbation)
        near_cap_penalty = near_cap_mask.astype(np.float64) * (
            r_search_decisions + r_search_conflicts + r_cpu_clipped + search_blowup_penalty
        )
        large_weight_phase_shift_penalty = perturbation * (1.0 - e_sym)
        consistency_penalty_applied = (
            float(cfg_get(cfg.training, "echosat_permutation_delta_weight", 2.0)) * (perm_delta_penalty + direction_penalty)
            + float(cfg_get(cfg.training, "echosat_pair_rank_penalty_weight", 0.0)) * pair_rank_penalty
        )
        large_weight_phase_shift_penalty_applied = (
            float(cfg_get(cfg.training, "echosat_large_weight_phase_shift_penalty_weight", 1.0))
            * large_weight_phase_shift_penalty
        )
        if target_mode in {"symmetry_grpo_v1_7", "symmetry_grpo_v1_8"}:
            positive_success_mask = positive_allowed & search_ok
            consistency_cap = (
                float(cfg_get(cfg.training, "echosat_v17_positive_consistency_penalty_fraction", 0.15))
                * np.maximum(positive_reward, 0.0)
            )
            large_shift_cap = (
                float(cfg_get(cfg.training, "echosat_v17_positive_large_shift_penalty_fraction", 0.20))
                * np.maximum(positive_reward, 0.0)
            )
            consistency_penalty_applied = consistency_penalty_applied.copy()
            large_weight_phase_shift_penalty_applied = large_weight_phase_shift_penalty_applied.copy()
            consistency_penalty_applied[positive_success_mask] = np.minimum(
                consistency_penalty_applied[positive_success_mask],
                consistency_cap[positive_success_mask],
            )
            large_weight_phase_shift_penalty_applied[positive_success_mask] = np.minimum(
                large_weight_phase_shift_penalty_applied[positive_success_mask],
                large_shift_cap[positive_success_mask],
            )

        reward = positive_reward - search_blowup_penalty
        reward -= float(cfg_get(cfg.training, "echosat_random_control_penalty_weight", 4.0)) * random_control_penalty
        reward -= float(cfg_get(cfg.training, "echosat_control_penalty_weight", 2.0)) * is_control.to_numpy(dtype=np.float64) * perturbation
        reward -= consistency_penalty_applied
        reward -= float(cfg_get(cfg.training, "echosat_weighted_risk_weight", 1.25)) * weighted_path_risk_penalty
        reward -= float(cfg_get(cfg.training, "echosat_near_cap_penalty_weight", 1.0)) * near_cap_penalty
        reward -= float(cfg_get(cfg.training, "echosat_delta_magnitude_weight", 0.5)) * unsupported_positive_penalty
        reward -= large_weight_phase_shift_penalty_applied
        reward -= float(cfg_get(cfg.training, "echosat_hard_negative_penalty_weight", 0.0)) * hard_negative_penalty
        reward -= float(cfg_get(cfg.training, "echosat_anchor_failure_penalty_weight", 0.0)) * anchor_failure_penalty
        reward -= float(cfg_get(cfg.training, "echosat_subset_failure_penalty_weight", 0.0)) * subset_failure_penalty
        reward -= float(cfg_get(cfg.training, "echosat_unsolved_penalty", 8.0)) * (~solved)
        reward -= float(cfg_get(cfg.training, "echosat_result_mismatch_penalty", 20.0)) * result_mismatch
        cost = -reward

        advantage_weight = np.zeros(len(out), dtype=np.float64)
        advantage_weight[symmetry_strength.eq("strong").to_numpy()] = strong_weight
        advantage_weight[symmetry_strength.eq("weak").to_numpy()] = weak_weight
        advantage_weight[non_control_mask] *= np.clip(e_sym[non_control_mask], 0.0, 1.0)
        if target_mode in {"symmetry_grpo_v1_5", "symmetry_grpo_v1_6", "symmetry_grpo_v1_7", "symmetry_grpo_v1_8"}:
            advantage_weight[is_control.to_numpy(dtype=bool)] = float(
                cfg_get(cfg.training, "echosat_control_negative_advantage_weight", 1.0)
            )
        else:
            advantage_weight[is_control.to_numpy(dtype=bool)] = 1.0
        advantage_upper_bound = np.full(len(out), np.inf, dtype=np.float64)
        advantage_upper_bound[~positive_allowed] = 0.0
        advantage_upper_bound[reward <= 0.0] = 0.0
        if target_mode in {"symmetry_grpo_v1_7", "symmetry_grpo_v1_8"}:
            advantage_upper_bound[positive_allowed & (positive_reward > 0.0)] = np.inf
        advantage_raw_upper_bound = np.full(len(out), np.inf, dtype=np.float64)
        if target_mode in {"symmetry_grpo_v1_5", "symmetry_grpo_v1_6", "symmetry_grpo_v1_7", "symmetry_grpo_v1_8"}:
            advantage_raw_upper_bound[is_control.to_numpy(dtype=bool)] = 0.0
            advantage_raw_upper_bound[anchor_failure_mask] = 0.0
            advantage_raw_upper_bound[hard_negative_failure_mask] = 0.0
            advantage_raw_upper_bound[subset_failure_mask] = 0.0
            hard_block_mixed_advantage = (
                bool(cfg_get(cfg.training, "echosat_v15_pair_mixed_advantage_hard_clamp", True))
                if target_mode == "symmetry_grpo_v1_5"
                else bool(cfg_get(cfg.training, "echosat_v16_hard_block_mixed_positive", False))
            )
            if hard_block_mixed_advantage:
                advantage_raw_upper_bound[mixed_group_mask] = 0.0
            advantage_upper_bound[is_control.to_numpy(dtype=bool)] = 0.0
            advantage_upper_bound[anchor_failure_mask] = 0.0
            advantage_upper_bound[hard_negative_failure_mask] = 0.0
            advantage_upper_bound[subset_failure_mask] = 0.0
            if hard_block_mixed_advantage:
                advantage_upper_bound[mixed_group_mask] = 0.0

        out["echosat_decision_reduction"] = decision_reduction
        out["echosat_conflict_reduction"] = conflict_reduction
        out["echosat_cpu_reduction"] = cpu_reduction
        out["echosat_search_ok"] = search_ok
        out["echosat_search_blowup"] = search_blowup
        out["echosat_positive_allowed_search"] = positive_allowed_search
        out["echosat_positive_allowed"] = positive_allowed
        out["echosat_positive_blocked_control"] = positive_blocked_control
        out["echosat_positive_blocked_subset_failure"] = positive_blocked_subset_failure
        out["echosat_positive_blocked_weighted_risk"] = positive_blocked_weighted_risk
        out["echosat_positive_blocked_near_cap"] = positive_blocked_near_cap
        out["echosat_positive_blocked_pair_inconsistency"] = positive_blocked_pair_inconsistency
        out["echosat_positive_blocked_anchor_failure"] = positive_blocked_anchor_failure
        out["echosat_positive_blocked_hard_negative_failure"] = positive_blocked_hard_negative_failure
        out["echosat_search_reward"] = positive_reward - search_blowup_penalty
        out["echosat_symmetry_reward"] = positive_reward
        out["echosat_r_search_decisions"] = r_search_decisions
        out["echosat_r_search_conflicts"] = r_search_conflicts
        out["echosat_r_cpu_clipped"] = r_cpu_clipped
        out["echosat_search_blowup_penalty"] = search_blowup_penalty
        out["echosat_random_control_penalty"] = random_control_penalty
        out["echosat_direction_consistency_penalty"] = direction_penalty
        out["echosat_pair_rank_penalty"] = pair_rank_penalty
        out["echosat_consistency_penalty_applied"] = consistency_penalty_applied
        out["echosat_group_mixed_direction"] = mixed_group_mask
        out["echosat_hard_negative_candidate"] = hard_negative_mask
        out["echosat_hard_negative_failure"] = hard_negative_failure_mask
        out["echosat_hard_negative_penalty"] = hard_negative_penalty
        out["echosat_anchor_candidate"] = anchor_mask
        out["echosat_anchor_failure"] = anchor_failure_mask
        out["echosat_anchor_failure_penalty"] = anchor_failure_penalty
        out["echosat_subset_failure_candidate"] = subset_failure_mask
        out["echosat_subset_failure_penalty"] = subset_failure_penalty
        out["echosat_near_cap_penalty"] = near_cap_penalty
        out["echosat_static_weighted_risk_raw"] = static_weighted_risk
        out["echosat_weighted_path_risk_penalty"] = weighted_path_risk_penalty
        out["echosat_large_weight_phase_shift_penalty"] = large_weight_phase_shift_penalty
        out["echosat_large_weight_phase_shift_penalty_applied"] = large_weight_phase_shift_penalty_applied
        out["echosat_event_nonzero_vars"] = event_nonzero
        out["echosat_graph_gate_evidence_proxy"] = graph_gate_evidence
        out["echosat_advantage_upper_bound"] = advantage_upper_bound
        out["echosat_advantage_raw_upper_bound"] = advantage_raw_upper_bound

    out["baseline_static_cpu_time"] = static_cpu
    out["baseline_static_conflicts"] = static_conflicts
    out["baseline_static_decisions"] = static_decisions
    out["baseline_neutral_cpu_time"] = neutral_cpu
    out["echosat_target_mode"] = target_mode
    out["echosat_final_cpu_cost"] = final_cpu_cost
    out["echosat_search_cost"] = search_cost
    out["echosat_overhead_cost"] = overhead
    out["echosat_weighted_risk"] = weighted_risk
    out["echosat_perturbation_penalty"] = perturbation
    out["echosat_perm_delta_penalty"] = perm_delta_penalty
    out["echosat_e_sym"] = e_sym
    out["echosat_advantage_weight"] = advantage_weight
    out["echosat_result_mismatch"] = result_mismatch
    out["echosat_cost"] = np.nan_to_num(cost, nan=float(cfg_get(cfg.training, "echosat_unsolved_penalty", 8.0)), posinf=20.0, neginf=-20.0)
    if target_mode == "symmetry_grpo_v1_8":
        out = apply_echosat_v18_advantage_repair(out, cfg)
    elif target_mode == "symmetry_grpo_v2":
        out = build_symmetry_grpo_v2_target(
            out,
            baseline_stats_by_name.get("plain_unguided"),
            baseline_stats_by_name.get("static_weighted"),
            cpu_cap=cap,
            near_cap_fraction=float(cfg_get(cfg.training, "echosat_near_cap_fraction", 0.8)),
            weighted_risk_threshold=float(cfg_get(cfg.training, "echosat_v2_weighted_risk_threshold", 0.0)),
            eps_decisions=float(cfg_get(cfg.training, "echosat_v2_eps_decisions", 0.0)),
            eps_conflicts=float(cfg_get(cfg.training, "echosat_v2_eps_conflicts", 0.0)),
        )
    return out


def add_speedup_target(
        solver_stats: pd.DataFrame,
        cfg: DictConfig,
        baseline_stats: pd.DataFrame | None,
) -> pd.DataFrame:
    if not uses_speedup_target(cfg):
        return solver_stats
    if baseline_stats is None:
        raise ValueError("speedup_cost requires baseline solver stats")

    out = solver_stats.copy()
    baseline = (
        baseline_stats.sort_values(["cnf_id", "sample_id"], ascending=[True, True])
        .drop_duplicates("cnf_id")
        .set_index("cnf_id")
    )

    cnf_ids = out["cnf_id"].to_numpy()

    def baseline_values(column: str, default: float = 0.0) -> np.ndarray:
        if column not in baseline.columns:
            return np.full(len(out), default, dtype=np.float64)
        values = pd.to_numeric(baseline[column], errors="coerce")
        fill_value = values.max()
        if pd.isna(fill_value):
            fill_value = default
        return values.reindex(cnf_ids).fillna(fill_value).to_numpy(dtype=np.float64)

    eps = float(cfg_get(cfg.training, "speedup_ratio_eps", 1.0e-6))
    clip = float(cfg_get(cfg.training, "speedup_log_ratio_clip", 2.0))
    cpu_column = str(cfg_get(cfg.training, "speedup_cpu_column", "CPU time"))

    cpu = numeric_stat(out, cpu_column).to_numpy(dtype=np.float64)
    conflicts = numeric_stat(out, "conflicts").to_numpy(dtype=np.float64)
    decisions = numeric_stat(out, "decisions").to_numpy(dtype=np.float64)
    base_cpu = baseline_values(cpu_column)
    base_conflicts = baseline_values("conflicts")
    base_decisions = baseline_values("decisions")

    cpu_ratio = bounded_log_ratio(cpu, base_cpu, eps=eps, clip=clip)
    conflicts_ratio = bounded_log_ratio(conflicts, base_conflicts, eps=eps, clip=clip)
    decisions_ratio = bounded_log_ratio(decisions, base_decisions, eps=eps, clip=clip)

    cost = np.zeros(len(out), dtype=np.float64)
    cost += float(cfg_get(cfg.training, "speedup_cpu_weight", 1.0)) * cpu_ratio
    cost += float(cfg_get(cfg.training, "speedup_conflicts_weight", 0.2)) * conflicts_ratio
    cost += float(cfg_get(cfg.training, "speedup_decisions_weight", 0.05)) * decisions_ratio

    solved = solved_mask(out).to_numpy(dtype=bool)
    baseline_result = (
        baseline["Result"].reindex(cnf_ids).astype(str).to_numpy()
        if "Result" in baseline.columns
        else np.array([""] * len(out), dtype=object)
    )
    result = out["Result"].astype(str).to_numpy() if "Result" in out.columns else np.array([""] * len(out), dtype=object)
    baseline_solved = np.isin(baseline_result, ["SATISFIABLE", "UNSATISFIABLE"])
    mismatch = solved & baseline_solved & (result != baseline_result)

    cost += float(cfg_get(cfg.training, "speedup_unsolved_penalty", 8.0)) * (~solved)
    cost += float(cfg_get(cfg.training, "speedup_result_mismatch_penalty", 20.0)) * mismatch

    out["baseline_cpu_time"] = base_cpu
    out["baseline_conflicts"] = base_conflicts
    out["baseline_decisions"] = base_decisions
    out["baseline_result"] = baseline_result
    out["speedup_cpu_log_ratio"] = cpu_ratio
    out["speedup_conflicts_log_ratio"] = conflicts_ratio
    out["speedup_decisions_log_ratio"] = decisions_ratio
    out["speedup_result_mismatch"] = mismatch
    out["speedup_cost"] = cost
    return out


def add_training_targets(
        solver_stats: pd.DataFrame,
        cfg: DictConfig,
        baseline_stats: pd.DataFrame | None = None,
        baseline_stats_by_name: dict[str, pd.DataFrame] | None = None,
        metadata: pd.DataFrame | None = None,
        data_list: list | None = None,
        static_data_list: list | None = None,
) -> pd.DataFrame:
    solver_stats = add_composite_target(solver_stats, cfg)
    solver_stats = add_speedup_target(solver_stats, cfg, baseline_stats=baseline_stats)
    solver_stats = add_echosat_target(
        solver_stats,
        cfg,
        baseline_stats_by_name=baseline_stats_by_name,
        metadata=metadata,
        data_list=data_list,
        static_data_list=static_data_list,
    )
    return solver_stats


def attach_grpo_advantage_columns(solver_stats: pd.DataFrame, cfg: DictConfig) -> pd.DataFrame:
    if str(cfg_get(cfg.training, "echosat_target_mode", "full")).lower() == "symmetry_grpo_v2":
        return attach_masked_grpo_advantage(
            solver_stats,
            target_column=str(cfg.training.target_stat),
        )
    target_stat = str(cfg.training.target_stat)
    out = solver_stats.copy()
    values = pd.to_numeric(out[target_stat], errors="coerce")
    finite = np.isfinite(values.to_numpy(dtype=np.float64))
    max_cost = values[finite].max() if finite.any() else 0.0
    target_values = values.replace([np.inf, -np.inf], np.nan).fillna(max_cost)
    out[target_stat] = target_values

    grouped = pd.DataFrame(
        {
            "cnf_id": out["cnf_id"].to_numpy(),
            target_stat: target_values.to_numpy(dtype=np.float64),
        }
    ).groupby("cnf_id", sort=False)[target_stat]
    group_mean = grouped.transform("mean").to_numpy(dtype=np.float64)
    group_std = grouped.transform("std").to_numpy(dtype=np.float64)
    target_array = target_values.to_numpy(dtype=np.float64)

    eps = 1.0e-8
    raw_unclamped = -((target_array - group_mean) / (group_std + eps))
    raw_unclamped = np.nan_to_num(raw_unclamped, nan=0.0, posinf=0.0, neginf=0.0)

    raw_upper = np.full(len(out), np.inf, dtype=np.float64)
    if "echosat_advantage_raw_upper_bound" in out.columns:
        raw_upper = pd.to_numeric(out["echosat_advantage_raw_upper_bound"], errors="coerce").fillna(np.inf).to_numpy(dtype=np.float64)
    raw_advantage = np.minimum(raw_unclamped, raw_upper)
    raw_advantage = np.nan_to_num(raw_advantage, nan=0.0, posinf=0.0, neginf=0.0)

    advantage_weight = (
        pd.to_numeric(out["echosat_advantage_weight"], errors="coerce").fillna(1.0).to_numpy(dtype=np.float64)
        if "echosat_advantage_weight" in out.columns
        else np.ones(len(out), dtype=np.float64)
    )
    weighted_advantage = raw_advantage * advantage_weight

    upper = np.full(len(out), np.inf, dtype=np.float64)
    if "echosat_advantage_upper_bound" in out.columns:
        upper = pd.to_numeric(out["echosat_advantage_upper_bound"], errors="coerce").fillna(np.inf).to_numpy(dtype=np.float64)
    final_advantage = np.minimum(weighted_advantage, upper)
    final_advantage = np.nan_to_num(final_advantage, nan=0.0, posinf=0.0, neginf=0.0)

    out["grpo_target_value"] = target_array
    out["grpo_group_mean_cost"] = group_mean
    out["grpo_group_std_cost"] = group_std
    out["grpo_raw_advantage_unclamped"] = raw_unclamped
    out["grpo_raw_advantage"] = raw_advantage
    out["grpo_weighted_advantage_before_clamp"] = weighted_advantage
    out["grpo_final_advantage"] = final_advantage
    out["grpo_positive_raw_advantage_clamped"] = (raw_unclamped > 1.0e-12) & (raw_advantage <= 1.0e-12)
    out["grpo_positive_advantage_clamped"] = (weighted_advantage > 1.0e-12) & (final_advantage <= 1.0e-12)
    out["advantage"] = final_advantage
    return out


def echosat_replay_role(frame: pd.DataFrame, cfg: DictConfig) -> pd.Series:
    role = pd.Series("other", index=frame.index, dtype=object)
    family = frame.get("family", pd.Series("", index=frame.index)).fillna("").astype(str)
    control_type = frame.get("control_type", pd.Series("", index=frame.index)).fillna("").astype(str)
    base = frame.get("base_instance_id", pd.Series("", index=frame.index)).fillna("").astype(str)
    variant = frame.get("variant", pd.Series("", index=frame.index)).fillna("").astype(str)

    subset_base = str(cfg_get(cfg.training, "echosat_subset_failure_base_id", "subset_cardinality_bw12"))
    subset_variant = str(cfg_get(cfg.training, "echosat_subset_failure_variant", "perm_seed1730"))
    role[family.eq("random_3sat_control") | control_type.eq("non_symmetric_control")] = "random_control"
    if subset_base and subset_variant:
        role[base.eq(subset_base) & variant.eq(subset_variant)] = "subset_failure"
    if "echosat_hard_negative_candidate" in frame.columns:
        role[bool_column(frame, "echosat_hard_negative_candidate")] = "hard_negative"
    if "echosat_anchor_candidate" in frame.columns:
        role[bool_column(frame, "echosat_anchor_candidate")] = "anchor"
    if "echosat_anchor_failure" in frame.columns:
        role[bool_column(frame, "echosat_anchor_failure")] = "anchor_failure"
    if "echosat_hard_negative_failure" in frame.columns:
        role[bool_column(frame, "echosat_hard_negative_failure")] = "hard_negative_failure"
    if subset_base and subset_variant:
        role[base.eq(subset_base) & variant.eq(subset_variant)] = "subset_failure"
    return role


def _default_echosat_replay_role(frame: pd.DataFrame) -> pd.Series:
    role = pd.Series("other", index=frame.index, dtype=object)
    family = frame.get("family", pd.Series("", index=frame.index)).fillna("").astype(str)
    control_type = frame.get("control_type", pd.Series("", index=frame.index)).fillna("").astype(str)
    base = frame.get("base_instance_id", pd.Series("", index=frame.index)).fillna("").astype(str)
    variant = frame.get("variant", pd.Series("", index=frame.index)).fillna("").astype(str)

    role[family.eq("random_3sat_control") | control_type.eq("non_symmetric_control")] = "random_control"
    role[base.eq("subset_cardinality_bw12") & variant.eq("perm_seed1730")] = "subset_failure"
    role[bool_column(frame, "echosat_hard_negative_candidate")] = "hard_negative"
    role[bool_column(frame, "echosat_anchor_candidate")] = "anchor"
    role[bool_column(frame, "echosat_anchor_failure")] = "anchor_failure"
    role[bool_column(frame, "echosat_hard_negative_failure")] = "hard_negative_failure"
    role[base.eq("subset_cardinality_bw12") & variant.eq("perm_seed1730")] = "subset_failure"
    return role


def apply_echosat_v18_advantage_repair(
        frame: pd.DataFrame,
        cfg: DictConfig | None = None,
        *,
        hard_negative_pressure_multiplier: float | None = None,
) -> pd.DataFrame:
    out = frame.copy()
    out["echosat_target_mode"] = "symmetry_grpo_v1_8"
    if "echosat_replay_role" in out.columns:
        role = out["echosat_replay_role"].fillna("other").astype(str)
    elif cfg is not None:
        role = echosat_replay_role(out, cfg)
        out["echosat_replay_role"] = role
    else:
        role = _default_echosat_replay_role(out)
        out["echosat_replay_role"] = role

    multiplier = (
        float(hard_negative_pressure_multiplier)
        if hard_negative_pressure_multiplier is not None
        else float(cfg_get(cfg.training, "echosat_v18_hard_negative_pressure_multiplier", 1.25)) if cfg is not None
        else 1.25
    )
    multiplier = max(multiplier, 1.0)

    for column in [
        "echosat_symmetry_reward",
        "echosat_cost",
        "grpo_raw_advantage",
        "grpo_weighted_advantage_before_clamp",
        "grpo_final_advantage",
        "advantage",
    ]:
        if column in out.columns and f"v17_{column}" not in out.columns:
            out[f"v17_{column}"] = numeric_column(out, column, 0.0)

    search_ok = bool_column(out, "echosat_search_ok")
    search_bad = ~search_ok
    blocked_role = role.isin(["random_control", "subset_failure", "anchor_failure", "hard_negative_failure"])
    cpu_only_search_bad = search_bad & (numeric_column(out, "echosat_r_cpu_clipped", 0.0) > 0.0)
    weighted_risk_blocked = bool_column(out, "echosat_positive_blocked_weighted_risk") | (
        numeric_column(out, "echosat_weighted_path_risk_penalty", 0.0) > 0.0
    )
    near_cap_blocked = bool_column(out, "echosat_positive_blocked_near_cap") | (
        numeric_column(out, "echosat_near_cap_penalty", 0.0) > 0.0
    )
    explicit_blocked = (
        bool_column(out, "echosat_positive_blocked_control")
        | bool_column(out, "echosat_positive_blocked_subset_failure")
        | bool_column(out, "echosat_positive_blocked_anchor_failure")
        | bool_column(out, "echosat_positive_blocked_hard_negative_failure")
    )
    result_mismatch = bool_column(out, "echosat_result_mismatch")
    blocked_positive_signal = (
        blocked_role
        | search_bad
        | cpu_only_search_bad
        | weighted_risk_blocked
        | near_cap_blocked
        | explicit_blocked
        | result_mismatch
    )

    out["echosat_v18_blocked_positive_signal"] = blocked_positive_signal
    out["echosat_v18_cpu_only_search_bad"] = cpu_only_search_bad
    out["echosat_v18_weighted_risk_blocked"] = weighted_risk_blocked
    out["echosat_v18_near_cap_blocked"] = near_cap_blocked
    out["echosat_v18_unclamped_positive_blocked"] = blocked_positive_signal & (
        numeric_column(out, "grpo_raw_advantage_unclamped", 0.0) > 1.0e-12
    )

    hard_positive = role.eq("hard_negative") & search_ok & (~blocked_positive_signal)
    pressure_base = (
        numeric_column(out, "echosat_r_search_decisions", 0.0)
        + numeric_column(out, "echosat_r_search_conflicts", 0.0)
        + numeric_column(out, "echosat_r_cpu_clipped", 0.0)
    ).clip(lower=0.0)
    pressure = hard_positive.astype(np.float64) * (multiplier - 1.0) * pressure_base
    out["echosat_v18_hard_negative_pressure"] = pressure

    if "echosat_advantage_weight" in out.columns:
        advantage_weight = numeric_column(out, "echosat_advantage_weight", 1.0)
        advantage_weight.loc[hard_positive] = advantage_weight.loc[hard_positive] * multiplier
        out["echosat_advantage_weight"] = advantage_weight

    raw_upper = numeric_column(out, "echosat_advantage_raw_upper_bound", np.inf)
    final_upper = numeric_column(out, "echosat_advantage_upper_bound", np.inf)
    raw_upper.loc[blocked_positive_signal] = 0.0
    final_upper.loc[blocked_positive_signal] = 0.0
    out["echosat_advantage_raw_upper_bound"] = raw_upper
    out["echosat_advantage_upper_bound"] = final_upper

    if "grpo_raw_advantage" in out.columns:
        raw = numeric_column(out, "grpo_raw_advantage", 0.0)
        raw.loc[blocked_positive_signal] = np.minimum(raw.loc[blocked_positive_signal], 0.0)
        raw.loc[hard_positive] = np.maximum(raw.loc[hard_positive], 0.0) * multiplier
        out["grpo_raw_advantage"] = raw
    if "grpo_weighted_advantage_before_clamp" in out.columns:
        weighted = numeric_column(out, "grpo_weighted_advantage_before_clamp", 0.0)
        weighted.loc[blocked_positive_signal] = np.minimum(weighted.loc[blocked_positive_signal], 0.0)
        weighted.loc[hard_positive] = np.maximum(weighted.loc[hard_positive], 0.0) * multiplier
        out["grpo_weighted_advantage_before_clamp"] = weighted
    if "grpo_final_advantage" in out.columns:
        final = numeric_column(out, "grpo_final_advantage", 0.0)
        final.loc[blocked_positive_signal] = np.minimum(final.loc[blocked_positive_signal], 0.0)
        final.loc[hard_positive] = np.maximum(final.loc[hard_positive], 0.0) * multiplier
        out["grpo_final_advantage"] = final
        out["advantage"] = final
    if "grpo_raw_advantage" in out.columns:
        out["grpo_positive_raw_advantage_clamped"] = (
            numeric_column(out, "v17_grpo_raw_advantage", 0.0) > 1.0e-12
        ) & (numeric_column(out, "grpo_raw_advantage", 0.0) <= 1.0e-12)
    if "grpo_final_advantage" in out.columns:
        out["grpo_positive_advantage_clamped"] = (
            numeric_column(out, "v17_grpo_final_advantage", 0.0) > 1.0e-12
        ) & (numeric_column(out, "grpo_final_advantage", 0.0) <= 1.0e-12)

    if "echosat_symmetry_reward" in out.columns:
        symmetry_reward = numeric_column(out, "echosat_symmetry_reward", 0.0)
        symmetry_reward.loc[hard_positive] = symmetry_reward.loc[hard_positive] * multiplier
        symmetry_reward.loc[blocked_positive_signal] = np.minimum(symmetry_reward.loc[blocked_positive_signal], 0.0)
        out["echosat_symmetry_reward"] = symmetry_reward
    if "echosat_cost" in out.columns:
        cost = numeric_column(out, "echosat_cost", 0.0) - pressure
        if "v17_echosat_cost" in out.columns:
            cost.loc[blocked_positive_signal] = np.maximum(
                cost.loc[blocked_positive_signal],
                numeric_column(out, "v17_echosat_cost", 0.0).loc[blocked_positive_signal],
            )
        out["echosat_cost"] = cost
    return out


def write_echosat_reward_replay_artifacts(
        solver_stats: pd.DataFrame,
        cfg: DictConfig,
        iteration: int,
        global_step: int,
) -> None:
    if not bool(cfg_get(cfg.training, "save_echosat_reward_replay", False)):
        return
    every = int(cfg_get(cfg.training, "save_echosat_reward_replay_every", 1))
    if every <= 0 or int(iteration) % every != 0:
        return

    replay_dir_value = str(cfg_get(cfg.training, "echosat_reward_replay_dir", ""))
    replay_dir = resolve_path(replay_dir_value) if replay_dir_value else resolve_path(Path(str(cfg.model_dir)) / "reward_replay")
    replay_dir.mkdir(parents=True, exist_ok=True)

    frame = solver_stats.copy()
    frame.insert(0, "global_step", int(global_step))
    frame.insert(0, "iteration", int(iteration))
    frame["echosat_replay_role"] = echosat_replay_role(frame, cfg)
    iteration_path = replay_dir / f"iter={int(iteration):06d}_solver_stats.csv"
    _atomic_write_dataframe(frame, iteration_path)

    group_cols = ["echosat_replay_role"]
    for column in ["family", "base_instance_id"]:
        if column in frame.columns:
            group_cols.append(column)
    metric_cols = [
        "echosat_cost",
        "echosat_r_search_decisions",
        "echosat_r_search_conflicts",
        "echosat_r_cpu_clipped",
        "echosat_search_blowup_penalty",
        "echosat_random_control_penalty",
        "echosat_direction_consistency_penalty",
        "echosat_pair_rank_penalty",
        "echosat_consistency_penalty_applied",
        "echosat_large_weight_phase_shift_penalty_applied",
        "echosat_hard_negative_penalty",
        "echosat_anchor_failure_penalty",
        "echosat_subset_failure_penalty",
        "echosat_v18_hard_negative_pressure",
        "grpo_raw_advantage_unclamped",
        "grpo_raw_advantage",
        "grpo_weighted_advantage_before_clamp",
        "grpo_final_advantage",
    ]
    present_metrics = [column for column in metric_cols if column in frame.columns]
    grouped = frame.groupby(group_cols, dropna=False, sort=True)
    summary = grouped[present_metrics].mean().reset_index() if present_metrics else grouped.size().reset_index(name="rows")
    summary["rows"] = grouped.size().to_numpy(dtype=np.int64)
    for column in [
        "echosat_search_ok",
        "echosat_search_blowup",
        "echosat_positive_allowed_search",
        "echosat_positive_allowed",
        "echosat_positive_blocked_control",
        "echosat_positive_blocked_subset_failure",
        "echosat_positive_blocked_weighted_risk",
        "echosat_positive_blocked_near_cap",
        "echosat_positive_blocked_pair_inconsistency",
        "echosat_positive_blocked_anchor_failure",
        "echosat_positive_blocked_hard_negative_failure",
        "echosat_v18_blocked_positive_signal",
        "echosat_v18_cpu_only_search_bad",
        "echosat_v18_weighted_risk_blocked",
        "echosat_v18_near_cap_blocked",
        "echosat_v18_unclamped_positive_blocked",
        "grpo_positive_raw_advantage_clamped",
        "grpo_positive_advantage_clamped",
    ]:
        if column in frame.columns:
            summary[f"{column}_frac"] = grouped[column].mean().to_numpy(dtype=np.float64)
    summary.insert(0, "global_step", int(global_step))
    summary.insert(0, "iteration", int(iteration))
    summary_path = replay_dir / "summary.csv"
    if summary_path.exists():
        existing = pd.read_csv(summary_path)
        if {"iteration", "global_step"}.issubset(existing.columns):
            same_run = (
                pd.to_numeric(existing["iteration"], errors="coerce").eq(int(iteration))
                & pd.to_numeric(existing["global_step"], errors="coerce").eq(int(global_step))
            )
            existing = existing.loc[~same_run]
        summary = pd.concat([existing, summary], ignore_index=True, sort=False)
    _atomic_write_dataframe(summary, summary_path)


def _atomic_write_dataframe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            frame.to_csv(handle, index=False)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _atomic_omegaconf_save(config: DictConfig, path: Path) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            OmegaConf.save(config, handle)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _atomic_torch_save(state_dict: dict, path: Path, *, immutable: bool) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
        torch.save(state_dict, temp_path)
        if immutable:
            try:
                os.link(temp_path, path)
            except FileExistsError as exc:
                raise ValueError(f"checkpoint already exists: {path}") from exc
        else:
            os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def save_model(model: GNN, cfg: DictConfig, checkpoint_name: str = "last", model_cfg: DictConfig | None = None) -> None:
    model_dir = Path(str(cfg.model_dir))
    model_dir.mkdir(parents=True, exist_ok=True)
    model_cfg = cfg if model_cfg is None else model_cfg
    cfg_path = model_dir / "config.yaml"
    training_cfg_path = model_dir / "training_config.yaml"
    ckpt_path = model_dir / f"{checkpoint_name}.pt"
    immutable = checkpoint_name.startswith("iter=")
    if immutable and ckpt_path.exists():
        raise ValueError(f"checkpoint already exists: {ckpt_path}")
    _atomic_omegaconf_save(model_cfg, cfg_path)
    _atomic_omegaconf_save(cfg, training_cfg_path)
    state_dict = model.state_dict()
    _atomic_torch_save(state_dict, ckpt_path, immutable=immutable)


def build_feedback_state_loader(
        model: GNN,
        dataset: DimacsCNFDataset,
        loader: DataLoader,
        cfg: DictConfig,
        device: torch.device | str,
        max_num_batches: int = -1,
        mode: str | None = None,
        shuffle: bool = True,
        orbit_store: OrbitFeatureStore | None = None,
) -> DataLoader:
    mode = cfg.training.feedback_input_mode if mode is None else mode
    if mode == "none":
        return loader

    feedback_state_type = str(cfg_get(cfg.training, "feedback_state_type", "global"))
    global_state_dim = int(getattr(model, "global_state_dim", 0))
    var_state_dim = int(getattr(model, "var_state_dim", 0))
    if feedback_state_type == "global" and global_state_dim <= 0:
        raise ValueError("global feedback requires model.global_state_dim > 0")
    if feedback_state_type == "event_var" and var_state_dim <= 0:
        raise ValueError("event_var feedback requires model.var_state_dim > 0")

    if mode == "mixed_warmup":
        mode = "model_warmup" if np.random.random() < cfg.training.feedback_model_warmup_prob else "random_warmup"

    if mode == "random_warmup":
        warmup_data_list = sample_random_var_params(
            loader=loader,
            num_samples=cfg.training.feedback_warmup_num_samples,
            max_num_batches=max_num_batches,
            weight_scale=cfg.training.feedback_random_weight,
        )
    elif mode == "model_warmup":
        warmup_data_list = sample_var_params(
            model=model,
            loader=loader,
            num_samples=cfg.training.feedback_warmup_num_samples,
            max_num_batches=max_num_batches,
            device=device,
            use_mode=True,
            scale_sigma=cfg.scale_sigma,
        )
    else:
        raise ValueError(f"Unknown feedback_input_mode {mode}")

    warmup_params = solver_params(cfg)
    warmup_budget_type = str(cfg_get(cfg.training, "feedback_warmup_budget_type", "cpu_time"))
    warmup_params["cpu-lim"] = cfg.training.feedback_warmup_cpu_lim
    if warmup_budget_type == "conflicts":
        warmup_params["conf-lim"] = int(cfg_get(cfg.training, "feedback_warmup_conflicts", 500))
    elif warmup_budget_type != "cpu_time":
        raise ValueError(f"Unknown feedback_warmup_budget_type={warmup_budget_type!r}")
    if feedback_state_type == "event_var":
        warmup_params["collect-events"] = True
        warmup_params["trace-lbd"] = int(cfg_get(cfg.training, "feedback_trace_lbd", 2))
    warmup_stats = compute_solver_stats(
        dataset=dataset,
        data_list=warmup_data_list,
        num_workers=cfg.solver.num_workers,
        solver=cfg.solver.solver,
        **warmup_params,
    )
    if feedback_state_type == "global":
        refined_graphs = attach_global_state_batch(
            warmup_data_list,
            warmup_stats,
            global_state_dim=global_state_dim,
        )
    elif feedback_state_type == "event_var":
        refined_graphs = attach_var_event_state_batch(
            warmup_data_list,
            warmup_stats,
            var_state_dim=var_state_dim,
            momentum=float(cfg_get(cfg.training, "feedback_state_momentum", 0.0)),
            feature_mode=str(cfg_get(cfg.training, "feedback_event_state_features", "legacy")),
        )
    else:
        raise ValueError(f"Unknown feedback_state_type={feedback_state_type!r}")
    if orbit_store is not None:
        refined_graphs = attach_echosat_v2_orbits(refined_graphs, orbit_store)

    stats_by_cnf = {
        int(cnf_id): group.sort_values("sample_id").iloc[0]
        for cnf_id, group in warmup_stats.groupby("cnf_id", sort=False)
    }
    for graph in refined_graphs:
        cnf_id = int(graph.cnf_id.item() if hasattr(graph.cnf_id, "item") else graph.cnf_id)
        stats = stats_by_cnf.get(cnf_id)
        attach_warmup_graph_evidence(graph, {} if stats is None else stats)
    return DataLoader(
        dataset=refined_graphs,
        batch_size=cfg.loader.batch_size,
        num_workers=cfg.loader.num_workers,
        shuffle=shuffle,
    )


@hydra.main(version_base=None, config_path="configs", config_name="config_train_rlaf")
def main(cfg: DictConfig):
    OmegaConf.resolve(cfg)
    validate_replay_only_config(cfg)
    allow_model_updates = model_updates_enabled(cfg)
    validate_training_output_directory(cfg)
    print(OmegaConf.to_yaml(cfg))
    seed_everything(cfg.seed)

    wandb_kwargs = {
        "project": cfg.wandb.project,
        "name": cfg.wandb.name,
        "config": OmegaConf.to_container(cfg),
    }
    if "mode" in cfg.wandb:
        wandb_kwargs["mode"] = cfg.wandb.mode
    wandb.init(**wandb_kwargs)

    model, transform, model_cfg = load_training_model(cfg)

    dataset_train = DimacsCNFDataset(
        path=dataset_path_from_config(cfg.dataset.train_path),
        transform=transform,
        lazy=bool(cfg_get(cfg.dataset, "lazy", False)),
    )
    training_manifest = load_training_manifest(cfg)
    train_metadata = dataset_metadata(dataset_train, training_manifest, required=uses_echosat_target(cfg))
    train_orbit_store = load_echosat_v2_orbit_store(cfg, train_metadata)
    loader_train = DataLoader(
        dataset=dataset_train,
        batch_size=cfg.loader.batch_size,
        num_workers=cfg.loader.num_workers,
        shuffle=True,
    )

    dataset_val, val_metadata, val_orbit_store, loader_val = build_validation_runtime(
        cfg=cfg,
        transform=transform,
        training_manifest=training_manifest,
        allow_model_updates=allow_model_updates,
    )

    assert cfg.training.cnf_per_iter % cfg.loader.batch_size == 0
    train_sample_num_batches = cfg.training.cnf_per_iter // cfg.loader.batch_size

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Using device {device}")
    trainable_parameters = configure_trainable_parameters(model, cfg)
    optim, sched = build_training_optimizer_scheduler(trainable_parameters, cfg)

    if allow_model_updates and cfg.ckpt_interval is not None:
        print(f"Saving checkpoint at iteration 0")
        save_model(model, cfg, f"iter=0", model_cfg=model_cfg)

    best_score = np.inf
    best_objective = best_checkpoint_mode(cfg)
    best_score_maximize = best_objective in {"echosat_strict_search_work", "echosat_strict_search_work_v2"}
    if best_objective not in {"target_stat_mean", "echosat_strict_search_work", "echosat_strict_search_work_v2"}:
        raise ValueError(f"Unsupported training.best_checkpoint_metric={best_objective!r}")
    if best_score_maximize:
        best_score = -np.inf

    global_step = 0
    for iteration in range(cfg.training.iterations):
        print(f" ----------------------- {'GRPO' if cfg.method == 'grpo' else 'DPO'} Iteration {iteration} ----------------------- ")

        # validate if necessary
        skip_initial_val = bool(cfg_get(cfg, "skip_initial_val", False))
        if (
            allow_model_updates
            and iteration % cfg.val_interval == 0
            and not (iteration == 0 and skip_initial_val)
        ):
            loader_val_current = build_feedback_state_loader(
                model=model,
                dataset=dataset_val,
                loader=loader_val,
                cfg=cfg,
                device=device,
                mode=cfg.training.feedback_val_mode,
                shuffle=False,
                orbit_store=val_orbit_store,
            )
            data_list_val = sample_var_params(
                model=model,
                loader=loader_val_current,
                num_samples=1,
                device=device,
                use_mode=True,
                scale_sigma=cfg.scale_sigma,
            )

            solver_stats_val = compute_solver_stats(
                dataset=dataset_val,
                data_list=data_list_val,
                num_workers=cfg.solver.num_workers,
                solver=cfg.solver.solver,
                **solver_params(cfg),
            )
            baseline_stats_val = None
            baseline_stats_by_name_val = {}
            static_data_list_val = None
            if uses_speedup_target(cfg):
                baseline_data_list_val = build_speedup_baseline_data_list(data_list_val, cfg)
                if baseline_data_list_val is not None:
                    baseline_stats_val = compute_solver_stats(
                        dataset=dataset_val,
                        data_list=baseline_data_list_val,
                        num_workers=cfg.solver.num_workers,
                        solver=cfg.solver.solver,
                        **solver_params(cfg),
                    )
            if uses_echosat_target(cfg):
                neutral_data_list_val = build_speedup_baseline_data_list(data_list_val, cfg)
                if neutral_data_list_val is not None:
                    baseline_stats_by_name_val["neutral_weighted"] = compute_solver_stats(
                        dataset=dataset_val,
                        data_list=neutral_data_list_val,
                        num_workers=cfg.solver.num_workers,
                        solver=cfg.solver.solver,
                        **solver_params(cfg),
                    )
                static_data_list_val = build_static_baseline_data_list(model, data_list_val, cfg, device)
                baseline_stats_by_name_val["static_weighted"] = compute_solver_stats(
                    dataset=dataset_val,
                    data_list=static_data_list_val,
                    num_workers=cfg.solver.num_workers,
                    solver=cfg.solver.solver,
                    **solver_params(cfg),
                )
                ensure_plain_unguided_baseline(
                    baseline_stats_by_name_val,
                    dataset_val,
                    data_list_val,
                    cfg,
                )
            solver_stats_val = add_training_targets(
                solver_stats_val,
                cfg,
                baseline_stats=baseline_stats_val,
                baseline_stats_by_name=baseline_stats_by_name_val,
                metadata=val_metadata,
                data_list=data_list_val,
                static_data_list=static_data_list_val,
            )

            log_solver_metrics(
                solver_stats=solver_stats_val,
                iteration=iteration,
                global_step=global_step,
                prefix="val",
                add_target_histogram=True,
                target_stat=cfg.training.target_stat
            )

            best_gate_pass = True
            if best_objective in {"echosat_strict_search_work", "echosat_strict_search_work_v2"}:
                if best_objective == "echosat_strict_search_work_v2":
                    score, best_metrics = strict_search_work_validation_score_v2(solver_stats_val, cfg)
                    best_gate_pass = bool(best_metrics.get("best_checkpoint_gate_pass", 0.0) >= 0.5)
                else:
                    score, best_metrics = strict_search_work_validation_score(solver_stats_val, cfg)
                metrics = {
                    f"val_best/{name}": value
                    for name, value in best_metrics.items()
                }
                metrics["iteration"] = iteration
                metrics["global_step"] = global_step
                wandb.log(metrics, step=global_step)
                print(
                    f"Best-checkpoint metric at iteration {iteration}: "
                    f"{best_objective}={score:.6f}"
                )
            else:
                score = solver_stats_val[cfg.training.target_stat].mean()

            improved = score > best_score if best_score_maximize else score < best_score
            if best_objective == "echosat_strict_search_work_v2" and bool(
                cfg_get(cfg.training, "best_checkpoint_require_gate_pass", True)
            ) and not best_gate_pass:
                improved = False
                print("Best checkpoint gate failed; not saving best checkpoint for this validation.")
            if allow_model_updates and improved:
                print("Saving new best checkpoint")
                save_model(model, cfg, "best", model_cfg=model_cfg)
                best_score = score

        if str(cfg_get(cfg.training, "echosat_sampling_mode", "default")).lower() == "base_group":
            loader_train_iteration, feedback_max_batches = build_base_group_iteration_loader(
                dataset=dataset_train,
                metadata=train_metadata,
                cfg=cfg,
                iteration=iteration,
            )
        else:
            loader_train_iteration = loader_train
            feedback_max_batches = train_sample_num_batches

        loader_train_current = build_feedback_state_loader(
            model=model,
            dataset=dataset_train,
            loader=loader_train_iteration,
            cfg=cfg,
            device=device,
            max_num_batches=feedback_max_batches,
            shuffle=True,
            orbit_store=train_orbit_store,
        )

        data_list_train = sample_var_params(
            model=model,
            loader=loader_train_current,
            num_samples=cfg.training.num_samples,
            max_num_batches=feedback_max_batches,
            device=device,
            scale_sigma=cfg.scale_sigma,
        )

        solver_stats = compute_solver_stats(
            dataset=dataset_train,
            data_list=data_list_train,
            num_workers=cfg.solver.num_workers,
            solver=cfg.solver.solver,
            **solver_params(cfg),
        )
        baseline_stats = None
        baseline_stats_by_name = {}
        static_data_list_train = None
        if uses_speedup_target(cfg):
            baseline_data_list = build_speedup_baseline_data_list(data_list_train, cfg)
            if baseline_data_list is not None:
                baseline_stats = compute_solver_stats(
                    dataset=dataset_train,
                    data_list=baseline_data_list,
                    num_workers=cfg.solver.num_workers,
                    solver=cfg.solver.solver,
                    **solver_params(cfg),
                )
        if uses_echosat_target(cfg):
            neutral_data_list_train = build_speedup_baseline_data_list(data_list_train, cfg)
            if neutral_data_list_train is not None:
                baseline_stats_by_name["neutral_weighted"] = compute_solver_stats(
                    dataset=dataset_train,
                    data_list=neutral_data_list_train,
                    num_workers=cfg.solver.num_workers,
                    solver=cfg.solver.solver,
                    **solver_params(cfg),
                )
            static_data_list_train = build_static_baseline_data_list(model, data_list_train, cfg, device)
            baseline_stats_by_name["static_weighted"] = compute_solver_stats(
                dataset=dataset_train,
                data_list=static_data_list_train,
                num_workers=cfg.solver.num_workers,
                solver=cfg.solver.solver,
                **solver_params(cfg),
            )
            ensure_plain_unguided_baseline(
                baseline_stats_by_name,
                dataset_train,
                data_list_train,
                cfg,
            )
        solver_stats = add_training_targets(
            solver_stats,
            cfg,
            baseline_stats=baseline_stats,
            baseline_stats_by_name=baseline_stats_by_name,
            metadata=train_metadata,
            data_list=data_list_train,
            static_data_list=static_data_list_train,
        )
        if cfg.method == "grpo" and uses_echosat_target(cfg):
            solver_stats = attach_grpo_advantage_columns(solver_stats, cfg)

        log_solver_metrics(
            solver_stats=solver_stats,
            iteration=iteration,
            global_step=global_step,
            prefix="train",
            add_target_histogram=True,
            target_stat=cfg.training.target_stat,
        )

        if cfg.method == "grpo" and not uses_echosat_target(cfg):
            solver_stats["advantage"] = get_grpo_advantage(solver_stats, cfg.training.target_stat)

        artifact_writer = lambda: None
        if cfg.method == "grpo" and uses_echosat_target(cfg):
            if "advantage" not in solver_stats.columns:
                solver_stats = attach_grpo_advantage_columns(solver_stats, cfg)
            artifact_writer = lambda: write_echosat_reward_replay_artifacts(
                solver_stats=solver_stats,
                cfg=cfg,
                iteration=iteration,
                global_step=global_step,
            )

        def training_update():
            if cfg.method == "grpo":
                iteration_dataset = RLTrainingDataset(
                    data_list=data_list_train,
                    solver_stats=solver_stats,
                    target_stat="advantage",
                    objective="maximize",
                )
            else:
                iteration_dataset = RLTrainingDataset(
                    data_list=data_list_train,
                    solver_stats=solver_stats,
                    target_stat=cfg.training.target_stat,
                )

            iteration_loader = DataLoader(
                dataset=iteration_dataset,
                batch_size=cfg.loader.batch_size,
                num_workers=cfg.loader.num_workers,
                shuffle=True,
            )

            if cfg.method == "grpo":
                return train_grpo(
                    model=model,
                    optim=optim,
                    sched=sched,
                    loader=iteration_loader,
                    steps=cfg.training.steps_per_iter,
                    clip_ratio=cfg.training.clip_ratio,
                    kl_penalty=cfg.training.kl_penalty,
                    global_step=global_step,
                    device=device,
                    use_amp=cfg.training.use_amp,
                    scale_sigma=cfg.scale_sigma,
                )
            return train_dpo(
                model=model,
                optim=optim,
                sched=sched,
                loader=iteration_loader,
                steps=cfg.training.steps_per_iter,
                beta=cfg.training.beta,
                kl_penalty=cfg.training.kl_penalty,
                global_step=global_step,
                device=device,
                use_amp=cfg.training.use_amp,
                scale_sigma=cfg.scale_sigma,
            )

        next_global_step = run_training_update_after_replay_artifacts(
            cfg,
            artifact_writer,
            training_update,
        )
        if not allow_model_updates:
            continue
        global_step = next_global_step

        checkpoint_name = completed_iteration_checkpoint_name(
            iteration,
            cfg.ckpt_interval if allow_model_updates else None,
        )
        if checkpoint_name is not None:
            completed_iteration = iteration + 1
            print(f"Saving checkpoint at completed iteration {completed_iteration}")
            save_model(model, cfg, checkpoint_name, model_cfg=model_cfg)

    wandb.finish()


if __name__ == '__main__':
    main()
