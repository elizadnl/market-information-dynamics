import pandas as pd

from market_information_dynamics.statistics.overlay_gate import adaptive_overlay_gates


def test_overlay_gate_is_zero_for_harmful_overlay_and_positive_for_helpful_overlay():
    dates = pd.date_range("2025-01-01", periods=80)
    good = pd.DataFrame(
        {
            "realized_date": dates,
            "target": "good",
            "loss_improvement": [0.2] * len(dates),
        }
    )
    bad = pd.DataFrame(
        {
            "realized_date": dates,
            "target": "bad",
            "loss_improvement": [-0.2] * len(dates),
        }
    )
    data = pd.concat([good, bad], ignore_index=True)
    out = adaptive_overlay_gates(
        data,
        targets=["good", "bad"],
        as_of=pd.Timestamp("2025-04-01"),
        half_life_days=60,
        min_observations=20,
        t_scale=2.0,
    ).set_index("target")
    assert out.loc["good", "gate"] > 0.5
    assert out.loc["bad", "gate"] == 0.0
