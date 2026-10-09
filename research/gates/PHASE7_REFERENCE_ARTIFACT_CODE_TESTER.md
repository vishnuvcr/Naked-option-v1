# Independent Tester Code Review — Phase 7 row-level reference artifact

**Decision: PASS WITH SCOPED RESTRICTIONS — artifact-output code only**  
**Reviewed developer commit:** `c380ad39ffb34557316fe36a060c3659330a4440` (test addition) and predecessor implementation `fc16bd6ca443d7cbd8322f65024f472efb69a85e).  
**Scope:** capture same-run predictions and provenance; no approval to change scientific methods or accept new metrics.

## Findings

- The new panel writer receives the same candidate arrays, labels, future returns and chronological block indices that the existing aggregate metrics loop uses. It does not refit models or transform probabilities.
- For intraday rows, the timestamp mask matches the Phase 7 hourly decision grid (minute-of-day 570 through 930, hourly). Daily rows use the loaded daily date column. Row-count checks fail closed.
- Each horizon panel contains P01–P10 probability columns plus labels, future return, stable source row index, decision timestamp, chronological block index, run ID and commit SHA.
- The manifest records panel hashes, aggregate JSON hash, source-file hashes, code-file hashes, runtime/package versions, platform/machine and threadpool fingerprint. Missing source/code files cause a hard failure.
- The regression tests exercise row alignment, block assignment, prediction preservation, panel hashing and manifest structure. The output path is additive; aggregate result keys and calculation calls remain unchanged.

## Required restrictions / follow-up

1. This gate does **not** authorize empirical execution by itself. The current in-flight Run #831 started before this code review was archived and must be treated as **NON-EVIDENCE** for accepting the new artifact, even if it finishes successfully.
2. Add the reference-artifact regression test to the Phase 7 regression workflow and include both the aggregate JSON and reference-panel directory in a separately named upload artifact.
3. Run the full Phase 7 regression workflow after the test/workflow changes are in the branch. Only then may the new artifact be built, and its output must receive a distinct post-run tester audit.
4. Confirm all 10 layer/horizon panels exist, each contains all ten method columns, every row has exactly one block assignment, all hashes validate, and the saved panel independently recomputes the aggregate Brier/accuracy/balanced-accuracy values within the frozen 1e-9 tolerance.
5. Run #654 remains immutable; Phase 8 manifest still points to Run #654 until a separate amendment gate passes. Do not execute the Phase 8 4,800-cell grid.

No scientific conclusion, model promotion, option P&L or empirical authorization is granted by this code review.
