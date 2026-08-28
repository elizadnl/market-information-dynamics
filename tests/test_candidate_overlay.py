import numpy as np
import pandas as pd

from market_information_dynamics.evaluation.candidate_overlay import walk_forward_candidate_overlay


def test_candidate_overlay_walk_forward_preserves_core_until_oos_residual_history_exists():
    rng = np.random.default_rng(44)
    n = 260
    x = rng.normal(scale=0.5, size=n)
    p = rng.normal(scale=0.5, size=n)
    y = np.zeros(n)
    for t in range(2, n):
        y[t] = 0.35 * x[t - 1] + 0.45 * p[t - 1] + rng.normal(scale=0.35)
    frame = pd.DataFrame(
        {"x": x, "y": y, "physical": p},
        index=pd.date_range("2020-01-01", periods=n),
    )
    result = walk_forward_candidate_overlay(
        frame,
        financial_columns=["x", "y"],
        candidate_columns=["physical"],
        target_columns=["y"],
        horizon=1,
        lags=2,
        alpha=0.03,
        min_train=100,
        refit_every=10,
        ar_alpha=1.0,
        overlay_alpha=0.03,
        overlay_min_train=35,
        overlay_ridge_alpha=1.0,
        edge_threshold=0.02,
        structural_half_life_days=90,
        contribution_half_life_days=60,
        min_selection_frequency=0.3,
        min_sign_stability=0.5,
        min_strength_retention=0.2,
        min_contributions=5,
        min_survival_snapshots=2,
        max_edges_per_target=2,
        gate_half_life_days=60,
        gate_min_observations=10,
        gate_t_scale=2.0,
    )
    assert set(result.predictions) == {
        "ar",
        "financial_direct_sparse",
        "candidate_overlay_sparse",
        "candidate_overlay_survival",
        "candidate_overlay_adaptive",
    }
    for pred in result.predictions.values():
        assert pred.index.equals(result.actuals.index)
    assert not result.core_residuals.empty
    assert set(result.overlay_edge_contributions.columns) >= {
        "source",
        "target",
        "loss_improvement",
    }
    assert not result.gate_history.empty
