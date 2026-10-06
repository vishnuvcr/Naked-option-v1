# NIFTY Naked-Option Direction Research

Research program for predicting NIFTY 50 direction and translating signals into **long-only naked option buying** strategies for intraday and positional horizons.

## Research status
### Latest Phase 2 execution

- Hosted GitHub Actions is now executing the real data-audit workflow with cached raw data and the repository HF_TOKEN secret.
- Official NSE legacy/UDiFF archive acquisition, schema validation, snapshot hashing and HF reference acquisition have all completed successfully in the observed runs.
- Reconciliation has so far failed on real data twice for legitimate engineering reasons: a fixed-offset timezone parsing issue, then an over-broad full-expiry coverage denominator (84.16%). Both failures are logged and corrected; the latest run is testing a pre-declared near-ATM validation universe.
- Full official NSE data remains canonical; derived Hugging Face data is only a validation source and is not being promoted to canonical.


- Repository initialized: 2026-10-07
- Current phase: Phase 2 — data engineering and point-in-time validation
- Developer branch: `developer`
- Tester branch: `tester`
- Strategy constraint: buy NIFTY calls or puts only; no option selling, spreads, short futures, or hidden short exposure.
- Execution costs: brokerage, STT, exchange charges, SEBI fee, GST, stamp duty where applicable, bid/ask, slippage and latency must be modeled.
- Validation standard: chronological walk-forward, untouched holdout, CPCV/DSR/PBO-style robustness, stress tests and independent tester review.
- Stop rule: the research stops after the pre-registered phase catalog is exhausted or a serious irreparable data/research limitation is reached. “Exhaust every possible way in the universe” is treated as an explicit **finite method-universe requirement**, not a claim of literal omniscience.

## Canonical documents

- [Research plan](research/RESEARCH_PLAN.md)
- [Research protocol](research/RESEARCH_PROTOCOL.md)
- [Method registry](research/METHOD_REGISTRY.md)
- [Hypothesis catalog](research/HYPOTHESIS_CATALOG.md)
- [Literature review](research/literature/LITERATURE_REVIEW.md)
- [Literature search protocol](research/literature/LITERATURE_SEARCH_PROTOCOL.md)
- [Machine-readable literature registry](research/literature/LITERATURE_REGISTRY.csv)
- [Cost model](research/COST_MODEL.md)
- [Data source registry](research/DATA_SOURCE_REGISTRY.md)
- [Phase status](research/STATUS.md)
- [Research log](research/logs/RESEARCH_LOG.md)
- [Error log](research/logs/ERROR_LOG.md)
- [Decision/chat log](research/logs/CHAT_LOG.md)
- [Gate reports](research/gates/)

## Branch governance

`developer` implements research code and evidence packages.

`tester` is an isolated independent review environment. The tester does not reuse developer conclusions as evidence; it independently checks mathematics, data joins, leakage, code logic, execution-cost assumptions, and reproducibility.

Each research phase will have separate phase branches and a developer-to-tester gate before progression.

## Important prior-project evidence

The current Project contains earlier NIFTY/market-inefficiency research artifacts. Those artifacts report, among other things, a failed untouched-holdout next-day directional model (AUC about 0.458) and a more promising future-volatility signal. These are **historical project findings, not yet accepted results for this repository**; they must be revalidated under the present protocol before being used in final conclusions.

## Disclaimer

This is research and backtesting infrastructure, not a guarantee of profit or investment advice. Long options can lose 100% of the premium paid.
