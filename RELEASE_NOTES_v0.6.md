# v0.6 release notes — protected-core candidate overlay

Empirical v2 reduced some of the long-horizon damage caused by the full physical+financial model,
but it did not solve the core problem: the filtered system still usually lost to the
financial-only model, and no improvement survived FDR.

v0.6 changes the hierarchy.

The financial model is now a protected core. Candidate data are trained only on fully realised
OOS errors left by that core. Candidate edges must demonstrate incremental loss reduction relative
to the core itself, surviving edges are refitted, and a second online gate controls whether the
complete candidate overlay is allowed to affect the final forecast.

The final architecture is:

```text
financial core
    +
OOS-residual candidate model
    +
edge survival
    +
post-selection refit
    +
adaptive model-level gate
```

If candidate evidence is weak or harmful, the gate returns the forecast to the financial core.

### Validation

- 39 tests collected.
- 38 pass + 1 optional native-backend skip without a compiled C++ library.
- 39/39 pass with the C++17 backend built.
- Controlled synthetic candidate-death demo ranks the adaptive overlay ahead of the ungated
  overlay and shows the gate moving from near one toward zero after the true candidate signal is
  removed.

### Evaluation caveat

The 2025+ period has already influenced v1 and v2 and is not a fresh confirmatory holdout for v3.
The next genuine validation step is to freeze v3 before prospective observations are scored.
