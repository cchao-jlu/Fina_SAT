from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent

DEFAULT_REFERENCE_OBSERVATIONS = (
    ROOT
    / "runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_v1_2_iter15_canonical_low_warmup_observations.csv"
)
DEFAULT_CANDIDATE_OBSERVATIONS: dict[str, Path] = {
    "iter=50": ROOT / "runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_iter=50_canonical_low_warmup_observations.csv",
    "iter=80": ROOT / "runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_iter=80_canonical_low_warmup_observations.csv",
    "iter=115": ROOT / "runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_iter=115_canonical_low_warmup_observations.csv",
}
DEFAULT_REWARD_REPLAY = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_7_reward_replay_dryrun_rows.csv"
DEFAULT_OUT_PREFIX = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_7_failure_attribution.md"

REFERENCE_LABEL = "v1_2_iter15"
ANCHOR_BASES = {"k9_color8", "php_p9_h8"}
HARD_NEGATIVE_BASES = {"k10_color9", "php_p10_h9"}
SUBSET_FAILURE_BASE = "subset_cardinality_bw12"
SUBSET_FAILURE_VARIANT = "perm_seed1730"
PAIR_KEYS = ["warmup_conflicts", "base_instance_id", "variant", "repeat_id"]
META_COLUMNS = [
    "source_csv",
    "instance_id",
    "family",
    "control_type",
    "scale",
    "benchmark_role",
    "symmetry_strength",
    "num_vars",
    "num_clauses",
    "final_cpu_lim",
    "warmup_cpu_lim",
    "checkpoint",
    "known_expected_result",
    "event_adapter_final_known_expected_match",
    "event_adapter_final_final_solved",
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


def resolve(path: str | Path) -> Path:
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


def format_float(value: Any) -> str:
    value = finite(value)
    if not math.isfinite(value):
        return "nan"
    return f"{value:.6g}"


def numeric_series(series: pd.Series | Any, index: pd.Index | None = None) -> pd.Series:
    if not isinstance(series, pd.Series):
        series = pd.Series(series, index=index)
    if series.dtype == bool:
        return series.astype("float64")
    return pd.to_numeric(series, errors="coerce").astype("float64")


def bool_series(series: pd.Series | Any, index: pd.Index | None = None) -> pd.Series:
    if not isinstance(series, pd.Series):
        series = pd.Series(series, index=index)
    if series.dtype == bool:
        return series.fillna(False)
    numeric = pd.to_numeric(series, errors="coerce")
    text = series.fillna("").astype(str).str.strip().str.lower()
    textual_true = text.isin({"true", "t", "yes", "y"})
    numeric_true = numeric.notna() & numeric.ne(0.0)
    return textual_true | numeric_true


def fraction(mask: pd.Series) -> float:
    if mask.empty:
        return float("nan")
    return float(bool_series(mask).mean())


def mean_numeric(values: pd.Series) -> float:
    if values.empty:
        return float("nan")
    out = pd.to_numeric(values, errors="coerce").mean()
    return float(out) if pd.notna(out) and math.isfinite(float(out)) else float("nan")


def role_fraction(frame: pd.DataFrame, role: str, column: str) -> float:
    rows = frame[frame["target_role"].astype(str).eq(role)]
    return fraction(rows[column]) if not rows.empty and column in rows.columns else float("nan")


def role_min_base_fraction(frame: pd.DataFrame, role: str, column: str) -> float:
    rows = frame[frame["target_role"].astype(str).eq(role)]
    if rows.empty or column not in rows.columns:
        return float("nan")
    values = [fraction(group[column]) for _, group in rows.groupby("base_instance_id", sort=True)]
    values = [value for value in values if math.isfinite(value)]
    return min(values) if values else float("nan")


def target_role(row: pd.Series) -> str:
    family = str(row.get("family", ""))
    control_type = str(row.get("control_type", ""))
    base = str(row.get("base_instance_id", ""))
    variant = str(row.get("variant", ""))
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


def load_observation_frame(
    source: Path | str | pd.DataFrame,
    *,
    candidate_label: str,
    source_path: Path | None = None,
) -> pd.DataFrame:
    if isinstance(source, pd.DataFrame):
        frame = source.copy()
    else:
        source_path = resolve(source)
        frame = pd.read_csv(source_path)

    required = set(PAIR_KEYS + ["family", "control_type", "adapter_cached_decisions_delta", "adapter_cached_conflicts_delta"])
    missing = sorted(required - set(frame.columns))
    if missing:
        label = str(source_path) if source_path is not None else "<dataframe>"
        raise ValueError(f"{label} is missing required columns: {missing}")

    frame = frame.copy()
    frame["candidate_label"] = str(candidate_label)
    if source_path is not None:
        frame["audit_source_path"] = str(source_path)
    for column in PAIR_KEYS:
        if column in {"warmup_conflicts", "repeat_id"}:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
        else:
            frame[column] = frame[column].astype(str)
    for column in METRIC_COLUMNS:
        if column not in frame.columns:
            frame[column] = float("nan")
        frame[column] = numeric_series(frame[column])

    frame["search_ok"] = (frame["adapter_cached_decisions_delta"] < 0.0) & (
        frame["adapter_cached_conflicts_delta"] < 0.0
    )
    frame["search_blowup"] = (frame["adapter_cached_decisions_delta"] > 0.0) | (
        frame["adapter_cached_conflicts_delta"] > 0.0
    )
    frame["cpu_only_win"] = (frame["adapter_cached_final_cpu_delta"] < 0.0) & ~frame["search_ok"]
    frame["protocol_only_win"] = (frame["adapter_plain_protocol_delta"] < 0.0) & ~frame["search_ok"]
    frame["random_control"] = frame["family"].astype(str).eq("random_3sat_control") | frame["control_type"].astype(str).eq(
        "non_symmetric_control"
    )
    frame["target_role"] = frame.apply(target_role, axis=1)
    return frame.sort_values(PAIR_KEYS).reset_index(drop=True)


def _comparison_keep_columns(frame: pd.DataFrame) -> list[str]:
    keep = PAIR_KEYS + ["candidate_label"]
    keep += [column for column in META_COLUMNS if column in frame.columns]
    keep += [column for column in METRIC_COLUMNS if column in frame.columns]
    keep += ["search_ok", "search_blowup", "cpu_only_win", "protocol_only_win", "random_control", "target_role"]
    return list(dict.fromkeys(keep))


def compare_against_reference(reference: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    missing_reference = sorted(set(PAIR_KEYS) - set(reference.columns))
    missing_candidate = sorted(set(PAIR_KEYS) - set(candidate.columns))
    if missing_reference or missing_candidate:
        raise ValueError(f"missing pair keys: reference={missing_reference} candidate={missing_candidate}")

    ref = reference[_comparison_keep_columns(reference)].copy()
    cand = candidate[_comparison_keep_columns(candidate)].copy()
    ref = ref.rename(columns={column: f"{column}_reference" for column in ref.columns if column not in PAIR_KEYS})
    cand = cand.rename(columns={column: f"{column}_candidate" for column in cand.columns if column not in PAIR_KEYS})
    paired = ref.merge(cand, on=PAIR_KEYS, how="inner", validate="one_to_one")
    if len(paired) != min(len(ref), len(cand)):
        raise ValueError(f"paired row count mismatch: reference={len(ref)} candidate={len(cand)} paired={len(paired)}")

    paired["candidate_label"] = paired["candidate_label_candidate"].astype(str)
    paired["reference_label"] = paired["candidate_label_reference"].astype(str)
    for column in ["family", "control_type", "scale", "benchmark_role", "symmetry_strength", "instance_id"]:
        candidate_col = f"{column}_candidate"
        reference_col = f"{column}_reference"
        if candidate_col in paired.columns:
            paired[column] = paired[candidate_col]
        elif reference_col in paired.columns:
            paired[column] = paired[reference_col]

    paired["target_role"] = paired.get("target_role_candidate", paired.get("target_role_reference", "other")).astype(str)
    paired["random_control"] = bool_series(
        paired.get("random_control_candidate", False), index=paired.index
    ) | bool_series(paired.get("random_control_reference", False), index=paired.index)

    for flag in ["search_ok", "search_blowup", "cpu_only_win", "protocol_only_win"]:
        paired[f"reference_{flag}"] = bool_series(paired.get(f"{flag}_reference", False), index=paired.index)
        paired[f"candidate_{flag}"] = bool_series(paired.get(f"{flag}_candidate", False), index=paired.index)

    for column in METRIC_COLUMNS:
        left = f"{column}_reference"
        right = f"{column}_candidate"
        if left in paired.columns:
            paired[left] = numeric_series(paired[left])
        if right in paired.columns:
            paired[right] = numeric_series(paired[right])
        if left in paired.columns and right in paired.columns:
            paired[f"{column}_change_vs_reference"] = paired[right] - paired[left]

    paired = paired.copy()
    paired["search_ok_lost_vs_reference"] = paired["reference_search_ok"] & ~paired["candidate_search_ok"]
    paired["search_ok_gained_vs_reference"] = ~paired["reference_search_ok"] & paired["candidate_search_ok"]
    paired["new_blowup_vs_reference"] = ~paired["reference_search_blowup"] & paired["candidate_search_blowup"]
    paired["hard_negative_lost_vs_reference"] = paired["target_role"].eq("hard_negative") & paired["search_ok_lost_vs_reference"]
    paired["hard_negative_gained_vs_reference"] = paired["target_role"].eq("hard_negative") & paired["search_ok_gained_vs_reference"]
    paired["anchor_lost_vs_reference"] = paired["target_role"].eq("anchor") & paired["search_ok_lost_vs_reference"]
    paired["random_positive_candidate"] = paired["target_role"].eq("random_control") & paired["candidate_search_ok"]
    paired["subset_failure_positive_candidate"] = paired["target_role"].eq("subset_perm_failure") & paired["candidate_search_ok"]
    paired["protocol_win_search_bad_candidate"] = paired["candidate_protocol_only_win"]
    return paired.sort_values(["candidate_label", *PAIR_KEYS]).reset_index(drop=True)


def summarize_candidate(paired: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_cols = ["candidate_label", "warmup_conflicts"]
    for (candidate_label, warmup), group in paired.groupby(group_cols, sort=True, dropna=False):
        known = bool_series(group.get("known_expected_result_candidate", False), index=group.index)
        matched = bool_series(group.get("event_adapter_final_known_expected_match_candidate", False), index=group.index)
        row: dict[str, Any] = {
            "candidate_label": candidate_label,
            "warmup_conflicts": int(warmup),
            "rows": int(len(group)),
            "base_instances": int(group["base_instance_id"].nunique()),
            "variants": int(group[["base_instance_id", "variant"]].drop_duplicates().shape[0]),
            "repeats": int(group["repeat_id"].nunique()),
            "reference_search_ok_frac": fraction(group["reference_search_ok"]),
            "candidate_search_ok_frac": fraction(group["candidate_search_ok"]),
            "candidate_search_blowup_frac": fraction(group["candidate_search_blowup"]),
            "cpu_only_win_frac": fraction(group["candidate_cpu_only_win"]),
            "protocol_win_search_bad_frac": fraction(
                bool_series(group.get("protocol_win_search_bad_candidate", False), index=group.index)
            ),
            "anchor_search_ok_frac": role_fraction(group, "anchor", "candidate_search_ok"),
            "anchor_min_search_ok_frac": role_min_base_fraction(group, "anchor", "candidate_search_ok"),
            "hard_negative_search_ok_frac": role_fraction(group, "hard_negative", "candidate_search_ok"),
            "hard_negative_min_search_ok_frac": role_min_base_fraction(group, "hard_negative", "candidate_search_ok"),
            "random_control_search_ok_frac": role_fraction(group, "random_control", "candidate_search_ok"),
            "subset_perm_failure_search_ok_frac": role_fraction(group, "subset_perm_failure", "candidate_search_ok"),
            "search_ok_lost_vs_reference_rows": int(bool_series(group.get("search_ok_lost_vs_reference", False), group.index).sum()),
            "search_ok_gained_vs_reference_rows": int(
                bool_series(group.get("search_ok_gained_vs_reference", False), group.index).sum()
            ),
            "anchor_lost_vs_reference_rows": int(bool_series(group.get("anchor_lost_vs_reference", False), group.index).sum()),
            "hard_negative_lost_vs_reference_rows": int(
                bool_series(group.get("hard_negative_lost_vs_reference", False), group.index).sum()
            ),
            "hard_negative_gained_vs_reference_rows": int(
                bool_series(group.get("hard_negative_gained_vs_reference", False), group.index).sum()
            ),
            "random_positive_candidate_rows": int(bool_series(group.get("random_positive_candidate", False), group.index).sum()),
            "subset_failure_positive_candidate_rows": int(
                bool_series(group.get("subset_failure_positive_candidate", False), group.index).sum()
            ),
            "known_expected_rows": int(known.sum()),
            "known_expected_match_rows": int((known & matched).sum()),
            "known_expected_all_match": bool(matched[known].all()) if bool(known.any()) else True,
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
            for suffix, label in [("reference", "reference"), ("candidate", "candidate")]:
                column = f"{metric}_{suffix}"
                if column in group.columns:
                    row[f"{metric}_{label}_mean"] = mean_numeric(group[column])
            change = f"{metric}_change_vs_reference"
            if change in group.columns:
                row[f"{metric}_change_vs_reference_mean"] = mean_numeric(group[change])
        rows.append(row)
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True)


def summarize_base(paired: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_cols = ["candidate_label", "warmup_conflicts", "family", "base_instance_id"]
    for key, group in paired.groupby(group_cols, sort=True, dropna=False):
        candidate_label, warmup, family, base = key
        row: dict[str, Any] = {
            "candidate_label": candidate_label,
            "warmup_conflicts": int(warmup),
            "family": family,
            "base_instance_id": base,
            "target_roles": ",".join(sorted(group["target_role"].dropna().astype(str).unique())),
            "rows": int(len(group)),
            "variants": int(group["variant"].nunique()),
            "repeats": int(group["repeat_id"].nunique()),
            "reference_search_ok_frac": fraction(group["reference_search_ok"]),
            "candidate_search_ok_frac": fraction(group["candidate_search_ok"]),
            "candidate_search_blowup_frac": fraction(group["candidate_search_blowup"]),
            "candidate_cpu_only_win_frac": fraction(group["candidate_cpu_only_win"]),
            "candidate_protocol_win_search_bad_frac": fraction(group["protocol_win_search_bad_candidate"]),
            "search_ok_frac_change_vs_reference": fraction(group["candidate_search_ok"]) - fraction(group["reference_search_ok"]),
            "search_ok_lost_vs_reference_rows": int(bool_series(group["search_ok_lost_vs_reference"]).sum()),
            "search_ok_gained_vs_reference_rows": int(bool_series(group["search_ok_gained_vs_reference"]).sum()),
            "new_blowup_vs_reference_rows": int(bool_series(group["new_blowup_vs_reference"]).sum()),
        }
        for metric in [
            "adapter_cached_decisions_delta",
            "adapter_cached_conflicts_delta",
            "adapter_cached_final_cpu_delta",
            "adapter_plain_protocol_delta",
            "event_state_l2_sum",
            "event_state_nonzero_vars",
        ]:
            for suffix in ["reference", "candidate"]:
                column = f"{metric}_{suffix}"
                if column in group.columns:
                    row[f"{metric}_{suffix}_mean"] = mean_numeric(group[column])
            change = f"{metric}_change_vs_reference"
            if change in group.columns:
                row[f"{metric}_change_vs_reference_mean"] = mean_numeric(group[change])
        rows.append(row)
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True)


def summarize_family(paired: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_cols = ["candidate_label", "warmup_conflicts", "family"]
    for key, group in paired.groupby(group_cols, sort=True, dropna=False):
        candidate_label, warmup, family = key
        rows.append(
            {
                "candidate_label": candidate_label,
                "warmup_conflicts": int(warmup),
                "family": family,
                "base_instances": int(group["base_instance_id"].nunique()),
                "rows": int(len(group)),
                "reference_search_ok_frac": fraction(group["reference_search_ok"]),
                "candidate_search_ok_frac": fraction(group["candidate_search_ok"]),
                "candidate_search_blowup_frac": fraction(group["candidate_search_blowup"]),
                "candidate_cpu_only_win_frac": fraction(group["candidate_cpu_only_win"]),
                "candidate_protocol_win_search_bad_frac": fraction(group["protocol_win_search_bad_candidate"]),
                "search_ok_lost_vs_reference_rows": int(bool_series(group["search_ok_lost_vs_reference"]).sum()),
                "search_ok_gained_vs_reference_rows": int(bool_series(group["search_ok_gained_vs_reference"]).sum()),
                "adapter_cached_decisions_delta_candidate_mean": mean_numeric(
                    group["adapter_cached_decisions_delta_candidate"]
                ),
                "adapter_cached_conflicts_delta_candidate_mean": mean_numeric(
                    group["adapter_cached_conflicts_delta_candidate"]
                ),
                "adapter_cached_final_cpu_delta_candidate_mean": mean_numeric(
                    group["adapter_cached_final_cpu_delta_candidate"]
                ),
                "adapter_plain_protocol_delta_candidate_mean": mean_numeric(
                    group["adapter_plain_protocol_delta_candidate"]
                ),
                "adapter_cached_decisions_delta_change_vs_reference_mean": mean_numeric(
                    group["adapter_cached_decisions_delta_change_vs_reference"]
                ),
                "adapter_cached_conflicts_delta_change_vs_reference_mean": mean_numeric(
                    group["adapter_cached_conflicts_delta_change_vs_reference"]
                ),
                "adapter_cached_final_cpu_delta_change_vs_reference_mean": mean_numeric(
                    group["adapter_cached_final_cpu_delta_change_vs_reference"]
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True)


def warmup_disagreement(frame: pd.DataFrame) -> pd.DataFrame:
    required = set(["candidate_label", "warmup_conflicts", "base_instance_id", "variant", "repeat_id", "candidate_search_ok"])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"warmup_disagreement missing columns: {missing}")
    left_cols = [
        "candidate_label",
        "base_instance_id",
        "variant",
        "repeat_id",
        "candidate_search_ok",
        "target_role",
        "family",
        "adapter_cached_decisions_delta_candidate",
        "adapter_cached_conflicts_delta_candidate",
        "adapter_cached_final_cpu_delta_candidate",
    ]
    left_cols = [column for column in left_cols if column in frame.columns]
    wc1 = frame[frame["warmup_conflicts"].eq(1)][left_cols].copy()
    wc3 = frame[frame["warmup_conflicts"].eq(3)][left_cols].copy()
    wc1 = wc1.rename(columns={column: f"wc1_{column}" for column in wc1.columns if column not in PAIR_KEYS[1:] + ["candidate_label"]})
    wc3 = wc3.rename(columns={column: f"wc3_{column}" for column in wc3.columns if column not in PAIR_KEYS[1:] + ["candidate_label"]})
    joined = wc1.merge(wc3, on=["candidate_label", "base_instance_id", "variant", "repeat_id"], how="inner", validate="one_to_one")
    if joined.empty:
        return joined
    joined["wc1_search_ok"] = bool_series(joined["wc1_candidate_search_ok"])
    joined["wc3_search_ok"] = bool_series(joined["wc3_candidate_search_ok"])
    joined = joined[joined["wc1_search_ok"] != joined["wc3_search_ok"]].copy()
    if "wc1_target_role" in joined.columns:
        joined["target_role"] = joined["wc1_target_role"]
    if "wc1_family" in joined.columns:
        joined["family"] = joined["wc1_family"]
    front = ["candidate_label", "family", "target_role", "base_instance_id", "variant", "repeat_id", "wc1_search_ok", "wc3_search_ok"]
    columns = [column for column in front if column in joined.columns] + [column for column in joined.columns if column not in front]
    return joined[columns].sort_values(["candidate_label", "base_instance_id", "variant", "repeat_id"]).reset_index(drop=True)


def important_slices(paired: pd.DataFrame) -> dict[str, pd.DataFrame]:
    columns = [
        "candidate_label",
        "warmup_conflicts",
        "family",
        "base_instance_id",
        "variant",
        "repeat_id",
        "target_role",
        "reference_search_ok",
        "candidate_search_ok",
        "search_ok_lost_vs_reference",
        "search_ok_gained_vs_reference",
        "candidate_search_blowup",
        "candidate_cpu_only_win",
        "protocol_win_search_bad_candidate",
        "adapter_cached_decisions_delta_reference",
        "adapter_cached_decisions_delta_candidate",
        "adapter_cached_decisions_delta_change_vs_reference",
        "adapter_cached_conflicts_delta_reference",
        "adapter_cached_conflicts_delta_candidate",
        "adapter_cached_conflicts_delta_change_vs_reference",
        "adapter_cached_final_cpu_delta_reference",
        "adapter_cached_final_cpu_delta_candidate",
        "adapter_cached_final_cpu_delta_change_vs_reference",
        "adapter_plain_protocol_delta_candidate",
    ]
    columns = [column for column in columns if column in paired.columns]
    sort_cols = ["candidate_label", "warmup_conflicts", "base_instance_id", "variant", "repeat_id"]
    return {
        "anchor_rows": paired[paired["target_role"].eq("anchor")][columns].sort_values(sort_cols),
        "hard_negative_rows": paired[paired["target_role"].eq("hard_negative")][columns].sort_values(sort_cols),
        "random_control_rows": paired[paired["target_role"].eq("random_control")][columns].sort_values(sort_cols),
        "subset_failure_rows": paired[paired["target_role"].isin(["subset_perm_failure", "subset_other_variant"])][columns].sort_values(
            sort_cols
        ),
    }


def load_reward_replay(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path).copy()
    for column in [
        "echosat_search_ok",
        "echosat_search_blowup",
        "echosat_positive_allowed",
        "echosat_positive_allowed_search",
        "echosat_positive_blocked_control",
        "echosat_positive_blocked_subset_failure",
        "echosat_positive_blocked_weighted_risk",
        "echosat_positive_blocked_near_cap",
        "echosat_positive_blocked_pair_inconsistency",
        "echosat_positive_blocked_anchor_failure",
        "echosat_positive_blocked_hard_negative_failure",
    ]:
        if column in frame.columns:
            frame[column] = bool_series(frame[column])
    for column in [
        "echosat_symmetry_reward",
        "grpo_raw_advantage_unclamped",
        "grpo_raw_advantage",
        "grpo_weighted_advantage_before_clamp",
        "grpo_final_advantage",
        "advantage",
    ]:
        if column in frame.columns:
            frame[column] = numeric_series(frame[column])
    if "grpo_final_advantage" in frame.columns:
        frame["positive_final_advantage"] = frame["grpo_final_advantage"] > 0.0
    else:
        frame["positive_final_advantage"] = False
    if "grpo_raw_advantage_unclamped" in frame.columns:
        frame["positive_raw_advantage_unclamped"] = frame["grpo_raw_advantage_unclamped"] > 0.0
    else:
        frame["positive_raw_advantage_unclamped"] = False
    if "echosat_search_ok" in frame.columns:
        frame["offline_positive_but_search_bad"] = frame["positive_final_advantage"] & ~frame["echosat_search_ok"]
    else:
        frame["offline_positive_but_search_bad"] = False
    return frame


def summarize_reward_replay(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    role_col = "echosat_replay_role" if "echosat_replay_role" in frame.columns else "base_instance_id"
    rows: list[dict[str, Any]] = []
    for role, group in frame.groupby(role_col, sort=True, dropna=False):
        row: dict[str, Any] = {
            role_col: role,
            "rows": int(len(group)),
            "search_ok_frac": fraction(group["echosat_search_ok"]) if "echosat_search_ok" in group.columns else float("nan"),
            "search_blowup_frac": fraction(group["echosat_search_blowup"])
            if "echosat_search_blowup" in group.columns
            else float("nan"),
            "positive_allowed_frac": fraction(group["echosat_positive_allowed"])
            if "echosat_positive_allowed" in group.columns
            else float("nan"),
            "positive_final_advantage_frac": fraction(group["positive_final_advantage"]),
            "positive_raw_advantage_unclamped_frac": fraction(group["positive_raw_advantage_unclamped"]),
            "offline_positive_but_search_bad_frac": fraction(group["offline_positive_but_search_bad"]),
        }
        for column in [
            "echosat_symmetry_reward",
            "grpo_raw_advantage_unclamped",
            "grpo_raw_advantage",
            "grpo_weighted_advantage_before_clamp",
            "grpo_final_advantage",
            "advantage",
        ]:
            if column in group.columns:
                row[f"{column}_mean"] = mean_numeric(group[column])
        rows.append(row)
    return pd.DataFrame(rows).sort_values(role_col).reset_index(drop=True)


def reward_mismatch_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    columns = [
        "iteration",
        "base_instance_id",
        "variant",
        "family",
        "echosat_replay_role",
        "echosat_search_ok",
        "echosat_search_blowup",
        "echosat_positive_allowed",
        "echosat_symmetry_reward",
        "grpo_raw_advantage_unclamped",
        "grpo_final_advantage",
        "positive_raw_advantage_unclamped",
        "positive_final_advantage",
        "offline_positive_but_search_bad",
        "echosat_positive_blocked_control",
        "echosat_positive_blocked_subset_failure",
        "echosat_positive_blocked_anchor_failure",
        "echosat_positive_blocked_hard_negative_failure",
    ]
    columns = [column for column in columns if column in frame.columns]
    mask = frame["offline_positive_but_search_bad"] | (frame["positive_raw_advantage_unclamped"] & ~frame.get("echosat_search_ok", False))
    return frame[mask][columns].sort_values(columns[: min(len(columns), 5)]).reset_index(drop=True)


def objective_repair_recommendations(
    *,
    candidate_summary: pd.DataFrame,
    base_summary: pd.DataFrame,
    reward_summary: pd.DataFrame,
    mismatch_rows: pd.DataFrame,
) -> pd.DataFrame:
    def best_value(label: str, warmup: int, column: str) -> float:
        rows = candidate_summary[
            candidate_summary["candidate_label"].astype(str).eq(label) & candidate_summary["warmup_conflicts"].eq(int(warmup))
        ]
        if rows.empty or column not in rows.columns:
            return float("nan")
        return finite(rows.iloc[0][column])

    reference_hard_wc1 = best_value(REFERENCE_LABEL, 1, "hard_negative_min_search_ok_frac")
    v17_hard_wc1 = mean_numeric(
        candidate_summary[
            candidate_summary["candidate_label"].astype(str).ne(REFERENCE_LABEL)
            & candidate_summary["warmup_conflicts"].eq(1)
        ]["hard_negative_min_search_ok_frac"]
    )
    random_wc3 = mean_numeric(
        candidate_summary[
            candidate_summary["candidate_label"].astype(str).ne(REFERENCE_LABEL)
            & candidate_summary["warmup_conflicts"].eq(3)
        ]["random_control_search_ok_frac"]
    )
    cpu_only_wc1 = mean_numeric(
        candidate_summary[
            candidate_summary["candidate_label"].astype(str).ne(REFERENCE_LABEL)
            & candidate_summary["warmup_conflicts"].eq(1)
        ]["cpu_only_win_frac"]
    )
    anchor_losses = int(
        candidate_summary[candidate_summary["candidate_label"].astype(str).ne(REFERENCE_LABEL)][
            "anchor_lost_vs_reference_rows"
        ].sum()
    )
    mismatch_count = int(len(mismatch_rows))
    role_lines: list[str] = []
    if not reward_summary.empty and "echosat_replay_role" in reward_summary.columns:
        for role in ["hard_negative_failure", "anchor_failure", "random_control", "subset_failure"]:
            rows = reward_summary[reward_summary["echosat_replay_role"].astype(str).eq(role)]
            if rows.empty:
                continue
            row = rows.iloc[0]
            role_lines.append(
                f"{role}: final_pos={format_float(row.get('positive_final_advantage_frac', float('nan')))}, "
                f"raw_pos={format_float(row.get('positive_raw_advantage_unclamped_frac', float('nan')))}"
            )
    reward_evidence = "; ".join(role_lines) if role_lines else "reward replay unavailable or no tracked failure roles"

    rows = [
        {
            "priority": 1,
            "issue": "hard_negative_recovery_below_v1_2",
            "evidence": (
                f"v1.2 wc1 hard_negative_min_search_ok={format_float(reference_hard_wc1)}; "
                f"mean v1.7 wc1 hard_negative_min_search_ok={format_float(v17_hard_wc1)}"
            ),
            "v1_8_requirement": "Make hard-negative pressure variant-level and require k10_color9/php_p10_h9 wc1 recovery at least v1.2 iter=15 before training.",
        },
        {
            "priority": 2,
            "issue": "random_control_positive_search",
            "evidence": f"mean v1.7 wc3 random_control_search_ok={format_float(random_wc3)}",
            "v1_8_requirement": "Clamp random-control raw reward and final GRPO advantage to <= 0; never count random-control search wins as symmetry positives.",
        },
        {
            "priority": 3,
            "issue": "cpu_or_protocol_win_can_mask_search_failure",
            "evidence": f"mean v1.7 wc1 cpu_only_win_frac={format_float(cpu_only_wc1)}",
            "v1_8_requirement": "CPU/protocol improvements should be non-positive reward unless both decisions and conflicts improve against cached trace.",
        },
        {
            "priority": 4,
            "issue": "anchor_preservation_must_be_hard_constraint",
            "evidence": f"v1.7 rows losing anchor search_ok vs v1.2={anchor_losses}",
            "v1_8_requirement": "Preserve k9_color8/php_p9_h8 as hard constraints in dry-run and checkpoint selection, not just aggregate terms.",
        },
        {
            "priority": 5,
            "issue": "wc1_wc3_event_instability",
            "evidence": "wc1/wc3 disagreement rows are emitted separately and should be inspected before changing warmup budgets.",
            "v1_8_requirement": "Add wc1/wc3 consistency penalty; wc3 is diagnostic until wc1 hard-negative behavior is stable.",
        },
        {
            "priority": 6,
            "issue": "offline_reward_runtime_mismatch",
            "evidence": f"reward mismatch rows={mismatch_count}; {reward_evidence}",
            "v1_8_requirement": "Dry-run v1.8 reward replay must show no positive raw or final advantage for search-bad, subset-failure, random-control, near-cap, or weighted-risk rows.",
        },
        {
            "priority": 7,
            "issue": "subset_bw12_perm1730_guard",
            "evidence": "subset_cardinality_bw12::perm_seed1730 is exported as a protected slice.",
            "v1_8_requirement": "Keep subset_cardinality_bw12::perm_seed1730 negative in replay and targeted acceptance; do not train it into a positive example.",
        },
    ]
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
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
                text = str(value).replace("\n", " ")
                cells.append(text)
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(
    *,
    path: Path,
    reference_path: Path,
    candidate_paths: dict[str, Path],
    reward_path: Path,
    paired: pd.DataFrame,
    candidate_summary: pd.DataFrame,
    base_summary: pd.DataFrame,
    family_summary: pd.DataFrame,
    disagreement: pd.DataFrame,
    reward_summary: pd.DataFrame,
    mismatch_rows: pd.DataFrame,
    recommendations: pd.DataFrame,
    outputs: dict[str, Path],
) -> None:
    warmups = ", ".join(map(str, sorted(paired["warmup_conflicts"].dropna().astype(int).unique().tolist())))
    headline_cols = [
        "candidate_label",
        "warmup_conflicts",
        "anchor_min_search_ok_frac",
        "hard_negative_min_search_ok_frac",
        "random_control_search_ok_frac",
        "subset_perm_failure_search_ok_frac",
        "candidate_search_ok_frac",
        "candidate_search_blowup_frac",
        "cpu_only_win_frac",
        "adapter_cached_decisions_delta_candidate_mean",
        "adapter_cached_conflicts_delta_candidate_mean",
        "adapter_cached_final_cpu_delta_candidate_mean",
        "search_ok_lost_vs_reference_rows",
        "search_ok_gained_vs_reference_rows",
    ]
    headline = candidate_summary[[column for column in headline_cols if column in candidate_summary.columns]].sort_values(
        ["warmup_conflicts", "candidate_label"]
    )
    focus_bases = base_summary[
        base_summary["base_instance_id"].astype(str).isin(
            sorted(ANCHOR_BASES | HARD_NEGATIVE_BASES | {SUBSET_FAILURE_BASE})
        )
    ].sort_values(["warmup_conflicts", "base_instance_id", "candidate_label"])
    random_family = family_summary[family_summary["family"].astype(str).eq("random_3sat_control")].sort_values(
        ["warmup_conflicts", "candidate_label"]
    )
    hard_wc1 = focus_bases[
        focus_bases["base_instance_id"].astype(str).isin(HARD_NEGATIVE_BASES) & focus_bases["warmup_conflicts"].eq(1)
    ]
    anchor_wc1 = focus_bases[
        focus_bases["base_instance_id"].astype(str).isin(ANCHOR_BASES) & focus_bases["warmup_conflicts"].eq(1)
    ]
    lines = [
        "# EchoSAT Symmetry GRPO v1.7 Failure Attribution",
        "",
        "This is an offline failure-attribution and objective-repair audit over existing v1.7 targeted acceptance and reward-replay artifacts. It does not train, rerun solver benchmarks, expand the benchmark, or add a gate/selector.",
        "",
        "## Inputs",
        "",
        f"- reference observations: `{display_path(reference_path)}`",
        *[f"- candidate `{label}` observations: `{display_path(path)}`" for label, path in sorted(candidate_paths.items())],
        f"- reward replay rows: `{display_path(reward_path)}`" if reward_path.exists() else f"- reward replay rows: `{display_path(reward_path)}` (missing)",
        "",
        "## Outputs",
        "",
        *[f"- {name}: `{display_path(output)}`" for name, output in outputs.items()],
        "",
        "## Scope",
        "",
        f"- paired rows: `{len(paired)}`",
        f"- warmup conflicts: `{warmups}`",
        f"- candidates: `{', '.join(sorted(paired['candidate_label'].astype(str).unique()))}`",
        f"- base instances: `{paired['base_instance_id'].nunique()}`",
        f"- wc1/wc3 disagreement rows: `{len(disagreement)}`",
        f"- reward mismatch rows: `{len(mismatch_rows)}`",
        "",
        "## Headline",
        "",
        "- The success metric remains adapter-vs-cached search work: both decisions and conflicts must decrease.",
        "- `v1_2_iter15` is included as a self-reference row; v1.7 rows are paired against it on the same base/variant/repeat/warmup keys.",
        "- CPU and protocol-time wins are diagnostic only and are tracked separately when search work is bad.",
        "",
        *markdown_table(headline, max_rows=20),
        "",
        "## WC1 Anchor Preservation",
        "",
        *markdown_table(
            anchor_wc1[
                [
                    "candidate_label",
                    "base_instance_id",
                    "candidate_search_ok_frac",
                    "reference_search_ok_frac",
                    "search_ok_frac_change_vs_reference",
                    "adapter_cached_decisions_delta_candidate_mean",
                    "adapter_cached_conflicts_delta_candidate_mean",
                    "adapter_cached_final_cpu_delta_candidate_mean",
                ]
            ],
            max_rows=40,
        ),
        "",
        "## WC1 Hard-Negative Recovery",
        "",
        *markdown_table(
            hard_wc1[
                [
                    "candidate_label",
                    "base_instance_id",
                    "candidate_search_ok_frac",
                    "reference_search_ok_frac",
                    "search_ok_frac_change_vs_reference",
                    "search_ok_lost_vs_reference_rows",
                    "adapter_cached_decisions_delta_candidate_mean",
                    "adapter_cached_conflicts_delta_candidate_mean",
                    "adapter_cached_final_cpu_delta_candidate_mean",
                ]
            ],
            max_rows=40,
        ),
        "",
        "## Random-Control Suppression",
        "",
        *markdown_table(
            random_family[
                [
                    "candidate_label",
                    "warmup_conflicts",
                    "candidate_search_ok_frac",
                    "candidate_search_blowup_frac",
                    "candidate_cpu_only_win_frac",
                    "candidate_protocol_win_search_bad_frac",
                    "adapter_cached_decisions_delta_candidate_mean",
                    "adapter_cached_conflicts_delta_candidate_mean",
                    "adapter_cached_final_cpu_delta_candidate_mean",
                    "adapter_plain_protocol_delta_candidate_mean",
                ]
            ],
            max_rows=40,
        ),
        "",
        "## WC1/WC3 Disagreement",
        "",
        *markdown_table(
            disagreement[
                [
                    column
                    for column in [
                        "candidate_label",
                        "family",
                        "target_role",
                        "base_instance_id",
                        "variant",
                        "repeat_id",
                        "wc1_search_ok",
                        "wc3_search_ok",
                    ]
                    if column in disagreement.columns
                ]
            ],
            max_rows=40,
        ),
        "",
        "## Reward Replay Mismatch",
        "",
        *markdown_table(reward_summary, max_rows=30),
        "",
        "Mismatch rows with positive raw/final advantage while replay search is bad:",
        "",
        *markdown_table(mismatch_rows, max_rows=40),
        "",
        "## v1.8 Objective-Repair Requirements",
        "",
        *markdown_table(recommendations, max_rows=20),
        "",
        "## Conclusion",
        "",
        "- Do not continue long GRPO training from the current v1.7 objective.",
        "- Do not expand benchmarks or train a gate/selector before objective repair.",
        "- Preserve `v1.2 iter=15.pt` as the conservative runtime candidate until a later objective beats it under strict search-work acceptance.",
        "- v1.8 should be dry-run audited first: anchors preserved, hard negatives pressured at variant level, random controls clamped, CPU-only wins non-positive, wc1/wc3 consistency enforced, and subset bw12 perm1730 kept negative.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_candidate_observations(values: list[str] | None) -> dict[str, Path]:
    if not values:
        return dict(DEFAULT_CANDIDATE_OBSERVATIONS)
    out: dict[str, Path] = {}
    for value in values:
        if "::" not in value:
            raise ValueError(f"candidate observation must use LABEL::PATH format: {value}")
        label, path = value.split("::", 1)
        out[label] = resolve(path)
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline v1.7 failure attribution against v1.2 iter=15.")
    parser.add_argument("--reference-observations", type=Path, default=DEFAULT_REFERENCE_OBSERVATIONS)
    parser.add_argument("--candidate-observation", action="append", dest="candidate_observations", default=None)
    parser.add_argument("--reward-replay", type=Path, default=DEFAULT_REWARD_REPLAY)
    parser.add_argument("--out-prefix", type=Path, default=DEFAULT_OUT_PREFIX)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reference_path = resolve(args.reference_observations)
    candidate_paths = parse_candidate_observations(args.candidate_observations)
    reward_path = resolve(args.reward_replay)
    out_prefix = resolve(args.out_prefix)
    doc_path = resolve(args.doc)

    reference = load_observation_frame(reference_path, candidate_label=REFERENCE_LABEL, source_path=reference_path)
    paired_frames = [compare_against_reference(reference, reference)]
    for label, path in sorted(candidate_paths.items()):
        candidate = load_observation_frame(path, candidate_label=label, source_path=path)
        paired_frames.append(compare_against_reference(reference, candidate))
    paired = pd.concat(paired_frames, ignore_index=True)

    candidate_summary = summarize_candidate(paired)
    base_summary = summarize_base(paired)
    family_summary = summarize_family(paired)
    disagreement = warmup_disagreement(paired)
    slices = important_slices(paired)

    reward_rows = load_reward_replay(reward_path)
    reward_summary = summarize_reward_replay(reward_rows)
    mismatch = reward_mismatch_rows(reward_rows)
    recommendations = objective_repair_recommendations(
        candidate_summary=candidate_summary,
        base_summary=base_summary,
        reward_summary=reward_summary,
        mismatch_rows=mismatch,
    )

    outputs = {
        "variant deltas": out_prefix.with_name(out_prefix.name + "_variant_deltas.csv"),
        "base summary": out_prefix.with_name(out_prefix.name + "_base_summary.csv"),
        "family summary": out_prefix.with_name(out_prefix.name + "_family_summary.csv"),
        "candidate summary": out_prefix.with_name(out_prefix.name + "_candidate_summary.csv"),
        "wc1 wc3 disagreement": out_prefix.with_name(out_prefix.name + "_wc1_wc3_disagreement.csv"),
        "anchor rows": out_prefix.with_name(out_prefix.name + "_anchor_rows.csv"),
        "hard negative rows": out_prefix.with_name(out_prefix.name + "_hard_negative_rows.csv"),
        "random control rows": out_prefix.with_name(out_prefix.name + "_random_control_rows.csv"),
        "subset failure rows": out_prefix.with_name(out_prefix.name + "_subset_failure_rows.csv"),
        "reward replay summary": out_prefix.with_name(out_prefix.name + "_reward_replay_summary.csv"),
        "reward runtime mismatch": out_prefix.with_name(out_prefix.name + "_reward_runtime_mismatch.csv"),
        "objective repair recommendations": out_prefix.with_name(out_prefix.name + "_objective_repair_recommendations.csv"),
    }
    for output in outputs.values():
        output.parent.mkdir(parents=True, exist_ok=True)

    paired.to_csv(outputs["variant deltas"], index=False)
    base_summary.to_csv(outputs["base summary"], index=False)
    family_summary.to_csv(outputs["family summary"], index=False)
    candidate_summary.to_csv(outputs["candidate summary"], index=False)
    disagreement.to_csv(outputs["wc1 wc3 disagreement"], index=False)
    slices["anchor_rows"].to_csv(outputs["anchor rows"], index=False)
    slices["hard_negative_rows"].to_csv(outputs["hard negative rows"], index=False)
    slices["random_control_rows"].to_csv(outputs["random control rows"], index=False)
    slices["subset_failure_rows"].to_csv(outputs["subset failure rows"], index=False)
    reward_summary.to_csv(outputs["reward replay summary"], index=False)
    mismatch.to_csv(outputs["reward runtime mismatch"], index=False)
    recommendations.to_csv(outputs["objective repair recommendations"], index=False)

    write_doc(
        path=doc_path,
        reference_path=reference_path,
        candidate_paths=candidate_paths,
        reward_path=reward_path,
        paired=paired,
        candidate_summary=candidate_summary,
        base_summary=base_summary,
        family_summary=family_summary,
        disagreement=disagreement,
        reward_summary=reward_summary,
        mismatch_rows=mismatch,
        recommendations=recommendations,
        outputs=outputs,
    )

    for name, output in outputs.items():
        print(f"wrote {name}: {output}")
    print(f"wrote doc: {doc_path}")


if __name__ == "__main__":
    main()
