# Phase 8 H=1 ULP Gate — Independent Tester Review R3 (2026-10-12)

## Decision
**REQUEST CHANGES — blocked by missing frozen source cache.**

## Evidence
- Developer code/test HEAD `da33a40f4f52e51807ca0fb7882e7920021c47a1` passed validator regression [#38164567189](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38164567189) and protocol check [#38164567374](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38164567374).
- The full reconstruction on commit `d012713dae811dba0ad919f2a6a0edb5821f0ff8` [run #38165151602](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38165151602) restored the immutable Run #994 artifact but failed closed because the cached daily source file was absent. No validation manifest was generated.
- Guarded retry on commit `a3c3e4c04f094f92aff61b5615f64ff74e0eafb5` [run #38165231846](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38165231846) passed protocol/regression and skipped the source-audit job as intended, but reconstruction failed on the same missing source cache.
- Prior successful reconstruction on older commit `21dd39b6819dcc1ecae67307633fe4621e168c58` observed 64 daily H=1 mismatches, maximum absolute difference `3.469446951953614e-18`, maximum distance 1 ULP, zero out-of-policy values. This does not close the exact-HEAD gate.

## Required next action
Developer must locate an already archived copy of the frozen daily/intraday source inputs and verify it against the pinned hashes. If no archived copy exists, submit a separate request for a one-time, strictly pinned historical-source restoration. No acquisition should occur before that review. Keep the immutable Run #994 artifact and `1e-9` tolerance unchanged.

## Restrictions
No option P&L, holdout access, strategy promotion, or new unpinned data/source acquisition. The R1 one-use preflight authorization remains consumed/disabled. The unintended source-audit run in #38165151602 is logged and its outputs are not accepted for this gate; the workflow now gates source acquisition on empirical authorization.

## Developer → Tester
Review only source provenance/recovery options; do not add unrelated requirements.

## Tester → Developer
Keep the gate open until exact-HEAD reconstruction produces persisted ULP diagnostics from hash-verified frozen source inputs.
