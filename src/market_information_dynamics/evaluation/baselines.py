from __future__ import annotations

import pandas as pd

from market_information_dynamics.models.autoregressive import UnivariateAR


def walk_forward_univariate_ar(
    frame: pd.DataFrame,
    *,
    lags: int = 3,
    min_train: int = 500,
    refit_every: int = 20,
    alpha: float = 1.0,
) -> pd.DataFrame:
    """Expanding-window target-only benchmark."""
    if len(frame) <= min_train:
        raise ValueError("frame is too short for min_train")
    model: UnivariateAR | None = None
    preds: list[pd.Series] = []
    for i in range(min_train, len(frame)):
        if model is None or (i - min_train) % refit_every == 0:
            model = UnivariateAR(lags=lags, alpha=alpha).fit(frame.iloc[:i])
        pred = model.predict_next(frame.iloc[:i])
        pred.name = frame.index[i]
        preds.append(pred)
    return pd.DataFrame(preds)
