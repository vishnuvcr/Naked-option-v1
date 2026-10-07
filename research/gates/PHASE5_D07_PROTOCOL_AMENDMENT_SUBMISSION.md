# Phase 5 D07 Protocol Amendment Proposal

Date: 2026-10-07
Developer branch: phase-05-developer
Developer run: 37606785909
Developer head under review: 3bb5fe0c17c1dce92624059a40b9e140d2c2814f

## Reason for amendment

The independent tester pre-check identified a mismatch between the frozen Phase 5 protocol wording and the implementation.

Current protocol wording describes D07 as “probability averaging of D01-D06”. The registered method family and current implementation both describe D07 as calibrated stacking. The implementation uses a chronological calibration split, fits D01-D06 only on the earlier training portion, trains a logistic meta-model on the calibration probabilities, refits D01-D06 on the full training window, and applies the frozen meta-model to the refitted base probabilities.

## Proposed clarification

Define D07 explicitly as:

**Calibrated logistic meta-stacking of D01-D06.** For each chronological training block, split the eligible training observations chronologically into base-training and calibration subsets; fit D01-D06 on base-training; obtain calibration probabilities on the held-out calibration subset; fit a logistic meta-model on those probabilities and calibration labels; then refit D01-D06 on the complete eligible training block and pass their test probabilities through the frozen logistic meta-model. No calibration or base-model fit may consume post-cutoff labels.

This is a definition clarification of the already-registered “calibrated stacking” method, not a result-selected hyperparameter change. No method, feature, horizon, refit cadence, cost assumption or promotion rule is changed.

## Regression pin requested by tester

Add a deterministic synthetic test that reconstructs the D07 training-only stack from the same base-model outputs and confirms the production D07 probability vector matches the independently reconstructed logistic meta-stack within numerical tolerance. Also retain explicit checks that changing post-cutoff labels cannot alter the produced test probabilities.

## Run #16 evidence rule

Run #16 remains preserved but is not scientific evidence because the frozen protocol wording was not fully aligned with the implementation at execution time. No Run #16 metric may be used to choose or tune the amendment.

## Gate request

Independent tester review is required before the main protocol or regression code is amended and before a fresh hosted Family D run is accepted.
