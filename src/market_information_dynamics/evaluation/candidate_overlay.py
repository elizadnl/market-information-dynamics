from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from market_information_dynamics.models.direct_sparse import DirectSparseForecaster
from market_information_dynamics.models.residual_overlay import ResidualOverlayForecaster
from market_information_dynamics.statistics.overlay_gate import adaptive_overlay_gates
from market_information_dynamics.statistics.signal_survival import edge_survival_table, survival_mask


@dataclass
class CandidateOverlayResult:
    horizon: int
    predictions: dict[str, pd.DataFrame]
    actuals: pd.DataFrame
    overlay_edge_snapshots: pd.DataFrame
    overlay_edge_contributions: pd.DataFrame
    survival_history: pd.DataFrame
    gate_history: pd.DataFrame
    model_contributions: pd.DataFrame
    core_residuals: pd.DataFrame


def _future_cumulative(
    frame: pd.DataFrame,
    origin: int,
    horizon: int,
    targets: list[str],
) -> pd.Series:
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


def _realise_pending(
    pending: list[dict[str, object]],
    realised: list[dict[str, object]],
    *,
    origin_date: pd.Timestamp,
) -> list[dict[str, object]]:
    still_pending: list[dict[str, object]] = []
    for row in pending:
        if pd.Timestamp(row["realized_date"]) < origin_date:
            realised.append(row)
        else:
            still_pending.append(row)
    return still_pending


