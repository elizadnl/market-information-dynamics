from market_information_dynamics.data.synthetic import generate_regime_switching_system
from market_information_dynamics.statistics.rolling_edges import rolling_edge_snapshots


def test_rolling_edges_detect_regime_change():
    frame = generate_regime_switching_system(n_obs=1200, seed=7)
    edges = rolling_edge_snapshots(frame, window=300, step=50, lags=3, alpha=0.035)
    pc = edges[(edges.source == "physical") & (edges.target == "commodity")].reset_index(drop=True)
    cf = edges[(edges.source == "commodity") & (edges.target == "fx")].reset_index(drop=True)
    assert pc.iloc[:4].strength.mean() > pc.iloc[-4:].strength.mean()
    assert cf.iloc[:4].strength.mean() < cf.iloc[-4:].strength.mean()
