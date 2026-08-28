from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _weights(dates: pd.Series, as_of: pd.Timestamp, half_life_days: float) -> np.ndarray:
    ages = (as_of - pd.to_datetime(dates)).dt.total_seconds().to_numpy() / 86400.0
    ages = np.maximum(ages, 0.0)
    return np.exp(-math.log(2.0) * ages / max(float(half_life_days), 1e-9))


def _weighted_t(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    if len(values) < 2 or float(weights.sum()) <= 0:
        return float("nan"), float("nan")
    mean = float(np.average(values, weights=weights))
    var = float(np.average((values - mean) ** 2, weights=weights))
    eff_n = float(weights.sum() ** 2 / np.sum(weights**2))
    if var <= 0 or eff_n <= 1:
        return mean, 0.0
    return mean, float(mean / math.sqrt(var / eff_n))


def adaptive_overlay_gates(
    realised_model_contributions: pd.DataFrame,
    *,
    targets: list[str],
    as_of: pd.Timestamp,
    half_life_days: float = 120.0,
    min_observations: int = 30,
    t_scale: float = 2.0,
) -> pd.DataFrame:
    """Online shrinkage gate for an alternative-data overlay.

    ``loss_improvement`` is core squared loss minus augmented squared loss. The gate is
    exactly zero unless the overlay has enough fully realised OOS observations, positive
    recency-weighted mean contribution, and positive evidence t-statistic. Otherwise it
    rises smoothly toward one rather than switching discontinuously on a p-value.
    """
    rows: list[dict[str, object]] = []
    if len(realised_model_contributions):
        data = realised_model_contributions.loc[
            pd.to_datetime(realised_model_contributions["realized_date"]) < as_of
        ].copy()
    else:
        data = realised_model_contributions.copy()

    for target in targets:
        g = data.loc[data.get("target", pd.Series(dtype=str)) == target] if len(data) else data
        n = int(len(g))
        mean = float("nan")
        t_stat = float("nan")
        gate = 0.0
        hit = float("nan")
        if n >= int(min_observations):
            w = _weights(g["realized_date"], as_of, half_life_days)
            values = g["loss_improvement"].to_numpy(dtype=float)
            mean, t_stat = _weighted_t(values, w)
            hit = float(np.average((values > 0).astype(float), weights=w))
            if np.isfinite(mean) and np.isfinite(t_stat) and mean > 0 and t_stat > 0:
                gate = float(np.tanh(t_stat / max(float(t_scale), 1e-9)))
        rows.append(
            {
                "target": target,
                "n": n,
                "weighted_mean_loss_improvement": mean,
                "contribution_hit_rate": hit,
                "contribution_t_stat": t_stat,
                "gate": gate,
            }
        )
    return pd.DataFrame(rows)
