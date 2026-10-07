# Phase 6 Implementation — Independent Tester Gate

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer submission: `research/gates/PHASE6_CODE_DEVELOPER_SUBMISSION.md`
Reviewed developer implementation commit lineage includes:
- `scripts/run_phase6_novel.py`
- `scripts/test_phase6_novel.py`
- `.github/workflows/phase-06-novel.yml`

## Decision

**REQUEST CHANGES — EMPIRICAL EXECUTION BLOCKED**

The frozen method specification itself had already been approved. The implementation is not yet safe to pass the code gate.

## Blocking findings

### 1. E06 implementation has a definite variable-name error
Inside `run_scope`, `e06_train_model` is called as:

`selected_lag, mi, table, train_sorted = e06_train_model(...)`

but the returned/reference variable is later used as `train_reference`.

This is an execution-breaking NameError path whenever E06 reaches the selected-lag branch.

Required fix:
- use one consistent variable name;
- retain the training-only reference returned by the fitter;
- add a direct regression test that fits E06 on synthetic data and applies a test value without using future observations.

### 2. E06 training/test binning semantics need a stronger regression pin
The source now defines a training reference and a deterministic mapping, which is directionally correct, but the test suite does not prove that changing observations after the training cutoff leaves the fitted E06 reference/table and selected lag unchanged.

Required fix:
- construct two synthetic series identical through the training cutoff but different afterward;
- assert identical E06 fitted lag, MI, reference and conditional-probability table;
- assert test predictions are changed only by the changed test input, not by recomputation of training bins.

### 3. E07 remains mathematically under-specified despite being BLOCKED_DATA today
The method specification calls the source a “predeclared global risk-on/off composite” but does not freeze the exact composite formula, source weights or aggregation rule.

This does not invalidate the current BLOCKED_DATA status, but it leaves the registered method non-reproducible when the required source history is later available.

Required fix:
- define the exact global component set, timing alignment, normalization and aggregation rule before any future E07 execution.

### 4. Workflow schema gate is too weak
The empirical schema validation checks method presence/status and broad metric ranges, but it does not verify:
- confusion-matrix reconciliation;
- probability-bin count reconciliation;
- non-empty execution coverage for methods that are expected to be EXECUTED;
- explicit required reasons for BLOCKED_DATA/BLOCKED_RUNTIME;
- absence of unexpected NaN/null values in mandatory executed metrics.

Required fix:
- strengthen the schema validator before empirical execution is authorized.

## Non-blocking observations

- The empirical job is correctly hard-gated on `research/gates/PHASE6_CODE_APPROVAL_TESTER.md`; no empirical run has been authorized by this tester report.
- The automatic/manual workflow structure is appropriate.
- Causal future-row mutation tests cover Hurst, MFDFA, sample entropy, permutation entropy and roughness, and fixed I03/I07/I08/I09 semantics.
- Option/global/liquidity inputs are conservatively handled as BLOCKED_DATA rather than replaced by retrospective proxies.

## Disposition

**REQUEST CHANGES.** The developer must correct the implementation and resubmit the code gate. No Phase 6 empirical workflow is authorized.

## Developer → Tester

Correct E06, strengthen the E06 cutoff-invariance test, freeze E07's exact composite definition, and strengthen workflow schema validation. Resubmit the implementation package.

## Tester → Developer

Re-audit the corrected code, regression suite and workflow. Approval requires a clean E06 path, explicit E07 reproducibility and a schema gate strong enough to prevent silent invalid artifacts.
