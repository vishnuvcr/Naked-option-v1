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


Rerun authorization: R2 — 2026-10-12. Use the corrected tester-approved runner/test/workflow blobs, the same two pinned artifacts, and the existing HF_TOKEN secret only to decrypt the cached composite. If the aggregate counters still show no eligible option rows, stop with the sanitized diagnostics and fix the parser; do not label that result as trading performance. No new data acquisition and no bid/ask gate.


## R3 rerun authorization — 2026-10-12

- Use the already-existing expiry-enriched composite artifact 11723198817, source run 38195812828, archive SHA-256 e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736. Its expiry mapping is a historical expiry-partition/Tuesdays proxy, not a point-in-time official contract master.
- Keep the immutable Phase 7 Run #994 forecast artifact and all 4,800 configurations × four friction scenarios unchanged.
- Do not acquire new market data, request bid/ask, refit forecasts or promote the best result automatically.
- If the runner fails again, the workflow records only sanitized aggregate diagnostics, updates research logs and preserves a failure artifact; fix the implementation autonomously and resubmit exact blobs for tester review.
