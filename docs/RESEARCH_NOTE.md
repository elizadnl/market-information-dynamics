# Research note — Market Information Dynamics

## Abstract

This project studies a practical quantitative-research problem: **how should a forecasting system change its trust in predictive models when relationships are non-stationary?** The original empirical hypothesis asked whether public maritime activity from IMF PortWatch added predictive information to a financial-market model. That hypothesis did not survive out-of-sample testing or multiple-testing correction. Rather than discard the failed experiment, the project used it to motivate a broader framework for signal survival, protected baselines and online model selection.

The final architecture contains a financial-only core model, a candidate-data overlay trained only on historical out-of-sample core residuals, edge-level realised forecast-loss attribution, recency-weighted survival diagnostics and causal Fixed-Share expert aggregation. Forecast horizons are 1, 5, 10 and 20 trading days. Evaluation uses expanding walk-forward estimation, delayed information admission, horizon-aware HAC forecast tests and Benjamini–Hochberg FDR control. Historical 2025–2026 evidence is explicitly treated as reused diagnostic history; the current methodology is frozen prospectively from 1 September 2026.

The project does **not** claim statistically robust trading alpha. Its central result is methodological: persistence of a fitted relationship is not equivalent to persistence of predictive value, and an adaptive model-selection layer can materially reduce losses from a decaying candidate model.

## 1. Motivation

Quantitative signals are rarely stationary. A variable can be selected repeatedly, retain the same sign and still stop helping forecasts. This creates two distinct research questions:

1. **signal discovery:** is there predictive information in the candidate data?
2. **signal trust:** after a relationship is discovered, how much evidence should be required before it is used, and how quickly should the system stop trusting it?

The second question became the focus of the project after the first real-data alternative-data experiment failed.

## 2. Data

The public empirical system uses two layers.

### Financial core

Daily FRED series span FX, equities, volatility, rates and energy. Twelve targets are evaluated over direct 1, 5, 10 and 20 trading-day horizons.

### Candidate information

IMF PortWatch chokepoint activity provides the deliberately difficult alternative-data layer. The project does not treat current historical API data as though it were a perfect real-time vintage archive: physical features receive an explicit availability lag and the original empirical stage reports sensitivity to nearby lag assumptions.

No employer or proprietary data are included.

## 3. Point-in-time design

A datum may enter the feature set only when it could reasonably have been available. All scaling, sparse selection, edge diagnostics and expert-weight updates are causal. For an `h`-step forecast, the realised target cannot update any model-trust statistic until the complete `h`-step outcome is observable.

This rule matters particularly at longer horizons because overlapping outcomes can otherwise leak information into model selection.

## 4. Research stages

### v1 — physical-data ablation

The first experiment compared:

- target-only autoregression;
- financial-only sparse VAR;
- financial + physical sparse VAR;
- a cumulative coefficient-stability filter.

The baseline PortWatch layer did **not** robustly improve the financial-only model. Mean one-day incremental RMSE skill was approximately `-0.10%`, and no improvement survived Benjamini–Hochberg FDR correction. This result is frozen rather than removed.

### v2 — predictive edge survival

v1 exposed a more interesting failure: repeated coefficient selection did not imply useful future forecasts. v2 therefore added direct multi-horizon models and edge-level out-of-sample attribution.

For a selected source–target edge, the system compares the realised squared loss with and without that edge:

```text
ΔL_edge,t = L_without_edge,t - L_with_edge,t
```

Positive values indicate that the edge helped the realised forecast. Survival state combines recent structural persistence with realised predictive contribution, and old evidence decays exponentially.

This reduced some candidate-model damage but did not reliably beat the financial core.

### v3 — protected financial core

The next failure was architectural. A candidate-data model could still damage forecasts even when individual edges appeared stable. v3 therefore protected the financial model and asked candidate information to predict only the historical **out-of-sample residuals** left by that core.

The final forecast takes the form:

