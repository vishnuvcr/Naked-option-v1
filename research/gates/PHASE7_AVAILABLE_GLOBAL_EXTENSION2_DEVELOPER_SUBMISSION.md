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
