import numpy as np
import pandas as pd

from market_information_dynamics.online.fixed_share import fixed_share_forecast


def _frames(n=300):
    idx = pd.bdate_range("2024-01-01", periods=n)
    rng = np.random.default_rng(1)
    y = rng.normal(size=n)
    actuals = pd.DataFrame({"x": y}, index=idx)
    core = pd.DataFrame({"x": y + rng.normal(scale=0.7, size=n)}, index=idx)
    candidate = pd.DataFrame({"x": y + rng.normal(scale=0.4, size=n)}, index=idx)
    return actuals, core, candidate


def test_fixed_share_weights_are_probabilities():
    actuals, core, candidate = _frames()
    result = fixed_share_forecast(
        actuals,
        {"core": core, "candidate": candidate},
        horizon=5,
    )
    pivot = result.weights.pivot_table(
        index=["date", "target"], columns="expert", values="weight", aggfunc="last"
    )
    assert np.allclose(pivot.sum(axis=1).to_numpy(), 1.0)
    assert (pivot.to_numpy() >= 0).all()


def test_future_outcome_cannot_change_pre_realisation_weights():
    actuals, core, candidate = _frames(n=120)
    base = fixed_share_forecast(
        actuals,
        {"core": core, "candidate": candidate},
        horizon=10,
    )
    changed = actuals.copy()
    # Change an outcome whose forecast origin is row 80. It cannot influence weights until
    # row 90 because the ten-step outcome has not fully realised before then.
    changed.iloc[80, 0] += 1000.0
    alt = fixed_share_forecast(
        changed,
        {"core": core, "candidate": candidate},
        horizon=10,
    )
    cutoff = actuals.index[89]
    a = base.weights.loc[pd.to_datetime(base.weights["date"]) <= cutoff, "weight"].to_numpy()
    b = alt.weights.loc[pd.to_datetime(alt.weights["date"]) <= cutoff, "weight"].to_numpy()
    assert np.allclose(a, b)


def test_fixed_share_recovers_after_candidate_signal_dies():
    rng = np.random.default_rng(2)
    n = 800
    idx = pd.bdate_range("2022-01-03", periods=n)
    y = rng.normal(size=n)
    core = y + rng.normal(scale=0.7, size=n)
    candidate = y + rng.normal(scale=0.35, size=n)
    candidate[400:] = y[400:] + rng.normal(scale=1.4, size=n - 400)
    result = fixed_share_forecast(
        pd.DataFrame({"x": y}, index=idx),
        {
            "core": pd.DataFrame({"x": core}, index=idx),
            "candidate": pd.DataFrame({"x": candidate}, index=idx),
        },
        horizon=5,
        share=1 / 252,
    )
    w = result.weights
    cand = w.loc[w["expert"] == "candidate"].set_index("date")["weight"]
    early = cand.iloc[300:380].mean()
    late = cand.iloc[-80:].mean()
    assert early > 0.6
    assert late < 0.4
