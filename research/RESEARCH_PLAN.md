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

## 4A. User-directed source-availability continuation amendment — 2026-10-11

This amendment records a direct user decision: accept Dhan price output as returned, do not require further independent NSE/third-party price-value reconciliation, and never stop the research programme merely because a data field/source is unavailable.

Dhan is the primary source for its documented daily, intraday and rolling expired-options fields. The existing Dhan one-row sample is accepted for development research under `research/gates/DHAN_SAMPLE_USER_ACCEPTANCE_WAIVER.json`; original provider bytes, source-request metadata and hashes are immutable. This acceptance is user-authorized and is not a claim that one row alone is statistically sufficient.

When any Dhan or other provider fails for a specific series, the acquisition workflow logs the source-specific error, uses the next predeclared free-source fallback, and merges compatible sources only with row-level provenance. If no eligible free source remains, only the affected feature/candidate cells are labelled `NOT_ESTIMABLE`; other sources, features, paper replications, methods and phases continue. Missing values are not fabricated, prices/options are not zero-filled, and proxy features are registered separately. Free sources must be searched before any paid source is considered.

This amendment changes the **response to source unavailability**, not the separate requirement for an exact-snapshot tester decision before a guarded bulk-request workflow runs, nor the sealed prospective holdout protocol. Gate checks protect reproducibility and security; they must not be used as a generic “data unavailable” stop condition. The detailed source matrix and acquisition rules are in `research/phase7/PPR4_DHAN_OPEN_SOURCE_ACQUISITION_PLAN.md`.

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

#### Phase 7 prediction-only available-data amendments

- **Extension 1 (Run #44):** daily cross-market/global price predictors; independently audited with no statistically significant family result and no candidate promoted. This is a documented negative result, not exhaustion of the method registry.
- **Extension 2 (proposed, not authorized):** pre-register the remaining free-data predictors G03 sector leadership, G14 FII/FPI flow, G15 DII flow, G17 advance/decline breadth, and F03/F04/F05 NIFTY option OI/volume features. The proposal is in `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md`. It uses official NSE archive source leads and a single global max-statistic bootstrap across all 35 method/horizon combinations. No full-history acquisition or empirical fit is allowed until the isolated tester approves the spec/source-feasibility gate and a separate exact-snapshot execution gate passes.

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

## 7. Completion / no-premature-null rule

A single failed model, family, backtest or phase is **never** sufficient to conclude that no usable strategy exists. The developer must complete the full pre-registered Phase 0-11 program, repair reproducible technical failures, rerun failed gates where scientifically valid, and preserve every null result before a final conclusion is issued.

The research remains finite and governed: the method universe is the pre-registered catalog in `METHOD_REGISTRY.md`, together with only explicitly documented amendments that pass the developer/tester governance gate. It must not become an uncontrolled infinite search or an unlogged optimization loop.

A final null conclusion is permissible only after the complete phase catalog, all declared candidate families, cost-aware execution tests, robustness gates and fresh-forward verification have been completed, or after a serious irreparable data/research limitation is formally recorded.

Literal “100% certainty” about future market direction is impossible. The scientific objective is the strongest defensible positive strategy evidence that survives the declared protocol.


## Holdout terminology control

The research protocol explicitly distinguishes a final **untouched holdout** from chronological training/validation folds and from the later fresh-forward verification. The final holdout must remain unopened during model selection and tuning.
