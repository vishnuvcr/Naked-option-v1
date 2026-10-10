# Independent Tester Report — Dhan Redirect-Target Discovery Specification

**Current decision: PASS WITH SCOPED RESTRICTIONS — specification only.**  
**Reviewed spec commit:** `aecd39a35ef411a15ba7ad3bc2d30164bb5b9677`.  
**Live request authorized: NONE.** Both prior Dhan manifests are SPENT.

## Review

Reviewed `research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md` and request `research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_REVIEW_REQUEST.md`.

The proposal is finite and safely constrained:
- one GET to the already-used documented Dhan `/v2/instrument/IDX_I` endpoint;
- no redirect follow;
- only normalized scheme and hostname may be reported from Location; path, query, fragment, userinfo and raw headers are prohibited;
- 1 KiB response/body budget, one request, 20-second timeout, no retry;
- no candle/history calls or alternate endpoints;
- any redirect follow would need another separate review and allowlist decision.

This is consistent with the failed bounded artifact: HTTP 302 was observed, but the destination was not retained. A hostname-only diagnostic is a reasonable minimal next step; it does not presume that the redirect target is safe or official.

## Conditions for implementation/code gate

1. Parse Location with a standard URL parser; reject missing/malformed values.
2. Require HTTPS; normalize hostname to lowercase/IDNA and validate its length.
3. Never store raw Location or path/query/userinfo, and never forward the access token to the redirect target.
4. Preserve only numeric HTTP status, safe content-type, redirect scheme/hostname, request count and bytes read.
5. Add offline tests for missing/malformed/non-HTTPS Location, hostname normalization, and sensitive URL components not appearing in serialized output.
6. Keep live calls blocked until a new exact-snapshot code gate and single-use manifest validate.

## Decision

**PASS WITH SCOPED RESTRICTIONS — specification only.** This does not authorize the diagnostic request itself, following a redirect, candle data acquisition, full-history download, features/labels, model fitting, metrics or holdout access.

**Tester → Developer:** Implement redirect-host parsing and offline tests only, then submit exact source/test/workflow blobs for a code gate.

**Developer → Tester:** Do not create a live manifest until the code gate passes. The diagnostic artifact must be independently audited; a later redirect follow requires a new proposal.
