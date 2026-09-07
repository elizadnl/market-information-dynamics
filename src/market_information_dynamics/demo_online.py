from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from market_information_dynamics.online.fixed_share import fixed_share_forecast


def run_online_demo(out_dir: str | Path = "artifacts") -> dict[str, Path]:
    rng = np.random.default_rng(7)
    n = 900
    dates = pd.bdate_range("2022-01-03", periods=n)
    y = rng.normal(0, 1, n)

    # Core is consistently competent. Candidate overlay is excellent early, then its
    # relationship breaks and it becomes materially worse.
    core = y + rng.normal(0, 0.75, n)
    candidate = y + rng.normal(0, 0.40, n)
    candidate[450:] = y[450:] + rng.normal(0, 1.25, n - 450)

    actuals = pd.DataFrame({"target": y}, index=dates)
    experts = {
        "financial_core": pd.DataFrame({"target": core}, index=dates),
        "candidate_overlay": pd.DataFrame({"target": candidate}, index=dates),
    }
    result = fixed_share_forecast(actuals, experts, horizon=5, share=1.0 / 252.0)
    weights = result.weights

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "synthetic_fixed_share_weights.csv"
    weights.to_csv(csv_path, index=False)

    wide = weights.pivot_table(index="date", columns="expert", values="weight", aggfunc="last")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for col in wide.columns:
        ax.plot(pd.to_datetime(wide.index), wide[col], label=col)
    ax.axvline(dates[450], linestyle="--", linewidth=1)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Expert weight")
    ax.set_title("Fixed-Share adapts after candidate signal death")
    ax.legend(loc="best")
    fig.tight_layout()
    fig_path = out / "synthetic_fixed_share_regime_switch.png"
    fig.savefig(fig_path, dpi=160)
    plt.close(fig)
    return {"weights": csv_path, "figure": fig_path}
