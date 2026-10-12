# Independent Tester Report — Phase 8 run 38222296903

Date: 2026-10-12  
Role: Independent tester (tester branch; no developer code edits performed)  
Decision: **REQUEST CHANGES — DO NOT PROMOTE / DO NOT ADVANCE PHASE 9**

## Evidence reviewed

- Hosted run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38222296903
- Artifact: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38222296903/artifacts/11736907952
- ZIP SHA-256 from hosted log: `07ede4908c9a49e78de9a3aec711ac514de78f16437a825a063b6d4eb0902d54`
- Artifact report says `COMPLETE_PROXY_BACKTEST`; summary contains 19,200 rows; ledger contains 1,596,680 trade rows with C0–C3 columns. The overall workflow failed later during Git rebase/publishing and its `FAILED_NO_METRICS` handler contradicts the generated artifact.
- Independent spot-check of the first ledger records reproduced the schema and showed fills not rounded to the ₹0.05 tick (e.g., C1 exit fill ₹0.04975), and the stored return can be below -100% (e.g., C0 net return -110.65%). The latter may be possible if the denominator is not limited to premium-at-risk, but the return definition must be stated and validated for a long-premium position.
- All inspected ledger rows use `BLACK_SCHOLES_RAW_IV_AT_DECISION_PROXY`; point-in-time availability of raw IV is not proven by the ledger.
- C3 preliminary summary has two positive-net-P&L configurations with ≥30 trades; reported profits are small relative to trade counts and profit factors are only 1.0243 and 1.0154. BH q-values 0.3990 and 0.0365 are in-sample screening outputs, not confirmatory evidence. No promotion supported.

## Findings requiring correction

1. **Maximum drawdown percentage is not trustworthy.** Existing calculation divides max drawdown by the maximum peak over the entire series rather than the preceding local peak at the drawdown trough. Recompute equity from ordered realized P&L, aggregate same-timestamp exits as specified, and use the local peak-to-trough denominator with a documented starting-equity convention.
2. **Fills violate ₹0.05 tick grid.** Round buys conservatively upward and sells downward to valid ticks after spread/slippage, then recalculate taxes, fees, P&L, win/loss, returns, drawdown and candidate ranking. A sensitivity-only count is not enough.
3. **Raw IV as-of provenance is unresolved.** Since contract selection relies on raw IV at decision time, show source timestamp/availability and prove it predates the decision. If impossible, mark affected delta-target results non-identifiable or use a pre-registered moneyness-only fallback as a separately gated experiment; do not silently assume the IV is point-in-time.
4. **OHLC integrity needs enforced validation.** Require finite positive prices, `high >= low`, `low <= open <= high`, and close inside [low, high]; count/reject invalid bars and record source counts.
5. **Registered liquidity tie-break is missing.** Add the frozen contemporaneous liquidity ranking (volume/OI availability as-of entry), then deterministic tie-breaks; quantify changed contract selections.
6. **Entry delay convention mismatch.** The runner allows 300 seconds, whereas frozen intraday convention caps at 120 seconds (t+1/t+2 minute bars). Apply the frozen cap and report rejected signals. Daily next-session entry is a separate convention.
7. **Expiry-based lot-size proxy can mis-scale contracts around transitions.** Obtain or construct a dated listed-contract lot-size map from available free evidence; otherwise exclude transition-window trades or label absolute INR metrics non-accepted.
8. **Publication workflow is not failure-safe.** Result computation generated valid artifact files, but git rebase conflicts led to a false `FAILED_NO_METRICS` diagnostic. Separate compute status from publication status; use artifact upload as durable fallback and a conflict-safe publication strategy. Failure-handler must inspect whether report/summary/ledger exist before setting no-metrics status.
9. **Reconcile summary vs ledger.** Independently recompute C0–C3 P&L, costs, wins/losses, profit factor, return denominator, timestamps, duplicate rows and counts for all configurations. Do not accept the developer's candidate scan without reproducible reconciliation.

## Gate disposition

This is a request-changes report. No candidate can be called a working strategy on the current evidence. The next empirical run must use a new exact snapshot with regression and independent pre-run approval. Then the tester must independently review the corrected result artifact before Phase 9.

**Tester → Developer:** resolve each numbered issue in an isolated developer commit, add regression tests and provide a new hash-pinned code-review request. Do not advance to empirical rerun until the tester approves the exact code snapshot.

**Developer → Tester:** submit corrected code and test results for independent review; do not self-approve this report.
