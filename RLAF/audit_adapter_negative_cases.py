from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent


def bool_series(frame: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=bool)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(default).astype(bool)
    normalized = values.fillna(str(default)).astype(str).str.strip().str.lower()
    return normalized.isin({"1", "true", "yes", "y"})


def numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default)


def label_negative_cases(frame: pd.DataFrame, event_eps: float, adapter_eps: float) -> pd.DataFrame:
    frame = frame.copy()
    event_l2 = numeric(frame, "event_feature_l2_range")
    adapted_mu = numeric(frame, "adapted_mu_range")
    static_mu = numeric(frame, "static_mu_range")
    audit_status = frame.get("audit_status", pd.Series("", index=frame.index)).fillna("").astype(str)
    valid_reason = frame.get("event_row_valid_reason", pd.Series("", index=frame.index)).fillna("").astype(str)
    event_valid = bool_series(frame, "event_row_valid", default=False)
    orbit_valid = bool_series(frame, "orbit_valid", default=True)
    frame["negative_case_type"] = "not_negative_case"
    frame.loc[event_valid & (event_l2 <= float(event_eps)), "negative_case_type"] = "valid_zero_identity"
    frame.loc[orbit_valid & (valid_reason == "no_solver_activity") & (event_l2 <= float(event_eps)), "negative_case_type"] = "no_activity_zero_event"
    frame.loc[orbit_valid & (valid_reason == "no_solver_activity") & (event_l2 > float(event_eps)), "negative_case_type"] = "no_activity_event_nonzero"
    frame.loc[orbit_valid & (audit_status == "missing_events"), "negative_case_type"] = "missing_events"
    frame["adapter_negative_violation"] = (
        frame["negative_case_type"].astype(str) != "not_negative_case"
    ) & (adapted_mu > float(adapter_eps))
    frame["adapter_negative_violation_eps"] = float(adapter_eps)
    frame["event_identity_eps"] = float(event_eps)
    frame["adapter_minus_static_mu_range"] = adapted_mu - static_mu
    return frame


def negative_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["negative_case_type"].astype(str) != "not_negative_case"].copy()


def summarize_negative(frame: pd.DataFrame) -> pd.DataFrame:
    negative = negative_rows(frame)
    if negative.empty:
        return pd.DataFrame()
    return (
        negative.groupby(["negative_case_type", "family"], sort=True)
        .agg(
            rows=("orbit", "count"),
            instances=("instance_id", "nunique"),
            mean_event_l2=("event_feature_l2_range", "mean"),
            max_event_l2=("event_feature_l2_range", "max"),
            mean_static_mu_range=("static_mu_range", "mean"),
            mean_adapted_mu_range=("adapted_mu_range", "mean"),
            max_adapted_mu_range=("adapted_mu_range", "max"),
            mean_adapter_minus_static_mu_range=("adapter_minus_static_mu_range", "mean"),
            violation_rows=("adapter_negative_violation", lambda values: int(pd.Series(values).astype(bool).sum())),
        )
        .reset_index()
    )


def summarize_overall(frame: pd.DataFrame) -> pd.DataFrame:
    negative = negative_rows(frame)
    if negative.empty:
        return pd.DataFrame()
    return (
        negative.groupby("negative_case_type", sort=True)
        .agg(
            rows=("orbit", "count"),
            families=("family", "nunique"),
            instances=("instance_id", "nunique"),
            mean_event_l2=("event_feature_l2_range", "mean"),
            max_event_l2=("event_feature_l2_range", "max"),
            mean_adapted_mu_range=("adapted_mu_range", "mean"),
            max_adapted_mu_range=("adapted_mu_range", "max"),
            violation_rows=("adapter_negative_violation", lambda values: int(pd.Series(values).astype(bool).sum())),
        )
        .reset_index()
    )


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


def write_doc(path: Path, labelled: pd.DataFrame, source_csv: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    overall = summarize_overall(labelled)
    family = summarize_negative(labelled)
    worst = negative_rows(labelled).sort_values("adapted_mu_range", ascending=False)
    lines = [
        "# Adapter Negative-Case Audit",
        "",
        f"- source orbit CSV: `{source_csv}`",
        "",
        "This audit checks whether the event adapter creates output separation",
        "on negative cases where it should ideally stay close to static output:",
        "valid zero-identity rows, no-solver-activity rows, and missing-events",
        "rows. It is a representation guardrail, not a solver speedup claim.",
        "",
        "`no_activity_event_nonzero` is separated from `no_activity_zero_event`",
        "because enhanced event features can contain propagation/assignment",
        "signals even when decisions and conflicts are zero.",
        "",
        "## Overall",
        "",
        *markdown_table(overall),
        "",
        "## Family Breakdown",
        "",
        *markdown_table(family),
        "",
        "## Largest Negative Adapter Ranges",
        "",
        *markdown_table(
            worst[
                [
                    column
                    for column in [
                        "negative_case_type",
                        "family",
                        "instance_id",
                        "variant",
                        "orbit",
                        "orbit_size",
                        "event_feature_l2_range",
                        "static_mu_range",
                        "adapted_mu_range",
                        "adapter_negative_violation",
                    ]
                    if column in worst.columns
                ]
            ],
            max_rows=30,
        ),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit adapter behavior on zero/no-activity negative event cases.")
    parser.add_argument("--orbits-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_event_orbits.csv")
    parser.add_argument("--output-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_negative_cases.csv")
    parser.add_argument("--summary-csv", type=Path, default=ROOT / "runs/analysis/symmetry_adapter_negative_case_summary.csv")
    parser.add_argument("--doc", type=Path, default=ROOT / "docs/symmetry_adapter_negative_case_audit.md")
    parser.add_argument("--event-identity-eps", type=float, default=1.0e-6)
    parser.add_argument("--adapter-violation-eps", type=float, default=1.0e-4)
    args = parser.parse_args()

    frame = pd.read_csv(args.orbits_csv)
    labelled = label_negative_cases(
        frame,
        event_eps=float(args.event_identity_eps),
        adapter_eps=float(args.adapter_violation_eps),
    )
    negative = negative_rows(labelled)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    negative.to_csv(args.output_csv, index=False)
    summary = summarize_negative(labelled)
    args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_csv, index=False)
    write_doc(args.doc, labelled=labelled, source_csv=args.orbits_csv)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.summary_csv}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
