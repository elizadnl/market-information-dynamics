import numpy as np
import pandas as pd

from market_information_dynamics.statistics.forecast_tests import (
    compare_forecasts_with_fdr,
    diebold_mariano,
)


def test_dm_detects_materially_better_challenger():
    rng = np.random.default_rng(3)
    y = pd.Series(rng.normal(size=400))
    benchmark = y + rng.normal(scale=1.0, size=400)
    challenger = y + rng.normal(scale=0.25, size=400)
    result = diebold_mariano(y, benchmark, challenger, hac_lags=3)
    assert result.mean_loss_difference > 0
    assert result.p_value < 0.01


def test_forecast_comparison_applies_fdr():
    rng = np.random.default_rng(4)
    idx = pd.RangeIndex(300)
    actuals = pd.DataFrame({"a": rng.normal(size=300), "b": rng.normal(size=300)}, index=idx)
    benchmark = actuals + rng.normal(scale=1.0, size=actuals.shape)
    challenger = actuals + rng.normal(scale=0.2, size=actuals.shape)
    out = compare_forecasts_with_fdr(actuals, benchmark, challenger, q=0.10, hac_lags=2)
    assert set(out["variable"]) == {"a", "b"}
    assert out["challenger_better"].all()
    assert out["fdr_reject"].all()
