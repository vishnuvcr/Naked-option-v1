# Phase 5 Protocol — Machine Learning / Nonlinear Direction Models

## Scope
Phase 5 evaluates the pre-registered Family D methods D01-D15 on the frozen Phase 3 labels and data layers. Family C results are inputs only; no method is selected because it looked favorable in Family C.

## Methods and fixed controls
- D01 Random Forest: 300 trees, max_depth=6, min_samples_leaf=20, class_weight=balanced.
- D02 Extra Trees: 300 trees, max_depth=6, min_samples_leaf=20, class_weight=balanced.
- D03 Gradient Boosting: 200 estimators, learning_rate=0.03, max_depth=2, min_samples_leaf=20.
- D04 XGBoost-style boosting: HistGradientBoostingClassifier with max_iter=200, learning_rate=0.03, max_leaf_nodes=15, min_samples_leaf=30.
- D05 LightGBM-style boosting: HistGradientBoostingClassifier with max_iter=250, learning_rate=0.02, max_leaf_nodes=15, min_samples_leaf=40; provider-independent surrogate is explicitly used.
- D06 CatBoost-style boosting: HistGradientBoostingClassifier with max_iter=250, learning_rate=0.02, max_leaf_nodes=15, min_samples_leaf=40; provider-independent surrogate is explicitly used.
- D07 Calibrated stacking: probability averaging of D01-D06, calibration fit only inside training blocks.
- D08 Elastic-net logistic: C=1.0, l1_ratio=0.5, saga/liblinear-compatible deterministic solver as available.
- D09 GAM/splines: fixed degree-3 spline basis with 8 knots per continuous feature, logistic ridge regularization.
- D10 kNN/prototype: k=31, distance-weighted, standardized training-only features.
- D11 SVM: RBF kernel, C=1, gamma='scale', probability calibration fit only inside training.
- D12 Controlled shallow neural network: one hidden layer of 32 units, early stopping disabled; deterministic seed.
- D13 Sequence model: fixed lag-window MLP representation using the last 20 observations, one hidden layer of 32 units.
- D14 Temporal convolution: fixed causal 1-D convolution representation with 16 filters and kernel size 3, followed by a 32-unit dense layer.
- D15 Transformer-style sequence model: fixed 20-step causal attention representation with 2 heads and model width 32; deterministic training seed.

## Feature policy
Use only the frozen Phase 3 core feature layer plus already-approved PIT-safe contextual features. Family C outputs may be included only in a separate secondary experiment explicitly labelled "with statistical-model features"; the primary D-family result must not depend on them.

## Walk-forward protocol
- Chronological training only.
- Minimum training size follows the Phase 3 minimum.
- Refit every 20 trading sessions for both daily and intraday. Intraday predictions are evaluated only on the frozen hourly decision grid; the refit cadence is session-based, not row-based. Sequence methods may use a fixed warm-up.
- Purge observations whose labels extend to or beyond the decision timestamp.
- Standardization, imputation, spline fitting, calibration, feature selection and class weighting are training-only.
- No final holdout access.
- All registered horizons are evaluated independently.

## Evaluation
For every D method/horizon report n, class rate, accuracy, balanced accuracy, ROC-AUC, PR-AUC, Brier, log-loss, confusion matrix, block-bootstrap accuracy interval, and probability-bin future-return diagnostic. Persist BLOCKED_DATA when a required input is unavailable.

## Statistical guard
This phase is directional-model screening, not strategy promotion. No D method is promoted from a single metric or horizon. Later multiple-testing, option-economic, CPCV/PBO/DSR and fresh-forward gates remain mandatory.

## Regression requirements
Before empirical execution, synthetic tests must verify:
1. chronological purge;
2. training-only scaling;
3. no test-fold fitting;
4. deterministic seeds;
5. sequence windows do not cross session boundaries;
6. output probabilities remain finite and in [0,1];
7. calibration never consumes future labels.

## Gate
Tester must independently inspect the protocol, code, workflow and regression tests before the first hosted empirical run. Phase 5 cannot advance to Phase 6 until the Family D artifact passes tester review.
