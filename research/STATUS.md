# Research Status

| Phase | Status | Gate |
|---|---|---|
| Phase 0 Governance/bootstrap | PASSED | tester report archived |
| Phase 1 Literature/method registry | PASSED | final tester gate passed |
| Phase 2 Data engineering/PIT | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived |
| Phase 3 Labels/baselines | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived; B9/B10 blocked |
| Phase 4 Single-family methods | PASSED WITH SCOPED RESTRICTIONS | Family B and Family C tester gates archived |
| Phase 5 Statistical/ML | **PASSED WITH SCOPED RESTRICTIONS** | Family D run #23 immutable artifact passed independent tester gate; no model promoted; downstream economic/robustness/fresh-forward gates remain mandatory |
| Phase 6 Novel methods | **PASSED WITH SCOPED RESTRICTIONS** | Run #581 immutable artifact independently accepted; no method promoted |
| Phase 7 Ensemble/regime | **PASSED WITH SCOPED RESTRICTIONS** | Run #654 immutable artifact independently audited; no candidate promoted |
| Phase 8 Long-option execution | BLOCKED | Paytm Money/cost/execution gate |
| Phase 9 Robustness/statistics | BLOCKED | CPCV/DSR/PBO gate |
| Phase 10 Fresh-forward | BLOCKED | untouched-forward gate |
| Phase 11 Manuscript/final conclusion | BLOCKED | final tester sign-off |

Last updated: 2026-10-08

## Phase 5 current state

- Frozen protocol tester review passed at `research/gates/PHASE5_PROTOCOL_TESTER.md`.
- Independent tester issued REQUEST CHANGES for the early correction lineage; those submissions are archived under `research/gates/`.
- Protocol amendment for intraday refit cadence was independently passed at `research/gates/PHASE5_PROTOCOL_AMENDMENT_TESTER.md`.
- Intraday Family D now refits once per 20 trading sessions and predicts on the frozen hourly decision grid.
- The previous Family D runs that failed regression or empirical execution are rejected evidence and are not used for selection.
- Hosted Family D run #16 (`37606785909`) is preserved as non-accepted evidence because the frozen D07 wording did not exactly match the calibrated-meta-stack implementation. Tester gate `research/gates/PHASE5_D07_POST_AMENDMENT_TESTER.md` authorized fresh execution. Hosted run #19 (`37611880308`) has passed the mandatory regression gate and is currently executing the empirical D01-D15 suite. No metric is accepted yet.
- Phase 6 remains blocked until the independent tester reviews an immutable Family D artifact and issues a gate decision.

## Research continuity rule

A failed family or model is not a terminal conclusion. The full finite pre-registered universe, option economics, transaction-cost stress, multiple-testing controls and untouched-forward validation must be completed before final synthesis.


## Live verification — 2026-10-07
- Family D hosted run #19 (37611880308): **CANCELLED — NON-EVIDENCE**.
- Active step at cancellation: empirical D01-D15 execution.
- Regression suite: **PASSED**.
- Result schema validation: **SKIPPED**.
- Immutable artifact upload: **SKIPPED**.
- Family D empirical acceptance: **NONE**.
- Phase 6: **BLOCKED** pending independent tester artifact audit.

## Run #20 tester gate
- Run #20 (`37626101730`): workflow success; artifact `phase5-family-d-results` created.
- Independent tester found intraday D13-D15 had n=0 for every registered horizon because 20-observation session-local windows were built on the hourly decision matrix.
- Run #20 is non-evidence. Tester gate `research/gates/PHASE5_RUN20_INTRADAY_SEQUENCE_TESTER.md` requests changes.
- Developer correction maps causal 20-observation representations from the full 1-minute path to the frozen hourly decision rows.
- Tester approved the correction in `research/gates/PHASE5_RUN20_INTRADAY_SEQUENCE_APPROVAL_TESTER.md`.
- A fresh hosted Family D run is required; Phase 6 remains blocked pending artifact audit.


## 2026-10-07 — Family D run #23 final technical gate

