# NIFTY Naked-Option Direction Research

Research program for predicting NIFTY 50 direction and translating signals into long-only naked option buying strategies for intraday and positional horizons.

## Research status

- Phase 2 passed the independent tester gate with explicit source restrictions.
- Phase 3 protocol passed its independent tester review, but the first empirical-execution package was rejected by the tester for workflow, logging, implementation, and PIT-validation defects.
- Those defects have now been corrected on the phase-03-developer branch.
- A fresh hosted Phase 3 run is required before any empirical baseline result is accepted.
- Phase 4 and all later phases remain blocked until the independent tester reproduces the Phase 3 result packet and passes the empirical gate.

### Current Phase 3 scope

The frozen label horizons are 5/15/30/60/120 minutes intraday and +1/+2/+3/+5/+10 sessions positional. Baselines B0-B11 are explicitly required for every evaluated horizon; a missing data layer must be recorded as BLOCKED_DATA, never silently omitted.

The workflow now performs protocol validation, NIFTY daily acquisition, Hugging Face intraday reference discovery/acquisition, official-NSE overlap validation for the intraday reference, positional/intraday baseline execution, result-schema validation, result persistence and artifact upload. Caches are retained to avoid unnecessary redownloads.

B9 global-overnight and B10 breadth are currently conservatively blocked in Phase 3 until their PIT-safe historical feature layers are materialized. India VIX/FII-DII remain governed by the Phase 2 publication-timestamp restrictions.

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
- [Phase 3 baseline data gaps](research/phase3/BASELINE_DATA_GAPS.md)
- [Gate reports](research/gates/)

## Branch governance

developer implements research code and evidence packages.
tester is an isolated independent review environment. The tester independently checks mathematics, data joins, leakage, code logic, execution-cost assumptions, and reproducibility.
Each research phase has separate phase developer/tester branches and a tester gate before progression.

## Important prior-project evidence

Earlier Project artifacts reported a failed untouched-holdout next-day directional model (AUC about 0.458) and a more promising future-volatility signal. These are historical inputs only and are not accepted current results until revalidated under this repository's protocol.

## Disclaimer

This is research and backtesting infrastructure, not a guarantee of profit or investment advice. Long options can lose 100% of the premium paid.
