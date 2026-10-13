# Prediction family synthetic gate — 2026-10-13

Status: PASS_SYNTHETIC_ONLY.

Latest workflow: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38423891261

The combined workflow passed 36 synthetic tests across logistic regression, chronological probability/score calibration, probit, LDA, QDA, elastic-net logistic, random forest, Extra Trees, gradient boosting, histogram gradient boosting, kernel SVM raw scores, nearest-centroid distance scores, KNN class-conditional density-ratio scores, and additive spline logistic regression.

The suite includes a finite-difference check for the probit likelihood gradient, an imbalanced-class check for KNN density-ratio direction, deterministic-tree checks, train-only preprocessing checks, and fail-closed tests for invalid support/parameters/nonfinite inputs. SVM and distance-based raw scores require chronological inner-OOF calibration before evaluation.

No market data was loaded and no holdout was accessed. These are synthetic implementation checks only, not prediction results or fitting authorization. Complex state-space and temporal families remain to be implemented/tested; method-level eligibility remains zero.
