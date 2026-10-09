# Developer Submission — Phase 7 Run #925 Corrections

**State: SUBMITTED FOR INDEPENDENT TESTER REVIEW — NOT APPROVED FOR EMPIRICAL EXECUTION**

Date: 2026-10-09  
Prior tester decision: [PHASE7_RUN925_EMPIRICAL_TESTER.md](PHASE7_RUN925_EMPIRICAL_TESTER.md) — REQUEST CHANGES  
Current developer branch: `phase-07-developer`  
Current submission snapshot (documentation-only head): `510e2b88a8c07a6ca2176b110c6a5baf0852aef5`

## Changes submitted for review

1. `scripts/run_phase7_ensemble.py`
   - Registered P10's frozen [0.45, 0.55] abstention interval alongside P05/P06.
   - Excluded observations lacking finite volatility or trend from all four regime-state training counts; left the training-only pooled-label fallback unchanged.
   - Added candidate-specific eligibility masks to chronological block diagnostics.
   - Added `candidate_brier_differential()`: abstentions receive zero differential only when y, p and baseline are evaluable; unavailable rows remain NaN.

2. `scripts/test_phase7_ensemble.py`
   - Added inclusive interval-endpoint tests and immediate-outside controls for P10.
   - Added differential tests for trade, eligible abstention and non-evaluable rows.
   - Added a candidate-masked block-diagnostic test.
   - Added a crafted regime fixture in which 20 missing-feature rows must not count toward the low/low state.

3. `scripts/validate_phase7_results.py`
   - Retained regime diagnostic schema checks but no longer requires P10's abstention-filtered chronological-block count to equal the unmasked regime diagnostic count. P08/P09 retain the equality invariant.

4. Workflow authorization safety
   - `.github/workflows/research-protocol.yml` no longer treats the older Phase 7 code approval as current empirical authorization. It requires a correction-specific independent tester PASS.
   - `.github/workflows/phase-07-ensemble.yml` applies the same correction-specific gate on the reusable/manual execution path.

## Change commits

- Production correction: `df1a835a8a3bcf53cfc2fad873c29de2f03b21a7`
- Targeted regression tests: `18be4a9ebcd3f04cf1e8588d25522974ac4fb680`
- Reusable-workflow correction gate: `9dff0e8e8e1a8ba10c2fa48ac010bb923339a801`
- Caller correction gate: `74e2c30cd9321f732f28acb196809b39228707c8`
- Result-validator adjustment: `871b276fadba110028ec7b5d97c6abb46841f1f9`

## Hosted test evidence

- [Run #964 / ID 37936076338](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37936076338): protocol checks and Phase 7 regression/reference-artifact regression passed. The empirical job was skipped because no correction-specific tester PASS is present.
- [Run #962 / ID 37935917149](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935917149): reusable workflow fail-closed check did not find the correction-specific approval; empirical job was skipped. Its overall workflow failure is an expected unapproved-gate stop, not a scientific result.
- Two older runs started empirical execution before the new authorization guard was committed: [37935752265](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935752265) and [37935794939](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935794939). They are explicitly **NON-EVIDENCE** regardless of eventual job outcome or artifact availability; no outputs from them may be interpreted or selected. This incident is documented in `research/ERROR_LOG.md`.

## Protocol preservation

No changes were made to `research/phase7/PHASE7_METHOD_SPEC.md), candidate universe, horizons, seed 42, block length, 500 family-bootstrap replications, walk-forward schedule, minimum training size, regime cutoff rule or frozen thresholds. The change is intended to implement—not amend—the frozen specification.

## Request to tester

Please independently inspect the complete source diff, the new regression cases, the result validator, and both workflow authorization paths. Confirm the four earlier defects are corrected, no new formula/sign/indexing defect exists, and the specification is unchanged.

**Requested decision:** `PASS WITH SCOPED RESTRICTIONS` for a *fresh empirical execution only*, or `REQUEST CHANGES`. A code-gate pass must not promote an empirical metric. After approval is archived on the developer branch, one fresh empirical run can execute and must receive the separate post-run artifact gate.

**Developer → Tester:** Review the exact proposed commits and hosted regression run; do not approve based solely on this summary.

**Tester → Developer:** Verify mathematics, data alignment, masks, family bootstrap missingness, validator semantics and both workflow gates independently. Do not authorize empirical execution until the correction-specific report passes.
