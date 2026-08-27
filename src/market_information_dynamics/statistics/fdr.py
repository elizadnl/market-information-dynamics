from __future__ import annotations

import numpy as np


def benjamini_hochberg(p_values, q: float = 0.05) -> np.ndarray:
    """Return a boolean rejection mask controlling false discovery rate at q."""
    p = np.asarray(p_values, dtype=float)
    if p.ndim != 1:
        raise ValueError("p_values must be one-dimensional")
    if not 0 < q < 1:
        raise ValueError("q must lie in (0, 1)")
    if np.any((p < 0) | (p > 1) | ~np.isfinite(p)):
        raise ValueError("p_values must be finite values in [0, 1]")
    if len(p) == 0:
        return np.zeros(0, dtype=bool)

    order = np.argsort(p)
    ranked = p[order]
    thresholds = q * np.arange(1, len(p) + 1) / len(p)
    passed = ranked <= thresholds
    reject = np.zeros(len(p), dtype=bool)
    if passed.any():
        k = np.flatnonzero(passed).max()
        reject[order[: k + 1]] = True
    return reject
