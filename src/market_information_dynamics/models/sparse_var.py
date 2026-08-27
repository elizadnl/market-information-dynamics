from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.preprocessing import StandardScaler

from market_information_dynamics.compute.lagged import build_lagged_design


@dataclass
class SparseVAR:
    """Sparse autoregression estimated target-by-target with L1 regularisation.

    Coefficients are estimated in standardised coordinates. The resulting adjacency
    matrix represents predictive influence, not structural causality.
    """

    lags: int = 3
    alpha: float = 0.035
    max_iter: int = 20_000
    design_backend: str = "auto"

    def _design(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        X, Y, backend = build_lagged_design(
            frame.to_numpy(dtype=float), self.lags, backend=self.design_backend
        )
        self.design_backend_ = backend
        return X, Y

    def fit(self, frame: pd.DataFrame) -> "SparseVAR":
        if frame.isna().any().any():
            raise ValueError("SparseVAR.fit requires a complete panel")
        self.columns_ = list(frame.columns)
        X, Y = self._design(frame)
        self.x_scaler_ = StandardScaler().fit(X)
        self.y_scaler_ = StandardScaler().fit(Y)
        Xs = self.x_scaler_.transform(X)
        Ys = self.y_scaler_.transform(Y)

        self.models_: list[Lasso] = []
        coefficients = np.zeros((len(self.columns_), self.lags, len(self.columns_)))
        for target_idx in range(len(self.columns_)):
            model = Lasso(alpha=self.alpha, fit_intercept=True, max_iter=self.max_iter)
            model.fit(Xs, Ys[:, target_idx])
            self.models_.append(model)
            coefficients[target_idx] = model.coef_.reshape(self.lags, len(self.columns_))

        self.coef_tensor_ = coefficients
        # Rows = source; columns = target. Sum absolute standardised effects across lags.
        adjacency = np.abs(coefficients).sum(axis=1).T
        self.adjacency_ = pd.DataFrame(adjacency, index=self.columns_, columns=self.columns_)

        # Signed coefficient of the strongest lag for interpretation.
        signed = np.zeros_like(adjacency)
        for target_idx in range(len(self.columns_)):
            for source_idx in range(len(self.columns_)):
                lag_coefs = coefficients[target_idx, :, source_idx]
                if np.any(lag_coefs):
                    signed[source_idx, target_idx] = lag_coefs[np.argmax(np.abs(lag_coefs))]
        self.signed_adjacency_ = pd.DataFrame(signed, index=self.columns_, columns=self.columns_)
        return self

    def predict_next(self, history: pd.DataFrame) -> pd.Series:
        if list(history.columns) != self.columns_:
            raise ValueError("history columns must match training columns and order")
        if len(history) < self.lags:
            raise ValueError("history is shorter than lags")
        vals = history.iloc[-self.lags :].to_numpy(dtype=float)
        row = np.concatenate([vals[-lag] for lag in range(1, self.lags + 1)]).reshape(1, -1)
        xs = self.x_scaler_.transform(row)
        pred_scaled = np.array([m.predict(xs)[0] for m in self.models_]).reshape(1, -1)
        pred = self.y_scaler_.inverse_transform(pred_scaled)[0]
        return pd.Series(pred, index=self.columns_, name=history.index[-1])

    def predict_next_masked(self, history: pd.DataFrame, edge_mask: pd.DataFrame) -> pd.Series:
        """Predict one step ahead after zeroing disallowed source→target lag coefficients.

        ``edge_mask`` is indexed by source and columned by target. Self-lag entries can be
        kept independently from cross-series edges. The mask is applied in standardised
        coordinates, so it changes only coefficient inclusion rather than preprocessing.
        """
        if list(history.columns) != self.columns_:
            raise ValueError("history columns must match training columns and order")
        if list(edge_mask.index) != self.columns_ or list(edge_mask.columns) != self.columns_:
            raise ValueError("edge_mask must have model columns on both axes in model order")
        if len(history) < self.lags:
            raise ValueError("history is shorter than lags")

        vals = history.iloc[-self.lags :].to_numpy(dtype=float)
        row = np.concatenate([vals[-lag] for lag in range(1, self.lags + 1)]).reshape(1, -1)
        xs = self.x_scaler_.transform(row)[0]
        pred_scaled = []
        for target_idx, model in enumerate(self.models_):
            source_mask = edge_mask.iloc[:, target_idx].to_numpy(dtype=float)
            flat_mask = np.tile(source_mask, self.lags)
            value = float(model.intercept_ + np.dot(model.coef_ * flat_mask, xs))
            pred_scaled.append(value)
        pred = self.y_scaler_.inverse_transform(np.asarray(pred_scaled).reshape(1, -1))[0]
        return pd.Series(pred, index=self.columns_, name=history.index[-1])

    def edge_table(self, threshold: float = 0.05) -> pd.DataFrame:
        rows = []
        for source in self.columns_:
            for target in self.columns_:
                if source == target:
                    continue
                strength = float(self.adjacency_.loc[source, target])
                if strength >= threshold:
                    rows.append(
                        {
                            "source": source,
                            "target": target,
                            "strength": strength,
                            "sign": float(np.sign(self.signed_adjacency_.loc[source, target])),
                        }
                    )
        if not rows:
            return pd.DataFrame(columns=["source", "target", "strength", "sign"])
        return pd.DataFrame(rows).sort_values("strength", ascending=False, ignore_index=True)
