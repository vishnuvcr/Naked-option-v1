# Phase 7 Gate — Official Primary-Source Cross-Check of the Dhan NIFTY Sample

**Status: PROPOSED — awaiting independent tester review. No request to NSE Indices or Dhan instrument-master source is authorized by this plan.**

## Purpose

The one-use Dhan daily history sample succeeded and was independently reviewed for acquisition integrity. Its OHLCV exactly matches an independent public historical table, but that table is not the authoritative primary source. Before the row is accepted into the research dataset, perform a single-date public official-source cross-check and verify the Dhan security-ID mapping from Dhan's official instrument master.

This is a data-integrity gate, not a research-model gate. It must not retrieve broader history, enrich features, rerun predictions, test options strategies or open the final holdout.

## Research question

Does the already cached Dhan row for 2 January 2024 match the official NSE Indices NIFTY 50 price-index OHLC record for the same date, and does Dhan's official instrument master explicitly map `securityId=13` in `IDX_I` to an index instrument suitable for the requested NIFTY 50 row?

## Frozen values under test

Dhan source snapshot:
- Request date: `2024-01-02` (local Asia/Kolkata trading date).
- Dhan request: `securityId=13`, `exchangeSegment=IDX_I`, `instrument=INDEX`.
- Cached row: O `21751.35`, H `21755.60`, L `21555.65`, C `21665.80`, volume `263711568`.
- Source raw SHA-256: `efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70`.
- One-use Dhan approval remains `SPENT` and is not reused.

## Bounded source lookups proposed

### A. Primary index-price reference

Official owner: NSE Indices, at https://www.niftyindices.com/reports (Historical Index Data). The public site's current front-end calls a historical-data endpoint:
- Exact URL: `https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString`
- Method: `POST`
- Body, with the exact frozen index and same-date window:
```json
{
  "cinfo": "{'name':'NIFTY 50','startDate':'02 Jan 2024','endDate':'02 Jan 2024','indexName':'NIFTY 50'}"
}
```
- Headers: `Content-Type: application/json; charset=UTF-8`, `X-Requested-With: XMLHttpRequest`, and official historical page as referer. No cookies, account credentials or Dhan token.
- Max one request, 20-second timeout, 512 KiB response, no retries, no redirect-follow.
- Expected output is one NIFTY 50 record for 02 Jan 2024. Parser must support only the documented/site-observed JSON envelope and fail closed on any unexpected envelope, date, index name or row count.
- Compare official OPEN/HIGH/LOW/CLOSE to the Dhan cache at exact 2-decimal precision. Record the official row's own hash and safe request metadata. This API route is exposed by the official site's historical-data UI; request shape is also documented in public implementation references, so the first live response must be independently parsed and audited rather than assumed correct.

### B. Dhan instrument mapping

Official instrument master described at https://dhanhq.co/docs/v2/instruments/:
- Exact URL proposed: `https://images.dhan.co/api-data/api-scrip-master.csv`
- Method: `GET`
- No credential, access-token header, cookie or client identifier may be sent to the instrument-master host.
- Max one request, 20-second timeout, 8 MiB response, no retries, no redirect-follow. A redirect or oversized CSV is a fail-closed result; do not switch URL or retry under this scope.
- Validate source bytes with the existing offline `scripts/dhan_instrument_master.py` parser and identify the candidate rows by the actual compact security-ID field for ID `13`; report only the minimum available evidence columns (security ID, exchange, compact segment, instrument name, trading symbol, display/symbol name, and exchange instrument type if present) plus source hash and row number. Do not assume the compact `SEM_SEGMENT` field uses API enums such as `IDX_I`; rely on the official instrument-list schema and Annexure as separate definitions. If the official CSV does not uniquely substantiate an index mapping, stop and propose an alternative under a new review gate.
- The existing 8 MiB cap is provisional. The gate must not infer that the CSV is unavailable or request paid access if this conservative cap fails; log the outcome and require a separately reviewed alternative such as an authenticated, segment-scoped endpoint or a revised cap.

**Total ceiling: two source requests maximum—one request to each host.** Each host has its own no-retry budget. Neither host receives credentials for the other host. No other endpoint is in scope.

## Acceptance criteria

