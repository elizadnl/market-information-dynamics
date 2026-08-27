import numpy as np
import pytest

from market_information_dynamics.compute.lagged import (
    build_lagged_design,
    native_available,
)


def test_python_lagged_design_ordering():
    values = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0], [4.0, 40.0]])
    X, Y, backend = build_lagged_design(values, 2, backend="python")

    assert backend == "python"
    np.testing.assert_allclose(X, [[2.0, 20.0, 1.0, 10.0], [3.0, 30.0, 2.0, 20.0]])
    np.testing.assert_allclose(Y, [[3.0, 30.0], [4.0, 40.0]])


def test_native_matches_python_when_built():
    if not native_available():
        pytest.skip("optional native library is not built")

    rng = np.random.default_rng(123)
    values = rng.normal(size=(250, 7))
    X_py, Y_py, _ = build_lagged_design(values, 4, backend="python")
    X_cpp, Y_cpp, backend = build_lagged_design(values, 4, backend="native")

    assert backend == "native"
    np.testing.assert_array_equal(X_cpp, X_py)
    np.testing.assert_array_equal(Y_cpp, Y_py)
