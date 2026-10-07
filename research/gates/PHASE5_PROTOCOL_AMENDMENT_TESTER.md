# Phase 5 Protocol Amendment Tester Review — Intraday Refit Cadence

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer amendment commit: `670d2c532e9e2683ec55c2239456c1223c576cb9`

## Review scope

The developer clarified the already-registered walk-forward cadence before any accepted Family D empirical result. The amended rule is:

- refit every 20 trading sessions for both daily and intraday;
- evaluate intraday predictions only on the frozen hourly decision grid;
- the intraday fit cadence is session-based rather than every 20 hourly rows.

## Independent checks

1. This is a computational clarification, not a result-selected hyperparameter change.
2. It reduces an accidental implementation ambiguity that caused excessive repeated refits in the rejected run.
3. It is consistent with the pre-existing project convention that the intraday decision grid is for evaluation timing, while model fitting must preserve chronological session boundaries.
4. The amendment occurs before any Family D empirical metric has been accepted.
5. D13-D15 remain fixed to the frozen sequence definitions; the session-local window safeguard remains mandatory.
6. No cost, option-selection, or economic promotion criterion is changed.

## Disposition

**PASS — PROTOCOL AMENDMENT ONLY**

The developer may execute the corrected hosted Family D run. This does not constitute a Family D empirical gate pass.

## Tester instruction to developer

Execute the corrected hosted run with the session-based intraday cadence. Do not modify model definitions or select methods using observed results. Submit the immutable artifact for independent numerical and leakage review.

## Developer instruction to tester

When the corrected artifact is available, independently audit the chronology, D01-D15 schema, D07 calibration isolation, D13-D15 session boundaries, valid sample counts, probability metrics, and numerical consistency before issuing the empirical gate.
