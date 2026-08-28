from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd


@dataclass
class FixedShareResult:
    prediction: pd.DataFrame
    weights: pd.DataFrame
    realised_losses: pd.DataFrame


def _learning_rate(n_updates: int, n_experts: int) -> float:
    """Self-confident Hedge learning rate for bounded losses in [0, 1]."""
    if n_experts <= 1:
        return 0.0
    return float(min(1.0, math.sqrt(8.0 * math.log(n_experts) / max(n_updates, 1))))


def fixed_share_forecast(
    actuals: pd.DataFrame,
    expert_predictions: dict[str, pd.DataFrame],
    *,
    horizon: int,
    share: float = 1.0 / 252.0,
    loss_scale_window: int = 252,
    loss_clip: float = 5.0,
) -> FixedShareResult:
    """Causally aggregate forecast experts with the Fixed-Share algorithm.

    The row index is the forecast origin. For an h-step forecast, the loss from origin
    ``i-h`` is admitted only before the forecast at origin ``i``. This prevents the
    online combiner from learning from a forecast whose target has not fully realised.

    Squared losses are normalised by a trailing median of *previously realised* pooled
    expert losses, clipped, and therefore bounded before the exponential update.
    ``share`` leaks a small amount of probability mass back to every expert so a model
    that was previously poor can recover after a regime change.
    """
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    if not 0.0 <= share < 1.0:
        raise ValueError("share must be in [0, 1)")
    if loss_scale_window < 1:
        raise ValueError("loss_scale_window must be >= 1")
    if loss_clip <= 0:
        raise ValueError("loss_clip must be > 0")
    if not expert_predictions:
        raise ValueError("at least one expert is required")

    names = list(expert_predictions)
    common_index = actuals.index
    common_columns = actuals.columns
    for frame in expert_predictions.values():
        common_index = common_index.intersection(frame.index)
        common_columns = common_columns.intersection(frame.columns)
    common_index = common_index.sort_values()
    if len(common_index) <= horizon:
        raise ValueError("not enough paired rows for delayed online aggregation")
    if not len(common_columns):
        raise ValueError("no common forecast targets")

    y = actuals.reindex(index=common_index, columns=common_columns).astype(float)
    preds = {
        name: frame.reindex(index=common_index, columns=common_columns).astype(float)
        for name, frame in expert_predictions.items()
    }

    prediction = pd.DataFrame(index=common_index, columns=common_columns, dtype=float)
    weight_records: list[dict[str, object]] = []
    loss_records: list[dict[str, object]] = []

    for target in common_columns:
        weights = np.full(len(names), 1.0 / len(names), dtype=float)
        scale_history: list[float] = []
        n_updates = 0

        for i, origin in enumerate(common_index):
            # Only now has the forecast from i-h fully realised.
            j = i - horizon
            if j >= 0:
                realised_origin = common_index[j]
                actual = float(y.loc[realised_origin, target])
                expert_values = np.array(
                    [float(preds[name].loc[realised_origin, target]) for name in names],
                    dtype=float,
                )
                raw_losses = (actual - expert_values) ** 2
                pooled = float(np.mean(raw_losses))
                if scale_history:
                    scale = float(np.median(scale_history[-loss_scale_window:]))
                else:
                    scale = pooled
                scale = max(scale, 1e-12)
                bounded = np.clip(raw_losses / scale, 0.0, loss_clip) / loss_clip

                n_updates += 1
                eta = _learning_rate(n_updates, len(names))
                updated = weights * np.exp(-eta * bounded)
                total = float(updated.sum())
                if not np.isfinite(total) or total <= 0:
                    updated = np.full(len(names), 1.0 / len(names), dtype=float)
                else:
                    updated /= total
                weights = (1.0 - share) * updated + share / len(names)
                weights /= weights.sum()
                scale_history.append(pooled)

                for k, name in enumerate(names):
                    loss_records.append(
                        {
                            "target": target,
                            "origin_date": realised_origin,
                            "realised_before": origin,
                            "expert": name,
                            "squared_loss": float(raw_losses[k]),
                            "bounded_loss": float(bounded[k]),
                            "eta": eta,
                        }
                    )

            expert_now = np.array(
                [float(preds[name].loc[origin, target]) for name in names], dtype=float
            )
            prediction.loc[origin, target] = float(np.dot(weights, expert_now))
            for k, name in enumerate(names):
                weight_records.append(
                    {
                        "date": origin,
                        "target": target,
                        "expert": name,
                        "weight": float(weights[k]),
                        "horizon": int(horizon),
                        "n_realised_updates": int(n_updates),
                    }
                )

    weights_df = pd.DataFrame(weight_records)
    losses_df = pd.DataFrame(loss_records)
    return FixedShareResult(prediction=prediction, weights=weights_df, realised_losses=losses_df)
