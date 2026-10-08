# Phase 8 — Literature and Evidence Review

## Scope

Phase 8 concerns the translation of directional forecasts into long index-option trades. The review therefore emphasizes option transaction costs, bid/ask effects, data snooping, and economic—not merely statistical—significance.

## Core evidence

### Trading frictions in options

Hong, Sung and Yang (2018), *On profitability of volatility trading on S&P 500 equity index options: the role of trading frictions*, International Review of Economics & Finance, DOI 10.1016/j.iref.2017.07.012, reports that profitability changes materially once bid-ask spreads and trading frictions are incorporated. This supports treating execution costs as a first-order research variable rather than an afterthought.

Jha and Kalimipalli (2010), *The economic significance of conditional skewness in index option markets*, Journal of Futures Markets 30(4):378–406, DOI 10.1002/fut.20414, finds that trading costs materially weaken option-strategy profitability. Phase 8 therefore reports gross and net P&L separately and uses multiple cost scenarios.

Do, Foster and Gray (2016), *The Profitability of Volatility Spread Trading on ASX Equity Options*, Journal of Futures Markets, DOI 10.1002/fut.21729, emphasizes that apparent option-strategy profits can depend strongly on optimistic spread execution. Phase 8 consequently distinguishes quote-backed execution from OHLC-only proxy execution.

The broader option-return literature also motivates explicit spread adjustment and liquidity controls rather than evaluating raw premium changes alone.

### Data snooping and multiple comparisons

White (2000), *A Reality Check for Data Snooping*, Econometrica 68(5):1097–1126, DOI 10.1111/1468-0262.00152, provides the canonical framework for testing whether the best result found within a specification search has predictive superiority after accounting for data snooping.

Sullivan, Timmermann and White (1999), *Data-Snooping, Technical Trading Rule Performance, and the Bootstrap*, Journal of Finance 54:1647–1691, DOI 10.1111/0022-1082.00163, demonstrates the value of family-level bootstrap inference over a full candidate universe.

Hansen's Superior Predictive Ability framework and later financial-data-snooping work motivate the Phase 9 use of SPA/Reality-Check/PBO/DSR-style controls after Phase 8 execution results are available.

## Evidence implications for the present study

1. Directional accuracy alone is insufficient; option convexity, theta, volatility repricing and execution friction can reverse the economic sign.
2. A realistic backtest must use the actual option contract path and not a synthetic payoff-only approximation when historical option prices exist.
3. Spread and slippage assumptions must be visible and stressed.
4. The candidate universe must be frozen before inspecting results.
5. The best-looking execution configuration cannot be treated as independently significant without correcting for the search over signal, contract and exit configurations.
6. Quote-backed and OHLC-proxy evidence must be clearly separated.

## Registered external sources used for Phase 8 cost governance

- Paytm Money F&O FAQ: current brokerage charge is ₹10 for each unique executed F&O order.
- NSE STT page: from 1 April 2026, option-sale STT is 0.15% of option premium.
- NSE Finance & Accounts circular NSE/FA/73061 dated 27 February 2026: from 1 March 2026, NIFTY/equity-option exchange transaction charge is ₹3,552 per crore of traded premium value per side, with NSE IPFT contribution ₹0.01 per crore per side.
- NSE SEBI/levies page: SEBI turnover fee 0.0001%, equity-option stamp duty 0.003% buyer, GST 18% for stock-broker services.
- NSE October 18, 2024 circular NSE/FAOP/64625: NIFTY 50 market lot revised from 25 to 75 for new contracts from 20 November 2024.
- NSE NIFTY 50 product specification: current NIFTY 50 index-option expiry is Tuesday, adjusted to the previous trading day when Tuesday is a holiday.
- NSE settlement mechanism: index options are European-style and cash settled; final exercise is automatic at expiry.

## Literature-gate disposition

The literature supports the Phase 8 design choices but does not establish a NIFTY-specific profitable strategy. No empirical hypothesis is accepted from literature alone.

## References

1. White, H. (2000). A Reality Check for Data Snooping. Econometrica, 68(5), 1097–1126. DOI: 10.1111/1468-0262.00152.
2. Sullivan, R., Timmermann, A., & White, H. (1999). Data-Snooping, Technical Trading Rule Performance, and the Bootstrap. Journal of Finance, 54, 1647–1691. DOI: 10.1111/0022-1082.00163.
3. Hong, S., Sung, S.-I., & Yang, S. (2018). On profitability of volatility trading on S&P 500 equity index options: the role of trading frictions. International Review of Economics & Finance. DOI: 10.1016/j.iref.2017.07.012.
4. Do, B., Foster, G., & Gray, S. (2016). The Profitability of Volatility Spread Trading on ASX Equity Options. Journal of Futures Markets. DOI: 10.1002/fut.21729.
5. Jha, R., & Kalimipalli, M. (2010). The economic significance of conditional skewness in index option markets. Journal of Futures Markets, 30(4), 378–406. DOI: 10.1002/fut.20414.
