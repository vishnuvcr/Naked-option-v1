# Independent Tester Re-review — Dhan Historical Pipeline Code Gate

**Decision: REQUEST CHANGES — one remaining cache-provenance guard; no live request authorized.**

**Reviewed developer code snapshot:** 85ebfef015f2188c983d3977ad6fb3b4e11dc29e  
**Current developer branch head after documentation/log updates:** 7bb4f4b90ba32dff73e1ad3090357897f6b4b166  
**Hosted offline regression:** [Run 38050016413](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050016413), success, 41 tests.  
**Protocol check:** [Run 38050016603](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050016603), success.

Reviewed blobs:
- pipeline: af560a7e1208d67fc7eb6275639ada701907c752
- tests: cf31bfa5538d449ee57abece6a68e959e22c7892
- offline workflow: dc0de4688bfac5ee932c32ccd25fdd586effd3c2

## Findings 1–5 from the prior REQUEST CHANGES report

The reviewed correction resolves these findings:

1. Daily and rolling-option end dates now use documented non-inclusive toDate semantics for caps and cache timestamp bounds. Exact 30-/365-day exclusive windows and the excluded end date have regression tests.
2. The sample request and total response-byte ceilings cannot be widened through RequestBudget constructor values or mutation without rejection before opener creation.
3. Recognized optional numeric arrays, including daily open_interest, now receive finite/non-negative and type validation.
4. Empty unrequested rolling-option IV/OI/strike/spot arrays are accepted in the documented shape; requested fields still must align, and populated optional fields are checked.
5. The initial rolling-option scope accepts ATM only; unsupported offset strings cannot be accidentally submitted.

The 41-test hosted run passes and the current offline workflow has read-only contents permission, no Dhan secret environment and no live-network step.

## Finding 6 — cache writer does not independently validate HTTP success and response content type

In atomic_cache_bundle, the writer validates JSON structure, schema, exact body bytes/hash/length and request-window provenance, but it does not require request_metadata to show an HTTP 200 response and a JSON content type. It also does not enforce that request metadata includes a request count within the sample budget.

request_json currently rejects non-2xx responses and non-JSON content types before returning data, so the intended call sequence protects this path when used correctly. However, atomic_cache_bundle is a separate public helper and currently can accept matching bytes/schema supplied with missing or incorrect HTTP status/content-type metadata. The cache boundary should be fail-closed itself, not depend solely on the upstream caller having used the request helper properly.

**Required correction:** before any cache write, require:
- request_metadata is a dict with http_status exactly 200;
- content_type normalizes to application/json (allow a normal JSON charset parameter if present);
- request_count is exactly 1 for this sample-gate adapter;
- response_sha256 and response_bytes match the raw payload (already implemented);
- cumulative_response_bytes equals the observed bytes for this one-request scope and does not exceed MAX_TOTAL_BYTES.

Add tests for missing status, non-200 status, HTML/wrong content type, absent/mismatched request count, and cumulative bytes mismatch. All failures must leave the cache root without a new bundle.

## Decision

The code is **not yet approved** for a live request. Findings 1–5 are resolved; finding 6 must be corrected and hosted-tested before the final independent code gate.

**Tester → Developer:** Add the cache-provenance checks above and their offline regressions, update the error log and exact code handoff, and request one final review. Keep the workflow offline-only; do not create/spend a live manifest or call Dhan.

**Developer → Tester:** Independently check the new metadata gate and failure-atomicity tests against the exact new blobs/run. If the checks pass, issue code-only PASS with restrictions. No actual request is authorized by that report.
