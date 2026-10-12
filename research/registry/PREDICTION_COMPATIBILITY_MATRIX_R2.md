# R2 Compatibility Matrix — preliminary conservative gate

Status: **DRAFT / BLOCKED**. This matrix is deliberately conservative: an empty/unknown compatibility cell is not permission to execute.

## Required dimensions
- Model family: 20 families in `METHOD_REGISTRY_V2_R2.json`
- Feature representation: 10 representations in the registry
- Inference operator: 5 operators in the registry

## Current decision
All Cartesian-product combinations remain **UNREVIEWED / BLOCKED** until a row-level compatibility manifest defines:
1. expected model output (score, probability, state posterior, hazard, or prediction set);
2. training-only fit and calibration method;
3. operator preconditions and threshold source;
4. temporal validity assumptions;
5. explicit ALLOW or BLOCK decision and reason;
6. evidence/test ID proving the adapter contract.

## Mandatory family-specific checks
- `conformal_set_decision`: require a temporal calibration protocol and a documented validity argument; no default exchangeability assumption for time series.
- `uncertainty_abstention`: define uncertainty measure, its training-only calibration, abstention coverage, and scoring treatment.
- `cost_sensitive_threshold`: cost matrix and threshold must be frozen using training data only.
- `probability_threshold`: verify calibrated probability semantics and a fixed threshold.
- `survival_first_passage`: require a registered time-to-event estimand, censoring policy, cause-specific cumulative incidence implementation, and numerical tests. Do not apply generic classifiers' probability adapters by analogy.
- `hidden_markov_model`, `markov_switching_logit`, and `bayesian_dynamic_logit`: verify state/posterior uncertainty output and avoid treating latent states as known labels.
- All feature representations: verify input schema, timestamp availability, missingness behavior, and that each representation adds a documented causal transform rather than a name-only variant.

## Count rule
The registry may claim 1,000 eligible methods only after every included combination passes compatibility checks and the tester confirms meaningful distinction under the frozen fingerprint rule. Invalid pairings must be excluded, not counted to reach a target.

## Tester gate
No model fitting or holdout access. Tester must independently inspect the matrix and adapter tests at a pinned commit and issue PASS/REQUEST CHANGES.
