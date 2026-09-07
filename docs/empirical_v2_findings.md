# Empirical v2 findings — predictive edge survival

Empirical v2 was the first real test of the project's signal-survival idea. The evidence pack is
frozen in `artifacts/empirical_v2_public/`.

## What happened

On the reused 2025+ evaluation segment, the financial-only direct sparse model remained the
strongest broad baseline at the one-day horizon. Mean RMSE skill versus the direct AR benchmark
was approximately:

| Horizon | Financial-only | Full financial+physical | Survival-refit full |
|---:|---:|---:|---:|
| 1 | +1.04% | +0.94% | +0.13% |
| 5 | -0.06% | -1.65% | -1.50% |
| 10 | -0.32% | -2.47% | -1.35% |
| 20 | -0.14% | -4.66% | -2.87% |

No target/horizon comparison survived Benjamini-Hochberg FDR correction.

The survival filter nevertheless did something real: relative to the unfiltered full model it
reduced forecast error on 7/12 targets at h=10 and 8/12 targets at h=20. The problem is that the
filtered system still usually failed to recover the stronger financial-only baseline.

## Why this matters

v2 scored an edge by asking whether it helped *inside the full model*. That is not the strict
incremental question that matters for alternative data. A physical edge can improve a weak
financial+physical model while the complete system still loses to the financial-only core.

The highest survival scores also became increasingly dominated by PortWatch edges at longer
horizons, even though the full physical layer was harmful on average. This exposed a hierarchy
problem:

1. structural persistence is not enough;
2. edge-level marginal usefulness inside a candidate model is not enough;
3. the candidate layer must add value **relative to the protected baseline model**;
4. the complete augmented model must also prove net realised OOS value after interactions and
   refitting.

That failure motivates empirical v3.

## v3 design implication

The financial-only model is now treated as a protected core. Candidate-domain features cannot
replace or prune it. Instead they are trained on fully realised out-of-sample residuals left by
the core. Each candidate edge is evaluated by comparing:

```text
core forecast
vs
core forecast + this candidate edge's residual adjustment
```

Only surviving candidate edges are refitted. A second model-level adaptive gate then shrinks the
entire candidate overlay to zero unless the augmented forecast has positive recent realised OOS
loss contribution versus the same core.

This converts the project from "find stable edges" into a stricter online model-augmentation
problem.
