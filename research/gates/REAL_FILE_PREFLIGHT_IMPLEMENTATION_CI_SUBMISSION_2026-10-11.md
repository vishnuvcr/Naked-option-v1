# Real-file preflight implementation CI submission

Date: 2026-10-11
Developer branch implementation snapshot is submitted for synthetic-only CI and exact tester review. This is not a request to execute the real-data job.

## Scope
- Pinned, source-lineage-checked real-file audit workflow with a second authorization gate that reads the tester-branch decision and an execution-request file.
- The real-data job must skip without an exact matching tester decision; source artifacts are not downloaded unless the authorization check returns true.
- Synthetic test coverage for the scanner, action-pin policy and exact-hash authorization helper.
- No model fitting, holdout, new data requests or strategy/P&L.

## Reviewed files in this submission
- `.github/workflows/phase-07-real-file-preflight-audit.yml`
- `.github/workflows/phase-07-offline-preflight-tests.yml`
- `scripts/offline_dataset_preflight.py`
- `scripts/test_offline_dataset_preflight.py`
- `scripts/check_workflow_action_pinning.py`
- `scripts/test_workflow_action_pinning.py`
- `scripts/validate_real_file_preflight_authorization.py`
- `scripts/test_validate_real_file_preflight_authorization.py`
- `scripts/decrypt_nifty_1m_composite.py`
- `requirements-composite.txt`
- `research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json`

## Required outcome
Synthetic CI must pass. The tester must inspect the exact merged-head file hashes, workflow source lineage, secret scope, action pins, cleanup and authorization behavior. A synthetic pass is not permission to decrypt or scan the actual dataset.

Developer → Tester: Review the exact code/workflow snapshot and issue a scoped decision. The real-file workflow must remain unapproved until all exact hashes are recorded.
Tester → Developer: Reject any stale hash, unpinned action, plaintext artifact path or authorization bypass.
