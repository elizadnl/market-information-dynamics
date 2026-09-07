from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_information_dynamics.data.synthetic import generate_regime_switching_system
from market_information_dynamics.evaluation.baselines import walk_forward_univariate_ar
from market_information_dynamics.evaluation.walk_forward import walk_forward_sparse_var
from market_information_dynamics.models.sparse_var import SparseVAR
from market_information_dynamics.statistics.edge_stability import summarise_edge_stability
from market_information_dynamics.statistics.rolling_edges import rolling_edge_snapshots
from market_information_dynamics.visualization.lifecycle import save_edge_lifecycle_plot
from market_information_dynamics.visualization.network import save_network_plot


def _metric_table(actual: pd.DataFrame, prediction: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in actual.columns:
        y = actual[col]
        p = prediction[col]
        rmse = float(np.sqrt(np.mean((y - p) ** 2)))
        mae = float(np.mean(np.abs(y - p)))
        direction = float(np.mean(np.sign(y) == np.sign(p)))
        corr = float(y.corr(p))
        rows.append({"variable": col, "rmse": rmse, "mae": mae, "directional_accuracy": direction, "corr": corr})
    return pd.DataFrame(rows).set_index("variable")


def run_demo(
    out_dir: str | Path = "artifacts",
    *,
    n_obs: int = 1800,
    seed: int = 7,
    lags: int = 3,
    alpha: float = 0.035,
    min_train: int = 500,
    refit_every: int = 20,
    edge_threshold: float = 0.05,
) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    data = generate_regime_switching_system(n_obs=n_obs, seed=seed)
    result = walk_forward_sparse_var(
        data,
        lags=lags,
        alpha=alpha,
        min_train=min_train,
        refit_every=refit_every,
    )
    sparse_metrics = result.metrics().add_prefix("sparse_var_")
    ar_pred = walk_forward_univariate_ar(
        data,
        lags=lags,
        min_train=min_train,
        refit_every=refit_every,
    )
    ar_metrics = _metric_table(result.actuals, ar_pred).add_prefix("ar_")
    comparison = sparse_metrics.join(ar_metrics)
    comparison["rmse_skill_vs_ar"] = 1 - comparison["sparse_var_rmse"] / comparison["ar_rmse"]

    stability = summarise_edge_stability(result.edge_snapshots, threshold=edge_threshold)
    rolling = rolling_edge_snapshots(data, window=400, step=20, lags=lags, alpha=alpha)
    latest_model = SparseVAR(lags=lags, alpha=alpha).fit(data)
    edges = latest_model.edge_table(threshold=edge_threshold)

    paths = {
        "metrics": out / "synthetic_model_comparison.csv",
        "stability": out / "synthetic_edge_stability.csv",
        "rolling_edges": out / "synthetic_rolling_edges.csv",
        "edges": out / "synthetic_latest_edges.csv",
        "predictions": out / "synthetic_predictions.csv",
        "network": out / "synthetic_information_network.png",
        "lifecycle": out / "synthetic_edge_lifecycle.png",
    }
    comparison.to_csv(paths["metrics"])
    stability.to_csv(paths["stability"], index=False)
    rolling.to_csv(paths["rolling_edges"], index=False)
    edges.to_csv(paths["edges"], index=False)
    pd.concat({"actual": result.actuals, "sparse_var": result.predictions, "ar": ar_pred}, axis=1).to_csv(
        paths["predictions"]
    )
    save_network_plot(edges, paths["network"], top_n=10)
    save_edge_lifecycle_plot(
        rolling,
        [("physical", "commodity"), ("commodity", "fx")],
        paths["lifecycle"],
        title="Synthetic validation: one edge dies while another strengthens",
    )
    return paths
