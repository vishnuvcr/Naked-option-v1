# CI revalidation note — 2026-10-11

This commit exists to re-trigger the pull-request CI suites after the real-file audit workflow's schema-test coverage and tester-decision filename were updated.

- Current developer base before this note: `0cfdbdafd468723c473b806b11c9bada0933432c`.
- Real-file audit workflow was updated to read the new schema-fix decision path and include `scripts/test_offline_dataset_actual_schema.py` in its exact reviewed-file hashes and synthetic test suite.
- The real-file audit must be skipped on pull-request refs. No execution request is changed by this note.
- Required validation: offline synthetic preflight tests and the audit workflow's synthetic authorization tests must pass on the pull-request snapshot. The real-data audit must not run on a pull-request ref.
- Existing exact-hash tester decision remains stale; this PR does not authorize data access.

**Developer → Tester:** Verify both hosted PR CI suites pass and ensure the real-file job is skipped on this PR ref.
**Tester → Developer:** Return independent CI and workflow-gating findings before any execution request is made.
