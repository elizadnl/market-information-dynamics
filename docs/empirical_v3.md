# Empirical v3 — protected-core candidate overlay

## Research question

Can a noisy candidate data domain add forecasting information **beyond** an already competitive
financial core, and can the system switch that augmentation off when its realised value decays?

## Architecture

At each forecast origin, v3 first produces the financial-only direct sparse forecast. That model
is the protected core.

The candidate layer is not fitted to the original target. It is fitted to historical residuals:

```text
residual(origin, h) = realised_h_day_target - core_forecast(origin, h)
```

Crucially, these are residuals from forecasts that were genuinely generated out of sample by the
walk-forward core model. A residual is unavailable for overlay training until its full h-day
outcome has realised.

For the current public-data experiment, the candidate domain is the PortWatch physical layer.
The implementation is generic: any columns outside the configured core universe can become a
candidate layer in a later experiment.

## Candidate edge attribution

For a selected candidate source→target edge, the realised contribution is measured against the
protected core itself:

```text
DeltaL_edge = loss(core) - loss(core + edge_adjustment)
```

This is stricter than empirical v2, which evaluated edge removal inside the full model.

## Two survival levels

### Edge survival

Candidate edges must demonstrate recent structural persistence, sign stability, coefficient
retention and positive realised OOS contribution relative to the core.

### Model-level overlay gate

Even individually useful edges can interact badly after joint refitting. The selected overlay is
therefore evaluated as a whole:

```text
DeltaL_overlay = loss(core) - loss(core + selected_overlay)
```

Past overlay evidence is exponentially downweighted. If there is insufficient history, negative
recent mean contribution or a non-positive recency-weighted contribution t-statistic, the gate is
exactly zero. Positive evidence maps smoothly to a weight in [0, 1].

The final forecast is:

```text
forecast = core_forecast + gate * selected_candidate_overlay
```

The protected core is therefore the automatic fallback.

## Why the residual layer is cross-fitted

Training an alternative-data model on residuals from an in-sample core could manufacture apparent
incremental structure. v3 instead accumulates only realised OOS core residuals from the historical
walk-forward evaluation. That makes the overlay learn the errors the core actually made in live-like
conditions.

## Evaluation status

The 2025+ period has already influenced v1/v2 development and remains diagnostic only. v3 does not
relabel it as a fresh holdout. The intended confirmatory test is prospective observation after the
method is frozen.
