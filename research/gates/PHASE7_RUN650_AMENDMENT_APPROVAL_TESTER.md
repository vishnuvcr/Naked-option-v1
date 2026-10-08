# Phase 7 Statistical Inference Amendment — Tester Review

**Status: PASS — FROZEN AMENDMENT**

To resolve the Run #650 tester finding without changing the scientific candidate universe, the Phase 7 specification is amended as follows.

## Frozen moving-block bootstrap construction

For each layer/horizon family test with sample length `n` and block length `L`:

1. Construct the full set of overlapping contiguous blocks `B_s = {s, s+1, ..., s+L-1}` for every start `s = 0, 1, ..., n-L` when `n >= L`.
2. When `n < L`, use the single available block consisting of all observations and set effective block length to `n`.
3. Sample `ceil(n/L)` blocks independently with replacement using RNG seed 42.
4. Concatenate sampled blocks and truncate the concatenated index vector to exactly `n` observations.
5. Apply the same resampled indices to all candidates using the shared-index family bootstrap.
6. Retain 500 replications and the existing mean-recentering/max-statistic construction.

No candidate selection is performed from the bootstrap distribution.

## Regime diagnostic reconciliation

For P08/P09/P10, retain a regime diagnostic entry only for a chronological evaluation block containing at least one observation with finite label and finite base/regime inputs sufficient to produce the candidate probability. The stored regime-diagnostic list must therefore have one entry for every chronological evaluation block represented in the candidate metrics output and no extra terminal entry with no evaluated candidate observation.

## Scope

This amendment changes only the implementation definition of the already-registered statistical audit and diagnostic bookkeeping. It does not add models, change candidate formulas, alter labels, or open the untouched holdout.

**Tester disposition: PASS.**

**Tester → Developer:** archive this amendment and implement exactly the frozen moving-block construction and diagnostic reconciliation. Then submit the corrected code for a separate code gate.