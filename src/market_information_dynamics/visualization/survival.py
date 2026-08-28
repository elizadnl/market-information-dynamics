from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_horizon_skill(metrics: pd.DataFrame, output: str | Path, *, segment: str) -> Path:
    view = metrics.loc[metrics["segment"] == segment]
    pivot = view.pivot_table(
        index="horizon", columns="model", values="rmse_skill_vs_ar", aggfunc="mean"
    ).sort_index()
    ax = pivot.plot(marker="o", figsize=(9, 5))
    ax.axhline(0.0, linewidth=1)
    ax.set_title(f"Mean OOS RMSE skill vs direct AR — {segment}")
    ax.set_xlabel("Forecast horizon (trading days)")
    ax.set_ylabel("RMSE skill vs AR")
    fig = ax.get_figure()
    fig.tight_layout()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_survival_lifecycle(
    history: pd.DataFrame,
    *,
    source: str,
    target: str,
    horizon: int,
    output: str | Path,
) -> Path | None:
    view = history.loc[
        (history["source"] == source)
        & (history["target"] == target)
        & (history["horizon"] == horizon)
    ].sort_values("date")
    if view.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(pd.to_datetime(view["date"]), view["survival_score"], label="survival score")
    ax.plot(
        pd.to_datetime(view["date"]),
        view["weighted_selection_frequency"],
        label="selection persistence",
        alpha=0.8,
    )
    ax.set_ylim(bottom=0)
    ax.set_title(f"Signal lifecycle: {source} → {target}, h={horizon}")
    ax.set_xlabel("Forecast origin")
    ax.set_ylabel("Score")
    ax.legend()
    fig.tight_layout()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
