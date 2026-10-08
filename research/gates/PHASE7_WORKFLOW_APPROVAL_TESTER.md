# Phase 7 Workflow Gate — Tester Approval

**Status: PASS — WORKFLOW GATE**

Tester independently reviewed the corrected Phase 7 workflow package at developer commit `91d23e44ba2054d286dd538f4e102508d7b3d8cb`.

## Checks passed

- `.github/workflows/phase-07-ensemble.yml` is a reusable workflow with a typed boolean `workflow_call` authorization input.
- It also defines `workflow_dispatch` with a manual boolean authorization control.
- Regression runs before the empirical job.
- Empirical execution is hard-gated on explicit authorization.
- The empirical job performs the Phase 7 run, validates the artifact schema, then uploads the immutable result artifact.
- `.github/workflows/research-protocol.yml` detects only `phase-07-developer` for automatic Phase 7 execution.
- Automatic empirical authorization is derived from the archived tester code-approval gate.
- The caller uses the corrected reusable workflow and passes the typed boolean.
- No invalid job-level `hashFiles()` expression is used.
- The default-branch registration requirement is understood: the Phase 7 workflow file must be present on the default branch for the GitHub manual Run workflow control to be exposed.

## Scope

This gate approves the workflow architecture for Phase 7. It does not approve empirical results.

**Tester → Developer:** copy the approved Phase 7 workflow and the corresponding Phase 7 caller-gating logic to the default branch, then trigger a regression-only workflow check. Do not authorize empirical execution until the default-branch registration is confirmed and the regression gate passes.