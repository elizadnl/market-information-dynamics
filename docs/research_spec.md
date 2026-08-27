# Research specification

## Core question

Can we estimate where predictive information first appears, how it propagates across a
mixed physical-financial system, and when previously useful relationships stop working?

The project deliberately studies **predictive information**, not structural causality.
A directed edge means that lagged observations of one variable improve forecasts of
another under the stated model and validation protocol.

## Pre-registered hypotheses for the first empirical release

**H1 — Incremental information exists.** Some directed lag relationships survive after
controlling for each target's own history and common features.

**H2 — Edge stability matters.** Forecasts conditioned on historically stable edges
outperform forecasts that use every in-sample relationship.

**H3 — The graph is non-stationary.** A time-varying model materially outperforms one
static graph over the full sample on genuine forward data.

**H4 — Physical data can add information.** A model with public physical-economy features
improves at least one pre-specified financial target relative to a financial-only baseline.

Failure to reject any hypothesis is an acceptable research outcome.

## Evaluation hierarchy

1. Naive persistence / historical-mean baseline.
2. Target-only autoregression.
3. Dense multivariate baseline where feasible.
4. Sparse VAR.
5. Sparse VAR + edge-stability filter.
6. Time-varying / change-point extension.

Every comparison is walk-forward. Scaling, feature selection, regularisation tuning and
network estimation must be fitted using training data only.

## Multiple testing

The network creates many candidate edges. Exploratory p-values are not reported as
"discoveries" without false-discovery-rate control and stability checks. Bootstrap or
block-permutation procedures will be used when serial dependence invalidates iid tests.

## Point-in-time rule

A datum can enter the feature panel only at the timestamp it was actually observable.
Macro vintages/revisions and delayed physical-data releases are represented using
`available_at`, not merely the economic observation date.

## Initial universe philosophy

Start with 20–40 interpretable variables, not hundreds of opaque tickers. Each node must
have a reason to exist and a documented observation frequency, timezone, publication lag,
transformation and source.

## What this project is not

- It is not a claim that Granger-style predictability proves causality.
- It is not a competition to maximise backtest Sharpe.
- It does not use employer data, code, models or proprietary research.
- It does not add deep learning unless a simpler model demonstrably leaves exploitable
  nonlinear structure on the table.
