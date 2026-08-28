import pandas as pd

from market_information_dynamics.statistics.signal_survival import (
    edge_survival_table,
    survival_mask,
)


def test_recent_oos_harm_kills_old_stable_edge():
    dates = pd.to_datetime(["2025-01-01", "2025-03-01", "2025-05-01", "2025-07-01"])
    snapshots = pd.DataFrame(
        {
            "date": dates,
            "source": ["x"] * 4,
            "target": ["y"] * 4,
            "strength": [0.20, 0.20, 0.18, 0.17],
            "signed_weight": [0.20, 0.20, 0.18, 0.17],
        }
    )
    contributions = pd.DataFrame(
        {
            "origin_date": pd.to_datetime(["2025-01-10", "2025-03-10", "2025-06-10", "2025-07-10"]),
            "realized_date": pd.to_datetime(["2025-01-11", "2025-03-11", "2025-06-11", "2025-07-11"]),
            "source": ["x"] * 4,
            "target": ["y"] * 4,
            "loss_improvement": [0.5, 0.4, -1.0, -1.2],
        }
    )
    table = edge_survival_table(
        snapshots,
        contributions,
        as_of=pd.Timestamp("2025-08-01"),
        structural_half_life_days=180,
        contribution_half_life_days=30,
    )
    row = table.iloc[0]
    assert row.weighted_selection_frequency > 0.9
    assert row.weighted_mean_loss_improvement < 0
    mask = survival_mask(
        table,
        sources=["x", "y"],
        targets=["y"],
        min_selection_frequency=0.5,
        min_sign_stability=0.6,
        min_strength_retention=0.5,
        min_contributions=2,
    )
    assert not bool(mask.loc["x", "y"])
    assert bool(mask.loc["y", "y"])


def test_positive_recent_contribution_survives():
    snapshots = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
            "source": ["x"] * 3,
            "target": ["y"] * 3,
            "strength": [0.15, 0.16, 0.17],
            "signed_weight": [0.15, 0.16, 0.17],
        }
    )
    contributions = pd.DataFrame(
        {
            "origin_date": pd.to_datetime(["2025-02-02", "2025-02-10", "2025-03-02"]),
            "realized_date": pd.to_datetime(["2025-02-03", "2025-02-11", "2025-03-03"]),
            "source": ["x"] * 3,
            "target": ["y"] * 3,
            "loss_improvement": [0.1, 0.2, 0.3],
        }
    )
    table = edge_survival_table(snapshots, contributions, as_of=pd.Timestamp("2025-03-10"))
    assert table.iloc[0].survival_score > 0
