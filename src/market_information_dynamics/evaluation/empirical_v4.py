from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import yaml

from market_information_dynamics.online.fixed_share import fixed_share_forecast
from market_information_dynamics.statistics.nested_forecast_tests import nested_forecast_tests


@dataclass
class EmpiricalV4HorizonResult:
    horizon: int
    actuals: pd.DataFrame
    predictions: dict[str, pd.DataFrame]
    weight_history: pd.DataFrame
    realised_losses: pd.DataFrame


@dataclass
class EmpiricalV4Result:
    horizon_results: dict[int, EmpiricalV4HorizonResult]
    metrics: pd.DataFrame
    forecast_tests: pd.DataFrame
    latest_weights: pd.DataFrame
    share_sensitivity: pd.DataFrame


def _read_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.DatetimeIndex(frame.index)
    return frame


def _metric_rows(
    result: EmpiricalV4HorizonResult,
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
    for model, prediction in result.predictions.items():
        pred = prediction.reindex(actuals.index)
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
                    "model": model,
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


def _skill_vs_core(
    actuals: pd.DataFrame, core: pd.DataFrame, challenger: pd.DataFrame, *, start: str | None
) -> tuple[float, int]:
    if start is not None:
        actuals = actuals.loc[actuals.index >= pd.Timestamp(start)]
    skills: list[float] = []
    for target in actuals.columns:
        paired = pd.concat(
            [actuals[target], core[target], challenger[target]], axis=1
        ).dropna()
        if not len(paired):
            continue
        y, b, c = (paired.iloc[:, i].to_numpy(dtype=float) for i in range(3))
        b_rmse = float(np.sqrt(np.mean((y - b) ** 2)))
        c_rmse = float(np.sqrt(np.mean((y - c) ** 2)))
        if b_rmse > 0:
            skills.append(1.0 - c_rmse / b_rmse)
    return (float(np.mean(skills)) if skills else np.nan, int(sum(x > 0 for x in skills)))


def run_empirical_v4(
    *,
    v3_dir: str | Path = "artifacts/empirical_v3",
    config_path: str | Path = "configs/empirical_v4.yaml",
) -> EmpiricalV4Result:
    """Apply a causal Fixed-Share combiner to already-generated v3 forecast experts."""
    config = yaml.safe_load(Path(config_path).read_text())
    v3 = Path(v3_dir)
    online = config["online_aggregation"]
    evaluation = config["evaluation"]
    primary_share = float(online["share"])
    experts = list(online["experts"])

    results: dict[int, EmpiricalV4HorizonResult] = {}
    sensitivity_rows: list[dict[str, object]] = []

    for horizon in [int(h) for h in config["horizons"]]:
        h_dir = v3 / f"h{horizon}"
        actuals = _read_frame(h_dir / "actuals.csv")
        base_predictions = {
            "ar": _read_frame(h_dir / "predictions_ar.csv"),
            "financial_direct_sparse": _read_frame(
                h_dir / "predictions_financial_direct_sparse.csv"
            ),
            "candidate_overlay_survival": _read_frame(
                h_dir / "predictions_candidate_overlay_survival.csv"
            ),
            "candidate_overlay_adaptive": _read_frame(
                h_dir / "predictions_candidate_overlay_adaptive.csv"
            ),
        }
        expert_frames = {name: base_predictions[name] for name in experts}
        agg = fixed_share_forecast(
            actuals,
            expert_frames,
            horizon=horizon,
            share=primary_share,
            loss_scale_window=int(online["loss_scale_window"]),
            loss_clip=float(online["loss_clip"]),
        )
        predictions = dict(base_predictions)
        predictions["online_fixed_share"] = agg.prediction
        results[horizon] = EmpiricalV4HorizonResult(
            horizon=horizon,
            actuals=actuals,
            predictions=predictions,
            weight_history=agg.weights,
            realised_losses=agg.realised_losses,
        )

        for share in [float(x) for x in online.get("share_sensitivity", [primary_share])]:
            diagnostic = fixed_share_forecast(
                actuals,
                expert_frames,
                horizon=horizon,
                share=share,
                loss_scale_window=int(online["loss_scale_window"]),
                loss_clip=float(online["loss_clip"]),
            )
            skill, n_better = _skill_vs_core(
                actuals,
                base_predictions["financial_direct_sparse"],
                diagnostic.prediction,
                start=evaluation.get("reused_evaluation_start"),
            )
            sensitivity_rows.append(
                {
                    "horizon": horizon,
                    "share": share,
                    "mean_rmse_skill_vs_financial_core": skill,
                    "targets_better": n_better,
                    "n_targets": len(actuals.columns),
                }
            )

    metric_parts: list[pd.DataFrame] = []
    for result in results.values():
        metric_parts.append(_metric_rows(result, segment="oos_all"))
        if evaluation.get("development_end"):
            metric_parts.append(
                _metric_rows(
                    result, segment="development", end=str(evaluation["development_end"])
                )
            )
        if evaluation.get("reused_evaluation_start"):
            metric_parts.append(
                _metric_rows(
                    result,
                    segment="reused_evaluation",
                    start=str(evaluation["reused_evaluation_start"]),
                )
            )
    metrics = pd.concat(metric_parts, ignore_index=True)

    # nested_forecast_tests only requires objects exposing actuals/predictions.
    lightweight = {
        h: SimpleNamespace(actuals=r.actuals, predictions=r.predictions)
        for h, r in results.items()
    }
    tests = nested_forecast_tests(
        lightweight,
        comparisons=[tuple(x) for x in config["forecast_test"]["comparisons"]],
        fdr_q=float(config["forecast_test"]["fdr_q"]),
        base_hac_lags=int(config["forecast_test"]["base_hac_lags"]),
        evaluation_start=evaluation.get("reused_evaluation_start"),
    )

    latest_parts: list[pd.DataFrame] = []
    for horizon, result in results.items():
        if result.weight_history.empty:
            continue
        latest_date = pd.to_datetime(result.weight_history["date"]).max()
        latest = result.weight_history.loc[
            pd.to_datetime(result.weight_history["date"]) == latest_date
        ].copy()
        latest_parts.append(latest)
    latest_weights = pd.concat(latest_parts, ignore_index=True) if latest_parts else pd.DataFrame()

    return EmpiricalV4Result(
        horizon_results=results,
        metrics=metrics,
        forecast_tests=tests,
        latest_weights=latest_weights,
        share_sensitivity=pd.DataFrame(sensitivity_rows),
    )
