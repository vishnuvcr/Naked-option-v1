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
- Spec Git blob: `3313d80f539957f1cdeaa8f9baeeb819379c6af1`
- The spec defines a maximum of 15 HTTP requests, 2 MiB total data, two 8-KiB HF byte ranges (requires status 206 + exact Content-Range), no full-file fallback, two fixed single-day CDSL XLS reports, one pinned chirag date JSON, and metadata-only probes for SEBI/NSE/CalcSetu/other mirrors.
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

**Developer → Tester:** Review spec blob `3313d80f539957f1cdeaa8f9baeeb819379c6af1`, with particular attention to the HF byte-range and CDSL XLS limits. Do not authorize network calls at the spec gate.

**Tester → Developer:** Only after a spec PASS may the developer implement the finite sampler and offline tests. Require a fresh exact-blob code-gate PASS and manifest before any data probe. No full-history acquisition or model fitting.
