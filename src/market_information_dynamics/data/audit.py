from __future__ import annotations

import numpy as np
import pandas as pd


def panel_audit(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Return per-column and panel-level diagnostics before any empirical claim."""
    if frame.empty:
        raise ValueError("cannot audit an empty panel")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("panel index must be a DatetimeIndex")

    rows: list[dict[str, object]] = []
    for col in frame.columns:
        s = pd.to_numeric(frame[col], errors="coerce")
        valid = s.dropna()
        rows.append(
            {
                "variable": col,
                "n": int(valid.size),
                "missing_pct": float(s.isna().mean()),
                "mean": float(valid.mean()) if len(valid) else np.nan,
                "std": float(valid.std(ddof=1)) if len(valid) > 1 else np.nan,
                "min": float(valid.min()) if len(valid) else np.nan,
                "max": float(valid.max()) if len(valid) else np.nan,
                "zero_pct": float((valid == 0).mean()) if len(valid) else np.nan,
            }
        )

    date_diffs = frame.index.to_series().sort_values().diff().dropna().dt.days
    summary: dict[str, object] = {
        "start": str(frame.index.min().date()),
        "end": str(frame.index.max().date()),
        "rows": int(len(frame)),
        "columns": int(frame.shape[1]),
        "complete_rows": int(frame.dropna(how="any").shape[0]),
        "duplicate_dates": int(frame.index.duplicated().sum()),
        "max_calendar_gap_days": int(date_diffs.max()) if len(date_diffs) else 0,
        "median_calendar_gap_days": float(date_diffs.median()) if len(date_diffs) else 0.0,
    }
    return pd.DataFrame(rows).set_index("variable"), summary