- Fresh hosted run #23 (`37642007846`) on developer head `75ed6ddd90ac261364bf52570999d3c308fb37b5` completed successfully.
- Immutable artifact `phase5-family-d-results` / artifact ID `11499450561` was independently downloaded and SHA-256 verified as `27ca6cbc6e1653d40e2d896a81211c97a8d5e70543cf37ad9f402597eee306d8`.
- Independent tester gate `research/gates/PHASE5_FAMILY_D_RUN23_TESTER.md` = **PASS WITH SCOPED RESTRICTIONS**.
- All 150 Family D method/horizon cells executed; numerical reconciliation passed; D07 leakage/isolation checks passed; intraday D13-D15 coverage is restored and non-zero at every registered horizon.
- No Family D model is promoted. Multiple-testing, option economics, transaction costs, robustness and fresh-forward validation remain mandatory.
- Phase 6 remains pending only for independent tester review of the developer's proposed scope.


## 2026-10-07 — Phase 6 implementation gate
- Frozen Phase 6 method specification was approved by the tester.
- Developer implemented E01-E10/I01-I10, added causal/numerical regression tests, and created a gated workflow.
- The empirical workflow job is blocked unless the tester approval file is present on the developer branch.
- No Phase 6 empirical metric has been generated or accepted.


## 2026-10-07 — Phase 6 code gate passed
- Tester code gate `research/gates/PHASE6_CODE_APPROVAL_TESTER.md` archived on developer branch.
- E06 implementation, cutoff-invariance test, E07 exact composite amendment and schema gate passed independent review.
- No empirical result is accepted yet. The next hosted run must pass regression, then the gated empirical job can execute.


## 2026-10-07 — Phase 6 workflow correction checkpoint
- Tester-approved code gate remains scientifically valid, but the first hosted workflow attempt failed before execution because of an invalid GitHub Actions context expression.
- Failed run `37668494609` is non-evidence; no artifact exists.
- Developer replaced the empirical gate with `workflow_call.inputs.empirical_authorized` and caller-side tester-file detection.
- The corrected reusable workflow was also synced to `main` so its manual-dispatch interface is registered on the default branch.
- A fresh tester workflow gate is mandatory before another hosted attempt.


## 2026-10-07 — Phase 6 workflow correction gate passed
- Tester gate `research/gates/PHASE6_WORKFLOW_APPROVAL_TESTER.md` = **PASS — WORKFLOW CORRECTION GATE**.
- Corrected reusable workflow uses typed `workflow_call.inputs.empirical_authorized`; automatic caller derives authorization from archived tester approval.
- The default `main` branch also contains the corrected reusable workflow for manual-dispatch registration.
- A fresh Phase 6 hosted run is now authorized. No metric or artifact is accepted until post-run tester audit.

## 2026-10-08 — Phase 6 run 575 residual-defect checkpoint — tester correction approved
- Fresh hosted Research Protocol Check run `37678088131` / #575 started from developer commit `9b9b7914f82993505ec4f2f0c3aac0b3d6732521` and passed protocol detection, repository contract checks, source acquisition and the Phase 6 regression suite.
- Tester independently inspected the complete Phase 6 implementation before accepting any empirical metric and found a residual invalid `decision_times.iloc[...]` access in the later global-I03 cutoff block.
- Run #575 is therefore treated as **NON-EVIDENCE** regardless of its eventual workflow outcome; no Phase 6 metric/artifact from that run can be accepted.
- Tester gate `research/gates/PHASE6_RUN25_RESIDUAL_CUTOFF_TESTER.md` = **REQUEST CHANGES**.
- Tester approval `research/gates/PHASE6_RUN25_RESIDUAL_CUTOFF_APPROVAL_TESTER.md` = **PASS — correction approved for fresh empirical execution**.
- Corrected detached commit `e27b6358901dc60bc90bad295f46c9493ab63d1e` passed independent cutoff/code review; the developer ref can now advance only to the approved commit that archives this gate.
- Phase 6 remains **BLOCKED for scientific promotion** pending the fresh immutable 200-cell artifact and separate empirical tester gate.

## 2026-10-08 — Phase 6 run 578 regression failure
- Fresh hosted run #578 (`37680279189`) used the tester-approved cutoff correction, passed protocol/source acquisition, but failed the mandatory Phase 6 regression suite before empirical execution.
- Failure: `global_i03_cutoff` fixture expected 11:00 instead of the mathematically correct 11:15.
- Tester gate `research/gates/PHASE6_RUN26_REGRESSION_TESTER.md` = **REQUEST CHANGES**.
- Run #578 is **NON-EVIDENCE**; empirical execution was skipped and no artifact/metric was accepted.
- Phase 6 remains **BLOCKED** until the regression arithmetic is corrected and independently approved.

