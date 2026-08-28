# Prospective protocol — frozen 28 August 2026

The project has now used data through August 2026 for iterative method development. No
post-September-2026 observation should therefore be treated as development data for the
current method.

## Frozen components

From **1 September 2026**, the following are fixed for prospective evaluation:

- the financial-core model class and hyperparameters;
- the candidate-overlay construction and survival screen;
- forecast horizons: 1, 5, 10 and 20 trading days;
- the Fixed-Share expert set: financial core + survival-filtered candidate overlay;
- primary share parameter: `1/252` per realised update;
- causal loss admission: an h-step forecast can update model weights only after the full
  h-step outcome has realised;
- the loss normalisation and clipping rule;
- RMSE, MAE, directional accuracy and HAC forecast-comparison tests;
- Benjamini-Hochberg FDR at q=0.10 across the target/horizon comparison family.

## What may change without invalidating the protocol

Pure engineering changes are allowed if they do not change historical values or model
outputs: API retries, caching, logging, plotting, packaging, test coverage and performance
optimisation. Any statistical/model change must be versioned as a new exploratory method
and cannot be retroactively judged on the same prospective window.

## Prospective claims

The repository will not call September-2026 onward a holdout until enough horizons have
fully realised. Results before that point are live monitoring only. A positive claim
requires improvement relative to the protected financial core and should survive the
pre-specified multiple-testing procedure.
