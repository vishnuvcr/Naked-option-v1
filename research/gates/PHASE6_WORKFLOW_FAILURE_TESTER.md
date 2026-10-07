# Phase 6 Workflow Failure — Independent Tester Review

Date: 2026-10-07
Tester branch: `phase-05-tester`
Failed hosted runs:
- Phase 6 workflow run `37668494609`
- Research Protocol Check run `37668496665`
Head SHA: `3bdf0a2999444e2eb416e445952698d100b1a947`

## Decision

**REQUEST CHANGES — EMPIRICAL EXECUTION REMAINS BLOCKED**

## Root cause

The reusable Phase 6 workflow used `hashFiles(...)` inside a **job-level** `if` expression to decide whether the empirical job should run.

GitHub Actions does not make the `hashFiles` special function available in `jobs.<job_id>.if`; that function is restricted to step-level contexts. This makes the workflow invalid at execution time. The hosted run failed before producing useful Phase 6 empirical output.

## Required correction

1. Replace the job-level `hashFiles` gate with a typed `workflow_call` boolean input such as `empirical_authorized`.
2. The existing Research Protocol detector must determine whether the tester approval file exists and pass that boolean to the reusable workflow.
3. Manual dispatch should expose the same boolean input, defaulting to false.
4. Remove direct push/pull_request triggering from the reusable workflow so there is a single automatic execution path through Research Protocol Check.
5. Re-run the workflow through the corrected automatic path.
6. Log this workflow failure and correction in the repository error/research logs.

## Disposition

Run `37668494609` is **non-evidence**. It produced no accepted scientific result and must not be counted as a Family E/I empirical run.

## Developer → Tester

Correct the reusable workflow gate as above and submit a fresh workflow configuration for re-review. Do not treat a successful regression-only run as empirical evidence.

## Tester → Developer

After the correction, independently inspect the caller/called workflow contract and the hosted run. Approve empirical execution only after the corrected gate is confirmed operational.
