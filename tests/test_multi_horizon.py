import numpy as np
import pandas as pd

from market_information_dynamics.evaluation.multi_horizon import walk_forward_signal_survival


def _panel(n=260):
    rng = np.random.default_rng(12)
    x = rng.normal(scale=0.5, size=n)
    y = np.zeros(n)
    p = rng.normal(scale=0.3, size=n)
    for t in range(1, n):
        y[t] = 0.5 * x[t - 1] + 0.15 * y[t - 1] + rng.normal(scale=0.4)
    return pd.DataFrame(
        {"x": x, "y": y, "p": p}, index=pd.date_range("2020-01-01", periods=n)
    )


def test_multi_horizon_walk_forward_outputs_are_aligned():
    frame = _panel()
    result = walk_forward_signal_survival(
        frame,
        financial_columns=["x", "y"],
        target_columns=["y"],
        horizon=5,
        lags=3,
        alpha=0.03,
        min_train=120,
        refit_every=20,
        ar_alpha=1.0,
        ridge_alpha=1.0,
        edge_threshold=0.03,
        structural_half_life_days=180,
        contribution_half_life_days=90,
        min_selection_frequency=0.4,
        min_sign_stability=0.5,
        min_strength_retention=0.3,
        min_contributions=5,
        min_survival_snapshots=3,
        max_edges_per_target=4,
    )
    expected = len(frame) - 5 - 120 + 1
    assert len(result.actuals) == expected
    for pred in result.predictions.values():
        assert pred.index.equals(result.actuals.index)
    assert set(result.edge_contributions.columns) >= {
        "origin_date",
        "realized_date",
        "source",
        "target",
        "loss_improvement",
    }
