# R2 Compatibility Matrix — row-level conservative audit

**Status: DRAFT / BLOCKED. This document does not authorize empirical fitting.**

- Source shard index SHA-256: `84af57bfc156d70fc4471f6daa21d7d222a7e093ae5d711e3fdaaaeed3b30661`
- Row-level records: 1000
- Compatibility-level allow-in-principle (conditional on adapter implementation/tests): 426
- Blocked by current compatibility/design deficiencies: 574
- Authorized for empirical fitting: **0**
- Unique semantic fingerprints: 1000 / 1000
- Duplicate semantic fingerprints: 0
- Duplicate family × representation × operator triples: 0

## Compatibility decision counts

- ALLOW_IN_PRINCIPLE: 426
- BLOCK: 574

## Operator counts

- conformal_set_decision: 200
- cost_sensitive_threshold: 200
- probability_threshold: 200
- regime_gated_decision: 200
- uncertainty_abstention: 200

## Family counts

- bayesian_dynamic_logit: 50
- change_point_segment_model: 50
- elastic_net_logistic: 50
- extra_trees: 50
- generalized_additive_model: 50
- gradient_boosting: 50
- hidden_markov_model: 50
- histogram_gradient_boosting: 50
- kernel_svm: 50
- knn_density_ratio: 50
- lda: 50
- logistic_regression: 50
- markov_switching_logit: 50
- nearest_centroid: 50
- probit_regression: 50
- qda: 50
- random_forest: 50
- shallow_mlp: 50
- survival_first_passage: 50
- temporal_convolution_network: 50

## Operator rules
- `probability_threshold`: allow in principle only when family-specific directional probability semantics are explicit; test calibration in inner chronological folds.
- `uncertainty_abstention`: predictive Bernoulli entropy, cut at inner-training 80th percentile to target 80% coverage; report selective log loss and coverage.
- `regime_gated_decision`: allow in principle only with a causal filtered regime/segment posterior or the explicit entropy-regime representation; no smoothed/future-informed state.
- `cost_sensitive_threshold`: blocked because no non-arbitrary asymmetric class-loss matrix is preregistered for this prediction-only phase.
- `conformal_set_decision`: blocked until chronological/conformal validity assumptions, calibration split, target coverage and coverage tests are frozen.
- `survival_first_passage`: all methods blocked until the fixed-horizon directional classification target is reconciled with event time, competing-risk incidence, censoring and no-event probability.

## Execution is still prohibited
Even rows marked `ALLOW_IN_PRINCIPLE` have `implementation_status=NOT_IMPLEMENTED_OR_TESTER_APPROVED` and `eligible_for_empirical_fitting=false`. Compatibility is a design screening only. The registry does **not** count all 1,000 Cartesian combinations as validated methods.

## Family output contracts and row-level decisions
The complete machine-readable matrix with each method's rationale, required test IDs, family output contract, semantic fingerprint and gate status is stored in `PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json`.
