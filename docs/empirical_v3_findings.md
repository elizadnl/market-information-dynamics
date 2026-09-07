# Empirical v3 findings — protected-core candidate overlay

The v3 run used 2025+ as **reused diagnostic history**, not a pristine holdout.

## Main result

Protecting the financial model worked as intended: the adaptive overlay was much less
harmful than allowing candidate data to enter unrestricted. Across the 48 target/horizon
comparisons, the adaptive model beat the survival-only overlay in 36 cases. However, it
beat the financial core in only 12/48 cases and **no comparison survived FDR correction**.

Mean RMSE skill versus the AR baseline on the reused 2025+ period was:

| horizon | financial core | adaptive candidate overlay |
|---:|---:|---:|
| 1 | +1.04% | +1.04% |
| 5 | -0.06% | -0.22% |
| 10 | -0.32% | -0.70% |
| 20 | -0.14% | -0.70% |

The current v3 gate was highly selective. At the final observation it assigned non-zero
weight mainly to Brent at 10/20 days, WTI at 20 days and AUD/USD at 20 days. The reused
history contains small exploratory gains for Brent and WTI at longer horizons, but these
are not confirmatory evidence.

## Why v4 exists

The hand-built gate is still a heuristic statistical decision rule. v4 therefore changes
only the *model-selection layer*: forecasts from the protected core and the candidate
model are treated as experts and combined by Fixed-Share exponential weighting. This is a
standard online-learning formulation designed for environments in which the identity of
the best forecaster can switch through time.
