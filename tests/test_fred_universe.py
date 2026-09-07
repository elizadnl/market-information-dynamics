from pathlib import Path

import pandas as pd

from market_information_dynamics.data.fred_universe import load_fred_universe


class FakeFRED:
    def series(self, series_id, observation_start=None, observation_end=None):
        idx = pd.date_range("2026-01-01", periods=8, freq="D")
        base = 100 if series_id == "AAA" else 200
        return pd.Series([base + i for i in range(8)], index=idx, name=series_id)


def test_load_fred_universe_without_network(tmp_path: Path):
    cfg = tmp_path / "u.yaml"
    cfg.write_text(
        """
financial:
  - id: a
    source: FRED
    series_id: AAA
    family: x
    transform: log_return
  - id: b
    source: FRED
    series_id: BBB
    family: y
    transform: difference
"""
    )
    panel, meta = load_fred_universe(cfg, client=FakeFRED())
    assert list(panel.columns) == ["a", "b"]
    assert len(panel) == 7
    assert len(meta) == 2


def test_empirical_universe_uses_difference_for_wti():
    import yaml

    config = yaml.safe_load(Path("configs/universe_v1.yaml").read_text())
    wti = next(node for node in config["financial"] if node["id"] == "wti")
    assert wti["series_id"] == "DCOILWTICO"
    assert wti["transform"] == "difference"
