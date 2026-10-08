# Phase 8 Execution Conventions — Independent Tester Gate

**Status: PASS WITH SCOPED RESTRICTIONS**  
**Empirical option P&L:** NOT YET AUTHORIZED

## Independent checks

### Causality

- Daily forecasts use the completed daily session; entry is restricted to the next session.
- Intraday forecasts use the frozen hourly grid; the first admissible option observation is one minute after the forecast timestamp.
- No same-bar or pre-decision option observation can generate a fill.
- Contract eligibility requires expiry strictly after the planned exit.

### Session mapping

- Daily H is measured in future NSE trading sessions, not calendar days.
- Daily exit target is fixed at 15:15 IST on the H-th future trading session, with search through 15:30 IST.
- Contract-expiry forced exit uses 15:15 IST on the contract's last trading session with the same window.
- Intraday exits use the exact H-minute target plus the frozen two-minute search tolerance.

### Q1 proxy execution

The bar-open rule is causal: the open of the first eligible bar is observable at the bar's start. Trigger fills use registered target/stop levels; when both thresholds are crossed in the same bar, the conservative stop-first rule is used.

### Q2 quote execution

The quote-backed rule requires a valid timestamped ask for entry or bid for exit and applies the stale-data window. A stale/missing quote cannot silently fall back to a future quote.

## Scoped restrictions

1. The daily 15:15 exit convention is deliberately pre-close rather than end-of-day. It is fixed for all Phase 8 runs and may not be changed based on results.
2. The final 15:30 intraday forecast row may have no next-minute entry observation. Such signals are recorded as `NO_FILL`, not discarded from the audit universe.
3. Q1 OHLC/proxy results remain non-quote-executable.

## Gate decision

**PASS WITH SCOPED RESTRICTIONS.**

The execution timing/fill convention is approved for engine implementation. The next gate must include the pure execution/cost regression suite and must still prohibit empirical P&L until data/cache and workflow gates pass.

**Tester → Developer:** implement these conventions exactly in the pure execution engine; add deterministic tests for DTE buckets, entry/exit timing, Q1/Q2 fills, stop-first logic, expiry forcing and charge arithmetic. Then submit the execution-engine code gate. Do not run the 4,800-cell empirical grid yet.
