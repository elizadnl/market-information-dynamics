from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_information_dynamics.models.sparse_var import SparseVAR


@dataclass
class WalkForwardResult:
    predictions: pd.DataFrame
    actuals: pd.DataFrame
    edge_snapshots: pd.DataFrame

    def metrics(self) -> pd.DataFrame:
        rows = []
        for col in self.actuals.columns:
            y = self.actuals[col]
            p = self.predictions[col]
            mask = y.notna() & p.notna()
            yv, pv = y[mask], p[mask]
            if len(yv) == 0:
                continue
            rmse = float(np.sqrt(np.mean((yv - pv) ** 2)))
            mae = float(np.mean(np.abs(yv - pv)))
            direction = float(np.mean(np.sign(yv) == np.sign(pv)))
            corr = float(yv.corr(pv)) if len(yv) > 2 else np.nan
            rows.append(
                {"variable": col, "rmse": rmse, "mae": mae, "directional_accuracy": direction, "corr": corr}
            )
        return pd.DataFrame(rows).set_index("variable")


def walk_forward_sparse_var(
    frame: pd.DataFrame,
    *,
    lags: int = 3,
    alpha: float = 0.035,
    min_train: int = 500,
    refit_every: int = 20,
) -> WalkForwardResult:
    """Expanding-window one-step-ahead evaluation with no future preprocessing."""
    if min_train <= lags:
        raise ValueError("min_train must exceed lags")
    if len(frame) <= min_train:
        raise ValueError("frame is too short for min_train")
    if frame.isna().any().any():
        raise ValueError("walk-forward demo expects a complete panel")

    predictions: list[pd.Series] = []
    actuals: list[pd.Series] = []
    edge_rows: list[dict] = []
    model: SparseVAR | None = None

    for i in range(min_train, len(frame)):
        if model is None or (i - min_train) % refit_every == 0:
            model = SparseVAR(lags=lags, alpha=alpha).fit(frame.iloc[:i])
            snapshot_date = frame.index[i]
            for source in frame.columns:
                for target in frame.columns:
                    if source == target:
                        continue
                    edge_rows.append(
                        {
                            "date": snapshot_date,
                            "source": source,
                            "target": target,
                            "strength": float(model.adjacency_.loc[source, target]),
                            "signed_weight": float(model.signed_adjacency_.loc[source, target]),
                        }
                    )

        pred = model.predict_next(frame.iloc[:i])
        pred.name = frame.index[i]
        predictions.append(pred)
        actual = frame.iloc[i].copy()
        actual.name = frame.index[i]
        actuals.append(actual)

    pred_df = pd.DataFrame(predictions)
    actual_df = pd.DataFrame(actuals)
    edges = pd.DataFrame(edge_rows)
    return WalkForwardResult(predictions=pred_df, actuals=actual_df, edge_snapshots=edges)
