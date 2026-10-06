# Phase 1 Literature Review and Evidence Map

## Review objective

Determine what has credible evidence for short-horizon index-direction prediction, what tends to fail after multiple-testing and transaction-cost controls, and which option-market/global/macro inputs deserve formal NIFTY tests.

## Evidence hierarchy

1. Official primary sources: NSE/NSE Indices, SEBI, RBI, broker tariff/rules.
2. Peer-reviewed finance/econometrics literature.
3. High-quality working papers/preprints with transparent methods/data.
4. Open-source implementations as replication targets, not as evidence.
5. Informal/vendor claims are hypothesis-only.

## Core methodological evidence

### 1. Lo — Adaptive Markets Hypothesis
URL: https://web.mit.edu/Alo/www/Papers/JIC2005_Final.pdf
Use: supports regime-dependent efficiency hypotheses; does not prove a trading edge.

### 2. White (2000) — Reality Check for Data Snooping
URL: https://doi.org/10.1111/1468-0262.00152
Use: controls the danger that the best result from a large search is a chance artifact.

### 3. Sullivan, Timmermann & White — Data-Snooping, Technical Trading Rule Performance, and the Bootstrap
URL: https://doi.org/10.1111/0022-1082.00163
Use: precedent for evaluating a large technical-rule universe with bootstrap adjustment.

### 4. Bailey et al. — Probability of Backtest Overfitting
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
Use: motivates combinatorial/selection-bias diagnostics after large method searches.

### 5. Bailey & López de Prado — Deflated Sharpe Ratio
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
Use: adjusts Sharpe interpretation for non-normality and selection bias.

### 6. Diebold & Mariano — Comparing Predictive Accuracy
URL: https://doi.org/10.1080/07350015.1995.10524599
Use: formal pairwise forecast-comparison test for dependent/non-Gaussian forecast errors.

### 7. Hsu, Hsu & Kuan — Stepwise SPA test
URL: https://www.sciencedirect.com/science/article/pii/S0927539810000022
Use: multiple-model predictive-ability testing without naïve data-snooping inference.

### 8. Technical trading revisited: false discoveries, persistence, transaction costs
URL: https://www.sciencedirect.com/science/article/pii/S0304405X1200116X
Use: baseline warning that apparent technical edges can disappear under data-snooping and costs.

### 9. Fang, Qin & Jacobsen — Technical market indicators: An overview
URL: https://www.sciencedirect.com/science/article/pii/S2214635014000495
Use: large indicator review; motivates breadth/volatility/sentiment indicator families while emphasizing data-snooping risk.

### 10. Technical analysis and stock-return predictability: aligned approach
URL: https://www.sciencedirect.com/science/article/pii/S1386418117300824
Use: supports testing richer technical-information combinations rather than isolated indicators.

### 11. 2025 — Accounting vs technical information
URL: https://www.sciencedirect.com/science/article/pii/S1042443125000976
Use: recent evidence that technical information can add short-horizon predictive content, but with higher turnover and implementation costs.

## Option-market information evidence

### 12. Ho & Hu — Option Return Predictability, A Machine-Learning Approach
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3073791
Use: broad option-universe evidence that option return predictors differ by moneyness/maturity; informs option-selection subtests.

### 13. Sensoy & Omole — Information content of order imbalance in the index options market
URL: https://www.sciencedirect.com/science/article/pii/S1059056021002367
Use: option order imbalance can contain incremental index information in some markets; motivates option-flow/OI tests.

### 14. Fahlenbrach & Sandås — Does information drive trading in option strategies?
URL: https://www.sciencedirect.com/science/article/pii/S037842661000097X
Use: caution: directional option flow may be less informative than volatility-related flow; prevents assuming call/put activity is automatically directional alpha.

### 15. Chordia, Kurov, Muravyev & Subrahmanyam — Index Option Trading Activity and Market Returns
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2798390
Use: puts/order flow can predict future index returns in specific U.S. samples, especially high-VIX/macroeconomic regimes; motivates regime-conditioned option-flow tests.

### 16. Joint modeling of call and put implied volatility
URL: https://www.sciencedirect.com/science/article/pii/S0169207009000041
Use: call/put IV interaction and asymmetry warrant explicit surface features.

### 17. 2026 — Retail option traders and the implied volatility surface
URL: https://www.sciencedirect.com/science/article/pii/S0304405X26000097
Use: recent evidence that retail demand can shift IV term structure, moneyness and call-put spreads; motivates retail-pressure/surface-state hypotheses.

### 18. 2026 — Predicting option prices from price history via machine learning
URL: https://link.springer.com/article/10.1007/s11147-026-09228-9
Use: confirms direct option-price forecasting is a distinct task from underlying-direction forecasting; informs option-specific validation.

## NIFTY/India-specific evidence

### 19. NSE India VIX methodology
URL: https://www.nseindia.com/static/products-services/indices-indiavix-index
Use: authoritative definition of India VIX as an option-implied 30-calendar-day expected-volatility measure.

### 20. NSE India VIX calculation methodology
URL: https://nsearchives.nseindia.com/web/sites/default/files/inline-files/India_VIX_comp_meth.pdf
Use: technical construction; relevant for PIT timing and IV-feature interpretation.

### 21. NSE historical contract-wise price/volume data
URL: https://www.nseindia.com/report-detail/fo_eq_security
Use: primary option contract OHLC/LTP/OI/volume/underlying source.

