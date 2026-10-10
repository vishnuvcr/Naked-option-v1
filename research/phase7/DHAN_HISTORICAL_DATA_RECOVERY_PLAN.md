# Phase 7 Amendment — Dhan Historical Data Recovery and Prediction Re-run

**Status: PROPOSED — plan amendment for independent tester review. No live API request, bulk download, feature fitting, model rerun or holdout access is authorized by this document.**

**Reason for amendment:** the current prediction checkpoint is based on a narrower dataset than the registered data plan. In particular, prior cross-market daily work did not test the missing NSE option-history/OI/IV and intraday features. User has now directed the research to use the available Dhan Data API to address those gaps. This plan replaces a metadata-only next-step as the primary objective; instrument metadata remains a prerequisite, not the research outcome.

## 1. Research questions

1. Does adding Dhan-backed NIFTY intraday and daily OHLCV improve out-of-sample direction prediction over the already-tested baseline?
2. Do point-in-time features from expired-option OHLC, IV, OI, volume, strike-relative-to-spot and spot context add incremental information at intraday and positional horizons?
3. How much previously blocked method/horizon coverage can be recovered without pretending that rolling ATM-relative expired-option data is a complete historical option chain?
4. Are any improvements robust to chronological testing, family-wise/multiple-testing correction, regime splits, source/coverage changes and missing-data stress?
5. Which registered predictors remain unavailable after using official Dhan history plus free official NSE/BSE/SEBI sources and carefully documented composite data?

## 2. Official Dhan API capabilities and bounds

Documentation references (checked 2026-10-10):
- Historical candles: https://dhanhq.co/docs/v2/historical-data/
- Expired options: https://dhanhq.co/docs/v2/expired-options-data/
- Instrument list: https://dhanhq.co/docs/v2/instruments/
- Live option chain: https://dhanhq.co/docs/v2/option-chain/
- Dhan API Data API access/plan explanation: https://dhan.co/support/platforms/dhanhq-api/how-to-use-algo-in-dhan/

Documented endpoint scope:
- Daily candles: `POST https://api.dhan.co/v2/charts/historical`; daily data is documented back to each instrument's inception. Request uses security ID, exchange segment, instrument, date interval and optional derivative OI.
- Intraday candles: `POST https://api.dhan.co/v2/charts/intraday`; intervals 1/5/15/25/60 minutes and up to five years for active instruments. Dhan says requests must be limited to 90 calendar days per call.
- Expired rolling options: `POST https://api.dhan.co/v2/charts/rollingoption`; documented up to five years and up to 30 days per call, with minute-level rolling moneyness (ATM and permitted strike offsets), OHLC, IV, volume, OI, strike and spot fields. Index-option offsets are documented up to ATM +/-10 near expiry; support for every historical contract/expiry is not assumed.
- Live option chain: `POST https://api.dhan.co/v2/optionchain`; it returns current option-chain observations, including OI, IV, Greeks, volume, LTP and best bid/ask. It is not a historical-chain archive and must not be backfilled as if historical.
- Instrument lists: the public CSV URLs are documented at https://dhanhq.co/docs/v2/instruments/. Security ID/segment mappings must be versioned as-of data acquisition; present-day master rows do not establish historical point-in-time availability.

A valid token does not itself establish active Data API entitlement. Expired tokens, entitlement failures, rate limits and unexpected responses must be logged only with safe status metadata; never log access tokens, profile identity, cookies or raw provider error bodies.

## 3. Workstream and gated phases

### Gate 0 — Freeze and scope
- Tester reviews this amendment against the current Phase 7 method registry, Run #44 audit, Extension 2 proposal and Phase 7 status.
- Keep the current result table and untouched final holdout immutable.
- Current scope remains **prediction only**; no options P&L/strategy optimization in this amendment.

