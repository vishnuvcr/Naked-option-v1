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


## 8. Tester-requested amendments — v1.1 (2026-10-10)

This section responds to the PPR-1 tester report. It narrows the future confirmatory scope; it does not authorize data pulls or model fitting.

### 8.1 Distinct inferential families and exact statistic

The operative pre-registration is [`PPR_TARGET_INFERENCE_CONTRACT.json`](PPR_TARGET_INFERENCE_CONTRACT.json). This file freezes the primary loss, baseline, candidate-family composition, target schema, point-in-time contract, common evaluation origins, centered-null block bootstrap, confidence intervals, missing-cell disposition and fit-call budget. No analyst may fill gaps through ad hoc interpretation; if implementation reveals an unresolved case, stop and amend before fitting.

- Direction, close-price regression and next-open regression are separate families. Classification candidates in the confirmatory direction family must all emit a probability vector for the same three-class label schema `DOWN, FLAT, UP`; binary labels and price regression may not be pooled into that family.
- Primary direction loss is multiclass Brier score on the fixed class order. Primary regression loss is absolute error against the matching target field, compared with the exact persistence equations in the contract.
- Within each family, all planned candidates and horizons use the same ordered decision-origin index. No pairwise row deletion is permitted. The family is `INCOMPLETE_NOT_PROMOTABLE` if any pre-frozen candidate lacks sufficient valid predictions/losses or positive finite standard error.
- For each candidate, define paired improvement as baseline loss minus candidate loss. Center each candidate's paired differential by subtracting its own sample mean before bootstrap resampling. Use moving blocks of length `max(5, maximum horizon in that family)`; use identical sampled block indexes across all candidates and horizons in that family.
- Run the frozen one-sided max-studentized-mean-improvement test with 10,000 block-bootstrap replicates, deterministic seed 20261010, and adjusted p-value `(1 + exceedances)/(1 + B)`. Use bootstrap standard deviations of null-centered mean differentials for studentization, and the max-absolute studentized null quantile for simultaneous 95% familywise intervals. The exact formulas and handling are in the JSON contract.
- The configuration cap is 80 base configuration rows **including task type/target schema**, 4 feature pipelines and 5 common horizons; every row is assigned to only one target family. A different task/output schema consumes a separate base row. Maximum outer cells are therefore 1,600 and maximum outer fit calls including up to three seeds is 4,800. The bounded tuning allowance is 20 configurations × 20 candidate settings × (up to five chronological folds plus one final refit) = 2,400 fit calls; total expected work is capped at 7,200 under an 8,000 global fit-call ceiling. The PPR-3 machine-readable manifest must calculate the actual budget and fail closed if a cap is exceeded.
- Undefined cells remain present with reason codes. No candidate may be added after result inspection. Paper-native tasks with an unclear target/metric stay descriptive, `AMBIGUOUS`, or `BLOCKED_METHOD`; they cannot quietly enter a common confirmatory family.

### 8.2 Target and endpoint alignment contract

Every experiment manifest must include: paper_id, method_id, task_type, decision_timestamp, timezone, decision_price_field, target_formula, forecast_endpoint, horizon_unit, neutral_tolerance, forecast_to_direction_rule, and eligible-row count.

- Common direction task: at decision close C_t, forecast the sign of C_(t+h)/C_t - 1 for h in {1,2,3,5,10} exchange sessions. The decision occurs only after official close data for session t is published and marked available. A forecast made before that publication must use the prior session close and cannot use t's close or indicators containing it.
- A price forecast is scored only against the exact endpoint it claims to forecast. A next-session close forecast maps to direction using predicted C_(t+1) versus the same C_t; a 30-session forecast is scored against C_(t+30), not a next-session label. Open-price forecasts are regression tasks and are not automatically treated as close-direction predictions.
- For all tasks, training row i is eligible at decision time t only if its label endpoint timestamp is strictly earlier than t. The forecast endpoint must equal the label endpoint. Ambiguous “30 days” versus “30 trading sessions” remains blocked until the source's wording is verified and the choice recorded.
- Flat handling: primary direction is UP for return > 0, DOWN for return < 0, and FLAT only when absolute return <= 1e-8. If a paper requires binary labels, map FLAT using a separately declared paper-native rule; do not silently merge classes.

### 8.3 Point-in-time availability rules

All timestamps are stored in Asia/Kolkata and normalized to UTC for comparisons; exchange-session identity follows the official NSE calendar.