The cross-check can pass only if all conditions below pass:
1. Both requests stay on the exact HTTPS host/path/method allowlist, return HTTP 200 with expected content type and remain within timeout and byte caps.
2. No retry, redirect follow, or credential forwarding occurs.
3. Primary official NIFTY 50 row date and all four OHLC values exactly match the cached Dhan row. If not, fail and preserve both hashes; do not resolve discrepancies by overwriting Dhan data.
4. Dhan's official compact instrument master contains exactly one candidate row with the documented security-ID field equal to `13`, and its available exchange, instrument-name, trading-symbol/display-name and exchange-instrument-type fields (where present) substantiate that the candidate is the NIFTY 50 index. Do **not** compare `SEM_SEGMENT` directly with `IDX_I`: the instrument-list docs describe `SEM_SEGMENT` as a compact segment code (`C`/`D`/`E`/`M`), while the API Annexure defines `IDX_I` as the API-level Index Value exchange-segment enum. Interpret the returned CSV fields according to the instrument-list schema and API enums separately. If no unique index candidate exists or the public CSV schema cannot substantiate the mapping, fail closed; do not accept the row or silently switch endpoints.
5. Both original raw sources, source timestamps, content hashes, response sizes, one-use manifest hash and validation outcome are cached atomically only after the complete comparison succeeds. Safe failure metadata may be written separately, with no raw provider error body.
6. Independent tester reviews the exact source/test/workflow/manifest snapshot and the first run artifact before sample acceptance.

A pass means only that this one daily row and instrument mapping have been independently checked. It does **not** establish historical coverage, qualify a predictive model, authorize full-history acquisition or change the previous null model results.

## Test and workflow plan

- Offline-only tests must use deterministic mocked responses for the exact official endpoint schema, matching/nonmatching OHLC, wrong index/date, zero/two-row results, malformed double-encoded JSON, non-JSON content type, 3xx redirect, 4xx/5xx, invalid length, oversized bodies, CSV BOM/header/missing columns/duplicate IDs, timeout and no-write-on-partial-failure.
- Static workflow regressions must verify no secret environment, no retries/redirects, exact URL allowlist, request order/budgets, explicit manual confirmation defaulting false, and one-use spend-before-fetch behavior.
- Manifest must pin exact Git blob and standard-library SHA-256 values for the script, offline tests, workflows, this proposal and Dhan sample artifact/tester report. Approval begins `PENDING_REVIEW`, records the isolated tester report, then can become `READY` only after an independent PASS. On an authorized run, the new cross-check approval must be pushed as `SPENT` before the first external request.
- A separate workflow on `main` may expose `workflow_dispatch`, but its job must always target `phase-07-developer`. Both workflows must use identical workflow content. Automated pushes must remain pinned to this scope.

## Risks and limitations

- The NiftyIndices history endpoint is served by an interactive web page; its undocumented envelope can change. Parse only a whitelisted response structure; never persist the entire unexpected/error response.
- The public Dhan CSV may exceed the provisional cap or redirect. The approved behavior is fail-closed, not retrying or silently using a different data source.
- Matching OHLC confirms only the specified daily price row. Volume semantics, historical index membership, point-in-time mapping, intraday history, expired options and model value remain untested here.
- Independent public secondary sources already agree with the row, but they do not replace the official primary-source check.



## Amendment note — compact segment vs API enum

Independent review identified that `SEM_SEGMENT` in the compact master must not be required to equal `IDX_I`. Dhan's Instrument List docs describe compact `SEM_SEGMENT` using its own codes (`C`, `D`, `E`, `M`), while the API Annexure defines `IDX_I` as the exchangeSegment enum for Index Value. The cross-check now evaluates the CSV's own mapping fields and interprets `IDX_I` only at the API layer. If the CSV lacks a unique, defensible NIFTY 50 index mapping, the result is a fail-closed mismatch, not permission to change source or expand scope.

Official references: [Dhan Instrument List](https://dhanhq.co/docs/v2/instruments/); [Dhan Annexure](https://dhanhq.co/docs/v2/annexure/).

## Gate state

**Current state: PROPOSED.** This plan neither executes network calls nor changes data acceptance. After the independent tester passes the proposal, developer may implement the offline parser/fetch adapter and tests, then submit that exact implementation for another tester gate. Only a separate manifest/workflow PASS can authorize the two specified bounded lookups.

**Developer → Tester:** Review whether the source scope, endpoints/body, request/byte ceilings, credential boundaries, fail-closed behavior, acceptance arithmetic and workflow/test plan satisfy the approved data-recovery plan. Return PASS or REQUEST CHANGES. Do not authorize a live source call in the plan review.
