from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_observations.csv"
DEFAULT_POLICY = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1_policy.csv"
DEFAULT_SUMMARY = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1_summary.csv"
DEFAULT_FAMILY = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1_by_family.csv"
DEFAULT_BASE = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1_by_base.csv"
DEFAULT_DOC = ROOT / "docs/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1.md"

METHOD_PREFIXES = [
    "plain_unguided_glucose",
    "neutral_weighted_glucose",
    "static_weighted_glucose",
    "cached_trace_no_adapter_final",
    "event_adapter_final",
]
REQUIRED_COLUMNS = [
    "warmup_conflicts",
    "family",
    "base_instance_id",
    "variant",
    "repeat_id",
    "plain_unguided_glucose_final_cpu_time",
    "plain_unguided_glucose_protocol_accounted_time",
    "neutral_weighted_glucose_final_cpu_time",
    "static_weighted_glucose_final_cpu_time",
    "cached_trace_no_adapter_final_final_cpu_time",
    "cached_trace_no_adapter_final_protocol_accounted_time",
    "event_adapter_final_final_cpu_time",
    "event_adapter_final_protocol_accounted_time",
    "event_state_l2_sum",
    "event_state_nonzero_vars",
    "event_adapter_graph_gate_open",
    "warmup_conflict_count",
    "warmup_decisions",
    "final_cpu_lim",
]


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values.fillna(False)
    return values.fillna(False).astype(str).str.lower().isin({"1", "true", "yes", "y"})


def finite(value: Any, default: float = math.nan) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def rel_delta(delta: pd.Series, baseline: pd.Series) -> pd.Series:
    return delta / pd.to_numeric(baseline, errors="coerce").clip(lower=1.0e-9)


