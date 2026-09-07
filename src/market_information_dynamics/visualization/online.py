from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def plot_expert_weights(
    history: pd.DataFrame,
    *,
    target: str,
    horizon: int,
    output: str | Path,
) -> Path:
    data = history.loc[
        (history["target"] == target) & (history["horizon"] == int(horizon))
    ].copy()
    if data.empty:
        raise ValueError("no matching weight history")
    data["date"] = pd.to_datetime(data["date"])
    wide = data.pivot_table(index="date", columns="expert", values="weight", aggfunc="last")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for col in wide.columns:
        ax.plot(wide.index, wide[col], label=col)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Online expert weight")
    ax.set_title(f"Expert trust lifecycle — {target}, h={horizon}")
    ax.legend(loc="best")
    fig.tight_layout()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