## 2026-10-08 — Phase 6 run 578 regression correction approved
- Tester gate `research/gates/PHASE6_RUN26_REGRESSION_APPROVAL_TESTER.md` = **PASS — correction approved for fresh empirical execution**.
- Detached correction `1a956f930b11850fb238ea3352565b36a7337395` changes only the expected timestamp in the global-I03 regression fixture from 11:00 to the mathematically correct 11:15.
- Run #578 remains **NON-EVIDENCE**; its empirical job was skipped and no artifact/metric was accepted.
- The developer branch may now advance to the archived approval commit and trigger a fresh gated Phase 6 execution.
- Phase 6 scientific promotion remains blocked until the fresh 200-cell artifact receives a separate independent empirical tester gate.
## 2026-10-08 — Phase 6 Run #581 empirical tester gate
- Fresh hosted run #581 (`37680832842`) completed successfully.
- Immutable artifact `phase6-novel-results`, ID `11513410209`, SHA-256 `2065f7d8025b87f67de1a9f04908ec2fc015a6bda98c5a8162ddad3b01961c24`.
- Complete registered grid: 200 cells = 140 EXECUTED + 60 BLOCKED_DATA; no missing or unexpected cells.
- Independent tester gate `research/gates/PHASE6_RUN581_TESTER.md` = **PASS WITH SCOPED RESTRICTIONS**.
- Technical validity is accepted; no Phase 6 method is promoted to a trading strategy.
- Phase 7 ensemble/regime research is now authorized, subject to a fresh tester gate. Phase 8 option execution, costs, robustness and fresh-forward validation remain mandatory.

## 2026-10-08 — Phase 7 specification gate
- Phase 7 developer specification `research/phase7/PHASE7_METHOD_SPEC.md` is frozen at commit `ae22d242631eb1cf2478ff818d285e458f5e33e6`.
- Tester gate `research/gates/PHASE7_SPEC_APPROVAL_TESTER.md` = **PASS — FROZEN SPECIFICATION**.
- P01-P10 definitions, blocked-predictor handling, exhaustive four-state regime partition, trend formula, trimmed mean, and 20-session expanding walk-forward schedule are now fixed.
- Phase 7 implementation is authorized; empirical execution remains blocked until a separate code gate and hosted regression gate pass.

## 2026-10-08 — Phase 7 regime amendment
- Tester found and resolved an internal P08 cutpoint inconsistency before implementation.
- Commit `5cdb61d38d83bfe16484f181380a60d612fbb9c2` freezes binary low/high volatility and low/high trend states using training-period medians.
- Tester gate `research/gates/PHASE7_SPEC_AMENDMENT_APPROVAL_TESTER.md` = **PASS**.
- Phase 7 implementation remains gated by the separate code review.

## 2026-10-08 — Phase 7 implementation authorization
- Tester-approved Phase 7 frozen specification is archived.
- Tester gate `research/gates/PHASE7_REGIME_CALIBRATION_APPROVAL_TESTER.md` = **PASS** for the causal regime calibration amendment.
- Developer implementation P01-P10 is prepared with the exact frozen rules, including P08/P09 = 0.5*base + 0.5*training regime rate.
- Separate Phase 7 code gate is now required before empirical authorization.

## 2026-10-08 — Phase 7 code correction cycle
- Tester requested changes to the first implementation because family-level data-snooping inference, regime diagnostics, chronological block diagnostics and numerical regression coverage were incomplete.
- Developer added the frozen 500-replication moving-block Brier-loss family bootstrap, four-state regime diagnostics/fallback counts, per-block performance records and deterministic synthetic tests.
- The family inference amendment was independently approved before implementation.
- A fresh Phase 7 code gate is required before empirical execution.

## 2026-10-08 — Phase 7 capture-order correction
- Tester review identified a latent prediction-to-method mapping defect in the first Phase 7 implementation.
- Because six Phase 6 methods are BLOCKED_DATA and therefore skip metric calls, the capture hook could not index against all 20 method names.
- Developer corrected this with explicit CAPTURE_ORDER and added regression coverage.
- No Phase 7 empirical execution occurred with the defective mapping.

