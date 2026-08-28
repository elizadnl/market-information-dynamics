# Empirical v2: predictive edge survival

## Motivation from v1

The first public-data experiment produced a useful negative result. Adding the baseline
PortWatch physical layer did not robustly improve one-day forecasts beyond the financial
sparse VAR, and no physical-data improvement survived FDR correction. More importantly,
some edges were selected with extremely high frequency and stable sign while still harming
subsequent forecast loss.

That observation motivates a sharper question:

> **When should a predictive relationship be trusted, and when should it be killed?**

v2 treats coefficient persistence as necessary but insufficient evidence.

## Direct multi-horizon targets

For transformed daily series `x`, the h-day target at origin `t` is

`y(t,h) = x[t] + ... + x[t+h-1]`.

The predictor uses only observations through `t-1`. Separate direct models are estimated
for `h = 1, 5, 10, 20`; forecasts are not generated recursively. This is particularly
important for slower physical-economy variables, where a one-day target may be an
unreasonably short information horizon.

## Online edge attribution

At every forecast origin, the unfiltered full sparse model produces a base forecast. For
each selected source→target edge, the engine also produces a counterfactual forecast with
that edge zeroed while holding the rest of the fitted model fixed.

After the entire forecast horizon is realised, marginal edge utility is recorded as

`ΔL = squared_loss_without_edge - squared_loss_with_edge`.

Positive `ΔL` means the edge reduced realised OOS forecast loss. Crucially, an attribution
cannot enter a survival decision until its horizon has fully realised.

## Recency-weighted survival

For each edge the engine maintains:

- exponentially weighted selection frequency;
- exponentially weighted sign stability;
- current strength relative to its recent weighted strength;
- recency-weighted mean realised OOS loss improvement;
- contribution hit rate and an effective-sample t-statistic.

Structural evidence has a 180-day half-life; realised forecast contribution has a 120-day
half-life in the locked baseline configuration. Old evidence therefore cannot keep a dying
edge alive indefinitely.

## Post-selection refitting

LASSO is used to discover sparse structure. Once an edge set survives, the final forecast
is re-estimated with Ridge conditional on those surviving sources (self-lags are always
retained). This avoids treating a zeroed version of the original LASSO fit as a fully
re-estimated model and reduces shrinkage bias after selection.

## Forecast tests

Three nested comparisons are pre-specified for every target and horizon:

1. direct AR → financial-only direct sparse model;
2. financial-only → financial + physical direct sparse model;
3. full sparse model → survival-filtered post-selection refit.

Because h-day cumulative targets overlap, HAC lag length is at least `h-1`. Benjamini-
Hochberg FDR is applied across all target/horizon tests within each comparison family.

## Evaluation-status caveat

The 2025+ segment was already inspected in empirical v1. It is therefore **not** described
as a pristine holdout in v2. v2 uses pre-2025 walk-forward evidence for development and
reports 2025+ as a reused secondary evaluation segment. Observations from September 2026
onward are reserved for genuinely prospective validation.

This distinction is deliberate: changing the method after seeing a holdout invalidates the
original confirmatory interpretation, even if the new method is economically motivated.
