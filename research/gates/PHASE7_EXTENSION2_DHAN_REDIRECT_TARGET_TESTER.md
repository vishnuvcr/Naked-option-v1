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


## Implementation/offline-code gate — 2026-10-10

**Current decision: PASS WITH SCOPED RESTRICTIONS — redirect-target parser and offline tests only.**  
**Reviewed developer commit:** `826287103a9961044d1434256354129c3934f821`.

Exact reviewed blobs:
- `research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md`: `7044afeb8ddc242059490686727a3fe354e87b6d`
- `scripts/dhan_market_data_recovery.py`: `2752b816cc6b04f63e0aaae6ccf60831a32979c1`
- `scripts/test_dhan_market_data_recovery.py`: `b0a9c2fc913c9a1d9a74be3feaff48b8495358c6`
- `.github/workflows/phase-07-dhan-market-data-tests.yml`: `b43ce4dadca4e5867173136531e71c63bb74e9a3`

Hosted offline [Run 38043938853](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043938853) passed **34/34 regressions**. New tests verify that the one-request diagnostic requires its own explicit authorization flag, emits only scheme/hostname, and rejects malformed/credential-bearing URLs. The offline workflow still has no source step and does not bind the secret.

This code gate does **not** authorize the diagnostic network call. A separate single-use manifest and a dedicated guarded workflow are still required. The diagnostic must make one request, not follow the redirect, and store no raw Location value. A future redirect-follow policy requires another proposal and gate.

**Tester → Developer:** Mirror this exact code-gate report. Build a dedicated one-request workflow and manifest validator for this diagnostic, then submit those exact workflow/validator blobs for another independent gate. Do not reuse either spent Dhan manifest.

**Developer → Tester:** Verify the dedicated workflow only exposes `DHAN_ACCESS_TOKEN` to the one probe step and spends a hash-bound manifest before the call. Audit the result artifact separately.
