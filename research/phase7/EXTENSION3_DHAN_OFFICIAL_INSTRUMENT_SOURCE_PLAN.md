# Extension 3 — Official Dhan Instrument-Source Validation Plan

**Status: PROPOSED — documentation review only; no request authorized.**  
**Predecessor evidence:** redirect-target probe run [#9 / 38047946667](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38047946667), independently reviewed in `research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_PROBE_RUN9_TESTER.md`.

## Research question

Can the Dhan instrument master be acquired through a directly documented official URL, without following the HTTP 302 from `api.dhan.co/v2/instrument/IDX_I`, and can the source be used only for instrument/security-ID mapping?

## Public documentation evidence (no live source request made)

Dhan's official [Instrument List documentation](https://dhanhq.co/docs/v2/instruments/) documents:
- Compact CSV: `https://images.dhan.co/api-data/api-scrip-master.csv`
- Detailed CSV: `https://images.dhan.co/api-data/api-scrip-master-detailed.csv`
- Segmentwise endpoint: `https://api.dhan.co/v2/instrument/{exchangeSegment}`

The official docs describe the CSV files as instrument lists with security IDs and related instrument metadata. This documentation supports considering a direct documented CSV endpoint as an alternative *candidate*, but does not establish that a request succeeds from the repository runner, that its contents are complete/current, or that the data provides price history. Historical candles are a separate API documented at [Historical Data](https://dhanhq.co/docs/v2/historical-data/).

## Scope of this plan

**This phase is documentation/code review only.** No HTTP request, redirect follow, token use, CSV download, price-history request, or dataset change is authorized by this file.

### Gate A — tester review of proposal

The independent tester must check:
1. The candidate URL is transcribed exactly from the official Dhan documentation.
2. The plan distinguishes instrument metadata from OHLC/options market history.
3. The next request scope is bounded and does not inherit the SPENT redirect manifest.
4. No secret is required for a public CSV unless official documentation states otherwise; do not send Dhan credentials to `images.dhan.co`.
5. Cache policy, size/timeout/byte caps, content-type validation, CSV schema checks, and redaction are specified before any implementation or request.
6. The plan does not authorize price history, option chain, DII/FII, news, or market-wide source access.

### Gate B — developer implementation, only after Gate A passes

Implement offline-only tests and a source adapter that:
- requests only the directly documented URL, with redirects disabled;
- uses a strict timeout and maximum response size;
- does not send access tokens or client identifiers;
- validates HTTPS, hostname allowlist, content type, bounded body size, CSV headers, encoding, duplicate security IDs and required fields;
- writes to a temporary file and atomically caches only after all validation succeeds;
- records URL, fetch time, byte count, response status, schema/version fingerprint and SHA-256 without logging secrets;
- never treats the instrument master as price history.

No live request until a fresh exact-snapshot tester report and a new one-use manifest explicitly authorize the bounded CSV request.

### Gate C — separate single-use data request

If Gates A and B pass, request a new tester decision and create a fresh manifest pinned to the exact developer commit, protected file Git blobs/SHA-256, test file, workflow, this proposal and tester report. The manifest must specify:
- exactly one GET to the exact official CSV URL;
- zero credentials/authorization headers;
- no redirect following;
- a strict response byte cap and timeout;
- explicit expected CSV schema/required columns;
- no price-history, option-chain or other API calls;
- artifact-only result for independent tester review.

Do not reuse the SPENT redirect-target manifest. A request that redirects, exceeds the cap, has unexpected content type/schema, or fails any validation must fail closed with no accepted cache.

### Gate D — independent artifact review

The tester verifies run/commit, request count, response/byte counters, absence of credentials, exact URL/host, redirect handling, cache hash, CSV schema, row counts, duplicate/missing identifiers, and consistency with official documentation. Only a separate PASS may make the instrument mapping available to later research steps.

## Acceptance criteria

- Source URL is documented by Dhan and requested directly.
- No credential is sent to the CSV host.
- The fetch remains within the one-request and byte budgets.
- CSV schema and security-ID uniqueness checks pass.
- Cache is content-hashed, reproducible and stored with provenance.
- Tester signs off the immutable artifact separately.

## Rejection criteria

Any unexpected redirect, non-HTTPS destination, hostname mismatch, credential requirement not documented by the official source, response over cap, malformed CSV, ambiguous security-ID mapping, or missing tester authorization means reject and do not use the cache.

## Scientific interpretation

Even a successful instrument-master acquisition would only resolve instrument metadata/security-ID mapping. It would **not** establish availability of NIFTY prices, historical candles, options history, DII/FII flow, sentiment, or a predictive model. Those require separate source discovery, provenance, and gates.

**Developer → Tester:** Review this proposal only. No live request is authorized. Return PASS/REQUEST CHANGES and list any schema, privacy, provenance or request-budget defect.

**Tester → Developer:** Do not implement a live path or request the CSV until the proposal and exact code snapshot are separately approved.
