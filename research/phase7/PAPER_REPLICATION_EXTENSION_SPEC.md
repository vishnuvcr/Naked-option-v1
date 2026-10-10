# Phase 7 Amendment Proposal — Uploaded-Paper Prediction Replications

**Status: PROPOSED — NOT AUTHORIZED FOR EMPIRICAL EXECUTION**  
**Developer branch:** `phase-07-developer`  
**Independent review branch:** `phase-07-tester`  
**Scope:** prediction methods reported by papers in the project; no option P&L / strategy optimization.

## 1. Research question

When implemented on point-in-time NIFTY data and evaluated on chronological out-of-sample observations, do the forecasting algorithms and feature combinations used in the project's papers provide measurable predictive information for NIFTY 50 direction beyond strong causal baselines? Which reported effects survive a common evaluation protocol, data-quality gates and familywise inference?

## 2. Aim and objectives

**Aim:** faithfully inventory and independently evaluate paper-derived prediction methods on NIFTY 50 while preserving the distinction between published findings, project replications and novel adaptations.

**Objectives:**
1. Extract every paper-native estimator, input/feature recipe, target, horizon, split, metric, baseline and reported limitation.
2. Crosswalk the 15 mounted PDFs and the repository's 36 literature records to the fixed experiment registry; list unique methods and gaps before fitting anything.
3. Test methods on the data range and feature set that actually pass source/point-in-time checks. Preserve unsupported source windows as `BLOCKED_DATA` rather than silently substituting a weaker signal.
4. Compare directional forecasts on common timestamps against causal historical-rate and persistence/previous-direction baselines; evaluate price forecasts separately.
5. Separate paper-faithful reproductions from safe adaptations where papers use random splits, full-sample feature selection, unclear “accuracy,” or unavailable data.
6. Apply block-aware uncertainty estimation and a pre-declared familywise test across the registered paper-method × horizon search.
7. Obtain independent tester review before each empirical batch and again after immutable result artifacts are produced.
8. Update status, README, logs, error log and final manuscript from audited evidence only.

## 3. Research phases and gates

| Gate | Work | Required evidence | Status |
|---|---|---|---|
| PPR-0 | Governance and source inventory | Current README/status, method registry, logs, branch roles and workflow authorization reviewed | COMPLETE FOR THIS SUBMISSION |
| PPR-1 | Full-text extraction and paper crosswalk | `PAPER_PREDICTION_METHOD_CROSSWALK.md`, citations/quotes checked against mounted PDFs | DEVELOPER DRAFT COMPLETE; TESTER REVIEW REQUIRED |
| PPR-2 | Full literature-registry crosswalk | Every existing literature row linked to a paper-method row, background-only row, or documented reason it has no prediction method | NOT STARTED |
| PPR-3 | Exact protocol freeze | Complete model/config grid, labels/horizons, common features, tuning budget, baselines, metrics, exclusions and multiplicity scope | NOT AUTHORIZED |
| PPR-4 | Data feasibility | Cache/schema inventory; free-source attempts; date coverage, availability timestamps, field ranges, source hashes and missingness report | NOT AUTHORIZED FOR NEW SOURCES |
| PPR-5 | Code implementation + offline tests | Deterministic runner, regression tests for target timing/signs, sequence windows, scaling, feature selection, zero-sample paths and schema validation | NOT STARTED |
| PPR-6 | Independent pre-run code/tester gate | Exact commit/blob/hash-bound tester PASS with allowed scope | NOT PASSED |
| PPR-7 | Gated empirical execution | All required regression/authorization/source jobs PASS; never manually bypass tester input | BLOCKED |
| PPR-8 | Independent artifact audit | Recompute every metric, target, row count, provenance hash and multiplicity test from immutable artifact | BLOCKED |
| PPR-9 | Coverage reconciliation | Every paper-method × pipeline × horizon marked TESTED_AND_AUDITED, TESTED_NEGATIVE, BLOCKED_DATA, BLOCKED_METHOD or REJECTED_AT_GATE | BLOCKED |
| PPR-10 | Final interpretation/manuscript | Methods, tables, plots, uncertainty, limitations, supplementary failures and reproducible run ids; final holdout only after its separate gate | BLOCKED |

