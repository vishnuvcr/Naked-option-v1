# Phase 3 Label Protocol — NIFTY Direction and Long-Option Economic Labels

## Purpose

Freeze the target variables before any model selection or optimization.

## Intraday decision grid

Default decision timestamps:
- 09:30 IST
- 10:00 IST
- 11:00 IST
- 12:00 IST
- 13:00 IST
- 14:00 IST
- 15:00 IST

A future horizon may only use observations strictly after the decision timestamp.

## Intraday horizons

Primary:
- 5 minutes
- 15 minutes
- 30 minutes
- 60 minutes
- 120 minutes

Secondary:
- same-day close
- open-to-close
- close-to-close where the decision timestamp is end-of-day

## Positional horizons

- +1 trading session
- +2
- +3
- +5
- +10 sessions

## Direction labels

### Binary sign label

`Y_dir = sign(log(S_future / S_decision))`

No tie-breaking by future information. Exact zero is class 0 and is handled separately.

### Thresholded direction label

`Y_thr(k) = sign(R_future)` only when `|R_future| > k * sigma_reference`; otherwise class 0.

Pre-registered `k` grid:
- 0.25
- 0.50
- 0.75
- 1.00

`sigma_reference` is the rolling standard deviation of the preceding 20 same-frequency decision-to-decision log returns, computed without annualization and without any observations at or after the decision timestamp. The 20-observation window is fixed for Phase 3 and is not tuned.

### Triple-barrier label

- upper barrier = +k * sigma_reference;
- lower barrier = -k * sigma_reference;
- time barrier = the chosen horizon;
- sigma_reference is the same fixed 20-observation same-frequency standard deviation described above;
- barriers are frozen at the decision timestamp and are never updated after entry.

The class is the first barrier hit, or 0 if neither is hit.

## Option-economic labels

Direction-only prediction is not sufficient for a long-option strategy.

For a candidate call/put observed at the decision time:

`net_pnl = (exit_price - entry_price) * lot_size - total_round_trip_costs - total_slippage_costs`

The economic label is:
- +1 when net P&L > 0;
- 0 when net P&L = 0;
- -1 when net P&L < 0.

For paired CE/PE candidates:
- +1 call opportunity if CE net P&L > 0 and dominates PE;
- -1 put opportunity if PE net P&L > 0 and dominates CE;
- 0 otherwise.

This label is evaluated separately from spot-direction accuracy.

## Delta-adjusted break-even diagnostic

When a point-in-time option delta is available:

`required_underlying_move ≈ (entry_premium + per_unit_cost) / |delta|`

This is a first-order diagnostic only. It must never replace the exact observed option-P&L label because gamma, theta, IV changes and nonlinear pricing matter.

## Abstention label

A model may choose:
- CALL
- PUT
- NO TRADE

NO TRADE is valid only when explicitly pre-registered and evaluated on the same out-of-sample data.

## Leakage rules

- The label horizon must begin strictly after the decision timestamp.
- Contract identity must exist at decision time.
- Entry premium must be a time-stamped observable at/after decision time.
- Exit price must not be used as a feature.
- Normalization, volatility estimates and thresholds are fit only on training history.
- Future expiry selection is prohibited.

## Baseline data requirements

Phase 3 first tests labels on canonical NIFTY daily data and a validated 1-minute research-reference track. It does not fit complex models.
