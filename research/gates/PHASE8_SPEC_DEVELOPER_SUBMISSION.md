# Phase 8 Specification — Developer Submission

**Branch:** `phase-08-developer`  
**Status:** SUBMITTED FOR INDEPENDENT TESTER REVIEW  
**Empirical execution:** NOT AUTHORIZED

## Files submitted

- `research/phase8/PHASE8_METHOD_SPEC.md`
- `research/phase8/PHASE8_DATA_PLAN.md`
- `research/phase8/PHASE8_LITERATURE_REVIEW.md`

## Frozen submission scope

This submission freezes:

- use of the accepted Phase 7 P01-P10 forecasts without result-driven reselection;
- CE/PE mapping;
- delta targets 0.40/0.50/0.60;
- DTE buckets 0–1, 2–5, 6–10 and 11–21 trading sessions;
- deterministic contract-selection tie-break rules;
- one-minute entry latency and no same-bar fill;
- four fixed exit policies;
- quote-backed versus OHLC/proxy execution distinction;
- four cost scenarios;
- date-aware Paytm/NSE/statutory costs;
- date-aware lot-size and expiry metadata;
- one-lot/no-pyramiding primary exposure;
- the Phase 8→Phase 9 shortlist rule;
- free-source-first acquisition and point-in-time controls;
- mandatory regression/data-quality gates before empirical execution.

## Tester request

Independently check:

1. mathematical definitions and charge arithmetic;
2. timestamp causality and contract-selection chronology;
3. lot-size/expiry point-in-time handling;
4. whether the finite execution universe is actually frozen and complete;
5. whether no parameter can be tuned from Phase 8 outcomes;
6. whether quote/proxy execution is correctly separated;
7. whether the Paytm/NSE charge schedule is sourced and versioned correctly;
8. whether the Phase 8 shortlist rule is auditable;
9. whether data availability and missing-fill rules can induce survivorship/selection bias;
10. whether the implementation plan can be reproduced in GitHub Actions with cached data and manual dispatch.

Do not authorize empirical execution until all requested changes are resolved and the tester gate is recorded.


## Pre-review clarification
- The Q1 OHLC/proxy execution track now has a fully frozen synthetic half-spread rule: C0 0.50%, C1 1.00%, C2 2.00%, C3 4.00% of premium per leg, floored at one point-in-time option tick. Incremental C0-C3 slippage remains separately 0%, 0.25%, 0.50%, 1.00% per leg. This clarification was made before tester review and is not based on Phase 8 performance.
- The literature review was supplemented with open-source/qualitative execution evidence; none is treated as quantitative validation.


## Tester correction cycle archived
- Independent tester gate `research/gates/PHASE8_SPEC_TESTER.md` = REQUEST CHANGES.
- Ten reproducibility/auditability issues were identified before empirical execution.
- Developer corrected the current lineage by freezing liquidity lookbacks, entry/exit tolerances, data-quality thresholds, historical brokerage fallback, delta fallback inputs, Run #654 reconstruction tolerance, the exact 4,800-cell execution universe, anomaly-concentration checks, 20-session option-P&L blocks, and overlap-skipping behavior.
- No empirical strategy result was generated during this correction cycle.
