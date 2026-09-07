from __future__ import annotations

import ctypes
import os
import platform
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np

Backend = Literal["auto", "python", "native"]


def _library_names() -> tuple[str, ...]:
    system = platform.system().lower()
    if system == "windows":
        return ("mid_native.dll", "libmid_native.dll")
    if system == "darwin":
        return ("libmid_native.dylib",)
    return ("libmid_native.so",)


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    explicit = os.getenv("MID_NATIVE_LIB")
    if explicit:
        candidates.append(Path(explicit).expanduser())

    # Editable installs keep this file under <repo>/src/market_information_dynamics/compute.
    repo_root = Path(__file__).resolve().parents[3]
    for name in _library_names():
        candidates.append(repo_root / "build" / "native" / name)
        candidates.append(repo_root / name)
    return candidates


@lru_cache(maxsize=1)
def _load_native() -> ctypes.CDLL | None:
    for path in _candidate_paths():
        if not path.exists():
            continue
        try:
            lib = ctypes.CDLL(str(path))
        except OSError:
            continue

        lib.mid_native_abi_version.argtypes = []
        lib.mid_native_abi_version.restype = ctypes.c_int
        if lib.mid_native_abi_version() != 1:
            continue

        lib.mid_build_lagged_design.argtypes = [
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.mid_build_lagged_design.restype = ctypes.c_int
        return lib
    return None


def native_available() -> bool:
    """Return whether the optional C++17 lag-matrix kernel is loadable."""
    return _load_native() is not None


def resolved_backend(backend: Backend = "auto") -> Literal["python", "native"]:
    if backend not in {"auto", "python", "native"}:
        raise ValueError("backend must be one of: auto, python, native")
    if backend == "native":
        if not native_available():
            raise RuntimeError(
                "Native backend requested but no compiled library was found. "
                "Run `python scripts/build_native.py` or set MID_NATIVE_LIB."
            )
        return "native"
    if backend == "auto" and native_available():
        return "native"
    return "python"


def _validate_values(values: np.ndarray, lags: int) -> np.ndarray:
    arr = np.ascontiguousarray(values, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("values must be a two-dimensional array")
    if lags < 1:
        raise ValueError("lags must be >= 1")
    if arr.shape[0] <= lags:
        raise ValueError("Not enough observations for requested lags")
    if arr.shape[1] == 0:
        raise ValueError("values must contain at least one column")
    return arr


def _python_design(values: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    n_rows, n_cols = values.shape
    n_samples = n_rows - lags
    X = np.empty((n_samples, lags * n_cols), dtype=np.float64)
    Y = np.empty((n_samples, n_cols), dtype=np.float64)

    for sample, t in enumerate(range(lags, n_rows)):
        for lag in range(1, lags + 1):
            start = (lag - 1) * n_cols
            X[sample, start : start + n_cols] = values[t - lag]
        Y[sample] = values[t]
    return X, Y


def _native_design(values: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    lib = _load_native()
    if lib is None:
        raise RuntimeError("Native backend is not available")

    n_rows, n_cols = values.shape
    n_samples = n_rows - lags
    X = np.empty((n_samples, lags * n_cols), dtype=np.float64, order="C")
    Y = np.empty((n_samples, n_cols), dtype=np.float64, order="C")

    status = lib.mid_build_lagged_design(
        values.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        n_rows,
        n_cols,
        lags,
        X.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        Y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
    )
    if status != 0:
        raise RuntimeError(f"Native lagged-design kernel failed with status {status}")
    return X, Y


def build_lagged_design(
    values: np.ndarray,
    lags: int,
    *,
    backend: Backend = "auto",
) -> tuple[np.ndarray, np.ndarray, Literal["python", "native"]]:
    """Build the VAR design matrix with an optional C++17 backend.

    Feature ordering is `[t-1 all columns, t-2 all columns, ...]`, matching the
    coefficient tensor used by :class:`SparseVAR`.
    """
    arr = _validate_values(values, lags)
    selected = resolved_backend(backend)
    if selected == "native":
        X, Y = _native_design(arr, lags)
    else:
        X, Y = _python_design(arr, lags)
    return X, Y, selected
