# Developer Handoff — Dhan Historical Pipeline Offline Code Gate (Final Corrected Snapshot)

**State: CODE GATE PASSED WITH SCOPED RESTRICTIONS. Live acquisition is NOT authorized.**  
**Exact snapshot commit:** 986d78cf4e3297f203c4960493ef86e2a8663697  
**Hosted offline regression:** [Run 38050266592](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050266592), success; **42 offline/mock tests passed**.  
**Hosted protocol check:** [Run 38050266689](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050266689), success.

## Exact files and Git blob SHA

| File | Git blob SHA |
|---|---|
| `scripts/dhan_history_pipeline.py` | `84e30b0d45ffb2a9b6985601b934c66db435b201` |
| `scripts/test_dhan_history_pipeline.py` | `e58ffd6d4b4daf8e049c0be0c2edca44dc16a161` |
| `.github/workflows/phase-07-dhan-history-pipeline-tests.yml` | `dc0de4688bfac5ee932c32ccd25fdd586effd3c2` |
| `research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md` | `9145f88ec99169a900d9ff2c7b77c0592781f5ae` |
| Prior independent planning gate (tester branch) | `d49298d7070cba557b1ccd31df39cdaad334a571` |
| First independent code REQUEST CHANGES report (tester branch) | `e9c9d3f59f7e267ed317b250df529c03c5f9598d` |
| Final independent code PASS report (tester branch) | `f1218310778c95499e2d7958d47118a4065c0f94` (blob); report commit `9b396b7ff6acd549d9f44fa0599934b209ee61fa` |

## Corrections included

1. **Exclusive end dates:** daily and rolling-option requests use the documented non-inclusive toDate semantics for date caps and response-window checks. Intraday end-boundary semantics remain separately constrained because the documentation does not explicitly label its toDate inclusive/non-inclusive.
2. **Hard request/byte limits:** the current sample adapter enforces MAX_REQUESTS=1 and MAX_TOTAL_BYTES=8 MiB even if callers attempt to widen RequestBudget; existing state is revalidated before a request.
3. **Optional numeric arrays:** every present recognized numeric array, including daily open_interest, is checked for array shape, numeric type, finite values and non-negativity.
4. **Rolling-option optional arrays:** empty arrays are accepted only for unrequested optional fields. Requested arrays must align with timestamp; populated optional arrays must also align and pass numeric validation.
5. **Strike scope:** the current rolling-option source-feasibility scope only allows strike="ATM". Offset grids require a separately reviewed implementation change.
6. **Cache provenance boundary:** before writing, atomic_cache_bundle now requires HTTP status exactly 200, a JSON content type, exactly one request for this sample scope, cumulative response bytes equal to the exact raw payload length and within the 8 MiB total budget, and response hash/byte count equal to the raw bytes. Errors, missing metadata or mismatches leave the cache unchanged.

## Test evidence

The 42 offline/mock tests include URL/body allowlists, explicit live authorization, token validation/redaction, redirect rejection, HTTP error-body non-reading, content type and length, response caps, hard request/byte budgets, OHLC arithmetic, timestamp validity and alignment, optional OI values, rolling-option documented empty optional-array behavior, exclusive-end range caps and exact toDate rejection, ATM-only strike scope, raw-byte/hash validation, full report recomputation, cache request-scope provenance, metadata status/content-type/request-count/cumulative-byte failures and atomic no-write-on-error behavior.

Hosted [Run 38050266592](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050266592) passed 42/42. Protocol check [Run 38050266689](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050266689) passed. All failed test iterations are preserved in ERROR_LOG.md; no run has contacted Dhan or changed scientific results.

## Remaining unverified data facts and scope

- No Dhan API request has been made by this pipeline. Token entitlement, real response schemas, coverage, data continuity, quotas and source quality remain unverified.
- The expired-options page states a 30-day maximum and a non-inclusive toDate but its example uses 2021-08-01 through 2021-09-01 (31 calendar days difference). This implementation uses the conservative stated 30-day duration; actual API edge behavior must remain unverified until a separately approved bounded request.
- Intraday timestamp window behavior is checked against the supplied local-naive Asia/Kolkata request timestamps; the end-boundary meaning must be established against observed official responses before claiming complete coverage.
- No data cache was populated; no feature matrix/model rerun occurred; prior results remain unchanged; the final untouched holdout stays sealed.

## Authorization boundary

This submission is **code-review only**. The workflow at this path is offline-only, contents-read-only, has no Dhan secret environment and contains no network request step. Even a tester PASS only permits preparation of a separate fresh one-use manifest and guarded workflow for one tiny daily NIFTY history request. The manifest must itself be independently checked against exact hashes before any API call. Bulk history, rolling options, feature fitting, prediction reruns and holdout access require later separate gates.

**Developer → Tester:** Independently review this exact snapshot and latest hosted run. Confirm that findings 1–6 are resolved, especially source-specific date arithmetic and cache metadata enforcement. Return PASS or REQUEST CHANGES. Do not authorize live data acquisition in the code review.

**Tester → Developer:** If the exact code and regression suite pass, issue code-only PASS with restrictions. Separately review a fresh one-use manifest before any request; no bulk download or model run is authorized by this report.
