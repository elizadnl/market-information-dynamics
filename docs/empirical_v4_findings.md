# Empirical v4 findings — online expert aggregation

Empirical v4 was computed from the already-generated v3 forecast paths. It therefore does
not create a fresh holdout: **2025+ remains reused diagnostic history**.

## Why v4 was added

The v3 protected-core architecture successfully reduced catastrophic candidate-model damage,
but its model-level gate was hand-designed and still activated some overlays that subsequently
underperformed. v4 changes only the model-selection layer. The financial core and the
survival-filtered candidate overlay are treated as forecast experts and combined by causal
Fixed-Share exponential weighting.

An h-step forecast may update expert weights only after the complete h-step outcome has
realised. A small fixed-share term continuously reintroduces probability mass to each expert,
which allows an expert that was poor in one regime to recover later.

## Reused 2025+ diagnostic result

Mean RMSE skill versus direct AR:

| horizon | financial core | survival overlay | Fixed-Share |
|---:|---:|---:|---:|
| 1 | +1.04% | +0.92% | +1.01% |
| 5 | -0.06% | -1.85% | -0.21% |
| 10 | -0.32% | -3.46% | -0.41% |
| 20 | -0.14% | -4.53% | -0.02% |

The online combiner beat the raw survival-overlay expert in **42/48** target/horizon
comparisons. Relative to the protected financial core it improved **19/48** comparisons.
No comparison survived Benjamini-Hochberg FDR correction.

At the pre-specified primary Fixed-Share parameter (`1/252` probability mass per realised
update), mean RMSE skill relative to the financial core was approximately:

- 1 day: **-0.03%** (2/12 targets better)
- 5 days: **-0.15%** (4/12 better)
- 10 days: **-0.09%** (5/12 better)
- 20 days: **+0.11%** (6/12 better)

Nearby share settings do not change the qualitative conclusion. The no-share cumulative
expert weighting diagnostic is somewhat stronger at 20 days, but it is not substituted for
the pre-specified primary rule.

## Interpretation

The result supports a narrower methodological claim than a trading claim. Online expert
aggregation materially reduces the damage from a weak candidate model and, at the longest
horizon, approximately matches/slightly improves the core on average. It does **not** provide
statistically robust evidence that the candidate data improve financial forecasting.

That is exactly why the next evidence must be prospective rather than another round of tuning
on 2025-2026 history.
