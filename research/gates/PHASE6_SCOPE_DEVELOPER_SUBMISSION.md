# Phase 6 Novel-Method Scope — Developer Resubmission

Date: 2026-10-07
Developer branch: `phase-05-developer`
Precondition: Family D run #23 tester gate = PASS WITH SCOPED RESTRICTIONS.
Previous tester decision: REQUEST CHANGES on under-specified exact method definitions.
Frozen method specification: `research/phase6/PHASE6_METHOD_SPEC.md`.

## Purpose

Phase 6 will test the pre-registered novel-information and complexity methods without selecting a winner from prior Family D maxima. The phase remains directional-model screening; option execution and final strategy promotion remain later gates.

## Registered scope

### Family E — Regime and information
- E01 Hurst with random-walk/surrogate controls
- E02 multifractal/MFDFA diagnostics
- E03 entropy / approximate entropy / sample entropy
- E04 permutation entropy
- E05 complexity / roughness
- E06 mutual information
- E07 transfer entropy / information flow
- E08 regime-conditioned model switching
- E09 volatility-state classifier
- E10 trend/volatility regime matrix

### Family I — Novel metrics
- I01 multi-scale directional pressure index
- I02 cross-market lead-lag pressure score
- I03 volatility-adjusted trend persistence score
- I04 option-surface directional asymmetry score
- I05 regime transition pressure index
- I06 liquidity-friction-adjusted signal quality
- I07 probability-of-move-vs-premium efficiency score
- I08 entropy-weighted ensemble confidence
- I09 abstention / edge-density score
- I10 composite Direction Conviction State score

No new method outside this registry will be added during the phase without a pre-result protocol amendment and tester approval.

## Data policy

1. Use the canonical point-in-time datasets and snapshots already accepted in Phases 2-5.
2. Use only free sources first for any explicitly required supplemental input; provenance, availability timing, snapshot hash and source lineage must be recorded.
3. Do not substitute a non-PIT proxy for a missing input. A method whose required input is unavailable is recorded as BLOCKED_DATA.
4. Options-derived methods must use only contract/surface variables demonstrably available at the decision timestamp.
5. Cross-market and event features must obey conservative next-session semantics where historical publication timestamps cannot be demonstrated.
6. All data transformations are training-only where learned parameters exist.

## Labels and evaluation

- Use the frozen Phase 3 directional labels and horizons: intraday 5/15/30/60/120 minutes; positional +1/+2/+3/+5/+10 sessions.
- Intraday evaluation remains on the frozen hourly decision grid with exact H-minute labels on the 1-minute path.
- Chronological walk-forward refits use the tester-approved 20-trading-session cadence where model fitting is required.
- Report the same directional diagnostics used for Family D: n, class rate, accuracy, balanced accuracy, ROC-AUC, PR-AUC, Brier, log-loss, confusion matrix, block-bootstrap accuracy interval and probability-bin future-return diagnostics.
- Information-theoretic quantities must report estimator/window settings and finite-sample safeguards.
- Regime methods must report state/regime counts and transition definitions.
- Abstention methods must report coverage and conditional performance rather than silently dropping observations.

## Leakage and reproducibility controls

- Feature timestamp/availability must be no later than the decision timestamp.
- No final holdout access.
- No method selected because of observed final-horizon performance.
- All random components use deterministic seeds.
- Every method/horizon receives an explicit status: EXECUTED, BLOCKED_DATA, NOT_APPLICABLE or BLOCKED_RUNTIME.
- Every artifact records git SHA, input lineage, configuration, seed and digest.

## Gate deliverables

The Phase 6 workflow must:
1. run static/regression tests first;
2. acquire/restore only declared data;
3. execute the complete registered E/I matrix or document a precise BLOCKED_DATA disposition;
4. validate result schema;
5. upload an immutable artifact;
6. stop before Phase 7 until the tester audits the artifact.

## Promotion boundary

Phase 6 is not an economic promotion gate. A high directional metric is a research lead only. No option strategy may be selected from Phase 6 without the later option-break-even, Paytm Money brokerage, spread/slippage/latency, multiple-testing, robustness and untouched-forward gates.

## Developer request to tester

Independently review whether this scope is consistent with the registry, protocol, previously accepted data restrictions, and the finite research plan. In particular, check that:
- no unregistered method is being introduced;
- E/I methods have explicit data-status handling;
- information-theoretic methods cannot use future labels or future normalization;
- abstention coverage is reported honestly;
- the proposed workflow can be audited reproducibly.

## Tester instruction

Return PASS / REQUEST CHANGES with concrete reasons before any Phase 6 empirical implementation or workflow execution.


## Corrections from tester request-changes
The exact E01-E10 and I01-I10 mathematical/algorithmic definitions are now frozen in `research/phase6/PHASE6_METHOD_SPEC.md`. The specification fixes estimator windows, discretization, thresholds, state rules, component sets, weights, seeds, backoff rules and BLOCKED_DATA semantics before empirical inspection.

The developer also accepts the tester-mandated causal mutation tests for every derived rolling/information feature, explicit no-centered-window checks, training-only binning/normalization assertions, deterministic regime/backoff tests, fixed-constant assertions and probability-range checks.

## Resubmission request to tester
Independently review `research/phase6/PHASE6_METHOD_SPEC.md` against the registry and protocol. Do not treat the specification as approved merely because it is deterministic; check for mathematical/sign/causality problems and data-availability contradictions before granting empirical execution.
