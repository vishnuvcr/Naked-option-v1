# Phase 7 — Ensemble and Regime-Conditioned Prediction Specification

## Status
**Developer proposal — tester review required before implementation or empirical execution.**

## Research question

Does combining the pre-registered Phase 6 probability forecasts, using fixed combination and regime-conditioned rules, produce a more stable out-of-sample directional forecast than the individual Phase 6 methods without introducing selection leakage?

The literature motivates combination/stacking and regime-aware forecasting, but it also makes data-snooping control essential. Zhao & Cheng (2022) report out-of-sample gains from stacking diverse return-prediction models, while regime-switching combination work explicitly models model/regime uncertainty. These are methodological motivations, not evidence that the present NIFTY problem will benefit. Data-snooping controls follow White/Sullivan/Timmermann.

## Fixed candidate universe

Phase 7 may use only forecasts already produced under the accepted Phase 6 artifact:
- E01-E10
- I01-I10

No Phase 6 method may be added, retuned, or selected after observing Phase 7 outcomes.

Blocked Phase 6 forecasts remain blocked. No replacement feature or alternative data source may be introduced merely to repair a blocked component.

## Registered ensemble families

### P01 — Equal-weight probability mean
For each decision time and horizon, average all available Phase 6 probabilities after mapping each forecast to a common directional probability.

### P02 — Probability median
Median of all available Phase 6 probabilities.

### P03 — 10% trimmed probability mean
For n available forecasts, set k=floor(0.10*n). If k=0, use the ordinary mean; otherwise remove exactly k observations from each tail and average the remainder. No alternative small-sample rule is permitted.

### P04 — Equal-weight family mean
First average E-family forecasts and I-family forecasts separately; then average the family means. If one family has no available forecast for a cell, use the other family without tuning.

### P05 — Fixed confidence abstention
Use P01, but abstain when the ensemble probability lies in [0.45, 0.55]. Threshold is frozen and not optimized.

### P06 — Strong-confidence abstention
Use P01, but abstain when probability lies in [0.40, 0.60]. Threshold is frozen.

### P07 — Chronological logistic stacking
For each layer/horizon, use the fixed set of Phase 6 methods whose status is EXECUTED for that cell in the accepted Phase 6 artifact. Blocked methods are omitted, never imputed or replaced, and the predictor set is not selected using Phase 7 outcomes. Fit a regularized logistic meta-model only inside the training portion of each chronological evaluation block using these Phase 6 probabilities as predictors. The meta-model is refit causally and never sees future labels. Hyperparameters are frozen: L2 penalty C=1.0, solver=lbfgs, max_iter=500, random_state=42. Standardization, if required, is fit only on the training portion.

### P08 — Regime-conditioned P01
Use P01, but calculate a causal regime state from NIFTY realized-volatility and trend features available at decision time. Three fixed states are used: low-vol/trend, high-vol/trend, and high-vol/non-trend. State thresholds are fixed from training quantiles only: 33rd and 67th percentile of training realized volatility and a frozen absolute trend-strength threshold defined in the implementation specification. No threshold may be optimized after results are seen.

### P09 — Regime-conditioned family combination
Use P04 inside each of the same four causal regimes and apply the same fixed training-only regime calibration: P09 = 0.5*P04 + 0.5*q_s, with the same <50-observation pooled-rate fallback. The regime-to-combination mapping and 0.5 blend weight are fixed; no regime-specific model selection.

### P10 — Fixed abstention + regime combination
Apply P09 and abstain at probability interval [0.45, 0.55].

## Causality and validation

- Every meta-model/regime statistic must be estimated only from observations strictly before the forecast timestamp.
- Chronological walk-forward evaluation is mandatory. The fixed schedule is an expanding training window with a minimum of 200 eligible training observations, followed by a 20-trading-session test block; refit at every 20-trading-session boundary. Intraday rows inherit the same session blocks, so no intraday-specific refit cadence may be tuned.
- Final untouched holdout remains unopened.
- Phase 7 test predictions must be generated without using labels from the same evaluation block.
- Any standardization, calibration, thresholding or regime quantile is fit on training data only.
- If a candidate cannot be computed without violating PIT rules, mark it BLOCKED_DATA rather than substituting another source.

## Benchmarks

Every Phase 7 candidate must be compared against:
1. majority-class baseline;
2. historical positive-rate probability baseline;
3. best pre-existing Phase 6 individual forecast only as a descriptive reference, not a post-result selected comparator.

## Statistical analysis

For each candidate/horizon:
- accuracy and balanced accuracy;
- ROC-AUC and PR-AUC;
- Brier score and log loss;
- block/bootstrap uncertainty;
- chronological block performance;
- calibration by probability bin;
- abstention coverage and conditional accuracy where applicable.

For family-level inference:
- White Reality Check / SPA-style data-snooping correction where applicable;
- multiple-comparison adjustment across the registered Phase 7 candidate family;
- block bootstrap preserving temporal dependence;
- parameter/sensitivity checks only after the primary frozen results are recorded.

The multiple-testing principle is mandatory because searching a large universe can create apparently strong winners by chance; White/Sullivan/Timmermann specifically address this problem.

## Promotion rule

A Phase 7 candidate is only a research candidate if it:
- beats the frozen baseline out-of-sample;
- shows stable chronological performance;
- survives the declared multiple-testing/data-snooping control;
- does not rely on a single fragile regime;
- has acceptable calibration;
- passes independent tester review.

It is not a trading strategy until Phase 8 long-option execution with realistic Paytm Money brokerage, exchange charges, spread and slippage is completed, followed by Phase 9 robustness and Phase 10 fresh-forward validation.

## Literature anchors

- Sullivan, Timmermann & White, Data-Snooping, Technical Trading Rule Performance, and the Bootstrap, Journal of Finance (1999), DOI 10.1111/0022-1082.00163.
- Zhao & Cheng, Stock return prediction: Stacking a variety of models, Journal of Empirical Finance (2022), DOI 10.1016/j.jempfin.2022.04.001.
- Ranjan & Gneiting, Combining probability forecasts, Journal of the Royal Statistical Society: Series B (2010), DOI 10.1111/j.1467-9868.2009.00726.x; this motivates explicit calibration checks for probability combinations.
- Zhu & Zhu, Predicting stock returns: A regime-switching combination approach and economic links, Journal of Banking & Finance (2013), DOI 10.1016/j.jbankfin.2013.07.016.

## Required gates

1. Tester reviews this specification.
2. Developer resolves tester findings.
3. Tester approves frozen specification.
4. Developer implements.
5. Tester performs code gate.
6. Hosted regression gate.
7. Hosted empirical execution.
8. Independent artifact audit.
9. Only then may Phase 8 be considered.

No Phase 7 empirical execution is authorized by this document alone.
