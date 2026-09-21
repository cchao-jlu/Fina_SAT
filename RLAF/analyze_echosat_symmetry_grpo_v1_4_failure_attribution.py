from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd
import torch


ROOT = Path(__file__).resolve().parent

DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter0_iter15_observations.csv"
DEFAULT_ITER0 = ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/iter=0.pt"
DEFAULT_ITER15 = ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/iter=15.pt"
DEFAULT_OUT_PREFIX = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_4_failure_attribution.md"

ANCHOR_BASES = {"k9_color8", "php_p9_h8"}
HARD_NEGATIVE_BASES = {"k10_color9", "php_p10_h9"}
SUBSET_FAILURE_BASE = "subset_cardinality_bw12"
SUBSET_FAILURE_VARIANT = "perm_seed1730"

PAIR_KEYS = ["warmup_conflicts", "base_instance_id", "variant", "repeat_id"]
META_COLUMNS = [
    "family",
    "control_type",
    "scale",
    "benchmark_role",
    "symmetry_strength",
    "num_vars",
    "num_clauses",
    "final_cpu_lim",
    "warmup_cpu_lim",
    "known_expected_result",
    "event_adapter_final_known_expected_match",
]
METRIC_COLUMNS = [
    "adapter_cached_decisions_delta",
    "adapter_cached_conflicts_delta",
    "adapter_cached_final_cpu_delta",
    "adapter_cached_protocol_delta",
    "adapter_plain_final_cpu_delta",
    "adapter_plain_protocol_delta",
    "warmup_cpu_time",
    "warmup_conflict_count",
    "warmup_decisions",
    "event_state_l2_sum",
    "event_state_nonzero_vars",
    "event_adapter_graph_gate_evidence",
    "event_adapter_graph_gate_open",
    "adapter_inference_wall_time",
    "plain_unguided_glucose_final_cpu_time",
    "plain_unguided_glucose_final_decisions",
    "plain_unguided_glucose_final_conflicts",
    "cached_trace_no_adapter_final_final_cpu_time",
    "cached_trace_no_adapter_final_final_decisions",
    "cached_trace_no_adapter_final_final_conflicts",
    "event_adapter_final_final_cpu_time",
    "event_adapter_final_final_decisions",
    "event_adapter_final_final_conflicts",
]


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def finite(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def numeric_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype("float64")
    return pd.to_numeric(series, errors="coerce").astype("float64")


def format_float(value: Any) -> str:
    value = finite(value)
    if not math.isfinite(value):
        return "nan"
    return f"{value:.6g}"


def markdown_table(frame: pd.DataFrame, max_rows: int = 30) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells: list[str] = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                cells.append(format_float(value))
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def load_observations(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = set(PAIR_KEYS + ["checkpoint", "adapter_cached_decisions_delta", "adapter_cached_conflicts_delta"])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    frame = frame.copy()
    frame["checkpoint"] = frame["checkpoint"].astype(str)
    frame["search_ok"] = (
        pd.to_numeric(frame["adapter_cached_decisions_delta"], errors="coerce") < 0.0
    ) & (
        pd.to_numeric(frame["adapter_cached_conflicts_delta"], errors="coerce") < 0.0
    )
    frame["search_blowup"] = (
        pd.to_numeric(frame["adapter_cached_decisions_delta"], errors="coerce") > 0.0
    ) | (
        pd.to_numeric(frame["adapter_cached_conflicts_delta"], errors="coerce") > 0.0
    )
    frame["cpu_only_win"] = (
        pd.to_numeric(frame.get("adapter_cached_final_cpu_delta", pd.Series(index=frame.index)), errors="coerce") < 0.0
    ) & ~frame["search_ok"]
    frame["random_control"] = (
        frame.get("family", "").astype(str).eq("random_3sat_control")
        | frame.get("control_type", "").astype(str).eq("non_symmetric_control")
    )
    frame["target_role"] = frame.apply(target_role, axis=1)
    return frame


def target_role(row: pd.Series) -> str:
    base = str(row.get("base_instance_id", ""))
    variant = str(row.get("variant", ""))
    family = str(row.get("family", ""))
    control_type = str(row.get("control_type", ""))
    if family == "random_3sat_control" or control_type == "non_symmetric_control":
        return "random_control"
    if base in ANCHOR_BASES:
        return "anchor"
    if base in HARD_NEGATIVE_BASES:
        return "hard_negative"
    if base == SUBSET_FAILURE_BASE and variant == SUBSET_FAILURE_VARIANT:
        return "subset_perm_failure"
    if base == SUBSET_FAILURE_BASE:
        return "subset_other_variant"
    return "other"


def paired_variant_deltas(observations: pd.DataFrame) -> pd.DataFrame:
    iter0 = observations[observations["checkpoint"].eq("iter=0")].copy()
    iter15 = observations[observations["checkpoint"].eq("iter=15")].copy()
    if iter0.empty or iter15.empty:
        raise ValueError("expected both iter=0 and iter=15 rows")

    keep_columns = PAIR_KEYS + [c for c in META_COLUMNS + METRIC_COLUMNS if c in observations.columns] + [
        "search_ok",
        "search_blowup",
        "cpu_only_win",
        "random_control",
        "target_role",
    ]
    iter0 = iter0[keep_columns].rename(columns={c: f"{c}_iter0" for c in keep_columns if c not in PAIR_KEYS})
    iter15 = iter15[keep_columns].rename(columns={c: f"{c}_iter15" for c in keep_columns if c not in PAIR_KEYS})
    paired = iter0.merge(iter15, on=PAIR_KEYS, how="inner", validate="one_to_one")
    if len(paired) != min(len(iter0), len(iter15)):
        raise ValueError(f"paired row count mismatch: iter0={len(iter0)} iter15={len(iter15)} paired={len(paired)}")

    for column in METRIC_COLUMNS:
        left = f"{column}_iter0"
        right = f"{column}_iter15"
        if left in paired.columns and right in paired.columns:
            paired[f"{column}_change"] = numeric_series(paired[right]) - numeric_series(paired[left])

    paired["family"] = paired["family_iter0"].astype(str)
    paired["control_type"] = paired["control_type_iter0"].astype(str)
    paired["symmetry_strength"] = paired["symmetry_strength_iter0"].astype(str)
    paired["target_role"] = paired["target_role_iter0"].astype(str)
    paired["random_control"] = bool_series(paired["random_control_iter0"]) | bool_series(paired["random_control_iter15"])
    paired["search_ok_iter0"] = bool_series(paired["search_ok_iter0"])
    paired["search_ok_iter15"] = bool_series(paired["search_ok_iter15"])
    paired["search_blowup_iter0"] = bool_series(paired["search_blowup_iter0"])
    paired["search_blowup_iter15"] = bool_series(paired["search_blowup_iter15"])
    paired["cpu_only_win_iter0"] = bool_series(paired["cpu_only_win_iter0"])
    paired["cpu_only_win_iter15"] = bool_series(paired["cpu_only_win_iter15"])
    paired["search_ok_lost"] = paired["search_ok_iter0"] & ~paired["search_ok_iter15"]
    paired["search_ok_gained"] = ~paired["search_ok_iter0"] & paired["search_ok_iter15"]
    paired["blowup_new"] = ~paired["search_blowup_iter0"] & paired["search_blowup_iter15"]
    paired["random_new_positive"] = paired["random_control"] & paired["search_ok_gained"]
    paired["anchor_lost"] = paired["target_role"].eq("anchor") & paired["search_ok_lost"]
    paired["hard_negative_recovered"] = paired["target_role"].eq("hard_negative") & paired["search_ok_gained"]
    paired["subset_failure_positive_iter15"] = paired["target_role"].eq("subset_perm_failure") & paired["search_ok_iter15"]
    return paired.sort_values(PAIR_KEYS).reset_index(drop=True)


def summarize_base(paired: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (warmup, family, base), group in paired.groupby(["warmup_conflicts", "family", "base_instance_id"], sort=True):
        row: dict[str, Any] = {
            "warmup_conflicts": int(warmup),
            "family": family,
            "base_instance_id": base,
            "target_role": ",".join(sorted(group["target_role"].dropna().astype(str).unique())),
            "rows": int(len(group)),
            "variants": int(group["variant"].nunique()),
            "repeats": int(group["repeat_id"].nunique()),
            "search_ok_frac_iter0": float(group["search_ok_iter0"].mean()),
            "search_ok_frac_iter15": float(group["search_ok_iter15"].mean()),
            "search_ok_frac_change": float(group["search_ok_iter15"].mean() - group["search_ok_iter0"].mean()),
            "search_blowup_frac_iter0": float(group["search_blowup_iter0"].mean()),
            "search_blowup_frac_iter15": float(group["search_blowup_iter15"].mean()),
            "cpu_only_win_frac_iter0": float(group["cpu_only_win_iter0"].mean()),
            "cpu_only_win_frac_iter15": float(group["cpu_only_win_iter15"].mean()),
            "search_ok_lost_rows": int(group["search_ok_lost"].sum()),
            "search_ok_gained_rows": int(group["search_ok_gained"].sum()),
            "new_blowup_rows": int(group["blowup_new"].sum()),
        }
        for metric in [
            "adapter_cached_decisions_delta",
            "adapter_cached_conflicts_delta",
            "adapter_cached_final_cpu_delta",
            "adapter_plain_protocol_delta",
            "event_state_l2_sum",
            "event_state_nonzero_vars",
            "warmup_decisions",
            "warmup_conflict_count",
        ]:
            left = f"{metric}_iter0"
            right = f"{metric}_iter15"
            change = f"{metric}_change"
            if left in group.columns and right in group.columns:
                row[f"{metric}_mean_iter0"] = float(pd.to_numeric(group[left], errors="coerce").mean())
                row[f"{metric}_mean_iter15"] = float(pd.to_numeric(group[right], errors="coerce").mean())
            if change in group.columns:
                row[f"{metric}_mean_change"] = float(pd.to_numeric(group[change], errors="coerce").mean())
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_family(paired: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (warmup, family), group in paired.groupby(["warmup_conflicts", "family"], sort=True):
        rows.append(
            {
                "warmup_conflicts": int(warmup),
                "family": family,
                "bases": int(group["base_instance_id"].nunique()),
                "rows": int(len(group)),
                "search_ok_frac_iter0": float(group["search_ok_iter0"].mean()),
                "search_ok_frac_iter15": float(group["search_ok_iter15"].mean()),
                "search_ok_frac_change": float(group["search_ok_iter15"].mean() - group["search_ok_iter0"].mean()),
                "search_blowup_frac_iter0": float(group["search_blowup_iter0"].mean()),
                "search_blowup_frac_iter15": float(group["search_blowup_iter15"].mean()),
                "search_ok_lost_rows": int(group["search_ok_lost"].sum()),
                "search_ok_gained_rows": int(group["search_ok_gained"].sum()),
                "adapter_cached_decisions_delta_mean_change": float(
                    pd.to_numeric(group.get("adapter_cached_decisions_delta_change"), errors="coerce").mean()
                ),
                "adapter_cached_conflicts_delta_mean_change": float(
                    pd.to_numeric(group.get("adapter_cached_conflicts_delta_change"), errors="coerce").mean()
                ),
                "adapter_cached_final_cpu_delta_mean_change": float(
                    pd.to_numeric(group.get("adapter_cached_final_cpu_delta_change"), errors="coerce").mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def load_state_dict(path: Path) -> dict[str, torch.Tensor]:
    loaded = torch.load(path, map_location="cpu")
    if isinstance(loaded, dict) and "state_dict" in loaded and isinstance(loaded["state_dict"], dict):
        loaded = loaded["state_dict"]
    if not isinstance(loaded, dict):
        raise TypeError(f"{path} did not load as a state dict")
    return {str(k): v.detach().cpu() for k, v in loaded.items() if torch.is_tensor(v)}


def checkpoint_param_delta(iter0: Path, iter15: Path) -> pd.DataFrame:
    a = load_state_dict(iter0)
    b = load_state_dict(iter15)
    rows: list[dict[str, Any]] = []
    for key in sorted(set(a) | set(b)):
        left = a.get(key)
        right = b.get(key)
        row: dict[str, Any] = {
            "key": key,
            "scope": "event_adapter" if key.startswith("event_adapter") else "base_model",
            "present_iter0": left is not None,
            "present_iter15": right is not None,
        }
        if left is None or right is None:
            row.update({"shape_match": False, "numel": 0})
            rows.append(row)
            continue
        row["shape_iter0"] = "x".join(map(str, left.shape))
        row["shape_iter15"] = "x".join(map(str, right.shape))
        row["shape_match"] = tuple(left.shape) == tuple(right.shape)
        row["numel"] = int(left.numel())
        if not row["shape_match"] or not left.dtype.is_floating_point or not right.dtype.is_floating_point:
            rows.append(row)
            continue
        left_f = left.to(dtype=torch.float64)
        right_f = right.to(dtype=torch.float64)
        delta = right_f - left_f
        left_norm = float(torch.linalg.vector_norm(left_f).item())
        delta_l2 = float(torch.linalg.vector_norm(delta).item())
        row.update(
            {
                "iter0_l2": left_norm,
                "iter15_l2": float(torch.linalg.vector_norm(right_f).item()),
                "delta_l2": delta_l2,
                "delta_rel_l2": delta_l2 / max(left_norm, 1.0e-12),
                "delta_mean_abs": float(delta.abs().mean().item()) if delta.numel() else 0.0,
                "delta_max_abs": float(delta.abs().max().item()) if delta.numel() else 0.0,
                "changed": bool(float(delta.abs().max().item()) > 1.0e-12) if delta.numel() else False,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["scope", "delta_l2", "key"], ascending=[True, False, True])


def important_slices(paired: pd.DataFrame) -> dict[str, pd.DataFrame]:
    metric_cols = [
        "warmup_conflicts",
        "family",
        "base_instance_id",
        "variant",
        "repeat_id",
        "target_role",
        "search_ok_iter0",
        "search_ok_iter15",
        "search_ok_lost",
        "search_ok_gained",
        "adapter_cached_decisions_delta_iter0",
        "adapter_cached_decisions_delta_iter15",
        "adapter_cached_decisions_delta_change",
        "adapter_cached_conflicts_delta_iter0",
        "adapter_cached_conflicts_delta_iter15",
        "adapter_cached_conflicts_delta_change",
        "adapter_cached_final_cpu_delta_iter0",
        "adapter_cached_final_cpu_delta_iter15",
        "adapter_cached_final_cpu_delta_change",
        "adapter_plain_protocol_delta_iter0",
        "adapter_plain_protocol_delta_iter15",
    ]
    cols = [c for c in metric_cols if c in paired.columns]
    return {
        "anchor_lost": paired[paired["anchor_lost"]][cols].sort_values(["warmup_conflicts", "base_instance_id", "variant", "repeat_id"]),
        "random_new_positive": paired[paired["random_new_positive"]][cols].sort_values(
            ["warmup_conflicts", "base_instance_id", "variant", "repeat_id"]
        ),
        "hard_negative": paired[paired["target_role"].eq("hard_negative")][cols].sort_values(
            ["warmup_conflicts", "base_instance_id", "variant", "repeat_id"]
        ),
        "subset_failure": paired[paired["target_role"].eq("subset_perm_failure")][cols].sort_values(
            ["warmup_conflicts", "base_instance_id", "variant", "repeat_id"]
        ),
    }


def write_doc(
    *,
    path: Path,
    observations_path: Path,
    iter0_checkpoint: Path,
    iter15_checkpoint: Path,
    paired: pd.DataFrame,
    base_summary: pd.DataFrame,
    family_summary: pd.DataFrame,
    param_delta: pd.DataFrame,
    slices: dict[str, pd.DataFrame],
    outputs: dict[str, Path],
) -> None:
    warmups = ", ".join(map(str, sorted(paired["warmup_conflicts"].dropna().astype(int).unique().tolist())))
    param_changed = param_delta[param_delta.get("changed", False).fillna(False)]
    changed_by_scope = (
        param_changed.groupby("scope", sort=True)
        .agg(changed_keys=("key", "size"), delta_l2_sum=("delta_l2", "sum"), delta_mean_abs_mean=("delta_mean_abs", "mean"))
        .reset_index()
        if not param_changed.empty
        else pd.DataFrame(columns=["scope", "changed_keys", "delta_l2_sum", "delta_mean_abs_mean"])
    )
    wc1 = base_summary[base_summary["warmup_conflicts"].eq(1)].copy()
    target_wc1 = wc1[wc1["target_role"].astype(str).str.contains("anchor|hard_negative|subset|random_control", regex=True)].sort_values(
        ["target_role", "family", "base_instance_id"]
    )
    family_view = family_summary.sort_values(["warmup_conflicts", "family"])
    top_param = param_changed.sort_values("delta_l2", ascending=False)[
        ["key", "scope", "numel", "delta_l2", "delta_rel_l2", "delta_mean_abs", "delta_max_abs"]
    ]

    total_lost = int(paired["search_ok_lost"].sum())
    total_gained = int(paired["search_ok_gained"].sum())
    anchor_lost = int(paired["anchor_lost"].sum())
    random_new = int(paired["random_new_positive"].sum())
    hard_recovered = int(paired["hard_negative_recovered"].sum())
    subset_positive = int(paired["subset_failure_positive_iter15"].sum())
    known_summaries: list[str] = []
    known_ok_values: list[bool] = []
    for suffix in ["iter0", "iter15"]:
        known_col = f"known_expected_result_{suffix}"
        match_col = f"event_adapter_final_known_expected_match_{suffix}"
        if known_col not in paired.columns or match_col not in paired.columns:
            continue
        known_mask = bool_series(paired[known_col])
        match_mask = bool_series(paired[match_col])
        known_rows = int(known_mask.sum())
        matched_rows = int((known_mask & match_mask).sum())
        known_ok_values.append(matched_rows == known_rows)
        known_summaries.append(f"{suffix}: {matched_rows}/{known_rows}")
    known_ok = all(known_ok_values) if known_ok_values else True
    known_summary = "; ".join(known_summaries) if known_summaries else "not reported"

    lines = [
        "# EchoSAT Symmetry GRPO v1.4 Failure Attribution",
        "",
        "This is an offline attribution pass over the existing v1.4 iter=0/iter=15 targeted acceptance outputs. It does not train, rerun final solver benchmarks, expand the benchmark, or add a gate/selector.",
        "",
        "## Inputs",
        "",
        f"- observations: `{display_path(observations_path)}`",
        f"- iter=0 checkpoint: `{display_path(iter0_checkpoint)}`",
        f"- iter=15 checkpoint: `{display_path(iter15_checkpoint)}`",
        "",
        "## Outputs",
        "",
        *[f"- {name}: `{display_path(value)}`" for name, value in outputs.items()],
        "",
        "## Scope",
        "",
        f"- paired variant-repeat rows: `{len(paired)}`",
        f"- warmup conflicts: `{warmups}`",
        f"- bases: `{paired['base_instance_id'].nunique()}`",
        f"- variants: `{paired[['base_instance_id', 'variant']].drop_duplicates().shape[0]}`",
        "",
        "## Headline",
        "",
        f"- search_ok losses from iter=0 to iter=15: `{total_lost}` rows",
        f"- search_ok gains from iter=0 to iter=15: `{total_gained}` rows",
        f"- anchor lost rows: `{anchor_lost}`",
        f"- random-control newly positive rows: `{random_new}`",
        f"- hard-negative recovered rows: `{hard_recovered}`",
        f"- subset perm failure positive rows at iter=15: `{subset_positive}`",
        f"- known expected correctness still matched where reported: `{known_ok}` ({known_summary})",
        "",
        "Interpretation: v1.4 did not merely fail best-checkpoint selection. By iter=15 it loses anchor search reductions and introduces positive random-control rows, while hard-negative recovery remains weak. That is objective drift, not a speedup result.",
        "",
        "## WC1 Target Base Summary",
        "",
        *markdown_table(
            target_wc1[
                [
                    "target_role",
                    "family",
                    "base_instance_id",
                    "rows",
                    "search_ok_frac_iter0",
                    "search_ok_frac_iter15",
                    "search_ok_frac_change",
                    "search_ok_lost_rows",
                    "search_ok_gained_rows",
                    "adapter_cached_decisions_delta_mean_iter0",
                    "adapter_cached_decisions_delta_mean_iter15",
                    "adapter_cached_conflicts_delta_mean_iter0",
                    "adapter_cached_conflicts_delta_mean_iter15",
                    "adapter_cached_final_cpu_delta_mean_iter0",
                    "adapter_cached_final_cpu_delta_mean_iter15",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Family-Level Drift",
        "",
        *markdown_table(
            family_view[
                [
                    "warmup_conflicts",
                    "family",
                    "bases",
                    "rows",
                    "search_ok_frac_iter0",
                    "search_ok_frac_iter15",
                    "search_ok_frac_change",
                    "search_ok_lost_rows",
                    "search_ok_gained_rows",
                    "adapter_cached_decisions_delta_mean_change",
                    "adapter_cached_conflicts_delta_mean_change",
                    "adapter_cached_final_cpu_delta_mean_change",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Anchor Lost Rows",
        "",
        *markdown_table(slices["anchor_lost"], max_rows=40),
        "",
        "## Random Newly Positive Rows",
        "",
        *markdown_table(slices["random_new_positive"], max_rows=40),
        "",
        "## Hard Negative Rows",
        "",
        *markdown_table(slices["hard_negative"], max_rows=40),
        "",
        "## Subset Failure Rows",
        "",
        *markdown_table(slices["subset_failure"], max_rows=20),
        "",
        "## Checkpoint Parameter Drift",
        "",
        *markdown_table(changed_by_scope, max_rows=10),
        "",
        "Top changed tensors:",
        "",
        *markdown_table(top_param, max_rows=20),
        "",
        "## Conclusion",
        "",
        "- `iter=0` remains the better v1.4 checkpoint under the strict search-work acceptance lens.",
        "- `iter=15` reduces some aggregate blowup magnitudes, but this comes with lost anchor consistency and random-control positive search reductions.",
        "- The current objective still allows generic perturbation and does not reliably preserve symmetry-specific anchor behavior.",
        "- Next work should audit the online reward/advantage on actual v1.4 batches or redesign the objective around paired ranking and anchor preservation before any further formal training.",
        "- No solver speedup claim follows from this attribution.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline failure attribution for EchoSAT Symmetry GRPO v1.4 iter=0 vs iter=15.")
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--iter0-checkpoint", type=Path, default=DEFAULT_ITER0)
    parser.add_argument("--iter15-checkpoint", type=Path, default=DEFAULT_ITER15)
    parser.add_argument("--out-prefix", type=Path, default=DEFAULT_OUT_PREFIX)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    observations_path = resolve(args.observations)
    iter0_checkpoint = resolve(args.iter0_checkpoint)
    iter15_checkpoint = resolve(args.iter15_checkpoint)
    out_prefix = resolve(args.out_prefix)
    doc_path = resolve(args.doc)

    observations = load_observations(observations_path)
    paired = paired_variant_deltas(observations)
    base_summary = summarize_base(paired)
    family = summarize_family(paired)
    param_delta = checkpoint_param_delta(iter0_checkpoint, iter15_checkpoint)
    slices = important_slices(paired)

    outputs = {
        "variant deltas": out_prefix.with_name(out_prefix.name + "_variant_deltas.csv"),
        "base summary": out_prefix.with_name(out_prefix.name + "_base_summary.csv"),
        "family summary": out_prefix.with_name(out_prefix.name + "_family_summary.csv"),
        "random newly positive": out_prefix.with_name(out_prefix.name + "_random_positive.csv"),
        "anchor lost": out_prefix.with_name(out_prefix.name + "_anchor_lost.csv"),
        "hard negative": out_prefix.with_name(out_prefix.name + "_hard_negative.csv"),
        "subset failure": out_prefix.with_name(out_prefix.name + "_subset_failure.csv"),
        "checkpoint parameter delta": out_prefix.with_name(out_prefix.name + "_checkpoint_param_delta.csv"),
    }
    for output in outputs.values():
        output.parent.mkdir(parents=True, exist_ok=True)

    paired.to_csv(outputs["variant deltas"], index=False)
    base_summary.to_csv(outputs["base summary"], index=False)
    family.to_csv(outputs["family summary"], index=False)
    slices["random_new_positive"].to_csv(outputs["random newly positive"], index=False)
    slices["anchor_lost"].to_csv(outputs["anchor lost"], index=False)
    slices["hard_negative"].to_csv(outputs["hard negative"], index=False)
    slices["subset_failure"].to_csv(outputs["subset failure"], index=False)
    param_delta.to_csv(outputs["checkpoint parameter delta"], index=False)

    write_doc(
        path=doc_path,
        observations_path=observations_path,
        iter0_checkpoint=iter0_checkpoint,
        iter15_checkpoint=iter15_checkpoint,
        paired=paired,
        base_summary=base_summary,
        family_summary=family,
        param_delta=param_delta,
        slices=slices,
        outputs=outputs,
    )
    print(f"wrote {outputs['variant deltas']}")
    print(f"wrote {outputs['base summary']}")
    print(f"wrote {outputs['family summary']}")
    print(f"wrote {outputs['random newly positive']}")
    print(f"wrote {outputs['anchor lost']}")
    print(f"wrote {outputs['hard negative']}")
    print(f"wrote {outputs['subset failure']}")
    print(f"wrote {outputs['checkpoint parameter delta']}")
    print(f"wrote {doc_path}")


if __name__ == "__main__":
    main()
