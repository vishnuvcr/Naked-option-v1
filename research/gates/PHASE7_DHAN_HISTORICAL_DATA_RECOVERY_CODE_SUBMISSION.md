# Developer Handoff — Dhan Historical Pipeline Offline Code Gate (Final Review Snapshot)

**State: SUBMITTED FOR INDEPENDENT CODE REVIEW. Live acquisition is NOT authorized.**  
**Exact code/test snapshot commit:** 53f1b4545a07d7d649245de5566620d67f80a82d  
**Hosted offline regression:** [Run 38049465398](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049465398), success; **34 offline/mock tests passed**.  
**Hosted protocol check:** [Run 38049465680](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049465680), success.  
This handoff supersedes earlier submissions: the final additional change preserves original HTTP response bytes so byte count and SHA-256 can be tied to the exact data cached.

## Exact files and Git blob SHA

| File | Git blob SHA |
|---|---|
| scripts/dhan_history_pipeline.py | 6ee45470df7fbdf17887de5bbef7b2dbf09c3ec6 |
| scripts/test_dhan_history_pipeline.py | 4f95962e95343b0e677971c432ee1c975c723bbb |
| .github/workflows/phase-07-dhan-history-pipeline-tests.yml | dc0de4688bfac5ee932c32ccd25fdd586effd3c2 |
| research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md | 9145f88ec99169a900d9ff2c7b77c0592781f5ae |
| Planning gate report on tester branch | d49298d7070cba557b1ccd31df39cdaad334a571 |

## Implementation controls

- Restricts POST requests to the three documented HTTPS api.dhan.co history endpoints: daily candles, intraday candles and rolling expired options. No profile/account/order endpoint is exposed.
- The request helper defaults to live_authorized=False. Import and CLI are offline-only. The current workflow has read-only contents permission, no Dhan secret environment, and only runs offline/mocked tests plus the offline status CLI.
- Enforces exact endpoint request-field allowlists; instrument-field presence; permitted intervals and option types; boolean OI; required rolling-option fields; and conservative inclusive date-window caps (daily <=365 calendar dates, intraday <=90, rolling options <=30).
- Rejects timezone-offset-bearing intraday requests rather than silently reinterpreting them.
- Uses a redirect-rejecting opener, 20-second timeout, 2 MiB per-response cap with cap+1 read, 8 MiB total byte budget, one-request default budget, 3-second minimum pacing, HTTP/content-type/Content-Length checks, object-only JSON and redacted error handling.
- Validates positive integral strictly increasing timestamps; array lengths for all list-valued fields; finite numeric fields; nonnegative prices/volume/OI/IV/strike/spot; and OHLC consistency.
- Rolling-option validation checks aligned timestamp/OHLC/volume and any requested IV/OI/strike/spot arrays. It does not treat rolling moneyness as a complete contract-level historical chain or historical bid/ask.
- The response helper returns parsed JSON, redacted metadata and original response bytes. Cache logic requires original response size and SHA-256 metadata to match those exact bytes, recomputes source-specific validation and compares the full validation report, validates exact request parameters, verifies timestamps remain inside the requested Asia/Kolkata window, and writes content-addressed cache bundles atomically.
- Cache metadata checks reject token/authorization/cookie-like keys and unrecognized request parameters. No cache write happens when schema, hash, date range or validation report mismatches.

## Regression coverage and latest outcome

34 tests cover offline import/CLI, explicit live-authorization guard, URL and request-body allowlists, no token leak, redirect rejection/no error-body read, HTTP error redaction, content type/Content-Length/body caps, pacing/request budgets, candle/OHLC arithmetic, timestamp validity/order, all-array alignment, rolling-option validation, date/timezone/OI constraints, exact response bytes, cache hash and byte-count binding, cache validation equality, timestamp range enforcement, atomic/idempotent cache and credential-key rejection.

Hosted offline run 38049465398 passed all 34 tests. Hosted protocol run 38049465680 passed. The failure history and corrections from earlier versions is in research/ERROR_LOG.md. These were offline harness/integration failures and no failed run invoked Dhan.

## Explicit non-claims

No actual Dhan API request has been made by this new pipeline; token entitlement, real response schemas, source availability, quotas, coverage and data quality remain unverified. No cache has been populated, no features/model rerun occurred, empirical results remain unchanged, and the untouched final holdout stays sealed. This code gate alone does not authorize a live request.

**Developer → Tester:** Independently inspect these exact blobs and hosted run. Review endpoint/request-body allowlisting, credential boundaries, redirect handling, rate/byte/date limits, response-byte/hash contract, timezone/timestamp semantics, arithmetic and array validation, cache provenance/atomicity, log redaction, tests and workflow permissions. Return PASS or REQUEST CHANGES. Do not authorize live acquisition at this gate.

**Tester → Developer:** If it passes, issue only a restricted authorization to prepare a fresh one-use manifest for a single tiny daily NIFTY index-history sample. The manifest requires a separate review before a request. No bulk history, feature fitting or model rerun is authorized.