## 2026-10-08 — Phase 7 code gate passed
- Tester gate `research/gates/PHASE7_CODE_APPROVAL_TESTER.md` = **PASS WITH SCOPED RESTRICTIONS**.
- Corrected implementation commit `3a883899d4ac32043e6771d677624f1c244ef86c` includes explicit Phase 6 capture ordering, P01-P10, family bootstrap inference, regime diagnostics, chronological block diagnostics and schema validation.
- Before empirical execution, the Phase 7 workflow must be registered on the default branch and the Research Protocol caller must contain the Phase 7 authorization gate.

## 2026-10-08 — Phase 7 workflow gate
- Tester gate `research/gates/PHASE7_WORKFLOW_APPROVAL_TESTER.md` = **PASS — WORKFLOW GATE**.
- Phase 7 reusable workflow and Research Protocol caller were independently reviewed.
- Default-branch registration is the remaining infrastructure action before the manual Run workflow control can be confirmed.
- Empirical execution remains blocked until regression passes after registration.

## 2026-10-08 — Phase 7 Run #600 workflow failure
- Hosted run #600 (`37716619573`) reached the Phase 7 regression job but failed before tests because `requirements.txt` does not exist.
- Run #600 is **NON-EVIDENCE**; empirical execution was skipped.
- Tester gate `research/gates/PHASE7_RUN600_WORKFLOW_FAILURE_TESTER.md` = **REQUEST CHANGES**.
- Developer corrected the workflow to use explicit dependencies and canonical Phase 6 data acquisition/cache steps; tester approval is required before another hosted run.

## 2026-10-08 — Phase 7 Run #600 workflow correction approved
- Tester correction gate PHASE7_RUN600_WORKFLOW_CORRECTION_APPROVAL_TESTER.md = PASS.
- Corrected workflow uses explicit dependencies and canonical cached data acquisition.
- Fresh hosted execution is authorized; Run #600 remains non-evidence.

## 2026-10-08 — Phase 7 Run #628 horizon correction approved
- Tester gate `research/gates/PHASE7_RUN628_HORIZON_APPROVAL_TESTER.md` = **PASS**.
- Production capture now binds each metrics call to the current horizon; deterministic multi-horizon regression coverage was added.
- Fresh hosted regression is authorized. Run #628 remains non-evidence.

## 2026-10-08 — Phase 7 Run #635 detector sequencing issue
- Run #635 (`37719802712`) is **NON-EVIDENCE** because the phase7 detector saw no qualifying Phase 7 file in the immediate push diff and skipped the gated workflow.
- Tester gate `research/gates/PHASE7_RUN635_DETECTOR_TESTER.md` = REQUEST CHANGES.
- Developer will use a harmless test-file trigger only; no scientific logic changes.

## 2026-10-08 — Phase 7 Run #637 repeated horizon-capture defect
- Run #637 (`37719955436`) passed regression but failed empirically at daily horizon 2 with `KeyError: ('2','E01')`.
- Cause: current developer branch still contained `H=horizons[0]`; the previously approved correction had not been preserved in the branch lineage.
- Run #637 is **NON-EVIDENCE**.
- The exact tester-approved horizon correction is being reapplied to the current branch. No scientific definitions change.

## 2026-10-08 — Phase 7 Run #637 horizon reapplication approved
- Tester gate `research/gates/PHASE7_RUN637_HORIZON_REAPPROVAL_TESTER.md` = **PASS**.
- Current developer lineage now contains the exact approved `H=H` horizon binding and direct multi-horizon capture regression.
- Fresh Phase 7 gated execution is authorized; Run #637 remains non-evidence.

## 2026-10-08 — Phase 7 Run #645 correction on current lineage
- The current branch lineage still contained `H=H`; the exact tester-requested closure fix has been rebuilt directly from the current branch head.
- No scientific definitions changed.

## 2026-10-08 — Phase 7 Run #645 closure fix approved
- Tester gate `research/gates/PHASE7_RUN645_CLOSURE_APPROVAL_TESTER.md` = **PASS**.
- Current-lineage `current_h=H` closure fix is approved; direct multi-horizon regression is present.
- Fresh gated regression is authorized; Run #645 remains non-evidence.

