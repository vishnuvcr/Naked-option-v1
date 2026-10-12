# Phase 8 OHLC Proxy Execution Request

Status: RUN_APPROVED_BY_TESTER

This request invokes the exact developer-branch runner, tests, and workflow blobs listed in the tester gate:
- Tester gate: research/gates/PHASE8_PROXY_STRATEGY_TESTER.md on phase-08-prediction-tester
- Execution quality: Q1/OHLC proxy; no bid/ask prerequisite
- Forecast: immutable Phase 7 Run #994 artifact, pinned by SHA-256
- Options input: existing 61-part composite artifact, pinned by SHA-256; no new market-data requests
- Grid: 4,800 frozen configurations × four spread/slippage scenarios
- Fees: existing date-effective cost schedule with historical Paytm Money brokerage fallback of ₹20 per executed order
- Results: retain all configurations, trade counts, net P&L, win/loss, average win/loss, return, profit factor, maximum drawdown, and yearly breakdown. Do not automatically promote the top-ranked configuration.
- Limitations: all results are Q1/OHLC proxy, historical lot sizing is approximate around contract transitions, and the results are not quote-executable.

Run only if GitHub Actions confirms the exact tester PASS and all required regression jobs pass.
