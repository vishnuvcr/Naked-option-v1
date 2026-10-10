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


## Current exact-snapshot re-review — 2026-10-10

**Current decision: REQUEST CHANGES — do not create the approval manifest or run the source sampler.**  
**Reviewed developer snapshot commit:** `1d8991255ff284c6b9cb20c4071ab56555d18dc6`  
**Scope:** static code/workflow review only. No live source call was made by this tester review.

### Current protected Git blobs reviewed

| Protected file | Reviewed Git blob |
|---|---|
| `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md` | `a5e65b56f9aa23c8292b718403c3db4448dad2e3` |
| `scripts/phase7_extension2_source_feasibility.py` | `f39f2a213b760c608e0deca2f1eaacc2225aca53` |
| `scripts/test_phase7_extension2_source_feasibility.py` | `2d8833719701c87e43f310396b29380220d58578` |
| `scripts/phase7_extension2_source_feasibility_v2.py` | `fb83fe5e880a26134a765a0426f7aa85380272fb` |
| `scripts/test_phase7_extension2_source_feasibility_v2.py` | `d818613dc2f9188224562a953fd979a6c274d292` |
| `.github/workflows/phase-07-extension2-source-feasibility-v2.yml` | `20470b88d29b1d97e8060936e5ed7a40fe28a80d` |

The source-spec, sampler and test blobs at the reviewed commit match the current developer branch. The workflow at that commit includes both bounded sampler scripts and both artifact report paths.

### Blocking finding 1 — one FII/DII URL requests a multi-year historical range

In `scripts/phase7_extension2_source_feasibility_v2.py`, `NSE_FII_URLS` includes:

`https://www.nseindia.com/api/fiidiiTradeReact?fromDate=01-01-2020&toDate=31-12-2025`

This is not a small deterministic sample. It requests a multi-year range and violates the tester-approved Gate A scope, which expressly excludes full-history acquisition. The workflow executes the sampler with no additional row/date cap, so the offline fixture gate does not contain this request.

**Required correction:** replace this URL with a fixed, small date window (for example, 2024-07-01 through 2024-07-10), add a regression that asserts every remote request stays within the approved date bound, and include a maximum expected row count / rejection rule for this endpoint. Then rerun the offline tests and request a new exact-snapshot review. The bounded window is for schema/source feasibility only; it cannot establish the 500-session historical coverage requirement.

### Blocking finding 2 — review-request workflow “Git blob” is actually a commit ID

The developer handoff table labels `1d8991255ff284c6b9cb20c4071ab56555d18dc6` as the workflow's Git blob. That value is the reviewed commit ID. The actual workflow Git blob is `20470b88d29b1d97e8060936e5ed7a40fe28a80d`. The handoff correctly names the reviewed commit separately near the end, but the protected-file table and a later “workflow blob” line repeat the incorrect ID.

**Required correction:** in the review request, use `20470b88d29b1d97e8060936e5ed7a40fe28a80d` wherever a workflow Git blob is requested, and reserve `1d8991255ff284c6b9cb20c4071ab56555d18dc6` for the reviewed commit only. Refresh the review request so its six protected Git-blob IDs exactly match the current tree.

### Findings that pass on static inspection

- The workflow runs the legacy/UDiFF F&O bounded sampler and the index/equity/FII-DII v2 sampler, and uploads both JSON reports.
- Manual source sampling defaults to false. Both push and opted-in manual sampling pass through the offline tests and the guarded exact-snapshot authorization job before the source job.
- The guard checks a fixed protected path set, SHA-256 content hashes, Git blob IDs quoted in the report, a report digest and reviewed-commit ancestry.
- The corrected FII/DII row validator checks each row's required fields, dates and numeric finite values; the current offline tests include invalid later-row, duplicate-date and nonnumeric-flow cases.
- No model/feature/label construction occurs in the sampler scripts.

### Disposition and next gate

**REQUEST CHANGES.** The primary blocker is the multi-year API request, which must be bounded before any live source call. No data were fetched, no artifact exists for this snapshot, and no empirical metric was produced.

**Tester → Developer:** Bound the NSE FII/DII date endpoint to a small sample window, add request-bound regression coverage, correct the review request's Git-blob/commit distinction, run the current offline suites, and resubmit. Do not create the approval manifest.

**Developer → Tester:** Re-review the exact corrected sampler/test/workflow snapshot. A pass may authorize one bounded Gate A source-sampling run only; full-history acquisition and model fitting remain prohibited.
