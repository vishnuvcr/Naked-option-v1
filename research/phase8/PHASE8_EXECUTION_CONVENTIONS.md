# Phase 8 — Execution Conventions Amendment

**Status: SUBMITTED FOR INDEPENDENT TESTER REVIEW — NO EMPIRICAL P&L AUTHORIZED**

This amendment resolves implementation-level timing/fill conventions without changing the registered signal, delta, DTE or exit-configuration universe.

## Decision timestamps

- Daily Phase 7 forecast: end of the identified NSE trading session. The canonical decision timestamp is 15:30 IST for alignment with the close-to-close label.
- Intraday Phase 7 forecast: the frozen hourly decision timestamps 09:30, 10:30, 11:30, 12:30, 13:30, 14:30 and 15:30 IST, represented internally in UTC.

## Daily option entry

For a daily forecast issued at session close, the earliest permitted entry observation is 09:16 IST on the next NSE trading session. The entry search window is 09:16–09:30 inclusive. The first valid observation in this interval is used.

This remains consistent with the previously frozen one-minute latency convention relative to the next available session.

## Daily option exit

The registered daily option exit target is **15:15 IST on the H-th future NSE trading session**, where H is the Phase 7 daily horizon.

The permitted exit search window is 15:15–15:30 inclusive. The first valid observation at or after 15:15 is used. This preserves a pre-close execution window while avoiding dependence on a post-market timestamp.

If the selected contract expires before the planned exit, its forced-exit timestamp is 15:15 IST on the last trading session of that contract, with the same 15-minute window through 15:30.

## Intraday option entry

At decision timestamp t, the earliest permitted option observation is t + 1 minute. The entry search window is exactly t+1 through t+2 minutes inclusive. No same-bar or pre-decision observation can enter the fill.

## Intraday option exit

For X0, the planned target is exactly decision timestamp + H minutes. The exit window is target through target + 2 minutes.

For X1–X3, trigger evaluation uses every valid observation after entry. If a trigger and the horizon occur in the same one-minute bar, the trigger is evaluated before the horizon exit.

## OHLC/proxy fill convention

Q1 rows without validated bid/ask are never called quote-executable.

For a Q1 entry, the executable base price is the **bar open** of the first eligible bar. For a Q1 exit at a horizon/forced-exit time, the executable base price is the **bar open** of the first eligible bar at or after the exit timestamp.

For stop/target-triggered Q1 exits:

- target is filled at the registered target premium when the bar high reaches/exceeds it;
- stop is filled at the registered stop premium when the bar low reaches/falls below it;
- when both are possible in the same bar, stop first.

Synthetic half-spread and the separately registered C0–C3 incremental slippage are then applied.

## Q2 quote-backed fills

For a validated Q2 entry, buy at contemporaneous ask. For a validated Q2 exit, sell at contemporaneous bid.

A quote timestamp must be no earlier than the executable timestamp and no older than the frozen stale-data window.

## Contract eligibility

A contract is eligible only if:

- its point-in-time expiry is strictly after the planned primary exit timestamp;
- its strike, option type, tick size and lot size are valid;
- its selection inputs are available by the decision timestamp.

No future option quote/volume/OI may influence entry contract selection.

## Scope

This amendment is a deterministic execution convention only. It does not add candidates, alter the 4,800-cell grid, or authorize empirical P&L.

## Tester request

Independently verify:
1. the timing is causal relative to the accepted Phase 7 forecast;
2. the daily H-session mapping is deterministic and does not mix calendar and trading-session counts;
3. the Q1 trigger and bar-open conventions avoid look-ahead;
4. Q2 quote timestamp validation is causal;
5. forced expiry handling is deterministic.

No empirical option results may be generated until this amendment is approved.
