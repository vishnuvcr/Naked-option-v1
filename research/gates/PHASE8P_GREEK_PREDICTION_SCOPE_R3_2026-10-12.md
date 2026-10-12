# Phase 8P — Greek Feature Incremental Prediction Study, Scope R3
Date: 2026-10-12
Role branch: phase-08-prediction-developer
Supersedes R1 and R2 for future work; both prior scopes and tester reports remain immutable history.
Status: **CORRECTED SCOPE SUBMITTED FOR INDEPENDENT REVIEW — NO EMPIRICAL RUN AUTHORIZED**

## 1. Purpose and boundary
This is prediction-only. It tests whether the accepted R3 Greek-enriched research artifact adds out-of-sample information for future NIFTY spot direction on the same timestamps and labels. It does not evaluate option entries/exits or P&L, access the final holdout, select a trading strategy, promote a method, or request new market data.

The work refines the existing plan's questions about incremental derivatives/options information without changing the Phase 0–11 catalog. R3 stays immutable. Its source is PARTIAL_GRID, its Greeks are model estimates, and CC-BY-NC-4.0 limits the study to non-commercial research.

## 2. Research questions, aim and objectives
**RQ8P.1:** Do fixed Greek/IV features add directional predictive information versus a matched spot-only comparator?
**RQ8P.2:** Does any improvement persist across daily horizons 1/2/3/5/10 sessions and intraday horizons 5/15/30/60/120 minutes?
**RQ8P.3:** How sensitive are results to IV and expiry-mapping provenance?
**RQ8P.4:** Is the overlap between the option feature panel and frozen forecast panels sufficient for a fair paired comparison?

Aim: measure incremental predictive value of the observed option panel without leakage or holdout contamination.

Objectives: pin and hash inputs; prove exact time/label contracts; produce provenance-stratified features; compare fixed models on identical development rows; quantify missingness/coverage; use paired uncertainty and multiplicity control; publish aggregate-only reproducibility artifacts; fail closed whenever identity, split, schema, time or label maturity cannot be proven.

## 3. Frozen inputs
### Accepted Greek-enriched data
- Source run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38195812828
- Artifact ID 11723198817; name nifty-1m-greeks-enriched-r3
- ZIP SHA-256: e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736
- HF source revision: 0f4800e43e6f96cec0794369d78eb4d3c4211ef5; license CC-BY-NC-4.0.
- 8,999,865 total rows = 8,490,723 option + 509,142 spot; 61 encrypted parts; 8,418,616 option rows with Delta.
- R3 tester review: https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-tester/research/gates/PHASE8_GREEK_ENRICHMENT_ARTIFACT_REVIEW_R1_2026-10-12.md
- Binding limitations: PARTIAL_GRID; European Black–Scholes estimates; r=0/q=0 proxies; historical expiry inferred from an HF partition list or Tuesday-rule proxy, not verified by official point-in-time contract master; no historical executable bid/ask evidence established.

### Frozen forecast panels
- Run #994: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656
- Artifact ID 11638738288; ZIP SHA-256 3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9
- Embedded manifest SHA-256 f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091
- Aggregate SHA-256 96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39
- Ten panels / 50,555 rows, already independently validated. P01–P10 are immutable reference predictions. This study cannot edit the predictions or access the protected holdout.
- Prior context only: Phase 7 reported daily best AUC around 0.579, balanced accuracy around 0.496, and non-significant family-level moving-block bootstrap outcomes. Revalidate against the accepted report before quoting in results.

## 4. Exact time, label and holdout preflight (mandatory before fitting)
Create a schema/coverage-only stage that produces a machine-readable JSON decision with these fields: decision (PASS/BLOCKED), developer commit SHA, both exact artifact IDs and digests, panel schema hash, Greek schema/manifest hash, confirmed decision-time field and timezone, confirmed Greek bar-end valuation-time convention, target-label field, target-end rule/source, label maturity purge rule, protected-holdout exclusion proof, per-layer/horizon panel counts, exact-join counts/rates, valid-feature counts/rates, provenance-stratified coverage, and failure reasons.

The modeling job must be unreachable unless the preflight decision is PASS and the independent tester has accepted that exact preflight artifact. A missing field, unrecognized schema, ambiguous split, or undocumented transformation means BLOCKED, with no model fit.

