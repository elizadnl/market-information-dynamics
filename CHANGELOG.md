## 0.4.0 — clean restart release

- Consolidates all v0.3.1-v0.3.3 hotfixes into a fresh repository release.
- Replaces the large historical PortWatch query with small per-chokepoint/year requests.
- Adds a resumable local PortWatch cache under `data/cache/portwatch`; reruns reuse completed years.
- Keeps TLS verification enabled through the native OS trust store and retains retry/backoff handling.
- Uses `python -m market_information_dynamics.cli` in scripts so Windows PATH configuration is not required.
- Adds a regression test proving cached PortWatch chunks are reused on restart.
- Test suite: 25 passing tests plus one optional native-backend skip when the C++ library is not built.

## 0.3.3 — PortWatch query resilience hotfix

- Resolve chokepoint names against PortWatch's dedicated 28-row chokepoint catalogue instead of running a DISTINCT scan over the 78k+ row daily table.
- Increase the default ArcGIS read timeout from 30s to 90s and retry transient timeout/connection errors with exponential backoff.
- Push coarse start/end year filters into the daily ArcGIS query to reduce payload and server work.
- Add a regression test for retry behaviour and lock catalogue-based name resolution.

## 0.3.2 — Windows TLS trust-store hotfix

- Use PyPA `truststore` so HTTPS clients can validate certificates against the native OS trust store.
- Keep TLS verification enabled; no `verify=False` bypass is used.
- Fixes managed-Windows environments where ArcGIS/PortWatch certificates are trusted by Windows but not by Requests' bundled CA set.

## v0.3.1

- Fix WTI transformation in the empirical universe: DCOILWTICO can be negative, so WTI now uses first differences instead of log returns.
- Add a regression test locking the WTI transformation.

# Changelog

## v0.3.0 — empirical research engine

- Added full pre-specified public-data ablation: AR, financial sparse VAR, full sparse VAR,
  and historical edge-stability-filtered full VAR.
- Locked a 2025-01-01 onward final holdout before inspecting real results.
- Added HAC paired forecast-loss tests and Benjamini-Hochberg FDR across targets.
- Added 7/14/21-day PortWatch availability-lag sensitivity runner.
- Replaced the baseline physical transform with a strictly past-only 52-week seasonal
  anomaly for the real experiment.
- Added automatic panel audits, result tables, figures and generated `RESULTS.md`.
- Added keyless FRED CSV fallback; an API key remains optional/preferred when available.
- Made PortWatch date parsing and chokepoint name resolution robust to live-schema/name
  variation (including the canonical `Malacca Strait` name).
- Added one-command PowerShell and bash research runners.
- Expanded the no-network test suite to 22 passing tests, including the empirical ablation,
  forecast tests, seasonal future-invariance and masked stability predictions.
