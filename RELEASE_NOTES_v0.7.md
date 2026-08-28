# v0.7 — online expert aggregation and prospective freeze

v0.7 stops tuning the historical candidate-overlay gate and reframes the final decision layer as
an online-learning problem.

## New

- Causal Fixed-Share exponential weighting between the protected financial core and the
  survival-filtered candidate overlay.
- Horizon-delayed updates: h-step forecast losses cannot alter expert weights until the full
  h-step outcome is observable.
- Bounded, causally normalised squared-loss updates and a self-confident Hedge learning rate.
- Small fixed-share probability mass so a previously weak expert can recover after a regime
  change.
- Pre-specified share sensitivity reported as diagnostics rather than used for cherry-picking.
- Empirical-v4 runner that consumes the already-generated v3 forecast evidence; no PortWatch
  redownload is required.
- Synthetic regime-switch test showing the candidate expert gains weight when informative and
  loses it after its signal dies.
- Prospective protocol frozen for September-2026 onward.
- Frozen empirical-v3 and empirical-v4 findings notes.

## Real diagnostic evidence

On reused 2025+ history, Fixed-Share beats the raw survival-overlay expert in 42/48
comparisons. It does not robustly beat the financial core: the primary rule gives about +0.11%
mean RMSE skill vs the core at 20 days, while shorter horizons are slightly negative, and no
comparison survives FDR correction.

The repository therefore makes no alpha claim. The methodological object is dynamic trust in
forecast models under non-stationarity.
