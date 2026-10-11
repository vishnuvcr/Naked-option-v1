# Phase 7 preflight synthetic CI submission

Date: 2026-10-11
Role: Developer submission; supporting document only, no model or market-data permissions requested.

## Snapshot being tested
- Scanner source commit: `6f11cc93f49e407c957ab843ea60311c41dba01f`
- Scanner test source commit: `f6284c458f408728a00f60673948d0fc35f5a417`
- Action-pin guard commit: `f63e44b2dc01620191ebc87634dc559112b1209e`
- Action-pin regression tests commit: `6854d5fdc7ff221fe86a86e01bb26b9bcb4c7301`
- Workflow pin/policy enforcement commit: `c97f40760804b06336a53748ec15607fb1d32d14`
- Supply-chain policy commit: `0aaa3b236c859ecca07bf6e0252092f6bc4d6b0a`

The pull-request workflow runs the tests without downloading or accessing the 4.75 GB dataset. It checks the action-pin allowlist, runs synthetic regression fixtures and asserts that the dataset CSV/CSV.GZ and `.env` are not staged. Permissions remain `contents: read` only; no project secrets are referenced.

## Requested tester scope
Review the final PR merge snapshot, confirm a successful Actions run tied to this exact code/workflow and check the duplicate-key fail-closed logic, gzip corruption/truncation, malformed row widths, cleanup, timestamp parsing and action pinning.

## Prohibitions
This submission does not request a real-data audit, data acquisition, model fitting/scoring, holdout access or strategy/P&L testing. These remain closed.

Developer → Tester: Return an exact-snapshot decision only after inspecting the Actions result and source/test/workflow blobs.
Tester → Developer: Reject the submission if the workflow run is absent/failing/stale; do not authorize any downstream work from a synthetic-only pass.
