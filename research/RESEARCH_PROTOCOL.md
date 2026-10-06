# Research Protocol

## Core principles

1. Pre-registration before performance inspection.
2. Point-in-time information only.
3. Chronological splitting.
4. No hyperparameter fitting on the final holdout.
5. Costs included in every executable result.
6. Failed hypotheses remain logged.
7. Composite datasets retain source-level lineage.
8. No manual cherry-picking of favorable periods.
9. Every model receives a deterministic experiment ID and manifest.
10. Tester review precedes phase advancement.

## Direction labels

Exact labels are to be frozen in Phase 3, but candidate families include:

- Binary future return sign.
- Thresholded return sign exceeding a cost/volatility threshold.
- Triple-barrier direction with time barrier.
- Intraday first-passage direction.
- Positional first-passage direction.
- Multi-class up/flat/down.

The main trade label must be linked to a realistic option break-even condition, not only spot direction.

## Data leakage controls

- Feature timestamp <= decision timestamp.
- External datasets use demonstrable availability/publication timestamps where possible.
- Corporate actions are as-of adjusted with explicit effective dates.
- Options use contract availability and listing state.
- No future expiry knowledge beyond what a trader knew at decision time.
- Normalization and imputation parameters are fit only on training data.
- Feature selection occurs inside training folds.

## Statistical framework

Report discrimination (AUC/PR-AUC), calibration (Brier/log-loss/reliability), directional accuracy, expected value, hit rate, payoff ratio, max drawdown, tail loss, Sharpe/Sortino where meaningful, turnover and cost sensitivity. Use HAC/block-robust inference where dependence requires it.

Multiple testing will be controlled using false-discovery or family-wise procedures where appropriate, plus Reality Check/SPA/PBO/DSR-style diagnostics for strategy selection.

## Option execution constraints

- Position type: long CE or long PE only.
- No naked short options.
- No spreads or multi-leg hedges in the primary strategy.
- Entry/exit may use marketable/limit execution assumptions, but every assumption is declared.
- Bid/ask and latency must be modeled from available data; when historical quote data are unavailable, conservative proxy scenarios are mandatory and the result cannot be labeled quote-executable.
- Total premium at risk per trade is finite; position sizing is capped.

## Cost scenarios

Primary, adverse and extreme scenarios will be reported. Every trade includes all applicable brokerage and statutory charges plus slippage/spread/latency assumptions.

## Reproducibility

Every run stores:

- git commit SHA;
- environment/version manifest;
- input snapshot IDs/hashes;
- experiment configuration;
- result artifact hashes;
- random seeds;
- test status.
