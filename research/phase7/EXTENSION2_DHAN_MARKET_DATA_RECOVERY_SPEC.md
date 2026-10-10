# Extension 2 — DhanHQ Market-Data Recovery

**Status: PROPOSED — implementation/offline tests only; no authenticated requests authorized yet.**  
**Developer branch:** `phase-07-developer`. **Independent tester branch:** `phase-07-tester`.  
**Requested secret:** GitHub Actions secret `DHAN_ACCESS_TOKEN`. Never print, echo, commit, hash, or include the token in an artifact/log.  
**Current source gate:** the prior one-run FII/DII manifest is spent. It cannot be reused for this step.

## 1. Research question

Can DhanHQ's authenticated Data APIs safely supply auditable historical NIFTY/index, equity, futures and options OHLC/OI data that are missing from current public-source coverage, while preserving point-in-time validity, source provenance, cost/coverage disclosure and the project's independent review gates?

A separate question is whether DhanHQ provides a compatible daily FII/FPI and DII cash-flow aggregate. The documented Historical Data endpoints return instrument candles (OHLC, volume and optionally open interest); they are **not documented as FII/DII flow endpoints**. Do not relabel instrument candles or FPI-only transaction records as FII/DII aggregate flows.

## 2. Aims and objectives

1. Test whether the secret is present and accepted without exposing its value or account/profile fields.
2. Verify Data API subscription/entitlement and token validity from HTTP status/error metadata only; never persist the profile response or identity fields.
3. Resolve instrument identifiers from an official, pinned Dhan instrument master; do not guess security IDs.
4. Establish schema and date coverage for a small daily-candle sample for NIFTY 50 and, if the official instrument master supports it, India VIX.
5. Determine whether Dhan's documented expired-options endpoint can provide historical NIFTY options and OI, and record entitlement/retention/expiry limits before any bulk pull.
6. Record the distinction between Dhan price/derivative candles and the still-unresolved FII/FPI/DII aggregate flow features.
7. If the sample passes a separate artifact gate, submit a new full-acquisition plan for review; do not silently download history or run models.

## 3. Official documentation reviewed

- DhanHQ v2 historical data: https://dhanhq.co/docs/v2/historical-data/
- DhanHQ v2 authentication: https://dhanhq.co/docs/v2/authentication/
- DhanHQ instrument list: https://dhanhq.co/docs/v2/instrument-list/
- DhanHQ expired options data: https://dhanhq.co/docs/v2/expired-options-data/

Documentation says daily candles can extend back to an instrument's inception, while intraday candles are limited to the last five years and can be requested for at most 90 days per call. Daily historical requests use `POST https://api.dhan.co/v2/charts/historical`; the end date is non-inclusive. Data APIs may require a separate subscription. Access tokens generated from Dhan Web are valid for 24 hours. These conditions must be verified against the actual account's response without exposing personal data.

## 4. Fixed proposed request scope — only after a fresh tester-approved manifest

The implementation must define a shared request/byte budget, URL allowlist, strict timeouts, response caps, bounded retries (default zero), redacted errors, and no automatic date-range widening.

### A. Authentication / entitlement probe
- One GET to `https://api.dhan.co/v2/profile` using `DHAN_ACCESS_TOKEN` in the `access-token` header.
- Store only HTTP status, a boolean token-validity result, whether the data-plan field is active, and a redacted error category. Discard the response body immediately; never persist client ID, name, UCC, active segments, token validity timestamp, or any raw profile JSON.
- If unauthorized/expired, missing secret, or data plan inactive, stop all further calls and report the category only. Do not attempt token renewal or login automation.

### B. Instrument identity
- Use the official segment-specific endpoint `GET https://api.dhan.co/v2/instrument/IDX_I` to resolve index metadata. The official docs describe this endpoint as returning instruments for one exchange segment. Enforce a 1 MiB transport cap, no redirect, 20-second timeout and no retry.
- Resolve NIFTY 50 and India VIX IDs by exact official symbol/segment/instrument metadata. Reject ambiguous or multiple mappings; do not guess or silently select the first match.
- Do not download the unbounded all-instrument CSV in this phase. If `IDX_I` is not a parseable supported response, stop and propose a separately reviewed fallback rather than widening the request.

### C. Daily candle schema sample
- At most two instruments (NIFTY 50 and India VIX, if resolved unambiguously), and at most two non-overlapping fixed windows of ten calendar days each. Total at most four daily-candle POST requests.
- Exact endpoint: `https://api.dhan.co/v2/charts/historical`.
- Request uses the resolved `securityId`, `exchangeSegment`, `instrument`, `fromDate`, `toDate`; `toDate` is exclusive.
- Per daily-candle response: maximum 768 KiB; reject non-JSON, error JSON, arrays of unequal length, missing required fields, non-finite OHLC, invalid OHLC inequalities, duplicate timestamps, dates outside the requested interval, or unsorted timestamps.
- Persist only these bounded sample rows, request/response hashes, schema checks and coverage summary after a separately approved sample. Never persist auth headers or token-bearing URLs.
- Do not call order, position, fund, account, or trade endpoints. No orders may be placed.