### Gate 1 — Instrument mapping and entitlement smoke test
- Reuse only tester-approved code and a newly pinned single-use manifest.
- Test public CSV acquisition separately from authenticated API calls; do not forward Dhan credentials to `images.dhan.co`.
- A minimal authenticated source probe must request a small, non-sensitive date window from one documented historical endpoint only after a fresh code/tester gate and a fresh one-use manifest.
- Do not call the profile endpoint merely to collect private account metadata. API responses must be summarized without identity fields.
- Record HTTP status, request count, bounded byte count, response schema/status, range, timestamp, content hash and safe rejection reason.
- No feature engineering/model fitting at this gate.

### Gate 2 — Daily reference history
- Acquire NIFTY 50 index daily candles and India VIX daily candles if their official instrument mappings and endpoint support are verified.
- Build an independent validation against available official NSE/NSE Indices reference observations and existing project cache, where overlapping fields/ranges exist.
- Require monotonic timestamps, OHLC inequalities, nonnegative volume/OI where meaningful, duplicate detection, reasonable trading-session calendar coverage, timezone/date-boundary verification and source-level provenance.
- Partition by instrument and date range; immutable content hashes and schema versions; cache only after validation.
- Do not overwrite earlier snapshots. Record corrections as new versions.

### Gate 3 — Intraday reference history
- Start with NIFTY index 1-minute bars, using strictly bounded 90-calendar-day chunks. Build 5/15/30/60/120-minute features only from completed prior bars, never by leaking future intrabar highs/lows into the decision timestamp.
- In a later separately approved step, add India VIX and index futures if mapping, coverage and request budget pass.
- Check timezone, missing/duplicate bars, market sessions, timestamp monotonicity, OHLC inequalities and overlap with official NSE intraday sample data where available.
- Do not infer bid/ask executability from candles.

### Gate 4 — Expired-option history (research predictors only)
- Begin with small 30-day windows for NIFTY index rolling options; explicitly enumerate documented interval, expiryFlag/expiryCode, strike-relative and option-type parameters.
- Test response semantics and exact array alignment for timestamp, OHLC, IV, OI, volume, strike and spot. Fail closed if arrays mismatch, units are ambiguous or dates/moneyness cannot be reconstructed.
- Expand chronologically only after the small-sample artifact receives independent tester approval and a separate authorization manifest.
- Treat this source as a rolling moneyness sample, not a complete contract-level chain. Never imply that it supplies historical top-of-book bid/ask if it does not.
- Feature construction must respect only fields observable by each historical decision time. Do not use same-bar close/IV/OI in predictions made before that bar is complete.
- Add registered OI/volume/IV/relative-strike features only through a frozen amendment to the method specification; no post-result feature shopping.

### Gate 5 — Composite market data recovery
- For global/peer daily series, NSE sector leadership, advances/declines, FII/FPI and DII flows, corporate actions, calendar/events and news/sentiment, continue to exhaust official/free sources first.
- Dhan is not assumed to supply these series unless official API documentation explicitly supports the fields.
- Merge only after independent per-source validation, timezone/availability-time normalization, overlap analysis, explicit precedence and row-level source lineage.
- If publication timestamps cannot be established, mark the feature as delayed/unsafe and exclude it from point-in-time model features rather than silently using it.

### Gate 6 — Frozen prediction re-run
- Preserve prior Run #44 and Phase 7 Run #994 results as historical baselines; do not mutate their data or results.
- Pre-register the amended features/method cells and the primary family-wise test before seeing new model metrics.
- Re-run identical accepted baselines first, then the additive feature families. Use chronological walk-forward splits and training-only preprocessing; maintain the sealed final holdout.
- Report coverage and missingness for every method/horizon before performance, plus Brier/log-loss/AUC/PR-AUC, accuracy against naive baselines, calibration, block-level stability, family bootstrap/max-statistic inference and corrected p-values.
- No candidate is promoted on a best cell, unadjusted p-value, or descriptive metric.

### Gate 7 — Independent empirical audit
- Tester independently reconstructs source manifests, split cutoffs, labels, data joins, feature timestamps, missingness, cell coverage, key metrics and multiple-testing calculations from immutable inputs/artifacts.
- Any mismatch invalidates the artifact; correct and rerun from a new immutable run. Never overwrite or relabel rejected evidence.
- Only after PASS may an amended dataset/model result enter the project status table.

