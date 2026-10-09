# Phase 7 Available-Data Prediction Extension

## Status and boundary

**Pre-registered proposal — NOT empirically authorized until the independent tester approves the exact source and code snapshot.**

This is a prediction-only extension on `phase-07-developer`; the independent review belongs on `phase-07-tester`. It does not open Phase 8, select option trades, or supersede the frozen Phase 6/7 results. It responds to the instruction to continue testing methods with currently available or freely obtainable historical data rather than ending a method solely because one source layer is absent.

## Research question

Do point-in-time-safe global/peer-market price changes available before a NIFTY decision improve out-of-sample NIFTY direction forecasts beyond a causal historical-rate baseline?

## Included, fixed candidate universe

The implementation will attempt the following public historical daily reference series, preserving exact provider, symbol, local timezone, date coverage, cache status, and SHA-256. A source that fails to acquire will be marked unavailable; other candidates continue.

- Peer India indices: SENSEX (`^BSESN`) and NIFTY Bank (`^NSEBANK`) — partial probes for G01/G02.
- Global equities: S&P 500 (`^GSPC`), Nasdaq Composite (`^IXIC`), Nikkei 225 (`^N225`), Hang Seng (`^HSI`) — G04/G05/G06.
- Context series to probe: Cboe VIX (`^VIX`), USD/INR (`INR=X`), gold futures (`GC=F`), crude futures (`CL=F`), and India VIX (`^INDIAVIX`) — partial tests for G08/G09/G11/G12/G16 where the source is genuinely returned by the public endpoint.
- G13 available-equity composite: arithmetic mean of the latest available prior-date 1-session and 5-session log returns for the four global equity indices that pass coverage validation. At least two of the four must be available; the exact series included is frozen in the acquisition manifest before metrics are generated.
- G18 weekday/calendar control: weekday indicators and fixed annual-cycle sine/cosine terms only. It is explicitly **not** a complete expiry/holiday-effect test.

Daily index/asset direction forecasts are evaluated for close-to-close horizons `{1,2,3,5,10}` NIFTY sessions. This extension does not claim that currently available data can substitute for historical FII/DII publication timestamps, news archives, point-in-time option IV/Greeks, historical bid/ask quotes, or full historical market breadth.

## Point-in-time and data rules

1. Use only free/public source downloads and the repository's existing NIFTY daily source. No paid data are required.
2. Existing cached files are reused and hashed. New files are not checked into Git if large; compact manifests and experiment outputs are retained as workflow artifacts.
3. Convert source timestamps to each instrument's reported exchange timezone using the provider's timezone metadata.
4. For NIFTY session date d, cross-market predictors may use only source observations whose local session date is **strictly earlier than d**. Use backward as-of joins with exact-date matches disabled. This conservative rule avoids using a source close that might occur after the NIFTY decision.
5. Compute 1/5-session log returns and 20-session realized volatility from each source's own strictly chronological close series. No backward fill, future fill, or revised snapshot overwrite.
6. Each model uses an expanding chronological training sample, minimum 252 eligible labeled rows, 20-session test blocks, fixed logistic regression `C=1.0`, training-only means/scales, and a purge of the last H training-label rows before each test block. No parameter or feature selection is performed from the test results.
7. A failed source does not abort unrelated candidates. Candidates requiring an absent source are explicitly BLOCKED_DATA; an available G13 composite is formed only from the pre-run manifest's validated constituent set.
8. No final untouched holdout is opened or selected on. Current reports are development-period screening evidence only.

## Evaluation

For every source candidate and horizon, report status/reason, source list, sample size, positive rate, accuracy, balanced accuracy, ROC-AUC, PR-AUC, Brier score, log loss, confusion counts, and calibration/probability diagnostics where defined. Reconcile confusion counts and metric denominators independently.

The benchmark probability is the positive-label rate estimated only from the eligible pre-test training prefix. For each horizon, test the maximum Brier improvement among executed candidates using a moving-block bootstrap (seed 42, 500 replicates, block length 20 sessions), recentered under the no-improvement null. Report raw family p-values and a Bonferroni-adjusted value across the five horizons. This family test is screening evidence and does not by itself establish generalizability.

## Gate sequence

1. Developer: submit this immutable method scope, acquisition/data-lineage code, implementation, and regression tests.
2. Tester: independently review feature timestamps, as-of joins, horizon labels, training/purge logic, test leakage, method grid, statistical test, source failure behavior, and numerical checks.
3. No empirical run before explicit tester PASS for the exact protected code/spec snapshot.
4. Run one hosted, cached-data-backed execution with artifact retention.
5. Tester independently audits exact source commit, source manifest, result schema, row alignment, metrics and family inference.
6. Fix failures through a new reviewed snapshot and new run; rejected runs remain non-evidence.
7. Update README, research status, logs and error log regardless of outcome.

## Interpretation limits

AUC/accuracy slightly above 0.5 or a raw best candidate is not a discovery. The family is only a predictive-information screen; robustness, full method-universe coverage, final untouched-forward evaluation, and any later economic work are separate gates. No option/trading strategy is created or selected here.

## Required handoff

**Developer → Tester:** Independently audit the entire exact snapshot and report PASS, PASS WITH SCOPED RESTRICTIONS, or REQUEST CHANGES. Do not rely on developer claims or empirical output.

**Tester → Developer:** Return a reproducible report listing checks, failures, protected-file hashes, exact reviewed commit, and whether one empirical run is authorized. Block execution on any scientific or integrity defect.
