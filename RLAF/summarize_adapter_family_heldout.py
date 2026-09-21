from __future__ import annotations

import argparse
from pathlib import Path

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


def summarize_by_eval_family(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (heldout, family, split), group in frame.groupby(["heldout_family", "family", "adapter_train_split"], sort=True):
        valid = valid_rows(group)
        positive = group[truthy_series(group, "event_identity_positive", default=False)].copy()
        rows.append(
            {
                "heldout_family": heldout,
                "eval_family": family,
                "adapter_train_split": split,
                "instances": int(group["instance_id"].nunique()),
                "orbit_rows": int(len(group)),
                "valid_rollout_rows": int(len(valid)),
                "event_positive_rows": int(len(positive)),
                "zero_identity_rows": int(truthy_series(group, "event_identity_zero", default=False).sum()),
                "mean_static_mu_range_valid": float(valid["static_mu_range"].mean()) if not valid.empty else float("nan"),
                "mean_event_l2_valid": float(valid["event_feature_l2_range"].mean()) if not valid.empty else float("nan"),
                "mean_adapted_mu_range_valid": float(valid["adapted_mu_range"].mean()) if not valid.empty else float("nan"),
                "max_adapted_mu_range_valid": float(valid["adapted_mu_range"].max()) if not valid.empty else float("nan"),
                "mean_adapter_gain_valid": float(valid["adapter_identity_gain"].mean()) if not valid.empty else float("nan"),
                "max_adapter_gain_valid": float(valid["adapter_identity_gain"].max()) if not valid.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def summarize_leave_one_out(frame: pd.DataFrame, baseline: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    baseline_by_family: dict[str, float] = {}
    if baseline is not None and not baseline.empty and "family" in baseline.columns:
        base_valid = valid_rows(baseline)
        baseline_by_family = {
            str(family): float(group["adapter_identity_gain"].mean())
            for family, group in base_valid.groupby("family", sort=True)
            if "adapter_identity_gain" in group.columns and not group.empty
        }
    for heldout, group in frame.groupby("heldout_family", sort=True):
        valid = valid_rows(group)
        all_train = group[group["adapter_train_split"].astype(str) == "train"]
        all_held = group[group["adapter_train_split"].astype(str) == "heldout"]
        train = valid[valid["adapter_train_split"].astype(str) == "train"]
        held = valid[valid["adapter_train_split"].astype(str) == "heldout"]
        train_gain = float(train["adapter_identity_gain"].mean()) if not train.empty else float("nan")
        held_gain = float(held["adapter_identity_gain"].mean()) if not held.empty else float("nan")
        train_range = float(train["adapted_mu_range"].mean()) if not train.empty else float("nan")
        held_range = float(held["adapted_mu_range"].mean()) if not held.empty else float("nan")
        base_gain = baseline_by_family.get(str(heldout), float("nan"))
        rows.append(
            {
                "heldout_family": heldout,
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
                "train_mean_adapted_mu_range_valid": train_range,
                "heldout_mean_adapted_mu_range_valid": held_range,
                "heldout_minus_train_adapted_mu_range": held_range - train_range,
                "full_adapter_mean_gain_for_heldout_family": base_gain,
                "heldout_minus_full_adapter_gain": held_gain - base_gain,
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
                values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_doc(path: Path, by_family: pd.DataFrame, leave_one_out: pd.DataFrame, inputs: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Adapter Family-Heldout Audit",
        "",
        "This is a representation-only leave-one-family-out audit. Each adapter",
        "checkpoint is trained on cached event traces from all event-role",
        "families except one, then evaluated on the same cached event-state",
        "audit set. No solver speedup or runtime claim is made here.",
        "",
        "## Leave-One-Family-Out Summary",
        "",
        *markdown_table(leave_one_out),
        "",
        "## Evaluation Family Matrix",
        "",
        *markdown_table(by_family, max_rows=120),
        "",
        "## Inputs",
        "",
        *[f"- `{path}`" for path in inputs],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize leave-one-family-out adapter symmetry audits.")
    parser.add_argument("--input-csv", type=Path, action="append", required=True)
    parser.add_argument("--baseline-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_event_orbits.csv")
    parser.add_argument("--output-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_family_heldout_by_family.csv")
    parser.add_argument("--summary-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_family_heldout_summary.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_adapter_family_heldout_audit.md")
    args = parser.parse_args()

    frames = [pd.read_csv(path) for path in args.input_csv]
    frame = pd.concat(frames, ignore_index=True)
    baseline = pd.read_csv(args.baseline_csv) if args.baseline_csv.exists() else None
    by_family = summarize_by_eval_family(frame)
    leave_one_out = summarize_leave_one_out(frame, baseline=baseline)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    by_family.to_csv(args.output_csv, index=False)
    args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
    leave_one_out.to_csv(args.summary_csv, index=False)
    write_doc(args.doc, by_family=by_family, leave_one_out=leave_one_out, inputs=args.input_csv)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.summary_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
