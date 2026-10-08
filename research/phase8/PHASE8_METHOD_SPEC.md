# Phase 8 — Long-Option Execution Research Specification

## Status

**DRAFT FOR INDEPENDENT TESTER GATE — NO EMPIRICAL EXECUTION AUTHORIZED**

Phase 8 translates the frozen Phase 7 probability forecasts P01–P10 into long NIFTY CE/PE trades. The Phase 7 forecasts are treated as fixed inputs; no Phase 7 method, label, probability rule, or holdout boundary may be changed because of Phase 8 results.

The phase is finite. It has defined data, execution, cost, option-selection and exit universes. Any amendment requires an explicit developer/tester gate before empirical execution.

## Research questions

**RQ8.1.** Does any frozen Phase 7 forecast produce positive *net* long-option expectancy after brokerage, statutory charges, spread and slippage?

**RQ8.2.** Does a spot-direction forecast retain economic value after mapping it to actual NIFTY CE/PE premium paths, including theta, IV changes and convexity?

**RQ8.3.** Which pre-registered contract-design factors matter most: absolute delta, time-to-expiry (DTE), and exit rule?

**RQ8.4.** Are any positive results stable across chronological blocks, volatility/regime states, liquidity tiers and the four cost scenarios?

**RQ8.5.** How often does a forecasted direction fail the option-level break-even requirement once the full round-trip cost is included?

**RQ8.6.** Are apparent option-level winners concentrated in a small number of trades, expiry days, low-liquidity contracts or unusually favorable execution assumptions?

## Aim

To determine whether the frozen Phase 7 directional forecasts can be translated into a reproducible, cost-aware long NIFTY option strategy without look-ahead, hindsight contract selection or unrealistic fills.

## Objectives

1. Rebuild a point-in-time NIFTY option contract panel from free, auditable sources before any paid source is considered.
2. Validate historical contract existence, strike, expiry, lot size, option type, OHLCV, OI and timestamps.
3. Test every frozen Phase 7 forecast cell against a fixed finite option-selection and exit universe.
4. Model current and historical Paytm Money brokerage/tariff versions and official statutory charges.
5. Model bid/ask, slippage, latency and missing-fill risk explicitly.
6. Report gross and net option P&L, break-even moves, drawdowns, tail losses, turnover, win/loss distribution and chronological stability.
7. Produce a finite shortlist for Phase 9 only; Phase 8 does not declare a strategy final.

## Frozen input boundary

Phase 7 Run #654 is the accepted technical forecast artifact. No P01–P10 candidate may be removed, retuned, reweighted or reselected using Phase 8 performance.

The Phase 7 untouched holdout remains protected.

The Phase 8 decision timestamp is the timestamp attached to the stored Phase 7 forecast. No option observation after that timestamp may be used to determine whether a contract is selected.

## Forecast-to-trade rule

For every non-abstaining probability p:

- p > 0.50 → long CE;
- p < 0.50 → long PE;
- p = 0.50 → no trade.

P05 uses its frozen [0.45, 0.55] abstention band; P06 uses its frozen [0.40, 0.60] abstention band.

One strategy cell may have at most one open trade at a time. No pyramiding or overlapping self-funded positions is permitted within a cell.

Primary analysis is one-lot NIFTY option exposure. Position scaling is deferred to later risk work.

## Frozen option contract-design universe

At each decision timestamp, select from contracts that are demonstrably listed and tradable at that timestamp.

### Delta targets

Three absolute-delta targets are evaluated:

- 0.40;
- 0.50;
- 0.60.

For a CE the target delta is positive; for a PE the absolute delta is used.

Preferred delta source order is fixed:

1. point-in-time exchange/vendor delta if present and timestamped;
2. Black–Scholes delta calculated only from information available at the decision timestamp;
3. strike/moneyness fallback only when the first two are unavailable, explicitly flagged as a non-Greek fallback.

No result-dependent choice between these sources is allowed.

### DTE buckets

DTE is the number of exchange trading sessions from decision date to the selected contract expiry.

Four fixed buckets:

- D0: 0–1 sessions;
- D1: 2–5 sessions;
- D2: 6–10 sessions;
- D3: 11–21 sessions.

A contract is eligible only if its expiry is strictly after the planned exit timestamp. No position may be intentionally carried through expiry in the primary execution tests.

### Contract selection

For each delta/DTE pair, choose the contract whose absolute delta is closest to the target among eligible strikes. Ties are broken by:

1. higher contemporaneous liquidity;
2. smaller absolute moneyness;
3. lower strike distance;
4. deterministic contract identifier ordering.

