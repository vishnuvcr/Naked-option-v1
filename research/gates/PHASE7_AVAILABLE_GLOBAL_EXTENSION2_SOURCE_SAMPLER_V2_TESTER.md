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
