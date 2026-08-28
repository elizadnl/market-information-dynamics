# Empirical v1 findings: a useful null result

The first real-data experiment was frozen and run on the public FRED + IMF PortWatch panel.
Its main purpose was to test whether the baseline physical layer added incremental one-day
forecast information beyond the financial sparse VAR.

## Primary result

On the 2025+ reporting segment, the financial + physical model did **not** improve average
forecast accuracy over the financial-only model. Mean incremental RMSE skill across the 12
targets was approximately **-0.10%** (median **-0.13%**). Four of twelve targets improved at
the baseline 10-day PortWatch availability lag, and none of the paired improvements survived
Benjamini-Hochberg FDR control.

The strongest positive physical-data result was Brent at roughly **+0.35%** incremental RMSE
skill; the weakest was Henry Hub at roughly **-0.45%**.

## Availability-lag sensitivity

The negative/weak conclusion was not an artefact of choosing one assumed PortWatch lag:

| assumed availability lag | mean incremental RMSE skill | targets improved | FDR-significant improvements |
|---:|---:|---:|---:|
| 7 days | -0.10% | 2 / 12 | 0 |
| 14 days | -0.09% | 5 / 12 | 0 |
| 21 days | -0.01% | 6 / 12 | 0 |

The baseline 10-day run similarly produced no FDR-significant physical-data improvements.

## What changed the project

The more interesting finding was methodological. Some edges were selected in every rolling
LASSO refit with stable sign yet did not improve subsequent forecasts. For example,
`pw_panama_canal_n_total_z → henry_hub` had 100% selection frequency and 100% sign stability,
but the full model's Henry Hub RMSE was worse than the financial-only model.

That failure motivates empirical v2:

> **coefficient persistence is not the same thing as predictive usefulness.**

v2 therefore measures realised marginal OOS forecast contribution and lets old evidence
decay, rather than trusting an edge merely because it keeps receiving a non-zero coefficient.

## Secondary financial result

AUD/USD provided a useful sanity check that the forecasting framework can detect some
multivariate information even when the physical hypothesis fails. On the 2025+ segment the
financial sparse model improved RMSE by about **8.1%** versus the direct AR-style benchmark,
with forecast correlation around **0.41**. The stability-filtered v1 model improved RMSE by
about **8.4%** versus AR. This remains exploratory rather than confirmatory: the corresponding
forecast-comparison evidence did not survive multiple-testing correction.

## Research interpretation

v1 is intentionally retained in the repository rather than hidden. The null result narrows
the research question and provides the empirical reason for the signal-survival framework.
It is evidence about research process, not a failed attempt to manufacture alpha.
