# Phase 7 Specification — Tester Review

**Status: REQUEST CHANGES**

Independent tester review of developer proposal `ba90a3aa4514cb72a08e5aa8640017c7849084e9`.

## Findings

### 1. P08 regime definition is incomplete
The proposal declares three states:
- low-vol/trend
- high-vol/trend
- high-vol/non-trend

This omits **low-vol/non-trend**, so the regime partition is not exhaustive.

**Required correction:** use an exhaustive four-state partition:
1. low-vol / low-trend
2. low-vol / high-trend
3. high-vol / low-trend
4. high-vol / high-trend

### 2. P08 trend-strength threshold is not frozen
The proposal says the absolute trend-strength threshold will be “defined in the implementation specification.” That leaves a scientific degree of freedom after the proposed gate.

**Required correction:** freeze the exact formula and threshold now, before implementation. Recommended reproducible definition:
- trend strength = absolute 20-observation mean return divided by 20-observation return standard deviation, with a deterministic numerical guard;
- high-trend = training-period median or another explicitly registered fixed quantile;
- the quantile must be frozen in the Phase 7 method specification itself.

### 3. P07 missing-base handling is under-specified
Phase 6 contains blocked methods. A stacking matrix therefore cannot assume all 20 predictors exist for every layer/horizon.

**Required correction:** explicitly state that, for each layer/horizon, the predictor set is the fixed set of Phase 6 methods that are EXECUTED for that cell. Blocked methods are omitted, never imputed, and never replaced. The set must be determined from the pre-existing Phase 6 artifact rather than selected using Phase 7 performance.

### 4. P03 small-sample behavior should be exact
The trimmed-mean rule says “when the available count is sufficient” without defining sufficient.

**Required correction:** define the exact minimum count and trimming count. Recommended: with n available forecasts, k=floor(0.10*n); if k=0, use the ordinary mean; otherwise remove k observations from each tail.

### 5. P07 chronological training/refit schedule should be frozen
“Each chronological evaluation block” is not sufficiently operational.

**Required correction:** explicitly define the same chronological walk-forward block structure used in the accepted Phase 5/6 protocol, or specify exact train/test block lengths and refit cadence before implementation.

## Gate consequence

No Phase 7 code or empirical execution should begin until these specification defects are corrected and independently re-reviewed.

**Tester → Developer:** revise the Phase 7 specification to freeze the exhaustive regime partition, exact trend metric/threshold, blocked-predictor handling, trimmed-mean rule, and chronological stacking schedule. Resubmit for tester approval.