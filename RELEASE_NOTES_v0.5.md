# v0.5 release notes

This release changes the centre of the project from *physical data as alpha* to the more
general problem exposed by empirical v1: **persistent coefficients can remain statistically
stable after their predictive value has died**.

## Frozen empirical v1

The public-data v1 evidence pack is now committed. Its central physical-data result is
negative/weak rather than hidden or re-labelled. This provides the empirical motivation for
v2.

## New v2 research engine

- direct cumulative 1/5/10/20-day forecasts;
- online leave-one-edge-out marginal forecast-loss attribution;
- no use of an edge's outcome before the whole horizon realises;
- exponentially decayed structural and predictive evidence;
- signal-survival scores and per-target survivor masks;
- post-selection Ridge refitting;
- horizon-aware HAC forecast tests;
- FDR across target/horizon pairs within nested comparison families;
- lifecycle plots and machine-generated v2 results note;
- explicit `development`, `reused_holdout`, and future `prospective` evaluation labels.

## Controlled demonstration

`artifacts/synthetic_signal_survival.png` shows a deliberately constructed regime change.
The LASSO edge remains selected with a stable sign after the true relationship changes, while
the OOS predictive-survival score collapses once recent realised contribution becomes harmful.
This is the exact failure mode v2 is designed to detect.

## Validation

The release contains 34 tests. All 34 pass when the optional native C++ library is built; on
a machine without a C++ compiler, the native parity test is skipped and the Python fallback
remains fully supported.
