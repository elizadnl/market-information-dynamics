from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _exp_weights(dates: pd.Series, as_of: pd.Timestamp, half_life_days: float) -> np.ndarray:
    ages = (as_of - pd.to_datetime(dates)).dt.total_seconds().to_numpy() / 86400.0
    ages = np.maximum(ages, 0.0)
    return np.exp(-math.log(2.0) * ages / max(float(half_life_days), 1e-9))


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    if len(values) == 0 or float(weights.sum()) <= 0:
        return float("nan")
    return float(np.average(values, weights=weights))


def _weighted_t_stat(values: np.ndarray, weights: np.ndarray) -> float:
    if len(values) < 2 or float(weights.sum()) <= 0:
        return float("nan")
    mean = _weighted_mean(values, weights)
    variance = _weighted_mean((values - mean) ** 2, weights)
    effective_n = float(weights.sum() ** 2 / np.sum(weights**2))
    if variance <= 0 or effective_n <= 1:
        return 0.0
    return float(mean / math.sqrt(variance / effective_n))


def edge_survival_table(
    snapshots: pd.DataFrame,
    contributions: pd.DataFrame,
    *,
    as_of: pd.Timestamp,
    edge_threshold: float = 0.05,
    structural_half_life_days: float = 180.0,
    contribution_half_life_days: float = 120.0,
) -> pd.DataFrame:
    """Compute recency-weighted structural and realised-OOS edge diagnostics.

    ``contributions`` must contain only outcomes whose ``realized_date`` is strictly before
    the forecast origin. Positive ``loss_improvement`` means the edge reduced squared loss.
    """
    required_s = {"date", "source", "target", "strength", "signed_weight"}
    required_c = {"origin_date", "realized_date", "source", "target", "loss_improvement"}
    if not required_s.issubset(snapshots.columns):
        raise KeyError(f"missing snapshot columns: {sorted(required_s - set(snapshots.columns))}")
    if len(contributions) and not required_c.issubset(contributions.columns):
        raise KeyError(
            f"missing contribution columns: {sorted(required_c - set(contributions.columns))}"
        )

    snap = snapshots.loc[pd.to_datetime(snapshots["date"]) <= as_of].copy()
    contrib = contributions.copy()
    if len(contrib):
        contrib = contrib.loc[pd.to_datetime(contrib["realized_date"]) < as_of].copy()

    rows: list[dict[str, object]] = []
    for (source, target), g in snap.groupby(["source", "target"], sort=False):
        g = g.sort_values("date")
        sw = _exp_weights(g["date"], as_of, structural_half_life_days)
        selected = (g["strength"].to_numpy(dtype=float) >= edge_threshold).astype(float)
        selection_frequency = _weighted_mean(selected, sw)
        selected_mask = selected > 0

        sign_stability = float("nan")
        if selected_mask.any():
            signs = np.sign(g.loc[selected_mask, "signed_weight"].to_numpy(dtype=float))
            sign_w = sw[selected_mask]
            positive = _weighted_mean((signs > 0).astype(float), sign_w)
            negative = _weighted_mean((signs < 0).astype(float), sign_w)
            sign_stability = float(max(positive, negative))

        weighted_strength = _weighted_mean(g["strength"].to_numpy(dtype=float), sw)
        latest_strength = float(g.iloc[-1]["strength"])
        if not np.isfinite(weighted_strength) or weighted_strength <= 1e-12:
            strength_retention = 0.0
        else:
            strength_retention = float(latest_strength / weighted_strength)

        cg = contrib.loc[(contrib["source"] == source) & (contrib["target"] == target)]
        n_contributions = int(len(cg))
        mean_loss_improvement = float("nan")
        contribution_hit_rate = float("nan")
        contribution_t_stat = float("nan")
        if n_contributions:
            cw = _exp_weights(cg["realized_date"], as_of, contribution_half_life_days)
            values = cg["loss_improvement"].to_numpy(dtype=float)
            mean_loss_improvement = _weighted_mean(values, cw)
            contribution_hit_rate = _weighted_mean((values > 0).astype(float), cw)
            contribution_t_stat = _weighted_t_stat(values, cw)

        structural_component = (
            max(selection_frequency, 0.0)
            * max(0.0 if not np.isfinite(sign_stability) else sign_stability, 0.0)
            * min(max(strength_retention, 0.0), 1.0)
        )
        predictive_component = 0.0
        if np.isfinite(contribution_t_stat) and contribution_t_stat > 0:
            predictive_component = math.tanh(contribution_t_stat / 2.0)
        survival_score = float(structural_component * predictive_component)

        rows.append(
            {
                "source": source,
                "target": target,
                "weighted_selection_frequency": selection_frequency,
                "weighted_sign_stability": sign_stability,
                "weighted_mean_strength": weighted_strength,
                "latest_strength": latest_strength,
                "strength_retention": strength_retention,
                "n_contributions": n_contributions,
                "weighted_mean_loss_improvement": mean_loss_improvement,
                "contribution_hit_rate": contribution_hit_rate,
                "contribution_t_stat": contribution_t_stat,
                "survival_score": survival_score,
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["survival_score", "weighted_selection_frequency"], ascending=False, ignore_index=True
    )


def survival_mask(
    table: pd.DataFrame,
    *,
    sources: list[str],
    targets: list[str],
    min_selection_frequency: float,
    min_sign_stability: float,
    min_strength_retention: float,
    min_contributions: int,
    min_mean_loss_improvement: float = 0.0,
    max_edges_per_target: int | None = None,
) -> pd.DataFrame:
    mask = pd.DataFrame(False, index=sources, columns=targets)
    for target in targets:
        if target in sources:
            mask.loc[target, target] = True
    if table.empty:
        return mask

    eligible = table.loc[
        (table["weighted_selection_frequency"] >= min_selection_frequency)
        & (table["weighted_sign_stability"].fillna(0.0) >= min_sign_stability)
        & (table["strength_retention"] >= min_strength_retention)
        & (table["n_contributions"] >= int(min_contributions))
        & (table["weighted_mean_loss_improvement"].fillna(-np.inf) > min_mean_loss_improvement)
    ].copy()

    for target, g in eligible.groupby("target"):
        ranked = g.sort_values("survival_score", ascending=False)
        if max_edges_per_target is not None:
            ranked = ranked.head(int(max_edges_per_target))
        for row in ranked.itertuples(index=False):
            if row.source in mask.index and row.target in mask.columns:
                mask.loc[row.source, row.target] = True
    return mask
