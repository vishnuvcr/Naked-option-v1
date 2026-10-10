# Developer Handoff — Dhan Historical Pipeline Offline Code Gate (Corrected Snapshot)

**State: RESUBMITTED FOR INDEPENDENT REVIEW. Live acquisition is NOT authorized.**  
**Exact snapshot commit:** 85ebfef015f2188c983d3977ad6fb3b4e11dc29e  
**Hosted offline regression:** [Run 38050016413](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050016413), success; **41 offline/mock tests passed**.  
**Hosted protocol check:** [Run 38050016603](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050016603), success.

## Exact files and Git blob SHA

| File | Git blob SHA |
|---|---|
| `scripts/dhan_history_pipeline.py` | `af560a7e1208d67fc7eb6275639ada701907c752` |
| `scripts/test_dhan_history_pipeline.py` | `cf31bfa5538d449ee57abece6a68e959e22c7892` |
| `.github/workflows/phase-07-dhan-history-pipeline-tests.yml` | `dc0de4688bfac5ee932c32ccd25fdd586effd3c2` |
| `research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md` | `9145f88ec99169a900d9ff2c7b77c0592781f5ae` |
| Prior independent planning gate (tester branch) | `d49298d7070cba557b1ccd31df39cdaad334a571` |
| Independent code REQUEST CHANGES report (tester branch, amended) | `e9c9d3f59f7e267ed317b250df529c03c5f9598d` |

## Fixes made after independent review

1. **Exclusive end dates.** Dhan explicitly documents `toDate` as non-inclusive on the daily-candle and rolling-expired-option endpoints. Their date-only caps now calculate the actual exclusive range duration, and cache validation enforces `fromDate <= returned local date < toDate`. Intraday behavior remains separately validated with local-naive Asia/Kolkata timestamps because its documentation does not explicitly state the end-boundary rule.
2. **Hard request/byte ceiling.** With this snapshot's `MAX_REQUESTS=1` and `MAX_TOTAL_BYTES=8 MiB`, the Budget object and request path reject caller-provided ceilings above those constants and validate budget state before opening a network connection. Future bulk acquisition requires a separately reviewed code/workflow scope.
3. **Optional numeric arrays.** Present known numeric arrays, including daily `open_interest`, are checked for type, finite values and non-negativity, not merely length.
4. **Rolling-option optional arrays.** Empty arrays for unrequested optional fields such as IV/OI/strike/spot are allowed, matching Dhan's published response example; those fields are required to align when explicitly requested, and populated optional arrays must align and pass numeric checks.
5. **Strike scope.** This initial pipeline accepts only `strike="ATM"` for rolling-option acquisition. Offset grids are not enabled until their documented expiry/instrument-specific bounds receive a separate implementation review.

## Test evidence

The 41 offline/mock tests include the prior URL allowlist, literal authorization guard, token validation/redaction, redirect rejection, HTTP/body handling, byte caps, request budgets, JSON checks, OHLC math and array alignment, plus new cases for exact exclusive-end 30-/365-day ranges, rejecting a timestamp on the excluded `toDate`, preventing caller-widened request/byte budgets, malformed/non-finite/negative optional OI, the documented empty optional rolling arrays, required optional-field alignment, and non-ATM strike rejection.

All failing earlier iterations are retained in `research/ERROR_LOG.md`. No earlier failed or passed offline run contacted Dhan, used a Dhan secret, populated a market-data cache, fitted a model, inspected the holdout or changed scientific results.

## Remaining source/documentation limitation

Dhan's expired-options documentation states up to 30 days per request and shows `toDate` non-inclusive, but its request example uses 2021-08-01 to 2021-09-01, a 31-calendar-day difference. The implementation uses the conservative stated 30-day duration. The exact allowed edge will be recorded as unverified until a separately authorized bounded source feasibility test; no wider window is permitted by this code snapshot.

## Explicit non-claims and authorization boundary

- No actual Dhan API request has been made by this pipeline.
- Token entitlement, real response schema, data coverage, historical continuity, quotas and price/option data quality remain unverified.
- No data cache exists from this pipeline, no feature matrix/model rerun occurred, previous prediction results remain unchanged, and the untouched final holdout remains sealed.
- The workflow remains offline-only with contents-read permission, no Dhan secret environment and no live-request step.
- This code gate does **not** authorize data acquisition. After an independent tester PASS, a separate exact-snapshot single-use manifest and guarded manual workflow must be reviewed for one tiny daily NIFTY index-history request only.

**Developer → Tester:** Independently re-review this exact snapshot and latest hosted run. Confirm findings 1–5 are resolved; review date/array boundary arithmetic, request-budget cap bypasses, cache/source-window consistency, tests and workflow permissions. Return PASS or REQUEST CHANGES. Do not authorize a live request within this report.

**Tester → Developer:** If the code passes, authorize only preparation of a fresh one-use manifest. Independently verify its exact commit and protected blobs before any API call; no bulk download, feature fitting or model rerun is authorized.