Specific rules:
- Download only the two exact pinned GitHub Actions artifacts; verify whole ZIP SHA-256 before extraction. No other sources or new source requests.
- The Greek file's source timestamp marks the candle start; Greek pricing fields are valued at timestamp +60 seconds. Before feature aggregation, the code must establish the exact UTC instant equal to the forecast decision time.
- The saved forecast panel schema and label protocol must explicitly prove the target label and target-end rule. Do not reconstruct labels from horizon names or guess minute offsets. If the saved panel lacks this contract, stop and submit a separate tester-reviewed amendment.
- Use the panel's protected split/holdout metadata or another already-approved immutable mask. If the exact development-only mask cannot be proven from the frozen source, stop with BLOCKED; do not fit on any rows.
- For each layer+horizon, join only on exact UTC instant. No nearest merge, interpolation, forward fill or cross-session carry.
- Only rows whose labels have fully matured before a training cutoff may train the model. Purge overlapping/immature labels from training. No future labels or test-row statistics may drive feature preprocessing.
- Raw counts, unmatched reasons and usable features must be reported before any fit.

## 5. Frozen feature formulas
All features are formed at the decision instant using observed data available by that instant. Underlying spot bars are joined by exact bar-end instant; their candle-start timestamps receive the documented +60-second bar-end convention.

### A. Spot-only comparator
From rows explicitly marked SPOT and only from values available at the decision instant:
- lag return k: r_k(t) = ln(S(t) / S(t-k)) for k in {1, 5, 15, 30, 60} completed one-minute bars;
- RV20(t) and RV60(t): sample standard deviation (ddof=1) of the preceding 20 or 60 one-minute log returns, respectively, with no annualization;
- previous-session return: ln(previous_session_close / prior_session_close_before_that) using two completed sessions only.
Missing lags/returns remain missing with explicit indicators; no cross-session synthetic bars or forward fills.

### B. Spot + visible-panel option/Greek block
Primary eligible rows require row_type=OPTION, option_type CE or PE, Greek status indicating estimated valid Greeks, finite values for the feature being aggregated, and no source flag for non-trading sessions. All aggregates are explicitly for the visible PARTIAL_GRID, not the complete exchange option chain.

For each timestamp:
- n_call / n_put: counts of eligible CE / PE rows; n_delta_call / n_delta_put: eligible rows with finite signed Delta.
- Only compute side-specific Greek medians when at least 5 valid rows exist for that side; otherwise return missing and set the relevant insufficient-coverage indicator.
- call_delta_median = median(Delta | CE); put_delta_median = median(Delta | PE) using signed Delta, so the PE median is normally negative.
- delta_imbalance = call_delta_median + put_delta_median. Positive means the median observed call Delta is larger than the absolute median observed put Delta; negative means the reverse. This is not a market-wide dealer-position estimate.
- For each side separately, compute medians of Gamma, Theta per day, Vega per 1% IV and Greek-implied IV from eligible finite rows; iv_skew = put_iv_median - call_iv_median only when both side medians are available.
- open-interest put/call ratio = sum(PE open_interest) / sum(CE open_interest), using only finite nonnegative OI values and only if both sides have valid observations and the CE denominator is strictly positive. Volume put/call ratio uses the same rule for volume. Never add an epsilon/smoothing constant; denominator zero or missing means missing ratio plus denominator-status indicator.
- provenance fractions: proportions of option rows with Greek status, IV source and expiry-mapping source, reported separately; these are diagnostics/quality covariates only and may not use target outcomes.
- OI/volume observations are usable only if their bar-end instant is no later than the forecast decision time.

Missingness and transforms: each continuous feature is imputed with its training-fold median only; missing indicators are allowed and fixed in advance. Any scaler is fit on training rows only. No winsorization, threshold search or target-based feature selection. Primary model comparison uses the exact same decision-row intersection for both arms within each model/horizon, with identical labels and test timestamps.

## 6. Fixed models and chronological evaluation
Models (no tuning; exact estimator settings are frozen):
1. L2 LogisticRegression pipeline: SimpleImputer(strategy=median, add_indicator=True) fitted on training rows only, then StandardScaler fitted on those imputed training rows only, then LogisticRegression(penalty=l2, C=1.0, solver=liblinear, class_weight=None, max_iter=1000, tol=1e-4, random_state=42). A convergence warning, non-converged fit or non-finite probability makes that model/horizon BLOCKED_MODEL_CONVERGENCE; do not change solver, tol or max_iter in response.
2. HistGradientBoostingClassifier pipeline: SimpleImputer(strategy=median, add_indicator=True) fitted on training rows only, then HistGradientBoostingClassifier(max_iter=200, learning_rate=0.03, max_leaf_nodes=15, min_samples_leaf=30, l2_regularization=0.0, max_bins=255, early_stopping=False, class_weight=None, random_state=42). No scaling. If the pinned scikit-learn version does not support the exact registered arguments, fail the regression gate and propose an explicit tester-reviewed amendment rather than silently switching settings.
All imputers, indicators, scalers and estimators are re-fit for each walk-forward training block. The model software versions are pinned in the run manifest.

For every model and horizon, compare spot-only with spot-plus-Greek features on identical eligible rows. Use expanding chronological walk-forward blocks and refit every 20 completed trading sessions. Do not import a new split convention: pin the exact approved Phase 3/7 splitter/label maturity rules into the code gate. Purge training rows whose target window overlaps the first test decision. All model preprocessing and calibration are training-only.

