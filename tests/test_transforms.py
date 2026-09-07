import numpy as np
import pandas as pd

from market_information_dynamics.data.transforms import transform_series


def test_log_return_and_inverse_direction():
    s = pd.Series([100.0, 110.0, 121.0], name="x")
    r = transform_series(s, "log_return")
    inv = transform_series(s, "negative_log_return")
    assert np.isclose(r.iloc[1], np.log(1.1))
    assert np.isclose(inv.iloc[1], -np.log(1.1))
