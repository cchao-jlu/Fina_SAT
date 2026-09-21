from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def fnum(value: Any) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(value):
        return "nan"
    return f"{value:.6g}"


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows)
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fnum(row[column]) for column in columns) + " |")
    return lines


def with_acceptance_gates(
    strict: pd.DataFrame,
    *,
    anchor_min: float,
    hard_min: float,
    random_max: float,
    subset_max: float,
    require_solved: bool,
    require_correctness: bool,
) -> pd.DataFrame:
    out = strict.copy()
    out["known_expected_all_match"] = (
        pd.to_numeric(out["known_expected_rows"], errors="coerce")
        == pd.to_numeric(out["known_expected_match_rows"], errors="coerce")
    )
    out["gate_anchor_pass"] = pd.to_numeric(out["anchor_min_search_ok_frac"], errors="coerce") >= anchor_min
    out["gate_hard_negative_pass"] = pd.to_numeric(out["hard_negative_min_search_ok_frac"], errors="coerce") >= hard_min
    out["gate_random_control_pass"] = pd.to_numeric(out["random_control_search_ok_frac"], errors="coerce") <= random_max
    out["gate_subset_perm1730_pass"] = pd.to_numeric(out["subset_bw12_perm1730_search_ok_frac"], errors="coerce") <= subset_max
    out["gate_solved_pass"] = out["all_solved"].astype(bool) if require_solved else True
    out["gate_correctness_pass"] = out["known_expected_all_match"].astype(bool) if require_correctness else True
    gate_columns = [
        "gate_anchor_pass",
        "gate_hard_negative_pass",
        "gate_random_control_pass",
        "gate_subset_perm1730_pass",
        "gate_solved_pass",
        "gate_correctness_pass",
    ]
    out["hard_gate_pass"] = out[gate_columns].all(axis=1)
    out["gate_violation_count"] = (~out[gate_columns]).sum(axis=1)
    out["gate_anchor_shortfall"] = (anchor_min - pd.to_numeric(out["anchor_min_search_ok_frac"], errors="coerce")).clip(lower=0.0)
    out["gate_hard_negative_shortfall"] = (hard_min - pd.to_numeric(out["hard_negative_min_search_ok_frac"], errors="coerce")).clip(lower=0.0)
    out["gate_random_control_excess"] = (pd.to_numeric(out["random_control_search_ok_frac"], errors="coerce") - random_max).clip(lower=0.0)
    out["gate_subset_perm1730_excess"] = (
        pd.to_numeric(out["subset_bw12_perm1730_search_ok_frac"], errors="coerce") - subset_max
    ).clip(lower=0.0)
    return out


