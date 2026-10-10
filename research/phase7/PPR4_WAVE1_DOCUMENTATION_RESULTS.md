# PPR-4 Wave 1 Documentation Results

Date: 2026-10-11. Scope: the three exact official documentation URLs approved in tester report `PHASE7_PPR4_TESTER_REVIEW4_WAVE1_METADATA.md`. No linked data endpoints were followed and no historical market values or files were requested.

## Results

| Request | Result | Verified from page |
|---|---|---|
| W1-DOC-001 — NSE historical index archive | Page content returned by web reader. | The page lists Historical Index Data, Total Returns Index Values, India VIX historical data, index daily/monthly reports, F&O contract-wise price/volume and daily/monthly reports. Displayed update date: 10/08/2026. |
| W1-DOC-002 — NSE India VIX methodology | Page content returned by web reader. | NSE says India VIX uses best bid/ask NIFTY option prices to estimate expected volatility over the next 30 calendar days. Page links methodology PDF, white paper and historical-value search. Displayed update date: 18/05/2023. |
| W1-DOC-003 — US Treasury feed documentation | Page title/domain returned; detailed text was not exposed adequately. | The page is titled “Treasury Daily Interest Rate XML Feed.” Query parameters, schema and release timing remain unverified. |

Exact URLs:
- https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives
- https://www.nseindia.com/static/products-services/indices-indiavix-index
- https://home.treasury.gov/treasury-daily-interest-rate-xml-feed

## Important interface limitation

The web reader does not expose raw response byte counts, complete HTTP headers or raw-body hashes. Therefore the 2 MiB transport cap cannot be independently attested from this run. The documentation reads are recorded as metadata evidence only, not as a byte-cap-certified acquisition. No linked PDFs, data endpoints, alternate URLs, retries or authentication were used.

No market series, files, model weights, holdout values or labels were requested. No data was accepted into a model panel; no feature/label generation, fitting, scoring or option P&L occurred.

## Disposition

NSE index archive and India VIX methodology are confirmed documentation leads, not validated data sources. Treasury feed documentation exists, but details need another approved metadata method. Coverage, license/redistribution, point-in-time availability and schema of actual data remain unresolved. The prospective holdout is still design-only. PPR-4 data acquisition remains blocked.

**Developer → Tester:** Review these metadata findings and the byte/header/hash limitation; do not infer data-source approval.

**Tester → Developer:** Keep historical-data requests, cache/model-panel acceptance, model execution and holdout access blocked until a separate exact-source gate passes.
