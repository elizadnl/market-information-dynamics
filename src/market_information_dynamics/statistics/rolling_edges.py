from __future__ import annotations

import pandas as pd

from market_information_dynamics.models.sparse_var import SparseVAR


def rolling_edge_snapshots(
    frame: pd.DataFrame,
    *,
    window: int = 400,
    step: int = 20,
    lags: int = 3,
    alpha: float = 0.035,
) -> pd.DataFrame:
    """Estimate sparse predictive networks on fixed-width rolling windows."""
    if window <= lags:
        raise ValueError("window must exceed lags")
    rows = []
    for end in range(window, len(frame) + 1, step):
        sample = frame.iloc[end - window : end]
        model = SparseVAR(lags=lags, alpha=alpha).fit(sample)
        date = sample.index[-1]
        for source in frame.columns:
            for target in frame.columns:
                if source == target:
                    continue
                rows.append(
                    {
                        "date": date,
                        "source": source,
                        "target": target,
                        "strength": float(model.adjacency_.loc[source, target]),
                        "signed_weight": float(model.signed_adjacency_.loc[source, target]),
                    }
                )
    return pd.DataFrame(rows)