def walk_forward_candidate_overlay(
    frame: pd.DataFrame,
    *,
    financial_columns: list[str],
    candidate_columns: list[str],
    target_columns: list[str],
    horizon: int,
    lags: int,
    alpha: float,
    min_train: int,
    refit_every: int,
    ar_alpha: float,
    overlay_alpha: float,
    overlay_min_train: int,
    overlay_ridge_alpha: float,
    edge_threshold: float,
    structural_half_life_days: float,
    contribution_half_life_days: float,
    min_selection_frequency: float,
    min_sign_stability: float,
    min_strength_retention: float,
    min_contributions: int,
    min_survival_snapshots: int,
    max_edges_per_target: int | None,
    gate_half_life_days: float,
    gate_min_observations: int,
    gate_t_scale: float,
) -> CandidateOverlayResult:
    """Protected financial core plus an online, cross-fitted candidate-data overlay.

    The candidate overlay is fitted only to *realised OOS residuals* left by the financial
    core. Candidate edges are evaluated against the core forecast itself, not against a
    potentially weaker full model. A second model-level gate shrinks the entire surviving
    overlay to zero unless its recent realised OOS contribution is positive.
    """
    if frame.isna().any().any():
        raise ValueError("candidate-overlay evaluation requires a complete panel")
    if not candidate_columns:
        raise ValueError("candidate_columns cannot be empty")
    if len(frame) <= min_train + horizon:
        raise ValueError("frame too short for requested training window and horizon")

    predictions: dict[str, list[pd.Series]] = {
        "ar": [],
        "financial_direct_sparse": [],
        "candidate_overlay_sparse": [],
        "candidate_overlay_survival": [],
        "candidate_overlay_adaptive": [],
    }
    actuals: list[pd.Series] = []

    financial_model: DirectSparseForecaster | None = None
    ar_models: dict[str, tuple[StandardScaler, StandardScaler, Ridge]] = {}
    overlay_model: ResidualOverlayForecaster | None = None
    survivor_overlay: ResidualOverlayForecaster | None = None
    current_gates = pd.Series(0.0, index=target_columns, dtype=float)

    snapshots: list[dict[str, object]] = []
    pending_edges: list[dict[str, object]] = []
    realised_edges: list[dict[str, object]] = []
    pending_core: list[dict[str, object]] = []
    realised_core: list[dict[str, object]] = []
    pending_model: list[dict[str, object]] = []
    realised_model: list[dict[str, object]] = []
    survival_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []

    last_origin = len(frame) - horizon
    for i in range(min_train, last_origin + 1):
        origin_date = pd.Timestamp(frame.index[i])
        history = frame.iloc[:i]

        pending_core = _realise_pending(pending_core, realised_core, origin_date=origin_date)
        pending_edges = _realise_pending(pending_edges, realised_edges, origin_date=origin_date)
        pending_model = _realise_pending(pending_model, realised_model, origin_date=origin_date)

        is_refit = financial_model is None or (i - min_train) % refit_every == 0
        if is_refit:
            financial_model = DirectSparseForecaster(
                lags=lags,
                horizon=horizon,
                alpha=alpha,
            ).fit(history[financial_columns], target_columns=target_columns)
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

            overlay_model = None
            survivor_overlay = None
            if len(realised_core) >= int(overlay_min_train):
                residual_df = pd.DataFrame(realised_core).set_index("origin_date")
                residual_df.index = pd.to_datetime(residual_df.index)
                residual_df = residual_df[target_columns].sort_index()
                overlay_model = ResidualOverlayForecaster(
                    lags=lags,
                    alpha=overlay_alpha,
                ).fit(history[candidate_columns], residual_df)

                for source in candidate_columns:
                    for target in target_columns:
                        snapshots.append(
                            {
                                "date": origin_date,
                                "horizon": horizon,
                                "source": source,
                                "target": target,
                                "strength": float(overlay_model.adjacency_.loc[source, target]),
                                "signed_weight": float(
                                    overlay_model.signed_adjacency_.loc[source, target]
                                ),
                            }
                        )

                snapshot_df = pd.DataFrame(snapshots)
                contribution_df = pd.DataFrame(realised_edges)
                n_snapshot_dates = int(snapshot_df["date"].nunique()) if len(snapshot_df) else 0
                if n_snapshot_dates >= int(min_survival_snapshots):
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
                    mask = survival_mask(
                        table,
                        sources=candidate_columns,
                        targets=target_columns,
                        min_selection_frequency=min_selection_frequency,
                        min_sign_stability=min_sign_stability,
                        min_strength_retention=min_strength_retention,
                        min_contributions=min_contributions,
                        max_edges_per_target=max_edges_per_target,
                    )
                    survivor_overlay = overlay_model
                    survivor_overlay.fit_post_selection(mask, ridge_alpha=overlay_ridge_alpha)

            gate_table = adaptive_overlay_gates(
                pd.DataFrame(realised_model),
                targets=target_columns,
                as_of=origin_date,
                half_life_days=gate_half_life_days,
                min_observations=gate_min_observations,
                t_scale=gate_t_scale,
            )
            gate_table = gate_table.assign(date=origin_date, horizon=horizon)
            gate_rows.extend(gate_table.to_dict("records"))
            current_gates = gate_table.set_index("target")["gate"].reindex(target_columns).fillna(0.0)

        assert financial_model is not None
        fin_pred = financial_model.predict_next(history[financial_columns])
        ar_pred = pd.Series(
            {
                target: _predict_direct_ar(
                    history,
                    target=target,
                    lags=lags,
                    fitted=ar_models[target],
                )
                for target in target_columns
            },
            name=origin_date,
        )

        zero_overlay = pd.Series(0.0, index=target_columns, name=origin_date)
        sparse_overlay = (
            zero_overlay
            if overlay_model is None
            else overlay_model.predict_next(history[candidate_columns])
        )
        survival_overlay = (
            zero_overlay
            if survivor_overlay is None
            else survivor_overlay.predict_post_selection(history[candidate_columns])
        )

        sparse_total = fin_pred + sparse_overlay
        survival_total = fin_pred + survival_overlay
        adaptive_total = fin_pred + survival_overlay * current_gates

        for name, pred in [
            ("ar", ar_pred),
            ("financial_direct_sparse", fin_pred),
            ("candidate_overlay_sparse", sparse_total),
            ("candidate_overlay_survival", survival_total),
            ("candidate_overlay_adaptive", adaptive_total),
        ]:
            pred = pred[target_columns].copy()
            pred.name = origin_date
            predictions[name].append(pred)

        actual = _future_cumulative(frame, i, horizon, target_columns)
        actuals.append(actual)
        realized_date = pd.Timestamp(frame.index[i + horizon - 1])

        # These core residuals are only admitted for future overlay fitting after their
        # complete horizon has realised.
        core_row: dict[str, object] = {
            "origin_date": origin_date,
            "realized_date": realized_date,
        }
        for target in target_columns:
            core_row[target] = float(actual[target] - fin_pred[target])
        pending_core.append(core_row)

        # Candidate edge utility is measured directly relative to the protected financial
        # core: financial forecast versus financial forecast plus this edge's own overlay.
        if overlay_model is not None:
            for row in overlay_model.edge_table(threshold=edge_threshold).itertuples(index=False):
                target = str(row.target)
                effect = overlay_model.predict_edge_effect(
                    history[candidate_columns], source=str(row.source), target=target
                )
                y = float(actual[target])
                core_value = float(fin_pred[target])
                edge_only = core_value + effect
                pending_edges.append(
                    {
                        "origin_date": origin_date,
                        "realized_date": realized_date,
                        "horizon": horizon,
                        "source": str(row.source),
                        "target": target,
                        "loss_improvement": float(
                            (y - core_value) ** 2 - (y - edge_only) ** 2
                        ),
                        "core_prediction": core_value,
                        "edge_only_prediction": edge_only,
                        "actual": y,
                    }
                )

        # The second gate asks whether the entire selected overlay is recently useful after
        # interactions/refitting, again relative to the same protected core forecast.
        for target in target_columns:
            y = float(actual[target])
            core_value = float(fin_pred[target])
            augmented = float(survival_total[target])
            pending_model.append(
                {
                    "origin_date": origin_date,
                    "realized_date": realized_date,
                    "horizon": horizon,
                    "target": target,
                    "loss_improvement": float(
                        (y - core_value) ** 2 - (y - augmented) ** 2
                    ),
                    "core_prediction": core_value,
                    "augmented_prediction": augmented,
                    "actual": y,
                }
            )

    core_df = pd.DataFrame(realised_core + pending_core)
    if len(core_df):
        core_df = core_df.set_index("origin_date").sort_index()
    return CandidateOverlayResult(
        horizon=horizon,
        predictions={name: pd.DataFrame(rows) for name, rows in predictions.items()},
        actuals=pd.DataFrame(actuals),
        overlay_edge_snapshots=pd.DataFrame(snapshots),
        overlay_edge_contributions=pd.DataFrame(realised_edges + pending_edges),
        survival_history=pd.DataFrame(survival_rows),
        gate_history=pd.DataFrame(gate_rows),
        model_contributions=pd.DataFrame(realised_model + pending_model),
        core_residuals=core_df,
    )
