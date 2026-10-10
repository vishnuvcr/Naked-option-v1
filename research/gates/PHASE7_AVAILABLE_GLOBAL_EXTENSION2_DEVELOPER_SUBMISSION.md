# Developer Submission — Phase 7 Available-Data Prediction Extension 2

**Status: SPECIFICATION REVIEW REQUESTED — NO EMPIRICAL EXECUTION AUTHORIZED.**

## Why this next step

Run #44 completed the first available-data cross-market family and was independently audited. Its five horizon-family p-values were 0.9840, 0.8882, 0.6786, 0.7745 and 0.9800; every Bonferroni-adjusted p-value was 1.0. No model was promoted. This does not exhaust the registered method universe. The next prediction-only proposal covers methods already in `research/METHOD_REGISTRY.md` that were not part of Run #44.

## Exact proposal

- Specification: [AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md)
- Research plan updated: [RESEARCH_PLAN.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/RESEARCH_PLAN.md)
- Prior result summary: [Run #44 result report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/results/PHASE7_RUN44_AVAILABLE_GLOBAL_PREDICTION_RESULTS.md)
- Prior independent result audit: [Run #44 tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md)

Frozen candidate universe: G03 sector leadership, G14 FII/FPI net flow, G15 DII net flow, G17 advance/decline breadth, F03 put/call OI ratio, F04 OI-change acceleration, and F05 volume/OI pressure. Five existing horizons remain 1/2/3/5/10 sessions. The global family test uses a maximum statistic across all 35 method/horizon combinations.

## Source leads reviewed

- NSE F&O UDiFF Common Bhavcopy Final ZIP, participant OI/volume reports: https://www.nseindia.com/all-reports-derivatives
- NSE historical index and Advances/Declines archives: https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives
- NSE FII/FPI and DII CSV reports (provisional/revisable): https://www.nseindia.com/reports/fii-dii

These are source leads only. Full history has not been downloaded, no normalized feature data exists, and no model has been fit.

## Requested tester actions

1. Independently check the exact spec commit and compare each candidate to the finite method registry and earlier phase outcomes.
2. Verify formulas and sign conventions, frozen sector set, option contract/expiry eligibility, source-vintage limits, exchange-local dates, one-session lag, and prohibition on same-date EOD inputs.
3. Audit the one-global-max bootstrap design for aligned dates, missing/abstained forecasts, and family-wide multiple-testing control.
4. Check the stop conditions and confirm the final untouched holdout remains unopened.
5. Return PASS or REQUEST CHANGES. If passing the specification, authorize only Gate A source-feasibility work (small deterministic archive samples and schema/coverage checks); this is not permission for full-history acquisition or empirical model fitting.

**Developer → Tester:** Review the proposed extension on the isolated tester branch and return concrete mathematical/data-governance findings. Do not authorize full data acquisition or model fitting at this gate.

**Tester → Developer:** No implementation or empirical fit may proceed until the exact spec receives an independent decision. Any changed candidate set, formula, expiry filter, timestamp rule, or multiplicity method requires a versioned spec amendment before results are viewed.


## Resubmission after tester REQUEST CHANGES — 2026-10-10

Tester report: [PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SPEC_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SPEC_TESTER.md), disposition **REQUEST CHANGES**. The developer corrected the spec at blob `7f6cc6e86556db3da9f87c23c0e183bcb3282310`:
- Added explicit legacy F&O bhavcopy to UDiFF canonical mapping and transition-date audit requirements.
- Replaced undefined NIFTY traded-value flow normalization with fixed `(buy-sell)/(buy+sell)` imbalance and zero-denominator handling.
- Defined F04 log-OI change/acceleration and F05 aggregate volume/OI pressure formulas.
- Replaced the ambiguous Energy/Oil & Gas alias with exact NIFTY Energy index identity and froze all ten sector names.
- Defined the 500-date minimum common grid and zero-improvement treatment for unavailable candidate forecasts in the global max-statistic bootstrap; added a synthetic abstention regression requirement.

No source feasibility downloads or model fitting occurred during this correction. The corrected exact spec is resubmitted for tester review; only a PASS can authorize Gate A small-sample source feasibility.

**Developer → Tester:** Re-review the corrected spec blob and explicitly decide whether Gate A may begin. Do not authorize full-history acquisition or model fitting at this stage.

**Tester → Developer:** If any formula, archive transition, or missingness rule remains ambiguous, return REQUEST CHANGES with a precise correction before source access proceeds.


## Final specification clarification before independent re-review — 2026-10-10

The G03 sector formula has been made explicit as two features: equal-weight sector excess 1-session return and equal-weight sector excess 5-session return, each relative to NIFTY and calculated across all ten frozen sector indices. The spec also allows a secondary public provider only for the identical index definition after a pre-run 60-session overlap audit, a frozen source mapping and documented source lineage; no performance-driven source switching is permitted.

Current exact spec blob: `8b5f17dd05c2f2d379142ca8eb2779149ca0fdbc`. No data has been downloaded. Please review this exact blob, not the earlier version.

**Developer → Tester:** Review this final spec snapshot and decide whether Gate A small-sample source feasibility may begin.

**Tester → Developer:** Return the gate decision against blob `8b5f17dd05c2f2d379142ca8eb2779149ca0fdbc`; do not authorize full-history acquisition or fitting.


## Gate A sampler implementation submitted for tester review — 2026-10-10

The tester passed the spec for small-sample source feasibility only. The developer has prepared a bounded sampler and offline regression fixtures, without running them against live sources yet:

- Sampler: `scripts/phase7_extension2_source_feasibility.py`, blob `a35178de4c32a9f86ae1b710a14fd2a8eb7ec072`.
- Offline tests: `scripts/test_phase7_extension2_source_feasibility.py`, blob `eac0e4289ebb6321c08677cc2301c8fc60aa0e13`.
- The sampler fetches only two single-day F&O ZIPs (2024-07-05 legacy and 2024-07-08 UDiFF), plus small official-page/API responses for sector-index, FII/DII and breadth source discovery. It validates headers/date/NIFTY option rows, records each attempted URL/status/retrieval time/hash, and stores only a small JSON feasibility report; it does not download full history, construct labels/features, or fit a model.
- A third-party GitHub archive mirror is a fallback only after official NSE archive hosts fail, and the report records which source actually supplied the bytes.

**No workflow has been added or run yet.** Please independently review the sampler and offline tests before the Gate A workflow is added.

**Developer → Tester:** Review network scope, fallback provenance, file size limit, archive/schema/date checks and offline tests. Pass or request changes; do not authorize full-history acquisition or model fitting.

**Tester → Developer:** Only after this sampler code gate passes may the small-sample Gate A workflow be enabled.


## Gate A sampler resubmission after REQUEST CHANGES — 2026-10-10

Tester report `research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_TESTER.md` found that the initial sampler validated only the first row's trade date. The developer corrected it to validate every row and record the distinct trade-date count.

- Corrected sampler blob: `f39f2a213b760c608e0deca2f1eaacc2225aca53`.
- Corrected offline tests blob: `2d8833719701c87e43f310396b29380220d58578`.
- Added negative fixtures where the first row is valid but a later row has a different trade date, for both legacy and UDiFF formats.
- No workflow or live source download has run. Please re-review these exact blobs.

**Developer → Tester:** Verify all-row date validation and both mixed-date tests; if passed, the Gate A workflow may be added and run for small samples only.

**Tester → Developer:** Do not enable the workflow until a fresh explicit code-gate PASS is recorded.


## G17 source fallback amendment submitted for tester review — 2026-10-10

Run #1 found that the official Advances/Declines page exposed no dated historical rows in the bounded sample. The developer has amended the spec to include a deterministic source-selection rule: use official dated A/D history only if Gate A verifies at least 500 dated sessions; otherwise derive daily breadth from official equity bhavcopy using a frozen `SERIES=EQ`, `ISIN` prefix and positive-close/volume filter, matched by ISIN. This is a source fallback, not a post-result candidate choice.

Current spec blob: `a5e65b56f9aa23c8292b718403c3db4448dad2e3`. The amendment also records the exact official daily index CSV pattern for G03. Please independently review the G17 fallback universe and formula before the revised source sampler is run.

**Developer → Tester:** Review the exact G17 amendment and decide whether the derived breadth definition is acceptable under the registered prediction-only scope.

**Tester → Developer:** Do not run the revised sampler or build breadth features until the amendment is explicitly passed.


## Revised Gate A sampler v2 submitted for tester code review — 2026-10-10

After Run #1, the developer prepared a revised bounded sampler using the official NSE daily index CSV pattern and daily equity bhavcopy samples, plus small FII/DII coverage checks:

- Sampler: `scripts/phase7_extension2_source_feasibility_v2.py`, blob `2cc90715401e7a99f63bd69bb99774ce53f56113`.
- Offline tests: `scripts/test_phase7_extension2_source_feasibility_v2.py`, blob `baecbf17db9b2b1734c7c0f5321ee6cf986b4cd9`.
- It requests only two daily index CSVs (2024-07-05, 2024-07-08), two single-day equity bhavcopy archives (legacy and UDiFF), one small 164-row GitHub FII/DII history file, and bounded current/history-page responses from free sources. No full history or model fit is included.
- It checks all ten frozen sector indices plus NIFTY 50, all-row dates, legacy/UDiFF equity schema, eligible `SERIES=EQ`/ISIN/close/volume counts, and FII/DII historical coverage/duplicate dates.
- The G17 derived-breadth fallback is now part of the amended spec, and the tester has passed that source-definition amendment for source feasibility only.

**No v2 workflow has been added or run yet.** Review these exact sampler/test blobs before enabling the next Gate A workflow.

**Developer → Tester:** Independently review the v2 network scope, exact source dates, row/date/schema validation, and FII/DII coverage reporting. Pass or request changes.

**Tester → Developer:** Do not enable the v2 workflow until a fresh code-gate PASS is recorded.
