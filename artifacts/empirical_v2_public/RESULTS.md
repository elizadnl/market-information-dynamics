# Empirical v2 — predictive edge survival

This release was motivated by the empirical-v1 null result: coefficient persistence
alone was not a reliable proxy for genuine out-of-sample forecast value.

**Important evaluation caveat:** the 2025+ segment was already inspected during v1.
It is therefore labelled a *reused holdout*, not a pristine confirmatory test. The
v2 method is assessed with pre-2025 walk-forward evidence and transparent secondary
evaluation; genuinely prospective validation begins with future observations.

## Mean skill by horizon

| horizon | model | mean RMSE skill vs AR |
|---:|---|---:|
| 1 | ar | 0.00% |
| 1 | financial_direct_sparse | 1.04% |
| 1 | full_direct_sparse | 0.94% |
| 1 | survival_refit_full | 0.13% |
| 5 | ar | 0.00% |
| 5 | financial_direct_sparse | -0.06% |
| 5 | full_direct_sparse | -1.65% |
| 5 | survival_refit_full | -1.50% |
| 10 | ar | 0.00% |
| 10 | financial_direct_sparse | -0.32% |
| 10 | full_direct_sparse | -2.47% |
| 10 | survival_refit_full | -1.35% |
| 20 | ar | 0.00% |
| 20 | financial_direct_sparse | -0.14% |
| 20 | full_direct_sparse | -4.66% |
| 20 | survival_refit_full | -2.87% |

## Nested forecast comparisons

| comparison | pairs | challenger better | FDR rejections |
|---|---:|---:|---:|
| ar -> financial_direct_sparse | 48 | 21 | 0 |
| financial_direct_sparse -> full_direct_sparse | 48 | 8 | 0 |
| full_direct_sparse -> survival_refit_full | 48 | 24 | 0 |

## Highest current survival scores

| h | source | target | survival | sel. freq | OOS loss improvement | n |
|---:|---|---|---:|---:|---:|---:|
| 20 | pw_cape_of_good_hope_capacity_z | cnyusd | 0.977 | 1.00 | 8.27e-06 | 690 |
| 20 | pw_panama_canal_n_total_z | audusd | 0.960 | 0.98 | 3.43e-05 | 570 |
| 10 | pw_panama_canal_capacity_z | krwusd | 0.947 | 1.00 | 1.17e-05 | 700 |
| 10 | pw_panama_canal_n_total_z | audusd | 0.946 | 0.96 | 1.14e-05 | 560 |
| 10 | pw_cape_of_good_hope_capacity_z | cnyusd | 0.913 | 1.00 | 2.01e-06 | 700 |
| 20 | pw_panama_canal_capacity_z | krwusd | 0.909 | 1.00 | 2.9e-05 | 690 |
| 20 | pw_strait_of_hormuz_capacity_z | brent | 0.889 | 1.00 | 0.00228 | 690 |
| 5 | pw_panama_canal_capacity_z | krwusd | 0.881 | 0.91 | 4.99e-06 | 665 |
| 20 | pw_cape_of_good_hope_n_total_z | us2y | 0.875 | 0.99 | 0.0016 | 630 |
| 20 | audusd | krwusd | 0.861 | 1.00 | 1.05e-05 | 690 |
| 5 | pw_panama_canal_n_total_z | audusd | 0.838 | 0.94 | 3.72e-06 | 485 |
| 5 | pw_cape_of_good_hope_capacity_z | cnyusd | 0.783 | 1.00 | 4.32e-07 | 705 |
| 5 | pw_cape_of_good_hope_n_total_z | brlusd | 0.769 | 1.00 | 4.87e-06 | 705 |
| 20 | krwusd | audusd | 0.591 | 1.00 | 7.03e-06 | 670 |
| 20 | sp500 | audusd | 0.562 | 0.86 | 4.92e-06 | 330 |
| 10 | sp500 | vix | 0.552 | 1.00 | 0.257 | 700 |
| 20 | pw_panama_canal_n_total_z | cnyusd | 0.549 | 0.59 | 1.43e-06 | 130 |
| 20 | pw_strait_of_hormuz_n_total_z | sp500 | 0.530 | 0.90 | 7.7e-05 | 350 |
| 20 | pw_strait_of_hormuz_n_total_z | vix | 0.520 | 0.82 | 1.02 | 330 |
| 5 | sp500 | vix | 0.494 | 0.96 | 0.12 | 505 |

## Interpretation

An edge is not trusted merely because LASSO repeatedly selects it. Survival requires
recent structural persistence *and* positive realised OOS marginal forecast contribution.
Old evidence decays exponentially. Final survivor forecasts are refitted with Ridge
conditional on the surviving source set rather than created by zeroing LASSO coefficients.
