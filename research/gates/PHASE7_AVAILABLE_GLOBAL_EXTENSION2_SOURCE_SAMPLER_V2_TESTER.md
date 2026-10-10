# Independent Tester Review — Extension 2 Gate A Sampler v2

**Decision: REQUEST CHANGES — do not add or run the v2 workflow yet.**  
**Reviewed sampler blob:** `2cc90715401e7a99f63bd69bb99774ce53f56113`  
**Reviewed offline test blob:** `baecbf17db9b2b1734c7c0f5321ee6cf986b4cd9`  
**Scope:** static code review only. No live source request was run by this tester.

## What passes

- Scope is bounded to two daily index CSVs, two single-day equity bhavcopy archives, one small rolling FII/DII JSON file, and bounded public-page/API responses.
- The index sampler verifies the expected ten frozen sector names plus NIFTY 50, a date column and close column, and checks all rows match the requested date.
- The equity archive sampler validates all-row trade dates, required legacy/UDiFF columns, and records eligible EQ/INE/positive-close/positive-volume counts.
- Tests cover missing sector identity, legacy/UDiFF schema, and mixed-date rejection.

## Blocking correction — FII/DII history validation is only first-row-deep

In `inspect_fii_history()`, `missing_required_fields` is computed from `rows[0]` only. A later row missing `fii_buy`, `fii_sell`, `dii_buy` or `dii_sell` would pass the schema check. The date list also silently filters rows without dates, so `distinct_date_count == len(rows)` can reject duplicates but does not directly report how many rows had invalid/missing dates. Finally, `zero_flow_rows` casts every field to float without handling malformed text, which could crash the report instead of recording a validation failure.

**Required:**
1. Validate required fields and numeric finite values across every history row.
2. Count and report rows with missing/invalid dates, missing required fields, and nonnumeric/nonfinite flow values.
3. Parse all dates deterministically and report duplicate dates separately.
4. Make malformed values a recorded `schema_status: FAIL`, not an uncaught exception.
5. Add offline fixtures with a valid first row and an invalid later row, plus duplicate-date and nonnumeric-flow fixtures.

## Disposition

**REQUEST CHANGES.** No v2 workflow was added or run, and no new data were downloaded.

**Tester → Developer:** Add full-row FII/DII schema/numeric/date validation and the negative fixtures, then resubmit exact blobs.

**Developer → Tester:** Keep the v2 workflow disabled until the corrected sampler receives a fresh independent code-gate decision.


## Corrected sampler re-review — 2026-10-10

**Current decision: PASS WITH SCOPED RESTRICTIONS — add/run the bounded Gate A workflow only.**  
**Reviewed sampler blob:** `4c69b20e3eb4a6a0f99c6f0137de06806a13ff1f`  
**Reviewed offline tests blob:** `d818613dc2f9188224562a953fd979a6c274d292`

### Checks passed

1. The sampler is bounded to two daily index CSV dates, two single-day equity bhavcopy archives, one rolling 164-record FII/DII JSON source, and small page/API responses. It does not download full history, create feature tables/labels, or fit models.
2. Official sector-index CSV validation checks the requested date across every row, the date/close/index-name columns, all ten frozen sector identities, and NIFTY 50.
3. Equity archive validation checks all rows' requested date, legacy/UDiFF required columns, source schema, and the explicit `SERIES=EQ` / ISIN-prefix / positive-close / positive-volume eligibility counts.
4. FII/DII history checks required fields and finite numeric values on every row, normalizes every date, counts duplicate dates, missing fields, invalid dates and invalid flows, and records malformed values rather than throwing.
5. Tests cover index missing-identity failure, legacy/UDiFF equity schema, mixed-date rejection, FII/DII later-row missing fields, duplicate dates, nonnumeric flows and timestamp-suffix normalization.

### Authorized scope

- Add an automatic/manual GitHub Actions workflow that runs the v2 offline tests and this sampler.
- Run only the exact sample dates and bounded page/API responses encoded in the script.
- Upload the JSON source-feasibility report as an immutable artifact.
- Keep official and third-party sources clearly labelled; do not treat a GitHub mirror as official-source verification.
- No full historical downloads, historical feature table, labels, model fitting, metrics/p-values, or final-holdout access.

### Next gate

Submit the immutable source-feasibility artifact and a summary showing index identity coverage, equity field mapping, flow-source date coverage, duplicate/missing/numeric counts, source hashes and attempted URLs. Tester will then decide whether Gate A is passed. This pass does not authorize full-history acquisition or model fitting.

**Tester → Developer:** Add/run the bounded v2 workflow and submit the artifact; do not exceed the sample scope.

**Developer → Tester:** Independently audit the source feasibility artifact. Keep full-history acquisition and model fitting closed until a separate Gate A artifact decision is recorded.
