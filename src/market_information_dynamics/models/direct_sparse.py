from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, Ridge
from sklearn.preprocessing import StandardScaler


@dataclass
class DirectSparseForecaster:
    """Direct multi-horizon sparse predictor with interpretable source→target edges.

    For forecast origin ``t`` the design uses only observations up to ``t-1``. The target
    is the cumulative transformed move over ``[t, t+horizon-1]``. This avoids recursive
    error accumulation and makes every horizon a distinct, falsifiable forecast problem.
    Coefficients live in standardised coordinates and represent predictive association,
    not structural causality.
    """

    lags: int = 5
    horizon: int = 1
    alpha: float = 0.035
    max_iter: int = 20_000

    def _design(
        self, frame: pd.DataFrame, target_columns: list[str]
    ) -> tuple[np.ndarray, np.ndarray]:
        values = frame.to_numpy(dtype=float)
        target_idx = [frame.columns.get_loc(c) for c in target_columns]
        n = len(frame)
        last_origin = n - self.horizon
        if last_origin < self.lags:
            raise ValueError("frame is too short for lags + horizon")

        rows: list[np.ndarray] = []
        targets: list[np.ndarray] = []
        for origin in range(self.lags, last_origin + 1):
            rows.append(
                np.concatenate([values[origin - lag] for lag in range(1, self.lags + 1)])
            )
            targets.append(values[origin : origin + self.horizon, :][:, target_idx].sum(axis=0))
        return np.asarray(rows), np.asarray(targets)

    def fit(
        self, frame: pd.DataFrame, *, target_columns: list[str] | None = None
    ) -> "DirectSparseForecaster":
        if frame.isna().any().any():
            raise ValueError("DirectSparseForecaster.fit requires a complete panel")
        if self.horizon < 1:
            raise ValueError("horizon must be >= 1")
        if self.lags < 1:
            raise ValueError("lags must be >= 1")

        self.columns_ = list(frame.columns)
        self.target_columns_ = list(target_columns or self.columns_)
        missing = [c for c in self.target_columns_ if c not in self.columns_]
        if missing:
            raise KeyError(f"target columns not in frame: {missing}")

        X, Y = self._design(frame, self.target_columns_)
        self.x_scaler_ = StandardScaler().fit(X)
        self.y_scaler_ = StandardScaler().fit(Y)
        self.Xs_ = self.x_scaler_.transform(X)
        self.Ys_ = self.y_scaler_.transform(Y)

        self.models_: list[Lasso] = []
        coefficients = np.zeros(
            (len(self.target_columns_), self.lags, len(self.columns_)), dtype=float
        )
        for target_idx in range(len(self.target_columns_)):
            model = Lasso(alpha=self.alpha, fit_intercept=True, max_iter=self.max_iter)
            model.fit(self.Xs_, self.Ys_[:, target_idx])
            self.models_.append(model)
            coefficients[target_idx] = model.coef_.reshape(self.lags, len(self.columns_))

        self.coef_tensor_ = coefficients
        adjacency = np.abs(coefficients).sum(axis=1).T
        self.adjacency_ = pd.DataFrame(
            adjacency, index=self.columns_, columns=self.target_columns_
        )

        signed = np.zeros_like(adjacency)
        for target_idx in range(len(self.target_columns_)):
            for source_idx in range(len(self.columns_)):
                lag_coefs = coefficients[target_idx, :, source_idx]
                if np.any(lag_coefs):
                    signed[source_idx, target_idx] = lag_coefs[np.argmax(np.abs(lag_coefs))]
        self.signed_adjacency_ = pd.DataFrame(
            signed, index=self.columns_, columns=self.target_columns_
        )
        self.post_models_: dict[str, tuple[np.ndarray, Ridge]] = {}
        return self

    def _latest_scaled_row(self, history: pd.DataFrame) -> np.ndarray:
        if list(history.columns) != self.columns_:
            raise ValueError("history columns must match training columns and order")
        if len(history) < self.lags:
            raise ValueError("history is shorter than lags")
        vals = history.iloc[-self.lags :].to_numpy(dtype=float)
        row = np.concatenate([vals[-lag] for lag in range(1, self.lags + 1)]).reshape(1, -1)
        return self.x_scaler_.transform(row)[0]

    def predict_next(self, history: pd.DataFrame) -> pd.Series:
        xs = self._latest_scaled_row(history)
        pred_scaled = np.array(
            [float(m.intercept_ + np.dot(m.coef_, xs)) for m in self.models_]
        ).reshape(1, -1)
        pred = self.y_scaler_.inverse_transform(pred_scaled)[0]
        return pd.Series(pred, index=self.target_columns_, name=history.index[-1])

    def predict_without_edge(self, history: pd.DataFrame, *, source: str, target: str) -> float:
        """Counterfactual prediction with one source→target edge zeroed, without refitting.

        This is used for online marginal forecast-loss attribution. It deliberately asks a
        narrow question: did the currently fitted edge improve the realised forecast, all
        else equal? Final survivor forecasts are refitted separately after selection.
        """
        source_idx = self.columns_.index(source)
        target_idx = self.target_columns_.index(target)
        xs = self._latest_scaled_row(history)
        model = self.models_[target_idx]
        base_scaled = float(model.intercept_ + np.dot(model.coef_, xs))
        edge_scaled = 0.0
        width = len(self.columns_)
        for lag in range(self.lags):
            feature_idx = lag * width + source_idx
            edge_scaled += float(model.coef_[feature_idx] * xs[feature_idx])
        counter_scaled = np.array([[base_scaled - edge_scaled]])
        # Invert only this target's scaling parameters.
        mean = float(self.y_scaler_.mean_[target_idx])
        scale = float(self.y_scaler_.scale_[target_idx])
        return float(counter_scaled[0, 0] * scale + mean)

    def fit_post_selection(
        self,
        edge_mask: pd.DataFrame,
        *,
        ridge_alpha: float = 1.0,
    ) -> "DirectSparseForecaster":
        """Refit selected predictors with Ridge after sparse edge selection.

        LASSO is used for structure discovery; the final forecast is not produced by merely
        zeroing coefficients from the original fit. Each target is re-estimated conditional
        on the surviving source set, reducing shrinkage bias while retaining regularisation.
        """
        if list(edge_mask.index) != self.columns_:
            raise ValueError("edge_mask index must match source columns")
        if list(edge_mask.columns) != self.target_columns_:
            raise ValueError("edge_mask columns must match target columns")

        width = len(self.columns_)
        self.post_models_ = {}
        for target_idx, target in enumerate(self.target_columns_):
            sources = edge_mask[target].to_numpy(dtype=bool)
            feature_mask = np.tile(sources, self.lags)
            idx = np.flatnonzero(feature_mask)
            if len(idx) == 0:
                # A target should normally retain self-lags, but keep a safe intercept-only path.
                idx = np.array([], dtype=int)
                model = Ridge(alpha=ridge_alpha, fit_intercept=True)
                model.fit(np.zeros((len(self.Xs_), 1)), self.Ys_[:, target_idx])
            else:
                model = Ridge(alpha=ridge_alpha, fit_intercept=True)
                model.fit(self.Xs_[:, idx], self.Ys_[:, target_idx])
            self.post_models_[target] = (idx, model)
        return self

    def predict_post_selection(self, history: pd.DataFrame) -> pd.Series:
        if not self.post_models_:
            raise RuntimeError("fit_post_selection must be called first")
        xs = self._latest_scaled_row(history)
        scaled: list[float] = []
        for target in self.target_columns_:
            idx, model = self.post_models_[target]
            if len(idx):
                value = float(model.predict(xs[idx].reshape(1, -1))[0])
            else:
                value = float(model.predict(np.zeros((1, 1)))[0])
            scaled.append(value)
        pred = self.y_scaler_.inverse_transform(np.asarray(scaled).reshape(1, -1))[0]
        return pd.Series(pred, index=self.target_columns_, name=history.index[-1])

    def edge_table(self, threshold: float = 0.05) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for source in self.columns_:
            for target in self.target_columns_:
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
