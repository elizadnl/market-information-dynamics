from pathlib import Path

import pandas as pd

from market_information_dynamics.data.synthetic import generate_regime_switching_system
from market_information_dynamics.evaluation.empirical import run_empirical_v1


def test_empirical_v1_runs_paired_ablation(tmp_path: Path):
    frame = generate_regime_switching_system(n_obs=520, seed=12)
    # Treat the first four nodes as the "financial" subset and the remaining nodes as
    # additional physical/information predictors. This test checks mechanics, not economics.
    financial = ["commodity", "fx", "equity", "rates"]
    cfg = tmp_path / "empirical.yaml"
    cfg.write_text(
        """
targets: [commodity, fx, equity, rates]
model:
  lags: 3
  alpha: 0.035
  ar_alpha: 1.0
  min_train: 260
  refit_every: 40
stability:
  edge_threshold: 0.05
  min_selection_frequency: 0.50
  min_sign_stability: 0.60
  min_snapshots: 3
forecast_test:
  hac_lags: 3
  fdr_q: 0.10
"""
    )
    result = run_empirical_v1(frame, financial_columns=financial, config_path=cfg)
    assert set(result.metrics["model"]) == {
        "ar",
        "financial_sparse_var",
        "full_sparse_var",
        "stability_filtered_full",
    }
    assert list(result.actuals.columns) == financial
    assert len(result.forecast_tests) == len(financial)
    assert not result.edge_stability.empty