### Gate 8 — Research synthesis
- Update status, error log, research log, chat/decision log, README and GitHub Pages research output with data coverage, download manifests, validation diagnostics, rejected sources, results and limitations.
- Keep Phase 8 option execution, cost-aware strategy P&L, Phase 9 robustness, Phase 10 fresh-forward and Phase 11 manuscript as separately gated phases; do not pretend prediction-only evidence is a profitable strategy.

## 4. Acquisition and security controls

- No live request until the exact implementation/tests/workflow snapshot has independent approval and a fresh single-use manifest binds the exact commit and protected Git blob/SHA-256 values.
- Separate workflows by purpose: (a) offline validation; (b) one-run source feasibility; (c) approved bounded bulk acquisition. Manual workflow dispatch remains available, but automated triggers must not bypass manifest checks.
- Historical candle/rolling-option calls use a strict host/path/method allowlist, timeouts, disabled redirects, request and total-byte budgets, request pacing, date-window limits, response schema validation, redacted errors and no order endpoints.
- Send credentials only to the documented `https://api.dhan.co` host and only where the endpoint requires them. Never send token/client ID/cookies to a redirect target or public CSV host.
- Spend authorization before any live call. An expired/spent manifest is never reused.
- Cache validated data by source/segment/instrument/range/schema; resume missing partitions from cache and hashes rather than redownloading good partitions. Never partially accept a corrupt response.
- Data larger than an appropriate Git-tracked cache should be stored as versioned compressed dataset artifacts with immutable manifests/hashes; GitHub Pages carries summaries/plots/manifests, not raw multi-gigabyte files. Any external dataset store must remain versioned and accessible to the research workflow.
- All errors are recorded without secret values, personal account fields, raw provider error bodies or sensitive query parameters.

## 5. Acceptance criteria

1. Documented endpoint and entitlement are verified by observed bounded response, not assumption.
2. Daily/intraday datasets have schema, date coverage, bar-count, quality and overlap reports.
3. Expired-option arrays and rolling moneyness semantics are validated before use.
4. Snapshot lineage, cache hashes, data versions and exact request scopes are reproducible.
5. Method/horizon coverage is explicit; no blocked-data cell is silently dropped.
6. Amended statistical tests are frozen before results and the untouched final holdout stays sealed.
7. Independent tester signs off every implementation, acquisition artifact and empirical artifact.
8. Every run updates phase status and durable logs, whether it succeeds or fails.

## 6. Known limitations that must remain visible

- Historical option chain bid/ask snapshots may still be unavailable; rolling-option candles are not a quote feed.
- Dhan's rolling option history is relative to ATM and has documented strike-offset limits; it may not provide every contract or every required timestamp.
- Some flow/breadth/news/corporate-action variables may need official external sources or remain blocked.
- API quotas, entitlements, endpoint behavior and actual data coverage must be observed in gated runs.
- Data quality or stronger prediction metrics do not alone establish tradable edge.

## 7. First implementation sequence

1. Tester approves this plan amendment.
2. Developer builds and tests a no-network source client for historical daily/intraday and expired rolling-option endpoints, plus parser/alignment/manifest/cache tests.
3. Tester reviews exact code/workflow snapshot and all mocked failure cases.
4. Developer prepares a fresh manifest for a tiny spot-history sample only.
5. Tester audits that sample before any further acquisition.
6. Proceed in separate bounded gates to intraday sample, rolling-option sample, then partitioned bulk acquisition.
7. Freeze data and amended feature/method registry before model reruns.
8. Run and independently audit empirical prediction experiment; only then report conclusions.

**Developer → Tester:** Review this amendment as a proposal. Check that API endpoints/capabilities and rate/range constraints are supported by official docs, that prediction-only scope is preserved, and that the gate order prevents unaudited bulk download or model fitting. Return PASS/REQUEST CHANGES; do not authorize a live request at this stage.

**Tester → Developer:** Do not implement live calls, create a live manifest, acquire data or rerun models before the plan amendment passes this independent review.
