# Data Source Registry

## Primary-source preference

NSE/NSE Indices, BSE, SEBI, RBI and other official publications are preferred for market/regulatory facts. Free/open sources are exhausted before paid-source declarations.

## Data layers

| Layer | Examples | Role |
|---|---|---|
| NIFTY underlying | NSE/NSE Indices | price/returns |
| NIFTY options | NSE F&O archives / option datasets | contract prices, OI, IV |
| India VIX | NSE | volatility regime |
| FII/FPI/DII | NSE/NSDL/SEBI | flows |
| Breadth | NSE | market participation |
| Global indices | official/index-provider or robust free sources | overnight lead-lag |
| Cboe VIX | Cboe | global risk regime |
| FX | RBI / free market sources | USD/INR |
| Rates | RBI / official government | discount-rate regime |
| Gold/crude | robust free sources | cross-asset risk |
| News | official feeds / reputable archives | event/sentiment |
| Corporate actions | exchange/company filings | adjusted features |
| Calendar | NSE/official | expiry/holiday/event timing |

## Composite-source rule

When a source has missing or inconsistent observations, combine only after:

1. source-level validation;
2. overlap consistency checks;
3. explicit precedence rules;
4. row-level provenance;
5. immutable snapshot hashing.

## Prior-project data evidence

The Project's earlier research reports successful access to a large NIFTY option dataset with roughly 2.86 million observations and more than 1.5k observation dates, but this is treated as an input to be independently revalidated in the current repo.

## Active Phase 3 intraday research reference

The current Phase 3 intraday reference is thetrademarkk/india-index-options-1m, using the pinned index/NIFTY.parquet spot series. It is CC-BY-NC-4.0 research data, not a canonical exchange feed. It must pass official NSE overlap checks before use, and its timestamps are treated as research-reference observation times rather than retroactively assigned publication times.
