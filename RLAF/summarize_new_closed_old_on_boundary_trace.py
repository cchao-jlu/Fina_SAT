from __future__ import annotations

from pathlib import Path

import pandas as pd


FEATURE_COLUMNS = [
    "new_risk_prob",
    "new_recovery_prob",
    "new_slowdown_prob",
]


def _file_key(value: object) -> str:
    return Path(str(value)).name


def merge_manifest_and_trace(manifest: pd.DataFrame, trace: pd.DataFrame) -> pd.DataFrame:
    manifest_frame = manifest.copy()
    trace_frame = trace.copy()
    if "file_key" not in manifest_frame.columns:
        if "file" not in manifest_frame.columns:
            raise KeyError("file_key")
        manifest_frame["file_key"] = manifest_frame["file"].map(_file_key)
    if "file_key" not in trace_frame.columns:
        if "file" not in trace_frame.columns:
            raise KeyError("file")
        trace_frame["file_key"] = trace_frame["file"].map(_file_key)
    return manifest_frame.merge(trace_frame, on="file_key", how="left", suffixes=("", "_trace"))


def local_reopen_labels(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    labels = []
    reasons = []
    for _, row in out.iterrows():
        cls = str(row.get("counterfactual_class", ""))
        base_result = str(row.get("base_result", ""))
        adapter_result = str(row.get("adapter_result", ""))
        reopen = cls == "positive" or (
            base_result not in {"SATISFIABLE", "UNSATISFIABLE"}
            and adapter_result in {"SATISFIABLE", "UNSATISFIABLE"}
        )
        if reopen:
            labels.append(1)
            reasons.append("reopen_by_current_trace")
        elif cls == "negative":
            labels.append(0)
            reasons.append("keep_closed_by_current_trace")
        else:
            labels.append(pd.NA)
            reasons.append("neutral")
    out["trace_reopen_label"] = labels
    out["trace_reopen_reason"] = reasons
    return out


def build_summary(frame: pd.DataFrame) -> pd.DataFrame:
    classes = frame.get("counterfactual_class", pd.Series(dtype=object)).astype(str)
    counts = classes.value_counts()
    return pd.DataFrame(
        [
            {
                "positive": int(counts.get("positive", 0)),
                "negative": int(counts.get("negative", 0)),
                "neutral": int(counts.get("neutral", 0)),
                "total": int(len(frame)),
            }
        ]
    )


def build_focus_frame(frame: pd.DataFrame, focus_keys: list[str]) -> pd.DataFrame:
    order = {key: idx for idx, key in enumerate(focus_keys)}
    focus = frame[frame["file_key"].isin(focus_keys)].copy()
    focus["_focus_order"] = focus["file_key"].map(order)
    focus = focus.sort_values("_focus_order").drop(columns=["_focus_order"])

    def profile(row: pd.Series) -> str:
        parts = []
        for name in FEATURE_COLUMNS:
            if name in row:
                parts.append(f"{name}={row[name]}")
        return "; ".join(parts)

    focus["feature_profile"] = focus.apply(profile, axis=1)
    return focus
