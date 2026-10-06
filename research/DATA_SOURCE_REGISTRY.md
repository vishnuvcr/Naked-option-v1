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