These gates are finite; the research is not open-ended. The end condition is a complete audited coverage ledger, not a requirement to find a profitable model.

## 4. Proposed experiment grid

### 4.1 Paper-derived estimators to consider

**Tabular regression/classification**
- Linear Regression / multivariate regression; Logistic Regression.
- Lasso, Ridge, Elastic Net, SGD regressor.
- KNN regressor/classifier.
- Decision Tree regressor/classifier.
- Bagging and Boosting; Random Forest.
- Gradient Boosting, AdaBoost and XGBoost-compatible model.
- SVM/SVR.
- Single-layer perceptron and MLP; RBF network.
- LSTM and Backward-Elimination LSTM (BE-LSTM).

**Sequence architectures**
- Simple RNN, LSTM, GRU, 1D CNN, TCN.
- Hybrids: LSTM+GRU, CNN+RNN, CNN+TCN, LSTM+TCN.
- Paper-native LSTM/ANN/SVM variants are separate configuration rows where target/features/tuning differ, even if estimator class is shared.

**Technical and context signals**
- 50/200 SMA crossover; 50/200 EMA Golden/Death Cross; other paper-specified moving-average periods only when explicitly found in full text.
- CCI 20-day as a *prediction-only spot-direction proxy* is proposed as a new registry amendment; no option trading P&L in this phase.
- FII gross purchases/sales, FII/FPI and DII net-flow ratios, USD/INR, India VIX, nearest-expiry PCR/option pressure, sector leadership and market breadth, if historical point-in-time data pass the source gate.
- Text sentiment: four-class daily sentiment and SOFNN from the Mehtab paper; BERT/financial-news sentiment plus LSTM from the Naik/Inamdar paper. These are distinct methods and cannot be credited as tested merely because a generic sentiment or sequence row ran.

**Strategy-only papers:** do not turn qualitative option-strategy descriptions into prediction models. CCI is retained only as an explicitly declared directional proxy; option entry, exit, brokerage, slippage, premium P&L and long-call/put execution remain Phase 8 work.

### 4.2 Targets and horizons

- Main common directional target: sign of future NIFTY close-to-close return at 1, 2, 3, 5 and 10 trading sessions. Label is computed from the decision-time close to the future close; direction threshold and neutral handling are frozen in the runner. Do not shift features forward or make the current close part of the future return.
- Price regression: next-day open and close where the paper predicts these; report price MAE/RMSE/R² separately. Derive a directional prediction from forecast-close versus current close and score on the same future label timestamps.
- Paper-native 30-session close forecast: supplemental task for IJSDR and JRFM/BE-LSTM only where the full text confirms that horizon. A 30-session result does not replace the common direction grid.
- The “next 30 days” wording may mean calendar days in some papers; the paper’s exact trading-session interpretation must be recorded before the supplemental task is activated.

### 4.3 Features and comparison pipelines

- Core available-data pipeline: OHLCV lags plus paper-specified indicators computed causally (SMA 10/20, RSI 14, daily return, rolling volatility 20; additional fixed windows only if the paper specifies them).
- Source-conditioned pipelines: FII/DII, USD/INR, India VIX, option OI/volume/PCR/Greeks and sector/breadth features, each separate from OHLCV-only baseline.
- Sentiment pipelines: only with historical source timestamps and publication/availability times earlier than each forecast cutoff. News or tweets without defensible historical timestamps cannot be joined as if they were known at the time.
- Ablations: OHLCV-only; technical features; external-market/flow/options features; sentiment only; combined feature set, subject to source availability.
- Missing data are not imputed from future rows; keep a per-cell reason code and disclose the exact active feature set for every model.

### 4.4 Evaluation and inference

