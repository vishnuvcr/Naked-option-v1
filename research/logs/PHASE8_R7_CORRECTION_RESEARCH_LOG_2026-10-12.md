# Phase 8 R7 Research Log — 2026-10-12

## Research question
Do the saved Phase 7 prediction signals retain any net performance under a conservative, timestamp-aligned long-option OHLC proxy after accounting for costs and correcting known backtest defects?

## Current method
- Frozen Run #994 forecast artifact `11638738288`; expiry-enriched option composite `11723198817`.
- Finite grid: 4,800 configurations × C0–C3 friction scenarios.
- Paytm Money brokerage assumption plus dated statutory/exchange fees; synthetic spread and slippage. Q1/OHLC proxy only, not quote-executable.
- No new data acquisition and no forecast refit.

## Corrections made after independent tester REQUEST CHANGES
1. Drawdown percent now uses timestamp-aggregated P&L and the local preceding positive peak.
2. Full OHLC structural checks include close consistency.
3. Simulated fills are conservatively rounded to ₹0.05 tick after spread/slippage.
4. Intraday entry is limited to 120 seconds after the forecast decision.
5. Contract selection no longer synthesizes delta from raw IV without a separate availability timestamp; only eligible prior-bar stored delta is used.
6. Prior-bar spot, volume and open interest are used for fallback/liquidity tie-break; same-timestamp duplicate records cannot supply lagged fields.
7. Duplicate contract-minute rows and conflicting OHLC groups are counted.
8. Conservative expiry windows around lot-size transitions are excluded.
9. Net-return denominator includes rounded entry premium plus modeled round-trip costs.
10. Workflow distinguishes missing-metrics failure from publication failure and commits run-unique artifacts to avoid shared-file conflicts.

## Gate and execution
- Exact-snapshot regression/self-test passed: [run 38229662631](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38229662631).
- Independent code gate PASS is recorded on `phase-08-prediction-tester`.
- Fresh corrected grid: [run 38229793041](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38229793041), initiated by commit `6b63919ca6b392fb6ca030f0ff85e33d22ce7277`.
- Result-level audit has not yet occurred; no corrected performance conclusion is available until its artifact is produced and independently reconciled.

## Limitations retained
- Historical Paytm Money brokerage rate is a documented fallback assumption.
- The enriched expiry mapping remains a proxy, not an official point-in-time contract master.
- Lot-size transition exclusions are conservative but do not substitute for a complete listed-contract master.
- Execution prices are OHLC proxies, not bid/ask quote-executable fills.
- Multiple-testing and IID screening values are not confirmatory inference.

**Developer → Tester:** audit the new artifact, cost arithmetic, P&L, corrected drawdown, and diagnostic counts independently.

**Tester → Developer:** do not promote a candidate or advance Phase 9 until result-level PASS.