- Daily OHLCV and close-derived indicators are usable for a decision only after the official close value for that session is available. If the forecast decision is pre-close, use the last completed session.
- FII/DII and exchange report features use publication/availability timestamp, not just event date. A daily record with no defensible publication timestamp is excluded from PIT predictors for that day and may be used only under a predeclared lag rule.
- VIX, option-chain/OI/PCR/Greeks and other market snapshots must have capture timestamps no later than the decision cutoff; expiry/contract mapping must be point-in-time. No backfilled end-of-day snapshot is allowed for an earlier decision.
- News and social text require original publication timestamp and, where available, ingestion timestamp. Both must precede cutoff; later edits/corrections are not retroactively available. Text with date-only timestamps is excluded from same-day PIT use unless a fixed lag is preregistered.
- Corrected/revised vendor records must preserve vintage metadata. If historical vintage cannot be reconstructed, mark the feature pipeline as adapted/limited and do not claim exact PIT replication.
- Regression tests must assert: no same-day close feature before close publication; no training label endpoint equal to or after decision time; no news/publication timestamp at or after cutoff; no future source revision; and exact horizon endpoint alignment.

### 8.4 Exact replication versus leakage-safe adaptation

Create separate manifest rows for each paper-native configuration and its leakage-safe adaptation. Record the paper's reported split, target, feature selection, horizon and metric separately from the project adaptation. A random split or full-sample feature selection may be reproduced only as a clearly labelled descriptive fidelity analysis if it does not contaminate the confirmatory evaluation; it cannot be used as evidence of deployable predictive performance. If the source does not sufficiently specify a method, label BLOCKED_METHOD and list the unresolved details instead of inventing hyperparameters.

### 8.5 Bounds on the confirmatory search

PPR-3 must freeze a machine-readable manifest before any fitting. Initial upper bound: 80 distinct estimator/architecture configurations, 5 common horizons, 4 feature-pipeline classes (OHLCV/causal technicals; external market; flows/options; timestamp-valid sentiment), and at most 3 predeclared seeds for stochastic neural methods. The actual manifest may be smaller; it may not exceed these bounds without a reviewed protocol amendment. At most 20 candidate configurations may receive hyperparameter search, each with at most 20 configurations per inner chronological search. All tuning remains inside training folds. No candidate may be added to the confirmatory family after any evaluation result has been inspected.

### 8.6 Metric edge cases and baselines

- Causal training-rate baseline: the expanding training-only class frequency, with Laplace smoothing alpha=1, recomputed at each decision point.
- Previous-direction baseline: sign of the most recent completed close-to-close return, with probability mapping frozen in the runner; it is not the same as a 50/50 random predictor.
- 50/50 is a reference only, not the primary baseline. Report class prevalence, n, and confusion matrix counts.
- AUC metrics require both classes. Percentage errors must define zero/near-zero denominator behavior before execution; MAPE is not used for return targets. Undefined metrics are stored as null with a reason code, never coerced to zero.

### 8.7 Source evidence requirement

The claim-level source table is now committed as [`PAPER_SOURCE_EVIDENCE_MATRIX.md`](../literature/PAPER_SOURCE_EVIDENCE_MATRIX.md). It separates methods, data/date span, target/horizon, split, metrics/results and limitations for each of the 15 PDFs, using physical PDF page locators. Its claims still require tester scrutiny: for example, the ISMLA dataset's option-like fields leave target identity unresolved; the JIER paper has conflicting moving-average periods/date windows; several papers report undefined accuracy figures; JRFM performs backward selection on the full sample; and the CCI paper has an inconsistent 68-versus-80 trade count. These are source uncertainties to preserve, not details to silently repair.

Every frozen config must assign `AUTHOR-IMPLEMENTED`, `BACKGROUND-ONLY`, `AMBIGUOUS`, or `PROJECT-ADAPTATION`, and cite the source locator for each method, data, target/horizon, split and metric field. Unresolved tasks stay blocked or descriptive.

**Status after amendment:** the source evidence matrix and machine-readable target/inference contract are committed, but independent review and a new exact-snapshot test receipt are required. PPR-2, new data pulls, fitting/scoring and holdout access remain unauthorized.

**Developer → Tester:** Review this amended protocol and the source-evidence additions in the crosswalk against the exact new blobs.  
**Tester → Developer:** Reject any snapshot that lacks page/section evidence or a machine-checkable manifest; no empirical authorization from this amendment alone.
