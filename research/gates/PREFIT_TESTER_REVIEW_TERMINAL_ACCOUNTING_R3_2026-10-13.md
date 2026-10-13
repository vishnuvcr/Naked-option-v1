# Pre-fit tester review — terminal accounting gate (2026-10-13)

## Decision
**PASS for terminal accounting only. NOT APPROVED for empirical fitting.**

## Reviewed evidence
- Hardened hosted workflow: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38420286467
- Terminal-row artifact: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38420286467/artifacts/11825388381
- Source module: https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-developer/scripts/prediction_accounting_executor_r3.py
- Registry integrity gate: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38418296924

## Checks passed
1. 400 configuration shards and 40 compatibility shards are hash/byte checked during registry/executor processing.
2. 40,000 configurations × 8 frozen outer folds produced 320,000 unique terminal rows.
3. Every row passed preregistered mandatory-field checks.
4. Every row had a valid blocked terminal status and failure reason; blocked metrics were null.
5. No-fit and no-holdout flags were false for every row.
6. Preflight status, canonical CSV hash agreement, and provenance flags are checked before output.
7. Scoped F01 data blocks remained limited to the five exact label/fold cells; no horizon-wide propagation.
8. Run summary confirms 20,000 BLOCKED_DATA and 300,000 BLOCKED_GATE rows, with no market-data load, model fitting, or holdout access.

## Issues found and corrected
- Initial executor did not fail closed on preflight status/hash/provenance and used a fixed value for created_utc. Both issues were corrected and recorded in research/ERROR_LOG.md; hardened workflow passed afterward.

## Remaining blockers
- All methods remain without implementation/tester approval; zero methods are empirically eligible.
- The accounting executor intentionally contains no estimator and must not be treated as prediction evidence.
- Before any model fit, each method family needs its own implementation tests and explicit eligibility gate, plus training-only transforms/calibration, maturity/purge/embargo and leakage tests, complete result validation, and approved preregistered inference.

## Tester instruction to developer
Proceed only to method-family implementation and synthetic tests. Do not run empirical fitting, do not open the holdout, and do not mark a method eligible by editing registry flags. Return a new implementation bundle for review before any empirical run.


## Follow-up synthetic family review
- Logistic adapter/calibration synthetic workflow [38420549917](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38420549917) passed five logistic tests and four chronological calibration tests. See [family report](PREDICTION_LOGISTIC_FAMILY_SYNTHETIC_RESULT_R3_2026-10-13.md).
- Decision remains limited to synthetic contract validation. No empirical fitting is approved. The method-to-adapter parameter mapping, exact compatibility conditions and per-method authorization still need a dedicated gate.


## Probit adapter numerical review
- Reviewed the probit negative log-likelihood and gradient: the signed response formulation uses `-s * phi(s*eta) / Phi(s*eta)` for the linear-predictor derivative and adds the registered quadratic coefficient penalty to slope terms only. A central finite-difference test now checks the analytic gradient.
- Latest combined synthetic workflow [38421586248](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38421586248) passed 14 tests, including the new gradient test. Summary: [probability adapter report](PREDICTION_PROBABILITY_ADAPTERS_SYNTHETIC_RESULT_R3_2026-10-13.md).
- Tester decision: PASS for logistic/probit adapter mechanics on synthetic data only. NOT APPROVED for market-data fitting; remaining family coverage and method-to-parameter mapping must be implemented and reviewed first.


## Additional family review — classical estimators
- LDA/QDA, elastic-net logistic, random forest, Extra Trees, gradient boosting, and histogram gradient boosting adapters were reviewed against the registered parameter shapes in the configuration shards. The adapters validate inputs and emit bounded probabilities; tree models use fixed seeds and single-thread execution for deterministic synthetic checks.
- Latest family suite [38422568667](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38422568667) passed 26 synthetic tests. Report: [classical adapter result](PREDICTION_CLASSICAL_ADAPTERS_SYNTHETIC_RESULT_R3_2026-10-13.md).
- Tester decision: PASS for synthetic mechanics only. Native probability outputs from tree ensembles are not automatically considered calibrated; inner chronological OOF calibration remains mandatory where specified. No empirical fitting is approved.


## Margin/distance family review
- Initial margin gate [38423018566](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38423018566) caught two nearest-centroid API errors; corrections passed in [38423098453](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38423098453).
- A second mathematical review found that KNN posterior log-odds were not a class-conditional density ratio under class imbalance. The implementation now normalizes local weighted mass by each class's sample count; the imbalanced-class test and combined 33-test suite passed in [38423391714](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38423391714).
- Tester decision: PASS for synthetic score mechanics only. SVM, centroid and KNN raw scores must be calibrated only on inner chronological OOF predictions before evaluation. No empirical fitting approved.


## Additive spline family review
- Addeditive spline logistic uses a train-only standardization and quantile-knot spline transform followed by regularized logistic regression. Synthetic tests passed for knot-count presets, probability bounds, train-only fitting and invalid support.
- Expanded combined workflow [38423891261](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38423891261) passed 36 synthetic tests across the current estimator set. See [family gate report](PREDICTION_FAMILY_SYNTHETIC_GATE_R3_2026-10-13.md).
- Tester decision remains PASS for synthetic implementation mechanics only. The HMM, Markov-switching, Bayesian dynamic, change-point, temporal convolutional network and survival-first-passage families remain unresolved; no empirical fitting approval.
