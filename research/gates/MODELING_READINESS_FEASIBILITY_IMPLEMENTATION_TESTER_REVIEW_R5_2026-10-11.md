# Tester Review — MR-0 to MR-5 Feasibility Runner R5

**Date:** 2026-10-11  
**Verdict:** REQUEST_CHANGES — no empirical execution  
**Reviewed developer commit:** `4c2b3e54697474739da97f517476f4f87ed98b09`  
**Scope:** synthetic implementation and authorization/report safeguards only

## Exact reviewed blobs

- Runner: `fa163ad6bc4ca050169511ed669f43b414fabf97`
- Tests: `10d99e36a4a0ace47b809332788105d818e7eed8`
- Report schema: `211af15fe2b8579c48464b43171fbacf61e880b9`
- Synthetic workflow: `d7df79c6fd159708d8a58119bca8e0062d0546fe`

## Findings requiring correction

1. **Target validity is not proven.** The runner computes close-to-close labels from the last valid SPOT bar per session, but input validation does not require an explicit candle timestamp convention or evidence that this bar is linked to the official NIFTY close. The proposal says targets must be `NOT_ESTIMABLE` where close linkage is unproved. Add explicit required manifest fields and fail closed before computing any target labels.

2. **Label-endpoint purge is not verified.** Split validation checks date order and holdout exclusion flags, but does not check that every train label endpoint is before the validation boundary and every validation endpoint is before the holdout boundary. It also does not enforce the preregistered minimum of 252 eligible training origins and 250 common validation origins. Do not set `split_status=PASS` without the exact purge evidence and minimum-count checks.

3. **The `one_use` flag is declarative only.** The same authorization JSON can be replayed: no exact Actions run/attempt binding or durable consumed-marker is checked. Add a fail-closed replay control before reading the dataset. A re-run or attempt greater than one must require a fresh tester decision.

4. **Report keys are not sufficiently allowlisted.** The feature-family dictionary accepts names from the input manifest and emits them in the report. Restrict names to the fixed preregistered families; reject all others so arbitrary source-derived labels cannot leak into public artifacts.

5. **The holdout byte boundary is trusted but not independently checked.** The manifest claims record-boundary and order verification, but the runner should check that the prefix offset is in range and ends at a complete CSV record before parsing the prefix. Keep parsing bounded strictly to the prefix. Add a test with deliberately malformed bytes immediately after the boundary.

6. **Cleanup status is overstated in blocked reports.** `build_blocked_report` reports `cleanup_status=PASS` before any cleanup action has been proven. Use `NOT_RUN` for a metadata-only early block, and only use `PASS` when the relevant workflow has produced cleanup evidence.

7. **Execution CI is not accepted as evidence yet.** The workflow is correctly scoped as synthetic-only with a manual dispatch button and no secrets; however, I could not verify a hosted run ID/conclusion through the currently exposed Actions interface. Do not describe the tests as hosted-CI-passed until the run and job steps are inspected.

## What is acceptable in this snapshot

- No data fetching, model fitting, prediction scoring, trade/P&L execution or holdout-label access is invoked by the synthetic workflow.
- The runner requires explicit manifests and an authorization object before real mode; the report has a bounded set of aggregate fields.
- The synthetic boundary test is a good direction and should be retained after the missing safeguards above are added.
- No real dataset was executed in this review.

## Required developer resubmission

Correct findings 1–6 on `phase-07-developer`, add focused regressions for each, verify the hosted synthetic workflow, then submit the new commit and exact file hashes. Do not trigger real-data execution while this decision is current.

**Tester → Developer:** Correct all blockers and resubmit an immutable exact-hash snapshot for review.  
**Developer → Tester:** Keep the empirical-run gate closed until a fresh implementation decision explicitly passes; do not infer execution permission from synthetic CI.
