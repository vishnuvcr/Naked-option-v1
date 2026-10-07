# Phase 5 Exact Sequence Precomputation Tester Review

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer commits reviewed: `2d7755b38af1bcca5d557483c2703e7d3a7ad804`, `3bb5fe0c17c1dce92624059a40b9e140d2c2814f`

## Gate result

**PASS — COMPUTATIONAL OPTIMIZATION ONLY**

## Independent checks

1. `precompute_sequence_representations()` calls the same deterministic `sequence_features()` function used previously.
2. The precomputed array is a row-aligned cache; it contains NaN where the causal warm-up is unavailable and the exact representation at every valid endpoint elsewhere.
3. D13-D15 continue to train only on rows strictly before the current `train_end`; no labels are used to construct representations.
4. Intraday session grouping is passed through unchanged, so no cached sequence window can cross a trading-session boundary.
5. The regression test explicitly verifies that the cached representation equals the previous direct construction for every row.
6. This correction changes computation only. Model definitions, labels, fit chronology, refit cadence, features, and promotion criteria are unchanged.

## Disposition

The optimization is approved for hosted execution. It is acceptable to supersede the currently long-running pre-optimization run, which will remain preserved as non-evidence.

## Tester instruction to developer

Run the fresh hosted Family D workflow with the exact-representation cache. Preserve the pre-optimization run as rejected/superseded evidence. Do not alter statistical definitions.

## Developer instruction to tester

Independently inspect the next artifact, then audit numerical consistency, sample denominators, D07 calibration isolation, and D13-D15 session-boundary behavior before issuing the final Family D gate.
