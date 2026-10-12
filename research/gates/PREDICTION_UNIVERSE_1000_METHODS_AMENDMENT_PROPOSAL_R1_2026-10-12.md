# Prediction Universe Expansion — R1 Amendment Proposal
Date: 2026-10-12
Status: **PROPOSED — NOT APPROVED; independent tester gate required before implementation or model execution**
Owner branch: `phase-08-prediction-developer`
Tester branch: `phase-08-prediction-tester` (independent review only)

## 1. Why this amendment is required

The current `research/METHOD_REGISTRY.md` contains 112 named registry entries across families A–J (A01–A05, B01–B13, C01–C12, D01–D15, E01–E10, F01–F15, G01–G18, H01–H06, I01–I10, J01–J08). This is not 1,000 prediction methods.

The latest Phase 8 run #38229793041 evaluates 4,800 forecast-to-option execution configurations under four cost scenarios. Those cells are execution/contract/exit configurations, **not 1,000 prediction methods**. They must not be presented as satisfying the prediction-method target.

The user's research priority is prediction first. Strategy economics are downstream and must not substitute for directional-prediction coverage.

## 2. Proposed research requirement

Before a prediction phase can be declared exhausted, build a tester-approved, versioned registry containing at least **1,000 distinct prediction-method definitions**. The count must not be inflated by merely changing a seed, fold, ticker name, horizon, or one numeric hyperparameter. Each method must have a substantive distinguishable rule, feature construction, model architecture, learning objective, information-combination mechanism, calibration/uncertainty mechanism, or causal decision policy.

For every method, separately pre-register a finite configuration grid and test every eligible configuration in that grid. Report method count and configuration count separately. Do not claim to test a literal infinite configuration space: “all configurations” means all entries in the frozen, finite machine-readable manifest.

The candidate manifest is generated before looking at new comparative performance, given stable IDs, and SHA-256 hashed. Any additions after result inspection require a documented protocol amendment and fresh tester approval.

## 3. Prediction-only boundary

Until the expanded prediction registry and its independent result audits are complete:
- Do not promote, select, or tune a trading strategy using the Phase 8 option-P&L grid.
- Keep option selection, exit-policy and profitability comparisons explicitly downstream.
- The completed Phase 8 Q1/OHLC proxy artifact remains archived as exploratory execution evidence; it does not count toward the 1,000-method target.
- Do not open or reuse the untouched holdout for model selection.
- Preserve every executed, failed, blocked, and rejected candidate with a reason and immutable artifact reference.

Existing accepted results from Phases 3–7 remain historical evidence, but count toward the new target only if their exact method identity, frozen specification, configuration coverage, data provenance and output artifact can be reconciled to the new manifest. No retrospective relabeling of old runs as distinct methods.

## 4. Required method families to cover

The registry amendment must include, where the relevant data passes source/PIT gates:
1. naive, class-prior, persistence and cost-aware break-even baselines;
2. technical trend, momentum, mean-reversion, breakout, range and price-action rule families;
3. statistical, econometric, time-series, state-space, Bayesian, change-point and survival/first-passage methods;
4. generalized linear/additive, discriminant, prototype, kernel, tree, bagging, boosting and calibrated ensemble methods;
5. neural architectures and sequence/temporal models under strict chronological training;
6. volatility, entropy, complexity, scaling, information theory and regime-switching methods;
7. options IV/skew/term structure/Greeks/OI/volume/liquidity and option-surface representations;
8. global-market, cross-index, futures, FX, rates, commodities, gold and volatility lead-lag signals;
9. FII/FPI/DII, breadth, sector rotation, macro events, calendar effects and corporate-action indicators;
10. news/sentiment/event features only where historical timestamps and point-in-time source provenance are valid;
11. feature selection, causal lag rules, normalization, missing-data strategies and robust representation learning;
12. multimodal fusion, cross-family interactions, mixture-of-experts, dynamic weighting, calibration, conformal/uncertainty and abstention mechanisms;
13. newly invented candidate methods with frozen mathematical definitions and synthetic correctness tests.

