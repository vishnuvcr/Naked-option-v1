# Phase 3 Option Break-Even Protocol

## Purpose

Prevent the common error of treating a correct NIFTY direction forecast as automatically profitable for a long option.

For each candidate long CE/PE:
1. record entry premium and size;
2. record all point-in-time costs;
3. model adverse spread/slippage;
4. select an exit rule fixed before testing;
5. calculate exact realized net P&L.

## Minimum cost layers

- brokerage;
- STT;
- exchange transaction charges;
- SEBI fee;
- GST;
- stamp duty;
- bid/ask or conservative slippage proxy;
- latency/missed-fill penalty where observable.

## Break-even quantities

### Premium break-even

`exit_price_break_even = entry_price + per_unit_total_cost + per_unit_slippage`

### Underlying first-order break-even

Only where delta is known:

`spot_move_break_even ≈ total_option_break_even_cost / |delta_entry|`

This is a diagnostic, not the execution rule.

### Exact option break-even

The primary metric is the actual option price required for zero net P&L under the complete cost model.

## Cost scenarios

All baselines are evaluated under:
- optimistic;
- base;
- adverse;
- extreme.

The exact numeric statutory schedule is versioned separately and may vary by historical period.

## Position constraint

Only one long option position per signal in the primary baseline:
- BUY CE
- BUY PE
- NO TRADE

No short legs.