def write_doc(
    path: Path,
    *,
    gated: pd.DataFrame,
    by_base: pd.DataFrame,
    by_family: pd.DataFrame,
    outputs: dict[str, Path],
    anchor_min: float,
    hard_min: float,
    random_max: float,
    subset_max: float,
) -> None:
    wc1 = gated[gated["warmup_conflicts"].eq(1)].sort_values(
        ["hard_gate_pass", "gate_violation_count", "strict_selection_score"],
        ascending=[False, True, False],
    )
    wc3 = gated[gated["warmup_conflicts"].eq(3)].sort_values(
        ["hard_gate_pass", "gate_violation_count", "strict_selection_score"],
        ascending=[False, True, False],
    )
    best_wc1 = wc1[wc1["checkpoint"].astype(str).eq("best")]
    iter50_wc1 = wc1[wc1["checkpoint"].astype(str).eq("iter=50")]
    pass_wc1 = wc1[wc1["hard_gate_pass"]]
    pass_all = gated[gated["hard_gate_pass"]]
    random_wc1 = by_family[
        by_family["warmup_conflicts"].eq(1)
        & by_family["family"].astype(str).eq("random_3sat_control")
    ].sort_values(["search_ok_frac", "adapter_cached_decisions_delta_mean"], ascending=[True, True])
    target_wc1 = by_base[
        by_base["warmup_conflicts"].eq(1)
        & by_base["base_instance_id"].astype(str).isin(["k9_color8", "php_p9_h8", "k10_color9", "php_p10_h9"])
    ].sort_values(["base_instance_id", "search_ok_frac"], ascending=[True, False])

    if pass_wc1.empty:
        wc1_conclusion = "No v1.3 checkpoint passes the wc1 hard gates."
    else:
        wc1_conclusion = f"{len(pass_wc1)} v1.3 checkpoint rows pass the wc1 hard gates."
    best_conclusion = "best.pt was not present in wc1 acceptance rows."
    if not best_wc1.empty:
        row = best_wc1.iloc[0]
        failed = [
            name
            for name in [
                "gate_anchor_pass",
                "gate_hard_negative_pass",
                "gate_random_control_pass",
                "gate_subset_perm1730_pass",
                "gate_solved_pass",
                "gate_correctness_pass",
            ]
            if not bool(row[name])
        ]
        best_conclusion = (
            f"`best.pt` wc1 hard gates pass={bool(row['hard_gate_pass'])}; "
            f"failed gates: `{', '.join(failed) if failed else 'none'}`."
        )

    lines = [
        "# EchoSAT Symmetry GRPO v1.3 Checkpoint Selection Mismatch Audit",
        "",
        "This is an offline audit of the v1.3 targeted acceptance outputs. It does not rerun solvers, train a model, expand the benchmark, or add a gate/selector.",
        "",
        "## Artifacts",
        "",
        *[f"- {name}: `{display_path(path)}`" for name, path in outputs.items()],
        "",
        "## Hard Gates",
        "",
        f"- wc1 anchor minimum search_ok fraction: `>= {anchor_min}` for `k9_color8` and `php_p9_h8`.",
        f"- wc1 hard-negative recovery minimum: `>= {hard_min}` for `k10_color9` and `php_p10_h9`.",
        f"- random-control search_ok fraction: `<= {random_max}`.",
        f"- `subset_cardinality_bw12::perm_seed1730` search_ok fraction: `<= {subset_max}`.",
        "- all event-adapter rows must solve.",
        "- known expected rows must match expected labels.",
        "",
        "## Main Finding",
        "",
        f"- {wc1_conclusion}",
        f"- {best_conclusion}",
        "- The online v1.3 best metric was an approximate single-validation score. The offline acceptance protocol is stricter because it uses repeated canonical low-warmup runs and explicit hard gates for anchors, hard negatives, random controls, and the known subset permutation failure.",
        "- Therefore `best.pt` should not be used as the main symmetry checkpoint for the current objective.",
        "",
        "## WC1 Gate Ranking",
        "",
        *markdown_table(
            wc1[
                [
                    "checkpoint",
                    "strict_selection_score",
                    "hard_gate_pass",
                    "gate_violation_count",
                    "anchor_min_search_ok_frac",
                    "hard_negative_min_search_ok_frac",
                    "random_control_search_ok_frac",
                    "subset_bw12_perm1730_search_ok_frac",
                    "overall_search_blowup_frac",
                    "known_expected_rows",
                    "known_expected_match_rows",
                ]
            ],
            max_rows=20,
        ),
        "",
        "## WC3 Diagnostic Ranking",
        "",
        *markdown_table(
            wc3[
                [
                    "checkpoint",
                    "strict_selection_score",
                    "hard_gate_pass",
                    "gate_violation_count",
                    "anchor_min_search_ok_frac",
                    "hard_negative_min_search_ok_frac",
                    "random_control_search_ok_frac",
                    "subset_bw12_perm1730_search_ok_frac",
                    "overall_search_blowup_frac",
                ]
            ],
            max_rows=20,
        ),
        "",
        "## best.pt vs iter=50.pt at WC1",
        "",
        *markdown_table(
            pd.concat([best_wc1, iter50_wc1], ignore_index=True)[
                [
                    "checkpoint",
                    "strict_selection_score",
                    "hard_gate_pass",
                    "gate_violation_count",
                    "gate_anchor_shortfall",
                    "gate_hard_negative_shortfall",
                    "gate_random_control_excess",
                    "gate_subset_perm1730_excess",
                    "overall_adapter_cached_decisions_delta_mean",
                    "overall_adapter_cached_conflicts_delta_mean",
                    "overall_adapter_cached_cpu_delta_mean",
                ]
            ],
            max_rows=10,
        ),
        "",
        "## Target Bases at WC1",
        "",
        *markdown_table(
            target_wc1[
                [
                    "checkpoint",
                    "family",
                    "base_instance_id",
                    "search_ok_frac",
                    "search_blowup_frac",
                    "adapter_cached_decisions_delta_mean",
                    "adapter_cached_conflicts_delta_mean",
                    "adapter_cached_cpu_delta_mean",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Random Controls at WC1",
        "",
        *markdown_table(
            random_wc1[
                [
                    "checkpoint",
                    "search_ok_frac",
                    "search_blowup_frac",
                    "adapter_cached_decisions_delta_mean",
                    "adapter_cached_conflicts_delta_mean",
                    "adapter_cached_cpu_delta_mean",
                ]
            ],
            max_rows=20,
        ),
        "",
        "## Actionable Fix",
        "",
        "- Add a stricter best-checkpoint metric that applies hard gate penalties before saving `best.pt`.",
        "- Require `best_checkpoint_require_gate_pass=true` for v1.4, so a checkpoint that fails anchors, hard-negative recovery, random-control suppression, or the subset failure guard cannot overwrite `best.pt`.",
        "- Continue to treat protocol time and adapter-vs-plain timing as diagnostics only.",
        "- No solver speedup claim follows from this audit.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit v1.3 online best-checkpoint mismatch against targeted acceptance.")
    parser.add_argument("--strict", type=Path, default=ROOT / "runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_strict_acceptance.csv")
    parser.add_argument("--by-base", type=Path, default=ROOT / "runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_summary_by_base.csv")
    parser.add_argument("--by-family", type=Path, default=ROOT / "runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_summary_by_family.csv")
    parser.add_argument("--out-gates", type=Path, default=ROOT / "runs/analysis/echosat_symmetry_grpo_v1_3_checkpoint_selection_mismatch_gates.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/echosat_symmetry_grpo_v1_3_checkpoint_selection_mismatch.md")
    parser.add_argument("--anchor-min", type=float, default=1.0)
    parser.add_argument("--hard-min", type=float, default=2.0 / 3.0)
    parser.add_argument("--random-max", type=float, default=0.05)
    parser.add_argument("--subset-max", type=float, default=0.0)
    parser.add_argument("--no-require-solved", action="store_true")
    parser.add_argument("--no-require-correctness", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    strict = pd.read_csv(resolve(args.strict))
    by_base = pd.read_csv(resolve(args.by_base))
    by_family = pd.read_csv(resolve(args.by_family))
    gated = with_acceptance_gates(
        strict,
        anchor_min=float(args.anchor_min),
        hard_min=float(args.hard_min),
        random_max=float(args.random_max),
        subset_max=float(args.subset_max),
        require_solved=not bool(args.no_require_solved),
        require_correctness=not bool(args.no_require_correctness),
    )
    out_gates = resolve(args.out_gates)
    out_gates.parent.mkdir(parents=True, exist_ok=True)
    gated.to_csv(out_gates, index=False)
    outputs = {"gate audit": out_gates}
    write_doc(
        resolve(args.doc),
        gated=gated,
        by_base=by_base,
        by_family=by_family,
        outputs=outputs,
        anchor_min=float(args.anchor_min),
        hard_min=float(args.hard_min),
        random_max=float(args.random_max),
        subset_max=float(args.subset_max),
    )
    print(f"wrote {out_gates}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
