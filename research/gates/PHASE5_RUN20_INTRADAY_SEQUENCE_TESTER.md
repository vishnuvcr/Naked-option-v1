# Phase 5 Family D Run #20 — Independent Tester Gate

Date: 2026-10-07
Run: 37626101730
Artifact: phase5-family-d-results (artifact 11492105041)
Head: 67b0fc4aa7e5e23d973cc8bfdb2b632abb049245

## Decision
**REQUEST CHANGES — Family D is NOT accepted and Phase 6 remains blocked.**

The hosted workflow completed successfully, including regression, empirical execution, schema validation, and artifact upload. However, the immutable artifact exposes a substantive implementation/data-coverage defect in the intraday D13–D15 sequence methods.

## Independent finding
The intraday protocol requires hourly-grid evaluation while preserving session-local sequence windows. The production code constructs the D13–D15 sequence representation cache from the already downsampled hourly decision matrix. The frozen sequence window is 20 observations. A normal trading session has only about 7 hourly decision-grid observations. Therefore a 20-observation session-local sequence window cannot exist within a single session on that hourly matrix.

The artifact confirms the consequence: for every intraday horizon (5/15/30/60/120 minutes), D13, D14 and D15 are labelled EXECUTED but have n=0 and ROC-AUC=None. This is not a valid completed empirical evaluation.

This also conflicts with the protocol requirement to persist BLOCKED_DATA when a required input is unavailable. An empty sequence output must not be silently represented as EXECUTED.

## Required developer correction
1. Build causal D13–D15 sequence representations from the full 1-minute intraday feature path (or another explicitly frozen pre-decision observation path that genuinely supplies 20 observations per session).
2. Row-align/map the resulting causal representations exactly to the frozen hourly decision timestamps used for model fitting/prediction.
3. Enforce session boundaries; no sequence may cross a trading-session boundary.
4. Preserve the 20-observation window, D13/D14/D15 architectures, deterministic seed, hourly decision grid, session-based 20-session refit cadence, and exact H-minute labels.
5. Ensure each representation uses only observations at or before the decision time; no future rows.
6. Add regression tests proving intraday D13–D15 produce finite predictions on a synthetic session with sufficient 1-minute warm-up and that mapped hourly rows are causal and session-local.
7. If insufficient source observations genuinely exist, return BLOCKED_DATA rather than EXECUTED with n=0.
8. Rerun the full hosted Family D workflow after tester approval. Run #20 remains non-accepted evidence.

## Other checks
- Workflow completed successfully.
- Regression suite passed.
- Schema validation passed.
- Artifact exists and is immutable for this run.
- Daily D01–D15 sequence methods have non-zero evaluation counts.
- D07 remains subject to the previously approved calibrated-meta-stack definition.
- No option-economic or strategy-promotion conclusion is permitted from this run.

## Gate status
**BLOCKED / REQUEST CHANGES.**

Developer must submit the exact implementation/protocol amendment and updated regression tests to the tester before another accepted empirical run.

Developer → Tester: correct the intraday D13–D15 sequence construction as specified above, add causal/session-boundary regression coverage, and submit the changed files for independent review before rerunning Family D.

Tester → Developer: after submission, independently verify causality, session-locality, 20-observation warm-up, hourly row alignment, D07 preservation, and absence of future-label leakage; do not approve the next run until these checks pass.