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


## Final corrected exact-snapshot code review — 2026-10-10

**Current decision: PASS WITH SCOPED RESTRICTIONS — exact current sampler/workflow snapshot, Gate A only.**  
**Reviewed developer commit:** `6050908b98c53d75c10175140e84e87f48934896`.  
**Full-history acquisition: NOT AUTHORIZED.**  
**Model fitting: NOT AUTHORIZED.**  
**Scope:** one bounded Gate A source-sampling run only, conditional on the exact report/hash manifest validating in the guarded workflow.

### Protected blobs independently re-fetched

| Protected file | Reviewed Git blob |
|---|---|
| `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md` | `a5e65b56f9aa23c8292b718403c3db4448dad2e3` |
| `scripts/phase7_extension2_source_feasibility.py` | `532c1212fad29dbd771d609b1e0ddb85d46d9e50` |
| `scripts/test_phase7_extension2_source_feasibility.py` | `4b470468a4aef23ba59d5efef8755be33ce23fe0` |
| `scripts/phase7_extension2_source_feasibility_v2.py` | `aa714264481034c52b9e2b75d020a270212c8204` |
| `scripts/test_phase7_extension2_source_feasibility_v2.py` | `43bd50df257ecc6d094ca64c6770f26a50340ecf` |
| `.github/workflows/phase-07-extension2-source-feasibility-v2.yml` | `20470b88d29b1d97e8060936e5ed7a40fe28a80d` |

These six protected Git blob IDs match between the reviewed developer commit and current developer branch. The actual workflow blob is kept distinct from the reviewed commit hash.

### Regression evidence

- [Offline v1+v2 suite — Run 38026024826](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026024826) succeeded on commit `b7713ff1ae90ac6ea8d3c477a01683634259dab1`: all **22 distinct offline checks passed** (7 v1 + 15 v2).
- [Legacy-workflow safety correction — Run 38026080844](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026080844) succeeded on commit `6050908b98c53d75c10175140e84e87f48934896`; its v1 offline suite passed.
- The v2 live-source workflow runs the same offline suites first, and the live source job depends on both those tests and the separate authorization job. It checks the exact report digest, fixed current-decision line, explicit scope restrictions, path allowlist, file hashes, Git blob IDs quoted in this report, and reviewed-commit ancestry.
- The NSE FII/DII date endpoint is fixed to a ten-day window. URL validation refuses wider or unregistered requests before fetch; API response bytes are capped at 512,000 and rows at 50. New tests exercise both the pre-fetch rejection and the row/byte/JSON-shape conditions.
- The only remaining live step in this approval scope is the bounded source sampler and report upload. It does not construct features or labels and does not fit models.

### Governance incident and containment

[Run 38025793938](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38025793938) had executed the legacy source sampler before the exact-snapshot approval gate was in place. It fetched only the two single-day F&O archive dates and a small set of public pages/API responses; it did not perform feature/label construction, model fitting or full-history acquisition. Because it ran without tester authorization, its artifact is **NON-ACCEPTED EVIDENCE** and must not be used to pass Gate A. This is recorded in the developer error log.

Containment was verified: the old workflow `.github/workflows/phase-07-extension2-source-feasibility.yml` is now offline tests only at Git blob `f23bb9fe8a5b1343a2a94d308c77b4e26de1d0f3`; its successful Run 38026080844 demonstrates it no longer includes the source-fetch step. The v2 live-source workflow remains the only enabled live sampling path and is fail-closed behind the exact manifest.

### Decision and strict limits

**PASS WITH SCOPED RESTRICTIONS** for one bounded Gate A sample run with the current exact six-file snapshot only. The approval manifest must bind the six Git blobs above and their byte-level SHA-256 hashes, plus this tester report's SHA-256, and the reviewed commit must be an ancestor of the workflow run.

- **Full-history acquisition: NOT AUTHORIZED.**
- **Model fitting: NOT AUTHORIZED.**
- No historical feature table, labels, predictions, metrics or p-values may be produced.
- Do not open the final untouched holdout or proceed to Phase 8.
- After the bounded sample artifact is uploaded, tester must perform a separate source-feasibility artifact audit. Any full-history acquisition or model fitting requires a later, separate approval.

**Tester → Developer:** Mirror this exact report to the developer branch and create only the hash-bound one-run Gate A approval manifest. Confirm the hosted job passes offline tests and the authorization guard before treating any bounded source report as evidence; submit both reports for separate post-run review. Keep full-history acquisition and model fitting closed.

