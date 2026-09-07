from __future__ import annotations

import numpy as np
import pandas as pd


def generate_regime_switching_system(n_obs: int = 1800, seed: int = 7) -> pd.DataFrame:
    """Generate a known directed system whose predictive graph changes mid-sample.

    The synthetic system is intentionally interpretable. It lets us verify that the
    research pipeline can recover signal direction and detect edge decay before we
    trust it on real markets, where ground truth is unknown.
    """
    if n_obs < 200:
        raise ValueError("n_obs must be at least 200")

    rng = np.random.default_rng(seed)
    names = ["physical", "commodity", "fx", "equity", "rates", "vol"]
    x = np.zeros((n_obs, len(names)), dtype=float)
    eps = rng.normal(size=x.shape)
    switch = n_obs // 2

    for t in range(3, n_obs):
        physical, commodity, fx, equity, rates, vol = x[t - 1]

        # Persistent physical activity.
        x[t, 0] = 0.62 * physical + 0.80 * eps[t, 0]

        # Regime 1: physical activity strongly leads commodity prices.
        # Regime 2: that edge largely dies.
        physical_to_commodity = 0.55 if t < switch else 0.08
        x[t, 1] = (
            0.22 * commodity
            + physical_to_commodity * physical
            + 0.85 * eps[t, 1]
        )

        # FX is partly driven by commodity information; the edge strengthens after switch.
        commodity_to_fx = 0.27 if t < switch else 0.52
        x[t, 2] = (
            0.18 * fx
            + commodity_to_fx * commodity
            + 0.12 * x[t - 2, 0]
            + 0.90 * eps[t, 2]
        )

        # Equity reacts later to FX plus its own persistence.
        x[t, 3] = 0.19 * equity + 0.35 * fx + 0.95 * eps[t, 3]

        # Rates react weakly to lagged commodity information.
        x[t, 4] = 0.30 * rates + 0.16 * x[t - 2, 1] + 0.90 * eps[t, 4]

        # Volatility responds inversely to equity and is persistent.
        x[t, 5] = 0.42 * vol - 0.24 * equity + 0.85 * eps[t, 5]

    idx = pd.bdate_range("2019-01-02", periods=n_obs)
    out = pd.DataFrame(x, index=idx, columns=names)
    out.index.name = "date"
    return out.iloc[10:].copy()
