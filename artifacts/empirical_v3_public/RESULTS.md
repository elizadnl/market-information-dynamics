# Empirical v3 — protected-core candidate overlay

v2 showed that filtering persistent edges could reduce damage from the full
physical+financial system, but it still usually failed to beat the financial-only
model. v3 changes the question: candidate data must explain realised out-of-sample
errors left by a protected financial core.

**Evaluation status:** 2025+ has already informed earlier project iterations and is
therefore a reused diagnostic period, not a pristine confirmatory holdout. The method
is intended to be frozen before prospective observations from September 2026 onward.

## Mean skill by horizon

| horizon | model | mean RMSE skill vs AR |
|---:|---|---:|
| 1 | ar | 0.00% |
| 1 | candidate_overlay_adaptive | 1.04% |
| 1 | candidate_overlay_sparse | 0.44% |
| 1 | candidate_overlay_survival | 0.92% |
| 1 | financial_direct_sparse | 1.04% |
| 5 | ar | 0.00% |
| 5 | candidate_overlay_adaptive | -0.22% |
| 5 | candidate_overlay_sparse | -3.79% |
| 5 | candidate_overlay_survival | -1.85% |
| 5 | financial_direct_sparse | -0.06% |
| 10 | ar | 0.00% |
| 10 | candidate_overlay_adaptive | -0.70% |
| 10 | candidate_overlay_sparse | -4.06% |
| 10 | candidate_overlay_survival | -3.46% |
| 10 | financial_direct_sparse | -0.32% |
| 20 | ar | 0.00% |
| 20 | candidate_overlay_adaptive | -0.70% |
| 20 | candidate_overlay_sparse | -6.26% |
| 20 | candidate_overlay_survival | -4.53% |
| 20 | financial_direct_sparse | -0.14% |

## Incremental forecast comparisons

| comparison | pairs | challenger better | FDR rejections |
|---|---:|---:|---:|
| ar -> financial_direct_sparse | 48 | 21 | 0 |
| candidate_overlay_survival -> candidate_overlay_adaptive | 48 | 36 | 0 |
| financial_direct_sparse -> candidate_overlay_adaptive | 48 | 12 | 0 |
| financial_direct_sparse -> candidate_overlay_sparse | 48 | 12 | 0 |
| financial_direct_sparse -> candidate_overlay_survival | 48 | 8 | 0 |

## Current candidate-edge survival

| h | candidate source | target | survival | selection | OOS edge value | n |
|---:|---|---|---:|---:|---:|---:|
| 20 | pw_panama_canal_n_total_z | audusd | 0.965 | 0.99 | 3.86e-05 | 530 |
| 10 | pw_malacca_strait_capacity_z | brent | 0.905 | 0.99 | 0.000568 | 540 |
| 10 | pw_panama_canal_n_total_z | audusd | 0.880 | 0.90 | 1.72e-05 | 460 |
| 20 | pw_malacca_strait_n_total_z | wti | 0.813 | 0.90 | 8.26 | 350 |
| 20 | pw_strait_of_hormuz_capacity_z | brent | 0.807 | 0.82 | 0.00208 | 250 |
| 20 | pw_panama_canal_n_total_z | cnyusd | 0.754 | 0.79 | 1.63e-06 | 270 |
| 20 | pw_strait_of_hormuz_capacity_z | wti | 0.746 | 0.92 | 3.58 | 350 |
| 10 | pw_strait_of_hormuz_n_total_z | cnyusd | 0.700 | 1.00 | 1.01e-06 | 560 |
| 20 | pw_malacca_strait_n_total_z | brent | 0.651 | 0.72 | 0.00193 | 250 |
| 10 | pw_malacca_strait_capacity_z | wti | 0.459 | 1.00 | 1.74 | 560 |
| 5 | pw_panama_canal_n_total_z | audusd | 0.359 | 0.38 | 5.4e-06 | 65 |
| 20 | pw_cape_of_good_hope_capacity_z | audusd | 0.308 | 0.85 | 4e-06 | 390 |
| 10 | pw_bab_el_mandeb_strait_capacity_z | audusd | 0.269 | 0.57 | 3.08e-06 | 200 |
| 10 | pw_strait_of_hormuz_capacity_z | brent | 0.262 | 0.76 | 0.000244 | 340 |
| 5 | pw_malacca_strait_n_total_z | wti | 0.236 | 0.75 | 0.3 | 345 |

## Current model-level overlay gates

