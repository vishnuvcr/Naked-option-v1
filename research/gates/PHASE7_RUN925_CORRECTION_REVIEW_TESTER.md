# Independent Tester Report — Review of Phase 7 Run #925 Corrections

**Decision: REQUEST CHANGES — CODE LOGIC REVIEWED; CORRECTION-SPECIFIC AUTHORIZATION IS NOT YET SAFE**

Date: 2026-10-09  
Developer submission: [PHASE7_RUN925_CORRECTION_CODE_SUBMISSION.md](PHASE7_RUN925_CORRECTION_CODE_SUBMISSION.md)  
Developer branch snapshot at submission: `510e2b88a8c07a6ca2176b110c6a5baf0852aef5` (code/test/validator changes include commits listed in the submission)  
Hosted regression evidence: [Run #964 / ID 37936076338](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37936076338)  
Unreviewed empirical runs: [37935752265](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935752265) and [37935794939](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935794939).

## Independent review disposition

### Correction logic — provisionally accepted for the scoped code review

Review of the current developer source confirms the reported four implementation changes are present:

1. P10 uses the registered inclusive [0.45, 0.55] abstention interval for headline metrics, coverage, chronological diagnostics and family-level differentials.
2. Regime training counts require finite labels, volatility and trend before assigning a row to one of the four states.
3. Chronological block diagnostics accept candidate-specific eligibility masks.
4. Family-Brier differential arrays remain NaN for unavailable observations, write zero only for eligible abstentions, and calculate benchmark-minus-candidate differential for eligible forecasts.

The targeted regression cases cover P10 endpoints/outside values, missing-versus-zero differentials, masked block diagnostics and missing regime features. Hosted Run #964 passed protocol/regression/reference-artifact-regression checks. This is code-test evidence only; it does not authorize or validate an empirical result.

### Material remaining finding — approval is not bound to the reviewed code snapshot

Both `.github/workflows/research-protocol.yml` and `.github/workflows/phase-07-ensemble.yml` currently authorize a future empirical run when `PHASE7_RUN925_CORRECTION_CODE_TESTER.md` exists and contains two expected text phrases. They do **not** verify that the code/workflow/protocol snapshot currently being run is the same snapshot approved by the tester.

After any correction-specific PASS is archived, a later commit can modify `scripts/run_phase7_ensemble.py`, its tests, the result validator, the frozen specification, or the workflow itself while the old PASS file remains. Because the current gate checks only the file/phrases, that stale approval could authorize the changed code. That violates the requirement for tester approval of the exact work that will run.

## Required correction

Bind approval to the exact reviewed developer snapshot. Implement a fail-closed mechanism on **both** manual and automatic paths that does one of the following:

- Preferably records the exact reviewed commit SHA plus SHA-256 hashes of protected source/test/validator/spec/workflow files in a machine-readable tester approval manifest and re-verifies every hash before empirical execution; or
- Pins the exact approved source commit and rejects any changed protected paths between that reviewed snapshot and the run commit.

Protected files must include at minimum `scripts/run_phase7_ensemble.py`, `scripts/test_phase7_ensemble.py`, `scripts/validate_phase7_results.py`, `scripts/run_phase6_novel.py`, `scripts/run_phase3_daily_baselines.py`, `scripts/run_phase3_intraday_baselines.py`, `research/phase6/*`, `research/phase7/*`, `.github/workflows/phase-07-ensemble.yml`, and `.github/workflows/research-protocol.yml`. Include any other execution/provenance file that can change Phase 7 results.

Add tests proving a matching approved snapshot authorizes fresh execution, while a changed protected file causes authorization to be false. Verify both `workflow_dispatch` and the automatic caller fail closed. The old approvals must not satisfy this correction-specific binding.

## Disposition of affected hosted attempts

Runs `37935752265` and `37935794939` started empirical execution before the strict correction-specific snapshot binding was in place. They are **NON-EVIDENCE**, irrespective of conclusion or artifact availability. Do not use, rank, publish or promote their metrics.

Phase 8 remains blocked. No trading strategy is promoted by this report.

**Tester → Developer:** Add exact source snapshot/hash binding and fail-closed regression tests on `phase-07-developer`; submit the exact commit for another independent tester review.

**Developer → Tester:** Review both authorization paths and negative tests independently. Do not archive a fresh-execution approval until a stale correction PASS cannot authorize modified code.
