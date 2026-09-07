import numpy as np

from market_information_dynamics.statistics.fdr import benjamini_hochberg


def test_bh_rejects_small_pvalues():
    p = np.array([0.001, 0.004, 0.03, 0.20, 0.90])
    reject = benjamini_hochberg(p, q=0.05)
    assert reject.tolist() == [True, True, True, False, False]
