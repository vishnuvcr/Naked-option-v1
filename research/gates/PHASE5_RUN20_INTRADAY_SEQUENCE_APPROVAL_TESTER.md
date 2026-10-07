# Phase 5 Run #20 Intraday Sequence Correction — Tester Approval

Date: 2026-10-07
Developer submission commit: 662ef2fb21d440892a8ae455fdf06bcb365fb5a9

## Decision
**APPROVED FOR FRESH HOSTED EMPIRICAL EXECUTION.**

Independent review confirms the correction addresses the run #20 defect without changing the registered model family or decision protocol.

## Checks passed
- Intraday D13-D15 representations are now constructed from the full 1-minute feature path before hourly row selection.
- The representation cache is mapped by exact decision_idx to the frozen hourly decision rows.
- sequence_features uses only the current row and preceding 19 rows within the same session.
- Session boundaries are enforced by group segmentation, so no window can cross a trading-session boundary.
- The protocol explicitly records the 1-minute representation path and hourly row alignment.
- Regression tests cover finite warm-up, session isolation, and invariance of an earlier representation to mutation of later rows.
- D07, labels, refit cadence, seed, model widths, and hourly decision grid are preserved.

## Conditions
- Run #20 remains non-evidence.
- A fresh full Family D hosted run is required.
- No metric may be accepted until the new immutable artifact is independently audited.
- If the new artifact again reports intraday D13-D15 n=0 or otherwise violates the amended protocol, the gate fails.

Developer → Tester: after the fresh run completes, independently audit the immutable artifact for non-zero D13-D15 intraday coverage, causality, denominator consistency, D07 calibration isolation, and schema integrity.

Tester → Developer: launch the fresh hosted Family D run on the approved commit; do not promote any metric until the tester completes the artifact gate.