from __future__ import annotations

import numpy as np
import pandas as pd


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def feature_distribution_summary(
    train: pd.DataFrame,
    online: pd.DataFrame,
    feature_names: list[str],
) -> pd.DataFrame:
    rows = []
    for name in feature_names:
        train_values = _numeric(train, name).dropna()
        online_values = _numeric(online, name).dropna()
        train_mean = float(train_values.mean()) if len(train_values) else np.nan
        online_mean = float(online_values.mean()) if len(online_values) else np.nan
        train_std = float(train_values.std(ddof=0)) if len(train_values) else 0.0
        p05 = float(train_values.quantile(0.05)) if len(train_values) else np.nan
        p95 = float(train_values.quantile(0.95)) if len(train_values) else np.nan
        outside = int(((online_values < p05) | (online_values > p95)).sum()) if len(online_values) else 0
        mean_shift_z = 0.0 if train_std <= 0.0 or np.isnan(online_mean) else float((online_mean - train_mean) / train_std)
        rows.append(
            {
                "feature": name,
                "train_mean": train_mean,
                "online_mean": online_mean,
                "train_std": train_std,
                "train_p05": p05,
                "train_p95": p95,
                "online_outside_p05_p95": outside,
                "mean_shift_z": mean_shift_z,
            }
        )
    return pd.DataFrame(rows)


def policy_outcome_label(base_solved: bool, selected_solved: bool) -> str:
    if base_solved and not selected_solved:
        return "lost_solution"
    if not base_solved and selected_solved:
        return "recovered_timeout"
    if base_solved and selected_solved:
        return "kept_solved"
    return "kept_timeout"


def instance_feature_audit(
    train: pd.DataFrame,
    online: pd.DataFrame,
    feature_names: list[str],
) -> pd.DataFrame:
    stats = {}
    for name in feature_names:
        values = _numeric(train, name).dropna()
        mean = float(values.mean()) if len(values) else 0.0
        std = float(values.std(ddof=0)) if len(values) else 0.0
        stats[name] = (mean, std)

    rows = []
    for _, row in online.iterrows():
        z_by_feature = {}
        for name in feature_names:
            value = pd.to_numeric(pd.Series([row.get(name)]), errors="coerce").iloc[0]
            mean, std = stats[name]
            z_by_feature[name] = 0.0 if std <= 0.0 or pd.isna(value) else float((float(value) - mean) / std)
        max_feature = max(feature_names, key=lambda item: abs(z_by_feature[item])) if feature_names else ""
        rows.append(
            {
                **row.to_dict(),
                "outcome_group": policy_outcome_label(bool(row.get("base_solved")), bool(row.get("selected_solved"))),
                "max_abs_train_z": abs(z_by_feature[max_feature]) if max_feature else 0.0,
                "max_abs_feature": max_feature,
            }
        )
    return pd.DataFrame(rows)