**Developer → Tester:** Independently audit both uploaded Gate A JSON reports, source hashes/URLs, date coverage, all-row schema checks, official-versus-third-party provenance, and the historical F&O transition. If source identity/coverage remains unresolved, return REQUEST CHANGES rather than expanding the request beyond the approved sample.


## Post-run Gate A artifact audit — Run #38026272245

**Artifact decision: REQUEST CHANGES — do not accept this Gate A artifact as a passed source-feasibility gate.** This is a separate artifact decision; the prior code-gate PASS did not validate live source outcomes.  
**Run:** [38026272245](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026272245)  
**Artifact ID:** `11660395594`, name `phase7-extension2-gate-a-source-feasibility-v2`  
**ZIP SHA-256:** `0a854524a857854aae050cdf35cf4b9e88fb90ed19a0fa061f869ed16984667a`  
**F&O/page/API JSON SHA-256:** `64e7a93a14c7a2c9baada1d576651e092b9f6204abec3b2a73ac5223a86c1d81`  
**Index/equity/FII-DII JSON SHA-256:** `131ce0e2905630ca6d83e574e93f83ea914aa8c316ba2278c269f81d761e8263`

### Findings that pass

- Official legacy F&O archive 2024-07-05: 33,930 rows, one trade date, required columns present and 1,634 NIFTY option rows; schema status PASS.
- Official UDiFF F&O archive 2024-07-08: 34,390 rows, one trade date, required columns present and 1,634 NIFTY option rows; schema status PASS.
- Official cash-equity archives 2024-07-05 and 2024-07-08 passed schema/date checks with 1,699 and 1,701 rows meeting the sampler's EQ/INE/positive-close/positive-volume filter.
- FII/DII request sizes were within the declared limits. The official current endpoint returned two current rows. The sampled GitHub mirror had 164 unique dated rows from 2026-01-14 through 2026-09-30.

### Blocking finding 1 — official index CSVs fail date validation

Both official index CSV downloads contain all ten frozen sector-index names plus NIFTY 50, and expose the expected close column. However, both records are marked `schema_status: FAIL` because every `Index Date` is formatted `DD-MM-YYYY` (for example, `05-07-2024`), which the current date normalizer does not recognize. The date samples therefore fail the point-in-time date check despite the correct requested date and all expected index names being present.

**Required:** add deterministic `%d-%m-%Y` parsing, change/add an offline fixture using the exact official `DD-MM-YYYY` format, rerun both offline test suites, and submit a fresh exact-snapshot code review before another source fetch.

### Blocking finding 2 — NSE date-filtered FII/DII API ignored the requested window

The request for `fromDate=01-07-2024&toDate=10-07-2024` returned the same 217-byte payload/hash as the unfiltered current endpoint: two records dated `09-Oct-2026`. Both rows are outside the requested window. The current implementation reports `JSON_PARSED` rather than identifying that the response is not a valid sample for the requested historical range.

**Required:** validate every returned row's date against the requested window. If any response row is outside the requested window or has no parseable date, mark the sample as rejected/unverified and do not treat the endpoint as a historical source. Add regression fixtures for out-of-window dates and in-window dates, then re-run the bounded sample only after renewed exact-snapshot approval.

### Historical FII/DII coverage still unestablished

The sampled ChartDrift page exposes only 16 recent rows around late September 2026; the sampled Fundata page does not expose a populated dated history table; the official page renders only general/current content in this sample; and the public GitHub mirror contains only 164 unique records (January–September 2026). This does not establish the 500+ aligned historical sessions required for the registered confirmatory family test. Do not declare the history unavailable yet: the free-source search must continue in a later approved source-discovery step before any paid source is considered.

### Disposition

This sample run stays **NON-ACCEPTED for Gate A completion** because the index date validator failed and the official historical FII/DII API request returned out-of-window rows. The F&O format/schema probe and cash-equity archive probe did succeed; retain their hashes as bounded evidence but do not treat the combined artifact as passing. No features, labels, predictions, metrics, p-values, full-history datasets or model fits were produced.

**Tester → Developer:** Correct both issues, add exact regression fixtures, update the error log/status and submit the new source/code snapshot for a separate tester gate. Expand the free FII/DII source discovery plan; do not download full history or fit models.

**Developer → Tester:** Re-review the date normalization and out-of-window response tests. After code approval, authorize only one corrected bounded sample run; the resulting artifact requires a separate post-run audit.


## Corrected source-validation code gate — 2026-10-10

