# Independent Tester Review — Phase 8P Greek Prediction Scope R2
Date: 2026-10-12
Reviewed developer branch: phase-08-prediction-developer
Reviewed scope file SHA-1: 2ed56b49d87f50f903f2ad772476184929bdedb6

## Decision
**REQUEST CHANGES — SCOPE NOT YET APPROVED.** No data artifact was decrypted, no model fitted and no empirical metric produced.

## Review summary
The R2 revision closes most R1 issues: exact Greek timestamp semantics, signed Delta formula, side-specific minimum coverage, ratio denominator treatment, same-row comparisons, holdout/schema preflight and fail-closed behavior are now explicit. The use of an immutable partial-grid artifact and the non-commercial restriction are preserved. The model-comparison scope remains prediction-only.

## Remaining required corrections
1. **Model specification still has avoidable degrees of freedom.** “Deterministic solver” and “maximum iterations high enough” are not exact settings. Freeze a named logistic solver, preprocessing pipeline and max_iter; fix the boosting random seed and all other available stochastic settings. Do not silently change solver or iteration count when a fit fails.
2. **The primary inferential p-value is under-specified.** Define the signed paired per-row loss differential d_i = Brier_i(spot-only) − Brier_i(spot+Greek), the null H0: mean(d) <= 0, the null-centered moving-block resampling rule, the one-sided p-value calculation and handling of failed/non-finite resamples. Keep the 500 resamples as fixed, and explain that this makes p-value resolution coarse; a PASS must not equate to proof of practical value. Then apply Holm to the 20 prespecified tests.
3. **Bootstrap unit must be established by the schema-only stage.** Phase 7's “60 intraday decision observations” cannot be applied if the current panel grid or ordering differs. State the required ordering/session checks and make the inference gate BLOCKED unless the panel matches the registered unit exactly.

## What can proceed after correction
A versioned R3 scope may receive a scope-only approval after the above items are fixed. This review does not authorize data access, fitting, holdout access, external requests, option economics or strategy promotion. Separate code and preflight gates remain mandatory.

**Tester → Developer:** freeze exact estimator settings and null-centered one-sided block-bootstrap inference; preserve R2 as history and resubmit a complete R3 scope.
**Developer → Tester:** provide the R3 file and blob SHA; request a scope-only review, not empirical authorization.
