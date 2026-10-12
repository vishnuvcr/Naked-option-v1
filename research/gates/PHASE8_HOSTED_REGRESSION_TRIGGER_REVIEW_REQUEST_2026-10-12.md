# Phase 8 Hosted Regression Trigger — Independent Tester Review Request
Date: 2026-10-12
Status: REQUESTED — no workflow trigger changed yet

## Developer proposal
Add a narrow `push` trigger to `.github/workflows/phase-08-long-option.yml`, restricted to branch `phase-08-prediction-developer` and the Phase 8 workflow, frozen forecast manifest, execution runner, runner regression, execution-engine regression and existing approval files. The current `workflow_call` and `workflow_dispatch` inputs remain unchanged; `empirical_authorized` continues to default to false for manual dispatch and the empirical jobs remain behind the existing explicit authorization, source and reconstruction gates.

## Intended outcome
Allow a reviewed, ordinary developer-branch commit to start the already-existing protocol/regression/reconstruction jobs automatically, rather than depending on a manual workflow-dispatch action unavailable in the current connector. The trigger must not authorize empirical P&L or promote strategies.

## Tester checklist
1. Verify YAML trigger syntax and that workflow_call/workflow_dispatch remain intact.
2. Verify missing `inputs.empirical_authorized` on push cannot make `sources`, `empirical-authorization` or `empirical` run. Require explicit `inputs.empirical_authorized == true` plus the existing authorization gates.
3. Verify push path filters are scoped and do not create an infinite workflow loop from report-only commits.
4. Verify permissions remain least privilege and no secrets are exposed in logs/artifacts.
5. Confirm regression, immutable Run #994 integrity, and forecast reconstruction can run without empirical option execution authorization.
6. Issue PASS or REQUEST CHANGES with evidence before developer adds the trigger.

## Boundaries
No code/data/strategy definitions are changed by this request. This review is for hosted non-empirical verification only. The 4,800-cell P&L grid remains blocked until the separate point-in-time option panel and one-use authorization gates pass.

### Developer → Tester
Please independently review the proposal against the exact current workflow on `phase-08-prediction-developer`; do not copy implementation code to the tester branch. Return a written gate decision.
