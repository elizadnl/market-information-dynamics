import numpy as np
import pandas as pd

from market_information_dynamics.models.direct_sparse import DirectSparseForecaster


def _panel(n: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    x = rng.normal(size=n)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = 0.75 * x[t - 1] + 0.10 * y[t - 1] + rng.normal(scale=0.35)
    return pd.DataFrame({"x": x, "y": y}, index=pd.date_range("2020-01-01", periods=n))


def test_direct_sparse_recovers_predictive_edge():
    frame = _panel()
    model = DirectSparseForecaster(lags=2, horizon=1, alpha=0.02).fit(
        frame.iloc[:400], target_columns=["y"]
    )
    assert model.adjacency_.loc["x", "y"] > model.adjacency_.loc["y", "y"]


def test_direct_sparse_future_changes_do_not_affect_prediction():
    frame = _panel()
    history = frame.iloc[:350].copy()
    model_a = DirectSparseForecaster(lags=3, horizon=5, alpha=0.03).fit(
        history, target_columns=["y"]
    )
    pred_a = model_a.predict_next(history)["y"]

    changed = frame.copy()
    changed.iloc[350:, :] = 9999.0
    history_changed = changed.iloc[:350]
    model_b = DirectSparseForecaster(lags=3, horizon=5, alpha=0.03).fit(
        history_changed, target_columns=["y"]
    )
    pred_b = model_b.predict_next(history_changed)["y"]
    assert np.isclose(pred_a, pred_b)


def test_post_selection_refit_respects_mask():
    frame = _panel()
    model = DirectSparseForecaster(lags=2, horizon=1, alpha=0.02).fit(
        frame.iloc[:400], target_columns=["y"]
    )
    mask = pd.DataFrame(False, index=["x", "y"], columns=["y"])
    mask.loc["y", "y"] = True
    model.fit_post_selection(mask, ridge_alpha=1.0)
    pred = model.predict_post_selection(frame.iloc[:400])
    assert np.isfinite(pred["y"])
