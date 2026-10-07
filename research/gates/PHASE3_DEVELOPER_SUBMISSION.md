# Phase 3 Developer Submission

## Scope

Freeze label definitions, baseline models and option break-even rules before any large-scale predictive model search.

## Gate history

- Phase 3 protocol gate: PASS on phase-03-tester.
- Phase 3 implementation review: PASS FOR EMPIRICAL EXECUTION after B7/B6/B8 corrections.
- Phase 3 data-execution review: REQUEST CHANGES. The first empirical package did not yet run the baseline suite from the workflow and contained implementation/PIT-validation mismatches.

## Corrected package

- Restored the complete research log and preserved all prior errors.
- Wired the automatic/manual workflow through intraday sample acquisition, baseline execution, result-schema validation, persistence and artifact upload.
- Added explicit B0-B11 result dispositions and exact horizon-set validation.
- Corrected intraday B3 to previous-session close and B4 to the frozen min(H,30) momentum rule.
- Aligned B11 to the frozen core feature contract; optional contextual features remain disabled unless PIT-safe historical layers are available.
- Added official-NSE overlap checks for the selected intraday research-reference dataset.
- Added calibration, confusion-matrix and block-bootstrap diagnostics.

## Current gate state

Phase 3 remains **OPEN / NOT PASSED**. A fresh hosted run and independent tester reproduction are mandatory before any Phase 4 method search.

## Developer instruction to tester

Independently review the fresh hosted Phase 3 artifact set. Verify protocol CI, exact horizon coverage, label timing, B0-B11 dispositions, B3/B4/B7 semantics, B11 feature lineage, intraday official-NSE overlap, block-bootstrap calculations, source/PIT restrictions and absence of look-ahead. Reproduce the reported metrics from the immutable artifact data before issuing PASS or REQUEST CHANGES.