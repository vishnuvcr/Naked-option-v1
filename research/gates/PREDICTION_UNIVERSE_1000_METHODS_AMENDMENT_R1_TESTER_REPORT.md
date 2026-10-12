# Independent Tester Review — 1,000+ Prediction-Method Amendment R1

Date: 2026-10-12
Decision: **REQUEST CHANGES**
Reviewed developer commit: `65dd011139e62ff17289c4a29a94602e92ef9fe3`
Reviewed proposal blob: `e0ad50a05447d062d4ec2a02f5dcc8ac8c2f2c8b`
Scope: protocol only. No market data, untouched holdout, or empirical model results were opened.

## Summary

R1 correctly acknowledges that the 112-entry named registry and 4,800-cell Phase 8 option-execution grid do not satisfy the 1,000+ distinct prediction-method requirement. Its prediction-first boundary, chronological evaluation, failure retention and tester gates are directionally appropriate. However, the protocol is not sufficiently precise to authorize registry construction or empirical execution.

## Blocking findings

### T1 — Method distinctness is not operationally testable
“Substantively distinguishable” has no reproducible decision rule. Require canonical fields for algorithm/rule family, mathematical decision function or architecture, learning objective, input representation, causal information set, target/horizon class and inference/abstention operator. Specify which changes constitute a new method versus a configuration. Require canonical JSON normalization, SHA-256 method fingerprints and a duplicate/near-duplicate report. Seeds, folds, data windows, scalar hyperparameter changes and renamings must not create new method IDs.

### T2 — Finite configuration manifest lacks a completeness contract
Require stable configuration IDs and hashes, parent method IDs, top-level method/configuration counts, expected batch IDs, code/input hashes and a reconciliation rule proving every config ended in EXECUTED or a documented BLOCKED/FAILED state. Missing or duplicated configurations must fail validation.

### T3 — Multiple-testing plan is underspecified
“Appropriate” correction could be chosen after observing results. Before execution, freeze primary metrics per target/horizon, null/baseline, hypothesis family, correction method and threshold, dependence-aware resampling plan, and descriptive-only metrics. Report raw and adjusted p-values/q-values where applicable, effect sizes and uncertainty intervals.

### T4 — Resource and deterministic batch plan is missing
Publish expected configuration counts, per-batch time/memory budgets, deterministic sharding, cache/reuse policy, checkpoint/restart semantics and failure taxonomy. Slow methods must not be silently skipped; resource blockers require evidence and review.

### T5 — Historical-result count credit needs a hard boundary
Historical Phase 3–7 results count only if immutable pre-existing specification, exact code/input hashes, configuration coverage and result artifact map to a canonical V2 record without post-result changes. Otherwise mark HISTORICAL_NOT_COUNTED. No retrospective count credit by name or narrative.

## Additional controls

Keep intraday and positional targets separate; predefine minimum sample and missingness rules; do not access the untouched holdout during protocol review; Phase 8 results may be audited for integrity but must not select predictors. The finite stopping rule is appropriate.

## Decision

**REQUEST CHANGES — protocol only.** No empirical method was run and no prediction result was accepted. Registry V2 generation and all new empirical prediction batches remain BLOCKED until R2 passes independent review and the registry/configuration manifest passes its own gate.

**Tester → Developer:** address T1–T5, pin R2, and resubmit. Do not run models or access the holdout.
**Developer → Tester:** resubmit the exact committed protocol and hashes for independent review.