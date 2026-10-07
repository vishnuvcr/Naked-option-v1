# Phase 6 Residual Cutoff Correction — Tester Approval

**Status: PASS — correction approved for fresh empirical execution**

## Independent review

Tester independently reviewed proposed detached correction commit `e27b6358901dc60bc90bad295f46c9493ab63d1e` against the prior developer defect and the complete Phase 6 cutoff implementation.

- The residual `decision_times.iloc[rows[0]]` defect is removed from both cutoff paths; both now use valid `DatetimeIndex[...]` positional access.
- The remaining `.iloc` uses are applied to Series/DataFrame objects (`X`, source columns, and label series), not to `decision_times`.
- The production change is computational/API-correct and does not alter any frozen Phase 6 method definition, label, horizon, training boundary, seed, or cost rule.
- The regression suite now explicitly checks the later global-I03 cutoff path and asserts that `decision_times.iloc` is absent from the implementation.
- The detached commit's indentation was independently inspected after an earlier developer assembly defect; the corrected cutoff line is properly nested under `if intraday:`.
- Documentation/error/status updates are consistent with the correction lineage; the developer branch has not yet been advanced.

## Approval scope

This gate approves the **code correction for a fresh empirical execution only**. It does not approve any scientific metric, model, or strategy. The fresh hosted run must pass the mandatory regression suite, produce the complete immutable Phase 6 artifact, and receive a separate independent empirical-results gate.

## Non-evidence disposition

Run #575 (`37678088131`) remains non-evidence because the tester found the residual defect before artifact acceptance. No result from that run may be used for model selection or inference.

**Tester → Developer:** Archive this approval with the corrected code before advancing the developer ref, then run the fresh gated empirical suite. Do not promote any Phase 6 metric without the post-run artifact audit.