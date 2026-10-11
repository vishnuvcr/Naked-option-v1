# Tester Recheck — Phase 8 Cached Composite Metadata Preflight Implementation R1

**Decision: PASS WITH SCOPED RESTRICTIONS — one metadata-only cached-composite preflight**  
Review snapshot: `7fb30a0a04eeba5aa65485e974ca35091fe035b6`  
Contract/regression workflow: [38161662282](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38161662282) — contract-tests job PASS; exact authorization gate is re-evaluating against the revised activation snapshot.

## Why this recheck was necessary

The first implementation review authorized an exact code snapshot whose synthetic workflow test expected `requested=false`. Once the tester had approved the one-use preflight, the developer correctly activated the request with `requested=true` and exact pins, but that fixture still assumed a disabled request in the checked-in file. Run [38161622139](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38161622139) failed at that contract assertion before any dataset artifact was downloaded. The test has now been corrected to allow either activation state while requiring the exact 15-file reviewed hash set when enabled and all trade/holdout/new-source/promotion flags false. Its synthetic fixture still confirms the default-disabled behavior independently.

The prior decision is archived as `PHASE8_CACHED_COMPOSITE_PREFLIGHT_IMPLEMENTATION_TESTER_DECISION_R1_PRE_ACTIVATION.json`. This recheck supersedes its blob snapshot; the research/data scope does not expand.

## Exact-snapshot review

Fifteen code/workflow/manifest/spec blobs were recomputed and are pinned in the companion decision JSON. The only production-logic check added in this recheck was stricter validation of request identity/flags; the other code files remain the same reviewed blobs. The required pins include the one-use workflow, no-refit runner, P05/P06/P10-aware option execution engine, cost regression tests, original encrypt/decrypt implementation, encrypted-part validator, authorization logic and synthetic tests, exact 61-part source manifest, Run #994 R2 forecast manifest, Phase 8 frozen method specification, Paytm Money/statutory cost schedule, and cryptography requirement.

The current contract run includes and passed:
- synthetic encrypted bundle validation (exact part set/bytes/digests, unsafe name and modified-ciphertext rejection);
- exact-snapshot authorization unit tests (stale blob and changed source/forecast identity fail closed);
- workflow structural tests for marker-before-decryption, push of durable marker, no marker-trigger loop, job-scoped write permission, metadata-only output and unconditional cleanup;
- 4,800-configuration contract test and existing fee/cost engine arithmetic tests;
- no-refit runner self-test;
- pinned static manifest and R2 forecast manifest git blob checks.

## Safety and arithmetic review

- The one-use marker step occurs after only encrypted-bundle hash metadata checks and accepted forecast archive/manifest/aggregate hashes, and before decrypting monthly parts or parsing the 9m-row CSV. Marker JSON is newline-terminated and remains durable on the developer branch.
- Revalidation is done against the latest developer branch and exact tester decision immediately before marker creation. If code pins are stale, request/source/forecast hashes differ, the reviewer decision is absent, marker already exists, or push races, execution must fail closed before plaintext open.
- The request can enable only `metadata-only cached composite preflight`; the authorizer hard-pins source and forecast identities and rejects any true value among empirical P&L, holdout, new-market-source requests and strategy-promotion flags.
- The workflow runs the runner strictly with `--mode preflight`, validates exact canonical decoded CSV SHA-256, 8,999,865 rows / 47 columns / OPTION-SPOT counts, checks all 4,800 configs remain `INELIGIBLE`, uploads metadata only and verifies temporary-data cleanup. It does not use a public/provider market-data endpoint.
- Top-level token permissions remain read-only. `contents: write` is scoped only to the actual preflight job for the required durable marker.
- If anything fails after marker commitment, R1 is consumed. Do not rerun R1: create a new request version and review if a second attempt is needed.
- This is still a data-readiness gate only. No actual option P&L, holdout use or strategy promotion is authorized. OHLC/Q1 is not quote-executable because strict historical bid/ask and point-in-time contract identity are not proven.

Reviewer caveat: branch-separated reviewer role is not a separate external human/model instance.

**Tester → Developer:** Sync the request's `approved_code_blob_shas` to the exact pins in the decision file without editing any reviewed code. Let the fresh authorization run pass before the one-use job opens the cached composite.

**Developer → Tester:** Report the immutable run ID, consumed-marker commit, canonical CSV digest/counts, four-thousand-eight-hundred-cell eligibility matrix digest, metadata artifact digest, and cleanup outcome. Do not call the result a strategy or P&L.
