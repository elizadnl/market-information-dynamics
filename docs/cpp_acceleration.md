# Optional C++17 acceleration

The project is intentionally **Python-first** because research iteration speed matters more
than low-level optimisation during model development. C++ is used only where there is a
clear systems reason.

The first native component accelerates repeated construction of lagged design matrices
inside rolling and walk-forward VAR fits. That operation is deterministic, easy to test
against a reference implementation, and sits on a hot path once the empirical universe
contains many series and refits.

## Design

- `cpp/lagged_design.cpp` implements a small C ABI in C++17.
- Python calls it through `ctypes`; no third-party binding framework is required.
- `SparseVAR(design_backend="auto")` uses native code when a compatible library exists and
  otherwise falls back to the fully tested Python implementation.
- Native and Python outputs are checked for exact parity in CI.

This architecture keeps the research package installable on machines without a C++
compiler while making optimisation explicit and measurable rather than decorative.

## Build

```bash
python scripts/build_native.py
pytest
python benchmarks/benchmark_lagged_design.py
```

On Windows, run the build command from a Visual Studio Developer PowerShell so that `cl`
is available. The C++ library is optional; all research functionality remains available
through the Python backend.

## Why not rewrite the model in C++?

The sparse regression itself is delegated to mature numerical libraries. Reimplementing
LASSO purely to increase the amount of C++ in the repository would add maintenance and
numerical risk without improving the research. Native code is added only when profiling
identifies a stable, well-specified computational kernel.
