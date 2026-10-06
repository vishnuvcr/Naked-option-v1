# Method Registry — NIFTY Direction

This is the finite pre-registered method universe. New methods may be added only as a protocol change before seeing the relevant final-test results.

## Family A — Baselines
A01 random 50/50
A02 no-change/persistence
A03 previous-bar sign
A04 moving-average directional rules
A05 buy-only trend benchmark

## Family B — Classical technical
B01 SMA/EMA crossovers
B02 MACD
B03 RSI
B04 stochastic
B05 ADX/trend-strength
B06 ATR/volatility breakout
B07 Donchian breakout
B08 Bollinger/range position
B09 VWAP deviation
B10 opening-range breakout
B11 CPR/pivot variants
B12 price-action swing structure
B13 multi-timeframe trend alignment

## Family C — Statistical/time-series
C01 logistic regression
C02 probit
C03 LDA/QDA
C04 AR/ARIMA-style return state models
C05 GARCH-family volatility-conditioned direction
C06 Markov switching
C07 hidden Markov models
C08 Bayesian dynamic/state-space models
C09 change-point detection
C10 Hawkes/self-exciting event features
C11 copula/dependence features
C12 survival/first-passage models

## Family D — Machine learning
D01 random forest
D02 extra trees
D03 gradient boosting
D04 XGBoost-style boosting
D05 LightGBM-style boosting
D06 CatBoost-style boosting
D07 calibrated stacking
D08 elastic-net
D09 GAM/splines
D10 kNN / prototype classifiers
D11 SVM
D12 controlled shallow neural networks
D13 sequence models
D14 temporal convolution
D15 transformer-style sequence model

## Family E — Regime and information
E01 Hurst with random-walk/surrogate controls
E02 multifractal/MFDFA diagnostics
E03 entropy/approximate entropy/sample entropy
E04 permutation entropy
E05 complexity/roughness
E06 mutual information
E07 transfer entropy / information flow
E08 regime-conditioned model switching
E09 volatility-state classifier
E10 trend/volatility regime matrix

## Family F — Options/derivatives
F01 ATM IV level
F02 IV percentile/rank
F03 put-call OI ratios
F04 OI change acceleration
F05 volume/OI pressure
F06 skew slope
F07 skew curvature
F08 term-structure slope
F09 IV-RV spread
F10 expected-move vs realized move
F11 gamma/vega proxy features
F12 option-implied directional pressure
F13 expiry/strike concentration
F14 max-pain as a weak feature only; never a standalone assumption
F15 option surface PCA/factors

## Family G — Cross-market/macro
G01 NIFTY vs SENSEX lead-lag
G02 NIFTY vs Bank Nifty leadership
G03 sector leadership breadth
G04 S&P 500 lead-lag
G05 Nasdaq lead-lag
G06 Nikkei/Hang Seng lead-lag
G07 SGX/GIFT-style overnight NIFTY proxy where historical integrity allows
G08 Cboe VIX
G09 USD/INR
G10 US 10Y / Indian yields
G11 gold
G12 crude oil
G13 global risk-on/risk-off composite
G14 FII/FPI flows
G15 DII flows
G16 India VIX
G17 market breadth / advance-decline
G18 calendar / expiry / holiday effects

## Family H — News/sentiment/events
H01 headline sentiment
H02 news volume shocks
H03 macro event indicators
H04 central-bank/event windows
H05 earnings/corporate-action aggregation
H06 gap/news interaction

## Family I — Novel metrics
I01 multi-scale directional pressure index
I02 cross-market lead-lag pressure score
I03 volatility-adjusted trend persistence score
I04 option-surface directional asymmetry score
I05 regime transition pressure index
I06 liquidity-friction-adjusted signal quality
I07 probability-of-move-vs-premium efficiency score
I08 entropy-weighted ensemble confidence
I09 abstention/edge-density score
I10 composite “Direction Conviction State” score

## Family J — Ensembles/policies
J01 simple voting
J02 probability averaging
J03 weighted ensemble from training only
J04 stacking with nested CV
J05 mixture-of-experts by regime
J06 conformal/uncertainty-aware abstention
J07 cost-aware decision thresholding
J08 option-break-even-aware policy

## Exhaustion definition

The method universe is exhausted when every registry row is either (a) tested and reported, (b) blocked by a documented data limitation, or (c) rejected by a prior gate with a reusable reason.
