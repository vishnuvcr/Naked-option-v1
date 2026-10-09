# Run #807 Follow-up — Historical Metric Mismatch Diagnostic Proposal

**Developer status: diagnosis incomplete; requesting tester review before code changes**

## Evidence
- Run #807 used Python 3.11.16 with OPENBLAS/OMP/MKL/NUMEXPR thread limits set to one. The historical aggregate mismatch persisted.
- The immutable Run #654 reference records P07 intraday H=60 chronological-block Brier:
  - block 33, n=119: 0.2482625195704263
  - block 55, n=120: 0.2516896166236784
- Run #807 reconstruction reports:
  - block 33: 0.24826251046324826
  - block 55: 0.2516896144464828
- Frozen tolerance remains absolute 1e-9. The discrepancy is real under the current contract; no source/reference/tolerance changes are proposed.

## Code-path observation
In `scripts/reconstruct_phase7_predictions.py`, `build_candidates()` computes candidate metrics, then the main loop calls `recursive_compare(expected, actual)` and exits immediately on mismatch. The call to `canonical_prediction_rows()` and Parquet write occurs only after the aggregate comparison passes. Consequently, the uploaded Run #807 artifact contains daily H=1/2/3/5/10 and intraday H=5/15/30 outputs, but no intraday H=60 per-row panel. The two failing aggregate metrics therefore cannot yet be decomposed into exact row-level prediction/label contributions from this artifact.

## Proposed diagnostic-only change
1. Keep the frozen Phase 7 source, Run #654 artifact, reference JSON, prediction method, labels, metric definitions, and tolerance unchanged.
2. For each reconstructed horizon, write the canonical per-row prediction panel and a sidecar diagnostic summary before evaluating the aggregate comparison, including the exact ordered block boundaries/masks, finite-row counts, labels, P07 probabilities after the existing clipping rule, squared-error terms, and per-block Brier calculated with the same frozen expression.
3. On mismatch, retain and upload those diagnostic files; continue to fail the gate. Do not permit downstream forecast-panel validation or empirical authorization.
4. Add regression tests asserting diagnostic files are emitted for a failing aggregate, values are derived from the exact prediction/label arrays, and failure still exits nonzero without changing TOL or the reference.
5. Have tester independently inspect the diff and tests before a fresh diagnostic-only hosted run.

## What this does and does not establish
This proposal does not claim the cause is solver/runtime nondeterminism. The diagnostic is intended to distinguish (a) changed per-row predictions/labels from (b) a difference in block membership, clipping, aggregation or reference construction. Any correction to scientific logic must be separately justified and tester-approved.

**Developer → Tester:** review this diagnostic-only proposal and reject any hidden tolerance, reference, model, or label changes.

**Tester → Developer:** approve only a diagnostic artifact run that remains non-empirical and fails closed on mismatch; audit the per-row decomposition before authorizing any scientific correction.
