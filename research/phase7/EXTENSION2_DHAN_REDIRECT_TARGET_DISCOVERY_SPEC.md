# Extension 2 — Dhan Instrument-Endpoint Redirect Target Discovery

**Status: PROPOSED — no request authorized yet.**  
**Purpose:** Diagnose the documented `GET https://api.dhan.co/v2/instrument/IDX_I` HTTP 302 without following the redirect or downloading data.

## Background and evidence

The first Dhan sample found a valid token and active Data API plan, but the segment instrument endpoint returned a non-200. The corrected bounded diagnostic retry reported HTTP 302:
- Run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043667443
- Artifact: `11667455094`
- ZIP SHA-256: `f388a9844db92836ec6551e2e442e207dc8d504bc9ae198df860117a2aabc68e`

The official Dhan instrument-list documentation shows the segment endpoint and also documents CSV instrument master URLs: https://dhanhq.co/docs/v2/instruments/. The current policy intentionally rejects redirects. No Location value or destination host was stored, and no redirect was followed.

## Research question

Does the 302 target a documented, official Dhan instrument-list host/path that can be used safely under a separate one-hop, no-credential-forwarding policy?

## Fixed scope for one diagnostic call

- One GET only: `https://api.dhan.co/v2/instrument/IDX_I`.
- Inject `DHAN_ACCESS_TOKEN` only in this request's header.
- Do not follow the redirect.
- If the response is 3xx, extract only the `Location` URL's normalized scheme and hostname; do not persist path, query, fragment, userinfo, cookies or any other header.
- The hostname must be lowercase, IDNA-normalized, and at most 253 characters; scheme must be HTTPS. If URL parsing fails, report `REDIRECT_TARGET_UNPARSEABLE`.
- Response body cap: 1 KiB; total body cap: 1 KiB; maximum requests: one; timeout 20 seconds; no retry.
- If response is non-redirect, record only status and safe content type; do not save body or error text.
- No historical candle calls, no all-instrument CSV download, no alternate endpoint, no redirect follow, no data parsing beyond redirect metadata.
- The prior Dhan sample manifest is SPENT and must not be reused. This step needs a fresh tester-approved code gate and one-run manifest.

## Acceptance / rejection rules

- Accept only a syntactically valid HTTPS redirect host for analysis.
- Do not automatically follow it, even if it appears official.
- Compare the hostname against official Dhan documentation only after the sample; a new allowlist or one-hop follow must be a separately reviewed change.
- If host is not official/documented, leave the endpoint blocked and propose an official source alternative with bounded scope.
- No raw Location string may appear in logs or artifacts.

## Prohibited work

No historical candle acquisition, full-history download, cache population, feature/label construction, model fitting, prediction metrics, options strategy evaluation, or final-holdout access.

**Developer → Tester:** Review this redirect-target-only specification. It authorizes no request by itself.

**Tester → Developer:** If passing, permit implementation/offline tests only. The live diagnostic needs a new exact-snapshot code gate and one-run manifest. The result artifact requires separate review before any redirect is followed.
