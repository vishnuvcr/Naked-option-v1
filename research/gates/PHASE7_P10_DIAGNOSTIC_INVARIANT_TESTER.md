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
 
## Developer resubmission — correction for independent review (2026-10-09)

Developer commit submitted: [`39e964d4ae99bb02b113fa4eabecd91c9af46c16`](https://github.com/vishnuvcr/Naked-option-v1/commit/39e964d4ae99bb02b113fa4eabecd91c9af46c16) on `phase-07-developer`.

Proposed changes for the tester to independently inspect:
- `regimes(...)` now retains original chronological block IDs alongside diagnostic records.
- New `candidate_regime_diagnostics(...)` filters P10 regime diagnostic records using the registered P10 eligible-row mask (finite label/probability and outside the inclusive [0.45, 0.55] abstention interval); P08/P09 diagnostics remain unchanged.
- `scripts/validate_phase7_results.py` now enforces regime diagnostic block-count equality for P08/P09/P10.
- `scripts/test_phase7_ensemble.py` includes a synthetic three-block fixture in which block 0 is fully abstained at the interval endpoints, block 1 is partly eligible, and block 2 has eligible rows just outside the endpoints; it asserts two retained P10 diagnostics and two metric blocks.
- The developer protocol workflow's regression job passed for this commit, but its empirical and tester-gated jobs were skipped because this was a source-code change on the developer branch, not an authorized empirical execution. This is not tester approval.
- The already-running Run #994 is immutable at source SHA `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`; the proposed correction cannot retroactively alter its output.

**Tester disposition required:** review the proposed code and test independently; verify block IDs stay aligned when a regime diagnostic is omitted; confirm P10 eligibility semantics and inclusive endpoints; ensure P08/P09 output and fallback accounting are unaffected; check the test's expected block counts against `block_diagnostics`; and issue PASS or REQUEST CHANGES. Do not approve based only on the developer workflow's regression pass. Even after code review, no Phase 8 promotion until the exact empirical artifact audit passes and the current immutable run is properly dispositioned.
 
## Independent review of developer correction commit 39e964d — 2026-10-10

**Code-review disposition: PASS FOR A FUTURE RUN ONLY; NO RETROACTIVE CHANGE TO RUN #994.**

Review performed against developer commit `39e964d4ae99bb02b113fa4eabecd91c9af46c16`, the frozen specification, the new synthetic regression and the unchanged Run #994 audit:

- The helper retains block IDs from the original regime diagnostic list and filters only P10 diagnostics whose block has no finite label/probability outside the inclusive [0.45, 0.55] abstention band.
- P08/P09 return the original diagnostics unchanged.
- The fixture exercises both endpoints (0.45 and 0.55 are abstained), a mixed block, and eligible probabilities below the lower endpoint; expected retained diagnostic IDs [1,2] and two metric blocks are consistent with `block_diagnostics`.
- The validator restores the stated count equality for P08/P09/P10.
- The Phase 7 developer CI run #1068 passed the regression step. This tester review is a static/code-contract review, not an independently executed hosted test job.

**Scope restriction:** this correction is on the developer branch after Run #994's immutable source SHA `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`. It does not alter Run #994's predictions or its report. The Run #994 technical audit remains PASS WITH SCOPED RESTRICTIONS; its family tests are all non-significant and it promotes no strategy. A fresh, pre-authorized run using the corrected commit must still pass the exact-run artifact audit, and options-level point-in-time data, costs/slippage and after-cost profitability gates remain mandatory before Phase 8.
