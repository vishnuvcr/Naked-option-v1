# Phase 8 Run #807 — Diagnostic Implementation Code Review

**Decision: PASS WITH SCOPED RESTRICTIONS — one hosted diagnostic-only run authorized**

Reviewed developer head `967f612b2ffa94007c1164d0f5fd4f051852bf34`, including:
- `scripts/reconstruct_phase7_predictions.py`
- `scripts/test_phase8_reconstruction.py`

## Review findings
- The mismatch diagnostic derives row-level P07 predictions, labels, clipping and squared errors from the existing `built` arrays.
- Block membership comes from the frozen Phase 7 `blocks_for` implementation.
- The frozen Run #654 reference, source hash, scientific method, metric expression, and 1e-9 tolerance remain unchanged.
- Canonical row panels are now written before the aggregate failure exit; the diagnostic sidecar is emitted for blocks named by the aggregate mismatch.
- The normal failure path remains fail-closed: any aggregate mismatch sets status to FAIL and raises `SystemExit`; forecast-panel validation and empirical jobs depend on successful reconstruction and are not authorized by this review.
- Regression coverage checks diagnostic row terms and ordering of panel emission before the fail-closed exit.

## Scope and limitations
This is a code-scope approval, not evidence that the new regression tests have passed in a hosted run and not acceptance of Run #807's metrics. Only one fresh hosted diagnostic-only reconstruction run is authorized. Empirical authorization input must remain false. If the diagnostic shows a block-membership/indexing discrepancy or a new defect, do not patch the science ad hoc; report it for review.

**Tester → Developer:** run the gated workflow with empirical authorization disabled, then submit the immutable artifact and exact row-level decomposition for independent audit.

**Developer → Tester:** audit that the diagnostic block indices, row counts, timestamps, labels, clipped P07 probabilities and squared-error mean reproduce the reported aggregate; no empirical grid until a separate tester decision.
