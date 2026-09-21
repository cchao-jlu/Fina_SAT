from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent


TARGET_BASES = ["k9_color8", "php_p9_h8", "k10_color9", "php_p10_h9"]
ANCHOR_BASES = ["k9_color8", "php_p9_h8"]
HARD_NEGATIVE_BASES = ["k10_color9", "php_p10_h9"]
SUBSET_FAILURE_BASE = "subset_cardinality_bw12"
SUBSET_FAILURE_VARIANT = "perm_seed1730"


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def checkpoint_order(label: str) -> float:
    match = re.fullmatch(r"iter=(\d+)", str(label))
    if match:
        return float(match.group(1))
    return math.inf


def read_observations(prefix: str, checkpoints: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for checkpoint in checkpoints:
        path = ROOT / "runs/analysis" / f"{prefix}_{checkpoint}_canonical_low_warmup_observations.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        if "checkpoint" in frame.columns:
            frame["checkpoint"] = checkpoint
        else:
            frame.insert(0, "checkpoint", checkpoint)
        if "checkpoint_order" in frame.columns:
            frame["checkpoint_order"] = checkpoint_order(checkpoint)
        else:
            frame.insert(1, "checkpoint_order", checkpoint_order(checkpoint))
        frames.append(frame)
    if not frames:
        raise ValueError("no observations were loaded")
    out = pd.concat(frames, ignore_index=True)
    out["search_ok"] = (out["adapter_cached_decisions_delta"] < 0) & (out["adapter_cached_conflicts_delta"] < 0)
    out["search_blowup"] = (out["adapter_cached_decisions_delta"] > 0) | (out["adapter_cached_conflicts_delta"] > 0)
    out["random_control"] = (
        out["family"].astype(str).eq("random_3sat_control")
        | out["control_type"].astype(str).eq("non_symmetric_control")
    )
    return out


def summarize_group(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(group_cols, sort=True, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        row = {column: value for column, value in zip(group_cols, key)}
        row.update(
            {
                "rows": int(len(group)),
                "search_ok_frac": float(group["search_ok"].mean()),
                "search_blowup_frac": float(group["search_blowup"].mean()),
                "adapter_cached_cpu_delta_mean": float(group["adapter_cached_final_cpu_delta"].mean()),
                "adapter_cached_cpu_delta_median": float(group["adapter_cached_final_cpu_delta"].median()),
                "adapter_cached_decisions_delta_mean": float(group["adapter_cached_decisions_delta"].mean()),
                "adapter_cached_conflicts_delta_mean": float(group["adapter_cached_conflicts_delta"].mean()),
                "adapter_plain_protocol_delta_mean": float(group["adapter_plain_protocol_delta"].mean()),
                "adapter_plain_protocol_improved_frac": float(group["adapter_plain_protocol_improved"].mean()),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def base_metric(frame: pd.DataFrame, base: str, warmup: int, column: str) -> float:
    rows = frame[(frame["warmup_conflicts"].eq(warmup)) & frame["base_instance_id"].astype(str).eq(base)]
    if rows.empty:
        return float("nan")
    return float(rows[column].mean())


def variant_metric(frame: pd.DataFrame, base: str, variant: str, warmup: int, column: str) -> float:
    rows = frame[
        (frame["warmup_conflicts"].eq(warmup))
        & frame["base_instance_id"].astype(str).eq(base)
        & frame["variant"].astype(str).eq(variant)
    ]
    if rows.empty:
        return float("nan")
    return float(rows[column].mean())


def strict_acceptance(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (checkpoint, order, warmup), group in frame.groupby(
        ["checkpoint", "checkpoint_order", "warmup_conflicts"],
        sort=True,
        dropna=False,
    ):
        anchors = [base_metric(group, base, int(warmup), "search_ok") for base in ANCHOR_BASES]
        hard_negatives = [base_metric(group, base, int(warmup), "search_ok") for base in HARD_NEGATIVE_BASES]
        subset_perm = variant_metric(group, SUBSET_FAILURE_BASE, SUBSET_FAILURE_VARIANT, int(warmup), "search_ok")
        random_rows = group[group["random_control"]]
        target_rows = group[group["base_instance_id"].astype(str).isin(TARGET_BASES)]
        strong_rows = group[group["symmetry_strength"].astype(str).eq("strong")]

        anchor_min = min(anchors) if all(math.isfinite(value) for value in anchors) else float("nan")
        hard_min = min(hard_negatives) if all(math.isfinite(value) for value in hard_negatives) else float("nan")
        random_ok = float(random_rows["search_ok"].mean()) if not random_rows.empty else float("nan")
        random_cpu = float(random_rows["adapter_cached_final_cpu_delta"].mean()) if not random_rows.empty else float("nan")
        strong_ok = float(strong_rows["search_ok"].mean()) if not strong_rows.empty else float("nan")
        target_ok = float(target_rows["search_ok"].mean()) if not target_rows.empty else float("nan")
        score = 0.0
        score += 3.0 * (anchor_min if math.isfinite(anchor_min) else 0.0)
        score += 2.0 * (hard_min if math.isfinite(hard_min) else 0.0)
        score += 1.0 * (strong_ok if math.isfinite(strong_ok) else 0.0)
        score -= 2.0 * (random_ok if math.isfinite(random_ok) else 0.0)
        score -= 1.0 * (subset_perm if math.isfinite(subset_perm) else 0.0)
        if math.isfinite(random_cpu) and random_cpu < 0.0:
            score += random_cpu

        rows.append(
            {
                "checkpoint": checkpoint,
                "checkpoint_order": order,
                "warmup_conflicts": int(warmup),
                "strict_selection_score": score,
                "anchor_min_search_ok_frac": anchor_min,
                "hard_negative_min_search_ok_frac": hard_min,
                "target_base_search_ok_frac": target_ok,
                "strong_symmetry_search_ok_frac": strong_ok,
                "random_control_search_ok_frac": random_ok,
                "random_control_cpu_delta_mean": random_cpu,
                "subset_bw12_perm1730_search_ok_frac": subset_perm,
                "overall_search_ok_frac": float(group["search_ok"].mean()),
                "overall_search_blowup_frac": float(group["search_blowup"].mean()),
                "overall_adapter_cached_cpu_delta_mean": float(group["adapter_cached_final_cpu_delta"].mean()),
                "overall_adapter_cached_decisions_delta_mean": float(group["adapter_cached_decisions_delta"].mean()),
                "overall_adapter_cached_conflicts_delta_mean": float(group["adapter_cached_conflicts_delta"].mean()),
                "overall_adapter_plain_protocol_delta_mean": float(group["adapter_plain_protocol_delta"].mean()),
                "all_solved": bool(group["event_adapter_final_final_solved"].all()),
                "known_expected_rows": int(group["known_expected_result"].sum()),
                "known_expected_match_rows": int(group["event_adapter_final_known_expected_match"].sum()),
            }
        )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows)
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells: list[str] = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                cells.append(f"{value:.6g}" if math.isfinite(value) else "nan")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(
    path: Path,
    *,
    observations: pd.DataFrame,
    strict: pd.DataFrame,
    by_family: pd.DataFrame,
    by_base: pd.DataFrame,
    outputs: dict[str, Path],
    title: str,
    description: str,
) -> None:
    top_wc1 = strict[strict["warmup_conflicts"].eq(1)].sort_values("strict_selection_score", ascending=False)
    top_wc3 = strict[strict["warmup_conflicts"].eq(3)].sort_values("strict_selection_score", ascending=False)
    target_base = by_base[by_base["base_instance_id"].astype(str).isin(TARGET_BASES)].sort_values(
        ["warmup_conflicts", "base_instance_id", "checkpoint_order", "checkpoint"]
    )
    random_family = by_family[by_family["family"].astype(str).eq("random_3sat_control")].sort_values(
        ["warmup_conflicts", "checkpoint_order", "checkpoint"]
    )

    best_wc1 = top_wc1.iloc[0].to_dict() if not top_wc1.empty else {}
    best_wc3 = top_wc3.iloc[0].to_dict() if not top_wc3.empty else {}
    lines = [
        f"# {title}",
        "",
        description,
        "",
        "## Artifacts",
        "",
        *[f"- {name}: `{display_path(path)}`" for name, path in outputs.items()],
        "",
        "## Scope",
        "",
        f"- observation rows: `{len(observations)}`",
        f"- checkpoints: `{', '.join(map(str, strict['checkpoint'].drop_duplicates().tolist()))}`",
        "- warmup conflicts: `1, 3`",
        "- target bases: `k9_color8`, `php_p9_h8`, `k10_color9`, `php_p10_h9`",
        "- random controls are treated as suppression/robustness evidence, not positive symmetry evidence.",
        "",
        "## Selection Summary",
        "",
        f"- best wc1 by strict selection score: `{best_wc1.get('checkpoint', 'NA')}`",
        f"- best wc3 by strict selection score: `{best_wc3.get('checkpoint', 'NA')}`",
        "- The score is only a diagnostic ranking: anchors and hard-negative recovery increase it; random-control search wins and subset bw12 perm1730 wins decrease it.",
        "",
        "## Top WC1",
        "",
        *markdown_table(
            top_wc1[
                [
                    "checkpoint",
                    "strict_selection_score",
                    "anchor_min_search_ok_frac",
                    "hard_negative_min_search_ok_frac",
                    "strong_symmetry_search_ok_frac",
                    "random_control_search_ok_frac",
                    "random_control_cpu_delta_mean",
                    "subset_bw12_perm1730_search_ok_frac",
                    "overall_adapter_cached_decisions_delta_mean",
                    "overall_adapter_cached_conflicts_delta_mean",
                    "overall_adapter_cached_cpu_delta_mean",
                ]
            ],
            max_rows=20,
        ),
        "",
        "## Top WC3",
        "",
        *markdown_table(
            top_wc3[
                [
                    "checkpoint",
                    "strict_selection_score",
                    "anchor_min_search_ok_frac",
                    "hard_negative_min_search_ok_frac",
                    "strong_symmetry_search_ok_frac",
                    "random_control_search_ok_frac",
                    "random_control_cpu_delta_mean",
                    "subset_bw12_perm1730_search_ok_frac",
                    "overall_adapter_cached_decisions_delta_mean",
                    "overall_adapter_cached_conflicts_delta_mean",
                    "overall_adapter_cached_cpu_delta_mean",
                ]
            ],
            max_rows=20,
        ),
        "",
        "## Target Bases",
        "",
        *markdown_table(
            target_base[
                [
                    "checkpoint",
                    "warmup_conflicts",
                    "family",
                    "base_instance_id",
                    "search_ok_frac",
                    "search_blowup_frac",
                    "adapter_cached_cpu_delta_mean",
                    "adapter_cached_decisions_delta_mean",
                    "adapter_cached_conflicts_delta_mean",
                    "adapter_plain_protocol_delta_mean",
                ]
            ],
            max_rows=120,
        ),
        "",
        "## Random Controls",
        "",
        *markdown_table(
            random_family[
                [
                    "checkpoint",
                    "warmup_conflicts",
                    "search_ok_frac",
                    "search_blowup_frac",
                    "adapter_cached_cpu_delta_mean",
                    "adapter_cached_decisions_delta_mean",
                    "adapter_cached_conflicts_delta_mean",
                    "adapter_plain_protocol_delta_mean",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Interpretation",
        "",
        "- This audit ranks checkpoints by adapter-vs-cached search-work behavior, not by protocol-time speedup.",
        "- A usable checkpoint should keep `k9_color8` and `php_p9_h8` at full variant search reduction while recovering at least part of `k10_color9` and `php_p10_h9` at wc1.",
        "- If wc3 remains search-work positive on average, the v1.2 objective should be treated as wc1-specific rather than a stable low-warmup fix.",
        "- No solver speedup claim follows from this table.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize EchoSAT Symmetry GRPO checkpoint time-slice acceptance.")
    parser.add_argument("--prefix", default="echosat_symmetry_grpo_v1_2_timeslice")
    parser.add_argument("--checkpoints", nargs="+", required=True)
    parser.add_argument("--out-observations", type=Path, default=ROOT / "runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_observations.csv")
    parser.add_argument("--out-family", type=Path, default=ROOT / "runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_summary_by_family.csv")
    parser.add_argument("--out-base", type=Path, default=ROOT / "runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_summary_by_base.csv")
    parser.add_argument("--out-strict", type=Path, default=ROOT / "runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_strict_acceptance.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/echosat_symmetry_grpo_v1_2_timeslice.md")
    parser.add_argument("--title", default="EchoSAT Symmetry GRPO v1.2 Checkpoint Time-Slice")
    parser.add_argument(
        "--description",
        default=(
            "This is a checkpoint time-slice acceptance audit for the v1.2 WC1 hard-negative run. "
            "It reuses the canonical low-warmup runtime protocol and does not train a model, "
            "expand the benchmark, or add a gate/selector."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    observations = read_observations(args.prefix, args.checkpoints)
    by_family = summarize_group(observations, ["checkpoint", "checkpoint_order", "warmup_conflicts", "family"])
    by_base = summarize_group(observations, ["checkpoint", "checkpoint_order", "warmup_conflicts", "family", "base_instance_id"])
    strict = strict_acceptance(observations)

    outputs = {
        "observations": resolve(args.out_observations),
        "summary by family": resolve(args.out_family),
        "summary by base": resolve(args.out_base),
        "strict acceptance": resolve(args.out_strict),
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    observations.to_csv(outputs["observations"], index=False)
    by_family.to_csv(outputs["summary by family"], index=False)
    by_base.to_csv(outputs["summary by base"], index=False)
    strict.to_csv(outputs["strict acceptance"], index=False)
    write_doc(
        resolve(args.doc),
        observations=observations,
        strict=strict,
        by_family=by_family,
        by_base=by_base,
        outputs=outputs,
        title=str(args.title),
        description=str(args.description),
    )
    print(f"wrote {outputs['observations']}")
    print(f"wrote {outputs['summary by family']}")
    print(f"wrote {outputs['summary by base']}")
    print(f"wrote {outputs['strict acceptance']}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
