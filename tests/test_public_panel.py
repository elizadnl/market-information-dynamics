import pandas as pd

from market_information_dynamics.data.public_panel import combine_financial_and_physical


def test_public_panel_respects_physical_availability():
    dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"])
    financial = pd.DataFrame({"audusd": [0.1, 0.2, -0.1, 0.3]}, index=dates)
    releases = pd.DataFrame(
        {
            "feature": ["pw_suez_capacity_z", "pw_suez_capacity_z"],
            "available_at": pd.to_datetime(["2026-01-02", "2026-01-04"]),
            "value": [1.0, 2.0],
        }
    )

    panel = combine_financial_and_physical(financial, releases, drop_incomplete=False)
    assert pd.isna(panel.loc[pd.Timestamp("2026-01-01"), "pw_suez_capacity_z"])
    assert panel.loc[pd.Timestamp("2026-01-03"), "pw_suez_capacity_z"] == 1.0
    assert panel.loc[pd.Timestamp("2026-01-04"), "pw_suez_capacity_z"] == 2.0
