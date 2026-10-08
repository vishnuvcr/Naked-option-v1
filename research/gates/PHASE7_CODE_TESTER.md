# Phase 7 Implementation Code Gate — Tester Review

**Status: REQUEST CHANGES**

Tester independently reviewed developer implementation commit `9da72d20161a598616775026e38c6d1719ca5480`.

## Findings

### 1. Mandatory family-level multiple-testing control is not implemented
The frozen specification requires White Reality Check / SPA-style data-snooping control or an equivalent declared family-level correction.

The current implementation reports ordinary forecast metrics only. It does not compute a family-level max-statistic bootstrap or an equivalent multiple-comparison-adjusted inference.

**Required correction:** implement a pre-registered dependent bootstrap family test against the frozen historical positive-rate baseline. Use a shared resampling index across candidates, preserve temporal blocks, recenter candidate loss differentials under the null, and report the observed maximum statistic plus a family-level p-value. The number of bootstrap replications and block construction must be frozen in code/spec before execution.

### 2. P08/P09 regime state is calculated but not retained
The implementation now applies the approved 0.5 base + 0.5 regime-rate formula, but the regime state counts are not recorded in the output.

**Required correction:** report four-state test counts for P08-P10 and the corresponding training fallback counts. This is necessary to audit whether a candidate is driven by a tiny regime.

### 3. Chronological block diagnostics are absent
The specification requires chronological block performance.

**Required correction:** store per-test-block accuracy, balanced accuracy and Brier score for every P01-P10 candidate. Do not use these block results for post-hoc model selection in the same run.

### 4. Regression coverage is too weak
The current test is mostly source-token checking. It does not numerically verify:
- exact P03 trimming;
- P07 causal training excludes the current block;
- P08/P09 exact 0.5 calibration formula;
- four-state regime partition;
- abstention masks;
- family-bootstrap recentering.

**Required correction:** add deterministic synthetic-array tests for these properties.

### 5. Literature/spec mismatch must be documented
The specification now explicitly invokes probability-combination calibration and data-snooping controls. The implementation must preserve these as methodological requirements, not merely comments.

## Gate consequence

No Phase 7 empirical execution is authorized.

**Tester → Developer:** implement the family-level data-snooping test, regime/block diagnostics, and numerical regression coverage. Resubmit the complete code for an independent code gate.