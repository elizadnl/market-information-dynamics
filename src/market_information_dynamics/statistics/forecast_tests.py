from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm

from market_information_dynamics.statistics.fdr import benjamini_hochberg


@dataclass(frozen=True)
class DMResult:
    statistic: float
    p_value: float
    mean_loss_difference: float
    n: int


def _newey_west_long_run_variance(x: np.ndarray, max_lag: int) -> float:
    centered = x - np.mean(x)
    n = len(centered)
    gamma0 = float(np.dot(centered, centered) / n)
    lrv = gamma0
    for lag in range(1, min(max_lag, n - 1) + 1):
        weight = 1.0 - lag / (max_lag + 1.0)
        gamma = float(np.dot(centered[lag:], centered[:-lag]) / n)
        lrv += 2.0 * weight * gamma
    return max(lrv, 0.0)


def diebold_mariano(
    actual: pd.Series,
    benchmark: pd.Series,
    challenger: pd.Series,
    *,
    loss: str = "squared",
    hac_lags: int = 5,
) -> DMResult:
    """Two-sided Diebold-Mariano-style forecast comparison with HAC variance.

    Positive mean loss difference means the challenger has lower loss than the benchmark.
    The implementation intentionally reports a two-sided p-value; directional claims can be
    made only after the sign of the loss difference is inspected.
    """
    data = pd.concat(
        [actual.rename("y"), benchmark.rename("b"), challenger.rename("c")], axis=1
    ).dropna()
    if len(data) < 20:
        raise ValueError("need at least 20 paired forecasts")

    eb = data["y"].to_numpy() - data["b"].to_numpy()
    ec = data["y"].to_numpy() - data["c"].to_numpy()
    if loss == "squared":
        d = eb**2 - ec**2
    elif loss == "absolute":
        d = np.abs(eb) - np.abs(ec)
    else:
        raise ValueError("loss must be 'squared' or 'absolute'")

    mean_d = float(np.mean(d))
    lrv = _newey_west_long_run_variance(d, hac_lags)
    if lrv <= 0:
        statistic = 0.0 if mean_d == 0 else float(np.sign(mean_d) * np.inf)
    else:
        statistic = float(mean_d / np.sqrt(lrv / len(d)))
    p_value = float(2.0 * norm.sf(abs(statistic)))
    return DMResult(statistic, p_value, mean_d, len(d))


def compare_forecasts_with_fdr(
    actuals: pd.DataFrame,
    benchmark: pd.DataFrame,
    challenger: pd.DataFrame,
    *,
    q: float = 0.10,
    hac_lags: int = 5,
) -> pd.DataFrame:
    common = [c for c in actuals.columns if c in benchmark.columns and c in challenger.columns]
    rows: list[dict[str, object]] = []
    for col in common:
        dm = diebold_mariano(
            actuals[col], benchmark[col], challenger[col], hac_lags=hac_lags
        )
        rows.append(
            {
                "variable": col,
                "dm_stat": dm.statistic,
                "p_value": dm.p_value,
                "mean_loss_improvement": dm.mean_loss_difference,
                "n": dm.n,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    accepted = benjamini_hochberg(out["p_value"].to_numpy(), q=q)
    out["fdr_reject"] = accepted
    out["challenger_better"] = out["mean_loss_improvement"] > 0
    return out.sort_values(["fdr_reject", "mean_loss_improvement"], ascending=[False, False])
