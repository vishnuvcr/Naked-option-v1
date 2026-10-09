# Independent Tester Static Review — P10 Diagnostic Block Invariant

**Decision: REQUEST CHANGES FOR SCIENTIFIC PROMOTION — static protocol/code consistency issue remains open**  
**Review type:** static contract review only; this is not the empirical artifact audit for Run #994.  
**Frozen protocol file:** `research/phase7/PHASE7_METHOD_SPEC.md`, identical blob at Run #925 commit `682eadf2a9eb4de250bc3db27d02e57f88687fa1` and Run #994 commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.

## Finding

The frozen specification explicitly states: “P08/P09/P10 regime diagnostics are retained only for chronological evaluation blocks containing at least one finite evaluated label/probability observation, and diagnostic block count must equal the candidate chronological-block count.”

However, the current implementation and validator are inconsistent with that explicit three-candidate invariant:

1. `scripts/run_phase7_ensemble.py` constructs a shared `regime_diag` from P01/P04 probability availability and finite regime features, then attaches that same diagnostic array to P08, P09 and P10.
2. The headline/block diagnostics for P10 apply its registered inclusive abstention mask [0.45, 0.55]. A chronological test block with no P10-eligible row may therefore be omitted from P10's `chronological_blocks`, while remaining in the shared `regime_diagnostics`.
3. `scripts/validate_phase7_results.py` now checks the regime-diagnostic/chronological-block count equality only for P08/P09. Its comment says P10 may have fewer eligible blocks, but the frozen specification still includes P10 in the equality rule.
4. The pinned independent auditor recomputes P10 regime diagnostics and its abstention-masked block metrics independently, but does not explicitly enforce the frozen specification's block-count equality for P10. Thus an empirical artifact could pass its current numeric checks without this literal protocol condition being resolved.

## Required disposition

- Do not change the frozen specification or relax a test after observing Run #994 results.
- Run #994 is already executing on immutable source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`. It may complete and its artifact may be independently audited, but **no Phase 7 method, metric or strategy is promotable while this contract mismatch remains unresolved**.
- Before any subsequent empirical run, the developer should prepare a correction proposal that either makes P10 regime diagnostic inclusion match P10's eligible chronological-block rule while keeping its abstention behavior, or formally proposes a pre-registered specification amendment. The proposed choice must be mathematically explicit and must not change results retrospectively.
- The tester must separately approve the corrected implementation or protocol amendment before another empirical execution; the approval must cover a regression where a complete block is P10-abstained and verify the [0.45, 0.55] endpoints.

## Instructions

**Tester → Developer:** Resolve the exact frozen-spec invariant above, add a regression test for a fully abstained chronological block, and resubmit the proposed patch/spec amendment for independent review. Do not alter Run #994's immutable source or use its results to select a strategy.

**Developer → Tester:** Continue the exact-run audit if Run #994 artifacts appear, include this invariant in the report, and preserve REQUEST CHANGES/no-promotion if the artifact or code contract fails. Phase 8 remains blocked.
