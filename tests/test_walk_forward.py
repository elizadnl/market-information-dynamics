from market_information_dynamics.data.synthetic import generate_regime_switching_system
from market_information_dynamics.evaluation.walk_forward import walk_forward_sparse_var


def test_walk_forward_alignment_and_no_early_predictions():
    frame = generate_regime_switching_system(n_obs=420, seed=4)
    result = walk_forward_sparse_var(frame, lags=2, alpha=0.04, min_train=200, refit_every=25)
    assert result.predictions.index[0] == frame.index[200]
    assert result.predictions.index.equals(result.actuals.index)
    assert len(result.predictions) == len(frame) - 200
    assert not result.edge_snapshots.empty
