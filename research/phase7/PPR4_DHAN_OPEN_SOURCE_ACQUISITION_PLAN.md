# PPR-4 Dhan-first / free-source continuation plan

**Date:** 2026-10-11  
**Branch:** `phase-07-developer`  
**Status:** DRAFT — exact-snapshot tester review required before live acquisition  
**Policy:** `research/phase7/PPR4_USER_DIRECTED_DATA_CONTINUATION_POLICY.json`  
**User acceptance waiver:** `research/gates/DHAN_SAMPLE_USER_ACCEPTANCE_WAIVER.json`

## 1. Binding decisions

The user explicitly instructed that Dhan output is to be accepted as provided, with no Dhan-versus-NSE/third-party market-value cross-check, and that research must not stop because an individual source or feature family is unavailable. This plan implements those decisions.

The existing Dhan one-row sample is accepted for development research under the user waiver. Its raw bytes, request parameters, timestamps and SHA-256 remain immutable. No further cross-source reconciliation will be requested as a prerequisite. Structural checks (JSON/CSV parseability, field lengths, timestamps, duplicate keys, time zones, hash verification and internal OHLC constraints) remain appropriate data-pipeline checks; they are not a comparison against another provider. Do not silently adjust a Dhan value to match any other source.

The past single-use approval is still `SPENT`. Never reuse it. A separate exact-snapshot source-acquisition manifest and tester PASS are required for the next multi-request historical acquisition. That gate exists to bound and reproduce the acquisition, not to make research contingent on every feature source succeeding.

## 2. Initial Dhan acquisition wave

Provider docs currently describe daily history back to instrument inception, intraday candles up to five years with at most 90 days per request, and rolling expired-option data up to five years with at most 30 days per request. The documented Data API limit is 5 requests/second and 100,000 requests/day. Implement lower serial pacing, immutable per-chunk cache, checkpoints and resumable execution.

| Dataset | Primary Dhan operation | Proposed coverage | Fields | Request policy |
|---|---|---|---|---|
| NIFTY 50 daily index | `POST https://api.dhan.co/v2/charts/historical` | Earliest returned history through 2026-10-10; deterministic calendar-year chunks if needed | timestamp, OHLC, volume | Begin with one bounded schema-checked request; then fetch chronological year shards under a new exact manifest |
| NIFTY 50 intraday index | `POST https://api.dhan.co/v2/charts/intraday` | Five-year provider window ending 2026-10-10 | 1-minute OHLCV; derive 5/15/30/60-minute bars from raw 1-minute data using session-aware aggregation and verify aggregation invariants | Calendar chunks no longer than 90 days; maximum 16 MiB/response; checkpoint each shard before proceeding |
| NIFTY index options — expired/rolling | `POST https://api.dhan.co/v2/charts/rollingoption` | Five-year provider window ending 2026-10-10 | 5-minute OHLC, IV, volume, OI, absolute strike, spot; relative-strike identifier retained | Calendar chunks no longer than 30 days; weekly/monthly expiry selection kept as separate fields; CALL/PUT separate; start ATM ±5, expand to ATM ±10 only where pre-registered tasks need it |
| Dhan public instrument list | Published compact/detailed CSV URL in official docs | Current mapping metadata only | Security ID, segment, instrument, underlying, expiry/strike/type/lot/tick fields when present | Use only to aid request configuration and effective-dated contract metadata; per user's instruction it is not a price-value cross-check |

