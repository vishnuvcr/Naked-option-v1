# Tester Review Cadence — Effective 2026-10-13

## Governing instruction

Independent tester review is deferred until the planned research results have been acquired, frozen, and indexed. Do **not** request a tester review for every intermediate step, phase, code commit, unit-test correction, registry edit, or workflow edit.

This policy changes the review cadence only. It does not waive scientific rigor, developer-side validation, data-provenance requirements, chronological leakage controls, statistical multiplicity controls, cost accounting, or final independent scrutiny.

## Roles

**Developer during execution**
- Work through the finite research plan and complete the result-acquisition steps without waiting for routine tester reviews.
- Run automated unit/regression/integrity tests, validate source manifests and hashes, preserve failed runs and null findings, and repair reproducible implementation defects.
- Keep a versioned activity ledger, error log, immutable run manifests, and updated README/status pages.
- Do not claim a result before a workflow/artifact actually exists. Do not relax frozen rules or access a protected holdout to improve a result.
- Keep a candidate out of promotion if internal validation identifies unresolved leakage, invalid labels, malformed results, or non-reproducible statistics. This is developer quality control, not tester review.

**Independent tester after result acquisition**
- Start only when a machine-readable `PREDICTION_RESULTS_ACQUIRED_REVIEW_REQUEST.json` states `results_acquired: true`, pins the exact developer commit and hashes, and inventories a complete result-bundle manifest.
- Review the acquired outputs and the corresponding implementation/protocol together: mathematical formulas, signs, source/label/data consistency, chronological leakage, target maturity/purge/embargo, all null/failed runs, multiplicity, robustness, cost/slippage assumptions, reproducibility, and promotion claims.
- Submit one consolidated hash-pinned PASS or REQUEST CHANGES report for the acquired bundle.
- If changes are required, the developer fixes and reruns the affected work and submits a complete corrected bundle for re-review. Do not interleave tester reviews with every correction commit.

## When an early stop/review may occur

Only a serious blocker that makes continuing unsafe or impossible—such as unrecoverable data corruption, an actual credential/security exposure, an unresolvable authorization constraint, or a protocol defect that would invalidate all subsequent outputs—may interrupt the planned result-acquisition run for a narrowly scoped intervention. Ordinary code/test findings should be fixed by the developer and logged, not sent to the tester as an intermediate review request.

## CI versus tester review

Developer-side automated tests, deterministic hash checks, schema validation, workflow regression tests, and data-quality assertions may run at every relevant commit. They are execution controls, not an independent tester verdict.

The tester workflow must not trigger merely because tester code, a review-request draft, or an intermediate artifact changes. It triggers on the formal acquired-results request (and retains a manual dispatch button for that same post-acquisition event). The workflow must fail closed if the request does not declare results acquired or if any pinned artifact hash differs.

## Current Phase 8P application

- The previous R2 1,000-method / 8,000-configuration artifact remains a synthetic/design pilot, not empirical prediction evidence.
- The developer must construct and validate the complete frozen ten-horizon registry (intraday 5/15/30/60/120 minutes; positional +1/+2/+3/+5/+10 exchange sessions), complete the planned empirical result-acquisition workload with developer-side quality checks, and preserve all results before initiating independent review.
- R2 pilot outputs may not rank methods. No empirical result may be described as independently accepted until the post-acquisition tester review is complete.
- The historical tester R3 REQUEST CHANGES report remains in the audit trail as evidence of issues discovered and subsequently addressed. It is not an instruction to run new tester reviews after each step under this updated cadence.

## Handoff format

**Developer → Tester (only after results acquired):** provide the exact source commit, source blob pins, frozen preregistration/protocol, result-bundle manifest and hashes, complete per-run outcomes (including failures/nulls), and the proposed conclusions. Request one consolidated independent review.

**Tester → Developer (after reviewing the acquired bundle):** return a hash-pinned decision with reproducible evidence for every defect. Identify which result artifacts must be corrected/rerun; do not ask for unrelated step-by-step submissions.

## Change control

This cadence policy takes effect on 2026-10-13. A change to the research scope still requires a dated, explicit plan amendment before results are inspected. Review cadence changes are recorded in this file and linked from the research plan, README, status, error log, and conversation log.