Selection must be based only on information available by the decision timestamp.

## Entry and exit execution

### Entry

The first executable option quote/bar at or after the decision timestamp plus a fixed latency of one minute is the earliest permitted entry.

A same-bar option observation cannot be used to create the fill.

If no valid observation exists within the registered entry tolerance, the signal is recorded as **NO_FILL**, not backfilled.

### Exit

Four fixed exit policies are evaluated:

- X0: exit at forecast horizon H;
- X1: +50% premium take-profit, otherwise exit at H;
- X2: -35% premium stop-loss, otherwise exit at H;
- X3: 25% trailing stop from the highest observed premium after entry, otherwise exit at H.

The position is also forcibly closed before expiry if the planned horizon would cross expiry.

When option OHLC data cannot determine whether both a stop and target were hit within the same bar, the conservative ordering is used: the stop is assumed to occur first for a long option.

No target, stop, trailing percentage or horizon may be tuned after observing Phase 8 results.

## Liquidity and data-quality rules

Primary eligibility requires:

- contract exists in a point-in-time instrument/contract master;
- positive option premium;
- option type, strike and expiry are unambiguous;
- no negative/zero OI when OI is used as a filter;
- entry and exit observations pass timestamp ordering;
- no stale observation beyond the registered tolerance;
- no duplicate contract/timestamp records after source reconciliation.

The primary report must show fill rate, missing-fill rate and data-gap rate by signal/configuration.

A cell with material unresolved data gaps is not promoted merely because its P&L is high.

## Execution-price hierarchy

### Quote-backed track

When valid bid/ask quotes exist:

- buy at ask;
- sell at bid;
- add explicit latency/slippage stress on top;
- preserve the observed quote timestamp and source provenance.

This is the only track that may be labeled **quote-executable**.

### OHLC/proxy track

When bid/ask history is unavailable:

- use a conservative price proxy from the registered OHLC bar;
- apply explicit synthetic spread and slippage assumptions;
- flag the result **non-quote-executable**.

No OHLC-only backtest may be described as having historical bid/ask execution.

## Frozen cost model

All costs are applied per trade and per historical date using the applicable rate/tariff version.

### Brokerage

The current Paytm Money F&O FAQ states ₹10 brokerage for each unique F&O order that gets executed. The current backtest configuration will therefore use ₹10/order for 2026-era observations, while historical observations must use a dated Paytm tariff version rather than back-applying the current rate.

Where an exact historical Paytm tariff cannot be independently verified, the trade remains reported under an explicit conservative brokerage stress rather than silently assuming the current tariff.

### Statutory and exchange charges

The dated cost engine must use official rates rather than one timeless hard-coded constant.

For current 2026 observations, the registered sources include:

- STT on sale of an option: 0.15% of option premium from 1 April 2026;
- NSE equity-option transaction charge: ₹3,552 per crore of traded premium value per side from 1 March 2026;
- NSE IPFT contribution: ₹0.01 per crore per side from 1 March 2026;
- SEBI turnover fee: 0.0001% of transaction value;
- equity-option stamp duty: 0.003% on the buyer side;
- GST: 18% on the broker service/taxable charge base, with statutory recoveries treated according to the applicable pure-agent/contract-note rules.

Historical rates are versioned by effective date from official NSE/SEBI/Paytm sources.

### Execution stress scenarios

Four fixed scenarios are reported:

- **C0 optimistic:** observed quote spread only; zero incremental slippage;
- **C1 base:** observed quote spread plus 0.25% of premium per leg incremental slippage;
- **C2 adverse:** observed quote spread plus 0.50% per leg;
- **C3 extreme:** observed quote spread plus 1.00% per leg.

For OHLC/proxy data, synthetic spread is separately reported. Proxy results are never upgraded to quote-executable status.

## Lot size and contract metadata

Lot size is a point-in-time field. It must be taken from the exchange instrument/contract master rather than hard-coded.

The NSE revised NIFTY 50 lot size from 25 to 75 for new index derivative contracts introduced from 20 November 2024; subsequent historical contract records therefore require date-aware lot-size handling. The implementation must use the applicable contract's own lot-size snapshot.

Expiry day, strike scheme, tick size and contract availability are also read from date-appropriate exchange metadata.

## Primary P&L

For a one-lot long option:

`gross_pnl = (exit_fill - entry_fill) * lot_size`

`net_pnl = gross_pnl - brokerage - exchange_charges - IPFT - STT - SEBI_fee - stamp_duty - GST - incremental_slippage - other_applicable_charges`

