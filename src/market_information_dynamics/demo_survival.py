from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from market_information_dynamics.evaluation.multi_horizon import walk_forward_signal_survival


def run_survival_demo(out_dir: str | Path = "artifacts") -> dict[str, Path]:
    """Controlled example where an edge stays selected after it stops helping forecasts."""
    rng = np.random.default_rng(42)
    n = 900
    x = rng.normal(size=n)
    y = np.zeros(n)
    noise = rng.normal(size=n)
    regime_change = 550
    for t in range(1, n):
        beta = 0.8 if t < regime_change else -0.7
        y[t] = beta * x[t - 1] + 0.1 * y[t - 1] + rng.normal(scale=0.6)
    frame = pd.DataFrame(
        {"x": x, "y": y, "noise": noise},
        index=pd.bdate_range("2020-01-01", periods=n),
    )

    result = walk_forward_signal_survival(
        frame,
        financial_columns=["x", "y"],
        target_columns=["y"],
        horizon=1,
        lags=3,
        alpha=0.03,
        min_train=300,
        refit_every=20,
        ar_alpha=1.0,
        ridge_alpha=1.0,
        edge_threshold=0.05,
        structural_half_life_days=180,
        contribution_half_life_days=90,
        min_selection_frequency=0.5,
        min_sign_stability=0.6,
        min_strength_retention=0.3,
        min_contributions=20,
        min_survival_snapshots=4,
        max_edges_per_target=4,
    )
    history = result.survival_history.loc[
        (result.survival_history["source"] == "x")
        & (result.survival_history["target"] == "y")
    ].copy()

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "synthetic_signal_survival.csv"
    history.to_csv(csv_path, index=False)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    dates = pd.to_datetime(history["date"])
    ax.plot(dates, history["weighted_selection_frequency"], label="LASSO selection persistence")
    ax.plot(dates, history["survival_score"], label="predictive survival score")
    ax.axvline(frame.index[regime_change], linestyle="--", linewidth=1, label="true regime change")
    ax.set_ylim(-0.02, 1.05)
    ax.set_title("A coefficient can remain persistent after predictive value dies")
    ax.set_xlabel("Date")
    ax.set_ylabel("Score")
    ax.legend()
    fig.tight_layout()
    plot_path = out / "synthetic_signal_survival.png"
    fig.savefig(plot_path, dpi=170)
    plt.close(fig)
    return {"csv": csv_path, "plot": plot_path}
