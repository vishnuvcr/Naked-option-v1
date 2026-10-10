# PPR-4 Tester Review 4 — Wave 1 Metadata-Only Request Manifest

**Date:** 2026-10-11  
**Branch:** `phase-07-tester`  
**Decision:** **PASS WITH SCOPED RESTRICTIONS — THREE DOCUMENTATION GETS ONLY**

## Exact snapshot

Developer blob: `cf49868c077b006315b0576519933312333a6efb`  
Manifest: `research/phase7/PPR4_WAVE1_METADATA_REQUEST_DRAFT.json`

## Structural checks

- Exactly 3 requests are specified.
- All requests are documentation-page GETs with empty query objects, one request each, no retries and no redirects.
- Per-response cap is 2 MiB; total cap is 5 MiB.
- Each request expects documentation HTML and permits only extraction of visible documentation/link labels/terms.
- Historical value endpoints, data files, redirects, authentication, cache/model-panel ingestion and model fitting are prohibited.
- Top-level request/download/model flags remain false in the submitted proposal.
- Independent schema check findings: no structural exceptions found.

## Scope of this PASS

The only newly authorized operations are one GET each to these exact public documentation URLs:
1. `https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives`
2. `https://www.nseindia.com/static/products-services/indices-indiavix-index`
3. `https://home.treasury.gov/treasury-daily-interest-rate-xml-feed`

Maximum aggregate bytes: 5 MiB. Maximum per response: 2 MiB. No retries, no redirects, no authentication, no query parameters, no following links. Record response status, content type, retrieval timestamp and content hash. If any URL redirects, exceeds the cap, or returns something other than the expected documentation, stop without retry or alternate endpoint.

This approval is **not** a data-sample authorization. It does not permit historical price/VIX/yield payloads, downloads, modeling-panel acceptance, feature/label generation, fitting/tuning/scoring, holdout forecasts/labels, or options P&L. The broader PPR-4 source-acquisition gate remains closed.

**Developer → Tester:** After completing only these exact documentation GETs, submit response metadata/hashes and a revised source register for review before any data-series sample.

**Tester → Developer:** Enforce the three-URL allowlist and byte limits; do not follow links or retrieve data values.
