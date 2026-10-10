# Independent Tester Report — DhanHQ Adapter / Offline Gate

**Current decision: PASS WITH SCOPED RESTRICTIONS — adapter/offline tests only.**  
**Reviewed developer commit:** `46305d374a60babd6ac813715aad516717a94d1b`.  
**Live Dhan requests: NOT AUTHORIZED.**  
**Full-history acquisition: NOT AUTHORIZED.**  
**Model fitting: NOT AUTHORIZED.**

## 1. Exact protected files independently reviewed

| File | Git blob ID |
|---|---|
| `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` | `f87e8ecaec0a26947438131fef466aae3e57d824` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md` | `9db93dfb56e309dcccf549e51da09004e5f4b276` |
| `scripts/dhan_market_data_recovery.py` | `3ee3d4db194fd5b9f05816454de2e756f9a8cb46` |
| `scripts/test_dhan_market_data_recovery.py` | `d45478853661a29d1160fc371def865e2bf1c510` |
| `.github/workflows/phase-07-dhan-market-data-tests.yml` | `b43ce4dadca4e5867173136531e71c63bb74e9a3` |

## 2. Hosted evidence

[Offline regression Run 38042858506](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042858506) succeeded on the reviewed commit and logged **25/25 checks passed**. It runs only the fixture test script and does not bind the Dhan secret or execute a live entrypoint.

An earlier run, [38042825681](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042825681), failed because the CSV fixture encoded literal backslash-n sequences rather than newlines. The fixture was corrected and the later hosted run passed. The earlier failure must remain in the developer error log.

## 3. Independent findings

- **Secret safety:** token is not accessed by the offline workflow; the profile parser emits only status/boolean fields. HTTP error bodies are discarded and error messages are reduced to a status or exception type.
- **Fail-closed transport:** registered HTTPS endpoints only; no redirects/retries; fixed timeout; request and aggregate byte budgets; profile, metadata and candle body caps.
- **Instrument identity:** JSON/CSV metadata parsing is supported; the parser refuses missing or ambiguous NIFTY 50 / India VIX mappings rather than guessing an ID.
- **Candle schema:** required arrays must align and be non-empty; values must be finite; OHLC inequalities, timestamp order/uniqueness, IST session date and requested window are checked.
- **Scope:** no live workflow exists in this reviewed snapshot. The adapter's live function is guarded by an explicit workflow authorization environment flag. This PASS cannot authorize setting that flag or making any request.
- **Data semantics:** Dhan daily candle APIs are a potential source for instrument OHLCV/OI; they do not document the aggregate daily FII/FPI/DII flow series. That gap remains open.
- **Source-shape caveat:** actual `IDX_I` response shape and actual data-plan entitlement remain unverified because no authenticated request has been made. If the approved sample disagrees with parser assumptions, stop and return REQUEST CHANGES; do not widen scope.

## 4. Decision

**PASS WITH SCOPED RESTRICTIONS** for adapter and offline-test code only. The next allowed task is to implement and submit a separate live workflow with a hash-bound one-run manifest validator/spend guard for independent review. That workflow must have automatic and manual entry points, but neither can bypass the manifest. The Dhan token must be injected only as `DHAN_ACCESS_TOKEN: ${{ secrets.DHAN_ACCESS_TOKEN }}` inside the guarded job, never printed, and never made available to offline test jobs.

This decision does **not** authorize:
- live authenticated requests;
- full-history acquisition or cache population;
- features/labels, predictions, model fitting, metrics or p-values;
- options strategy testing or final-holdout access.

**Tester → Developer:** Mirror this report exactly to the developer branch. Submit a separate guarded live workflow and manifest validator for independent review. Keep all network requests disabled until that workflow passes and a new single-use manifest is created.

**Developer → Tester:** Review the exact workflow snapshot independently, especially manifest digest/hash/blob/ancestry checks and manifest consumption before the first HTTP request. After the one approved sample, audit the artifact separately.


## Final workflow/manifest review — 2026-10-10

**Current decision: PASS WITH SCOPED RESTRICTIONS — guarded workflow code only.**  
**Reviewed developer commit:** `2df2d2874074dbeb65b8687ab5fcaa005bb0714a`.  
**Live requests: NOT AUTHORIZED until a fresh single-use manifest is created and validated.**

Exact reviewed workflow and validator Git blobs:
- `.github/workflows/phase-07-dhan-market-data-live.yml`: `aa37cec66d46f3c181a7bda213226991c045b189`
- `.github/workflows/phase-07-dhan-market-data-tests.yml`: `b43ce4dadca4e5867173136531e71c63bb74e9a3`
- `scripts/validate_dhan_sample_approval.py`: `3c99140a5488cd58ee3bed9c21cd659183adbdf2`
- `scripts/dhan_market_data_recovery.py`: `2398cc3a3b050e15107ef7fa88c5415f93845fe9`
- `scripts/test_dhan_market_data_recovery.py`: `acf5140f34da4cd406d95a1c9b567ec29cd83609`

### Checks passed

1. The manifest validator requires `APPROVED_ONE_RUN` + `READY`, exact scope, exact protected path set, tester-report SHA-256, file byte SHA-256, Git blob IDs, reviewed-commit ancestry, explicit no-full-history/no-model flags and the request/body budgets.
2. The live workflow runs offline regressions before manifest validation. It calls `spend` and commits/pushes the spent manifest before the first source script call.
3. A subsequent workflow run triggered by the spent-manifest push will fail the `READY`/decision check and cannot make a second sample request.
4. The secret is injected only into the final source step; offline tests and manifest-validation steps do not receive it.
5. Manual dispatch defaults to false and requires explicit confirmation; it cannot bypass the manifest check.
6. The offline workflow has no live source step and does not bind the secret.
7. The adapter does not call order/trading endpoints; no request was made during this review.
8. The 4 MiB global budget is consistent with 64 KiB profile + 1 MiB index metadata + four 752 KiB candle caps.
9. The Dhan candle source is not presented as FII/FPI/DII aggregate flow data.

### Hosted evidence

- [Run 38043020539](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043020539) passed all 27 offline regressions on the code snapshot before the review-request-only commit.
- Previous failing fixture/assertion runs were corrected and are retained in the logs; current run is green.

### Decision and exact limit

This PASS authorizes **only the creation of a new exact-hash, one-run sample manifest** for the reviewed snapshot. It does not itself authorize a source request; the manifest must be independently bound to the exact current report digest, protected file hashes/blob IDs, and reviewed commit before the guarded workflow can call Dhan.

**Not authorized:** full-history download, feature/label construction, model fitting, prediction metrics/p-values, option strategy evaluation or final-holdout access.

**Tester → Developer:** Create a new one-run manifest only for this exact snapshot. Include all eight protected files listed in the developer handoff, exact byte hashes and Git blobs, exact mirrored tester-report SHA-256, reviewed commit ancestry, fixed scope, six-request/4 MiB budgets and explicit false flags for full-history/model fitting. Do not trigger the workflow until validation is expected to pass.

**Developer → Tester:** Independently verify the manifest values and current branch hashes before allowing the one bounded run. After upload, audit the artifact's source statuses, date windows, row schemas, coverage and absence of secrets. Do not progress directly to bulk acquisition or modeling.


## Post-run artifact audit — Run 38043148580

**Artifact decision: REQUEST CHANGES — no usable Dhan candle sample was obtained.**  
Run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043148580  
Artifact ID: `11666064550` (`dhan-market-data-bounded-sample`)  
Artifact ZIP SHA-256: `45f2b23a0835cb6b1af52ac12913bf86062f9c82a0d3edcef4c810a3f30f38d9`  
Artifact JSON content:
```json
{
  "request_count": 2,
  "status": "BLOCKED_INSTRUMENT_METADATA"
}
```

### Findings

- Offline regression suite and exact manifest/hash/ancestry/scope validation passed.
- The one-run manifest was marked SPENT before the first source request, as required.
- The script completed two requests: the profile probe passed far enough to proceed beyond token/entitlement checks; the index metadata request then returned a non-200 status and stopped before any historical candle requests.
- No candle rows, price history, option history or FII/FPI/DII flow records were obtained. No model or analysis was rerun.
- **Reporting defect:** the artifact omitted the HTTP status for the failed instrument metadata request. This prevents a conclusive distinction between authentication/entitlement, endpoint, rate-limit and provider errors. The adapter must include the numeric HTTP status and safe content-type only; it must not include provider error body, account data, token or raw headers.
- The manifest is SPENT and must not be reused. No additional Dhan requests are authorized by this artifact decision.

### Required correction

1. Include the numeric metadata HTTP status in the bounded report on non-200 responses. Keep provider error bodies discarded and do not echo exception text.
2. Add offline tests for the blocked metadata result retaining only status and not raw body/secret.
3. Re-run offline tests and request a fresh exact-snapshot tester review.
4. Only after code review may a new one-run manifest be created. The next sample must still stop at the metadata endpoint if its status is non-200; do not broaden the URL, add retries, or skip identity resolution.

**Tester → Developer:** Return REQUEST CHANGES for this artifact and update status/error logs. Add safe HTTP-status reporting and fixtures; do not reuse the spent manifest.

**Developer → Tester:** Re-review the exact corrected blobs. If approved, a fresh manifest may authorize one diagnostic retry within the same request budget only. No candle history/full history or model fitting until the metadata source passes and the new sample artifact is independently audited.