### D. Options-data feasibility
- Read the official expired-options documentation and endpoint schema offline first.
- No expired-options endpoint request is in the initial sample budget. A later options-specific proposal must pin instrument, expiry, strike/option-type scope, dates, response caps, entitlement, and adjustment/expiry semantics.
- Do not infer historical option premiums/OI from current option-chain snapshots.

### E. Request budget
- Maximum 1 profile request + 1 segment-specific instrument metadata request + 4 historical daily-candle requests; total maximum 6 authenticated requests in the first sample.
- Maximum total response bodies 4 MiB across the run; profile body is discarded and must be bounded at transport level (64 KiB maximum); index-segment metadata is capped at 1 MiB.
- Per-request timeout 20 seconds; no retry, no redirect, no fallback to a different host. If a response exceeds a cap, abort and mark the source unverified.
- Workflow must not run a source request unless offline tests pass and the one-run exact-snapshot manifest validates. The manifest is consumed before the first request. Any changed protected blob invalidates it.

## 5. Research questions and acceptance criteria

1. **Secret/token:** is `DHAN_ACCESS_TOKEN` present, valid and unexpired? Report only `present/missing`, HTTP status category and validity boolean.
2. **Entitlement:** is historical Data API access enabled? Report only active/inactive/unknown.
3. **Instrument identity:** are instrument IDs uniquely mapped from official metadata?
4. **History:** does the sample contain dated candles for the exact requested windows with valid aligned OHLCV fields and credible timestamp conversion?
5. **Data limitations:** are missing sessions exchange holidays, API gaps, instrument inception limits or access restrictions?
6. **Cost/terms:** is a Data API subscription required/active, and what retention/rate-limit constraints are documented?
7. **FII/DII:** Dhan candles alone do not solve aggregate FII/FPI/DII data. That source bottleneck remains open unless a distinct official compatible endpoint is documented and separately approved.

A sample can pass schema feasibility while historical coverage or entitlement remains insufficient. Do not interpret a schema PASS as complete dataset availability.

## 6. Prohibited actions at this stage

- No live authenticated requests before a new exact-snapshot tester code PASS and a new single-use manifest.
- No full-history download, cache population from broad ranges, feature/label construction, model fitting, predictive metrics/p-values, strategy testing or final-holdout access.
- No trading/order endpoint calls.
- No exposure of `DHAN_ACCESS_TOKEN` in logs, artifacts, exception strings, workflow summaries, or committed files.
- No use of Dhan price/option data as a proxy for FII/DII flow.
- No claim that this token resolves all data gaps until source coverage is measured and independently audited.

## 7. Proposed phases and gates

1. **D0 — Design:** this spec and endpoint semantics reviewed.
2. **D1 — Offline implementation:** import-safe adapter, strict parser, redaction and budget manager; no network calls in unit tests.
3. **D2 — Independent code gate:** tester verifies exact source/test/workflow blobs, token redaction, request caps and fail-closed workflow.
4. **D3 — One-run authenticated sample:** only after new hash-bound single-use manifest; five requests maximum and fixed dates only.
5. **D4 — Independent artifact audit:** tester verifies response hashes, sample schemas, dates, coverage, source identity, entitlement and absence of secrets.
6. **D5 — Full acquisition proposal:** only if sample and entitlement pass; define bounded chunking, cache manifests, provenance, reconciliation and exact scope. It needs another separate review/manifest.
7. **D6 — Research data integration:** after full-acquisition approval, join on exchange session/date with explicit publication/vintage lag, missingness and source conflicts.
8. **D7 — Prediction rerun:** only after data integration audit, time-ordered split review and a separate modeling authorization. Include transaction costs only if/when moving from prediction to strategy evaluation.

The plan is finite; stop after D4 if the sample/entitlement fails. Do not endlessly retry or broaden the endpoints.

## 8. Literature/research interpretation

Dhan historical candles can potentially improve price/volatility/volume/derivative coverage. They do not, by themselves, establish an FII/DII flow history or news/sentiment dataset. The research manuscript must separate source availability, predictive performance and any later trading strategy conclusions. Do not report model results until a new authorized analysis actually runs.

**Developer → Tester:** Review this exact proposal before any implementation can reach live data. Verify official endpoint semantics, token redaction, entitlement checks, request/byte budgets, fixed windows, and the fact that this does not claim to replace FII/DII flows.

**Tester → Developer:** Keep all live requests disabled until the exact implementation/workflow snapshot receives a code-gate PASS and a new single-use manifest. After one approved sample, audit the artifact separately; no full-history acquisition or model fitting is authorized by this spec.
