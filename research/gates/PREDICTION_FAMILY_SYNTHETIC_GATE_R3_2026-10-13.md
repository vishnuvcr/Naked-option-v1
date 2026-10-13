# Prediction family synthetic gate — 2026-10-13

Status: PASS_SYNTHETIC_ONLY.

Latest workflow: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38424574167

Prior MLP implementation run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38424265378

The combined workflow passed 40 synthetic tests across logistic regression, chronological probability/score calibration, probit, LDA, QDA, elastic-net logistic, random forest, Extra Trees, gradient boosting, histogram gradient boosting, kernel SVM raw scores, nearest-centroid distance scores, KNN class-conditional density-ratio scores, additive spline logistic regression, and a deterministic shallow MLP with dropout and weight decay.

The suite includes a finite-difference check for the probit likelihood gradient, an imbalanced-class check for KNN density-ratio direction, deterministic-tree and MLP checks, a finite-difference check of MLP backpropagation, train-only preprocessing checks, and fail-closed tests for invalid support/parameters/nonfinite inputs. SVM and distance-based raw scores require chronological inner-OOF calibration before evaluation.

No market data was loaded and no holdout was accessed. These are synthetic implementation checks only, not prediction results or fitting authorization. Complex state-space families (HMM, Markov-switching logit, Bayesian dynamic logit, change-point, and temporal convolution) remain to be implemented/tested; method-level eligibility remains zero.
