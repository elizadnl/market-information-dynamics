## 0.5.0 — predictive edge survival

- Freezes the first real public-data evidence pack in `artifacts/empirical_v1_public/`.
- Records the empirical-v1 null result instead of hiding it: the baseline PortWatch layer did
  not robustly improve one-day forecasts beyond financial history and produced no FDR-significant
  incremental improvements.
- Adds direct multi-horizon sparse forecasts for 1, 5, 10 and 20 trading-day cumulative targets.
- Adds edge-level marginal OOS loss attribution with horizon-realisation gating.
- Replaces lifetime edge persistence with exponentially decayed structural and predictive evidence.
- Adds post-selection Ridge refitting after sparse edge discovery.
- Adds nested AR → financial → full → survival forecast comparisons with horizon-aware HAC lags
  and Benjamini-Hochberg FDR by comparison family.
- Explicitly relabels 2025+ as a reused holdout in v2 because it was inspected during v1;
  prospective validation begins with future observations from September 2026 onward.
- Adds signal-lifecycle plots and a generated empirical-v2 evidence note.
- Test suite expanded to 33 passing tests plus one optional native-backend skip.

## 0.4.0 — clean restart release

- Consolidates all v0.3.1-v0.3.3 hotfixes into a fresh repository release.
- Replaces the large historical PortWatch query with small per-chokepoint/year requests.
- Adds a resumable local PortWatch cache under `data/cache/portwatch`; reruns reuse completed years.
- Keeps TLS verification enabled through the native OS trust store and retains retry/backoff handling.
- Uses `python -m market_information_dynamics.cli` in scripts so Windows PATH configuration is not required.
- Adds a regression test proving cached PortWatch chunks are reused on restart.

## 0.3.3 — PortWatch query resilience hotfix

- Resolve chokepoint names against PortWatch's dedicated chokepoint catalogue instead of a DISTINCT scan over the daily table.
- Increase ArcGIS read timeout and retry transient timeout/connection errors with exponential backoff.
- Push start/end year filters into daily ArcGIS requests.

## 0.3.2 — Windows TLS trust-store hotfix

- Use PyPA `truststore` so HTTPS clients validate certificates against the native OS trust store.
- Keep TLS verification enabled; no `verify=False` bypass is used.

## 0.3.1 — WTI negative-price fix

- Use first differences for WTI because the April 2020 negative-price episode makes log returns undefined.
- Add a regression test locking the transformation.

## 0.3.0 — first empirical research engine

- Added AR, financial sparse VAR, full sparse VAR and historical edge-stability-filtered ablation.
- Locked a 2025-01-01 onward reporting holdout before the first real run.
- Added HAC paired forecast-loss tests, FDR, PortWatch lag sensitivity and automatic evidence pack.
