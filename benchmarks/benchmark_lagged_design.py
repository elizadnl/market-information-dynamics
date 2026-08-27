from __future__ import annotations

import argparse
import time

import numpy as np

from market_information_dynamics.compute.lagged import build_lagged_design, native_available


def timed(values: np.ndarray, lags: int, backend: str, repeats: int) -> float:
    # Warm-up keeps one-off loader/allocation effects out of the comparison.
    build_lagged_design(values, lags, backend=backend)
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        build_lagged_design(values, lags, backend=backend)
        times.append(time.perf_counter() - start)
    return min(times)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--cols", type=int, default=40)
    parser.add_argument("--lags", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    rng = np.random.default_rng(7)
    values = rng.normal(size=(args.rows, args.cols))
    py_time = timed(values, args.lags, "python", args.repeats)
    print(f"python: {py_time:.6f}s")

    if not native_available():
        print("native: unavailable (run `python scripts/build_native.py`)")
        return

    native_time = timed(values, args.lags, "native", args.repeats)
    speedup = py_time / native_time
    print(f"native: {native_time:.6f}s")
    print(f"speedup: {speedup:.2f}x")


if __name__ == "__main__":
    main()
