# Research Plan — NIFTY Naked-Option Direction

## 1. Research question

Can NIFTY 50 direction be predicted robustly at intraday and positional horizons using price, volatility, options, participation, macro/global, sentiment/news and regime information, and can those forecasts be converted into positive net-expectancy **long-only naked call/put** trades after realistic execution costs?

## 2. Secondary questions

1. Which information families contribute incremental out-of-sample directional information?
2. Are there regime-dependent predictors rather than one universal predictor?
3. Is direction more predictable at specific horizons, times of day, volatility states, or expiry distances?
4. Can option selection be optimized for delta, moneyness, tenor and liquidity without introducing survivorship or look-ahead bias?
5. Can a forecast be profitable after premium decay, spreads, latency, brokerage and taxes?
6. Which apparently successful signals fail under multiple-testing corrections, CPCV and untouched-forward testing?
7. Can abstention/no-trade materially improve risk-adjusted performance?

## 3. Aims

### Aim A — Build a trustworthy point-in-time NIFTY research dataset
Combine official/free sources first, with explicit provenance, publication timestamps and immutable snapshots.

### Aim B — Test a broad but finite method universe
Evaluate rule-based, statistical, machine-learning, regime, cross-market, options-surface and novel-feature methods using pre-registered definitions.

### Aim C — Translate direction forecasts into executable long-option trades
Only long NIFTY CE/PE positions are permitted.

### Aim D — Establish whether any edge survives robust validation
A method is not promoted on a single backtest metric.

## 4. Objectives

- Create a PIT-clean multi-frequency dataset.
- Define non-overlapping intraday and positional labels.
- Establish naive and economically meaningful baselines.
- Test the complete method registry.
- Use nested walk-forward tuning.
- Apply transaction-cost and slippage scenarios.
- Evaluate calibration, discrimination and trading economics separately.
- Perform independent tester gates at every phase.
- Produce a reproducible final manuscript with tables, figures, appendices and machine-readable experiment manifests.

## 5. Pre-registered phase catalog

### Phase 0 — Governance/bootstrap
Repository rules, roles, branches, status ledgers, error logging, workflow templates.

### Phase 1 — Literature + method universe
Systematic review of academic papers, official exchange/regulator material, open-source implementations, technical-analysis evidence, options microstructure evidence and prior project findings. Build the method registry before seeing strategy results.

### Phase 2 — Data engineering + PIT validation
NIFTY spot/index, index futures where useful, option contracts/OHLCV/OI, IV/Greeks, India VIX, FII/FPI/DII, breadth, sector indices, global equity indices, VIX, USD/INR, rates, gold, commodities, calendar/corporate-action/news/sentiment inputs where justified. Build composite datasets only with source lineage preserved.

### Phase 3 — Labels + baseline directionability
Define intraday horizons (for example 5/15/30/60/120 minutes and close-to-close variants) and positional horizons (1/2/3/5/10 sessions). Establish class balance, persistence, drift, volatility and cost-aware break-even rates.

### Phase 4 — Single-family method tests
Technical trend/momentum, mean reversion, range/volatility, price-action/market-structure, breadth, derivatives/OI, IV/skew/term structure, calendar, global lead-lag, macro, sentiment/news and cross-asset methods.

### Phase 5 — Statistical + nonlinear models
Logistic/GLM, LDA/QDA, GAMs, tree ensembles, random forests, gradient boosting, calibrated classifiers, state-space models, HMM/regime models, Bayesian models, survival/hazard views of directional moves, and controlled sequence models.

### Phase 6 — Novel research methods
Pre-registered experimental metrics and representations, including entropy/complexity, multi-scale features, information-flow measures, adaptive regime scores, composite lead-lag pressure, option-implied directional pressure and abstention/confidence operators. Novel methods must beat strong baselines out-of-sample and pass tester review.

### Phase 7 — Ensemble + regime-conditioned prediction
Stack only models that have passed earlier gates. Compare static, regime-conditioned, mixture-of-experts and abstention policies. Freeze all selection rules before touching the final holdout.

### Phase 8 — Long-option execution research
Map directional forecasts to calls/puts. Test expiry, delta/moneyness, DTE, entry timing, exit timing, stop/time-stop, profit target, trailing exit, IV filters and no-trade rules. Never use information unavailable at trade time.

### Phase 9 — Robustness + statistical gate
Walk-forward, purged/embargoed validation where needed, CPCV, PBO, Deflated Sharpe, White/Reality-Check or SPA-type controls as appropriate, block bootstrap, sensitivity matrices, cost stress, parameter perturbation, regime-by-regime results, and multiple-comparison accounting.

### Phase 10 — Fresh-forward / paper-trading verification
Lock strategy and parameters. Run a later untouched dataset and/or live paper sleeve without re-fitting. No promotion after peeking at results.

### Phase 11 — Final synthesis
Research manuscript, full methods, data provenance, all null findings, winning/failed candidates, risk analysis, limitations and future research.

## 6. Promotion criteria

A candidate can reach final review only if it has:

- no look-ahead or survivorship breach;
- reproducible data lineage;
- positive expectancy after the primary cost model;
- robustness to realistic slippage and spread assumptions;
- acceptable drawdown/tail risk;
- calibration/ROC/PR evidence appropriate to the label;
- stability across multiple chronological blocks;
- no dependence on a fragile single parameter;
- tester approval;
- untouched forward validation.

No single numeric threshold is sufficient for promotion; all gates are conjunctive.

## 7. Stop rule

The research will not expand without limit. The method universe ends when the pre-registered catalog in `METHOD_REGISTRY.md` has been exhausted, all surviving candidates have passed the statistical gates, and the fresh-forward test is complete.

Literal “100% certainty” about future market direction is impossible. The scientific objective is the strongest defensible evidence under the declared protocol.


Protocol terminology note: the final **untouched holdout** is the untouched forward-validation segment reserved from all development, tuning, and candidate selection; it is not reused for model selection.
