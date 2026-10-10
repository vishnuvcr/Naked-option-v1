# Independent Tester Report — Dhan Historical Pipeline Code Gate

**Decision: REQUEST CHANGES — no live request authorized.**

**Reviewed branch/head:** phase-07-developer / c6ca5ae84c050d0c72d9ba72b63c3803305160c2  
**Latest hosted offline run:** [38049711849](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38049711849), success, 36 offline/mock tests passed; CLI reports network_enabled=false.  
**Exact reviewed blobs:**
- scripts/dhan_history_pipeline.py: f0260544157a099dbecef8bfa47105fc152f0344
- scripts/test_dhan_history_pipeline.py: e156c0915320a9ed075e8ba6d55857a56bca9f61
- .github/workflows/phase-07-dhan-history-pipeline-tests.yml: dc0de4688bfac5ee932c32ccd25fdd586effd3c2

The developer code-submission document in this snapshot still pins an earlier code/test commit and blobs, so it must be refreshed before final approval.

## Findings requiring changes

### 1. Daily and rolling-option date windows incorrectly treat toDate as inclusive

Dhan's official historical-data documentation explicitly says the daily candle endpoint's toDate is non-inclusive: https://dhanhq.co/docs/v2/historical-data/ (Daily Historical Data, Request Structure). Dhan's official expired-options documentation also says the rolling-option endpoint's toDate is non-inclusive: https://dhanhq.co/docs/v2/expired-options-data/ (Historical Rolling Data, Request Structure).

Current code:
- _validate_date_range uses (to_date - from_date).days + 1 for all three endpoint types.
- The daily and rolling-option timestamp checker accepts any row whose date is <= toDate.

Consequences:
- A 30-day exclusive range such as 2024-01-01 through 2024-01-31 is rejected as 31 days, even though the end date is excluded and the period is 30 calendar days.
- A 365-day daily chunk has the same off-by-one restriction.
- A response with a timestamp on the excluded toDate could pass cache timestamp validation.

**Required correction:** separate endpoint-specific date semantics. For daily and rolling options, cap the exclusive range using (to - from).days and verify every returned local date satisfies fromDate <= date < toDate. Preserve intraday semantics only as supported by its documentation or explicitly mark/test that endpoint's inclusive boundary as unresolved until observed. Add boundary regressions for one-day, exact 30-/365-day, end-date exclusion and an out-of-window row exactly on toDate.

### 2. The sample request budget can be raised above its approved ceiling

MAX_REQUESTS = 1 is described as the sample-gate budget, but RequestBudget(request_limit=3) and larger values are accepted. request_json trusts the caller-provided budget; with live_authorized=True, the same code can therefore make multiple source requests without changing the code snapshot. The 8 MiB total-byte budget can likewise be increased by passing a custom byte_limit.

This conflicts with the plan's first live sample being a one-request/strict-byte-budget gate. A later bulk workflow can use a distinct reviewed adapter or scope; it should not be possible to widen the sample helper's limits by caller arguments alone.

**Required correction:** enforce the hard maximum in the request path (at least request_limit <= MAX_REQUESTS and byte_limit <= MAX_TOTAL_BYTES; also validate existing counts before reservation). Add tests that custom budgets over either bound fail before opener creation or any request.

### 3. Optional known numeric arrays are not fully value-validated

validate_candle_payload validates every list's length, but finite-number and non-negative checks apply only to required_fields. For example, the documented daily response may include open_interest when OI is requested, yet NaN, non-numeric or negative open_interest values can pass the validator if the array length matches. Such fields may later become model features.

**Required correction:** validate all recognized numeric arrays when present (including open_interest and the Dhan OI field), or reject/explicitly mark unvalidated optional numeric fields so they cannot enter feature engineering. Include malformed, non-finite and negative optional-OI regression cases.

### 4. Rolling-option validator rejects a documented response shape when optional fields were not requested

Dhan's official rolling-option example requests open/high/low/close/volume only, while its response example shows iv, oi, strike and spot as empty arrays and timestamp/OHLCV arrays populated: https://dhanhq.co/docs/v2/expired-options-data/ (Request Structure and Response Structure). Current validate_rolling_option_payload rejects any list-valued field whose length differs from timestamp count, including those empty unrequested optional arrays.

**Required correction:** require exact alignment for timestamp and requestedData fields, validate unrequested optional arrays only if they are populated, and accept an empty optional array only when that field was not requested. Add a mock matching the published response structure and a rejection case where a requested optional array is empty/misaligned.

### 5. Rolling-option strike input accepts arbitrary strings outside the documented enum

The official API documents the strike field as an enum string: ATM, ATM-relative offsets up to +/-10 for index options near expiry and up to +/-3 for other contracts. Current validation accepts any nonempty string, including unsupported values such as ATM+999, and also accepts positive integers even though the field is documented as a string enum.

**Required correction:** validate the literal ATM-relative grammar and applicable offset bound for the intended instrument/scope, or restrict the initial sample-gate implementation to the exact supported value ATM. Add tests for valid ATM offsets and arbitrary/oversized offset rejection. Do not silently pass unrecognized strike values to Dhan.

## Checks that passed in the reviewed scope

- Latest hosted run passed 36 tests and the module CLI remains offline-only.
- URL allowlist is exact to the three documented https://api.dhan.co/v2/charts/* endpoints; unsafe host/path/query/profile endpoint are rejected.
- Live helper requires literal boolean True; error messages do not echo credentials/provider body; HTTP redirects are rejected without following.
- Content type, body size, response hashing, timestamp ordering, parallel-array lengths, OHLC consistency, rolling-option alignment and atomic cache checks are present.
- The current workflow is contents-read-only, contains no Dhan secret environment, and runs only offline/mock tests. No actual data request has been made.

## Decision and next gate

The code is not approved for live acquisition. The corrections above must be implemented on phase-07-developer, regression-tested in GitHub Actions, and submitted as a new exact snapshot. The independent review must be repeated against the new blobs, including the date-boundary arithmetic.

**Tester → Developer:** Correct findings 1–5 on the developer branch, add the requested regression cases, refresh the exact-snapshot submission and research logs, then request a fresh tester review. Do not create a live workflow, spend a manifest or call Dhan before a new PASS.

**Developer → Tester:** Re-review the corrected code and new hosted run independently. Do not authorize beyond code review; after a PASS, only a fresh manifest for one tiny daily NIFTY history request may be considered.
