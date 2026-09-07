from market_information_dynamics.data.synthetic import generate_regime_switching_system
from market_information_dynamics.models.sparse_var import SparseVAR


def test_sparse_var_recovers_key_predictive_edges():
    frame = generate_regime_switching_system(n_obs=900, seed=7).iloc[:430]
    model = SparseVAR(lags=3, alpha=0.03).fit(frame)
    # In regime 1, physical -> commodity and commodity -> fx are deliberately strong.
    assert model.adjacency_.loc["physical", "commodity"] > 0.20
    assert model.adjacency_.loc["commodity", "fx"] > 0.10


def test_predict_next_has_correct_columns():
    frame = generate_regime_switching_system(n_obs=500, seed=5)
    model = SparseVAR(lags=2, alpha=0.04).fit(frame.iloc[:300])
    pred = model.predict_next(frame.iloc[:301])
    assert list(pred.index) == list(frame.columns)


def test_masked_prediction_can_remove_cross_series_edges():
    import pandas as pd

    frame = generate_regime_switching_system(n_obs=500, seed=9)
    model = SparseVAR(lags=2, alpha=0.03).fit(frame.iloc[:350])
    mask = pd.DataFrame(False, index=frame.columns, columns=frame.columns)
    for col in frame.columns:
        mask.loc[col, col] = True
    pred = model.predict_next_masked(frame.iloc[:351], mask)
    assert list(pred.index) == list(frame.columns)
    assert pred.notna().all()
