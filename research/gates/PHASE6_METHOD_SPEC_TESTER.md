# Phase 6 Frozen Method Specification — Independent Tester Review

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer specification commit: `b0dabfcfa72c1be1125203f98a257d566c4eeab5`
Developer resubmission commit: `3101f9088e1575b757ad43ef3442f25c2fb602dd`

## Decision

**REQUEST CHANGES — DO NOT EXECUTE PHASE 6 YET**

The resubmission materially improves pre-registration, but the tester found two substantive specification problems and several reproducibility clarifications that must be corrected before coding.

## Required corrections

### 1. I07 put-option break-even sign is incorrect / ambiguous
The specification says the probability for both CE and PE is the probability that the future underlying return “exceeds” the break-even threshold. For a long PE, the economically relevant event is a **downward** move beyond the put break-even, not an upward excess.

Required fix:
- CE: estimate P(return_H >= CE_break_even_return).
- PE: estimate P(return_H <= PE_break_even_return).
- Define the return break-even thresholds explicitly from strike, premium and spot using the exact observed contract terms.

### 2. I03 volatility adjustment is badly scaled
The current definition divides a bounded persistence score in [-1,1] by raw volatility and then clips to [-3,3]. Because NIFTY return volatility is much smaller than 1, this will routinely saturate near ±3 and destroys the intended variation in the score.

Required fix:
- use a dimensionless volatility ratio, e.g. current causal volatility divided by its training-block median;
- define the adjusted score explicitly so high/low volatility has a controlled effect;
- retain a fixed clip only after the dimensionless adjustment.

### 3. Exact quantile tie handling
E06/E07 must define how repeated quantile edges are handled when many observations share the same value. No library default that changes by version may silently alter bins.

### 4. Sample-entropy tolerance wording
Define exactly whether the 0.20*SD tolerance uses the current causal 100-observation window or a training-block statistic. The choice must be fixed and implemented identically at every walk-forward block.

### 5. Implementation-level numerical guards
The spec should explicitly define minimum-positive denominators and behavior when MFDFA scales lack enough finite segments, when ordinal patterns are degenerate, and when transition/state cells have no observations.

## Passed checks

- E01-E10 and I01-I10 match registered Family E/I methods.
- The scope remains finite and pre-registered.
- Causal/right-aligned windows are required.
- Training-only learned quantities are required.
- D07/E08/I08 component provenance is fixed.
- BLOCKED_DATA semantics are explicit.
- I10 uses fixed component weights and does not silently reweight blocked components.
- The no-result-driven-selection rule is clear.

## Disposition

No empirical Phase 6 implementation or hosted run should start until the two substantive mathematical corrections and the reproducibility guards above are incorporated and independently re-reviewed.

## Tester → Developer

Correct I07 break-even directionality, repair I03 scaling, and freeze the requested numerical/tie-handling rules. Resubmit the exact specification. Do not begin empirical execution.

## Developer → Tester

Independently re-audit the corrected formulas and confirm that the fixed specification is mathematically coherent, dimensionally sensible, causal and reproducible before workflow implementation.
