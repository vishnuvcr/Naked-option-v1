# Developer → Tester Review Request — DhanHQ Guarded Sample Workflow

**Requested decision: PASS / REQUEST CHANGES for exact adapter + workflow snapshot.**  
**Reviewed developer commit:** `d8a8f347b38b362fd4105933a5d8d84e28fb383b`.  
**Live Dhan requests authorized by this submission: NONE.** No manifest exists.

## Exact files and Git blob IDs

| File | Git blob ID |
|---|---|
| `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` | `f87e8ecaec0a26947438131fef466aae3e57d824` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md` | `9db93dfb56e309dcccf549e51da09004e5f4b276` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md` | `b2b7d5434eb85ddb9592312cfe587434c4f7e0b7` |
| `scripts/dhan_market_data_recovery.py` | `2398cc3a3b050e15107ef7fa88c5415f93845fe9` |
| `scripts/test_dhan_market_data_recovery.py` | `acf5140f34da4cd406d95a1c9b567ec29cd83609` |
| `scripts/validate_dhan_sample_approval.py` | `3c99140a5488cd58ee3bed9c21cd659183adbdf2` |
| `.github/workflows/phase-07-dhan-market-data-tests.yml` | `b43ce4dadca4e5867173136531e71c63bb74e9a3` |
| `.github/workflows/phase-07-dhan-market-data-live.yml` | `aa37cec66d46f3c181a7bda213226991c045b189` |

## Hosted offline evidence

- [Run 38042858506](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042858506): 25 offline regressions passed before the guarded live workflow was added.
- [Run 38043020539](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043020539): **27/27 offline regressions passed** on the current adapter/test/workflow snapshot.
- Failed fixture/guard runs were corrected and remain visible in Actions history: [38042825681](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042825681) (CSV fixture literal newline issue), [38042956380](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042956380) (malformed assertion string), and [38042983388](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042983388) (escaped workflow secret expression assertion). The current run is green.

## Workflow design for independent scrutiny

- Offline workflow runs fixture tests only, does not bind `DHAN_ACCESS_TOKEN`, and has no source calls.
- Live workflow only runs on `phase-07-developer`; manual dispatch defaults to false and requires explicit confirmation.
- It runs offline tests, validates the exact report digest, reviewed-commit ancestry, exact protected path set, each file's byte SHA-256 and Git blob ID, scope flags and request budgets, then marks the manifest SPENT and pushes that change **before** the source script runs.
- The secret is injected only into the final authenticated sample step. No other step receives it.
- The one-run manifest does not exist yet. Therefore this workflow cannot run live data requests until a fresh independent workflow/code gate passes and a separate exact manifest is created.
- The source adapter never calls order/trading endpoints and has no default network behavior on import.

## Tester must verify

1. Check all exact Git blob IDs and reviewed-commit ancestry.
2. Inspect the manifest validator: exact report SHA-256, exact path set, file byte hashes, Git blob hashes, scope booleans, budget, and spent-state enforcement.
3. Confirm that the manifest is committed as SPENT before the source script executes, including on manual dispatch.
4. Verify that push-triggered follow-up caused by spending the manifest cannot execute a second sample (the spent state must fail validation).
5. Confirm secret scope and logs/artifacts cannot expose token/profile identifiers.
6. Independently review instrument CSV/JSON mapping, India Standard Time date checks, fixed ten-day windows, non-inclusive end date, array validation and OHLC constraints.
7. Confirm Dhan candles remain distinct from aggregate FII/FPI/DII flows.
8. Return PASS or REQUEST CHANGES. If passing, authorize only a new single-use bounded sample manifest; no full-history acquisition or model fitting.

**Tester → Developer:** Independently review the current live workflow and validator. Do not authorize requests until every guard is verified.

**Developer → Tester:** After the workflow decision, compute exact file byte hashes and create a single-use manifest only if approved. The sample artifact requires a separate independent audit.