**Current decision: PASS WITH SCOPED RESTRICTIONS — exact current sampler/workflow snapshot, Gate A only.**  
**Reviewed developer commit:** 784474de59a050ba6229ee5cb9a708c0f74ca2dc.  
**Full-history acquisition: NOT AUTHORIZED.**  
**Model fitting: NOT AUTHORIZED.**  
**Important separation:** this is a fresh code-gate PASS for a corrected, bounded retry; it does **not** change the prior post-run artifact decision on Run #38026272245, which remains REQUEST CHANGES/non-accepted. Only one new bounded source-feasibility batch may run; its artifact requires another independent review.

### Exact protected snapshot

| Protected file | Reviewed Git blob ID |
|---|---|
| research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md | a5e65b56f9aa23c8292b718403c3db4448dad2e3 |
| scripts/phase7_extension2_source_feasibility.py | 532c1212fad29dbd771d609b1e0ddb85d46d9e50 |
| scripts/test_phase7_extension2_source_feasibility.py | 4b470468a4aef23ba59d5efef8755be33ce23fe0 |
| scripts/phase7_extension2_source_feasibility_v2.py | 1f5013a43c5394ea92bdd300a67e299c1bdb079f |
| scripts/test_phase7_extension2_source_feasibility_v2.py | 9b90eb50eae7974ce583fc5201fedcd53b35ae19 |
| .github/workflows/phase-07-extension2-source-feasibility-v2.yml | a699eaf8af92978da2ae6961cb3c5dabb44a47a4 |
| .github/workflows/phase-07-extension2-source-feasibility.yml (offline-only legacy workflow) | f23bb9fe8a5b1343a2a94d308c77b4e26de1d0f3 |
| .github/workflows/phase-07-extension2-source-feasibility-tests.yml (offline-only test workflow) | 593da783fa81788a1041d17d82945e24d76caf4d |

All eight protected blobs were re-fetched from the developer branch. The v2 authorization allowlist now contains all eight paths, including both workflows documented as offline-only, and verifies their byte hashes and Git blob IDs against this report. The reviewed commit is an ancestor of current developer HEAD.

### Source-validation corrections verified

1. The date normalizer now handles the official index CSV's numeric DD-MM-YYYY format.
2. The date-parameter FII/DII response validator checks every returned row against the exact requested interval. Any row outside the interval is rejected as REJECTED_ROWS_OUTSIDE_REQUESTED_WINDOW; rows without a parseable date are UNVERIFIED_RESPONSE_DATE.
3. The source-level function passes the parsed requested window to the payload validator. A new integration regression simulates the actual NSE API request path returning 2026-10-09 rows for the July 2024 request and verifies that the response is rejected.
4. Request restrictions remain in place: ten-day query window, 512 KB response cap, maximum 50 rows, and no fetch for unregistered/wide date ranges.
5. Both prior data-validation defects have direct regression coverage; the rejected payload is not included as an accepted sample in the report.

### Hosted tests and guarded-flow checks

- Offline source tests Run 38026629021 succeeded with **25 checks** (7 v1 + 18 v2), including the new end-to-end out-of-window response test.
- Fail-closed check Run 38026802711 passed offline tests, rejected the explicitly revoked manifest, and skipped the live source job. This intentionally failed workflow run demonstrates the current gate does not acquire sources while approval is revoked.
- The prior unapproved legacy workflow incident remains logged. Its workflow is offline-only and protected by this same snapshot; no new data were fetched by this code-review step.

### Decision and limit

Code gate is **PASS WITH SCOPED RESTRICTIONS** for **one bounded Gate A re-sample only**, conditional on the current approval manifest being replaced by a fresh exact-snapshot manifest. The corrected sample may only upload the two source-feasibility JSON reports. It must not create full historical datasets, features/labels, predictions, metrics or p-values, and must not open the final holdout. No model fitting is authorized.

Free-source FII/DII history is still unresolved. The next artifact audit must check the corrected NSE index samples and reject the NSE date-parameter response if it continues to ignore the requested window. Additional public source leads have been discovered but are not yet accepted; they must be tested under a separately reviewed bounded source-discovery scope if the corrected artifact does not establish 500+ usable sessions.

**Tester → Developer:** Mirror this report exactly; create a new manifest binding this exact commit, the eight blob IDs and file hashes, and the report hash. The guarded workflow must re-run offline tests and the exact authorization check before sampling. After the artifact uploads, independently audit it again. Keep full history and model fitting unauthorized.

**Developer → Tester:** Do not infer that code PASS equals source-coverage PASS. Recheck URLs, dates, hashes, official/source-vintage provenance, sector identities, and response-window behavior on the new immutable artifact. If historical FII/DII coverage remains insufficient, continue researching free sources under a new gate rather than using a paid source or fitting the model.
