# Developer Handoff — Dhan Historical Pipeline Offline Code Gate (Revised Snapshot)

**State: SUBMITTED FOR INDEPENDENT CODE REVIEW. Live acquisition is NOT authorized.**  
**Exact code/test snapshot commit:** 61c33eb8c0bf56fe2a01967c78b86295e618d8e8  
**Hosted offline regression:** [Run 38049314836](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049314836), success; **34 offline/mock tests passed**.  
**Hosted protocol check:** [Run 38049314978](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049314978), success.  
This snapshot supersedes the earlier handoff revision; the source code was further hardened before requesting review.

## Exact files and Git blob SHA

| File | Git blob SHA |
|---|---|
| scripts/dhan_history_pipeline.py | d483901227770b560b695ce051a131aced02dacf |
| scripts/test_dhan_history_pipeline.py | 8cbe345a1abde1a9c5470e5953fa5ab3a7fc3b47 |
| .github/workflows/phase-07-dhan-history-pipeline-tests.yml | dc0de4688bfac5ee932c32ccd25fdd586effd3c2 |
| research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md | 9145f88ec99169a900d9ff2c7b77c0592781f5ae |
| Planning gate report on tester branch | d49298d7070cba557b1ccd31df39cdaad334a571 |

## What the implementation does

- Restricts POST requests to the three documented HTTPS api.dhan.co history endpoints: daily candles, intraday candles and rolling expired options. It does not expose profile/account calls or order endpoints.
- The request helper has an explicit live_authorized=False default. Import and CLI are offline-only. The committed workflow has only read permissions, no Dhan secret environment, and runs offline/mock tests plus an offline status CLI.
- Enforces exact endpoint request-field allowlists, instrument-field presence, interval/option type enums, boolean OI flag, nonnegative expiry code and required rolling-option fields.
- Enforces conservative inclusive calendar-date caps: daily <=365 calendar dates, intraday <=90 calendar dates, rolling expired-options <=30 calendar dates. Timezone-offset-bearing intraday requests are rejected rather than silently reinterpreted.
- Uses a redirect-rejecting opener, timeout, 2 MiB response cap with cap+1 read, 8 MiB total response budget, one-request default budget, minimum 3-second pacing, status/content-type/Content-Length/JSON checks and redacted exception messages.
- Rejects duplicate/out-of-order/nonpositive/nonintegral timestamps, array-length mismatches (including all additional response arrays), malformed/non-finite/negative numeric fields and inconsistent OHLC rows.
- Validates rolling-option timestamp alignment and requested OHLC/volume/IV/OI/strike/spot arrays where fields were requested. It does not represent rolling-option candles as a complete contract history or historical bid/ask data.
- Before cache creation it recomputes source-specific schema validation, requires exact validation-report equality, validates the exact request manifest and verifies all returned timestamps fall inside that request’s Asia/Kolkata date/time window. It stores content-addressed response and manifest files via atomic directory replacement. Cache metadata keys are screened for credential-like names and unknown request keys.

## Offline regression coverage

34 tests cover offline import/CLI, explicit live authorization guard, exact endpoint allowlist, request-body field allowlists, missing/malformed token guards and no token leak, redirect rejection and zero reads from HTTP error streams, HTTP error redaction, content type/Content-Length/byte caps, request count/pacing, candle schemas and OHLC arithmetic, timestamp positivity/integrality/order, all-array alignment, rolling-option schemas/signs, endpoint intervals/range windows/timezone constraints, daily OI type, cache idempotence, recomputed validation equality, request-window timestamp checks, bad JSON/empty validation, atomic cache and credential-key rejection.

## Failed iterations and corrections

All observed failures are recorded in research/ERROR_LOG.md, including the harness failures found in prior runs. They involved closed mock streams, credential-key detection, tests not yet updated to the strengthened request/cache contract, inclusive calendar-day counting, and deterministic fixture timestamps outside their declared request window. Corrections were made and the final hosted 34-test run passed. No failed run performed a live request or generated scientific metrics.

## Explicit non-claims

- This new pipeline has made no actual Dhan API request; the actual response schema, entitlement, quota, date coverage and live source quality remain unverified.
- No market-data cache was populated and no feature matrix/model rerun occurred. Existing empirical results remain unchanged, no predictor has been promoted, and the untouched final holdout remains sealed.
- This code gate does not authorize a live request. A new one-use manifest and separate guarded workflow will be prepared only after the independent tester passes this exact snapshot.

**Developer → Tester:** Independently inspect these exact blobs and hosted run. Check endpoint/request-body allowlisting, credential boundaries, redirects, timeout/byte/rate/date limits, response and timestamp semantics, every array and numerical invariant, cache lineage/atomicity, secret redaction, test coverage and workflow permissions. Return PASS or REQUEST CHANGES. Do not authorize live acquisition at this gate.

**Tester → Developer:** If the code gate passes, issue only a restricted authorization to prepare a fresh one-use manifest for a single tiny daily NIFTY index-history sample. The manifest must be reviewed separately before any API request. Do not authorize bulk history, feature fitting or model reruns.