- Common primary metrics: ROC AUC, PR AUC, Brier score, log loss and balanced accuracy. Also report accuracy, sensitivity, specificity, precision/PPV, NPV, calibration and class prevalence to match the relevant papers where interpretable.
- Regression metrics: MAE, RMSE, R², SMAPE/MAPE only with explicit handling of zero denominators; never use the paper’s undefined “accuracy” as a comparable metric.
- Baselines: causal training-rate probability; persistence/previous-direction; 50/50 random reference for context. Price-regression baseline: last-observation persistence.
- Use identical common evaluation rows for paired comparisons within each target/horizon. Hyperparameter and feature selection occur only inside the training history. Fit scalers and feature selectors inside each training fold.
- Use a pre-declared block bootstrap for dependent observations and one familywise maximum-statistic test over the full authorized paper-method × feature pipeline × horizon grid. Report raw/adjusted p-values, effect sizes, uncertainty intervals and best descriptive results even when non-significant.
- For models selected using cross-validation, do not treat the validation folds as the final test; preserve one untouched forward segment until the separate Phase 10 authorization.

## 5. Data constraints known before this proposal

- Latest independently audited Run #44 artifact contains 1,676 daily NIFTY rows from 2020-01-01 through 2026-10-09, plus 11 global/peer histories. This supports available-sample evaluation, not an exact 5/10/20-year replication.
- Run #44's global/peer extension completed 12 registered methods × 5 horizons (60 cells); none passed its horizon-family significance test. Those results remain separate and cannot be represented as outcomes of every method in this proposal.
- Current status blocks broader historical fitting pending official-source NIFTY cross-check, instrument mapping, exact-snapshot approval and an independent tester gate. The one-use Dhan sample approval is spent and the one-row sample is not model data.
- Full historical news/tweets, BERT input histories, option-chain PCR/Greeks and FII/DII/sector/breadth require separate point-in-time/source feasibility. Apply free-source search before any paid-source conclusion.
- Current paper crosswalk is limited to the 15 mounted PDFs. The repository's separate 36-record literature inventory still must be mapped at PPR-2.
- No current artifact demonstrates a tested final result for all specific paper configurations. Existing family-level results are only reusable where the method, target, feature recipe, horizon, split and artifact genuinely match.

## 6. Execution sequence once reviewed

1. Tester independently reviews PPR-1 crosswalk for omissions and unsupported interpretations.
2. Developer reconciles all literature registry records and freezes PPR-3 configuration matrix; add a new registry candidate only through a documented pre-test amendment.
3. Tester approves exact protocol/configuration scope.
4. Developer runs only bounded source feasibility; tester independently reviews archive/schema/provenance/coverage.
5. Developer implements and runs offline tests; tester audits exact protected files and workflow before execution.
6. The automatic GitHub Actions workflow verifies hashes/tester manifest and performs the authorized empirical batch only if all conditions pass.
7. Tester downloads immutable artifacts and recomputes outputs. Any discrepancy creates an error-log entry, invalidates the run as evidence, and triggers a fresh reviewed snapshot.
8. Update status/README/research log after every gate. Run later paper families sequentially within this finite protocol, not as an unlimited search.
9. At final phase, produce the research manuscript with method registry, paper matrix, metrics, significance/uncertainty tables, charts, failures, caveats and supplementary material. Keep Phase 8 economics and the untouched holdout behind their own explicit gates.

## 7. Explicit non-authorizations

This proposal does **not** authorize:
- full-history source pulls or live exchange requests;
- training, tuning or scoring any new paper-specific models;
- final-holdout access;
- adding paper-derived CCI/BERT/SOFNN/hybrid methods directly to the frozen registry and testing them before review;
- any options trading strategy, option P&L, or profitability claim.

**Developer → Tester:** Review the paper-method list, label/horizon definitions, per-paper feature/target mapping, familywise inference and the current source constraints. Return an exact-snapshot PASS/REQUEST CHANGES. If passing, authorize only the next stated gate—not an unrestricted empirical run.

**Tester → Developer:** Keep all new method fitting and full-history source acquisition fail-closed until the exact protocol and relevant source/code gates pass.
