# NIFTY Naked-Option Direction Research

Research program for predicting NIFTY 50 direction and translating signals into **long-only naked option buying** strategies for intraday and positional horizons.

## Research status
### Latest Phase 2 execution

- Final hosted Phase 2 audit run #104 completed successfully after real-data failures were diagnosed and corrected.
- Official NSE legacy/UDiFF archives were acquired, schema-checked, hashed and cached; global reference series, official lot-size validation, India VIX/FII-DII source checks and cross-source reconciliations also completed.
- The S08 derived option dataset passed the pre-declared secondary corroboration gate on 96 near-ATM contracts, while its strict 0.25%/tick metric remains visible as a diagnostic; it is not canonical.
- S31 remains quarantined because its ATM parquet files do not expose sufficient expiry/contract semantics for reliable reconciliation.
- Phase 3 now starts from official canonical data with explicit quarantine rules for auxiliary sources that lack historical publication timestamps.


- Repository initialized: 2026-10-07
- Current phase: Phase 3 — labels, baselines and cost-aware directionability
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

### Phase 3 execution

The Phase 3 protocol has passed independent tester review. The current workflow acquires a long daily NIFTY history via a free Yahoo Finance bulk reference with mandatory official NSE overlap validation, discovers and samples a long intraday NIFTY research reference from Hugging Face, then runs frozen positional/intraday baselines. Derived intraday data remain non-canonical under the Phase 2 restrictions. No Phase 4 method search has started.
