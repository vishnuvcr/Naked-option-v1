# Independent Tester Review — Extension 2 Gate A Source Sampler

**Decision: REQUEST CHANGES — do not enable or run the Gate A workflow yet.**  
**Reviewed sampler blob:** `a35178de4c32a9f86ae1b710a14fd2a8eb7ec072`  
**Reviewed offline test blob:** `eac0e4289ebb6321c08677cc2301c8fc60aa0e13`  
**Review scope:** static source/code review only. No live source request was run by this tester.

## What passes

- Scope is bounded to two single-day F&O archives plus small official page/API responses.
- Requests are size-capped at 12 MB, the report records source attempts and hashes, and no credentials or model fitting are involved.
- Legacy and UDiFF required-column lists are grounded in the public NSE F&O archive mirror's validator. The source script records whether the bytes came from an official archive or a third-party mirror.
- Offline fixtures cover legacy and UDiFF happy paths, missing required columns, and a wrong legacy trade date.

## Blocking correction

### Trade-date validation checks only the first row

In `archive_schema()`, the legacy path checks `TIMESTAMP` only on `rows[0]`, and the UDiFF path checks `TradDt` only on `rows[0]`. This can accept an archive where the first record has the expected date but later records contain a different date. The source feasibility gate is specifically meant to verify date integrity at the format transition, so all records must be checked.

**Required:**
1. Verify every non-empty legacy row has `TIMESTAMP == 05-JUL-2024`.
2. Verify every non-empty UDiFF row has `TradDt` equal to the requested 2024-07-08 date (normalize date-only/timestamp forms deterministically).
3. Add one regression fixture for each format with a valid first row and an invalid second row; both must fail.
4. Record the count of distinct trade dates observed in the archive summary.

### Small provenance note

If an official NSE archive URL fails and the GitHub mirror supplies the sample, retain that as `third_party_github_mirror` and do not describe the sample as official-source-verified. The current code does this correctly; keep the distinction in the final feasibility report.

## Disposition

**REQUEST CHANGES.** No workflow was run, no source data were downloaded, and no full-history acquisition or model fitting is authorized by this report.

**Tester → Developer:** Correct full-file date validation and add the two mixed-date negative fixtures. Resubmit the exact sampler/test blobs.

**Developer → Tester:** Do not add or run the source-feasibility workflow until the corrected sampler receives a fresh independent code-gate decision.
