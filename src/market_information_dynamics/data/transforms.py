from __future__ import annotations

import numpy as np
import pandas as pd


def transform_series(series: pd.Series, transform: str) -> pd.Series:
    """Apply a named transformation while preserving the original index."""
    s = pd.to_numeric(series, errors="coerce").astype(float)
    if transform == "level":
        out = s
    elif transform == "difference":
        out = s.diff()
    elif transform == "log_return":
        if (s.dropna() <= 0).any():
            raise ValueError("log_return requires strictly positive observations")
        out = np.log(s).diff()
    elif transform == "negative_log_return":
        if (s.dropna() <= 0).any():
            raise ValueError("negative_log_return requires strictly positive observations")
        out = -np.log(s).diff()
    elif transform == "pct_change":
        out = s.pct_change(fill_method=None)
    else:
        raise ValueError(f"Unknown transform: {transform}")
    return out.rename(series.name)
