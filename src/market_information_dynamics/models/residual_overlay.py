from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, Ridge
from sklearn.preprocessing import StandardScaler


@dataclass
class ResidualOverlayForecaster:
    """Sparse candidate-data overlay trained on realised OOS core forecast residuals.

    The core model is deliberately outside this class. Training targets are historical
    ``actual - core_forecast`` residuals from forecasts that were genuinely made out of
    sample and have fully realised. Candidate features are lagged observations available
    before each residual's forecast origin.

    This makes the alternative-data layer answer a strict incremental question: can the
    candidate domain explain errors left behind by the protected core model?
    """

    lags: int = 5
    alpha: float = 0.035
    max_iter: int = 20_000

    def _design(
        self,
        candidate_history: pd.DataFrame,
        residuals: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray, pd.DatetimeIndex]:
        if candidate_history.isna().any().any():
            raise ValueError("candidate_history must be complete")
        if residuals.isna().any().any():
            raise ValueError("residuals must be complete")
        if self.lags < 1:
            raise ValueError("lags must be >= 1")

        values = candidate_history.to_numpy(dtype=float)
        index = pd.DatetimeIndex(candidate_history.index)
        loc = {pd.Timestamp(d): i for i, d in enumerate(index)}
        rows: list[np.ndarray] = []
        targets: list[np.ndarray] = []
        used: list[pd.Timestamp] = []
        for date, row in residuals.sort_index().iterrows():
            pos = loc.get(pd.Timestamp(date))
            if pos is None or pos < self.lags:
                continue
            rows.append(
                np.concatenate([values[pos - lag] for lag in range(1, self.lags + 1)])
            )
            targets.append(row.to_numpy(dtype=float))
            used.append(pd.Timestamp(date))
        if not rows:
            raise ValueError("no residual origins have enough candidate lag history")
        return np.asarray(rows), np.asarray(targets), pd.DatetimeIndex(used)

    def fit(
        self,
        candidate_history: pd.DataFrame,
        residuals: pd.DataFrame,
    ) -> "ResidualOverlayForecaster":
        self.columns_ = list(candidate_history.columns)
        self.target_columns_ = list(residuals.columns)
        X, Y, used = self._design(candidate_history, residuals)
        self.training_origins_ = used
        self.x_scaler_ = StandardScaler().fit(X)
        self.Xs_ = self.x_scaler_.transform(X)

        # Scale residual magnitudes but intentionally do not subtract their mean. An overlay
        # with no candidate signal should be exactly zero rather than an unconditional bias
        # correction that could masquerade as alternative-data value.
        scales = np.std(Y, axis=0, ddof=0)
        scales = np.where(scales <= 1e-12, 1.0, scales)
        self.y_scale_ = scales.astype(float)
        self.Ys_ = Y / self.y_scale_

        self.models_: list[Lasso] = []
        coefficients = np.zeros(
            (len(self.target_columns_), self.lags, len(self.columns_)), dtype=float
        )
        for target_idx in range(len(self.target_columns_)):
            model = Lasso(
                alpha=self.alpha,
                fit_intercept=False,
                max_iter=self.max_iter,
            )
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
        self.post_models_: dict[str, tuple[np.ndarray, Ridge] | None] = {}
        return self

    def _latest_scaled_row(self, candidate_history: pd.DataFrame) -> np.ndarray:
        if list(candidate_history.columns) != self.columns_:
            raise ValueError("candidate history columns must match training columns and order")
        if len(candidate_history) < self.lags:
            raise ValueError("candidate history is shorter than lags")
        vals = candidate_history.iloc[-self.lags :].to_numpy(dtype=float)
        row = np.concatenate([vals[-lag] for lag in range(1, self.lags + 1)]).reshape(1, -1)
        return self.x_scaler_.transform(row)[0]

    def predict_next(self, candidate_history: pd.DataFrame) -> pd.Series:
        xs = self._latest_scaled_row(candidate_history)
        scaled = np.asarray([float(np.dot(m.coef_, xs)) for m in self.models_])
        pred = scaled * self.y_scale_
        return pd.Series(pred, index=self.target_columns_, name=candidate_history.index[-1])

    def predict_edge_effect(
        self,
        candidate_history: pd.DataFrame,
        *,
        source: str,
        target: str,
    ) -> float:
        """Return this source→target edge's additive residual forecast contribution."""
        source_idx = self.columns_.index(source)
        target_idx = self.target_columns_.index(target)
        xs = self._latest_scaled_row(candidate_history)
        width = len(self.columns_)
        effect_scaled = 0.0
        model = self.models_[target_idx]
        for lag in range(self.lags):
            feature_idx = lag * width + source_idx
            effect_scaled += float(model.coef_[feature_idx] * xs[feature_idx])
        return float(effect_scaled * self.y_scale_[target_idx])

    def fit_post_selection(
        self,
        edge_mask: pd.DataFrame,
        *,
        ridge_alpha: float = 1.0,
    ) -> "ResidualOverlayForecaster":
        if list(edge_mask.index) != self.columns_:
            raise ValueError("edge_mask index must match candidate source columns")
        if list(edge_mask.columns) != self.target_columns_:
            raise ValueError("edge_mask columns must match targets")

        self.post_models_ = {}
        for target_idx, target in enumerate(self.target_columns_):
            sources = edge_mask[target].to_numpy(dtype=bool)
            idx = np.flatnonzero(np.tile(sources, self.lags))
            if len(idx) == 0:
                # Zero overlay is the protected-core fallback.
                self.post_models_[target] = None
                continue
            model = Ridge(alpha=ridge_alpha, fit_intercept=False)
            model.fit(self.Xs_[:, idx], self.Ys_[:, target_idx])
            self.post_models_[target] = (idx, model)
        return self

    def predict_post_selection(self, candidate_history: pd.DataFrame) -> pd.Series:
        if not self.post_models_:
            raise RuntimeError("fit_post_selection must be called first")
        xs = self._latest_scaled_row(candidate_history)
        values: list[float] = []
        for target_idx, target in enumerate(self.target_columns_):
            fitted = self.post_models_[target]
            if fitted is None:
                values.append(0.0)
                continue
            idx, model = fitted
            scaled = float(model.predict(xs[idx].reshape(1, -1))[0])
            values.append(scaled * self.y_scale_[target_idx])
        return pd.Series(values, index=self.target_columns_, name=candidate_history.index[-1])

    def edge_table(self, threshold: float = 0.05) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for source in self.columns_:
            for target in self.target_columns_:
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
