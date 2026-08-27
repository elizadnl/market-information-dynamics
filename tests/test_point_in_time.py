import pandas as pd

from market_information_dynamics.data.point_in_time import build_point_in_time_panel


def test_point_in_time_uses_only_available_information():
    releases = pd.DataFrame(
        {
            "feature": ["macro", "macro", "macro"],
            "available_at": ["2026-01-05", "2026-02-05", "2026-03-05"],
            "value": [1.0, 2.0, 3.0],
        }
    )
    times = pd.to_datetime(["2026-01-04", "2026-01-10", "2026-02-01", "2026-02-10"])
    panel = build_point_in_time_panel(times, releases)
    assert pd.isna(panel.loc[pd.Timestamp("2026-01-04"), "macro"])
    assert panel.loc[pd.Timestamp("2026-01-10"), "macro"] == 1.0
    assert panel.loc[pd.Timestamp("2026-02-01"), "macro"] == 1.0
    assert panel.loc[pd.Timestamp("2026-02-10"), "macro"] == 2.0
