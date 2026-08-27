from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


@dataclass
class UnivariateAR:
    """Target-only autoregressive benchmark fitted separately to each series."""

    lags: int = 3
    alpha: float = 1.0

    def fit(self, frame: pd.DataFrame) -> "UnivariateAR":
        if frame.isna().any().any():
            raise ValueError("UnivariateAR.fit requires a complete panel")
        self.columns_ = list(frame.columns)
        self.models_ = {}
        self.x_scalers_ = {}
        self.y_scalers_ = {}

        for col in self.columns_:
            values = frame[col].to_numpy(dtype=float)
            X = np.array([[values[t - lag] for lag in range(1, self.lags + 1)] for t in range(self.lags, len(values))])
            y = values[self.lags :].reshape(-1, 1)
            xs = StandardScaler().fit(X)
            ys = StandardScaler().fit(y)
            model = Ridge(alpha=self.alpha)
            model.fit(xs.transform(X), ys.transform(y).ravel())
            self.models_[col] = model
            self.x_scalers_[col] = xs
            self.y_scalers_[col] = ys
        return self

    def predict_next(self, history: pd.DataFrame) -> pd.Series:
        if len(history) < self.lags:
            raise ValueError("history is shorter than lags")
        preds = {}
        for col in self.columns_:
            values = history[col].to_numpy(dtype=float)
            x = np.array([[values[-lag] for lag in range(1, self.lags + 1)]])
            x_scaled = self.x_scalers_[col].transform(x)
            p_scaled = self.models_[col].predict(x_scaled).reshape(-1, 1)
            preds[col] = self.y_scalers_[col].inverse_transform(p_scaled)[0, 0]
        return pd.Series(preds)
