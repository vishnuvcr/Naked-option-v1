# Standing research execution permission — 2026-10-14

## User direction

The user explicitly stated: **“No need for Authorization.”**

## Operational interpretation

This is standing permission to continue the already-defined prediction-only research and to run registered development/outer-validation experiments automatically once the relevant technical and scientific gates pass. Do not pause to request another user authorization for each method, run, phase, or workflow.

This permission removes the need for repeated *manual/user authorization*. It does **not** waive the frozen preregistration or any hard execution controls:
- exact dataset, calendar, feature and label pins must verify;
- compatibility blocks remain blocked;
- an implementation must exist and pass developer-side tests before its configuration can run;
- fold-level sample-support blocks remain scoped to their exact label/fold cells;
- training-label maturity, chronological splits, purge, embargo, train-only transforms, deterministic accounting, and complete failure/null rows remain mandatory;
- no holdout access, result-driven protocol changes, or strategy research in this prediction-only phase;
- independent tester review remains deferred until the complete result bundle is acquired, frozen and hash-pinned.

The compatibility registry's legacy value `NOT_IMPLEMENTED_OR_TESTER_APPROVED` must not be interpreted as a requirement for an intermediate tester review. Developer-side implementation/tests and the formal post-results tester review are separate controls. A method remains blocked until its actual implementation and tests are evidenced, regardless of this standing permission.

## Execution rule

Proceed autonomously through the finite registered plan. When a gate fails, log the exact failure and fix the implementation or preserve the scoped block; do not request routine permission. Do not describe a method as empirically eligible until a machine-readable developer gate demonstrates that its implementation, data cell, registry mapping, and execution contract all pass.

## Scope boundary

This is a dated governance clarification of execution permission and review cadence. It does not alter the frozen target labels, horizons, feature representation, folds, sample thresholds, metrics, multiplicity correction, configuration universe, or holdout policy.

**Developer → Tester:** wait for the consolidated post-results bundle.  
**Tester → Developer:** review the complete frozen bundle only after formal handoff.
