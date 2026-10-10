# Developer Handoff — Dhan Historical Pipeline Offline Code Gate (Latest Exact Review Snapshot)

**State: SUBMITTED FOR INDEPENDENT CODE REVIEW. Live acquisition is NOT authorized.**  
**Exact code/test snapshot commit:** 79e7ae5b2a02841d83e4848b22be67980aab6096  
**Hosted offline regression:** [Run 38049609609](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049609609), success; **36 offline/mock tests passed**.  
**Hosted protocol check:** [Run 38049609776](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049609776), success.  
This revision supersedes all prior code handoffs. Its source/test blobs were pinned to the exact snapshot above.

## Exact files and Git blob SHA

| File | Git blob SHA |
|---|---|
| scripts/dhan_history_pipeline.py | 6533b11456efbaa99f470d5ca20887862c2ca6b3 |
| scripts/test_dhan_history_pipeline.py | e156c0915320a9ed075e8ba6d55857a56bca9f61 |
| .github/workflows/phase-07-dhan-history-pipeline-tests.yml | dc0de4688bfac5ee932c32ccd25fdd586effd3c2 |
| research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md | 9145f88ec99169a900d9ff2c7b77c0592781f5ae |
| Planning gate report on tester branch | d49298d7070cba557b1ccd31df39cdaad334a571 |

## Implementation controls

- Restricts POST requests to the three documented HTTPS api.dhan.co history endpoints: daily candles, intraday candles and rolling expired options. No profile/account/order endpoint is exposed.
- The request helper only accepts the literal boolean live_authorized=True; it defaults to False. Import and CLI are offline-only. The current workflow has read-only contents permission, no Dhan secret environment, and runs only offline/mocked tests plus an offline status CLI.
- Requires ASCII, nonempty, CR/LF-free token values if called; exact endpoint request-field allowlists; positive scalar numeric security IDs; nonempty exchange/instrument strings; permitted intervals/options; boolean OI; nonnegative expiry code; and required rolling-option fields.
- Enforces conservative inclusive calendar-date caps: daily <=365 calendar dates, intraday <=90 and rolling options <=30. Timezone-offset-bearing intraday input is rejected rather than silently reinterpreted.
- Uses a redirect-rejecting opener, 20-second timeout, 2 MiB response cap with cap+1 read, 8 MiB total budget, one-request default budget, minimum 3-second pacing, HTTP/content-type/Content-Length checks, object-only JSON and redacted exception messages.
- Validates positive integral strictly increasing timestamps; alignment of every list-valued response field; finite numeric values; nonnegative prices/volume/OI/IV/strike/spot; and consistent OHLC rows.
- Rolling-option validation checks aligned timestamp/OHLC/volume and any requested IV/OI/strike/spot arrays. Rolling moneyness is not treated as a complete contract-level historical chain or historical bid/ask.
- The request helper returns parsed JSON, redacted metadata and the original HTTP response bytes. Before cache creation, code binds byte count and SHA-256 to those original bytes, recomputes source-specific validation and compares the full validation report, validates exact request parameters, and verifies all timestamps fall inside the requested Asia/Kolkata date/time window. Cache bundles are content-addressed and atomically written only after every check passes.
- Cache metadata keys are screened for token/authorization/cookie-like names and unknown request keys. No cache write happens after a hash, schema, date-range or validation-report mismatch.

## Regression coverage and latest result

36 offline/mock tests cover import/CLI offline behavior, literal live-authorization gating, host/path/body allowlists, malformed/missing token checks and redaction, scalar instrument IDs, redirects/error-body non-reading, error redaction, content-type/Content-Length/byte caps, request/pacing budgets, OHLC arithmetic, timestamp validity/order, all-array alignment, rolling-option schemas, date/timezone/OI/strike constraints, exact raw response bytes, cache hash/byte-count binding, full validation-report recomputation, in-window timestamps, cache idempotence/atomic behavior, and credential-key rejection.

Hosted run 38049609609 passed all 36 tests. Hosted protocol run 38049609776 passed. Previous test failures and corrections are fully recorded in research/ERROR_LOG.md; all runs were offline and no failed run invoked Dhan.

## Explicit non-claims

This code gate has not made an actual Dhan API request. Token entitlement, actual response schemas, source coverage, quotas, date continuity and source quality remain unverified. No data cache was populated, no feature matrix/model rerun occurred, existing results are unchanged, and the untouched final holdout stays sealed. This code gate alone does not authorize a live request.

**Developer → Tester:** Independently inspect these exact blobs and hosted run. Review endpoint and request-body allowlists, credential boundary, literal authorization guard, redirects, timeout/byte/pacing/date limits, raw response-byte/hash contract, Asia/Kolkata time semantics, numerical and array validation, source-aware cache provenance/atomicity, secret redaction, tests and workflow permissions. Return PASS or REQUEST CHANGES. Do not authorize a live API request at this gate.

**Tester → Developer:** If the code passes, issue only a restricted authorization to prepare a fresh one-use manifest for a single tiny daily NIFTY index-history sample. The manifest must be independently reviewed before any API call. Bulk history, feature fitting and model reruns remain prohibited.