## 2026-10-08 — Phase 7 Run #650 tester gate
- Run #650 (`37723308187`), artifact `11532515562`, completed all 100 candidate cells.
- Independent tester gate `PHASE7_RUN650_EMPIRICAL_TESTER.md` = REQUEST CHANGES for bootstrap and regime-diagnostic implementation mismatches.
- Frozen correction amendment `PHASE7_RUN650_AMENDMENT_APPROVAL_TESTER.md` = PASS.
- Corrected implementation is in preparation; no candidate is promoted.


## 2026-10-08 — Phase 7 Run #654 independent empirical gate
- Fresh hosted Run #654 (`37763242007`) from developer head `4f1d695f291ed32996c07f01710afcecc6f2a540` completed protocol, regression, empirical execution, validation and artifact upload successfully.
- Immutable artifact `phase7-ensemble-results`, ID `11551679532`, SHA-256 `c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a`.
- Independent tester gate [PHASE7_RUN654_EMPIRICAL_TESTER.md](research/gates/PHASE7_RUN654_EMPIRICAL_TESTER.md) = **PASS WITH SCOPED RESTRICTIONS**.
- Complete frozen grid: 2 layers × 5 horizons × 10 candidates = 100 executed cells. Confusion counts, metric ranges, regime-diagnostic reconciliation, and artifact digest passed independent checks.
- Corrected moving-block bootstrap construction is present and verified; the Run #650 bootstrap mismatch is closed.
- No Phase 7 candidate is promoted. All ten family-level p-values are > 0.05; the strongest raw Brier improvement is daily +10 P08 (0.00315275) with family p=0.464.
- Scoped restrictions are carried into Phase 8: abstention chronological diagnostics are not trade-only, and the intraday regime observation scale (1-minute causal path sampled at hourly decision rows) must remain fixed and explicitly documented.
- Phase 7 technical evidence is now accepted; Phase 8 remains **BLOCKED** until its independent execution/cost gate is satisfied.
- This is a status update only; no method definitions were changed after observing Run #654 results.


## 2026-10-08 — Phase 7 Run #654 final independent gate closure
- Tester report `research/gates/PHASE7_RUN654_FINAL_TESTER_GATE.md` = **PASS WITH SCOPED RESTRICTIONS**.
- Independent audit reconciled all 100 candidate cells, confusion-matrix arithmetic, metric ranges, chronological/regime diagnostic counts, and family-bootstrap p-values.
- No Phase 7 family-level test is significant at alpha=0.05; therefore no P01-P10 candidate is promoted.
- Phase 7 is closed. Phase 8 is authorized to begin only as the pre-planned long-option execution/cost translation, with final holdout still sealed.


## 2026-10-09 — Phase 7 row-level reference artifact implementation checkpoint
- Tester proposal gate `research/gates/PHASE8_RUN822_FOLLOWUP_PROPOSAL_TESTER.md` on Phase 8 tester branch authorized artifact-output infrastructure only. Tester code review `research/gates/PHASE7_REFERENCE_ARTIFACT_CODE_TESTER.md` passed with scoped restrictions; report is archived on this developer branch.
- Developer added same-run Parquet panels containing P01-P10 forecasts, labels, future returns, timestamps and block IDs, plus hashes and runtime/source manifest. Existing metric calls and scientific method definitions are unchanged.
- Hosted Run #831 (`37912024282`) passed the existing Phase 7 regression suite but started before the new tester code gate and must be treated as NON-EVIDENCE for accepting the new reference artifact. Run #835 (`37912125332`), #837 (`37912165684`) and #838 (`37912206197`) exposed a defect in the new manifest regression fixture: its aggregate JSON temporary path was outside repository ROOT, causing `Path.relative_to(ROOT)` to raise `ValueError`.
- Corrected the fixture to create temporary files under `data/reports`; commit `14d20380632e365b2a0b6b63afe58f2775375950`. Run #846 (`37912507182`) skipped the Phase 7 gate because the changed paths did not include a science trigger; a fresh hosted regression gate is still required.
- Next: trigger one fresh Phase 7 hosted gate from the reviewed source path, verify both original and new reference-artifact regression suites, then independently audit the uploaded artifact. No new Phase 7 metrics or Phase 8 option execution is accepted yet.