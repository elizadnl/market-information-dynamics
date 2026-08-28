from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from market_information_dynamics.evaluation.candidate_overlay import walk_forward_candidate_overlay


def run_overlay_demo(out_dir: str | Path = "artifacts") -> dict[str, Path]:
    """Controlled demonstration: useful candidate signal dies and the adaptive gate closes."""
    rng = np.random.default_rng(77)
    n = 900
    x = rng.normal(size=n)
    candidate = rng.normal(size=n)
    y = np.zeros(n)
    break_idx = 520
    for t in range(2, n):
        beta = 0.65 if t < break_idx else 0.0
        y[t] = (
            0.45 * x[t - 1]
            + 0.15 * y[t - 1]
            + beta * candidate[t - 1]
            + rng.normal(scale=0.5)
        )
    frame = pd.DataFrame(
        {"financial_x": x, "target": y, "candidate": candidate},
        index=pd.date_range("2022-01-01", periods=n),
    )
    result = walk_forward_candidate_overlay(
        frame,
        financial_columns=["financial_x", "target"],
        candidate_columns=["candidate"],
        target_columns=["target"],
        horizon=1,
        lags=2,
        alpha=0.03,
        min_train=260,
        refit_every=10,
        ar_alpha=1.0,
        overlay_alpha=0.03,
        overlay_min_train=80,
        overlay_ridge_alpha=1.0,
        edge_threshold=0.02,
        structural_half_life_days=100,
        contribution_half_life_days=70,
        min_selection_frequency=0.30,
        min_sign_stability=0.50,
        min_strength_retention=0.20,
        min_contributions=10,
        min_survival_snapshots=3,
        max_edges_per_target=1,
        gate_half_life_days=70,
        gate_min_observations=20,
        gate_t_scale=2.0,
    )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    gate = result.gate_history.loc[result.gate_history["target"] == "target"].copy()
    gate_path = out / "synthetic_candidate_overlay_gate.png"
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(pd.to_datetime(gate["date"]), gate["gate"], label="adaptive overlay gate")
    ax.axvline(frame.index[break_idx], linestyle="--", label="candidate signal removed")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("Protected-core overlay: useful signal is learned, then switched off")
    ax.set_xlabel("Forecast origin")
    ax.set_ylabel("Overlay gate")
    ax.legend()
    fig.tight_layout()
    fig.savefig(gate_path, dpi=160)
    plt.close(fig)

    actual = result.actuals["target"]
    rows = []
    for name, pred in result.predictions.items():
        paired = pd.concat([actual, pred["target"]], axis=1).dropna()
        err = paired.iloc[:, 0] - paired.iloc[:, 1]
        rows.append({"model": name, "rmse": float(np.sqrt(np.mean(err**2)))})
    comparison = pd.DataFrame(rows).sort_values("rmse")
    comparison_path = out / "synthetic_candidate_overlay_comparison.csv"
    comparison.to_csv(comparison_path, index=False)
    gate_csv = out / "synthetic_candidate_overlay_gate.csv"
    gate.to_csv(gate_csv, index=False)
    return {"figure": gate_path, "comparison": comparison_path, "gate": gate_csv}
