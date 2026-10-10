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
