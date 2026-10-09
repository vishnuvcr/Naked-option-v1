## Phase 8 panel-consumer proposal

**Status: SUBMITTED FOR TESTER REVIEW**

### Problem
Phase 8 attempts to re-fit the Phase 7 models in a later GitHub runner and compare floating-point aggregates with the immutable Run #654 result. The immutable Run #654 artifact has only aggregate JSON, not row-level predictions. Repeated replay attempts fail two P07 intraday H=60 block-Brier values by more than the frozen 1e-9 tolerance. Python/package pinning and single-thread controls did not resolve the mismatch; root cause remains unproven.

### Proposed resolution
After a new same-run Phase 7 reference artifact containing all 10 prediction panels and its aggregate JSON is independently accepted, amend the Phase 8 frozen-input manifest through a separate tester-approved gate. Preserve Run #654 and its manifest history unchanged.

The Phase 8 reconstruction path should then:
1. Verify the new artifact ID, archive SHA-256, manifest schema, run ID/commit, and aggregate JSON hash.
2. Verify exactly 10 panels cover daily horizons 1/2/3/5/10 and intraday horizons 5/15/30/60/120; each panel has all P01-P10 columns and unique row keys.
3. Verify per-panel SHA-256, stable row index, monotonic timestamps, label/future-return consistency, no missing block assignments, and complete source/code/runtime fingerprint.
4. Load the saved prediction arrays rather than refit the Phase 7 component models.
5. Recompute all registered method metrics and family tests from the saved arrays under the frozen Phase 7 metric code; compare with the paired aggregate JSON using the existing absolute tolerance 1e-9. Preserve the historical panel/aggregate pair as the immutable reference.
6. Only after a separate tester artifact audit, update the Phase 8 manifest to the new artifact ID/hash. No 4,800-cell option grid or option P&L is authorized by this proposal.

### Acceptance criteria
- Existing Run #654 artifact and result JSON are untouched.
- New panel and aggregate JSON are produced in the same Phase 7 execution and hash-linked in one manifest.
- All ten panels, labels, timestamps, block assignments, hashes and aggregate diagnostics reconcile.
- Phase 8 never silently falls back to re-fitting models when the panel artifact is absent or invalid; it fails closed.
- The 1e-9 tolerance and all frozen scientific definitions remain unchanged.
- Independent tester approves the manifest amendment and the consumer code before any empirical option execution.

### Restrictions
This proposal does not itself authorize a manifest change, Phase 8 panel consumption, strategy promotion, or empirical option-grid execution. Separate code and artifact gates are mandatory.