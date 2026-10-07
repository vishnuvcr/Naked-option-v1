# Phase 6 Frozen Method Specification — Tester Approval

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer corrected specification commit: `eb9030ff35c38291392c49936451e7d4de8ff16d`

## Decision

**APPROVED FOR PHASE 6 IMPLEMENTATION AND PRE-EMPIRICAL TESTING**

The previous I07 directionality and I03 scaling defects are corrected, and the remaining estimator edge cases are sufficiently specified for coding.

## Independent checks

- I07 now has correct side-specific favorable events: CE requires an upward move to call break-even; PE requires a downward move to put break-even.
- Invalid PE break-even cases are blocked rather than clipped.
- I03 now uses a dimensionless volatility ratio instead of dividing by raw volatility.
- E06/E07 binning is deterministic under repeated values via explicit average ranks.
- E03 tolerance is explicitly based on the current causal 100-observation window.
- MFDFA, permutation entropy, sample entropy and transition edge cases have explicit neutral/fallback behavior.
- E08 model switching is fixed ex ante and cannot be changed based on observed test performance.
- I08 component membership and weighting are fixed.
- I09 abstention coverage is explicitly reportable.
- I10 fixed component weights and BLOCKED_DATA behavior are explicit.
- No new method outside the registered E/I universe was introduced.

## Conditions for the implementation gate

Before any hosted Phase 6 empirical execution, the developer must:
1. implement the frozen formulas without silent substitutions;
2. add causal future-row mutation tests for each rolling/information-theoretic feature family;
3. test deterministic rank binning and fixed constants;
4. test probability bounds and all specified fallbacks;
5. persist explicit method status (EXECUTED/BLOCKED_DATA/BLOCKED_RUNTIME/NOT_APPLICABLE);
6. run a static/regression workflow on the exact submitted commit;
7. submit the workflow/code/regression package for tester review before the empirical run.

No Phase 6 result may be accepted before the independent tester audits the immutable artifact.

## Tester → Developer

Proceed to implementation of the exact frozen specification. Submit the Phase 6 implementation/regression package for gate review before launching the empirical suite.

## Developer → Tester

Independently inspect the Phase 6 code, formulas, causality tests, workflow controls and data-status handling once submitted. Do not approve empirical execution based on code inspection alone if the static/regression gate fails.
