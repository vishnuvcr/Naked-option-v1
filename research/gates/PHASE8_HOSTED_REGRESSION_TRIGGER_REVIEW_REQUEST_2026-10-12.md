# Phase 8 Hosted Regression Trigger — Independent Tester Review Request
Date: 2026-10-12
Status: REQUESTED — developer change committed; independent review and run evidence still pending.

## Exact change under review
- Developer branch: `phase-08-prediction-developer`
- Commit: `5de4a2c1626b5f2633c4e0565e84592297ad4b44`
- Workflow: `.github/workflows/phase-08-long-option.yml`
- Current workflow blob: `b59ac6882be9e6f94a2ec39914d2c21ab2bdab6f`
- Change: adds a narrow `push` trigger restricted to the developer branch and Phase 8 workflow/runner/regression/frozen-manifest/approval paths. Existing `workflow_call` and `workflow_dispatch` inputs remain in place; manual dispatch defaults `empirical_authorized` to false.
- The current connector's commit-run lookup returned an empty list because it only exposes PR-triggered runs. This is **not** evidence that the workflow did not run or that it passed. Hosted run status is unverified.

## Required independent checks
1. Validate the YAML trigger syntax and verify the existing reusable/manual triggers are intact.
2. Prove push events cannot accidentally set `inputs.empirical_authorized == true`; all source acquisition and empirical jobs must remain disabled on an ordinary push.
3. Check that the trigger cannot bypass the frozen manifest, data-quality gate, one-use authorization, or independent tester approval.
4. Inspect the first hosted run through the GitHub Actions UI/API, record run ID and per-job outcomes, and preserve artifacts/logs.
5. If the run fails, report the exact failing job/step and classify the failure; do not infer an infrastructure cause without evidence.
6. Keep empirical P&L and strategy promotion unauthorized.

## Decision boundary
This request does not itself approve the workflow, prove that a run occurred, or authorize any real-data diagnostic or empirical option P&L. Tester role remains independent and must not edit developer code.

**Tester → Developer:** issue a written PASS/REQUEST_CHANGES decision tied to the exact workflow blob and provide hosted run evidence if accessible.
**Developer → Tester:** preserve the current fail-closed empirical gates; do not treat an empty connector response as a successful run.
