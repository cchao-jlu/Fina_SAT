from __future__ import annotations

import pandas as pd


def normalise_size_column(frame: pd.DataFrame) -> pd.Series:
    """Return the instance size column as nullable integer values."""
    if "size" not in frame.columns:
        raise KeyError("size")
    return pd.to_numeric(frame["size"], errors="coerce").astype("Int64")
