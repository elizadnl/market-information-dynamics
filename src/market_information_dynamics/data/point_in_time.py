from __future__ import annotations

import pandas as pd


def build_point_in_time_panel(
    evaluation_times: pd.DatetimeIndex,
    releases: pd.DataFrame,
    *,
    feature_col: str = "feature",
    available_col: str = "available_at",
    value_col: str = "value",
) -> pd.DataFrame:
    """Create a panel using only values observable by each evaluation timestamp.

    `releases` may contain revisions. For each feature and evaluation time, the most
    recently *available* record is used. This is the basic anti-lookahead primitive
    for macro/alternative datasets with publication delays.
    """
    required = {feature_col, available_col, value_col}
    missing = required.difference(releases.columns)
    if missing:
        raise KeyError(f"Missing release columns: {sorted(missing)}")

    releases = releases.copy()
    releases[available_col] = pd.to_datetime(releases[available_col])
    evaluation = pd.DataFrame({"evaluation_time": pd.DatetimeIndex(evaluation_times)}).sort_values(
        "evaluation_time"
    )

    pieces: list[pd.Series] = []
    for feature, group in releases.groupby(feature_col, sort=True):
        g = group.sort_values(available_col)[[available_col, value_col]]
        merged = pd.merge_asof(
            evaluation,
            g,
            left_on="evaluation_time",
            right_on=available_col,
            direction="backward",
            allow_exact_matches=True,
        )
        pieces.append(merged.set_index("evaluation_time")[value_col].rename(str(feature)))

    if not pieces:
        return pd.DataFrame(index=evaluation_times)
    return pd.concat(pieces, axis=1).reindex(evaluation_times)
