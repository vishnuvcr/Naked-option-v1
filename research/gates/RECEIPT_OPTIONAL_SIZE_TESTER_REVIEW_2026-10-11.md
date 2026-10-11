# Independent tester review — optional raw byte-count reference

Date: 2026-10-11
PR: [#19 — Allow content-hash validation without unverified raw byte count](https://github.com/vishnuvcr/Naked-option-v1/pull/19)
Reviewed publisher blob: `3f72a86f4261180cb578c84c1058e6ca5d963a66`.
Reviewed regression test blob: `8d972ac0478de1b393d6e5bbeb9e2f19c51832bc`.
Hosted developer CI: [run 38145624981](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38145624981) — success, 48 tests passed, including the publisher’s unknown-reference-byte-count case and the core preflight hash/schema tests.

## Decision
**PASS WITH SCOPED RESTRICTIONS** for allowing an unspecified expected uncompressed byte count when the full uncompressed content hash is pinned and verified.

## Findings
- The audit manifest provides the expected uncompressed SHA-256 but does not provide a separately grounded reference uncompressed byte count. The earlier `4,747,892,392` value was not traceable to an authoritative reference and is removed from the gate; it must not be treated as fact.
- The scanner still hashes the entire decompressed CSV byte stream and compares it to the pinned SHA-256 `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204` before reporting structural status.
- The `expected_uncompressed_size_bytes` and `uncompressed_size_matches_expected` fields can both be `null` when there is no independent byte-count reference. The receipt validator accepts that only when the uncompressed SHA check is explicitly `true`.
- If an expected size is supplied, it must be a non-negative integer and the match flag must be boolean. A size mismatch cannot receive a pass receipt.
- Compressed container SHA is retained as metadata and may differ after recompression; the raw-content SHA remains the actual content identity gate.
- Hosted regression test run 38145624981 passed 48 tests against these exact publisher/test blobs. No real-file or trading tests were executed by this review.

## Scope
This approves only the receipt publisher schema/validation correction. It does not authorize another real-file audit by itself and does not confer model, holdout, strategy, or P&L permissions.

**Tester → Developer:** Merge PR #19 and verify the final `main` publisher hash before incorporating that publisher into the R4 reviewed file snapshot.
**Developer → Tester:** Keep R4 and downstream experiments closed until the exact snapshot is reviewed, the raw-content hash is checked, and the actual structural report receives separate approval.
