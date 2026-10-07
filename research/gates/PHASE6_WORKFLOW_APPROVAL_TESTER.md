# Phase 6 Workflow Correction — Independent Tester Approval

Date: 2026-10-07
Tester branch: `phase-05-tester`
Prior failure: `research/gates/PHASE6_WORKFLOW_FAILURE_TESTER.md`
Correction reviewed: developer commits `93cdc1011908769343c224f3890502f1abf6bd9b` and `c1793af7a877e847fda72b357660c01cd67d105f`

## Decision

**APPROVED FOR FRESH HOSTED REGRESSION AND EMPIRICAL EXECUTION**

## Independent checks

### 1. Reusable workflow contract
- `workflow_call.inputs.empirical_authorized` is typed boolean with default false.
- `workflow_dispatch.inputs.empirical_authorized` is also typed boolean with default false.
- The empirical job now uses the typed input rather than `hashFiles()` in a job-level conditional.
- The invalid context expression from run `37668494609` is removed.

### 2. Automatic authorization path
- `Research Protocol Check` now exposes an `empirical_authorized` job output.
- The detector sets that output true only when the archived tester approval file `research/gates/PHASE6_CODE_APPROVAL_TESTER.md` is present on the developer branch.
- The caller passes the boolean explicitly to the reusable workflow.
- The automatic trigger remains restricted to Phase 6-relevant changes on `phase-05-developer`.

### 3. Manual dispatch
- The reusable workflow retains a manual-dispatch button.
- Manual empirical execution defaults to false, preventing accidental empirical execution without explicitly passing authorization.
- The corrected workflow is synced to the default `main` branch so the manual-dispatch interface is registered there.

### 4. Scientific boundary
- The correction changes only workflow control; no E/I method definition, data source, label, horizon, seed or evaluation rule was changed.
- Failed run `37668494609` remains non-evidence.
- No empirical metric is accepted by this gate.

## Required post-run gate

After the fresh hosted run starts, the tester must independently verify:
- regression completion;
- whether the empirical job actually received authorization;
- artifact creation and immutable lineage;
- schema and all E/I cells;
- denominators/metrics and BLOCKED_DATA reasons.

## Disposition

**PASS — WORKFLOW CORRECTION GATE**

The developer may archive this gate to `phase-05-developer` and trigger the corrected automatic path. Do not interpret workflow success as scientific acceptance.

## Tester → Developer

Archive this approval, make one Phase 6-relevant developer-branch change to trigger the automatic Research Protocol path, and monitor the resulting hosted workflow.

## Developer → Tester

After the fresh artifact is produced, independently audit the artifact and either PASS WITH SCOPED RESTRICTIONS or REQUEST CHANGES before any Phase 7 transition.
