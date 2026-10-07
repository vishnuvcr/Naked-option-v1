# Phase 4 Classical Technical Method Protocol

## Scope

Phase 4 tests Family B (Classical technical) from the pre-registered method registry. No hyperparameter search is permitted in this family gate. Every parameter below is fixed before the run.

The outputs are directional spot forecasts only. No option trade is promoted in Phase 4.

## Registered methods

| ID | Method | Fixed rule |
|---|---|---|
| B01 | SMA/EMA crossover | Bullish when EMA20 > EMA50; bearish when EMA20 < EMA50 |
| B02 | MACD | MACD(12,26) above signal EMA9 = bullish; below = bearish |
| B03 | RSI | RSI14 > 55 bullish; RSI14 < 45 bearish; otherwise neutral |
| B04 | Stochastic | %K(14) > %D(3) and %K > 50 bullish; %K < %D and %K < 50 bearish |
| B05 | ADX/trend strength | ADX14 >= 25 and +DI > -DI bullish; ADX14 >=25 and -DI > +DI bearish; else neutral |
| B06 | ATR/volatility breakout | Close > prior-20 high + 0.5*ATR14 bullish; close < prior-20 low - 0.5*ATR14 bearish |
| B07 | Donchian breakout | Close > prior-20 high bullish; close < prior-20 low bearish |
| B08 | Bollinger/range position | Close > upper band bullish; close < lower band bearish; otherwise sign of close-middle band, neutral at equality |
| B09 | VWAP deviation | BLOCKED_DATA in the current spot-only reference because volume is not available for a PIT-safe NIFTY VWAP |
| B10 | Opening-range breakout | Intraday only: after 09:30, close above 09:15-09:30 high bullish; below opening-range low bearish |
| B11 | CPR/pivot | Use prior session pivot P=(H+L+C)/3; bullish above prior-session R1; bearish below prior-session S1; otherwise neutral |
| B12 | Price-action swing structure | Bullish if close > prior-5 high and rolling 5-low is rising; bearish if close < prior-5 low and rolling 5-high is falling |
| B13 | Multi-timeframe trend alignment | Daily: EMA20 > EMA50 > EMA100 bullish and reverse bearish. Intraday: 20/50/100-minute EMA alignment at hourly decision times |

## Label definitions

Use the frozen Phase 3 positional horizons {1,2,3,5,10} sessions and intraday horizons {5,15,30,60,120} minutes.

For every feature, feature timestamp <= decision timestamp.

## Decision evaluation

For each method/horizon:
- sample n;
- positive rate;
- accuracy;
- balanced accuracy;
- ROC-AUC;
- PR-AUC;
- Brier score;
- log loss;
- confusion matrix;
- fixed probability-bin mean future return;
- 95% block-bootstrap accuracy interval.

The probability mapping is fixed:
- bullish -> 0.55;
- bearish -> 0.45;
- neutral -> 0.50.

No parameter may be tuned on these results.

## Family gate

Family B advances only after:
1. all B01-B13 rows are EXECUTED or explicitly BLOCKED_DATA/NOT_APPLICABLE;
2. no look-ahead or publication-timing breach;
3. all result denominators reconcile;
4. independent tester reproduces the family metrics;
5. any apparently strong results are preserved but are not promoted until Phase 9 robustness.

## No-premature-null rule

Failure of the classical family is a family result, not a research conclusion. Proceed through the remaining registered families under the same gates.
