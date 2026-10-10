# Developer Handoff — Dhan Historical Pipeline Offline Code Gate

**State: SUBMITTED FOR INDEPENDENT CODE REVIEW. Live acquisition is NOT authorized.**  
**Reviewed code snapshot commit:** `c4b6bc5a06f296bb8765e6facd85c2d8e396eb53`  
**Hosted offline regression:** [Run 38049058737](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049058737), success; **30 offline/mock tests passed**.  
**Hosted protocol check:** [Run 38049058835](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049058835), success.

## Exact files and Git blob SHA

| File | Git blob SHA |
|---|---|
| `scripts/dhan_history_pipeline.py` | `6e1bca4c2c565d3fe54e6b2e848bd9528c74439a` |
| `scripts/test_dhan_history_pipeline.py` | `df7495af90450097db42a82b7572b9ed65f17d9f` |
| `.github/workflows/phase-07-dhan-history-pipeline-tests.yml` | `dc0de4688bfac5ee932c32ccd25fdd586effd3c2` |
| `research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md` | `9145f88ec99169a900d9ff2c7b77c0592781f5ae` |
| Planning gate report on tester branch | `d49298d7070cba557b1ccd31df39cdaad334a571` |

## What the implementation does

- Restricts POST requests to the three documented HTTPS `api.dhan.co` history endpoints: daily candles, intraday candles and rolling expired options. It does not expose profile/account calls or order endpoints.
- Has an explicit `live_authorized=False` guard on the request helper; import and CLI are offline-only. The only committed workflow for this addition runs offline tests and has no Dhan secret environment.
- Enforces endpoint-specific body-field allowlists, non-empty instrument identifiers, interval enums, daily <=365-calendar-day code-level partitions, intraday <=90-calendar-day window limit, rolling option <=30-calendar-day window limit and required data-field constraints.
- Uses a redirect-rejecting opener, timeout, 2 MiB response cap, cap+1 overflow read, 8 MiB global response budget, default one-request budget, minimum 3 second pacing and response-size/content-type/JSON validation.
- Rejects duplicate/out-of-order timestamps, array-length mismatches, malformed/non-finite/negative fields and inconsistent OHLC rows. Rolling option arrays are checked for timestamp alignment and required IV/OI/volume/strike/spot fields where requested.
- Creates a content-addressed cache bundle only after re-computing source-specific validation against the raw response, matching row count and timestamp hash, and validating the exact request manifest. Atomic replacement and secret-key/unknown request-field checks are covered by tests.
- Does not infer historical bid/ask from rolling option candles and does not treat the live option-chain endpoint as historical.

## Offline regression coverage

Thirty tests include: import/CLI offline behavior, explicit live guard, URL/host/method field restrictions, token missing/malformed and metadata redaction, no redirect follow or error-body read, non-JSON responses, Content-Length errors, cap+1 handling, request and pacing budgets, OHLC schema/invariants, duplicate timestamps, rolling-option array alignment and value constraints, date-window and timezone constraints, cache hash/idempotence, cache validation recomputation, no cache on mismatched validation and secret-key rejection.

## Failed iterations and corrections

The full failures are recorded in `research/ERROR_LOG.md`. In brief: two mocked HTTPError tests initially inspected a body after the wrapper closed it; the cache-manifest key test exposed missing detection of `auth_token`; several mock response tests initially failed at the newly added request-body validation rather than reaching response handling; and the cache idempotence fixture initially omitted the full request parameters. Those were corrected, then the final 30-test hosted run passed. No failed run performed a live request or generated scientific metrics.

## What is not claimed

- No Dhan API request was made by this new pipeline.
- No live credential was exposed to the new workflow.
- No actual Dhan response schema, entitlement, range coverage, quota or source quality has been verified by this pipeline.
- No data cache was populated, no feature matrix/model rerun occurred, no prediction result changed, and the untouched holdout remains sealed.
- This code gate does not authorize a live request. A fresh exact-snapshot one-use manifest and a separately guarded manual workflow will be a further gate after tester approval.

**Developer → Tester:** Independently inspect these exact blobs and the hosted run. Check request-body allowlisting, token/header boundaries, redirects, timeout/byte/rate budgets, all arithmetic and timestamp cases, historical vs rolling-option schema semantics, source-aware cache revalidation, atomicity, secret redaction, test completeness and workflow permissions. Return PASS or REQUEST CHANGES. Do not authorize a live request at this gate.

**Tester → Developer:** If the implementation passes, issue a restricted code-gate report authorizing preparation of a fresh one-use manifest for a *single tiny daily NIFTY index-history sample only*. The manifest must be reviewed separately before any actual API request; no bulk history or model rerun is authorized.