Provider references:
- [Historical candles](https://dhanhq.co/docs/v2/historical-data/)
- [Expired/rolling options](https://dhanhq.co/docs/v2/expired-options-data/)
- [Instrument list](https://dhanhq.co/docs/v2/instruments/)
- [Rate limits](https://dhanhq.co/docs/v2/)

The initial option pull is deliberately based on rolling options with OHLC/IV/OI/volume/spot, rather than the current option-chain endpoint; current chain values must not be mistaken for historical snapshots. The current option-chain API is not treated as a historical archive.

### 2.1 Dhan request execution controls

- Read `DHAN_ACCESS_TOKEN` only from the GitHub Actions secret at runtime. Never echo it, store it in a data artifact, or write it to logs.
- Check token/API error responses in memory, then log only redacted status/error codes. If authentication or subscription fails, record the failure and move to free-source fallbacks; do not terminate unrelated source jobs.
- Use a conservative serial limit of at most 2 requests/second despite the documented ceiling of 5/second; implement a daily request budget well below 100,000.
- Write each successful response to a unique immutable cache shard with endpoint, exact parameters, UTC fetch time, schema version, response length, SHA-256, row count, date bounds and code hash. Verify cache hits locally and reuse them; never redownload valid shards.
- On response-size cap, split the approved date interval deterministically into smaller non-overlapping chunks. On a repeated schema/HTTP/auth failure, mark that source shard failed and continue fallback acquisition. Do not loop indefinitely or silently alter requested fields.
- Log every failed shard, HTTP status, retry decision, fallback source and terminal disposition in `research/ERROR_LOG.md` and machine-readable per-run reports.
- Keep provider-native response payloads immutable; normalized data are separate versioned products with lineage to raw shard hashes.
- Public repository commits must respect source terms and size limits. Store eligible compact canonical datasets in `data/cache`; retain large sharded payloads as immutable workflow artifacts/content-addressed files where Git repository size or data license makes direct Git commits inappropriate. The cache manifest must make reuse deterministic.

## 3. Free-source fallback matrix

If Dhan does not provide a required field, date range or dataset, run this matrix for that feature family. A single source failure never stops unrelated families.

| Feature family | First fallback(s) | Later fallback(s) / composite rule |
|---|---|---|
| NIFTY daily OHLC/TRI | Official [NSE Indices historical archive](https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives) | Existing audited historical research artifact for development-only method prototyping; documented free mirrors only if licenses and row lineage are usable. Do not compare accepted Dhan values against alternatives as a condition of acceptance. |
| NIFTY intraday | Dhan 1-minute history | Specific GitHub/Kaggle/Hugging Face dataset with explicit schema/license/provenance; downshift only the intraday candidate cells to `NOT_ESTIMABLE` if no usable fallback remains, and continue daily/positional methods. |
| NIFTY options EOD/OHLC/OI | Official [NSE derivatives reports / UDiFF bhavcopy](https://www.nseindia.com/all-reports-derivatives) | Public archive mirrors such as [NSE-FNO-Data-bank](https://github.com/SantoshSrinivas79/NSE-FNO-Data-bank); HF datasets only after license/provenance review. Preserve the 2024-07-08 format change as a versioned parser boundary. |
| Historical option IV/Greeks/relative-strike data | Dhan rolling expired-options API | Free research datasets and exchange EOD reports. Infer Greeks only from same-time available option/spot/rate/dividend inputs under a versioned model convention; never invent missing quote history. |
| India VIX | Official NSE India VIX history/methodology | If official historical series is temporarily inaccessible, use a separately labeled India-volatility proxy only for proxy-compatible experiments; do not relabel Cboe VIX as India VIX. |
| FII/FPI/DII | NSE aggregate FII/DII and derivatives-participant reports | [CDSL FPI archive](https://www.cdslindia.com/Publications/ForeignPortInvestor.html), [SEBI FPI archives](https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html), or licensed/reproducible public datasets. FPI-only must not be mislabeled as DII or total institutional flow. |
| Global indices / volatility | Cboe VIX, exchange-published prices where freely available | Documented free APIs/mirrors such as Yahoo Finance or Stooq for fallback features; preserve market-local close and availability time in IST. |
| FX / rates / crude / gold / macro | RBI reference rates, US Treasury yield curve, EIA data | FRED/World Bank/other public central-bank and government archives; gold source licensing checked per series. |
| News / event / sentiment | GDELT public event/news infrastructure | Open-licensed dated news/event corpora or HF/Kaggle datasets if publication time, license and leakage risk can be audited. Static sentiment datasets are not a substitute for historically available news. |
| Corporate actions / trading calendar | NSE and BSE official archives/calendar | Public calendar libraries for fallback/session detection, with official session overrides when retrievable; record source and confidence. |
| Historical contract master, lot size, expiry and tick regime | Dhan contract metadata plus NSE/BSE official contract archives | Public dated contract files; do not backfill historical lot size from today's contract master. |

The current 34-source register remains the starting index; source discovery is not exhausted. The source acquisition wave should search the official sources and open datasets first, then add new source rows as justified. Paid sources must not be considered until documented free-source paths are exhausted for the required feature.

## 4. Composite-data rules

1. Retain `source_id`, `source_version`, `retrieved_at_utc`, `observed_at`, `available_at`, `source_timezone`, raw SHA-256, license basis and transformation hash per source row or source shard.
2. Normalize timestamps to UTC and preserve source-local time. For global markets convert true local close to IST with daylight-saving rules. Feature eligibility is based on `available_at <= decision_time`.
3. Merge on explicit index/contract/session keys. Use deterministic as-of joins for asynchronous series and report staleness; do not assume same calendar date means information was available at decision time.
4. Keep official, Dhan, community and synthetic sources as distinct provenance tiers. Composite data means combining non-conflicting fields or filling gaps while retaining each row's original source—not overwriting Dhan values to match another provider.
5. No zero-imputation for missing prices, option quotes, IV, OI, news sentiment or institutional flows. Missingness is a feature/quality flag only where preregistered and scientifically defensible.
6. Feature family data coverage is measured separately. Run eligible model cells on their pre-registered feature set. If a family has no viable data, set only those cells `NOT_ESTIMABLE`; continue with remaining cells and report the limitation.
7. Do not substitute proxy series under the original feature name. A proxy creates a separately named feature/candidate with its own pre-result registration.
8. Keep raw, normalized and model-panel artifacts separate. A failed parser should quarantine that shard and let other sources continue; no destructive cache overwrite.

## 5. Research continuation / no-source-stop rule

The only global stops are security breaches, scope/rate-limit violations, unresolvable data-integrity/leakage hazards in the affected artifact, or a required independent governance gate not yet passed. **Missing data alone is never a global stop.**

When a feature source fails:
1. record the failed source, reason, timestamp, status code and request/hash context without credentials;
2. attempt the next pre-listed free alternative within its own license and request rules;
3. combine compatible free sources into a lineage-preserving composite where scientifically valid;
4. if still absent, mark the specific field/family/horizon as `NOT_ESTIMABLE` with a row/cell coverage report;
5. continue unaffected feature families, literature replications, baselines, methods, documentation and statistical analyses;
6. resume the failed family if another approved source later becomes available, without revising prior result records silently.

No phase may claim complete coverage when fields are absent. The programme is still expected to complete every finite registered phase and provide a manuscript that contains negative, partial and source-limited results. Research is not declared complete merely because one source is inaccessible.

## 6. Gates and immediate next step

The accepted one-row sample is covered by the user waiver, and no cross-source price check is required. The single-use sample authorization must remain spent. A new bulk Dhan/free-source manifest should now pin the exact first acquisition shards, date bounds, fields, row/byte/request caps, cache destinations, fallback handling and protected scripts/workflows. The isolated tester reviews that exact snapshot and hosted offline tests before the live acquisition workflow is allowed to call endpoints.

The first live wave should prioritize:
1. Dhan daily NIFTY history and a small schema-controlled first intraday window;
2. Dhan intraday history in resumable 90-day shards;
3. Dhan expired rolling options in resumable 30-day shards at five-minute cadence, ATM ±5 first;
4. free-source acquisition for VIX, official derivatives/participant data, institutional flows, cross-market/macro, news and calendar/corporate actions;
5. composite panel generation with immutable source lineage and field-level missingness;
6. feature/label generation and development-only prediction runs after the required execution/holdout gates pass.

The exact manifest and runtime workflow still need their own tester gate. That governance requirement is not a claim that data is unavailable and must not be used to stop unrelated research work.

## 7. Provenance and reproducibility

Every step produces:
- source/request manifest and approval hash;
- raw response SHA-256, request parameters and source version;
- byte/row/date/schema report;
- fallback decision and errors;
- cache hit/miss and output-hash report;
- developer commit and CI run ID;
- tester report and disposition;
- updated status, research log and error log.

The Dhan access token is injected only as a secret into the live request step. No value, prefix, suffix or token-derived reversible string is written to artifacts.
