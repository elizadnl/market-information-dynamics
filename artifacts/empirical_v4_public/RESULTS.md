# Empirical v4 — online expert aggregation

v3 protected the financial core and allowed candidate data to act only as an overlay.
That architecture prevented large failures, but the hand-built gate still turned on
some overlays that later underperformed. v4 replaces the heuristic gate with a causal
Fixed-Share expert aggregator: model weights are updated only after each forecast horizon
has fully realised, and a small share term lets a previously weak expert recover after a
regime change.

**Evaluation status:** 2025+ is reused diagnostic history, not a pristine confirmatory
holdout. The online aggregation rule is frozen for prospective monitoring from September
2026 onward.

## Mean skill by horizon

| horizon | model | mean RMSE skill vs AR |
|---:|---|---:|
| 1 | ar | 0.00% |
| 1 | candidate_overlay_adaptive | 1.04% |
| 1 | candidate_overlay_survival | 0.92% |
| 1 | financial_direct_sparse | 1.04% |
| 1 | online_fixed_share | 1.01% |
| 5 | ar | 0.00% |
| 5 | candidate_overlay_adaptive | -0.22% |
| 5 | candidate_overlay_survival | -1.85% |
| 5 | financial_direct_sparse | -0.06% |
| 5 | online_fixed_share | -0.21% |
| 10 | ar | 0.00% |
| 10 | candidate_overlay_adaptive | -0.70% |
| 10 | candidate_overlay_survival | -3.46% |
| 10 | financial_direct_sparse | -0.32% |
| 10 | online_fixed_share | -0.41% |
| 20 | ar | 0.00% |
| 20 | candidate_overlay_adaptive | -0.70% |
| 20 | candidate_overlay_survival | -4.53% |
| 20 | financial_direct_sparse | -0.14% |
| 20 | online_fixed_share | -0.02% |

## Incremental forecast comparisons

| comparison | pairs | challenger better | FDR rejections |
|---|---:|---:|---:|
| ar -> financial_direct_sparse | 48 | 21 | 0 |
| candidate_overlay_survival -> online_fixed_share | 48 | 42 | 0 |
| financial_direct_sparse -> candidate_overlay_survival | 48 | 8 | 0 |
| financial_direct_sparse -> online_fixed_share | 48 | 19 | 0 |

## Current expert weights

| h | target | candidate_overlay_survival | financial_direct_sparse |
|---:|---|---:|---:|
| 1 | audusd | 0.500 | 0.500 |
| 1 | brent | 0.495 | 0.505 |
| 1 | brlusd | 0.493 | 0.507 |
| 1 | cnyusd | 0.494 | 0.506 |
| 1 | eurusd | 0.504 | 0.496 |
| 1 | henry_hub | 0.490 | 0.510 |
| 1 | krwusd | 0.486 | 0.514 |
| 1 | sp500 | 0.484 | 0.516 |
| 1 | us10y | 0.484 | 0.516 |
| 1 | us2y | 0.502 | 0.498 |
| 1 | vix | 0.497 | 0.503 |
| 1 | wti | 0.495 | 0.505 |
| 5 | audusd | 0.493 | 0.507 |
| 5 | brent | 0.459 | 0.541 |
| 5 | brlusd | 0.507 | 0.493 |
| 5 | cnyusd | 0.350 | 0.650 |
| 5 | eurusd | 0.446 | 0.554 |
| 5 | henry_hub | 0.419 | 0.581 |
| 5 | krwusd | 0.441 | 0.559 |
| 5 | sp500 | 0.457 | 0.543 |
| 5 | us10y | 0.429 | 0.571 |
| 5 | us2y | 0.437 | 0.563 |
| 5 | vix | 0.466 | 0.534 |
| 5 | wti | 0.508 | 0.492 |
| 10 | audusd | 0.306 | 0.694 |
| 10 | brent | 0.554 | 0.446 |
| 10 | brlusd | 0.406 | 0.594 |
| 10 | cnyusd | 0.312 | 0.688 |
| 10 | eurusd | 0.434 | 0.566 |
| 10 | henry_hub | 0.430 | 0.570 |
| 10 | krwusd | 0.371 | 0.629 |
| 10 | sp500 | 0.419 | 0.581 |
| 10 | us10y | 0.385 | 0.615 |
| 10 | us2y | 0.443 | 0.557 |
| 10 | vix | 0.469 | 0.531 |
| 10 | wti | 0.478 | 0.522 |
| 20 | audusd | 0.449 | 0.551 |
| 20 | brent | 0.672 | 0.328 |
| 20 | brlusd | 0.414 | 0.586 |
| 20 | cnyusd | 0.224 | 0.776 |
| 20 | eurusd | 0.378 | 0.622 |
| 20 | henry_hub | 0.333 | 0.667 |
| 20 | krwusd | 0.319 | 0.681 |
| 20 | sp500 | 0.357 | 0.643 |
| 20 | us10y | 0.390 | 0.610 |
| 20 | us2y | 0.463 | 0.537 |
| 20 | vix | 0.371 | 0.629 |
| 20 | wti | 0.446 | 0.554 |

## Fixed-Share sensitivity

| h | share | mean RMSE skill vs financial core | targets better |
|---:|---:|---:|---:|
| 1 | 0.00000 | -0.03% | 2/12 |
| 1 | 0.00198 | -0.03% | 2/12 |
| 1 | 0.00397 | -0.03% | 2/12 |
| 1 | 0.00794 | -0.03% | 2/12 |
| 5 | 0.00000 | -0.05% | 6/12 |
| 5 | 0.00198 | -0.11% | 5/12 |
| 5 | 0.00397 | -0.15% | 4/12 |
| 5 | 0.00794 | -0.19% | 4/12 |
| 10 | 0.00000 | 0.05% | 5/12 |
| 10 | 0.00198 | -0.03% | 5/12 |
| 10 | 0.00397 | -0.09% | 5/12 |
| 10 | 0.00794 | -0.16% | 4/12 |
| 20 | 0.00000 | 0.21% | 5/12 |
| 20 | 0.00198 | 0.16% | 5/12 |
| 20 | 0.00397 | 0.11% | 6/12 |
| 20 | 0.00794 | 0.06% | 6/12 |

## Interpretation

The online combiner is deliberately model-agnostic. It does not decide that shipping
or any other candidate domain *should* matter. It treats the financial core and the
survival-filtered candidate overlay as competing forecast experts, updates their weights
only after losses are observable, and retains a small probability of switching back after
a regime change. This is a sequential decision problem, not evidence of structural causality.

The primary research claim remains methodological: in non-stationary systems, a model
should learn not only predictive relationships but also when to stop trusting the model
that generated them.
