from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from market_information_dynamics.models.direct_sparse import DirectSparseForecaster
from market_information_dynamics.statistics.signal_survival import (
    edge_survival_table,
    survival_mask,
)


@dataclass
class MultiHorizonResult:
    horizon: int
    predictions: dict[str, pd.DataFrame]
    actuals: pd.DataFrame
    edge_snapshots: pd.DataFrame
    edge_contributions: pd.DataFrame
    survival_history: pd.DataFrame


def _future_cumulative(frame: pd.DataFrame, origin: int, horizon: int, targets: list[str]) -> pd.Series:
    values = frame.loc[:, targets].iloc[origin : origin + horizon].sum(axis=0)
    values.name = frame.index[origin]
    return values


def _fit_direct_ar(
    history: pd.DataFrame,
    *,
    target: str,
    lags: int,
    horizon: int,
    ridge_alpha: float,
) -> tuple[StandardScaler, StandardScaler, Ridge]:
    s = history[target].to_numpy(dtype=float)
    last_origin = len(s) - horizon
    X, y = [], []
    for origin in range(lags, last_origin + 1):
        X.append([s[origin - lag] for lag in range(1, lags + 1)])
        y.append(float(s[origin : origin + horizon].sum()))
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1, 1)
    xs = StandardScaler().fit(X)
    ys = StandardScaler().fit(y)
    model = Ridge(alpha=ridge_alpha, fit_intercept=True)
    model.fit(xs.transform(X), ys.transform(y).ravel())
    return xs, ys, model


def _predict_direct_ar(
    history: pd.DataFrame,
    *,
    target: str,
    lags: int,
    fitted: tuple[StandardScaler, StandardScaler, Ridge],
) -> float:
    xs, ys, model = fitted
    s = history[target].to_numpy(dtype=float)
    row = np.asarray([[s[-lag] for lag in range(1, lags + 1)]], dtype=float)
    pred_scaled = float(model.predict(xs.transform(row))[0])
    return float(ys.inverse_transform([[pred_scaled]])[0, 0])