def load_observations(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    for prefix in METHOD_PREFIXES:
        solved_col = f"{prefix}_final_solved"
        if solved_col in frame.columns:
            if not bool_series(frame[solved_col]).all():
                raise ValueError(f"{path} contains unsolved rows for {prefix}")
    if "weighted_no_pre" in frame.columns and bool_series(frame["weighted_no_pre"]).any():
        raise ValueError(f"{path} contains weighted_no_pre=True rows; v1 gate audit expects patched_pretrue_main.")
    if "solver_path_role" in frame.columns:
        roles = sorted(set(frame["solver_path_role"].dropna().astype(str)))
        if roles and roles != ["patched_pretrue_main"]:
            raise ValueError(f"{path} has non-main solver path roles: {roles}")
    out = frame.copy()
    numeric_columns = [
        column
        for column in out.columns
        if column.endswith("_time")
        or column.endswith("_delta")
        or column.endswith("_decisions")
        or column.endswith("_conflicts")
        or column
        in {
            "warmup_conflicts",
            "warmup_conflict_count",
            "warmup_decisions",
            "event_state_l2_sum",
            "event_state_nonzero_vars",
            "event_adapter_graph_gate_evidence",
            "final_cpu_lim",
            "num_vars",
            "num_clauses",
        }
    ]
    for column in numeric_columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out["event_adapter_graph_gate_open"] = bool_series(out["event_adapter_graph_gate_open"])
    return out


def add_prefinal_features(frame: pd.DataFrame, *, near_cap_fraction: float) -> pd.DataFrame:
    out = frame.copy()
    out["neutral_plain_final_cpu_delta"] = (
        out["neutral_weighted_glucose_final_cpu_time"] - out["plain_unguided_glucose_final_cpu_time"]
    )
    out["static_neutral_final_cpu_delta"] = (
        out["static_weighted_glucose_final_cpu_time"] - out["neutral_weighted_glucose_final_cpu_time"]
    )
    out["neutral_plain_final_cpu_rel_delta"] = rel_delta(
        out["neutral_plain_final_cpu_delta"],
        out["plain_unguided_glucose_final_cpu_time"],
    )
    out["static_neutral_final_cpu_rel_delta"] = rel_delta(
        out["static_neutral_final_cpu_delta"],
        out["neutral_weighted_glucose_final_cpu_time"],
    )
    cap = out["final_cpu_lim"].fillna(out["final_cpu_lim"].max()).clip(lower=1.0e-9)
    cap_threshold = float(near_cap_fraction) * cap
    out["plain_near_cap"] = out["plain_unguided_glucose_final_cpu_time"] >= cap_threshold
    out["neutral_near_cap"] = out["neutral_weighted_glucose_final_cpu_time"] >= cap_threshold
    out["static_near_cap"] = out["static_weighted_glucose_final_cpu_time"] >= cap_threshold
    out["event_density"] = out["event_state_l2_sum"] / out["event_state_nonzero_vars"].clip(lower=1.0)
    return out


def family_allowed(frame: pd.DataFrame, allowed: set[str]) -> pd.Series:
    return frame["family"].astype(str).isin(allowed)


def weighted_path_ok(
    frame: pd.DataFrame,
    *,
    abs_threshold: float,
    rel_threshold: float,
    slowdown_logic: str,
    use_cap_veto: bool,
) -> pd.Series:
    neutral_abs = frame["neutral_plain_final_cpu_delta"] > float(abs_threshold)
    neutral_rel = frame["neutral_plain_final_cpu_rel_delta"] > float(rel_threshold)
    static_abs = frame["static_neutral_final_cpu_delta"] > float(abs_threshold)
    static_rel = frame["static_neutral_final_cpu_rel_delta"] > float(rel_threshold)
    if slowdown_logic == "both":
        neutral_risk = neutral_abs & neutral_rel
        static_risk = static_abs & static_rel
    elif slowdown_logic == "either":
        neutral_risk = neutral_abs | neutral_rel
        static_risk = static_abs | static_rel
    else:
        raise ValueError(f"unknown slowdown_logic={slowdown_logic!r}")
    cap_risk = frame["plain_near_cap"] | frame["neutral_near_cap"] | frame["static_near_cap"]
    if not use_cap_veto:
        cap_risk = pd.Series(False, index=frame.index)
    return ~(neutral_risk | static_risk | cap_risk)


def event_signal_ok(
    frame: pd.DataFrame,
    *,
    min_event_l2: float,
    min_event_density: float,
    require_graph_gate_open: bool,
) -> pd.Series:
    ok = (frame["event_state_l2_sum"] >= float(min_event_l2)) & (frame["event_density"] >= float(min_event_density))
    if require_graph_gate_open:
        ok &= frame["event_adapter_graph_gate_open"].astype(bool)
    return ok


def scale_ok(
    frame: pd.DataFrame,
    *,
    max_vars: int | None,
    min_vars: int,
) -> pd.Series:
    if "num_vars" not in frame.columns:
        return pd.Series(True, index=frame.index)
    num_vars = pd.to_numeric(frame["num_vars"], errors="coerce")
    ok = num_vars >= int(min_vars)
    if max_vars is not None:
        ok &= num_vars <= int(max_vars)
    return ok.fillna(False)


def apply_policy(frame: pd.DataFrame, policy_name: str, allow_adapter: pd.Series) -> pd.DataFrame:
    out = frame.copy()
    use_adapter = allow_adapter.fillna(False).astype(bool)
    out["policy_name"] = policy_name
    out["policy_uses_adapter"] = use_adapter
    out["policy_solver_path_role"] = np.where(use_adapter, "event_adapter_allowed", "plain_fallback")
    metric_pairs = {
        "final_cpu_time": (
            "event_adapter_final_final_cpu_time",
            "plain_unguided_glucose_final_cpu_time",
            "cached_trace_no_adapter_final_final_cpu_time",
        ),
        "protocol_accounted_time": (
            "event_adapter_final_protocol_accounted_time",
            "plain_unguided_glucose_protocol_accounted_time",
            "cached_trace_no_adapter_final_protocol_accounted_time",
        ),
        "final_decisions": (
            "event_adapter_final_final_decisions",
            "plain_unguided_glucose_final_decisions",
            "cached_trace_no_adapter_final_final_decisions",
        ),
        "final_conflicts": (
            "event_adapter_final_final_conflicts",
            "plain_unguided_glucose_final_conflicts",
            "cached_trace_no_adapter_final_final_conflicts",
        ),
    }
    for metric, (adapter_col, plain_col, cached_col) in metric_pairs.items():
        if adapter_col in out.columns and plain_col in out.columns:
            out[f"policy_{metric}"] = np.where(use_adapter, out[adapter_col], out[plain_col])
            out[f"policy_minus_plain_{metric}"] = out[f"policy_{metric}"] - out[plain_col]
            out[f"adapter_minus_plain_{metric}"] = out[adapter_col] - out[plain_col]
        if adapter_col in out.columns and cached_col in out.columns:
            out[f"adapter_minus_cached_{metric}"] = out[adapter_col] - out[cached_col]
    return out


def policy_frames(frame: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    weighted_ok = weighted_path_ok(
        frame,
        abs_threshold=float(args.weighted_abs_threshold),
        rel_threshold=float(args.weighted_rel_threshold),
        slowdown_logic=str(args.weighted_slowdown_logic),
        use_cap_veto=not bool(args.no_cap_veto),
    )
    event_ok = event_signal_ok(
        frame,
        min_event_l2=float(args.min_event_l2),
        min_event_density=float(args.min_event_density),
        require_graph_gate_open=not bool(args.no_require_graph_gate_open),
    )
    small_symmetric_ok = scale_ok(frame, max_vars=int(args.feature_max_vars), min_vars=int(args.feature_min_vars))
    family_upper_bound_ok = family_allowed(frame, {"complete_coloring"}) & weighted_ok & event_ok
    family_complete_php_ok = family_allowed(frame, {"complete_coloring", "php"}) & weighted_ok & event_ok
    feature_gate_ok = weighted_ok & event_ok & small_symmetric_ok
    frames = [
        apply_policy(frame, "always_event_adapter", pd.Series(True, index=frame.index)),
        apply_policy(frame, "weighted_hard_veto_only", weighted_ok),
        apply_policy(frame, "family_complete_coloring_upper_bound", family_upper_bound_ok),
        apply_policy(frame, "family_complete_php_upper_bound", family_complete_php_ok),
        apply_policy(frame, "feature_small_symmetric_prefinal_gate", feature_gate_ok),
    ]
    return pd.concat(frames, ignore_index=True)


def summarize(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(group_columns, sort=True, dropna=False)
    out = grouped.agg(
        rows=("instance_id", "size") if "instance_id" in frame.columns else ("repeat_id", "size"),
        base_instances=("base_instance_id", "nunique"),
        variants=("variant", "nunique"),
        repeats=("repeat_id", "nunique"),
        adapter_allowed_rows=("policy_uses_adapter", "sum"),
        adapter_allowed_fraction=("policy_uses_adapter", "mean"),
        policy_minus_plain_protocol_mean=("policy_minus_plain_protocol_accounted_time", "mean"),
        policy_minus_plain_protocol_median=("policy_minus_plain_protocol_accounted_time", "median"),
        policy_minus_plain_final_cpu_mean=("policy_minus_plain_final_cpu_time", "mean"),
        policy_minus_plain_final_cpu_median=("policy_minus_plain_final_cpu_time", "median"),
        adapter_minus_plain_protocol_mean=("adapter_minus_plain_protocol_accounted_time", "mean"),
        adapter_minus_plain_final_cpu_mean=("adapter_minus_plain_final_cpu_time", "mean"),
        adapter_minus_cached_final_cpu_mean=("adapter_minus_cached_final_cpu_time", "mean"),
        adapter_minus_cached_decisions_mean=("adapter_minus_cached_final_decisions", "mean"),
        adapter_minus_cached_conflicts_mean=("adapter_minus_cached_final_conflicts", "mean"),
        event_l2_mean=("event_state_l2_sum", "mean"),
        event_density_mean=("event_density", "mean"),
        graph_gate_open_fraction=("event_adapter_graph_gate_open", "mean"),
        neutral_plain_delta_mean=("neutral_plain_final_cpu_delta", "mean"),
        static_neutral_delta_mean=("static_neutral_final_cpu_delta", "mean"),
        warmup_decisions_mean=("warmup_decisions", "mean"),
    )
    out = out.reset_index()
    out["policy_protocol_improved_vs_plain"] = out["policy_minus_plain_protocol_mean"] < 0.0
    out["policy_final_cpu_improved_vs_plain"] = out["policy_minus_plain_final_cpu_mean"] < 0.0
    return out


def base_summary(policy: pd.DataFrame) -> pd.DataFrame:
    return summarize(policy, ["policy_name", "warmup_conflicts", "family", "base_instance_id"])


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells = []
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
    policy: pd.DataFrame,
    summary: pd.DataFrame,
    by_family: pd.DataFrame,
    by_base: pd.DataFrame,
    policy_csv: Path,
    summary_csv: Path,
    family_csv: Path,
    base_csv: Path,
    args: argparse.Namespace,
) -> None:
    overall_view = summary[
        [
            "policy_name",
            "warmup_conflicts",
            "rows",
            "base_instances",
            "adapter_allowed_fraction",
            "policy_minus_plain_protocol_mean",
            "policy_minus_plain_final_cpu_mean",
            "adapter_minus_cached_final_cpu_mean",
        ]
    ].sort_values(["warmup_conflicts", "policy_name"])
    family_view = by_family[
        [
            "policy_name",
            "warmup_conflicts",
            "family",
            "base_instances",
            "adapter_allowed_fraction",
            "policy_minus_plain_protocol_mean",
            "policy_minus_plain_final_cpu_mean",
            "adapter_minus_cached_final_cpu_mean",
        ]
    ].sort_values(["warmup_conflicts", "policy_name", "family"])
    allowed_bases = by_base[by_base["adapter_allowed_fraction"] > 0.0][
        [
            "policy_name",
            "warmup_conflicts",
            "family",
            "base_instance_id",
            "adapter_allowed_fraction",
            "policy_minus_plain_protocol_mean",
            "policy_minus_plain_final_cpu_mean",
            "adapter_minus_cached_final_cpu_mean",
            "event_l2_mean",
            "event_density_mean",
            "neutral_plain_delta_mean",
            "static_neutral_delta_mean",
        ]
    ].sort_values(["warmup_conflicts", "policy_name", "family", "base_instance_id"])
    feature_gate = by_family[by_family["policy_name"] == "feature_small_symmetric_prefinal_gate"].sort_values(
        ["warmup_conflicts", "family"]
    )
    lines = [
        "# EchoSAT Low-Warmup Pre-Final Gate Audit v1",
        "",
        "This is an offline policy replay over corrected low-warmup CSVs. It does not train, does not rerun solver jobs, and does not use event-adapter final runtime to decide whether the adapter is allowed.",
        "",
        "## Policy Inputs",
        "",
        "- neutral weighted final CPU versus plain final CPU",
        "- static weighted final CPU versus neutral weighted final CPU",
        "- near-cap risk from plain, neutral weighted, or static weighted final CPU",
        "- warmup event L2, event density, graph-gate-open evidence, and CNF scale",
        "",
        "The family-aware policies are upper-bound audits, not deployable gates. The feature-only policy uses no family label and is included to check whether pre-final signals separate complete_coloring/php from random controls.",
        "",
        "Important caveat: `docs/echosat_formula_equivalence_audit_v1.md` shows that the harder-baseline `complete_coloring/k9_color8` and `php_p9_h8` rows, and likewise `k10_color9` and `php_p10_h9`, share the same unordered CNF formula. Their DIMACS clause order differs. Therefore complete_coloring/php runtime differences in this audit are ordering/permutation diagnostics, not family-specific SAT symmetry evidence by themselves.",
        "",
        "## Selected Thresholds",
        "",
        f"- weighted slowdown: abs>{args.weighted_abs_threshold}, rel>{args.weighted_rel_threshold}, logic={args.weighted_slowdown_logic}",
        f"- near-cap veto fraction: {'disabled' if args.no_cap_veto else args.near_cap_fraction}",
        f"- event signal: L2>={args.min_event_l2}, density>={args.min_event_density}, graph gate required={not args.no_require_graph_gate_open}",
        f"- feature-only scale window: {args.feature_min_vars} <= num_vars <= {args.feature_max_vars}",
        "",
        "## Artifacts",
        "",
        f"- policy CSV: `{display_path(policy_csv)}`",
        f"- summary CSV: `{display_path(summary_csv)}`",
        f"- by-family CSV: `{display_path(family_csv)}`",
        f"- by-base CSV: `{display_path(base_csv)}`",
        "",
        "## Overall",
        "",
        *markdown_table(overall_view, max_rows=80),
        "",
        "## Feature-Only Gate By Family",
        "",
        *markdown_table(
            feature_gate[
                [
                    "warmup_conflicts",
                    "family",
                    "base_instances",
                    "adapter_allowed_fraction",
                    "policy_minus_plain_protocol_mean",
                    "policy_minus_plain_final_cpu_mean",
                    "adapter_minus_cached_final_cpu_mean",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## By Family",
        "",
        *markdown_table(family_view, max_rows=120),
        "",
        "## Adapter-Allowed Base Rows",
        "",
        *markdown_table(allowed_bases, max_rows=160),
        "",
        "## Interpretation Rules",
        "",
        "- `policy_minus_plain_protocol_mean < 0` is the end-to-end replay criterion against basic Glucose.",
        "- `adapter_minus_cached_final_cpu_mean < 0` means the adapter changed final search beneficially after sharing the same cached-trace path.",
        "- If only family-aware policies work, the current evidence is mechanism-local but not yet deployable.",
        "- If feature-only policy excludes random controls but cannot separate formula-equivalent complete_coloring/php ordering cases, the next step is canonicalization/order-sensitivity analysis, not selector training.",
        "- If feature-only policy admits random controls with large gains, the signal remains generic perturbation rather than SAT symmetry-specific.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline pre-final gate audit for corrected EchoSAT low-warmup runs.")
    parser.add_argument("--observations-csv", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--policy-csv", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--by-family-csv", type=Path, default=DEFAULT_FAMILY)
    parser.add_argument("--by-base-csv", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--near-cap-fraction", type=float, default=0.80)
    parser.add_argument("--weighted-abs-threshold", type=float, default=0.25)
    parser.add_argument("--weighted-rel-threshold", type=float, default=0.10)
    parser.add_argument("--weighted-slowdown-logic", choices=["both", "either"], default="both")
    parser.add_argument("--no-cap-veto", action="store_true")
    parser.add_argument("--min-event-l2", type=float, default=50.0)
    parser.add_argument("--min-event-density", type=float, default=1.0)
    parser.add_argument("--no-require-graph-gate-open", action="store_true")
    parser.add_argument("--feature-min-vars", type=int, default=1)
    parser.add_argument("--feature-max-vars", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    observations = load_observations(resolve(args.observations_csv))
    observations = add_prefinal_features(observations, near_cap_fraction=float(args.near_cap_fraction))
    policy = policy_frames(observations, args)
    summary = summarize(policy, ["policy_name", "warmup_conflicts"])
    by_family = summarize(policy, ["policy_name", "warmup_conflicts", "family"])
    by_base = base_summary(policy)

    policy_path = resolve(args.policy_csv)
    summary_path = resolve(args.summary_csv)
    family_path = resolve(args.by_family_csv)
    base_path = resolve(args.by_base_csv)
    for path in [policy_path, summary_path, family_path, base_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
    policy.to_csv(policy_path, index=False)
    summary.to_csv(summary_path, index=False)
    by_family.to_csv(family_path, index=False)
    by_base.to_csv(base_path, index=False)
    write_doc(
        resolve(args.doc),
        policy=policy,
        summary=summary,
        by_family=by_family,
        by_base=by_base,
        policy_csv=policy_path,
        summary_csv=summary_path,
        family_csv=family_path,
        base_csv=base_path,
        args=args,
    )
    print(f"wrote {policy_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {family_path}")
    print(f"wrote {base_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
