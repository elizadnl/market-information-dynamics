from __future__ import annotations

import pandas as pd

from market_information_dynamics.data.point_in_time import build_point_in_time_panel


def combine_financial_and_physical(
    financial_panel: pd.DataFrame,
    physical_releases: pd.DataFrame,
    *,
    drop_incomplete: bool = True,
) -> pd.DataFrame:
    """Align market-date financial features with availability-aware physical features."""
    if financial_panel.empty:
        raise ValueError("financial_panel is empty")
    evaluation_times = pd.DatetimeIndex(financial_panel.index).sort_values()
    physical = build_point_in_time_panel(evaluation_times, physical_releases)
    combined = financial_panel.reindex(evaluation_times).join(physical, how="left")
    if drop_incomplete:
        combined = combined.dropna(how="any")
    return combined
