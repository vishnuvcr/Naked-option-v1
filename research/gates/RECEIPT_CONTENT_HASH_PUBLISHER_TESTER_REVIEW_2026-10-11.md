# Independent tester review — compressed vs uncompressed content identity

Date: 2026-10-11
PR: [#17 — Verify uncompressed CSV identity in preflight receipts](https://github.com/vishnuvcr/Naked-option-v1/pull/17)
Reviewed feature head after redundant workflow removal: 210cff0072c384ce417ee942ceb457ab0d171773.
Independent hosted regression run: [Phase 07 Offline Dataset Preflight Tests #38145457955](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38145457955) — success, **48 tests passed**. This run exercised the same publisher and receipt-test file blobs as PR #17; publisher script blob 487d5383c75a6d2316a2ff36273c0904ab599e74, test blob 1742cf0f696aa700016d0a958c7fde5c92f22bc3.

## Decision
**PASS WITH SCOPED RESTRICTIONS** for the receipt publisher's content-identity schema correction.

## Independent checks
- Compressed-container SHA and uncompressed-content SHA/byte count are represented separately; receipt acceptance requires the uncompressed SHA and expected byte count to match.
- A gzip hash mismatch with matching uncompressed content gets the explicit status REPORT_PRESENT_PASS_CONTENT_HASH_VERIFIED, rather than silently being treated as the old compressed hash match.
- Uncompressed SHA/size mismatches cannot receive a pass receipt.
- Row-width, row-count, content-hash and content-size failure statuses are allowed only as non-pass receipts.
- Required hash fields are format-checked; content identity booleans and byte counts are type-checked; unapproved report keys remain rejected.
- Synthetic coverage passed for compressed hash variance with matching content, content mismatch, missing identity fields, structural failure statuses, unexpected raw fields and workflow least-privilege/action pinning policy.
- The redundant standalone test workflow was removed from PR #17; tests are run through the already-working phase-07-developer offline synthetic CI workflow instead.
- No real market data, model outputs, holdout or trading P&L are involved in this PR.

## Scope and remaining gate
This review approves only the sanitized receipt schema/publisher change. It does not approve the actual dataset or open modelling. The real-file audit still requires its own fresh exact-file decision and single-use execution request. Its report and cleanup evidence require a separate data-readiness review.

**Tester → Developer:** Merge PR #17, verify the resulting main-branch publisher tests and pin its final content hash before requesting R4. Do not claim data readiness from synthetic tests.
**Developer → Tester:** Review the R4 real-file report, raw content hash/byte count, row/key metrics and cleanup evidence before opening prediction experiments.
