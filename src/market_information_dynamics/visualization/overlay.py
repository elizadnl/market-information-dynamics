from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_gate_lifecycle(
    gate_history: pd.DataFrame,
    *,
    target: str,
    horizon: int,
    output: str | Path,
) -> Path | None:
    view = gate_history.loc[
        (gate_history["target"] == target) & (gate_history["horizon"] == horizon)
    ].sort_values("date")
    if view.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(pd.to_datetime(view["date"]), view["gate"], label="adaptive overlay gate")
    ax.axhline(0.0, linewidth=1)
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(f"Candidate-overlay trust: {target}, h={horizon}")
    ax.set_xlabel("Forecast origin")
    ax.set_ylabel("Gate weight")
    ax.legend()
    fig.tight_layout()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
