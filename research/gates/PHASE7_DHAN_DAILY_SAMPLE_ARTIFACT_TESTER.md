# Independent Tester Report — Dhan One-Use Sample Acquisition Artifact Review

**Decision: PASS WITH SCOPED RESTRICTIONS — the one-run acquisition and cache artifact are valid; data-model acceptance and any wider acquisition remain blocked pending a direct official NSE Indices cross-check and a separate next-gate review.**

## Run and state-transition evidence

- Guarded acquisition run: [38055202149](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38055202149), conclusion `success`.
- Offline test run: [38055202163](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38055202163), conclusion `success`.
- Run commit: `97b455b9060536bc9ee8cee9b16d6c4d27035fb7`.
- Final developer branch head after run artifact commits: `1463efd4380aae34da9bd456d44e9f5ec60950e2`.
- One-use approval: `SPENT`, exact scope `dhan-nifty50-daily-2024-01-02-one-request`.
- Approval was pushed as SPENT before the source-request step, with `spent_from_commit=6cc6ece9a97c6e86df49db37b553508810c78d09`.
- No attempt was retried; no redirect was followed.

## One-row source receipt and cache

| Field | Observed result |
|---|---|
| Endpoint | `https://api.dhan.co/v2/charts/historical` |
| Request | `securityId=13`, `exchangeSegment=IDX_I`, `instrument=INDEX`, `fromDate=2024-01-02`, `toDate=2024-01-03`, `oi=false` |
| HTTP/content type | `200`, `application/json` |
| Requests / bytes / retries / redirects | `1 / 121 / 0 / 0` |
| Response SHA-256 | `efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70` |
| Cached response blob | `215c3b38889b2a143613766ce33f88d954a1ea9a` |
| Cache manifest blob | `601f956e4e31e5a1288a3381fbf59217e37dee10` |
| Cache bundle | `data/cache/dhan_daily_sample/478f0942f8654bd763b8343a05370f8065ef5041483cb59cc3f7dd6b57ef78ba-efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70/` |
| Redacted status artifact blob | `d9729dc4ec07476f9095402ef72d9b331c99bd4e` |

The status report says `SOURCE_SAMPLE_VALIDATED`, `CACHE_CREATED`, row_count 1, and records no model-fitting or holdout authorization.

## Returned daily observation

| Trading date | Open | High | Low | Close | Volume |
|---|---:|---:|---:|---:|---:|
| 2024-01-02 | 21,751.35 | 21,755.60 | 21,555.65 | 21,665.80 | 263,711,568 |

The source timestamp `1704133800` corresponds to `2024-01-01 18:30:00 UTC`, i.e. `2024-01-02 00:00:00 Asia/Kolkata`. The daily `toDate` was exclusive, so the response date is within the requested [2024-01-02, 2024-01-03) range.

## Independent cross-check performed

EquityPandit's published NIFTY 50 historical table reports the same 2 January 2024 row, with the same open/high/low/close/volume and daily change `-0.35%`: https://www.equitypandit.com/share-price/today/nifty-50-historical-data (visible row at lines 746 of the opened source). Its previous-session 1 January close is 21,741.90. That implies ((21665.80/21741.90 - 1)	imes100 approx -0.3500%), consistent with the table's rounded -0.35%. A second public mirror contains matching OHLC values: https://www.scribd.com/document/820628326/NIFTY-50-Historical-Data.

The officially maintained historical report interface exists at https://www.niftyindices.com/reports and identifies an `Historical Index Data` report with Date/Open/High/Low/Close columns, but the report result for this exact date was not retrieved in this gate. The exact instrument-master mapping for `securityId=13` was likewise not downloaded in this one-request gate. Dhan's documentation is at https://dhanhq.co/docs/v2/historical-data/.

## Mathematical and structural checks

- OHLC consistency: `low <= min(open, close) <= max(open, close) <= high` holds.
- High-low range: (21,755.60 - 21,555.65 = 199.95) points.
- Close minus open: (21,665.80 - 21,751.35 = -85.55) points, a negative close-to-open session move.
- Change vs the previous close reported by the independent table: (21,665.80 - 21,741.90 = -76.10) points; percentage change is approximately (-0.35\%).
- The raw API response has one element in every returned required array; the response hash and byte count in the cache manifest match the actual stored JSON bytes.
- No secret or provider error body was saved to the sample status artifact.
- The one-run workflow and offline tests both completed successfully; the approval is not reusable.

## Restrictions and next gate

**PASS WITH SCOPED RESTRICTIONS.** The acquisition protocol and cached sample pass this artifact review, and the returned values are strongly corroborated by an independent public historical table. However, this one-row sample is **not yet approved as training/validation data** because the official NSE Indices historical row and the exact instrument master mapping have not been independently fetched.

Before data are accepted into the broader prediction dataset, the developer must submit a separate, bounded official-reference cross-check gate for tester review. It should retrieve only the official NIFTY 50 row for 2 January 2024 and the minimal instrument-master mapping needed to confirm `13 / IDX_I / INDEX`, record source timestamps/hashes, compare values field by field, and fail closed on discrepancies. That official-reference request must not reuse the SPENT Dhan manifest. No bulk retrieval, intraday history, rolling options, feature fitting, predictor reruns, strategy testing or holdout access is authorized by this artifact review.

**Tester → Developer:** Record this artifact review and the exact raw response/cache hashes in the research ledgers. Prepare a fresh official-reference-only cross-check proposal/workflow; get its exact snapshot independently reviewed before issuing any public reference request. Keep the Dhan approval SPENT and do not fit or evaluate models on this row until the official reference check passes.
