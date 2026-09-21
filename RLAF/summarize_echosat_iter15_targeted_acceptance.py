from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd

from analyze_echosat_low_warmup_sweep import observations_from_file
from echosat_iter15_acceptance_common import (
    DEFAULT_BUDGETS,
    ROOT,
    TARGET_PREFIX,
    candidate_by_label,
    existing_per_instance_path,
)


ANCHOR_BASES = ["k9_color8", "php_p9_h8"]
HARD_RECOVERY_BASES = ["k10_color9", "php_p10_h9"]
SUBSET_FAILURE_BASE = "subset_cardinality_bw12"
SUBSET_FAILURE_VARIANT = "perm_seed1730"


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values.fillna(False)
    return values.fillna(False).astype(str).str.lower().isin({"1", "true", "yes", "y"})


def finite_mean(values: pd.Series, default: float = 0.0) -> float:
    if values.empty:
        return default
    out = pd.to_numeric(values, errors="coerce").mean()
    return float(out) if pd.notna(out) and math.isfinite(float(out)) else default


def load_observations(candidates: list[str] | None, budgets: list[int]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for candidate in candidate_by_label(candidates):
        for budget in budgets:
            path, source = existing_per_instance_path(candidate, int(budget))
            if path is None:
                raise FileNotFoundError(
                    f"missing per-instance CSV for {candidate.label} wc{budget}; "
                    "run run_echosat_iter15_targeted_acceptance.py first"
                )
            frame = observations_from_file(path, allow_weighted_no_pre=False)
            frame.insert(0, "candidate_label", candidate.label)
            frame.insert(1, "candidate_name", candidate.display_name)
            frame.insert(2, "candidate_role", candidate.role)
            frame.insert(3, "candidate_checkpoint_path", str(candidate.checkpoint_path))
            frame.insert(4, "source_kind", source)
            frames.append(frame)
    if not frames:
        raise ValueError("no targeted acceptance observations loaded")
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
                "base_instances": int(group["base_instance_id"].nunique()),
                "variants": int(group["variant"].nunique()),
                "repeats": int(group["repeat_id"].nunique()),
                "search_ok_frac": float(group["search_ok"].mean()),
                "search_blowup_frac": float(group["search_blowup"].mean()),
                "adapter_cached_decisions_delta_mean": float(group["adapter_cached_decisions_delta"].mean()),
                "adapter_cached_conflicts_delta_mean": float(group["adapter_cached_conflicts_delta"].mean()),
                "adapter_cached_cpu_delta_mean": float(group["adapter_cached_final_cpu_delta"].mean()),
                "adapter_plain_protocol_delta_mean": float(group["adapter_plain_protocol_delta"].mean()),
                "all_event_adapter_solved": bool(bool_series(group["event_adapter_final_final_solved"]).all()),
                "known_expected_rows": int(bool_series(group["known_expected_result"]).sum()),
                "known_expected_match_rows": int(bool_series(group["event_adapter_final_known_expected_match"]).sum()),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def base_search_ok(group: pd.DataFrame, base: str) -> float:
    rows = group[group["base_instance_id"].astype(str).eq(base)]
    return float(rows["search_ok"].mean()) if not rows.empty else float("nan")


def variant_search_ok(group: pd.DataFrame, base: str, variant: str) -> float:
    rows = group[
        group["base_instance_id"].astype(str).eq(base)
        & group["variant"].astype(str).eq(variant)
    ]
    return float(rows["search_ok"].mean()) if not rows.empty else float("nan")


def strict_score(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, name, role, warmup), group in frame.groupby(
        ["candidate_label", "candidate_name", "candidate_role", "warmup_conflicts"],
        sort=True,
        dropna=False,
    ):
        anchors = [base_search_ok(group, base) for base in ANCHOR_BASES]
        hard = [base_search_ok(group, base) for base in HARD_RECOVERY_BASES]
        anchor_min = min(anchors) if all(math.isfinite(value) for value in anchors) else float("nan")
        hard_min = min(hard) if all(math.isfinite(value) for value in hard) else float("nan")
        random_rows = group[group["random_control"]]
        strong_rows = group[group["symmetry_strength"].astype(str).eq("strong")]
        random_ok = float(random_rows["search_ok"].mean()) if not random_rows.empty else float("nan")
        strong_ok = float(strong_rows["search_ok"].mean()) if not strong_rows.empty else float("nan")
        subset_perm = variant_search_ok(group, SUBSET_FAILURE_BASE, SUBSET_FAILURE_VARIANT)
        blowup = float(group["search_blowup"].mean())
        score = 0.0
        score += 3.0 * (anchor_min if math.isfinite(anchor_min) else 0.0)
        score += 2.0 * (hard_min if math.isfinite(hard_min) else 0.0)
        score += 1.0 * (strong_ok if math.isfinite(strong_ok) else 0.0)
        score -= 2.0 * (random_ok if math.isfinite(random_ok) else 0.0)
        score -= 1.0 * (subset_perm if math.isfinite(subset_perm) else 0.0)
        score -= 1.0 * blowup

        known = bool_series(group["known_expected_result"])
        matched = bool_series(group["event_adapter_final_known_expected_match"])
        rows.append(
            {
                "candidate_label": candidate,
                "candidate_name": name,
                "candidate_role": role,
                "warmup_conflicts": int(warmup),
                "strict_search_work_score": score,
                "anchor_min_search_ok_frac": anchor_min,
                "hard_recovery_min_search_ok_frac": hard_min,
                "k9_color8_search_ok_frac": base_search_ok(group, "k9_color8"),
                "php_p9_h8_search_ok_frac": base_search_ok(group, "php_p9_h8"),
                "k10_color9_search_ok_frac": base_search_ok(group, "k10_color9"),
                "php_p10_h9_search_ok_frac": base_search_ok(group, "php_p10_h9"),
                "strong_symmetry_search_ok_frac": strong_ok,
                "random_control_search_ok_frac": random_ok,
                "subset_bw12_perm1730_search_ok_frac": subset_perm,
                "overall_search_ok_frac": float(group["search_ok"].mean()),
                "overall_search_blowup_frac": blowup,
                "overall_adapter_cached_decisions_delta_mean": float(group["adapter_cached_decisions_delta"].mean()),
                "overall_adapter_cached_conflicts_delta_mean": float(group["adapter_cached_conflicts_delta"].mean()),
                "overall_adapter_cached_cpu_delta_mean": float(group["adapter_cached_final_cpu_delta"].mean()),
                "overall_adapter_plain_protocol_delta_mean": float(group["adapter_plain_protocol_delta"].mean()),
                "all_event_adapter_solved": bool(bool_series(group["event_adapter_final_final_solved"]).all()),
                "known_expected_rows": int(known.sum()),
                "known_expected_match_rows": int(matched.sum()),
                "known_expected_all_match": bool(matched[known].all()) if bool(known.any()) else True,
            }
        )
    return pd.DataFrame(rows)


def main_acceptance(summary: pd.DataFrame, random_threshold: float) -> pd.DataFrame:
    rows = summary[
        summary["candidate_label"].astype(str).eq("v1_2_iter15")
        & summary["warmup_conflicts"].eq(1)
    ].copy()
    if rows.empty:
        raise ValueError("main candidate v1_2_iter15 wc1 summary is missing")
    row = rows.iloc[0]
    checks = {
        "k9_color8_wc1_search_ok_is_1": float(row["k9_color8_search_ok_frac"]) >= 1.0,
        "php_p9_h8_wc1_search_ok_is_1": float(row["php_p9_h8_search_ok_frac"]) >= 1.0,
        "k10_color9_wc1_search_ok_at_least_2_of_3": float(row["k10_color9_search_ok_frac"]) >= (2.0 / 3.0),
        "php_p10_h9_wc1_search_ok_at_least_2_of_3": float(row["php_p10_h9_search_ok_frac"]) >= (2.0 / 3.0),
        "random_control_wc1_search_ok_near_zero": float(row["random_control_search_ok_frac"]) <= float(random_threshold),
        "subset_bw12_perm1730_remains_negative": float(row["subset_bw12_perm1730_search_ok_frac"]) <= 0.0,
        "all_event_adapter_solved": bool(row["all_event_adapter_solved"]),
        "known_expected_all_match": bool(row["known_expected_all_match"]),
    }
    out = pd.DataFrame(
        [{"check": check, "passed": bool(passed)} for check, passed in checks.items()]
    )
    out.loc[len(out)] = {"check": "MAIN_CANDIDATE_WC1_ACCEPTANCE", "passed": bool(all(checks.values()))}
    return out


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
    by_base: pd.DataFrame,
    by_family: pd.DataFrame,
    acceptance: pd.DataFrame,
    outputs: dict[str, Path],
) -> None:
    focus_bases = set(ANCHOR_BASES + HARD_RECOVERY_BASES + [SUBSET_FAILURE_BASE])
    focus = by_base[by_base["base_instance_id"].astype(str).isin(focus_bases)].sort_values(
        ["warmup_conflicts", "base_instance_id", "candidate_role", "candidate_label"]
    )
    random_family = by_family[by_family["family"].astype(str).eq("random_3sat_control")].sort_values(
        ["warmup_conflicts", "candidate_role", "candidate_label"]
    )
    acceptance_pass = bool(
        acceptance.loc[acceptance["check"].eq("MAIN_CANDIDATE_WC1_ACCEPTANCE"), "passed"].iloc[0]
    )
    lines = [
        "# EchoSAT iter=15 Targeted Acceptance",
        "",
        "This freezes v1.2 `iter=15.pt` as the main candidate and compares it against v1.2 `best.pt`, v1.2 `iter=235.pt`, v1.1 `iter=85.pt`, and v1.2 `iter=50.pt` as a wc3 diagnostic. It does not train, expand the benchmark, or add a gate/selector.",
        "",
        "## Artifacts",
        "",
        *[f"- {name}: `{display_path(output)}`" for name, output in outputs.items()],
        "",
        "## Scope",
        "",
        f"- observation rows: `{len(observations)}`",
        "- families: `complete_coloring`, `php`, `subset_cardinality`, `random_3sat_control`",
        "- primary acceptance budget: `wc1`",
        "- diagnostic budgets: `wc3`, `wc5`",
        "- success metric: adapter-vs-cached decisions/conflicts reduction; CPU is diagnostic only.",
        "",
        "## Acceptance",
        "",
        f"- main candidate wc1 acceptance: `{'PASS' if acceptance_pass else 'FAIL'}`",
        "",
        *markdown_table(acceptance, max_rows=20),
        "",
        "## Strict Search-Work Scores",
        "",
        *markdown_table(
            strict.sort_values(["warmup_conflicts", "strict_search_work_score"], ascending=[True, False])[
                [
                    "candidate_label",
                    "candidate_name",
                    "candidate_role",
                    "warmup_conflicts",
                    "strict_search_work_score",
                    "anchor_min_search_ok_frac",
                    "hard_recovery_min_search_ok_frac",
                    "strong_symmetry_search_ok_frac",
                    "random_control_search_ok_frac",
                    "subset_bw12_perm1730_search_ok_frac",
                    "overall_search_blowup_frac",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Focus Bases",
        "",
        *markdown_table(
            focus[
                [
                    "candidate_label",
                    "candidate_role",
                    "warmup_conflicts",
                    "family",
                    "base_instance_id",
                    "search_ok_frac",
                    "search_blowup_frac",
                    "adapter_cached_decisions_delta_mean",
                    "adapter_cached_conflicts_delta_mean",
                    "adapter_cached_cpu_delta_mean",
                    "adapter_plain_protocol_delta_mean",
                ]
            ],
            max_rows=140,
        ),
        "",
        "## Random Controls",
        "",
        *markdown_table(
            random_family[
                [
                    "candidate_label",
                    "candidate_role",
                    "warmup_conflicts",
                    "search_ok_frac",
                    "search_blowup_frac",
                    "adapter_cached_decisions_delta_mean",
                    "adapter_cached_conflicts_delta_mean",
                    "adapter_cached_cpu_delta_mean",
                    "adapter_plain_protocol_delta_mean",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Interpretation",
        "",
        "- `v1_2_iter15` is accepted only on wc1; wc3/wc5 are diagnostics for warmup sensitivity.",
        "- `v1_2_iter50` remains a wc3 diagnostic and is not promoted to the main candidate.",
        "- Protocol time and adapter-vs-plain deltas are recorded, but they do not define success here.",
        "- No solver speedup claim follows from this targeted acceptance report.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize iter=15 targeted acceptance.")
    parser.add_argument("--candidates", nargs="*", default=None)
    parser.add_argument("--budgets", nargs="*", type=int, default=DEFAULT_BUDGETS)
    parser.add_argument("--random-threshold", type=float, default=0.05)
    parser.add_argument("--observations-csv", type=Path, default=ROOT / f"runs/analysis/{TARGET_PREFIX}_observations.csv")
    parser.add_argument("--strict-csv", type=Path, default=ROOT / f"runs/analysis/{TARGET_PREFIX}_strict_acceptance.csv")
    parser.add_argument("--by-base-csv", type=Path, default=ROOT / f"runs/analysis/{TARGET_PREFIX}_by_base.csv")
    parser.add_argument("--by-family-csv", type=Path, default=ROOT / f"runs/analysis/{TARGET_PREFIX}_by_family.csv")
    parser.add_argument("--acceptance-csv", type=Path, default=ROOT / f"runs/analysis/{TARGET_PREFIX}_main_candidate_checks.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / f"docs/{TARGET_PREFIX}.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    observations = load_observations(args.candidates, [int(budget) for budget in args.budgets])
    by_base = summarize_group(
        observations,
        ["candidate_label", "candidate_name", "candidate_role", "warmup_conflicts", "family", "base_instance_id"],
    )
    by_family = summarize_group(
        observations,
        ["candidate_label", "candidate_name", "candidate_role", "warmup_conflicts", "family"],
    )
    strict = strict_score(observations)
    acceptance = main_acceptance(strict, random_threshold=float(args.random_threshold))

    outputs = {
        "observations": args.observations_csv,
        "strict acceptance": args.strict_csv,
        "summary by base": args.by_base_csv,
        "summary by family": args.by_family_csv,
        "main candidate checks": args.acceptance_csv,
    }
    for output in [*outputs.values(), args.doc]:
        output.parent.mkdir(parents=True, exist_ok=True)
    observations.to_csv(args.observations_csv, index=False)
    strict.to_csv(args.strict_csv, index=False)
    by_base.to_csv(args.by_base_csv, index=False)
    by_family.to_csv(args.by_family_csv, index=False)
    acceptance.to_csv(args.acceptance_csv, index=False)
    write_doc(
        args.doc,
        observations=observations,
        strict=strict,
        by_base=by_base,
        by_family=by_family,
        acceptance=acceptance,
        outputs=outputs,
    )
    print(f"wrote {args.observations_csv}")
    print(f"wrote {args.strict_csv}")
    print(f"wrote {args.by_base_csv}")
    print(f"wrote {args.by_family_csv}")
    print(f"wrote {args.acceptance_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
