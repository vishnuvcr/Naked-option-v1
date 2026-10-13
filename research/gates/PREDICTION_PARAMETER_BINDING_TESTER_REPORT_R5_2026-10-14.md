# Independent tester report — Phase 8P R4 remediation

Date: 2026-10-14
Tester branch: `phase-08-prediction-param-audit-tester-r5`
Reviewed developer snapshot: `aa10f90c972c08d1b4788ffa30777e3266da01b3`
Hosted workflow: [run 38463664826 — SUCCESS](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38463664826)
Artifact: [11848135257](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38463664826/artifacts/11848135257)
Artifact ZIP SHA-256: `3008482c0ca76834bc2c0437859bd5837656349a3320bed24cd5af9e020523e8`

## Decision

**NUMERICAL REMEDIATION: PASS. PARAMETER-SEMANTICS GATE: BLOCKED ON CONTRACT STATUS FINALIZATION. EMPIRICAL FITTING: NOT AUTHORIZED.**

The older R4 tester report remains valid for its earlier snapshot and is preserved. This report covers the later resubmission listed above.

## Verified evidence

The exact workflow completed successfully: 111 synthetic tests passed; 20 prediction modules compiled; 1,000 method rows and 40,000 configurations audited; 38,000 configurations bound to implemented families; 2,000 survival/event-time configurations explicitly blocked. Compatibility decisions remain 426 `ALLOW_IN_PRINCIPLE` and 574 `BLOCK`; empirical eligibility remains zero.

The audit verified preregistration V2 blob `1748edd2e0065db591bfd9598c2812d14f48327d` and contract blob `c0402b71e709156e6684e0d20fe0a5a87f0d2efc`. No market data was loaded, no fit was authorized, and the holdout was not accessed.

## T1 — Markov final posterior and log-likelihood consistency: PASS

Reviewed adapter blob `555b4d05023715a0254630565e55900b4dfa49ea` and test blob `73673d50aa3622b4be76b0095e9d7dec7d25b4b8`.

After each M-step, the adapter calculates likelihood with updated parameters. After training, it recomputes the forward recursion from the final initial distribution, transition matrix and regime-specific logistic parameters. The stored terminal log-likelihood and terminal state posterior therefore refer to the same final fit.

The test independently reconstructs the forward recursion rather than calling the adapter helper, then compares the terminal posterior and log-likelihood. I found no remaining prior-iterate mismatch. Two- and three-regime tests verify finite normalized outputs, and the alpha 2/5 sensitivity test shows the setting changes the transition matrix on a fixed synthetic fixture.

## T2 — Transition-prior formula and pin integrity: mathematically acceptable; status not final

The contract defines `transition_prior` as symmetric Dirichlet concentration alpha per transition-matrix cell, with allowed values 2 and 5. For each row, the estimator is (expected transition count + alpha) divided by the row's expected transition-count sum plus K times alpha. The implementation adds alpha to every expected count and normalizes each row. Tests verify the formula for K=2 and K=3 and both alpha values.

The audit checks the parent V1 blob, V2-to-contract pin, contract blob, parameter domains and no-empirical authorization. These components are consistent.

However, the controlled files still say approval is pending:
- Contract status: `DEVELOPER_PROPOSED_TESTER_REVIEW_REQUIRED_NO_EMPIRICAL_RUNS`
- Preregistration V2 status: `DEVELOPER_AMENDMENT_PROPOSED_TESTER_REVIEW_REQUIRED_NO_EMPIRICAL_RUNS`
- V2's contract entry says `PROPOSED_REQUIRES_INDEPENDENT_TESTER_APPROVAL`

I cannot mark the semantic contract formally approved while the controlled files still declare it proposed. This is a status/version alignment blocker, not a discovered formula defect.

### Required developer closeout

1. Update contract and V2 status fields to a clear tester-approved, code-contract-only state. Do not grant empirical fitting authorization.
2. Refresh V2's contract blob SHA and the workflow's expected V2 blob SHA after the JSON changes.
3. Re-run all tests and the full registry audit on the exact new commit.
4. Submit the new commit and artifact for final independent confirmation.

## Separate preregistration/data blockers

Even after this subgate closes, empirical fitting remains prohibited because V2 inherits unresolved `NOT_FROZEN_BLOCKED` items, including bootstrap block length and seed, flat-return tolerance, chronological fold dates, minimum train/validation/class-support rows, missingness thresholds and the frozen multiplicity family definition. These are separate gates and not covered by this code-only review.

## Final disposition

- T1 numerical consistency: **PASS**.
- T2 formula and hash verification: **PASS**.
- T2 formal metadata approval: **BLOCKED until the status/pins are updated and rerun**.
- Empirical fitting, market-data access, holdout access, option P&L, ranking and strategy promotion: **NOT AUTHORIZED**.

**Tester → Developer:** synchronize approved status values, refresh affected blob pins and rerun R4 on a new exact SHA.
**Developer → Tester:** submit the new workflow URL, artifact hash and exact commit for final approval; do not open empirical data.
