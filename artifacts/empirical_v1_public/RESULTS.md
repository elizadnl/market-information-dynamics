# Empirical v1 results

This file is generated from the walk-forward outputs. It reports predictive evidence,
not causal effects and not a claim of deployable alpha.

**Assumed PortWatch availability lag:** 10 calendar days.

**Forecast reporting segment:** final_holdout.

## Incremental physical-data forecast skill

Positive values mean the full financial+physical model has lower RMSE than the
financial-only sparse VAR on the same OOS dates.

| target | incremental RMSE skill |
|---|---:|
| brent | 0.35% |
| wti | 0.05% |
| audusd | 0.03% |
| krwusd | 0.01% |
| vix | -0.08% |
| sp500 | -0.12% |
| eurusd | -0.13% |
| us2y | -0.14% |
| brlusd | -0.14% |
| cnyusd | -0.27% |
| us10y | -0.27% |
| henry_hub | -0.45% |

## Paired forecast tests

| target | DM stat | p-value | FDR reject | full better |
|---|---:|---:|:---:|:---:|
| wti | 0.255 | 0.7987 | no | yes |
| brent | 0.876 | 0.3810 | no | yes |
| audusd | 0.310 | 0.7564 | no | yes |
| krwusd | 0.179 | 0.8580 | no | yes |
| cnyusd | -0.946 | 0.3442 | no | no |
| eurusd | -1.614 | 0.1065 | no | no |
| brlusd | -0.523 | 0.6010 | no | no |
| sp500 | -0.757 | 0.4492 | no | no |
| us2y | -0.501 | 0.6162 | no | no |
| us10y | -1.745 | 0.0811 | no | no |
| henry_hub | -1.399 | 0.1618 | no | no |
| vix | -1.651 | 0.0988 | no | no |

## Most persistent predictive edges

| source | target | selection freq. | mean strength | sign stability |
|---|---|---:|---:|---:|
| wti | brent | 1.00 | 0.373 | 1.00 |
| pw_panama_canal_n_total_z | henry_hub | 1.00 | 0.253 | 1.00 |
| pw_suez_canal_capacity_z | pw_bab_el_mandeb_strait_capacity_z | 1.00 | 0.228 | 1.00 |
| sp500 | krwusd | 1.00 | 0.213 | 1.00 |
| sp500 | audusd | 1.00 | 0.204 | 1.00 |
| eurusd | krwusd | 1.00 | 0.170 | 1.00 |
| sp500 | eurusd | 1.00 | 0.151 | 1.00 |
| us2y | krwusd | 1.00 | 0.149 | 1.00 |
| pw_malacca_strait_n_total_z | pw_malacca_strait_capacity_z | 1.00 | 0.109 | 1.00 |
| us2y | cnyusd | 1.00 | 0.106 | 1.00 |
| sp500 | cnyusd | 1.00 | 0.103 | 1.00 |
| eurusd | sp500 | 1.00 | 0.087 | 1.00 |
| us2y | eurusd | 1.00 | 0.080 | 0.97 |
| sp500 | brlusd | 1.00 | 0.074 | 1.00 |
| cnyusd | us10y | 1.00 | 0.072 | 1.00 |

## Interpretation rule

A positive physical-data result is treated as interesting only if it is paired,
out-of-sample, survives the pre-specified availability-lag sensitivity, and is not
driven by a single target or short episode. Otherwise it is reported as weak/negative evidence.
