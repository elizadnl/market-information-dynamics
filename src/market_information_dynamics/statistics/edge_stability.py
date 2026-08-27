from __future__ import annotations

import numpy as np
import pandas as pd


def summarise_edge_stability(
    snapshots: pd.DataFrame,
    threshold: float = 0.05,
    recent_n: int | None = None,
) -> pd.DataFrame:
    """Summarise edge survival and sign stability over model refits."""
    required = {"date", "source", "target", "strength", "signed_weight"}
    missing = required.difference(snapshots.columns)
    if missing:
        raise KeyError(f"Missing snapshot columns: {sorted(missing)}")

    data = snapshots.sort_values("date").copy()
    if recent_n is not None:
        dates = data["date"].drop_duplicates().sort_values()
        data = data[data["date"].isin(dates.iloc[-recent_n:])]

    rows = []
    for (source, target), g in data.groupby(["source", "target"], sort=False):
        selected = g["strength"] >= threshold
        selected_weights = g.loc[selected, "signed_weight"]
        sign_stability = np.nan
        if len(selected_weights):
            signs = np.sign(selected_weights)
            sign_stability = float(max(np.mean(signs > 0), np.mean(signs < 0)))
        rows.append(
            {
                "source": source,
                "target": target,
                "selection_frequency": float(selected.mean()),
                "mean_strength": float(g["strength"].mean()),
                "latest_strength": float(g.iloc[-1]["strength"]),
                "sign_stability": sign_stability,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["selection_frequency", "mean_strength"], ascending=False, ignore_index=True
    )
