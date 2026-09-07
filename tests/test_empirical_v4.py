from pathlib import Path
import numpy as np
import pandas as pd
import yaml

from market_information_dynamics.evaluation.empirical_v4 import run_empirical_v4


def test_empirical_v4_reads_v3_artifacts_and_builds_online_forecast(tmp_path: Path):
    v3 = tmp_path / "v3"
    idx = pd.bdate_range("2023-01-02", periods=220)
    rng = np.random.default_rng(4)
    for h in [1, 5]:
        d = v3 / f"h{h}"
        d.mkdir(parents=True)
        y = pd.DataFrame({"x": rng.normal(size=len(idx))}, index=idx)
        ar = pd.DataFrame({"x": rng.normal(scale=0.05, size=len(idx))}, index=idx)
        core = y + rng.normal(scale=0.8, size=y.shape)
        cand = y + rng.normal(scale=0.6, size=y.shape)
        adaptive = (core + cand) / 2
        y.to_csv(d / "actuals.csv")
        ar.to_csv(d / "predictions_ar.csv")
        core.to_csv(d / "predictions_financial_direct_sparse.csv")
        cand.to_csv(d / "predictions_candidate_overlay_survival.csv")
        adaptive.to_csv(d / "predictions_candidate_overlay_adaptive.csv")

    cfg = {
        "horizons": [1, 5],
        "online_aggregation": {
            "experts": ["financial_direct_sparse", "candidate_overlay_survival"],
            "share": 1 / 252,
            "share_sensitivity": [0.0, 1 / 252],
            "loss_scale_window": 50,
            "loss_clip": 5.0,
        },
        "evaluation": {
            "development_end": "2023-08-01",
            "reused_evaluation_start": "2023-08-02",
        },
        "forecast_test": {
            "base_hac_lags": 2,
            "fdr_q": 0.10,
            "comparisons": [["financial_direct_sparse", "online_fixed_share"]],
        },
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))
    result = run_empirical_v4(v3_dir=v3, config_path=cfg_path)
    assert set(result.horizon_results) == {1, 5}
    assert "online_fixed_share" in set(result.metrics["model"])
    assert not result.latest_weights.empty
    assert len(result.share_sensitivity) == 4
