from __future__ import annotations

import pandas as pd

from market_information_dynamics.statistics.fdr import benjamini_hochberg
from market_information_dynamics.statistics.forecast_tests import diebold_mariano


def nested_forecast_tests(
    results: dict[int, object],
    *,
    comparisons: list[tuple[str, str]],
    fdr_q: float = 0.10,
    base_hac_lags: int = 5,
    evaluation_start: str | None = None,
) -> pd.DataFrame:
    """Compare nested forecast models across target/horizon pairs with family-wise BH FDR.

    Overlapping h-day outcomes induce serially correlated loss differences, so the HAC lag
    is at least ``horizon - 1``.
    """
    rows: list[dict[str, object]] = []
    for horizon, result in sorted(results.items()):
        actuals = result.actuals
        predictions = result.predictions
        if evaluation_start is not None:
            cutoff = pd.Timestamp(evaluation_start)
            actuals = actuals.loc[actuals.index >= cutoff]
        for benchmark_name, challenger_name in comparisons:
            benchmark = predictions[benchmark_name].reindex(actuals.index)
            challenger = predictions[challenger_name].reindex(actuals.index)
            for target in actuals.columns:
                paired = pd.concat(
                    [actuals[target], benchmark[target], challenger[target]], axis=1
                ).dropna()
                if len(paired) < 20:
                    continue
                hac_lags = max(int(base_hac_lags), int(horizon) - 1)
                dm = diebold_mariano(
                    paired.iloc[:, 0],
                    paired.iloc[:, 1],
                    paired.iloc[:, 2],
                    hac_lags=hac_lags,
                )
                rows.append(
                    {
                        "comparison": f"{benchmark_name} -> {challenger_name}",
                        "benchmark": benchmark_name,
                        "challenger": challenger_name,
                        "horizon": int(horizon),
                        "target": target,
                        "n": dm.n,
                        "hac_lags": hac_lags,
                        "dm_stat": dm.statistic,
                        "p_value": dm.p_value,
                        "mean_loss_improvement": dm.mean_loss_difference,
                        "challenger_better": dm.mean_loss_difference > 0,
                    }
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["fdr_reject"] = False
    for comparison, idx in out.groupby("comparison").groups.items():
        accepted = benjamini_hochberg(out.loc[idx, "p_value"].to_numpy(), q=fdr_q)
        out.loc[idx, "fdr_reject"] = accepted
    return out.sort_values(
        ["comparison", "fdr_reject", "mean_loss_improvement"],
        ascending=[True, False, False],
        ignore_index=True,
    )
