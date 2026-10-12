# Phase 8 — OHLC Proxy Strategy Testing Plan

Date: 2026-10-12
Status: Tester R3 approved for one frozen-grid OHLC proxy run; expiry-enriched input rerun 38220714996 is in progress.
Execution branch: phase-08-prediction-developer
Independent tester branch: phase-08-prediction-tester
Tester gate: research/gates/PHASE8_PROXY_STRATEGY_TESTER.md

## Objective

Use the already-collected option OHLC composite and the immutable Phase 7 Run #994 forecasts to measure whether forecast-directed naked long-call/long-put trades have positive net outcomes after conservative simulated execution friction and Paytm Money/statutory charges. Bid/ask data are not required for this Q1 proxy study, per the user's instruction. No new market-data acquisition, model refit, or strategy promotion is permitted by this run.

## Frozen inputs

- Forecast reference: Run 37957677656, artifact 11638738288, SHA-256 3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9.
- Primary strategy input: existing expiry-enriched composite from Run 38195812828, artifact 11723198817, SHA-256 e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736. It derives from the already-collected 8,490,723-option/509,142-spot row composite; no new market-data acquisition is used.
- Expiry mapping is inherited from the existing enrichment artifact: public expiry-partition file-list plus a weekly Tuesday-rule proxy after the latest listed expiry. It is not an official point-in-time exchange contract master and must remain a stated limitation.
- The prior repaired artifact 11698879857 (Run 38131641336, SHA-256 40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b) was unsuitable for contract selection because all option rows had blank expiry_date. That failed attempt generated no metrics and is logged in research/ERROR_LOG.md.
- Decryption uses the existing repository HF_TOKEN secret and the repository decryptor; decoded data exist only in ephemeral runner scratch.
- Forecast models remain frozen. All 10 registered probability methods P01-P10 and the saved daily/intraday forecast panels are consumed as stored.

## Design

The registered grid is 4,800 configurations:
- 100 forecast cells: 10 saved panels × 10 frozen methods.
- Delta target: 0.40, 0.50, 0.60.
- DTE bucket: D0 = 0-1, D1 = 2-5, D2 = 6-10, D3 = 11-21 observed sessions.
- Exit policy: X0 scheduled horizon; X1 take profit at 150% of entry premium; X2 stop at 65% of entry premium; X3 trailing stop at 75% of the running premium high.

Direction thresholds come from the frozen Phase 8 execution engine. Candidate contract selection occurs at the entry-time option bar using the observed/modeled absolute delta where available, with a moneyness fallback. Entries use the first observed option OHLC bar strictly after the forecast decision. Intraday horizons scheduled beyond the 15:30 India-session close are skipped. A stop gap below the stop level is filled at the lower of the stop level and the bar open. For trigger logic using OHLC bars, intrabar ordering is inherently unobserved and outcomes remain proxy estimates.

## Friction and costs

Four scenarios apply a synthetic spread component to each side plus incremental slippage:
- C0: spread 0.5% per side, slippage 0.00% per side.
- C1: spread 1.0% per side, slippage 0.25% per side.
- C2: spread 2.0% per side, slippage 0.50% per side.
- C3: spread 4.0% per side, slippage 1.00% per side.

Round-trip brokerage uses the conservative historical-unverified Paytm Money fallback of ₹20 per executed order, plus date-effective exchange transaction charges, IPFT, option-sale STT, SEBI fee, stamp duty and GST from data/reference/phase8_cost_schedule.json. Fees are assessed against the simulated buy/sell fill prices on the corresponding execution dates. The lot-size schedule is expiry-date-based rather than a precise listed-contract instrument-master join, so absolute INR metrics may be wrong around lot-size transition dates and are estimates.

## Outputs

- Full 4,800-configuration × four-scenario (19,200 rows) summary CSV.
- Compressed trade-level ledger as a workflow artifact.
- Top 50 configurations with positive aggregate net P&L under C3 and at least 30 trades, ranked by net INR P&L; this is a discovery shortlist, not automatic promotion.
- Year-by-year C0-C3 breakdown for the shortlisted configurations.
- JSON run report with source hashes, execution coverage, skipped-event reasons and explicit Q1 limitations.
- Root README, research status, research log, and chat/decision log are updated by the hosted publishing step.

## Metrics

Per configuration and cost scenario: number of trades, wins/losses/breakevens, win/loss rates, total and average net rupee P&L, average and median net return on one-lot premium capital, average winning trade, average losing trade, profit factor, maximum cumulative-P&L drawdown and its peak/trough timestamps, plus IID t-test p-values and Benjamini-Hochberg q-value screening columns.

The IID tests and BH correction are exploratory diagnostics across serially dependent trades and many tested cells; they are not confirmatory significance results. This run cannot choose a final strategy on peak historical return alone. A candidate should be considered promising only if worst-cost performance, year/regime stability, drawdown, coverage and later holdout/robustness gates are also considered.

## Interpretation limits

- Q1/OHLC proxy, not bid/ask execution or executable quote P&L.
- Composite is a partial rolling-option grid; some cells can have no eligible contracts/trades.
- Greek values can be estimated; expiry mapping can be inferred; duplicate contract/timestamp observations are not dropped.
- Contract selection uses the current entry-time row, rather than pretending a quote existed at the forecast decision.
- Historical lot-size changes are approximated by expiry date; INR P&L/cost estimates can be mis-scaled for transition-month contracts.
- This is a historical research screen; no live-trading recommendation is authorized.

## Gate and finite stopping rule

This run has passed synthetic regression and the exact-code tester gate. Run it once over the frozen grid and cost scenarios. If the runner fails, record the runtime error and correct it without restarting data acquisition. After output is uploaded and published, the tester independently audits the output and reports PASS/REQUEST CHANGES. The research step stops after this finite 4,800-config run and its tester outcome; results may justify a separately approved robustness phase, not indefinite re-search.
