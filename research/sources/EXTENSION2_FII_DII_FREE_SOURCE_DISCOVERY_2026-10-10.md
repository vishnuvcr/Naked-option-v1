# Extension 2 — Free FII/DII Historical Source Discovery

**Search date:** 2026-10-10  
**Purpose:** identify free sources that might supply G14/G15 inputs before declaring historical cash-market flows unavailable.  
**Scope of this note:** repository metadata, README and search-result inspection only. No new full history file was downloaded, and no values here have been accepted into the research dataset.

## 1. Official sources

| Source | What it offers | Current evidence and limits |
|---|---|---|
| [NSE FII/FPI & DII reports](https://www.nseindia.com/reports/fii-dii) | Exchange-displayed daily buy/sell/net cash-market values, both NSE-exclusive and combined NSE/BSE/MSEI variants | The page explicitly says values are provisional and subject to revision. The bounded sampler's date-parameter API ignored the requested July 2024 range and returned current 2026-10-09 rows. Therefore the specific date-query route is not yet verified as a historical source; do not use it as such. |
| [SEBI FPI curated links](https://www.sebi.gov.in/curation/fpi.html) | Links to NSDL/CDSL FPI publications including historical trade-wise equity reports | Potentially relevant alternative for foreign portfolio flows, but not automatically interchangeable with combined FII/FPI and DII cash-market aggregate series. Need a separate definition/source review before considering a proxy. |
| [NSE historical-report archive](https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives) | Historical index and Advances/Declines archives | Primary leads for G03/G17; Gate A confirmed the relevant daily index CSV contains the required ten sector names and NIFTY 50. Date parsing was corrected after the first artifact was rejected. |

## 2. GitHub public repositories inspected

Repository metadata/tree listing and README were inspected; raw history JSON files were not downloaded in this discovery step.

| Repository | Observable metadata / README claim | Assessment for G14/G15 |
|---|---|---|
| [chirag127/fii-dii-activity-api](https://github.com/chirag127/fii-dii-activity-api) | Per-date static JSON endpoints; repository tree currently has 63 dated files from 2026-06-22 through 2026-10-01 | Useful for a small response-schema sample and possibly current-day fallback. Its visible tracked date coverage is far below 500 sessions. |
| [MrChartist/fii-dii-data](https://github.com/MrChartist/fii-dii-data) | README documents an API endpoint described as “full history (800 records)” and repository tree includes data/history.json (143,498 bytes) | High-priority follow-up lead, but claims and current artifact findings disagree: the earlier bounded Gate A artifact recorded 164 unique dated records from 2026-01-14 to 2026-09-30. The file appears to have changed or different endpoints/schema may be involved. Do not assume either count is definitive. Verify a bounded source sample under separate approval, including the actual row/date range and provenance. |
| [marketcalls/fii-dii-data](https://github.com/marketcalls/fii-dii-data) | README advertises daily last-15 rows, weekly 12 weeks, monthly 24 months and annual aggregates; tree contains data/history.json of 3,993 bytes | Likely a recent rolling daily window plus coarser aggregates. Aggregates cannot substitute for daily observations in the registered walk-forward model. Small-sample feasibility candidate only. |
| [r7sh7/fii-dii-data](https://github.com/r7sh7/fii-dii-data) | README claims historical history going back 14 years; tracked data/history.json is only 1,503 bytes | README claim versus tracked file size requires validation. Treat as unverified until actual row count and earliest/latest dates are independently inspected. |
| [nagarahasyamm/fii-dii-data](https://github.com/nagarahasyamm/fii-dii-data), [thisisamu/fii-dii-analysis](https://github.com/thisisamu/fii-dii-analysis), [gothamSpark/fii-dii-data](https://github.com/gothamSpark/fii-dii-data) | Their README blobs are identical and describe the same embedded dashboard with 15 daily rows, 12-month monthly aggregates and annual figures | These are not independent historical data sources. Do not count each fork/copy as separate corroboration; daily range remains short. |
| [MrChartist raw-history repository](https://github.com/MrChartist/fii-dii-data/tree/main/data) | Tree exposes a tracked history JSON plus fetch logs and other aggregate files | Publicly accessible in principle, but its full JSON must not be downloaded during the current sample-only gate. A later bounded sample gate should verify count/date span and source labels without automatically importing the entire file. |

## 3. Other free public dashboards discovered

These are search leads, not accepted data. Their daily values, historical coverage, row-level source dates, endpoint limits and source-vintage rules have not been independently reconciled.

- [Stockezee — FII/DII historical data](https://www.stockezee.com/fii-dii-historical-data) describes a day-by-day cash-market and derivatives-flow archive. A page excerpt shows October 2026 daily values and claims an archive; the underlying history endpoint and earliest date are not yet validated.
- [StrikeVue — FII/DII data](https://strikevue.com/in/fii-dii-data) describes about six months of daily flows, insufficient by itself for the planned 500+ aligned sessions.
- [RG Tools — FII/DII data](https://tools.ruchirgupta.in/tools/fii-dii/index) exposes From, To and Load Range controls with a daily table; its API and historical range are not yet validated.
- [Ansaar — FII/DII data](https://www.ansaar.in/equities/fii-dii-data) describes the last 30 sessions; this is insufficient alone.
- [ChartDrift](https://www.chartdrift.com/fii-dii) advertises a date-filtered view/export; the earlier bounded HTML sample parsed only 16 recent rows, so the actual range/export endpoint requires further inspection.

A search-engine query for Kaggle did not surface a clearly matching, freely accessible daily FII/DII cash-flow dataset in the results inspected. This is not proof that none exists; no Kaggle dataset is accepted or ruled out by this limited search. Hugging Face search surfaced Indian market OHLCV/options datasets, but not a clearly matching FII/DII daily cash-flow dataset in the results inspected. Price/option data are relevant to other research families, not direct evidence of G14/G15 coverage.

## 4. Method/data qualification

1. Do not combine source series with different scopes without a versioned mapping. NSE-exclusive figures and combined NSE/BSE/MSEI figures are different series.
2. The registered feature is a cash-market buy/sell imbalance, with a one-session source lag. It is not a derivative participant OI series, and should not be silently replaced by futures/option positioning.
3. Secondary sources must record their origin, date range, schema, retrieval timestamp and SHA-256; published provisional/revised values are a point-in-time limitation.
4. A source claiming “800 records” or “14 years” is only a discovery lead until a sampled response proves actual unique dates, schema completeness, numeric values and provenance.
5. Continue with free sources before considering any paid source. No full-history dataset was fetched or accepted in this source-discovery step.

## 5. Next bounded source-discovery task

After the corrected Gate A parser/code snapshot gets its independent code gate and the official index/API validation sample is rerun, create a new, separately reviewed **small-source** sampler for the remaining FII/DII leads:
- one fixed date per-date JSON endpoint from chirag127;
- small bounded requests / metadata for Stockezee, RG Tools and ChartDrift range filters;
- one deliberately bounded record slice if the provider supports it, or otherwise a fail-closed response-size/row-limit plan for the large MrChartist history file;
- repository metadata/README and source-file history to resolve the current size/count discrepancy without importing full data.

The next decision should be based on an independent artifact audit. Do not advance to full history or model fitting until 500+ valid dated sessions, source lineage and historical-vintage limitations are sufficiently established and a later exact-snapshot gate authorizes the acquisition.


## 6. Further free-source leads found on 2026-10-10 (metadata/page only)

### CDSL archive — promising independent FPI data source

- The [CDSL Daily Trends page](https://www.cdslindia.com/publications/FIIDailyData.aspx) provides daily FPI investment reports and explains that confirmed figures are based on custodian reports covering trades on and up to previous trading days. A web-rendered historical report was visible for 30-Aug-2024, including equity gross purchases/sales/net investment; that report is FPI-only, not DII.
- The [CDSL FPI archive index](https://www.cdslindia.com/Publications/ForeignPortInvestor.html) contains date links for daily FPI reports including 2024 dates. Example linked XLS URL observed on the index: `https://www.cdslindia.com/downloads/Publications/Latest/Latest_30092024.xls`. An additional example was `Latest_09102024.xls`. The browser inspection couldn't decode XLS, so no values from these files were accepted.
- CDSL exposes an archive form at [FIITrends.aspx](https://www.cdslindia.com/Publications/FIITrends.aspx) labelled "1999-Till Date", but that route returned HTTP 403 through the web reader. This is a failed bounded discovery attempt, not evidence that the archive itself is unavailable.
- Coverage in the visible daily link list goes back to at least September 2024, but this list alone does not establish 500+ sessions. A next approved sampler should test only two or three exact historical XLS links and inspect the archive metadata page, with strict byte limits. CDSL offers FPI, not DII; it cannot fill G15 alone.

### Hugging Face candidate — requires bounded sample validation

- Dataset: [johnwick3690/stocks](https://huggingface.co/datasets/johnwick3690/stocks).
- A public dataset commit listing showed a file at `nifty historical data/fii dii data/fii_dii_2024_to_today.csv` with 503 added lines, plus a separate `fii_derivatives_historical_2024_2026.csv` and an F&O contract file.
- The 503-line indication is a promising lead for daily cash flows, but it does not prove there are 500 unique valid market sessions, that each row contains both FII/FPI and DII, or that values are real and sourced correctly. The dataset card/API metadata and tiny head/tail byte-range samples must be checked under a newly approved scope. No file content was downloaded in the search that identified this link.

### Provenance correction — Mr. Chartist seed code and one out-of-scope read

- GitHub repository source-code review of [MrChartist/fii-dii-data](https://github.com/MrChartist/fii-dii-data) found `scripts/seed_history.js` explicitly says it **generates realistic per-day FII/DII records from known monthly/yearly aggregate totals for roughly the last six months**. Therefore any rows marked `historical-seed` are synthetic/backfilled estimates, not observed daily cash-flow records; they must be excluded from empirical training and confirmation. The repository's raw history file has mixed source labels and must not be accepted wholesale.
- During this source review, the entire public `data/history.json` file (143,498 bytes) was inadvertently retrieved while inspecting the repository. It was **not copied into project research data, not treated as a valid dataset, and no model or feature was run on it**. This exceeded the intended metadata/code-only discovery scope and is logged in `research/ERROR_LOG.md` as non-accepted evidence. Future source discovery must fetch repository metadata/code only until an exact bounded sample gate authorizes data probes; never request the history file itself just to inspect its README or code.

### Additional official lead — SEBI FPI transaction data

- [SEBI Trade-wise Equity Data of FPI](https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html) lists monthly transaction-level equity archive files going back to 2003. The page documents fields including transaction date/type, value, ISIN and report date. This is not directly equivalent to the daily combined FII/FPI/DII cash market totals required by G14/G15, and it contains no DII side. Consider it only as a possible separately specified FPI proxy if daily cash-flow aggregate sources cannot be reconciled, with reporting lag/vintage constraints treated explicitly.

## 7. New next step needed

A new bounded source-discovery spec should separately define:
1. CDSL archive-page metadata plus at most three exact daily XLS samples, each under a fixed response-size cap.
2. Hugging Face dataset metadata and two strict byte-range CSV samples (header/first records and tail records), refusing any response that ignores Range; maximum bytes/rows checked in tests.
3. A single-date `chirag127` JSON sample and small metadata/row-count probes of `marketcalls`/`r7sh7`, rejecting placeholder or synthetic-seed provenance.
4. Metadata/code-only review of the seed scripts for these candidate repos; no raw full-history file pulls.
5. An explicit audit rule to reject synthetic/generated/backfilled “realistic” day-level values, and no source switching based on observed predictive results.

This phase needs its own independent tester review, code/test gate, one-run manifest and post-sample artifact audit. **No further source request is authorized by the spent Gate A manifest, and no full-history acquisition/model fitting is allowed.**
