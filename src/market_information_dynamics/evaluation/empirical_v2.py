from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from market_information_dynamics.evaluation.multi_horizon import (
    MultiHorizonResult,
    walk_forward_signal_survival,
)
from market_information_dynamics.statistics.nested_forecast_tests import nested_forecast_tests
from market_information_dynamics.statistics.signal_survival import edge_survival_table


@dataclass
class EmpiricalV2Result:
    horizon_results: dict[int, MultiHorizonResult]
    metrics: pd.DataFrame
    forecast_tests: pd.DataFrame
    latest_survival: pd.DataFrame


def _metrics_for_result(
    result: MultiHorizonResult,
    *,
    segment: str,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    actuals = result.actuals.copy()
    if start is not None:
        actuals = actuals.loc[actuals.index >= pd.Timestamp(start)]
    if end is not None:
        actuals = actuals.loc[actuals.index <= pd.Timestamp(end)]

    rows: list[dict[str, object]] = []
    for model_name, pred_all in result.predictions.items():
        pred = pred_all.reindex(actuals.index)
        for target in actuals.columns:
            paired = pd.concat(
                [actuals[target].rename("y"), pred[target].rename("p")], axis=1
            ).dropna()
            if not len(paired):
                continue
            error = paired["y"] - paired["p"]
            rows.append(
                {
                    "segment": segment,
                    "horizon": result.horizon,
                    "model": model_name,
                    "variable": target,
                    "n": int(len(paired)),
                    "rmse": float(np.sqrt(np.mean(error**2))),
                    "mae": float(np.mean(np.abs(error))),
                    "directional_accuracy": float(
                        np.mean(np.sign(paired["y"]) == np.sign(paired["p"]))
                    ),
                    "corr": float(paired["y"].corr(paired["p"]))
                    if len(paired) > 2
                    else np.nan,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    baseline = out.loc[
        out["model"] == "ar", ["segment", "horizon", "variable", "rmse"]
    ].rename(columns={"rmse": "ar_rmse"})
    out = out.merge(baseline, on=["segment", "horizon", "variable"], how="left")
    out["rmse_skill_vs_ar"] = 1.0 - out["rmse"] / out["ar_rmse"]
    return out


def run_empirical_v2(
    full_panel: pd.DataFrame,
    *,
    financial_columns: list[str],
    config_path: str | Path = "configs/empirical_v2.yaml",
) -> EmpiricalV2Result:
    config = yaml.safe_load(Path(config_path).read_text())
    model_cfg = config["model"]
    survival_cfg = config["survival"]
    evaluation_cfg = config["evaluation"]
    test_cfg = config["forecast_test"]

    full = full_panel.dropna(how="any").copy()
    target_columns = [c for c in config["targets"] if c in financial_columns]
    if not target_columns:
        raise ValueError("no configured targets are present in financial_columns")

    results: dict[int, MultiHorizonResult] = {}
    for horizon in [int(h) for h in config["horizons"]]:
        results[horizon] = walk_forward_signal_survival(
            full,
            financial_columns=financial_columns,
            target_columns=target_columns,
            horizon=horizon,
            lags=int(model_cfg["lags"]),
            alpha=float(model_cfg["alpha"]),
            min_train=int(model_cfg["min_train"]),
            refit_every=int(model_cfg["refit_every"]),
            ar_alpha=float(model_cfg.get("ar_alpha", 1.0)),
            ridge_alpha=float(model_cfg.get("post_selection_ridge_alpha", 1.0)),
            edge_threshold=float(survival_cfg["edge_threshold"]),
            structural_half_life_days=float(survival_cfg["structural_half_life_days"]),
            contribution_half_life_days=float(survival_cfg["contribution_half_life_days"]),
            min_selection_frequency=float(survival_cfg["min_selection_frequency"]),
            min_sign_stability=float(survival_cfg["min_sign_stability"]),
            min_strength_retention=float(survival_cfg["min_strength_retention"]),
            min_contributions=int(survival_cfg["min_contributions"]),
            min_survival_snapshots=int(survival_cfg["min_survival_snapshots"]),
            max_edges_per_target=(
                None
                if survival_cfg.get("max_edges_per_target") is None
                else int(survival_cfg["max_edges_per_target"])
            ),
        )

    metric_parts: list[pd.DataFrame] = []
    for result in results.values():
        metric_parts.append(_metrics_for_result(result, segment="oos_all"))
        dev_end = evaluation_cfg.get("development_end")
        if dev_end:
            metric_parts.append(
                _metrics_for_result(result, segment="development", end=str(dev_end))
            )
        reused_start = evaluation_cfg.get("reused_holdout_start")
        if reused_start:
            metric_parts.append(
                _metrics_for_result(
                    result, segment="reused_holdout", start=str(reused_start)
                )
            )
    metrics = pd.concat(metric_parts, ignore_index=True)

    comparisons = [tuple(x) for x in test_cfg["comparisons"]]
    tests = nested_forecast_tests(
        results,
        comparisons=comparisons,
        fdr_q=float(test_cfg["fdr_q"]),
        base_hac_lags=int(test_cfg["base_hac_lags"]),
        evaluation_start=evaluation_cfg.get("reused_holdout_start"),
    )

    latest_parts: list[pd.DataFrame] = []
    for horizon, result in results.items():
        if result.edge_snapshots.empty:
            continue
        as_of = pd.Timestamp(full.index[-1]) + pd.Timedelta(days=1)
        table = edge_survival_table(
            result.edge_snapshots,
            result.edge_contributions,
            as_of=as_of,
            edge_threshold=float(survival_cfg["edge_threshold"]),
            structural_half_life_days=float(survival_cfg["structural_half_life_days"]),
            contribution_half_life_days=float(survival_cfg["contribution_half_life_days"]),
        )
        if len(table):
            table.insert(0, "horizon", horizon)
            latest_parts.append(table)
    latest_survival = (
        pd.concat(latest_parts, ignore_index=True) if latest_parts else pd.DataFrame()
    )
    return EmpiricalV2Result(results, metrics, tests, latest_survival)