Every component must be stored separately.

Net return metrics are reported both on:

1. initial premium capital at risk; and
2. one-lot rupee P&L.

No leverage is assumed.

## Break-even analysis

For every entry, compute the option premium break-even exit and equivalent underlying move needed to cover the *full* round-trip cost.

The primary break-even output is based on the actual traded contract, not an abstract Black–Scholes approximation.

The Black–Scholes calculation is used only for contract selection/fallback diagnostics.

## Statistical analysis in Phase 8

Phase 8 is primarily an economic/execution screening phase; it does not override the formal Phase 9 statistical gate.

For each cell report:

- trade count and fill count;
- mean/median net P&L;
- mean/median net return on premium;
- hit rate;
- payoff ratio and profit factor;
- cumulative P&L;
- maximum drawdown;
- worst trade and 1%, 5% tail losses;
- Sortino and Sharpe where the return series supports them;
- chronological-block results;
- performance by volatility/regime state;
- performance by delta/DTE/exit configuration;
- gross versus net cost decomposition;
- sensitivity to C0–C3 costs.

A moving/block bootstrap confidence interval is used for trade-sequence metrics where dependence requires it.

Phase 9 will apply the declared family-level data-snooping controls across the complete execution universe, including all signal/configuration cells that were actually tested.

## Phase 8 → Phase 9 shortlist rule

A cell may be forwarded to Phase 9 only when all conditions below hold:

1. at least 100 completed trades;
2. positive base-scenario net expectancy;
3. positive cumulative net P&L in the base scenario;
4. at least 60% of chronological evaluation blocks are non-negative;
5. no unresolved data-lineage or timestamp breach;
6. its result survives the full registered cost decomposition;
7. it is not dependent on one or a few anomalous fills or a single expiry period.

This shortlist rule is fixed before empirical execution and is not a significance test. Phase 9 remains the final promotion/statistical gate.

## Phase 8 deliverables

1. immutable composite options dataset with row-level provenance;
2. point-in-time contract master snapshots;
3. cost-rate/tariff table with effective dates;
4. reproducible option-selection/execution engine;
5. regression tests for timestamp order, lot-size changes, expiry eligibility, charge arithmetic and stop/target ordering;
6. complete P01–P10 × layer × horizon × delta × DTE × exit results;
7. fill/missing-data audit;
8. cost decomposition tables and stress charts;
9. Phase 8 tester gate and error log;
10. Phase 9 candidate shortlist, if any.

## Phase 8 acceptance boundary

No strategy is accepted in Phase 8 alone.

A Phase 8 result may advance only to the Phase 9 robustness/statistical gate. Final strategy promotion still requires Phase 9, untouched fresh-forward verification in Phase 10, tester approval and the conjunctive promotion criteria in `research/RESEARCH_PLAN.md`.

### OHLC/proxy spread rule (frozen)

For Q1 OHLC/proxy rows, a synthetic half-spread is applied independently at entry and exit:

- C0: max(1 tick, 0.50% of premium) per side;
- C1: max(1 tick, 1.00% of premium) per side;
- C2: max(1 tick, 2.00% of premium) per side;
- C3: max(1 tick, 4.00% of premium) per side.

The option tick size is taken from the point-in-time contract metadata. The synthetic spread is not claimed to reproduce an observed historical quote; it is a conservative stress proxy. Incremental slippage from the C0–C3 scenario is then added separately. A Q1 result therefore remains **non-quote-executable**.

## Phase 7 forecast reconstruction gate

The accepted Run #654 aggregate artifact does not itself store every row-level P01–P10 probability and decision timestamp. Phase 8 therefore requires a deterministic reconstruction step **before option P&L is generated**.

The reconstruction must:

1. use the exact Run #654 developer commit and the frozen Phase 6/7 inputs;
2. execute the same P01–P10 definitions, training schedule, blocked-predictor handling and seeds;
3. preserve the original Phase 7 chronological horizon/layer boundaries;
4. output one row per decision timestamp with P01–P10 probabilities and abstention state;
5. compare aggregate metrics against the immutable Run #654 artifact for all 100 cells;
6. fail closed if any metric differs beyond the pre-registered numerical tolerance;
7. hash and archive the reconstructed prediction dataset before option execution.

The reconstruction is a reproducibility operation, not a new model. No Phase 8 result may be used to alter Phase 7 code or reconstruction parameters.


## Reproducibility clarifications added after tester review

