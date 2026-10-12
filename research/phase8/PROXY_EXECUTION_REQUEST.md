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


## R4 as-of correction rerun — 2026-10-12

- Previous run 38220714996 uses a pre-correction snapshot and is explicitly NON-ACCEPTED due to one-minute lookahead in stored Greek delta selection.
- Corrected exact code blobs are the runner, tests, and workflow recorded in tester R4 at research/gates/PHASE8_PROXY_STRATEGY_TESTER.md on phase-08-prediction-tester.
- Regression and exact-blob gate passed in run 38221310213. This request triggers the first empirical run on the as-of corrected runner, against the same pinned enriched option artifact 11723198817 and saved Run #994 forecasts.
- Use the same frozen 4,800-config grid and C0-C3 costs. No new data acquisition, no bid/ask prerequisite, no forecast refit, and no automatic promotion.


## R5 vectorized as-of-corrected run — 2026-10-12

- The exact R5 runner/test/workflow blob set is approved in tester gate `research/gates/PHASE8_PROXY_STRATEGY_TESTER.md` on `phase-08-prediction-tester`.
- Hosted run 38222175404 passed compilation, all 12 synthetic tests, runner self-test, and exact tester gate. It did not run the empirical job because this was the regression-only trigger.
- Launch the finite 4,800-config × four-scenario proxy grid using the already-existing expiry-enriched option artifact 11723198817 and frozen Run #994 forecast artifact 11638738288. All previous runs that used the loop-based trigger scan are superseded diagnostics; the R3 stored-delta lookahead run is NON-ACCEPTED.
- No new market-data acquisition, no bid/ask prerequisite, no refit, and no promotion based solely on historical ranking.


## R7 corrected execution request — 2026-10-12

- Independent tester R7 code gate PASS is recorded on `phase-08-prediction-tester` for the exact runner/test/workflow blobs; hosted regression run 38229662631 passed compile, synthetic regression and runner self-test.
- Launch one fresh finite grid against the same pinned Run #994 forecast artifact and enriched option artifact. The corrected runner applies tick-rounded fills, 120-second intraday entry cap, timestamp-aggregated local-peak drawdown, strict OHLC consistency validation, prior-bar-only delta/spot/liquidity, duplicate same-timestamp lag invalidation, duplicate diagnostics and lot-size transition expiry exclusions.
- Raw-IV Black–Scholes recomputation is disabled because the frozen source does not provide a separate IV-availability timestamp. Count fallback/usable delta selection in output; do not imply the raw IV is point-in-time proven.
- Keep Paytm Money brokerage as the documented historical fallback and all statutory charges/slippage; execution remains Q1/OHLC proxy, not quote-executable.
- Workflow publication is run-directory-only to avoid shared-file rebase conflicts; failure status must distinguish a missing-metrics failure from a publication failure when result artifacts exist.
- This is a request to run the corrected grid only. It does not authorize promotion. The result-level tester must independently reconcile the new ledger, summaries, tick costs, P&L, win/loss, returns, drawdowns, diagnostics and yearly robustness before any strategy decision.
