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


## Round 2 — correction approval snapshot binding

**Exact protected-code snapshot submitted for independent review:** `b9fc7c9e7c77efb5149d35e31509251f701122ce`  
**Hosted workflow evidence:** [Run #981 / ID 37938077088](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37938077088)  
**Disposition:** SUBMITTED FOR INDEPENDENT REVIEW; fresh empirical execution is still not authorized.

### Added fail-closed approval validator

- `scripts/validate_phase7_correction_approval.py` requires the exact correction-specific Markdown PASS plus a machine-readable `research/gates/PHASE7_RUN925_CORRECTION_APPROVAL.json`.
- The JSON approval binds a reviewed developer commit, tester-report SHA-256 and an exact hash map for every listed protected source, label/feature, candidate, test, protocol and workflow file.
- The validator fetches `phase-07-tester`, verifies the local Markdown/JSON copies are byte-identical to the independent tester branch versions, confirms the reviewed commit exists and is an ancestor of the current checkout, rejects missing/extra protected paths, and recomputes every protected-file hash. Any missing file, fetch problem, stale approval or mismatch fails closed.
- Both automatic caller and reusable/manual Phase 7 workflow run this validator before allowing empirical execution. The validator itself and its tests are in the protected path set.
- The Phase 7 regression workflow now runs `scripts/test_phase7_correction_approval.py` with positive and negative cases: matching snapshot, mutated protected file, modified tester copy, non-ancestor reviewed commit, and incomplete protected-file map.

### Hosted evidence

Run #981 passed:
- Repository protocol/literature validators.
- Phase 7 regression suite, including the corrections to P10 abstention, finite regime inputs, candidate-specific block diagnostics, and family-bootstrap missingness.
- Approval-validator positive/negative regression suite.
- Row-level reference-artifact regression suite.

The authorization and empirical jobs were **SKIPPED** because no independent tester PASS/approval manifest has been archived. This is the expected safe behavior, not a workflow failure.

### Request to tester

Independently review the exact commit `b9fc7c9e7c77efb5149d35e31509251f701122ce`, including the protected path list, validator, positive/negative tests, and both automatic/manual workflow paths. Verify the current gate and manifest are absent and empirical execution cannot start from this unapproved state.

If approved, create on `phase-07-tester`:
1. `research/gates/PHASE7_RUN925_CORRECTION_CODE_TESTER.md` with **PASS WITH SCOPED RESTRICTIONS — fresh empirical execution only**, and the exact reviewed developer commit line.
2. `research/gates/PHASE7_RUN925_CORRECTION_APPROVAL.json` with schema_version 1, status PASS, that reviewed commit SHA, the SHA-256 of the exact tester report bytes, and the SHA-256 values of every protected file listed in `scripts/validate_phase7_correction_approval.py`.

Archive both files byte-for-byte on `phase-07-developer`. Any mismatch must instead result in REQUEST CHANGES. Approval permits only one fresh empirical execution; it does not accept metrics or promote a strategy.

**Developer → Tester:** Review the exact snapshot and both authorization paths; do not approve based only on this description.

**Tester → Developer:** Independently verify the protected-path list and hash comparison, prove stale/modified approvals fail closed, then issue PASS for fresh execution only or REQUEST CHANGES. No Phase 8 until the fresh empirical artifact independently passes.
