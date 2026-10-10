# Developer Submission — Extension 2 Free Daily Flow Source Discovery 3

**Status: SPECIFICATION REVIEW REQUESTED. No code is implemented for this scope and no new source requests have been issued.**  
**Prior Gate A manifest:** SPENT; not reusable.  
**Current allowed scope:** proposal review only.

## Files under review
- Frozen proposal: [EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md)
- Previous bounded source report: [Run 2 artifact audit](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/PHASE7_EXTENSION2_GATE_A_RUN2_ARTIFACT_TESTER.md)
- Prior source inventory: [EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/sources/EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md)
- Current recorded Gate A disposition: schema samples pass, but G14/G15 source-coverage gate remains open. No feature/label table, model fitting or metrics have been produced.

## Exact frozen spec snapshot
- Spec Git blob: `4e30415632545c04a2875d627afa0191afe3f383`
- The spec defines a maximum of 15 initial probes plus no more than three one-hop HF redirects (18 exchanges total), 2 MiB total data, two 8-KiB HF byte ranges (requires status 206 + exact Content-Range), no full-file fallback, two fixed single-day CDSL XLS reports, one pinned chirag date JSON, and metadata-only probes for SEBI/NSE/CalcSetu/other mirrors.
- It explicitly rejects generated/seeded daily values. The MrChartist `seed_history.js` source code describes generating “realistic per-day” values from monthly/yearly aggregate totals, so its `historical-seed` rows are not treated as raw daily ground truth.

## Current source leads and why this phase is needed
1. The HF commit view for [johnwick3690/stocks](https://huggingface.co/datasets/johnwick3690/stocks) lists `fii_dii_2024_to_today.csv` with a 503-line added diff. This might hold daily FII/DII rows but is not yet independently verified for 500 unique dates or provenance.
2. CDSL's [dated FPI archive](https://www.cdslindia.com/Publications/ForeignPortInvestor.html) links to daily Excel reports. It is FPI-only, so cannot supply G15, but may provide an independent source for G14.
3. SEBI’s [trade-wise FPI equity archive](https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html) lists monthly files to 2003; these are transaction-level FPI data and cannot silently replace the frozen combined-flow series.
4. NSE’s [FII/FPI & DII reports](https://www.nseindia.com/reports/fii-dii/) still provides official field/CSV metadata, but the previously sampled date-parameter API ignored historical range parameters. The proposal prohibits widening/retrying it.
5. Public JSON mirrors and dashboards may be rolling, synthetic, placeholder-based or FPI-only. The spec demands clear provenance and labels source rows accordingly.

## Explicit governance incident
During metadata/code review, the full public MrChartist `data/history.json` (143,498 bytes) was inadvertently returned by a repository file-fetch call. It was not imported to this repo’s dataset or used for modelling; it is now recorded as non-accepted evidence in the developer error log. The spec prohibits further full-history path requests during source discovery and makes strict byte range caps a regression requirement.

## Requested tester action
Independently audit:
- finite list of exact endpoints and maximum response budgets;
- correct distinction between FPI-only, combined FII/DII, transaction-level and synthetic/seeded data;
- range request behavior (206 and Content-Range must match; any server ignoring Range is rejected);
- no path to full file fetch, no unbounded retry and no automatic source retry outside the list;
- source vintage/publication lag and the difference between a source-date sample and proof of 752+ useful sessions.

Return PASS or REQUEST CHANGES for this specification only. A spec PASS authorizes implementation plus offline regression tests—not network retrieval. A separate code gate and a separate one-run exact-snapshot manifest will be required before any source probe is made.

**Developer → Tester:** Review spec blob `4e30415632545c04a2875d627afa0191afe3f383`, with particular attention to the HF byte-range and CDSL XLS limits. Do not authorize network calls at the spec gate.

**Tester → Developer:** Only after a spec PASS may the developer implement the finite sampler and offline tests. Require a fresh exact-blob code-gate PASS and manifest before any data probe. No full-history acquisition or model fitting.


## Budget reconciliation completed before tester review

The original draft had two inconsistencies, now corrected in frozen spec blob `30a8b77828b61c74d5de9c94d3033254a598b37a`:
- Sum of per-source maximum body budgets was 1,584 KiB, not an over-budget total; the spec states that global 2 MiB cap and body-budget sum explicitly.
- Range responses are now strict: only HTTP 206 with exact matching Content-Range is accepted. HTTP 200 is always rejected, even if it carries a Content-Range header.
- The spec now enumerates exact initial URL shapes and the source-specific redirect policy. Maximum is 15 initial probes plus at most three single-hop redirects only for the HF HEAD/range requests (18 HTTP exchanges maximum). All other redirects are rejected without follow-up.
- Redirects to any unregistered HF host are rejected rather than broadening the allowlist; no HF tokens/cookies are forwarded to redirect targets.


## Additional metadata-safety correction before tester review

- The spec now uses only GitHub Contents **directory** endpoints (`/contents/data`) to read tracked file sizes and SHAs. It expressly forbids file-specific `/contents/data/history.json` requests because the Contents API can return the entire small file body inline. This prevents repeating the earlier unintended raw-history retrieval.
- Hugging Face tail sampling is conditional on a credible HEAD Content-Length greater than 8 KiB. Missing/invalid length or a file no larger than the head sample means skip the tail request and mark the source not verified.
- New offline test requirements cover safe directory metadata parsing, no inline file contents, range length math, allowed/disallowed redirects, redirect hop caps, and credential stripping.


## Clarification after tester comment

The spec's redirect rule was clarified to remove an internal contradiction: every non-HF-data request rejects all redirects without following them; only the HF HEAD and two Range requests may follow one redirect to an explicit host allowlist. Latest spec blob: `4e30415632545c04a2875d627afa0191afe3f383`. This is a scope tightening, and the latest exact blob must be reflected in the tester report before implementation.


## Code/workflow gate submission — 2026-10-10

The source-discovery sampler and separate workflows are implemented on the developer branch. No live source requests have been made by this snapshot.

- Frozen proposal: `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md` (Git blob `4e30415632545c04a2875d627afa0191afe3f383`; current spec-only tester gate PASS).
- Code review request: [PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md).
- Snapshot commit: `b3a6c3dcde845923a0dba55a0f350d5e67361a76`.
- Hosted offline suite: [Run 38028738968](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38028738968), 27/27 tests passed.

The six protected blob IDs and byte SHA-256 values are in the review request. Key safeguards include exact URL/method/range allowlists, shared request/byte budgets, strict 206/Content-Range checks, redirect allowlists and credential stripping, synthetic/provenance rejection, and a one-use approval manifest consumed **before** any source request.

Recent test failures while tightening the byte-range contract were fixture mismatches: old 4-byte range fixtures and one stale Content-Range assertion were updated. These failures and their corrections are recorded in the error log. They are superseded by the 27/27 green exact-snapshot run.

**Current gate:** independent tester code review pending. A code-gate PASS may authorize a new single-use manifest only; it does not authorize source requests. The one-run manifest is absent; no full history, feature table, labels, model fit, metrics/p-values or final-holdout access is authorized.

**Developer → Tester:** Review all six current protected blobs against the hashes in the code review request, especially one-run consumption before data access.

**Tester → Developer:** Return PASS/REQUEST CHANGES against this exact snapshot only. Keep network access blocked until a separate single-use manifest validates.
