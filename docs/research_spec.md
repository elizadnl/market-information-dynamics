# Research specification

## Core question

Can we estimate where predictive information appears, whether it remains useful out of sample,
and when previously useful relationships stop working?

The project studies **predictive information**, not structural causality. A directed edge means
that lagged observations of one variable contribute to an explicit forecast under the stated
model and validation protocol.

## Empirical v1: physical-data ablation

The first real-data release pre-specified a one-day comparison between target-only AR,
financial-only sparse VAR, financial + physical sparse VAR, and a cumulative historical
edge-stability filter. It also fixed a 2025+ reporting segment and PortWatch availability-lag
sensitivity before the first real run.

The physical-data hypothesis produced a null result: the baseline PortWatch layer did not
robustly improve the financial-only model, and no physical-data improvement survived FDR.
This result remains frozen under `artifacts/empirical_v1_public/`.

## Empirical v2: predictive edge survival

v1 exposed a more general failure: repeated coefficient selection and sign stability did not
necessarily imply useful subsequent forecasts. v2 therefore pre-specifies the following
questions.

**H1 — Multivariate information exists at some horizon.** A financial-only direct sparse model
can improve on a target-only direct AR for at least some pre-specified target/horizon pairs.

**H2 — Physical information is horizon-dependent.** If public physical-economy data adds
incremental information, the effect may appear at 5/10/20-day horizons rather than only at one
day. This is tested as a family, not selected after the fact.

**H3 — Realised predictive contribution matters.** A survivor model that requires positive
past OOS marginal loss contribution improves on the unfiltered full sparse model more reliably
than coefficient persistence alone.

**H4 — Signals decay.** Recency-weighted edge state should distinguish relationships whose
recent predictive contribution is deteriorating from relationships kept alive by old history.

Failure to support any hypothesis remains an acceptable outcome.

## v2 evaluation hierarchy

1. target-only direct AR;
2. financial-only direct sparse model;
3. full financial + physical direct sparse model;
4. predictive-edge-survival filter;
5. post-selection Ridge refit on surviving sources.

Horizons are fixed at 1, 5, 10 and 20 trading days. All forecasts are direct cumulative-target
forecasts, not recursive rollouts.

## Online attribution rule

For each selected cross-series edge, the engine computes a counterfactual forecast with that
edge removed. The edge's marginal squared-loss improvement cannot enter its survival state until
the entire forecast horizon is observed. This prevents the survival filter from using future
outcomes.

## Multiple testing and overlapping horizons

The project tests three nested comparison families across targets and horizons. Loss-difference
inference uses HAC variance with lag length at least `h-1` for overlapping h-day outcomes.
Benjamini-Hochberg FDR is applied within each pre-specified comparison family.

## Holdout-status rule

The 2025+ window was inspected in empirical v1. It is therefore a **reused holdout** in v2, not
a pristine confirmatory sample. v2 development is anchored in pre-2025 walk-forward evidence,
while observations from September 2026 onward are reserved for prospective validation.

## Point-in-time rule

A datum can enter the feature panel only at the timestamp it could reasonably have been
available. Macro revisions and delayed physical observations must be represented with explicit
availability timing rather than economic observation date alone.

## What this project is not

- It is not a claim that Granger-style predictability proves causality.
- It is not a competition to maximise backtest Sharpe.
- It does not use employer data, code, models or proprietary research.
- It does not add a more complex model merely because it sounds more sophisticated.
