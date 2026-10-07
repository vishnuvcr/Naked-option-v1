# Phase 5 Family D — Run #16 Independent Tester Pre-Check

Date: 2026-10-07
Tester branch: phase-05-tester
Developer run under review: 37606785909
Developer head under review: 3bb5fe0c17c1dce92624059a40b9e140d2c2814f

## Scope

This is a pre-artifact tester review. It is not a Family D empirical gate pass.

The hosted run has completed the mandatory regression, cache-restore and acquisition steps and is still executing the empirical D01-D15 suite. The immutable result artifact is not yet available, so no metric is accepted.

## Independent checks completed before artifact review

- The current developer workflow is the tester-approved Phase 5 workflow with a manual dispatch path and cached research-data restoration.
- The exact D13-D15 row-aligned causal sequence-cache correction is the previously approved computational optimization.
- Intraday refitting is session-based at 20 trading sessions while predictions remain on the frozen hourly decision grid.
- Regression controls cover chronological purge, training-only scaling, deterministic sequence construction, session-boundary protection and probability bounds.

## Blocking protocol/code discrepancy identified

The frozen Phase 5 protocol states:

“D07 Calibrated stacking: probability averaging of D01-D06, calibration fit only inside training blocks.”

The current developer implementation in scripts/run_phase5_family_d.py instead constructs a logistic meta-model over D01-D06 probability predictions after a chronological calibration split, then refits the base models on the full training window before test prediction.

A logistic meta-stack is consistent with the broad METHOD_REGISTRY label “D07 calibrated stacking”, but it is not the same operation as simple probability averaging. The distinction must not be silently ignored after a hosted run has started.

## Tester disposition

**BLOCKED — NO EMPIRICAL METRIC MAY BE ACCEPTED FROM RUN #16 UNTIL THIS PROTOCOL/IMPLEMENTATION MISMATCH IS RESOLVED THROUGH THE DEVELOPER → TESTER AMENDMENT GATE.**

Run #16 should remain preserved as non-accepted execution evidence. If it completes, its artifact may be inspected for secondary regression diagnosis, but it must not be used for model selection or promotion.

## Required developer response

1. Preserve run #16 and its artifact if produced.
2. Add a formal protocol amendment that explicitly defines D07 as the intended frozen operation.
3. Do not use any run #16 metric to choose the amendment.
4. Submit the amended definition and regression coverage to the tester for approval.
5. Execute a fresh hosted Family D run after tester approval.
6. Re-run the full independent numerical/schema/leakage audit on the fresh immutable artifact.

## Developer instruction to tester

After the developer submits the protocol amendment, independently verify that the amendment is a definition clarification rather than a result-driven change, that regression tests pin the D07 formula, and that no other Family D definition has changed.
