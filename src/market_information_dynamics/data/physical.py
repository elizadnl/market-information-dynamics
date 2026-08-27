from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def load_physical_csv(
    path: str | Path,
    date_col: str,
    value_cols: Iterable[str],
    *,
    resample: str | None = None,
    agg: str = "sum",
) -> pd.DataFrame:
    """Load a public physical-economy export (e.g. PortWatch download).

    Column names are supplied explicitly instead of being hard-coded because public
    portal exports can change schema. This keeps data provenance visible in config.
    """
    frame = pd.read_csv(path)
    if date_col not in frame.columns:
        raise KeyError(f"Missing date column: {date_col}")
    value_cols = list(value_cols)
    missing = [c for c in value_cols if c not in frame.columns]
    if missing:
        raise KeyError(f"Missing value columns: {missing}")

    frame[date_col] = pd.to_datetime(frame[date_col], errors="raise")
    out = frame.set_index(date_col)[value_cols].apply(pd.to_numeric, errors="coerce")
    out = out.sort_index()
    if resample:
        sampler = out.resample(resample)
        if agg == "sum":
            out = sampler.sum(min_count=1)
        elif agg == "mean":
            out = sampler.mean()
        else:
            raise ValueError("agg must be 'sum' or 'mean'")
    return out
