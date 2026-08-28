import numpy as np
import pandas as pd

from market_information_dynamics.models.residual_overlay import ResidualOverlayForecaster


def test_residual_overlay_recovers_candidate_edge_and_zero_mask_is_zero():
    rng = np.random.default_rng(123)
    n = 260
    p = rng.normal(size=n)
    q = rng.normal(size=n)
    idx = pd.date_range("2020-01-01", periods=n)
    candidates = pd.DataFrame({"physical": p, "noise": q}, index=idx)

    # OOS core residual at origin t depends on candidate information from t-1.
    origins = idx[20:220]
    residual = []
    for d in origins:
        pos = idx.get_loc(d)
        residual.append(0.8 * p[pos - 1] + rng.normal(scale=0.15))
    residuals = pd.DataFrame({"target": residual}, index=origins)

    model = ResidualOverlayForecaster(lags=2, alpha=0.03).fit(candidates.iloc[:230], residuals)
    assert model.adjacency_.loc["physical", "target"] > model.adjacency_.loc["noise", "target"]

    mask = pd.DataFrame(False, index=["physical", "noise"], columns=["target"])
    model.fit_post_selection(mask, ridge_alpha=1.0)
    pred = model.predict_post_selection(candidates.iloc[:230])
    assert pred["target"] == 0.0


def test_edge_effect_is_additive_residual_component():
    rng = np.random.default_rng(9)
    n = 220
    x = rng.normal(size=n)
    idx = pd.date_range("2021-01-01", periods=n)
    candidates = pd.DataFrame({"x": x}, index=idx)
    origins = idx[10:200]
    residuals = pd.DataFrame(
        {"y": [0.6 * x[idx.get_loc(d) - 1] for d in origins]}, index=origins
    )
    model = ResidualOverlayForecaster(lags=1, alpha=0.001).fit(candidates.iloc[:205], residuals)
    full = float(model.predict_next(candidates.iloc[:205])["y"])
    effect = model.predict_edge_effect(candidates.iloc[:205], source="x", target="y")
    assert np.isclose(full, effect)