```text
y_hat = y_hat_core + g_t * residual_hat_candidate
```

where the overlay weight is zero when recent realised candidate contribution is poor.

This strongly reduced damage relative to the unrestricted candidate model, but on reused 2025+ history it beat the financial core in only 12 of 48 target–horizon comparisons, with no FDR-significant gains.

### v4 — online model trust

The hand-built gate in v3 was still heuristic. The final stage reframes model choice as an online-learning problem. The protected financial core and survival-filtered candidate overlay are treated as forecast experts.

For bounded realised expert loss `ℓ_k,t`, Fixed-Share updates:

```text
w~_k,t+1 ∝ w_k,t exp(-η_t ℓ_k,t)

w_k,t+1 = (1 - α) w~_k,t+1 + α / K
```

The share term allows a previously weak model to recover after a regime switch instead of being permanently eliminated.

On reused 2025+ history, Fixed-Share beat the raw survival-overlay expert in **42/48** target–horizon comparisons. Relative to the protected financial core, the primary rule was slightly negative at 1/5/10 days and approximately `+0.11%` mean RMSE skill at 20 days. No target–horizon improvement survived FDR correction.

The correct interpretation is therefore not that alternative data generate alpha. The narrower result is that online model aggregation materially reduces damage from a weak or decaying candidate model.

## 5. Statistical safeguards

The main safeguards are:

- expanding walk-forward evaluation;
- no random train/test split for time-series claims;
- direct horizon-specific forecasting;
- point-in-time availability rules;
- causal residual training;
- delayed `h`-step loss admission;
- horizon-aware HAC inference for overlapping targets;
- Benjamini–Hochberg FDR correction across pre-specified test families;
- frozen historical evidence packs;
- a prospective methodology freeze rather than repeated tuning on the same diagnostic window.

## 6. Controlled falsification

Synthetic environments provide known ground truth.

One experiment deliberately removes a true predictive edge while the sparse model continues selecting it. The survival score must learn that structural persistence is insufficient.

A second experiment makes the candidate forecast expert genuinely useful early and deliberately worse after a regime switch. The online aggregator must increase candidate weight while it helps and shift back toward the core when it deteriorates.

These tests are designed to falsify the mechanism, not to advertise synthetic performance.

## 7. Engineering

The research code is Python-first. C++17 accelerates lagged design-matrix construction only because profiling identified it as a repeated deterministic hot path. The native backend has exact parity tests against Python, CI coverage, a benchmark and an automatic Python fallback.

The repository also includes resumable public-data caching, TLS trust-store handling, tests for the WTI negative-price edge case, and regression tests for point-in-time alignment.

## 8. Limitations

The project intentionally keeps several limitations visible:

- PortWatch historical observations are not a perfect archived real-time vintage feed.
- The 2025–2026 period was reused during method development and is not confirmatory evidence.
- The candidate domain is currently narrow, so generalisation to other alternative datasets remains untested.
- No target–horizon improvement survives FDR correction in the reused historical diagnostics.
- Predictive edges are not structural causal claims.

These limitations are why the current methodology is frozen prospectively rather than tuned again on the same history.

## 9. Prospective evaluation

The statistical rule is frozen for observations from **1 September 2026 onward**. Model-class, horizons, expert set, primary share parameter, loss timing, evaluation metrics and multiple-testing procedure are specified in `docs/prospective_protocol.md`; SHA-256 hashes of the frozen configuration and key model files are recorded in `docs/prospective_manifest.json`.

The next meaningful evidence is prospective performance under that frozen rule, not another historical optimisation pass.

## Conclusion

The project began as an alternative-data prediction experiment and became a study of **when predictive models should stop being trusted**. Its strongest contribution is not a backtest return or an alpha claim; it is a reproducible research path showing how null results can motivate better model-selection questions, how forecast utility can be separated from coefficient persistence, and how online learning can adapt model trust in a non-stationary environment.
