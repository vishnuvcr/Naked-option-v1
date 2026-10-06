# Phase 3 Baseline Protocol

## Research questions

1. Is NIFTY direction measurably predictable at any pre-registered horizon before considering complex models?
2. Which simple baselines survive chronological out-of-sample testing?
3. Does any baseline materially outperform a 50/50 or persistence benchmark?
4. Does thresholding/abstention improve calibration without creating selection bias?
5. Does a spot-direction edge survive conversion to a long CE/PE economic label after costs?

## Baselines

### B0 Random
Deterministic 50/50 benchmark with fixed seed for reproducibility.

### B1 Persistence
Predict the next direction as the last observed direction.

### B2 Previous-session sign
Predict future sign from previous session return.

### B3 Gap sign
For intraday:
- sign of open minus previous close.

### B4 Intraday momentum
Sign of the most recent 5/15/30-minute return.

### B5 Moving-average state
Price versus a fixed 5/20-observation moving-average pair. No period search is allowed in Phase 3.

### B6 Range-position state
Current price relative to the rolling prior-20-observation high/low range, computed only from observations available at the decision timestamp. No future bar may enter the range.

### B7 Volatility-conditioned sign
Use current rolling 20-observation volatility percentile over a fixed trailing 252-observation history. Frozen rule: below the 33rd percentile, use persistence 0.55/0.45; between 33rd and 67th, use 0.50/0.50; above the 67th, invert persistence to 0.45/0.55. No cutpoint optimization. The regime counts must be reported separately.

### B8 Calendar-only
Weekday, month-end and holiday-adjacent indicators, tested as probability shifts, not deterministic trade rules. The current Phase 3 baseline uses weekday only; it must not be described as an expiry-day effect.

### B9 Global overnight
Equal-weight mean of standardized previous-available daily closes for S&P 500, Nasdaq Composite, Nikkei 225 and Hang Seng. Each series is standardized using only the training history; a market is omitted for that decision if its local close was not yet available before the NIFTY decision.

### B10 Breadth
`breadth = (advances - declines) / (advances + declines)`, using only breadth observations available before the decision timestamp. Missing denominator rows are NO FEATURE, not zero.

### B11 Logistic baseline
Fixed regularized logistic regression. Preprocessing and model specification are frozen: feature scaler fit on training fold only; L2 penalty; C=1.0; solver=`liblinear`; max_iter=1000; class_weight=None. No hyperparameter sweep in Phase 3. All baseline feature periods, formulas and model parameters above are frozen before any result is inspected.

Feature set:
- last return;
- rolling volatility;
- gap;
- breadth;
- India VIX when PIT-safe;
- global overnight composite when PIT-safe.

No hyperparameter sweep in Phase 3.

## Statistical reporting

For each horizon:
- class frequencies;
- accuracy;
- balanced accuracy;
- ROC-AUC where binary labels are non-degenerate;
- PR-AUC;
- Brier score;
- log loss;
- calibration slope/intercept;
- confusion matrix;
- mean future return by predicted probability bin;
- uncertainty interval via block bootstrap.

## Economic reporting

For long-option conversion:
- trade count;
- net expectancy;
- median P&L;
- win rate;
- payoff ratio;
- max drawdown;
- ES95/ES99;
- return on premium at risk;
- cost sensitivity.

No strategy is declared successful from directional accuracy alone.