| h | target | gate | recent OOS value | t-stat | n |
|---:|---|---:|---:|---:|---:|
| 1 | audusd | 0.000 | 0 | 0.00 | 700 |
| 1 | brlusd | 0.000 | -5.22e-08 | -0.31 | 700 |
| 1 | cnyusd | 0.000 | -1.94e-09 | -0.14 | 700 |
| 1 | krwusd | 0.000 | -1.06e-07 | -0.46 | 700 |
| 1 | eurusd | 0.000 | -1.03e-08 | -0.15 | 700 |
| 1 | sp500 | 0.000 | -5.16e-08 | -0.17 | 700 |
| 1 | vix | 0.000 | -0.00248 | -0.27 | 700 |
| 1 | us2y | 0.000 | -4.98e-06 | -0.19 | 700 |
| 1 | us10y | 0.000 | -8.97e-06 | -0.47 | 700 |
| 1 | wti | 0.000 | -0.000731 | -0.14 | 700 |
| 1 | brent | 0.000 | -1.09e-06 | -0.62 | 700 |
| 1 | henry_hub | 0.000 | -6.55e-07 | -0.03 | 700 |
| 5 | audusd | 0.000 | -2.63e-07 | -0.49 | 696 |
| 5 | brlusd | 0.000 | -4.8e-06 | -0.90 | 696 |
| 5 | cnyusd | 0.000 | -1.98e-06 | -3.85 | 696 |
| 5 | krwusd | 0.000 | -2.43e-06 | -1.37 | 696 |
| 5 | eurusd | 0.000 | -2.39e-06 | -0.92 | 696 |
| 5 | sp500 | 0.000 | -1.09e-05 | -1.61 | 696 |
| 5 | vix | 0.000 | -0.358 | -2.03 | 696 |
| 5 | us2y | 0.000 | -0.000511 | -1.46 | 696 |
| 5 | us10y | 0.000 | -0.000488 | -1.59 | 696 |
| 5 | wti | 0.000 | -0.00945 | -0.01 | 696 |
| 5 | brent | 0.000 | -0.000266 | -1.43 | 696 |
| 5 | henry_hub | 0.000 | -0.000615 | -1.34 | 696 |
| 10 | brent | 0.936 | 0.00143 | 3.42 | 671 |
| 10 | audusd | 0.000 | -7.5e-05 | -5.10 | 671 |
| 10 | brlusd | 0.000 | -3e-05 | -1.92 | 671 |
| 10 | cnyusd | 0.000 | -7.12e-06 | -4.66 | 671 |
| 10 | krwusd | 0.000 | -1.64e-05 | -3.46 | 671 |
| 10 | eurusd | 0.000 | -1.24e-05 | -1.80 | 671 |
| 10 | sp500 | 0.000 | -4.28e-05 | -1.66 | 671 |
| 10 | vix | 0.000 | -0.166 | -0.75 | 671 |
| 10 | us2y | 0.000 | -0.00135 | -1.38 | 671 |
| 10 | us10y | 0.000 | -0.00147 | -2.40 | 671 |
| 10 | wti | 0.000 | -0.0507 | -0.08 | 671 |
| 10 | henry_hub | 0.000 | -0.000852 | -1.29 | 671 |
| 20 | brent | 0.976 | 0.0017 | 4.43 | 661 |
| 20 | wti | 0.929 | 13.9 | 3.31 | 661 |
| 20 | audusd | 0.529 | 2.28e-05 | 1.18 | 661 |
| 20 | brlusd | 0.000 | -9.97e-05 | -2.59 | 661 |
| 20 | cnyusd | 0.000 | -1.4e-05 | -5.23 | 661 |
| 20 | krwusd | 0.000 | -3.86e-05 | -2.59 | 661 |
| 20 | eurusd | 0.000 | -3.07e-05 | -1.80 | 661 |
| 20 | sp500 | 0.000 | -0.000183 | -2.82 | 661 |
| 20 | vix | 0.000 | -1.52 | -3.18 | 661 |
| 20 | us2y | 0.000 | -0.00201 | -0.94 | 661 |
| 20 | us10y | 0.000 | -0.00295 | -2.27 | 661 |
| 20 | henry_hub | 0.000 | -0.00659 | -2.18 | 661 |

## Interpretation

The financial model is the protected core. Candidate data are not allowed to replace
it. The sparse overlay is trained only on fully realised out-of-sample core residuals.
Candidate edges are scored by whether adding that edge to the core would have reduced
realised forecast loss. Surviving edges are refitted, then the entire overlay is shrunk
toward zero unless its own recent realised OOS performance is positive.

This is an online model-augmentation problem, not a claim of structural causality.