### 22. NSE all derivatives reports
URL: https://www.nseindia.com/all-reports-derivatives
Use: official source for participant-wise OI, participant-wise trading volume, FII derivatives statistics, UDiFF and daily reports.

### 23. NSE FII/FPI & DII activity
URL: https://www.nseindia.com/reports/fii-dii
Use: daily institutional-flow features; data are provisional and subject to later confirmation.

### 24. NSE historical index data
URL: https://www.nseindia.com/reports-indices-historical-index-data
Use: primary NIFTY index and index-history layer.

### 25. SEBI FY25–FY26 profitability study
URL: https://www.sebi.gov.in/reports-and-statistics/research/aug-2026/study-profitability-of-individual-traders-in-the-equity-derivatives-segment-fy25-fy26-_103835.html
Use: current regulatory evidence on retail derivatives outcomes; contextual risk evidence, not a predictor.

### 26. SEBI FY25–FY26 trading behaviour study
URL: https://www.sebi.gov.in/reports-and-statistics/research/aug-2026/study-trading-behaviour-of-individual-traders-in-the-equity-derivatives-segment-fy25-fy26-_103836.html
Use: current evidence on trading behavior and market participation.

### 27. Chakrabarti & Kumar — High-frequency return–implied-volatility relationship: Nifty and India VIX
URL: https://ideas.repec.org/a/jda/journl/vol.54year2020issue3pp53-68.html
Use: five-minute NIFTY/India-VIX dynamics and asymmetry; motivates intraday vol/return interactions.

### 28. On the relationship between implied-volatility index and equity-index returns
URL: https://doi.org/10.1108/JES-12-2013-0198
Use: India VIX/NIFTY asymmetry and calendar/expiry seasonality hypotheses.

### 29. Forecasting the direction of daily changes in India VIX using machine learning
URL: https://www.mdpi.com/1911-8074/15/12/552
Use: time-series ML on India VIX; supports regime-state predictors.

### 30. 2025/2026 India VIX/NIFTY spillover studies
URL: https://ideas.repec.org/a/spr/ijsaem/v16y2025i6d10.1007_s13198-025-02711-w.html
Use: VAR/DCC-GARCH evidence on changing NIFTY/India-VIX relations; informs regime-conditioned features.

### 31. 2026 — Open Interest Repositioning around Intraday Price-structure Breaks in NIFTY 50 Index Options
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7394780
Use: directly relevant recent hypothesis that PE-minus-CE OI shifts around intraday structure breaks may contain directional information. Treat as unverified until independently reproduced.

### 32. 2026 — NIFTY 50 direction with explainable XGBoost
URL: https://www.abacademies.org/articles/an-explainable-machine-learning-framework-for-predicting-nifty-50-stock-market-direction-using-xgboost-and-shap-analysis-18199.html
Use: recent NIFTY directional ML claim; replication required, with strong temporal and leakage audits.

### 33. 2025/2026 — News sentiment and NIFTY direction
URL: https://www.researchgate.net/publication/398712882_Can_News_Sentiment_Improve_Deep_Learning_Models_for_Nifty_50_Index_Forecasting
Use: recent evidence that sentiment may improve next-day NIFTY direction models; data timestamp integrity is a critical replication issue.

### 34. 2026 — Wavelet/cross-country influence for Indian market prediction
URL: https://www.researchgate.net/publication/406025875_A_Wavelet-Decomposed_D-Band_with_Constricted_PSO-Tuned_Light_Gradient_Boosting_Machine_for_Indian_Stock_Market_Prediction_with_Cross-Country_Market_Influence
Use: supports testing multi-scale + cross-country features, but complexity/selection bias must be controlled.

### 35. 2026 — NIFTY option VRP with realistic frictions
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6876580
Use: recent friction-focused NIFTY options evidence; mainly a warning that option premia do not automatically translate into tradeable retail profits.

## Open-source replication targets

### 36. NIFTY50 Market Direction Prediction
URL: https://github.com/AtomicHalifax/NIFTY50-Market-Direction-Prediction
Use: inspect feature engineering, model families and split conventions; treat reported metrics as unverified until replicated under this protocol.

## Literature synthesis

### What has relatively strong support

- Predictability can be state-dependent rather than stationary.
- Technical information may contain some short-horizon predictive content, but data snooping and turnover/costs are central threats.
- Option-market order flow and surface variables can contain information in some settings, but the sign and persistence of information are market- and regime-dependent.
- India VIX is a legitimate forward-looking volatility state variable, but volatility predictability is not equivalent to direction predictability.
- Cross-market and news information are plausible incremental predictors at short horizons if and only if their publication/trading-time alignment is correct.

### What remains doubtful

- A universal next-day NIFTY direction model with stable edge.
- Standalone CPR/max-pain/PCR heuristics without conditional tests.
- High headline classification accuracy translated directly into net option profits.
- Any strategy whose result depends on one threshold, one expiry, or one short historical interval.
- Any option-buyer edge that ignores IV level, theta, spread and execution.

### Phase 1 research implications

1. Direction labels must be evaluated at multiple horizons.
2. The primary statistical target should be calibrated probability and economically relevant expected option payoff, not raw accuracy alone.
3. Option surface and OI features are high-priority but require strict as-of validation.
4. Global markets and overnight information should be separated from intraday information.
5. Novel metrics should be tested only after strong baselines and multiple-testing accounting are established.
