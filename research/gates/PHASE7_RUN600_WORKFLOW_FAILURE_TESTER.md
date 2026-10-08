# Phase 7 Run #600 Workflow Failure — Tester Review

**Status: REQUEST CHANGES**

Fresh hosted Research Protocol Check run #600 (`37716619573`) reached the Phase 7 reusable workflow, but the regression job failed before the test suite because `.github/workflows/phase-07-ensemble.yml` attempted `pip install -r requirements.txt`.

The repository has no root `requirements.txt`; the established Phase 6 workflow installs the required packages explicitly.

## Impact

- Regression suite did not execute.
- Empirical job was skipped.
- No Phase 7 scientific metric or artifact exists.
- Run #600 is **NON-EVIDENCE**.
- This is an infrastructure/workflow defect, not a scientific failure.

## Required correction

1. Replace the nonexistent requirements-file installation with the established explicit dependency installation: numpy, pandas, scikit-learn, pyarrow.
2. Add the Phase 7 cached-data restoration and canonical daily/intraday/global acquisition steps because the Phase 7 implementation imports and reuses the Phase 6 prediction engine.
3. Preserve the existing empirical authorization gate and artifact schema validation.
4. Re-run the hosted regression gate before any empirical execution.

**Tester → Developer:** Correct the workflow, log the failure, and resubmit the workflow correction for independent tester approval.