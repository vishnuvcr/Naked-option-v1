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


## Corrected sampler re-review — 2026-10-10

**Decision: PASS WITH SCOPED RESTRICTIONS — Gate A sample workflow may be added/run.**  
**Full-history acquisition/model fitting remain NOT AUTHORIZED.**

Exact reviewed blobs:
- Sampler: `f39f2a213b760c608e0deca2f1eaacc2225aca53`
- Offline tests: `2d8833719701c87e43f310396b29380220d58578`

The corrected sampler validates the requested trade date across every non-empty row in both archive formats and records the distinct observed date count. The two new negative fixtures put a wrong date in the second row after a valid first row; both must fail. The previous four happy-path/schema/date tests remain. The workflow has not yet been run, so no claim is made about live source availability.

### Authorized Gate A action

- Add a bounded automatic/manual workflow that runs only the sampler and offline regression tests.
- Fetch only the two pre-transition/post-transition single-day F&O archive samples plus the already listed small page/API requests. Retain per-source status, attempted URL, retrieval time, content hashes, schema/coverage and minimal sample rows.
- Do not download full historical series, create normalized historical feature tables, create labels, fit models, calculate prediction metrics or p-values, or open the final holdout.
- If a third-party mirror supplies a sample, keep it explicitly labelled as a mirror and do not claim official-source verification.
- If NSE blocks a source, record the failed attempt and explore other free source routes; do not declare the data unavailable solely from one failed URL.

After the run, submit the immutable Gate A artifact and its source report to the tester. Full-history acquisition remains gated on a separate tester decision after that artifact is reviewed.

**Tester → Developer:** Add/run the bounded Gate A workflow and submit the source-feasibility artifact for review; no model fitting.

**Developer → Tester:** Independently inspect the live sample results, archive hashes and source labels. Approve or reject Gate A output before full-history acquisition is attempted.
