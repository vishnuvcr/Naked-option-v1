# Developer → Tester Review Request — Dhan Redirect-Target-Only Probe

**Requested decision: PASS / REQUEST CHANGES for specification only.**  
**Spec commit:** `aecd39a35ef411a15ba7ad3bc2d30164bb5b9677`.  
**Live request authorized now: NONE.** Both prior Dhan manifests are spent.

## Source of the issue

The last guarded sample [Run 38043667443](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043667443) confirmed:
- profile HTTP 200, token valid and Data API plan active;
- `GET /v2/instrument/IDX_I` returned HTTP 302;
- no redirect was followed, no candle call was made;
- artifact ZIP SHA-256: `f388a9844db92836ec6551e2e442e207dc8d504bc9ae198df860117a2aabc68e`.

Independent artifact audit: `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_SAMPLE_AUDIT_2.md`, decision REQUEST CHANGES for data feasibility.

## Proposed exact scope

Read `research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md`.

- One GET to the same official `https://api.dhan.co/v2/instrument/IDX_I` endpoint.
- Do not follow the redirect.
- Report only HTTP status, safe content type and normalized redirect scheme/hostname. Never persist the raw Location string, path, query, fragment, userinfo or raw headers.
- 1 KiB response/body cap, 1 KiB global body budget, one request, 20-second timeout, no retry.
- No candle calls, no instrument-master download, no alternate endpoint and no history/model work.
- A later one-hop redirect policy must be separately reviewed after comparing the target against official Dhan documentation. This spec does not authorize a redirect follow.

## Tester checks

1. Verify that URL parsing only emits HTTPS scheme and normalized hostname and cannot leak query/path or credentials.
2. Verify the one-request/1 KiB cap and no-redirect transport remain in force.
3. Confirm no secret is emitted and error response bodies are discarded.
4. Confirm the previous manifests are SPENT and this specification does not authorize any live call.
5. Return PASS or REQUEST CHANGES.

**Tester → Developer:** Review the exact spec only; no network request is authorized at this gate.

**Developer → Tester:** If the spec passes, implement parser/tests and offline workflow only, then submit exact blobs for code review. A new one-run manifest is required before the single diagnostic call.