### Liquidity tie-break
Liquidity is strictly pre-decision:
- intraday: sum of option contracts traded in the prior 15 complete one-minute bars ending before the decision timestamp;
- daily: prior NSE trading-session option volume.
No entry-bar/future volume is permitted. Higher prior-volume value wins the first contract-selection tie-break.

### Entry and exit tolerances
- intraday entry: search only t+1 and t+2 one-minute observations after the fixed one-minute latency;
- daily entry: search the next trading session from 09:16 through 09:30 IST after the fixed one-minute latency convention;
- intraday planned exit: use the first valid observation at or after the target timestamp and within +2 minutes;
- daily planned exit: use the first valid observation at or after the target timestamp and within +15 minutes of the next-session-aligned target.
If a valid exit observation is still unavailable within the window, the trade is marked `EXIT_LIQUIDITY_FAIL`, liquidated at zero premium for the conservative accounting view, and the cell's data-quality/fill statistics record the event.

### Data-quality thresholds
Before empirical promotion:
- duplicate contract/timestamp rows: 0 allowed;
- invalid/non-positive premium: 0 allowed among executable rows;
- missing critical contract metadata: <=0.5%;
- stale observation rate beyond the registered windows: <=1%;
- entry no-fill rate: <=10%;
- exit-liquidity-failure rate: <=1%.
A cell exceeding a threshold is `DATA_QUALITY_FAIL` and cannot enter the Phase 9 shortlist. Signals with no entry fill remain logged as `NO_FILL` rather than being silently removed.

### Historical brokerage fallback
For any historical date for which a dated Paytm tariff cannot be independently verified, the cost engine uses a fixed conservative fallback of **₹20 per executed order**, marked `BROKERAGE_FALLBACK`. The 2026 verified primary rate remains ₹10 per unique executed F&O order. No other rate may be inferred from strategy outcomes.

### Delta/Black–Scholes fallback
If an audited point-in-time delta is unavailable, Black–Scholes delta uses:
- underlying: the latest NIFTY value available at/before decision time;
- volatility: point-in-time option IV from the selected source, otherwise an IV reconstructed only from information at/before decision time;
- risk-free rate: latest 91-day Government of India Treasury-bill yield available from the RBI data source on/before decision date;
- dividend yield: 0 for the delta-ranking approximation;
- European option formula;
- no stochastic-volatility/model fitting.
If any required input is unavailable, fall back to strike/moneyness ranking and flag the contract as `MONEYNESS_FALLBACK`. The fallback is never selected from future performance.

### Forecast reconstruction tolerance
For the Run #654 reconstruction gate:
- integer counts and sample sizes must match exactly;
- continuous aggregate metrics must match the Run #654 artifact within **1e-9 absolute tolerance**;
- any mismatch beyond tolerance fails closed and blocks option execution.

### Registered execution universe
The complete theoretical Phase 8 grid is exactly:
**100 forecast cells × 3 delta targets × 4 DTE buckets × 4 exit policies = 4,800 configuration cells.**
Every configuration receives one status: `EXECUTED`, `INELIGIBLE`, `DATA_QUALITY_FAIL`, or `NO_PREDICTION`. Ineligible configurations require a deterministic reason such as no qualifying expiry/strike; they are not removed after observing P&L.

### Anomaly-concentration rule
To pass the Phase 8→Phase 9 economic screen:
- define k = max(1, ceil(0.01*n_completed));
- after removing the k highest-net-P&L completed trades, base-case mean net P&L per completed trade must remain >0;
- no single expiry calendar month may contribute >50% of total positive base-case net P&L.

### Chronological option blocks
Chronological performance blocks are fixed at **20 NSE trading sessions** for both daily and intraday layers. Partial terminal blocks are retained only if they contain at least one completed trade; otherwise they are omitted from performance statistics but retained in the execution audit.

### Overlapping signals
When a signal occurs while the same strategy/configuration cell already has an open position, the signal is not queued. It is logged as `OVERLAP_SKIPPED` and does not alter the open trade.


### IV reconstruction solver convention
When a point-in-time IV is unavailable but a premium observation is available, IV is recovered from the European Black–Scholes price equation using a deterministic bisection solver over volatility `[1e-6, 5.0]`, 80 iterations, with the model price checked for bracketing/no-arbitrage validity first. Failure to bracket a unique solution produces `MONEYNESS_FALLBACK`; no future price is used.

### Venue/source scope
NIFTY 50 index options are primarily validated against NSE records. BSE derivatives data are audited as a secondary venue/source check where the same NIFTY contract history exists, but BSE data cannot replace the controlling NSE contract metadata for an NSE-execution study.
