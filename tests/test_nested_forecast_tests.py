from types import SimpleNamespace

import numpy as np
import pandas as pd

from market_information_dynamics.statistics.nested_forecast_tests import nested_forecast_tests


def test_nested_tests_use_horizon_aware_hac():
    rng = np.random.default_rng(2)
    idx = pd.date_range("2025-01-01", periods=120)
    y = pd.DataFrame({"x": rng.normal(size=len(idx))}, index=idx)
    bad = pd.DataFrame({"x": y["x"] + rng.normal(scale=1.0, size=len(idx))}, index=idx)
    good = pd.DataFrame({"x": y["x"] + rng.normal(scale=0.2, size=len(idx))}, index=idx)
    results = {10: SimpleNamespace(actuals=y, predictions={"bad": bad, "good": good})}
    out = nested_forecast_tests(
        results,
        comparisons=[("bad", "good")],
        base_hac_lags=5,
        evaluation_start="2025-01-01",
    )
    assert int(out.iloc[0].hac_lags) == 9
    assert bool(out.iloc[0].challenger_better)
