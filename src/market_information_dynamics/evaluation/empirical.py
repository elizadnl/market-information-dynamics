from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from market_information_dynamics.evaluation.baselines import walk_forward_univariate_ar
from market_information_dynamics.evaluation.walk_forward import walk_forward_sparse_var
from market_information_dynamics.models.sparse_var import SparseVAR
from market_information_dynamics.statistics.edge_stability import summarise_edge_stability
from market_information_dynamics.statistics.forecast_tests import compare_forecasts_with_fdr


@dataclass
class EmpiricalV1Result:
    metrics: pd.DataFrame
    predictions: dict[str, pd.DataFrame]
    actuals: pd.DataFrame
    full_edges: pd.DataFrame
    edge_stability: pd.DataFrame
    forecast_tests: pd.DataFrame


def _metric_table(
    actuals: pd.DataFrame,
    predictions: dict[str, pd.DataFrame],
    *,
    segment: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for model_name, pred in predictions.items():
        for col in actuals.columns:
            paired = pd.concat([actuals[col].rename("y"), pred[col].rename("p")], axis=1).dropna()
            if paired.empty:
                continue
            error = paired["y"] - paired["p"]
            rows.append(
                {
                    "segment": segment,
                    "model": model_name,
                    "variable": col,
                    "n": int(len(paired)),
                    "rmse": float(np.sqrt(np.mean(error**2))),
                    "mae": float(np.mean(np.abs(error))),
                    "directional_accuracy": float(
                        np.mean(np.sign(paired["y"]) == np.sign(paired["p"]))
                    ),
                    "corr": float(paired["y"].corr(paired["p"])) if len(paired) > 2 else np.nan,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    baseline = out.loc[out["model"] == "ar", ["segment", "variable", "rmse"]].rename(
        columns={"rmse": "ar_rmse"}
    )
    out = out.merge(baseline, on=["segment", "variable"], how="left")
    out["rmse_skill_vs_ar"] = 1.0 - out["rmse"] / out["ar_rmse"]
    return out.sort_values(["variable", "model"]).reset_index(drop=True)


def _stability_mask(
    snapshots: pd.DataFrame,
    columns: list[str],
    *,
    threshold: float,
    min_selection_frequency: float,
    min_sign_stability: float,
) -> pd.DataFrame:
    summary = summarise_edge_stability(snapshots, threshold=threshold)
    mask = pd.DataFrame(False, index=columns, columns=columns)
    for col in columns:
        mask.loc[col, col] = True
    keep = summary.loc[
        (summary["selection_frequency"] >= min_selection_frequency)
        & (summary["sign_stability"].fillna(0.0) >= min_sign_stability)
    ]
    for row in keep.itertuples(index=False):
        mask.loc[row.source, row.target] = True
    return mask


def walk_forward_stability_filtered(
    frame: pd.DataFrame,
    *,
    target_columns: list[str],
    lags: int,
    alpha: float,
    min_train: int,
    refit_every: int,
    edge_threshold: float,
    min_selection_frequency: float,
    min_sign_stability: float,
    min_snapshots: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Expanding forecast whose cross-series coefficients must survive prior refits.

    The stability mask at time ``t`` is built only from models fitted no later than ``t``.
    Before enough snapshots exist, the unfiltered sparse VAR is used rather than inventing
    confidence from an undersized history.
    """
    predictions: list[pd.Series] = []
    snapshot_rows: list[dict[str, object]] = []
    model: SparseVAR | None = None
    mask: pd.DataFrame | None = None

    for i in range(min_train, len(frame)):
        if model is None or (i - min_train) % refit_every == 0:
            model = SparseVAR(lags=lags, alpha=alpha).fit(frame.iloc[:i])
            date = frame.index[i]
            for source in frame.columns:
                for target in frame.columns:
                    if source == target:
                        continue
                    snapshot_rows.append(
                        {
                            "date": date,
                            "source": source,
                            "target": target,
                            "strength": float(model.adjacency_.loc[source, target]),
                            "signed_weight": float(model.signed_adjacency_.loc[source, target]),
                        }
                    )
            snapshots = pd.DataFrame(snapshot_rows)
            n_dates = snapshots["date"].nunique()
            mask = None
            if n_dates >= min_snapshots:
                mask = _stability_mask(
                    snapshots,
                    list(frame.columns),
                    threshold=edge_threshold,
                    min_selection_frequency=min_selection_frequency,
                    min_sign_stability=min_sign_stability,
                )

        if mask is None:
            pred = model.predict_next(frame.iloc[:i])
        else:
            pred = model.predict_next_masked(frame.iloc[:i], mask)
        pred.name = frame.index[i]
        predictions.append(pred[target_columns])

    return pd.DataFrame(predictions), pd.DataFrame(snapshot_rows)


def run_empirical_v1(
    full_panel: pd.DataFrame,
    *,
    financial_columns: list[str],
    config_path: str | Path = "configs/empirical_v1.yaml",
) -> EmpiricalV1Result:
    config = yaml.safe_load(Path(config_path).read_text())
    model_cfg = config["model"]
    stability_cfg = config["stability"]
    test_cfg = config["forecast_test"]

    target_columns = [c for c in config["targets"] if c in financial_columns]
    if not target_columns:
        raise ValueError("no configured targets are present in financial_columns")

    # One common complete panel and one common OOS calendar make all model losses paired.
    full = full_panel.dropna(how="any").copy()
    financial = full[financial_columns].copy()
    lags = int(model_cfg["lags"])
    alpha = float(model_cfg["alpha"])
    min_train = int(model_cfg["min_train"])
    refit_every = int(model_cfg["refit_every"])

    if len(full) <= min_train:
        raise ValueError(f"complete panel has {len(full)} rows but min_train={min_train}")

    ar_pred = walk_forward_univariate_ar(
        financial[target_columns],
        lags=lags,
        min_train=min_train,
        refit_every=refit_every,
        alpha=float(model_cfg.get("ar_alpha", 1.0)),
    )
    financial_result = walk_forward_sparse_var(
        financial,
        lags=lags,
        alpha=alpha,
        min_train=min_train,
        refit_every=refit_every,
    )
    full_result = walk_forward_sparse_var(
        full,
        lags=lags,
        alpha=alpha,
        min_train=min_train,
        refit_every=refit_every,
    )
    stable_pred, _ = walk_forward_stability_filtered(
        full,
        target_columns=target_columns,
        lags=lags,
        alpha=alpha,
        min_train=min_train,
        refit_every=refit_every,
        edge_threshold=float(stability_cfg["edge_threshold"]),
        min_selection_frequency=float(stability_cfg["min_selection_frequency"]),
        min_sign_stability=float(stability_cfg["min_sign_stability"]),
        min_snapshots=int(stability_cfg.get("min_snapshots", 5)),
    )

    actuals = full_result.actuals[target_columns]
    predictions = {
        "ar": ar_pred.reindex(actuals.index)[target_columns],
        "financial_sparse_var": financial_result.predictions.reindex(actuals.index)[target_columns],
        "full_sparse_var": full_result.predictions.reindex(actuals.index)[target_columns],
        "stability_filtered_full": stable_pred.reindex(actuals.index)[target_columns],
    }
    metric_parts = [_metric_table(actuals, predictions, segment="oos_all")]
    evaluation_cfg = config.get("evaluation", {})
    final_holdout_start = evaluation_cfg.get("final_holdout_start")
    test_actuals = actuals
    test_predictions = predictions
    if final_holdout_start:
        cutoff = pd.Timestamp(final_holdout_start)
        holdout_actuals = actuals.loc[actuals.index >= cutoff]
        if len(holdout_actuals) >= 20:
            holdout_predictions = {
                name: pred.reindex(holdout_actuals.index) for name, pred in predictions.items()
            }
            metric_parts.append(
                _metric_table(holdout_actuals, holdout_predictions, segment="final_holdout")
            )
            test_actuals = holdout_actuals
            test_predictions = holdout_predictions
    metrics = pd.concat(metric_parts, ignore_index=True)
    stability = summarise_edge_stability(
        full_result.edge_snapshots,
        threshold=float(stability_cfg["edge_threshold"]),
    )
    forecast_tests = compare_forecasts_with_fdr(
        test_actuals,
        test_predictions["financial_sparse_var"],
        test_predictions["full_sparse_var"],
        q=float(test_cfg["fdr_q"]),
        hac_lags=int(test_cfg["hac_lags"]),
    )
    return EmpiricalV1Result(
        metrics=metrics,
        predictions=predictions,
        actuals=actuals,
        full_edges=full_result.edge_snapshots,
        edge_stability=stability,
        forecast_tests=forecast_tests,
    )
