from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def save_edge_lifecycle_plot(
    snapshots: pd.DataFrame,
    edges: list[tuple[str, str]],
    path: str | Path,
    *,
    title: str = "Predictive edge lifecycle",
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for source, target in edges:
        g = snapshots[(snapshots["source"] == source) & (snapshots["target"] == target)]
        ax.plot(g["date"], g["strength"], label=f"{source} → {target}")
    ax.axhline(0, linewidth=0.8)
    ax.set_ylabel("standardised edge strength")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
