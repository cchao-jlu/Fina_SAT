from __future__ import annotations

import pandas as pd


def select_new_closed_old_on(frame: pd.DataFrame) -> pd.DataFrame:
    """Select rows where the new selector closes cases the old selector opened."""
    if "decision_change" not in frame.columns:
        raise KeyError("decision_change")
    return frame[frame["decision_change"].astype(str).eq("new_closed_old_on")].copy()


def add_local_boundary_labels(frame: pd.DataFrame) -> pd.DataFrame:
    """Label local boundary cases where the old adapter should be reopened."""
    out = frame.copy()
    labels = []
    reasons = []
    for _, row in out.iterrows():
        old_solved = bool(row.get("old_solved", False))
        new_solved = bool(row.get("new_solved", False))
        delta = pd.to_numeric(pd.Series([row.get("delta_time_vs_old", 0.0)]), errors="coerce").fillna(0.0).iloc[0]
        reopen = old_solved and ((not new_solved) or float(delta) > 0.0)
        labels.append(1 if reopen else 0)
        reasons.append("reopen_old_adapter" if reopen else "keep_closed")
    out["local_closed_old_label"] = labels
    out["local_closed_old_reason"] = reasons
    return out