These family labels are coverage requirements, not an accepted list of 1,000 methods by themselves. The detailed definitions and grid must live in the machine-readable registry before empirical comparison.

## 5. Configuration manifest and evaluation design

Each registry record must specify:
- stable method ID, mathematical/algorithmic definition, intended signal, source code hash and tests;
- input features and lag/availability requirements, with point-in-time provenance;
- target and label definition; intraday and positional horizons remain separated;
- model-specific parameter values or bounded parameter grid, preprocessing, lookback and refit cadence;
- causal chronological split, training-only scaling/selection/calibration and purge/embargo when required;
- metrics and null/baseline comparator, including Brier/log loss and calibration for probabilistic predictions, AUC/PR and balanced accuracy where suitable;
- missing-data and failure policy, required sample minimums, runtime estimates and data dependencies;
- candidate status: NOT_RUN, EXECUTED, BLOCKED_DATA, BLOCKED_GATE, FAILED_TECHNICAL, REJECTED_EMPIRICAL or ACCEPTED_FOR_NEXT_GATE;
- artifact IDs, full-run hashes, fold/block metrics, and tester decision.

Test all entries in the frozen finite grid or report a specific technical/data blocker for each. No candidate may disappear because it performs poorly. Record runtime failures in `research/ERROR_LOG.md`; record phase and candidate disposition in status/results tables.

## 6. Validation, multiple testing and gates

- Split by time; no random row split for time-series outcomes.
- Fit all transformations and feature selection on training data only.
- Maintain a clean distinction between in-sample fitting, validation/tuning, chronological out-of-sample evaluation and untouched forward evaluation.
- Store per-candidate/per-fold metrics and aggregate them only using frozen rules.
- Apply appropriate family-wise or false-discovery controls, block bootstrap and data-snooping-aware selection corrections before calling any method promising.
- Do not use Phase 8 execution results to select the prediction model.
- Developer submits one immutable family/batch artifact; the independent tester reconciles counts, code/hash, leakage, metrics and failures before the next batch/phase is authorized.
- Phase 9 robustness and Phase 10 fresh-forward remain mandatory; a 1,000-method sweep alone is not sufficient evidence of an edge.

## 7. Finite stopping rule

The expanded registry must be finite and frozen. Research stops when every registered method and each of its declared configurations is either (a) run and independently audited, (b) blocked with an independently verified reason, or (c) rejected with a documented empirical reason; surviving candidates then complete the pre-registered multiple-testing, robustness and fresh-forward gates. Do not expand indefinitely after viewing results.

## 8. Immediate next steps (not yet authorized)

1. Independent tester reviews this proposal only; no empirical data/model execution as part of this review.
2. On approval, create `METHOD_REGISTRY_V2` (machine-readable JSON/CSV plus human-readable index) with at least 1,000 substantive method definitions and all bounded configs.
3. Have the tester independently validate uniqueness, configuration coverage, manifest hash, leakage contracts, resource plan and test completeness.
4. Only then schedule prediction-only batches on the designated developer branch and require result-level tester gates after each batch.
5. Reclassify Phase 8 run #38229793041 as downstream exploratory execution evidence; finish its independent artifact audit for integrity/accounting, but do not use it to select prediction methods.
6. Update the main README, phase status, error log, candidate registry and conversation log at every completed gate.

**Developer → Tester:** Independently assess whether this amendment faithfully implements the explicit 1,000+ distinct prediction-method requirement, whether the uniqueness rule prevents configuration-count inflation, and whether the finite configuration/evaluation protocol is reproducible. Report PASS or REQUEST CHANGES on the tester branch; do not fit models or access the holdout.

**Tester → Developer:** Submit only a hash-pinned independent review. If approved, return the required corrections or bounded clarifications; keep all empirical prediction execution blocked until V2 manifest and code have separately passed their gates.
