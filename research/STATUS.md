# Research Status

| Phase | Status | Gate |
|---|---|---|
| Phase 0 Governance/bootstrap | PASSED | tester report archived |
| Phase 1 Literature/method registry | PASSED | final tester gate passed |
| Phase 2 Data engineering/PIT | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived |
| Phase 3 Labels/baselines | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived; B9/B10 blocked |
| Phase 4 Single-family methods | PASSED WITH SCOPED RESTRICTIONS | Family B and Family C tester gates archived |
| Phase 5 Statistical/ML | **ACTIVE — RUN 1 REJECTED; CORRECTION SET UNDER HOSTED GATE** | independent tester REQUEST CHANGES; new gate required |
| Phase 6 Novel methods | BLOCKED | Phase 5 gate |
| Phase 7 Ensemble/regime | BLOCKED | freeze gate |
| Phase 8 Long-option execution | BLOCKED | Paytm Money/cost/execution gate |
| Phase 9 Robustness/statistics | BLOCKED | CPCV/DSR/PBO gate |
| Phase 10 Fresh-forward | BLOCKED | untouched-forward gate |
| Phase 11 Manuscript/final conclusion | BLOCKED | final tester sign-off |

Last updated: 2026-10-07

## Phase 5 current state

- Protocol: frozen and independently reviewed at `research/gates/PHASE5_PROTOCOL_TESTER.md`.
- Hosted run #1: `37594529634`, failed in the regression suite before empirical execution.
- Run #1 tester decision: **REQUEST CHANGES**, archived at `research/gates/PHASE5_RUN1_TESTER.md`.
- Rejected evidence: no Family D empirical metric from run #1 is accepted.
- Developer correction head: `f80b08d9a4d9f244e3e9f1c8563d6cebb5d3c94b`.
- Corrections include D07 training-only calibrated stacking, D13-D15 sequence architecture and session-boundary controls, training-only preprocessing tests, chronology/purge tests, and hourly-grid intraday fitting.
- Corrected hosted run is active. Phase 6 remains blocked until the independent tester reviews the new artifact.

## Research continuity rule

A failed family or model is not a terminal conclusion. The full finite pre-registered universe, option economics, transaction-cost stress, multiple-testing controls and untouched-forward validation must be completed before final synthesis.
