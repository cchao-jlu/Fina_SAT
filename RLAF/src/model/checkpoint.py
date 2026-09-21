from __future__ import annotations

import torch


def _prefix_extended_tensor(source: torch.Tensor, target: torch.Tensor) -> torch.Tensor | None:
    if source.ndim != target.ndim:
        return None
    if any(src > dst for src, dst in zip(source.shape, target.shape)):
        return None
    if tuple(source.shape) == tuple(target.shape):
        return source

    expanded = torch.zeros_like(target)
    slices = tuple(slice(0, size) for size in source.shape)
    expanded[slices] = source.to(dtype=target.dtype)
    return expanded


def load_compatible_state_dict(
    model: torch.nn.Module,
    ckpt_path: str,
) -> tuple[list[str], list[str]]:
    checkpoint_state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    model_state = model.state_dict()
    compatible_state = {}
    skipped = []
    for key, value in checkpoint_state.items():
        target = model_state.get(key)
        if target is None:
            skipped.append(key)
            continue
        extended = _prefix_extended_tensor(value, target)
        if extended is None:
            skipped.append(key)
            continue
        compatible_state[key] = extended

    missing, unexpected = model.load_state_dict(compatible_state, strict=False)
    skipped.extend(unexpected)
    return sorted(compatible_state), sorted(set(skipped + list(missing)))
