# Execution Cost Model

The primary strategy is long NIFTY CE/PE only.

The exact statutory rates must be sourced and versioned before Phase 8. Do not hard-code a historical brokerage rule as timeless.

## Required cost components

- Broker brokerage under Paytm Money rules applicable to the tested product and period.
- STT on the applicable option transaction side(s).
- Exchange transaction charges.
- SEBI turnover fee.
- GST on applicable brokerage/transaction components.
- Stamp duty where applicable.
- Bid/ask spread.
- Market-impact/slippage proxy.
- Decision-to-fill latency.
- Partial fill/missed fill handling where data permit.

## Stress matrix

At minimum:

1. optimistic;
2. base;
3. adverse;
4. extreme.

For each, report break-even premium movement and strategy performance.

## No-free-lunch execution rule

A spot directional prediction is not automatically an executable option-buying signal. A trade is valid only when predicted underlying move, option delta/gamma/vega/theta effects and all costs support positive expected net payoff.
