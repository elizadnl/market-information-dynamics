import numpy as np
import pandas as pd
import yaml

from market_information_dynamics.evaluation.empirical_v3 import run_empirical_v3


def test_empirical_v3_runs_protected_core_overlay_ablation(tmp_path):
    rng = np.random.default_rng(5)
    n = 280
    x = rng.normal(scale=0.4, size=n)
    p = rng.normal(scale=0.4, size=n)
    y = np.zeros(n)
    for t in range(2, n):
        y[t] = 0.35 * x[t - 1] + 0.40 * p[t - 1] + rng.normal(scale=0.35)
    frame = pd.DataFrame(
        {"x": x, "y": y, "physical": p},
        index=pd.date_range("2024-01-01", periods=n),
    )
    cfg = {
        "targets": ["y"],
        "horizons": [1, 5],
        "model": {
            "lags": 2,
            "alpha": 0.03,
            "ar_alpha": 1.0,
            "min_train": 110,
            "refit_every": 10,
        },
        "overlay": {
            "alpha": 0.03,
            "min_oos_residuals": 35,
            "post_selection_ridge_alpha": 1.0,
        },
        "survival": {
            "edge_threshold": 0.02,
            "structural_half_life_days": 90,
            "contribution_half_life_days": 60,
            "min_selection_frequency": 0.3,
            "min_sign_stability": 0.5,
            "min_strength_retention": 0.2,
            "min_contributions": 5,
            "min_survival_snapshots": 2,
            "max_edges_per_target": 2,
        },
        "adaptive_gate": {
            "half_life_days": 60,
            "min_observations": 10,
            "t_scale": 2.0,
        },
        "evaluation": {
            "development_end": "2024-06-30",
            "reused_evaluation_start": "2024-07-01",
        },
        "forecast_test": {
            "base_hac_lags": 3,
            "fdr_q": 0.10,
            "comparisons": [
                ["ar", "financial_direct_sparse"],
                ["financial_direct_sparse", "candidate_overlay_sparse"],
                ["financial_direct_sparse", "candidate_overlay_survival"],
                ["financial_direct_sparse", "candidate_overlay_adaptive"],
            ],
        },
    }
    path = tmp_path / "v3.yaml"
    path.write_text(yaml.safe_dump(cfg))
    result = run_empirical_v3(frame, financial_columns=["x", "y"], config_path=path)
    assert set(result.horizon_results) == {1, 5}
    assert set(result.metrics["model"]) >= {
        "ar",
        "financial_direct_sparse",
        "candidate_overlay_sparse",
        "candidate_overlay_survival",
        "candidate_overlay_adaptive",
    }
    assert not result.forecast_tests.empty
    assert set(result.latest_gates.columns) >= {"target", "gate", "horizon"}
