from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _preferred_segment(metrics: pd.DataFrame) -> pd.DataFrame:
    if "segment" not in metrics.columns:
        return metrics
    segment = "final_holdout" if (metrics["segment"] == "final_holdout").any() else "oos_all"
    return metrics.loc[metrics["segment"] == segment].copy()


def plot_oos_skill(metrics: pd.DataFrame, output: str | Path) -> Path:
    data = _preferred_segment(metrics)
    data = data.loc[data["model"] != "ar"].copy()
    pivot = data.pivot(index="variable", columns="model", values="rmse_skill_vs_ar")
    fig, ax = plt.subplots(figsize=(10, max(4, 0.42 * len(pivot))))
    im = ax.imshow(pivot.to_numpy(), aspect="auto")
    ax.set_xticks(np.arange(len(pivot.columns)), labels=pivot.columns, rotation=25, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)), labels=pivot.index)
    ax.set_title("Out-of-sample RMSE skill versus target-only AR")
    fig.colorbar(im, ax=ax, label="1 - RMSE(model) / RMSE(AR)")
    fig.tight_layout()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_physical_incremental_skill(metrics: pd.DataFrame, output: str | Path) -> Path:
    data = _preferred_segment(metrics)
    pivot = data.pivot(index="variable", columns="model", values="rmse")
    required = {"financial_sparse_var", "full_sparse_var"}
    if not required.issubset(pivot.columns):
        raise KeyError(f"metrics missing required models: {sorted(required.difference(pivot.columns))}")
    skill = 1.0 - pivot["full_sparse_var"] / pivot["financial_sparse_var"]
    skill = skill.sort_values()
    fig, ax = plt.subplots(figsize=(9, max(4, 0.4 * len(skill))))
    ax.barh(skill.index, skill.values)
    ax.axvline(0.0, linewidth=1)
    ax.set_xlabel("Incremental RMSE skill from physical layer")
    ax.set_title("Does PortWatch improve financial-only forecasts?")
    fig.tight_layout()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path