Never use the untouched final holdout. A study cannot begin fitting until the protected boundary is independently proven from frozen metadata. If the validated split rule cannot be recovered exactly, remain BLOCKED_DATA pending a new tester-approved amendment.

## 7. Metrics and inference
Primary: paired Brier-score improvement = Brier(spot-only) - Brier(spot-plus-Greek); positive means the augmented variant has lower Brier loss.
Secondary: ROC-AUC, PR-AUC, balanced accuracy, log loss, calibration slope/intercept and class rate, each reported with eligible/test row counts and coverage.

Use identical rows, labels and test timestamps per paired comparison. Define d_i = Brier_i(spot-only) - Brier_i(spot-plus-Greek); positive d means the augmented arm is better. For each of the 20 primary comparisons (2 model types × 10 horizons), test one-sided H0: mean(d) <= 0 using the Phase 7 moving-block construction only if the panel grid/unit is proven to match: daily L=20 sessions; intraday L=60 decision observations. The ordered input must be unique and chronologically sorted; daily inputs must contain one row per registered decision session, and intraday block positions must be the frozen Phase 7 decision-observation sequence. The preflight must verify these invariants. Otherwise inference is BLOCKED and requires a tester-reviewed amendment.

For each comparison, compute observed statistic T = mean(d). Construct null-centered values d0_i = d_i - T. For each of B=500 replications with seed 42, enumerate all contiguous block starts s=0,...,n-L, sample ceil(n/L) starts with replacement, concatenate blocks and truncate to n exactly as Phase 7 specifies; use the same sampled indices for the paired d-vector. Compute T_b = mean(resampled d0). The one-sided raw p-value is (1 + count(T_b >= T)) / (B + 1). If inputs, resampling or any statistic are non-finite, fail the gate rather than dropping observations or reducing the denominator. The minimum attainable raw p-value is 1/501; record this coarse resolution as a limitation. Apply Holm step-down correction to the full pre-registered 20 raw p-values and save raw/adjusted p-values, resample configuration and family membership. Do not select a winner by unadjusted metrics.

## 8. Data feasibility gates and fixed stop rule
For each model/horizon, a PASS preflight requires:
- exact feature join of at least 60% of eligible development panel rows;
- at least 1,000 eligible training rows at the first fit;
- at least 500 out-of-sample rows;
- at least 20 chronological test blocks;
- target horizon and maturity rule proven;
- protected holdout rows explicitly excluded;
- identical eligible rows across paired arms.

If any item fails, emit INSUFFICIENT_OVERLAP/BLOCKED_DATA with exact counts and reasons. Thresholds are not relaxed after seeing results; do not swap datasets because a result is poor.

## 9. Security, licence and out-of-scope work
- Use only the two pinned artifacts; no Hugging Face, Dhan, NSE, BSE or other market-data requests.
- Decrypt/read data only in runner temporary storage using the existing HF_TOKEN-derived AES key. Never print or pass the token/key on command line.
- Delete all plaintext/intermediate data before job completion. Do not upload raw rows, decrypted CSV/Parquet, token-derived keys, or raw per-contract details. Aggregate-only reports and pinned hashes may be artifacts.
- No option P&L, costs/execution, brokerage/slippage, holdout access, strategy testing/promotion or commercial use.
- If Greeks do not improve the registered paired metric, record that result; this is not permission to expand endlessly or inspect the holdout.

## 10. Required workflow gates
1. Tester approves this scope.
2. Developer implements a schema preflight, aggregation/math functions, model runner, regression tests, and fail-closed workflow.
3. Independent tester reviews exact source/blob hashes and synthetic-only tests before real artifacts are opened.
4. Hosted preflight validates immutable inputs, schema/time/labels/holdout and cleanup. Tester accepts that exact preflight artifact before any fit.
5. Hosted prediction-only run emits immutable aggregate-only metrics.
6. Independent tester independently recalculates metrics, formulas/signs, bootstrap/Holm inference, row alignment, purging, holdout exclusion and hashes.
7. Update README, research status, error log, chat log and decision artifacts for every outcome. No phase/gate advances on developer success alone.

## Current status
Scope R3 is submitted for tester review. No new artifact has been decrypted for this sub-study, no model has been fitted, and no empirical result is claimed.

**Developer → Tester:** independently review the exact formulas, fixed estimator settings, same-row comparison, timestamp/target/holdout preflight, label purge, null-centered bootstrap p-value, exact block unit and encrypted-only handling. Approve scope only or return precise changes; do not grant empirical authorization.

**Tester → Developer:** preserve R1/R2 and their findings; do not implement/launch fitting until scope approval, then require independent code review and a separate preflight decision.
