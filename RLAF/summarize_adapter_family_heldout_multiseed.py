from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


def truthy_series(frame: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=bool)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(default).astype(bool)
    normalized = values.fillna(str(default)).astype(str).str.strip().str.lower()
    return normalized.isin({"1", "true", "yes", "y"})


def valid_rows(frame: pd.DataFrame) -> pd.DataFrame:
    mask = truthy_series(frame, "event_row_valid", default=False)
    if "orbit_valid" in frame.columns:
        mask &= truthy_series(frame, "orbit_valid", default=True)
    return frame[mask].copy()


def numeric_mean(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return float("nan")
    return float(pd.to_numeric(frame[column], errors="coerce").mean())


def numeric_max(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return float("nan")
    return float(pd.to_numeric(frame[column], errors="coerce").max())


def baseline_gain_by_family(baseline: pd.DataFrame | None) -> dict[str, float]:
    if baseline is None or baseline.empty or "family" not in baseline.columns:
        return {}
    base_valid = valid_rows(baseline)
    if base_valid.empty or "adapter_identity_gain" not in base_valid.columns:
        return {}
    return {
        str(family): float(group["adapter_identity_gain"].mean())
        for family, group in base_valid.groupby("family", sort=True)
        if not group.empty
    }


def ensure_seed_columns(frame: pd.DataFrame, source_csv: Path, seed: int | None = None) -> pd.DataFrame:
    frame = frame.copy()
    if "train_seed" not in frame.columns:
        if seed is None:
            raise ValueError(f"{source_csv} has no train_seed column and no --seed override was provided")
        frame["train_seed"] = int(seed)
    frame["source_csv"] = str(source_csv)
    return frame


def summarize_seed_runs(frame: pd.DataFrame, baseline: pd.DataFrame | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    baseline_by_family = baseline_gain_by_family(baseline)
    for (heldout, seed), group in frame.groupby(["heldout_family", "train_seed"], sort=True):
        valid = valid_rows(group)
        train = valid[valid["adapter_train_split"].astype(str) == "train"]
        held = valid[valid["adapter_train_split"].astype(str) == "heldout"]
        all_train = group[group["adapter_train_split"].astype(str) == "train"]
        all_held = group[group["adapter_train_split"].astype(str) == "heldout"]
        train_gain = numeric_mean(train, "adapter_identity_gain")
        held_gain = numeric_mean(held, "adapter_identity_gain")
        full_gain = baseline_by_family.get(str(heldout), float("nan"))
        rows.append(
            {
                "heldout_family": str(heldout),
                "train_seed": int(seed),
                "train_eval_families": int(all_train["family"].nunique()) if not all_train.empty else 0,
                "train_valid_families": int(train["family"].nunique()) if not train.empty else 0,
                "heldout_eval_instances": int(all_held["instance_id"].nunique()) if not all_held.empty else 0,
                "heldout_valid_instances": int(held["instance_id"].nunique()) if not held.empty else 0,
                "heldout_orbit_rows": int(len(all_held)),
                "train_valid_rows": int(len(train)),
                "heldout_valid_rows": int(len(held)),
                "train_mean_adapter_gain_valid": train_gain,
                "heldout_mean_adapter_gain_valid": held_gain,
                "heldout_minus_train_gain": held_gain - train_gain,
                "heldout_mean_adapted_mu_range_valid": numeric_mean(held, "adapted_mu_range"),
                "heldout_max_adapted_mu_range_valid": numeric_max(held, "adapted_mu_range"),
                "full_adapter_mean_gain_for_heldout_family": full_gain,
                "heldout_minus_full_adapter_gain": held_gain - full_gain,
            }
        )
    return pd.DataFrame(rows)


def bootstrap_ci(values: pd.Series | np.ndarray, seed: int, samples: int, alpha: float) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return float("nan"), float("nan")
    if array.size == 1 or samples <= 0:
        value = float(array.mean())
        return value, value
    rng = np.random.default_rng(int(seed))
    draws = rng.choice(array, size=(int(samples), array.size), replace=True).mean(axis=1)
    low = float(np.quantile(draws, alpha / 2.0))
    high = float(np.quantile(draws, 1.0 - alpha / 2.0))
    return low, high


def summarize_multiseed(
    seed_summary: pd.DataFrame,
    bootstrap_seed: int = 1729,
    bootstrap_samples: int = 10000,
    alpha: float = 0.05,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for heldout, group in seed_summary.groupby("heldout_family", sort=True):
        gains = pd.to_numeric(group["heldout_mean_adapter_gain_valid"], errors="coerce")
        minus_full = pd.to_numeric(group["heldout_minus_full_adapter_gain"], errors="coerce")
        train_gains = pd.to_numeric(group["train_mean_adapter_gain_valid"], errors="coerce")
        low, high = bootstrap_ci(gains, seed=bootstrap_seed, samples=bootstrap_samples, alpha=alpha)
        mf_low, mf_high = bootstrap_ci(minus_full, seed=bootstrap_seed + 1, samples=bootstrap_samples, alpha=alpha)
        finite_gains = gains[np.isfinite(gains)]
        rows.append(
            {
                "heldout_family": str(heldout),
                "seeds": int(group["train_seed"].nunique()),
                "seed_list": ",".join(str(int(seed)) for seed in sorted(group["train_seed"].unique())),
                "heldout_valid_rows": int(pd.to_numeric(group["heldout_valid_rows"], errors="coerce").max())
                if not group.empty
                else 0,
                "heldout_valid_instances": int(pd.to_numeric(group["heldout_valid_instances"], errors="coerce").max())
                if not group.empty
                else 0,
                "heldout_gain_mean": float(finite_gains.mean()) if finite_gains.size else float("nan"),
                "heldout_gain_std": float(finite_gains.std(ddof=1)) if finite_gains.size > 1 else 0.0 if finite_gains.size == 1 else float("nan"),
                "heldout_gain_min": float(finite_gains.min()) if finite_gains.size else float("nan"),
                "heldout_gain_max": float(finite_gains.max()) if finite_gains.size else float("nan"),
                "heldout_gain_bootstrap_ci_low": low,
                "heldout_gain_bootstrap_ci_high": high,
                "positive_gain_seeds": int((finite_gains > 0.0).sum()) if finite_gains.size else 0,
                "train_gain_mean": float(train_gains.mean()) if np.isfinite(train_gains).any() else float("nan"),
                "heldout_minus_train_gain_mean": numeric_mean(group, "heldout_minus_train_gain"),
                "full_adapter_mean_gain_for_heldout_family": numeric_mean(group, "full_adapter_mean_gain_for_heldout_family"),
                "heldout_minus_full_adapter_gain_mean": numeric_mean(group, "heldout_minus_full_adapter_gain"),
                "heldout_minus_full_bootstrap_ci_low": mf_low,
                "heldout_minus_full_bootstrap_ci_high": mf_high,
            }
        )
    return pd.DataFrame(rows)


def summarize_eval_family(frame: pd.DataFrame) -> pd.DataFrame:
    seed_rows: list[dict[str, object]] = []
    for (heldout, seed, family, split), group in frame.groupby(
        ["heldout_family", "train_seed", "family", "adapter_train_split"],
        sort=True,
    ):
        valid = valid_rows(group)
        seed_rows.append(
            {
                "heldout_family": str(heldout),
                "train_seed": int(seed),
                "eval_family": str(family),
                "adapter_train_split": str(split),
                "valid_rollout_rows": int(len(valid)),
                "mean_adapter_gain_valid": numeric_mean(valid, "adapter_identity_gain"),
                "mean_adapted_mu_range_valid": numeric_mean(valid, "adapted_mu_range"),
                "max_adapted_mu_range_valid": numeric_max(valid, "adapted_mu_range"),
            }
        )
    seed_frame = pd.DataFrame(seed_rows)
    if seed_frame.empty:
        return seed_frame
    rows: list[dict[str, object]] = []
    for (heldout, family, split), group in seed_frame.groupby(
        ["heldout_family", "eval_family", "adapter_train_split"],
        sort=True,
    ):
        gains = pd.to_numeric(group["mean_adapter_gain_valid"], errors="coerce")
        finite = gains[np.isfinite(gains)]
        rows.append(
            {
                "heldout_family": str(heldout),
                "eval_family": str(family),
                "adapter_train_split": str(split),
                "seeds": int(group["train_seed"].nunique()),
                "valid_rollout_rows": int(pd.to_numeric(group["valid_rollout_rows"], errors="coerce").max()),
                "mean_adapter_gain_valid_mean": float(finite.mean()) if finite.size else float("nan"),
                "mean_adapter_gain_valid_std": float(finite.std(ddof=1)) if finite.size > 1 else 0.0 if finite.size == 1 else float("nan"),
                "mean_adapted_mu_range_valid_mean": numeric_mean(group, "mean_adapted_mu_range_valid"),
                "max_adapted_mu_range_valid_max": numeric_max(group, "max_adapted_mu_range_valid"),
            }
        )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> list[str]:
    if frame.empty:
        return ["_None._"]
    view = frame.copy()
    if max_rows is not None:
        view = view.head(int(max_rows))
    columns = list(view.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in view.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                if math.isnan(value):
                    values.append("nan")
                else:
                    values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_doc(
    path: Path,
    summary: pd.DataFrame,
    seed_summary: pd.DataFrame,
    eval_family: pd.DataFrame,
    inputs: list[Path],
    baseline_csv: Path,
    bootstrap_samples: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Adapter Family-Heldout Multi-Seed Audit",
        "",
        "This is a representation-only leave-one-family-out adapter audit.",
        "Each heldout family is trained with multiple adapter initialization",
        "seeds on cached event traces from the other families, then evaluated",
        "on the same cached event-state audit set. No solver speedup or runtime",
        "claim is made here.",
        "",
        f"Bootstrap intervals are over seed-level heldout means with {bootstrap_samples} resamples.",
        f"The full-adapter baseline is `{baseline_csv}`.",
        "",
        "## Multi-Seed Summary",
        "",
        *markdown_table(summary),
        "",
        "## Seed-Level Summary",
        "",
        *markdown_table(seed_summary, max_rows=120),
        "",
        "## Evaluation Family Matrix",
        "",
        *markdown_table(eval_family, max_rows=160),
        "",
        "## Inputs",
        "",
        *[f"- `{path}`" for path in inputs],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize multi-seed leave-one-family-out adapter audits.")
    parser.add_argument("--input-csv", type=Path, action="append", required=True)
    parser.add_argument("--seed", type=int, action="append", default=None)
    parser.add_argument("--baseline-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_neggate_event_orbits.csv")
    parser.add_argument("--output-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_neggate_family_heldout_multiseed_by_family.csv")
    parser.add_argument("--seed-summary-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_neggate_family_heldout_multiseed_seed_summary.csv")
    parser.add_argument("--eval-family-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_neggate_family_heldout_multiseed_eval_family.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_adapter_neggate_family_heldout_multiseed_audit.md")
    parser.add_argument("--bootstrap-seed", type=int, default=1729)
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    args = parser.parse_args()

    if args.seed is not None and len(args.seed) != len(args.input_csv):
        raise ValueError("--seed must be provided once per --input-csv when used")
    frames = []
    for idx, path in enumerate(args.input_csv):
        seed = args.seed[idx] if args.seed is not None else None
        frames.append(ensure_seed_columns(pd.read_csv(path), source_csv=path, seed=seed))
    frame = pd.concat(frames, ignore_index=True)
    baseline = pd.read_csv(args.baseline_csv) if args.baseline_csv.exists() else None
    seed_summary = summarize_seed_runs(frame, baseline=baseline)
    summary = summarize_multiseed(
        seed_summary,
        bootstrap_seed=int(args.bootstrap_seed),
        bootstrap_samples=int(args.bootstrap_samples),
    )
    eval_family = summarize_eval_family(frame)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_csv, index=False)
    args.seed_summary_csv.parent.mkdir(parents=True, exist_ok=True)
    seed_summary.to_csv(args.seed_summary_csv, index=False)
    args.eval_family_csv.parent.mkdir(parents=True, exist_ok=True)
    eval_family.to_csv(args.eval_family_csv, index=False)
    write_doc(
        args.doc,
        summary=summary,
        seed_summary=seed_summary,
        eval_family=eval_family,
        inputs=args.input_csv,
        baseline_csv=args.baseline_csv,
        bootstrap_samples=int(args.bootstrap_samples),
    )
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.seed_summary_csv}")
    print(f"wrote {args.eval_family_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
