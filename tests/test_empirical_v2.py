import numpy as np
import pandas as pd
import yaml

from market_information_dynamics.evaluation.empirical_v2 import run_empirical_v2


def test_empirical_v2_runs_small_multi_horizon_ablation(tmp_path):
    rng = np.random.default_rng(11)
    n = 190
    x = rng.normal(scale=0.4, size=n)
    y = np.zeros(n)
    p = rng.normal(scale=0.3, size=n)
    for t in range(1, n):
        y[t] = 0.45 * x[t - 1] + 0.1 * y[t - 1] + rng.normal(scale=0.35)
    frame = pd.DataFrame(
        {"x": x, "y": y, "p": p}, index=pd.date_range("2024-01-01", periods=n)
    )
    cfg = {
        "targets": ["y"],
        "horizons": [1, 5],
        "model": {
            "lags": 3,
            "alpha": 0.03,
            "ar_alpha": 1.0,
            "post_selection_ridge_alpha": 1.0,
            "min_train": 90,
            "refit_every": 20,
        },
        "survival": {
            "edge_threshold": 0.03,
            "structural_half_life_days": 120,
            "contribution_half_life_days": 60,
            "min_selection_frequency": 0.4,
            "min_sign_stability": 0.5,
            "min_strength_retention": 0.3,
            "min_contributions": 4,
            "min_survival_snapshots": 3,
            "max_edges_per_target": 4,
        },
        "evaluation": {
            "development_end": "2024-05-31",
            "reused_holdout_start": "2024-06-01",
        },
        "forecast_test": {
            "base_hac_lags": 3,
            "fdr_q": 0.10,
            "comparisons": [
                ["ar", "financial_direct_sparse"],
                ["financial_direct_sparse", "full_direct_sparse"],
                ["full_direct_sparse", "survival_refit_full"],
            ],
        },
    }
    path = tmp_path / "v2.yaml"
    path.write_text(yaml.safe_dump(cfg))
    result = run_empirical_v2(frame, financial_columns=["x", "y"], config_path=path)
    assert set(result.horizon_results) == {1, 5}
    assert set(result.metrics["horizon"]) == {1, 5}
    assert set(result.metrics["model"]) >= {
        "ar",
        "financial_direct_sparse",
        "full_direct_sparse",
        "survival_refit_full",
    }
    assert not result.forecast_tests.empty
