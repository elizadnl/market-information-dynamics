from market_information_dynamics.data.synthetic import generate_regime_switching_system


def test_synthetic_shape_and_columns():
    frame = generate_regime_switching_system(n_obs=500, seed=3)
    assert list(frame.columns) == ["physical", "commodity", "fx", "equity", "rates", "vol"]
    assert len(frame) == 490
    assert not frame.isna().any().any()
