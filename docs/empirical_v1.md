# Empirical pilot v1 — locked specification

This document is the pre-result specification for the first public-data experiment. The
important rule is that the choices below are made **before** inspecting the 2025+ final
holdout.

## Question

Does a small, public physical-economy layer contain **incremental predictive information**
for liquid financial variables after conditioning on the financial system's own lagged
history?

This is a forecasting question, not a structural-causality claim.

## Financial layer — 12 daily nodes

Five FX series (AUD, BRL, CNY, KRW and EUR versus USD), S&P 500, VIX, 2Y and 10Y Treasury
yields, WTI, Brent and Henry Hub natural gas. The universe is deliberately compact so every
node can be audited and every result can be paired on the same OOS dates.

## Physical layer — PortWatch chokepoints

Baseline features are past-only **seasonality-adjusted** anomalies in total transit calls
and estimated transit capacity for:

- Suez Canal
- Panama Canal
- Strait of Hormuz
- Bab el-Mandeb Strait
- Cape of Good Hope
- Malacca Strait

The live IMF ArcGIS layer exposes date, chokepoint name, vessel-type counts, total vessel
counts and capacity fields. The World Bank's PortWatch tutorial documents the same daily
chokepoint service and its 1,000-record API limit, which the client paginates around.

The feature transform uses a trailing seven-day smooth, a 364-day (52-week) log difference
to remove annual/weekday seasonality, and a rolling z-score whose mean/variance are shifted
by one observation. No centred smoothing or full-sample seasonal estimate is used.

Additional tanker / dry-bulk / container metrics are deliberately excluded from the first
baseline and can enter only through a named later ablation.

## Availability treatment

The current PortWatch history does not itself reconstruct historical publication vintages.
The primary run therefore assumes a 10-calendar-day availability lag and repeats the full
experiment at 7, 14 and 21 days. This is a conservative modelling choice, not a claim that
10 days is the exact historical publication delay.

## Primary ablation

All models are evaluated on the same complete panel and same forecast dates:

1. **AR** — each target uses only its own five daily lags.
2. **Financial sparse VAR** — all 12 financial nodes, five lags.
3. **Full sparse VAR** — financial nodes plus the PortWatch physical layer.
4. **Stability-filtered full VAR** — cross-series coefficients are used only after the edge
   has survived enough prior expanding-window refits; own lags remain available.

Sparse-VAR coefficients are standardised and estimated target-by-target with L1
regularisation. The initial alpha is fixed at 0.035 for v1; tuning/robustness can be added on
the development period but must not use the final holdout.

## Time split

- Start: 2019-01-01, subject to source availability and transformation burn-in.
- Minimum expanding training history: 750 complete observations.
- Refit cadence: every 20 forecast observations.
- **Final holdout begins 2025-01-01.**

The pre-2025 OOS segment is useful for debugging and development diagnostics. The 2025+
segment is the reporting holdout and should not be used to choose model architecture,
features or thresholds.

## Primary statistical test

For each financial target, compare the paired squared forecast losses of:

`financial_sparse_var` vs `full_sparse_var`.

The loss-difference mean is tested with a HAC long-run variance (five lags). P-values across
targets are corrected with Benjamini-Hochberg at q=10%.

A positive physical-data finding therefore needs both:

- lower OOS loss for the full model; and
- statistical support after the multiple-target correction.

Even then, the result is described as predictive evidence rather than causality or
production alpha.

## Stability filter

At each refit, the mask is built only from edge snapshots already estimated by that date.
A cross-series edge must have:

- strength >= 0.05 when selected;
- historical selection frequency >= 60%;
- sign stability >= 70%;
- at least five prior snapshots before filtering is activated.

This is meant to test the project's central idea: whether **relationship survival** is useful
information beyond coefficient magnitude alone.

## Required robustness before promotion

A result is not promoted based on one attractive chart. At minimum it must survive:

1. 7/14/21-day PortWatch availability-lag sensitivity;
2. target-by-target inspection rather than only an aggregate mean;
3. episode inspection to ensure one crisis window is not doing all the work;
4. coefficient/edge survival diagnostics;
5. later block-bootstrap or block-permutation significance for selected network edges.

## Output contract

`market-information-dynamics public-research` writes an evidence pack containing:

- panel audit and summary;
- model metrics for all OOS dates and the final holdout;
- all paired predictions/actuals;
- expanding edge snapshots;
- edge-stability table;
- physical-vs-financial paired forecast tests;
- availability-lag sensitivity summary;
- OOS skill figures; and
- an automatically generated `RESULTS.md` that explicitly avoids causal/alpha claims.
