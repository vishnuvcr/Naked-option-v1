# Legacy Strategy Intake — Tradetron + Prior GitHub Research

## Purpose

This file registers user-supplied Tradetron strategies and relevant prior GitHub research as **research inputs**, not as accepted final strategies.

The final research constraint remains: **NIFTY naked long option buying only** (long CE or long PE, intraday and positional). Any legacy strategy containing a short option, spread, short straddle/strangle, ratio, calendar, iron condor, or other short exposure is therefore not directly eligible for the final executable strategy. Its timing, state machine, premium, delta, regime and exit rules are mined into testable naked-long ablations.

## Tradetron attachments

| ID | Strategy | Direct final eligibility | Main components to mine |
|---|---|---|---|
| TT-A01 | Profit Breakout Premium Match Straddle | NO — contains 4 short legs and 2 long legs | 10:00–10:05 entry; non-expiry vs expiry-day split; ATM short-premium structure; premium-matching strike discovery; -₹7,000 global loss stop; 15:15 exit |
| TT-A02 | 0.20/0.10 Delta Calendar Hedge Spread v4 | NO — short near expiry + long far expiry, multiple adjustments | 0.20/0.10 delta levels; 0W/1W term structure; delta-decay/reversal triggers at ±0.08/±0.50; runtime state transitions; 09:20–15:00 operating window |
| TT-A03 | Corrected Dynamic-n NIFTY Weekly Options Strategy | NO — 1 long + 2 shorts | DTE=3; 10:00–10:05 entry; bullish/bearish side mapping; ±300/350/400 point strike ladder; expiry-day exit rule |
| TT-A04 | Dynamic Ratio Reversals | NO — ratio structures include shorts | Bullish put-ratio vs bearish call-ratio state machine; monthly expiry; delta bands 0.08–0.65; runtime state/entry counters |
| TT-A05 | Simple Intraday Short Straddle | NO — both legs short | 09:30–15:10 window; one trade/day; weekday/expiry-day separation; -₹3,000 loss stop; 15:15 exit. Use only as volatility-regime/premium benchmark, never as final execution |
| TT-A06 | Intraday Asym Premium | NO — 4 shorts + 2 longs | 09:30–15:10; one trade/day; Monday exclusion; ATM + far-expiry LTP-matched strike logic; -₹4,000 loss stop; 15:15 exit |
| TT-A07 | Dynamic IC to Ratio | NO — iron condor/ratio structures | Friday setup; IC → call/put ratio transitions; delta thresholds 0.10/0.30/0.40/0.50/0.65; runtime state machine; month expiry |

## Tradetron backtest links supplied by user

The seven links are retained as references:

1. `https://tradetron.tech/bt/view/d164b781832c2202116c72af0d6dc76d`
2. `https://tradetron.tech/bt/view/57d2b9ddc507843ad486a5323316622a`
3. `https://tradetron.tech/bt/view/79b5f5977342301347e82a8175e9ddf8`
4. `https://tradetron.tech/bt/view/b83f1f24a8b677c67f472d5189902130`
5. `https://tradetron.tech/bt/view/667be6a22e2caa8866b7476065a68120`
6. `https://tradetron.tech/bt/view/bc0e67d112845360381bd736f9f98e2d`
7. `https://tradetron.tech/bt/view/ade954a4a6aed2bb03b57462d71dd406`

### Retrieval status

The connected Tradetron backtest-status service returned **not_found** for all seven supplied 32-hex tokens. This is recorded as an access/retrieval limitation, not as a failed backtest. The URLs remain preserved for manual provenance.

No new Tradetron backtest was submitted: new backtests can be chargeable and require explicit user consent before a chargeable run.

## Extraction rules

Each legacy strategy is converted into atomic hypotheses/ablations:

- timing windows;
- weekday/expiry-day filters;
- DTE buckets;
- directional side selection;
- ATM vs delta-based strike selection;
- premium-ratio / premium-match conditions;
- delta crossing/decay triggers;
- state-machine transitions;
- term-structure and expiry-offset relationships;
- P&L/time-barrier exits;
- one-trade-per-day throttles.

Each extracted component will be tested independently and in combination against the canonical Phase 2 dataset. The parent multi-leg structure is retained only for historical comparison and is not eligible for the final naked-long strategy.

## Research status

This intake is complete for the seven supplied JSON strategies. Final statistical testing remains blocked until the Phase 2 data/PIT gate passes.