def walk_forward_signal_survival(
    frame: pd.DataFrame,
    *,
    financial_columns: list[str],
    target_columns: list[str],
    horizon: int,
    lags: int,
    alpha: float,
    min_train: int,
    refit_every: int,
    ar_alpha: float,
    ridge_alpha: float,
    edge_threshold: float,
    structural_half_life_days: float,
    contribution_half_life_days: float,
    min_selection_frequency: float,
    min_sign_stability: float,
    min_strength_retention: float,
    min_contributions: int,
    min_survival_snapshots: int,
    max_edges_per_target: int | None,
) -> MultiHorizonResult:
    """Direct multi-horizon walk-forward evaluation with online edge survival.

    Edge survival at forecast origin ``t`` uses only model snapshots available by ``t`` and
    forecast-loss attributions whose outcome horizon has fully realised before ``t``.
    """
    if frame.isna().any().any():
        raise ValueError("walk-forward signal-survival evaluation requires a complete panel")
    if len(frame) <= min_train + horizon:
        raise ValueError("frame too short for requested training window and horizon")

    models: dict[str, DirectSparseForecaster] = {}
    ar_models: dict[str, tuple[StandardScaler, StandardScaler, Ridge]] = {}
    survivor_model: DirectSparseForecaster | None = None
    survivor_mask: pd.DataFrame | None = None

    predictions: dict[str, list[pd.Series]] = {
        "ar": [],
        "financial_direct_sparse": [],
        "full_direct_sparse": [],
        "survival_refit_full": [],
    }
    actuals: list[pd.Series] = []
    snapshots: list[dict[str, object]] = []
    pending_attributions: list[dict[str, object]] = []
    realised_contributions: list[dict[str, object]] = []
    survival_rows: list[dict[str, object]] = []

    last_origin = len(frame) - horizon
    for i in range(min_train, last_origin + 1):
        origin_date = pd.Timestamp(frame.index[i])
        history = frame.iloc[:i]

        # Outcomes become admissible for survival only after the whole forecast horizon realises.
        still_pending: list[dict[str, object]] = []
        for row in pending_attributions:
            if pd.Timestamp(row["realized_date"]) < origin_date:
                realised_contributions.append(row)
            else:
                still_pending.append(row)
        pending_attributions = still_pending

        if not models or (i - min_train) % refit_every == 0:
            models["financial"] = DirectSparseForecaster(
                lags=lags, horizon=horizon, alpha=alpha
            ).fit(history[financial_columns], target_columns=target_columns)
            models["full"] = DirectSparseForecaster(
                lags=lags, horizon=horizon, alpha=alpha
            ).fit(history, target_columns=target_columns)
            ar_models = {
                target: _fit_direct_ar(
                    history,
                    target=target,
                    lags=lags,
                    horizon=horizon,
                    ridge_alpha=ar_alpha,
                )
                for target in target_columns
            }

            full_model = models["full"]
            for source in frame.columns:
                for target in target_columns:
                    if source == target:
                        continue
                    snapshots.append(
                        {
                            "date": origin_date,
                            "horizon": horizon,
                            "source": source,
                            "target": target,
                            "strength": float(full_model.adjacency_.loc[source, target]),
                            "signed_weight": float(
                                full_model.signed_adjacency_.loc[source, target]
                            ),
                        }
                    )

            snapshot_df = pd.DataFrame(snapshots)
            contribution_df = pd.DataFrame(realised_contributions)
            n_snapshot_dates = int(snapshot_df["date"].nunique()) if len(snapshot_df) else 0
            if n_snapshot_dates >= min_survival_snapshots:
                table = edge_survival_table(
                    snapshot_df,
                    contribution_df,
                    as_of=origin_date,
                    edge_threshold=edge_threshold,
                    structural_half_life_days=structural_half_life_days,
                    contribution_half_life_days=contribution_half_life_days,
                )
                if len(table):
                    table = table.assign(date=origin_date, horizon=horizon)
                    survival_rows.extend(table.to_dict("records"))
                survivor_mask = survival_mask(
                    table,
                    sources=list(frame.columns),
                    targets=target_columns,
                    min_selection_frequency=min_selection_frequency,
                    min_sign_stability=min_sign_stability,
                    min_strength_retention=min_strength_retention,
                    min_contributions=min_contributions,
                    max_edges_per_target=max_edges_per_target,
                )
                survivor_model = full_model
                survivor_model.fit_post_selection(survivor_mask, ridge_alpha=ridge_alpha)
            else:
                survivor_model = None
                survivor_mask = None

        financial_pred = models["financial"].predict_next(history[financial_columns])
        full_pred = models["full"].predict_next(history)
        ar_pred = pd.Series(
            {
                target: _predict_direct_ar(
                    history, target=target, lags=lags, fitted=ar_models[target]
                )
                for target in target_columns
            },
            name=origin_date,
        )
        if survivor_model is None:
            survival_pred = full_pred.copy()
        else:
            survival_pred = survivor_model.predict_post_selection(history)

        for name, pred in [
            ("ar", ar_pred),
            ("financial_direct_sparse", financial_pred),
            ("full_direct_sparse", full_pred),
            ("survival_refit_full", survival_pred),
        ]:
            pred.name = origin_date
            predictions[name].append(pred[target_columns])

        actual = _future_cumulative(frame, i, horizon, target_columns)
        actuals.append(actual)
        realized_date = pd.Timestamp(frame.index[i + horizon - 1])

        # Marginal OOS edge utility in the unfiltered full sparse model.
        full_model = models["full"]
        for row in full_model.edge_table(threshold=edge_threshold).itertuples(index=False):
            if row.target not in target_columns:
                continue
            without = full_model.predict_without_edge(
                history, source=row.source, target=row.target
            )
            y = float(actual[row.target])
            with_edge = float(full_pred[row.target])
            pending_attributions.append(
                {
                    "origin_date": origin_date,
                    "realized_date": realized_date,
                    "horizon": horizon,
                    "source": row.source,
                    "target": row.target,
                    "loss_improvement": float((y - without) ** 2 - (y - with_edge) ** 2),
                    "with_edge_prediction": with_edge,
                    "without_edge_prediction": without,
                    "actual": y,
                }
            )

    return MultiHorizonResult(
        horizon=horizon,
        predictions={name: pd.DataFrame(rows) for name, rows in predictions.items()},
        actuals=pd.DataFrame(actuals),
        edge_snapshots=pd.DataFrame(snapshots),
        edge_contributions=pd.DataFrame(realised_contributions + pending_attributions),
        survival_history=pd.DataFrame(survival_rows),
    )
