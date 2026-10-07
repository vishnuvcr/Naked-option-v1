# NIFTY Naked-Option Direction Research

Research program for predicting NIFTY 50 direction and translating signals into long-only naked option buying strategies for intraday and positional horizons.

## Research status

- Phase 2 passed the independent tester gate with explicit source restrictions.
- Phase 3 passed the independent tester gate with scoped data restrictions.
- Phase 4 Family B passed with VWAP blocked for missing PIT-safe volume; Family C passed with C10/C11 blocked for missing PIT-safe feature layers.
- Phase 5 Family D is active. The initial empirical lineage has been rejected/invalidated before accepted evidence because of deterministic regression, timestamp, and runtime-control defects; all are logged and preserved.
- The failed run is preserved as rejected evidence; no Family D metric from it is accepted.
- Independent tester submissions for the Family D correction cycle are archived under [Phase 5 gates](research/gates/), including the run-1 request-changes report and the protocol-amendment approval.
- The current correction uses a session-based 20-trading-session intraday refit cadence, explicitly tester-approved as a protocol amendment, while predictions remain on the frozen hourly grid. Run #16 is preserved as non-accepted evidence because of a D07 protocol/implementation mismatch. The tester-approved D07 clarification and regression pin are now applied; fresh hosted run #19 passed the mandatory regression gate but hit the explicit 90-minute workflow timeout during the empirical suite before producing an artifact; it is non-accepted evidence. The tester approved a runtime-only amendment to a 180-minute hard timeout with progress markers. A fresh execution is required. No Family D metric is accepted.
- The research is not allowed to stop because an early model fails. The finite pre-registered phase sequence, execution-cost analysis, robustness gates and untouched-forward verification remain mandatory.

### Current Phase 5 scope

Family D evaluates D01-D15 using the frozen horizons: 5/15/30/60/120 minutes intraday and +1/+2/+3/+5/+10 sessions positional.

The current implementation retains the frozen hyperparameters. D04-D06 are explicitly provider-independent HistGradientBoosting surrogates. D13 uses a 20-observation lag-window MLP; D14 uses 16 fixed causal 3-tap filters followed by a 32-unit dense learner; D15 uses a fixed 2-head causal-attention representation of width 32 followed by a 32-unit dense learner. Intraday model fitting/prediction uses the frozen hourly decision grid while exact H-minute labels remain on the 1-minute path, and session-local sequence windows are enforced.

D07 now uses chronological training-only calibration for its base-probability stack. Standardization and all fitted transforms remain training-only. Failed runs are never treated as evidence.

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
- [Phase 5 run-1 research addendum](research/logs/PHASE5_RUN1_RESEARCH_LOG.md)
- [Error log](research/logs/ERROR_LOG.md)
- [Phase 5 run-1 error record](research/logs/PHASE5_RUN1_ERROR.md)
- [Phase 5 sequence precompute tester gate](research/gates/PHASE5_SEQUENCE_PRECOMPUTE_TESTER.md)
- [Phase 5 D07 amendment submission](research/gates/PHASE5_D07_PROTOCOL_AMENDMENT_SUBMISSION.md)
- [Phase 5 D07 amendment tester review](research/gates/PHASE5_D07_PROTOCOL_AMENDMENT_TESTER.md)
- [Phase 5 run #16 tester pre-check](research/gates/PHASE5_RUN16_TESTER_PRECHECK.md)
- [Phase 5 D07 post-amendment tester gate](research/gates/PHASE5_D07_POST_AMENDMENT_TESTER.md)
- [Decision/chat log](research/logs/CHAT_LOG.md)
- [Phase 5 resume chat log](research/logs/CHAT_LOG_PHASE5_20261007.md)
- [Gate reports](research/gates/)

## Branch governance

developer implements research code and evidence packages.
tester is an isolated independent review environment. The tester independently checks mathematics, data joins, leakage, code logic, execution-cost assumptions, and reproducibility.
Each research phase has separate phase developer/tester branches and a tester gate before progression.

## Important prior-project evidence

Earlier Project artifacts reported a failed untouched-holdout next-day directional model (AUC about 0.458) and a more promising future-volatility signal. These are historical inputs only and are not accepted current results until revalidated under this repository's protocol.

## Disclaimer

This is research and backtesting infrastructure, not a guarantee of profit or investment advice. Long options can lose 100% of the premium paid.
