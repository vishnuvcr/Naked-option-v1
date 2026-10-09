# Research Status

## Current checkpoint — 2026-10-10, available-data prediction extension

| Workstream | Current state | Evidence / next gate |
|---|---|---|
| Previously accepted Phase 7 Run #994 | Accepted technical artifact with scoped restrictions; no significant family-level predictive improvement | [Independent empirical audit](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_RUN_37957677656_EMPIRICAL_TESTER.md); all ten family p-values were non-significant |
| Available-data prediction extension | **Developer submission prepared; independent tester review pending** | [Method specification](phase7/AVAILABLE_DATA_PREDICTION_SPEC.md) and [developer handoff](gates/PHASE7_AVAILABLE_GLOBAL_DEVELOPER_SUBMISSION.md) |
| Extension regression | **PASS on run #5** | [Workflow run #5](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37984078118); 6 deterministic regression checks passed |
| Extension empirical execution | **NOT AUTHORIZED / SKIPPED** | Workflow correctly skipped predictions because no independent tester approval JSON had been mirrored |
| Options strategy research | **OUT OF SCOPE for this user request** | Do not enter Phase 8; no option trades or strategy P&L are being tested |
| Final untouched holdout | **UNOPENED** | Retain for a later independently approved forward-validation gate |

### Current extension scope

- Candidate data: SENSEX, Bank Nifty, S&P 500, Nasdaq Composite, Nikkei 225, Hang Seng, Cboe VIX, USD/INR, gold, crude oil, and India VIX where free historical acquisition passes validation.
- Candidate methods: G01/G02, G04/G05/G06, G08/G09/G11/G12/G13/G16, plus a deliberately limited G18 weekday/annual-cycle control.
- Horizons: 1, 2, 3, 5, and 10 NIFTY sessions.
- Method code: [acquisition](../scripts/acquire_global_history.py), [predictor](../scripts/run_phase7_available_global.py), [regression tests](../scripts/test_phase7_available_global.py), [gated workflow](../.github/workflows/phase-07-available-global.yml).
- Strict point-in-time rule remains unchanged: global source session date must be strictly earlier than the NIFTY session date. Source failures are isolated and recorded; no fabricated data or backfilled values.
- Regression runs #1 and #3 failed on test-fixture mistakes and are preserved/logged as non-evidence. Run #4 passed after fixture correction; run #5 passed after cache-freshness refinement. No empirical prediction result has yet been created for this extension.
- Next step: independent tester must audit source timing, leakage/purging, feature and result formulas, family bootstrap, code hashes, and workflow fail-closed behavior. Empirical execution is authorized only if the tester explicitly approves the exact protected code snapshot.

Developer → Tester: review all submitted files independently and issue a gate report; do not infer scientific validity from regression success alone.

Tester → Developer: report any mathematical, data-alignment, leakage, or workflow issue; provide verified protected SHA-256 values and explicit approval/rejection for one empirical prediction run.

---

| Phase | Status | Gate |
|---|---|---|
| Phase 0 Governance/bootstrap | PASSED | tester report archived |
| Phase 1 Literature/method registry | PASSED | final tester gate passed |
| Phase 2 Data engineering/PIT | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived |
| Phase 3 Labels/baselines | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived; B9/B10 blocked |
| Phase 4 Single-family methods | PASSED WITH SCOPED RESTRICTIONS | Family B and Family C tester gates archived |
| Phase 5 Statistical/ML | **PASSED WITH SCOPED RESTRICTIONS** | Family D run #23 immutable artifact passed independent tester gate; no model promoted; downstream economic/robustness/fresh-forward gates remain mandatory |
| Phase 6 Novel methods | **PASSED WITH SCOPED RESTRICTIONS** | Run #581 immutable artifact independently accepted; no method promoted |
| Phase 7 Ensemble/regime | **BLOCKED — CORRECTION WORKFLOW REQUEST CHANGES** | Four result defects have implementation/test corrections, but tester requires approval to bind to exact protected-code snapshot; see [correction review](gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md) |
| Phase 8 Long-option execution | BLOCKED | Paytm Money/cost/execution gate |
| Phase 9 Robustness/statistics | BLOCKED | CPCV/DSR/PBO gate |
| Phase 10 Fresh-forward | BLOCKED | untouched-forward gate |
| Phase 11 Manuscript/final conclusion | BLOCKED | final tester sign-off |

Last updated: 2026-10-09

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

## 2026-10-09 — Phase 7 reference artifact regression gate PASS
- Fresh hosted Run #852 (`37912587739`, head `ac6b30090e5146d527bb0af6dd9352a9b6a7fc93`) passed the original Phase 7 regression suite, the new reference-artifact regression, and the reference-artifact tester authorization gate.
- Tester report `research/gates/PHASE7_REFERENCE_ARTIFACT_REGRESSION_TESTER.md` = PASS for regression only. The Phase 7 empirical job is in progress; no new reference artifact or metrics are accepted until post-run audit.
- Run #831 remains non-evidence because it started before the new code gate. Runs #835/#837/#838 remain non-evidence because the new regression fixture failed in those runs. Run #852 is the first correctly gated run for the new output contract.
- Phase 8 manifest amendment and the 4,800-cell option grid remain blocked pending a complete, hash-verified artifact and independent audit.

## 2026-10-09 — Phase 7 immutable reference artifact checkpoint

- Reconciled GitHub Actions runs #852 (37912587739), #924 (37914896724), and #925 (37914905848). At this checkpoint all three still report `in_progress`; their empirical jobs are executing `scripts/run_phase7_ensemble.py`, and none has published an artifact.
- Run #852 remains unusually stale: its run metadata last updated at 09:39:25 UTC despite the empirical job still being marked active. Live log retrieval for #852 and #925 returned GitHub `BlobNotFound`; this is treated as an observability limitation, not evidence of success or failure.
- Regression and tester-authorization jobs passed in the later runs, but the real-data artifact audit has not occurred. No Phase 7 metrics are newly accepted, and Phase 8 remains blocked.
- The moving-block bootstrap allocation optimization has passed equivalence regression and received tester approval with scoped restrictions; this does not waive empirical completion or artifact provenance review.
- Operational correction: avoid launching additional competing empirical jobs while these runs are active. Reconcile the first completed run and audit its artifact before deciding whether remaining attempts are duplicates or require further action.


## 2026-10-09 — repeated live poll
- No state transition: runs #852, #924 and #925 are still marked `in_progress`, each active at the Phase 7 ensemble script; no artifacts are listed.
- Added the prolonged-execution/observability issue to `research/ERROR_LOG.md`. The root cause remains unknown; stale run metadata and missing live logs are not interpreted as scientific outcomes.
- Next gate remains unchanged: first completed artifact → independent source/provenance/statistical audit → tester decision. Phase 8 stays blocked.


## 2026-10-09 — Phase 7 Run #925 independent empirical audit — REQUEST CHANGES

- Runs #852, #924 and #925 completed and uploaded artifacts. The tester selected Run #925 (ID `37914905848`) on immutable source commit `682eadf2a9eb4de250bc3db27d02e57f88687fa1`.
- Independent tester workflow Run #943 (`37935031119`) reconciled artifact/source/code hashes, ten panel identities, timestamps, labels and future returns, then found 2,775 passing checks and 323 failing checks clustered into four implementation defects.
- Defects: P10's frozen [0.45, 0.55] abstention is absent; rows with missing volatility/trend enter low/low regime counts; P05/P06 block diagnostics do not use abstention masks; non-evaluable rows are incorrectly treated as zero in family-bootstrap differential arrays.
- Independent tester report: [PHASE7_RUN925_EMPIRICAL_TESTER.md](gates/PHASE7_RUN925_EMPIRICAL_TESTER.md) = **REQUEST CHANGES**.
- Run #925 is **NON-ACCEPTED EVIDENCE**. Older Run #654 remains an archived technical artifact but does not override this newer protocol-compliance finding.
- Phase 7/8 progression is blocked. Developer must correct these defects on `phase-07-developer`, add regression tests, and submit the exact correction commit for independent tester review before fresh empirical execution. The Phase 8 4,800-cell grid must not start until the fresh Phase 7 artifact passes.


## 2026-10-09 — Phase 7 correction submission reviewed; fresh-run gate remains blocked

- Developer correction submitted at `research/gates/PHASE7_RUN925_CORRECTION_CODE_SUBMISSION.md`.
- The targeted source fixes were independently verified and hosted Run #964 (`37936076338`) passed protocol/regression/reference-panel regression checks; empirical execution was skipped.
- Tester report `research/gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md` = **REQUEST CHANGES** because the correction-specific PASS is not bound to the exact reviewed snapshot. Any later source/workflow/protocol change could reuse stale approval text.
- Next developer action: bind approval to exact reviewed commit and hashes of protected source/test/validator/spec/workflow files; add positive and negative authorization tests for both manual and automatic paths.
- Runs `37935752265` and `37935794939` began empirical execution before the guard was corrected. They remain **NON-EVIDENCE**, regardless of artifact availability.
- No Phase 7 metric or strategy is promoted. Phase 8 remains blocked.


## 2026-10-09 — Phase 7 approval snapshot binding implemented

- Developer commit `b9fc7c9e7c77efb5149d35e31509251f701122ce` adds a fail-closed approval validator and positive/negative regression tests, and wires it into both the automatic caller and reusable/manual execution workflow.
- Protected source, tests, input/acquisition logic, method specifications and workflow files must match SHA-256 values in a tester-branch approval manifest. The reviewed commit must exist and be an ancestor; tester report and manifest must match byte-for-byte across branches and the report hash must match the manifest.
- Hosted [Run #981](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37938077088) passed protocol, Phase 7 regression, correction-approval validator regression and reference-artifact regression. Authorization and empirical jobs were skipped, as expected, because independent approval/manifest are not yet present.
- State: **AWAITING INDEPENDENT TESTER REVIEW**. No empirical run authorized, no metric accepted, Phase 8 blocked.


## 2026-10-09 — Phase 7 correction-approval test fixture repair

- Latest hosted check [#989](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37953177951) failed after protocol and the standard Phase 7 tests passed; the correction-approval regression asserted a bare filename against full-path registry entries.
- Developer corrected the assertion to the canonical full path. The production protected-file registry already covered that report; no scientific logic or model metrics changed.
- State: **ENGINEERING RE-RUN AND INDEPENDENT TESTER REVIEW REQUIRED**. Run #989 is non-evidence; no new Phase 7 artifact/metric is accepted. Phase 8 remains blocked until Phase 7 correction approval and a fresh post-run artifact audit pass.


## 2026-10-09 — Phase 7 snapshot approval retry

- Run #990: protocol, Phase 7 regression, correction-approval regression and reference-artifact regression passed on the corrected test snapshot.
- Tester issued a correction-specific code-gate approval with 25 protected-file hashes. The first mirrored attempt, Run #992, was correctly refused by the fail-closed validator due to a report-format/digest mismatch and one protected hash transcription error.
- Tester corrected the report and manifest on the isolated `phase-07-tester` branch. Developer mirrors the exact tester blob versions and records the Run #992 refusal.
- State: **AWAITING FRESH HOSTED SNAPSHOT VALIDATION**. Run #992 is non-evidence; no empirical metrics are accepted. Phase 8 remains blocked.


## 2026-10-09 — Phase 7 fresh empirical run authorized and started

- Snapshot-bound correction code gate: **PASS WITH SCOPED RESTRICTIONS** for one fresh empirical execution only.
- Hosted [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656) passed protocol, regression, approval-validator, reference-artifact regression and snapshot authorization. All 25 protected-file hashes and the exact tester report/manifest copies validated.
- The empirical job is currently **IN PROGRESS**. No output is accepted yet; its artifact must undergo separate independent post-run audit, including all ten method panels, P10 abstention, finite regime eligibility, P05/P06 masks, family inference, hashes and metric reconciliation.
- Run #925 remains rejected (including the re-audit in tester Run #993). Run #992 remains a logged authorization-refusal attempt. Phase 8 stays blocked until the fresh empirical gate passes.


## 2026-10-09 — Run #994 active empirical execution: runtime guardrail

- Run #994's snapshot authorization and regression gates passed; its empirical script started at 16:15:48 UTC and remains active. Validator/upload steps are pending.
- Live logs are unavailable while active (`BlobNotFound`); no failure is inferred.
- Run #925's corresponding script took 1h 53m 20s. Current run remains within the last observed runtime window.
- State: **EMPIRICAL SCRIPT ACTIVE — WAIT FOR TERMINAL STATE**. Do not start another empirical run while this one remains active. Phase 8 remains blocked.


 
## 2026-10-09 — Phase 8 costs: preliminary official-source review only

- Captured current official Paytm Money and NSE source links for the future option-execution cost model.
- Paytm public information is account-plan-sensitive: its F&O FAQ reports ₹10 per unique executed order, while its older plan notice documents ₹10/₹15 grandfathered and ₹20 newer-account plans. Use ₹10/₹15/₹20 sensitivity until the account-specific tariff/contract note is verified.
- NSE 2026 option transaction charges: ₹3,553/crore premium turnover per side from 1-Mar-2026; STT 0.15% on option sale premium and 0.15% on intrinsic value on exercise from 1-Apr-2026. Other statutory levies/GST, spread, slippage, latency and premium decay still require explicit handling.
- This is preparation only. Phase 8 has not advanced; its opening gate remains the fresh Phase 7 Run #994 artifact and independent empirical approval.


## 2026-10-09 — Additional free-source leads recorded (pre-gate only)

- Identified candidates on Hugging Face, Kaggle (reported via a community issue), Zenodo and GitHub that are not all covered by the current Phase 8 source-probe list. Candidate source URLs and limitations are recorded in the research log.
- The candidates are not accepted datasets: licensing/provenance, row coverage, expiry/strike omissions, OHLC-vs-bid/ask fields and official NSE cross-validation still require an audit.
- State is unchanged: Phase 7 Run #994 remains the active empirical target; Phase 8 is blocked and no P&L grid or source-composite amendment is authorized.


## 2026-10-09 — Free-source preview quality caveat

The current Hugging Face dataset viewer for rissin/nse-options-intraday shows legacy daily option rows dated 2005-06-10 with open/high/low/close, volume, open interest and settlement values all equal to zero for sample contracts. These may be placeholders for contracts with no eligible trade/quote, not valid executable observations. Do not silently forward-fill, impute or assign positive execution value to these rows. Validate zero/missing values by source and contract, retain explicit status/reason fields, and exclude invalid/non-positive premium rows from executable P&L while keeping them in coverage diagnostics. The dataset's license field is “other”, its provenance/redistribution terms need review, and it does not describe bid/ask data. Source: https://huggingface.co/datasets/rissin/nse-options-intraday

This confirms the source remains a candidate only. No source was imported and no Phase 8 gate was opened.



## 2026-10-09 — Hugging Face schema-range red flags found during pre-gate source search

A public preview of `artist-23/nifty-options-data` reports 33.96 million rows and shows suspicious extrema: `volume` minimum -4,288,892,671 and maximum 1.44 billion, while `iv` reaches 4,540. Those reported ranges require direct file inspection and source reconciliation; they are not evidence that every row is corrupt, but they make this candidate unsuitable for blind use. The preview includes normal-looking rows, which can coexist with bad/misparsed/extreme rows. Dataset viewer/source: https://huggingface.co/datasets/artist-23/nifty-options-data (viewer summary and schema).

The public dataset `codepyx23/india-index-options-1m` explicitly states it is a **duplicate** of `thetrademarkk/india-index-options-1m`, and both carry `CC-BY-NC-4.0`; do not count those as independent data sources or use them to claim independent cross-validation. Source: https://huggingface.co/datasets/codepyx23/india-index-options-1m/blob/main/README.md

The dataset `thetrademarkk/india-index-options-1m` describes partial option coverage, missing OI/settlement on intraday rows and no bid/ask stream. It is Q1 OHLC proxy data, not Q2 quote-executable evidence. Source: https://huggingface.co/datasets/thetrademarkk/india-index-options-1m

Required pre-acceptance checks for any of these candidates: check `high >= max(open, close, low)`, `low <= min(open, close, high)`, positive premium for executable rows, non-negative volume/OI when fields are present, IV unit/range sanity, timestamps/IST alignment, duplicated contract-minute keys, strike/expiry completeness, and overlap with official NSE contract rows. Keep raw input hash and row-level invalid reason codes. Never clamp, impute or drop bad rows silently. This is source QA preparation only: no dataset imported, composite built, or Phase 8 P&L executed.



## 2026-10-09 — Additional free minute-level spot source lead (not options)

The Hugging Face dataset `Hitjob-Done/indian-stock-market-minute-data` reports approximately 720 million rows/10.5 GB, an MIT license, and minute/day stock/index OHLCV data including symbols such as `NIFTY_50`. It is a candidate for independent underlying-index spot cross-checks, not a substitute for contract-level option records. Its card describes timestamps in UTC (convert to IST explicitly) and OI = 0 where not applicable; validate the actual NIFTY_50 shards, date coverage, timestamp conversion, license/provenance and overlap with NSE before use. Its displayed loading snippets point to dataset `xxparthparekhxx/indian-stock-market-minute-data`; the current page appears to be a source/reupload mirror, so investigate data identity/provenance and do not count mirrors as independent sources. Sources: https://huggingface.co/datasets/Hitjob-Done/indian-stock-market-minute-data and https://huggingface.co/datasets/xxparthparekhxx/indian-stock-market-minute-data.

This source can only help with spot-layer corroboration. It does not provide a contract quote, option bid/ask, or independently validated option premium path. No download or merge occurred; it remains a candidate for the free-source audit.



## 2026-10-09 — NSE official data-use / public-repository governance checkpoint

The main repository is publicly readable. The official [NSE Data Sharing & Usage Policy](https://www.nseindia.com/static/market-data/nse-data-policy) states that market data ownership remains with NSE/NSE Data and redistribution is not permitted except as agreed in the relevant agreement. The official [NSE copyright page](https://www.nseindia.com/static/nse-copyright) says website content generally may not be reproduced or stored on another website/electronic retrieval system, while its stated permission for download is scoped to personal, non-commercial or educational use and conditions. Specific instrument/data terms should be checked for the actual use case; this note is not legal advice.

**Implementation consequence for this public repo:** do not commit raw NSE bhavcopy archives, raw option rows, or public row-level datasets obtained from sources whose terms restrict redistribution unless documented permission/license explicitly allows it. Do not assume that publicly downloadable equals redistributable. Keep raw downloads transient or in access-controlled storage only where applicable terms and GitHub access controls permit; where cache reuse is appropriate, cache only under an access model compliant with the source license. Publicly store source IDs/URLs, data dates, schemas, per-file hashes, license status, reconciliation reports, aggregate research results and code. Check GitHub Actions cache/artifact visibility before relying on it for licensed raw market data. The repository’s goal of keeping reproducible evidence should not override data-licensing restrictions.

Free-source code candidates for later independent methodology review:
- https://github.com/SatvikBajpai/nifty-options-greeks — states it ships MIT-licensed code, not market data; locally downloads official NSE EOD bhavcopies, normalises legacy/UDiFF schemas, caches raw files, computes option forward/IV/Greeks, and has explicit liquidity/solver validation. Important limitation: end-of-day only, not historical bid/ask or intraday execution data; its spot source defaults to Yahoo. Suitable for a code/methodology cross-check after code-license and dependency review, not an independent data source.
- https://github.com/shayakbanerjee99/nifty-options-elt — ETL code for transforming official NSE daily F&O bhavcopy into queryable DuckDB option chains; a pipeline, not a separate price vendor.
- https://github.com/Aniruddha1980/Bhavcopy — open-source NSE report-fetching utility (README claims MIT); inspect current site compatibility/cache and provenance before use.
- https://github.com/NikhilSuthar/indian-market-data/blob/main/docs/datasets.md — catalog of NSE report types and file patterns; a useful free-source inventory, not a data license or hosted dataset.
- https://github.com/darshkale/nse-options-data-pipeline — option EOD enrichment/execution-modeling code; treat outputs as derived from the same NSE source family until lineage proves otherwise.

These do not provide historically executable bid/ask quotes. They must not be counted as independent price evidence when their output derives from the same official bhavcopy source. This is a governance/methodology preflight only: no files imported, no Phase 8 specification/workflow changed, and no option-P&L run authorized.



## 2026-10-09 16:53 UTC — Run #994 active-state recheck

- Same immutable workflow: [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656), source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- Empirical job `113912548214` still reports `in_progress` at `scripts/run_phase7_ensemble.py` (started 16:15:48 UTC); validation and artifact upload remain pending. No Run #994 artifacts are listed.
- GitHub run-level `updated_at` remains stale and active live logs are unavailable in earlier polls; that is an observability constraint, not a terminal failure.
- At this poll elapsed runtime is about 37 minutes, less than the previous completed Run #925's 1h 53m 20s model-step duration.
- No duplicate was dispatched, no data/result was accepted, and Phase 8 remains blocked.



## 2026-10-09 — Additional GitHub/Rust/EOD option research candidates (pre-gate)

Read-only repository search identified four further leads:
- **NSE-FNO-Data-bank** — https://github.com/SantoshSrinivas79/NSE-FNO-Data-bank claims a validated daily NSE F&O bhavcopy archive with 1,579 files, 13-Apr-2020 to 31-Aug-2026 (approximately 1.2 GB compressed), plus a downloader/validator. This may help cross-check calendar/availability counts and archive integrity, but it is EOD data only. Publicly committed raw NSE data is not proof of a redistribution licence; do not mirror its archive into this repository absent documented permission.
- **jugaad-rs** — https://github.com/Am1n1602/jugaad-rs provides a Rust NSE data library/CLI including derivative history, daily reports, option-chain snapshots and related market reports. It is code for retrieving NSE data, not an independent vendor. Useful to test source redundancy/API fallbacks after licence and schema review; intraday historical quote availability must be confirmed per method.
- **Nifty IV Surface & Event-Vol Tracker** — https://github.com/kfinance/nifty-iv-event-vol-tracker documents an overnight straddle research path using NSE F&O bhavcopy (claimed 2024-01-01 to 2026-09-18), including IV/event-vol studies and a claimed backtest. Treat as a hypothesis/code-review lead only; independently verify no synthetic data contamination, reconstruct results from allowed inputs, use a chronological out-of-sample design and reconcile all costs/slippage before any strategy inference. Do not import its reported return as evidence or add it post-hoc to the frozen current Phase 7 run.
- **NSE historical archive bank / API tools** — https://github.com/Aniruddha1980/Bhavcopy and https://github.com/Teja-Ram-Pooniya/nser-r-programming-option-data-nse include methods for historical F&O bhavcopy and selected NSE reports, but are overlapping retrieval wrappers over the same official data source, not independent price observations.

No candidate raw data was downloaded or copied. These leads are listed for the next permitted data/method gate only. Current Run #994 remains the active empirical target; Phase 8 remains blocked until its independent artifact gate.


## 2026-10-09 — Automatic independent audit orchestration added

- Added main-branch workflow [.github/workflows/phase7-approved-artifact-audit.yml](https://github.com/vishnuvcr/Naked-option-v1/blob/main/.github/workflows/phase7-approved-artifact-audit.yml).
- Automatic path: after a successful completed Research Protocol Check on phase-07-developer, preflight retrieves the exact run metadata and proceeds only when the run is successful and has one non-expired, non-empty phase7-ensemble-results artifact and one phase7-ensemble-reference artifact. Non-eligible automatic events are skipped.
- Manual path: the same workflow exposes workflow_dispatch with a required run_id; the same source branch/status/artifact checks apply, and invalid manual inputs fail closed.
- Independence: the audit uses the generic tester script from pinned tester commit 50334eb728a85ae8ca88f9ded5246b867c9cb56f, checks out the exact developer source SHA, downloads only artifacts for the requested run, and writes its JSON/Markdown report and phase status/log entries to phase-07-tester. The final workflow gate fails unless the report identity is exact and all checks pass.
- The legacy Run #925 audit on phase-07-tester is now manual-only and also requires an explicit boolean opt-in; normal tester-branch pushes no longer repeat the rejected historical audit.
- **Run #994 has not yet completed** at this checkpoint (its empirical step remains in progress and no artifacts are published). No audit was run on it yet, no metrics were accepted, and Phase 8 remains blocked.


## 2026-10-09 — Approved-audit workflow smoke test (preflight only)

- A completed developer protocol run [#1033](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37965583008) had no Phase 7 result artifacts because it was documentation-only.
- The newly installed automatic audit workflow [run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37965605363) inspected that exact run, found zero phase7-ensemble-results artifacts, and correctly skipped the independent audit. No tester code was executed and no metric was inferred.
- The main workflow was subsequently tightened to require the upstream workflow name to be exactly Research Protocol Check in addition to branch, completion, successful conclusion, source SHA and both non-empty artifact checks. Future auto events will recheck these constraints. Manual dispatch requires a run ID and rejects incomplete/missing-artifact runs.
- This is preflight evidence only, not empirical evidence. Run #994 remains in progress with no artifacts; Phase 8 remains blocked.


 
## 2026-10-09 — Automatic audit preflight identity check confirmed

- Automatic Phase 7 approved-audit workflow run #2 (Actions run 37966008847) processed completed developer protocol run 37965987043.
- It accepted the exact source as a successful Research Protocol Check on phase-07-developer, then correctly stopped before audit because there were 0 required aggregate result artifacts. The independent tester job was skipped.
- This confirms the name/branch/state guard plus fail-closed artifact preflight path. It is not a scientific or tester empirical decision.
- Run #994 remains active at the ensemble script with no result artifacts. Phase 8 remains blocked.


## 2026-10-09 — Exact implementation comparison: Run #925 vs Run #994

- Compared the frozen Phase 7 source at Run #925 commit `682eadf2a9eb4de250bc3db27d02e57f88687fa1` with Run #994 source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- The method specification file `research/phase7/PHASE7_METHOD_SPEC.md` is byte-identical at both commits (Git blob SHA `964b323f5ed86b12f743dea1c9b842aba166996a`). Thus the frozen protocol text was not amended between runs.
- The implementation and tests differ materially in fixes that target the prior independent audit defects:
  1. `P10` is included in the registered abstention mask `[0.45, 0.55]`, including both endpoints.
  2. P08/P09 regime-state counts now require finite volatility **and** trend; missing features are no longer silently classified as low/low.
  3. Family-bootstrap Brier differentials now leave rows non-evaluable when label, forecast or causal baseline is unavailable; only eligible abstentions receive zero differential, preventing missing data from diluting family means.
  4. Chronological-block diagnostics can receive the method-specific eligibility mask, so P05/P06/P10 diagnostics use the same registered row eligibility as the reported metrics.
  5. Regression tests now include explicit cases for these abstention, missing-regime-feature, family-missingness and candidate-mask conditions. Result validation permits P10's candidate-eligible block count to differ from the underlying regime diagnostic count, while P08/P09 retain their equality invariant.
- These are implementation corrections toward the frozen protocol, not changes to the protocol file. They do not guarantee that the new run passes; only the independent exact-run artifact audit can establish that. Run #994 remains active, has no artifacts at the latest poll, and Phase 8 remains blocked.


## 2026-10-09 — OPEN TESTER CHECK: P10 regime-diagnostic block-count invariant

- Frozen protocol `research/phase7/PHASE7_METHOD_SPEC.md` currently says the P08/P09/P10 regime-diagnostic block count must equal the candidate chronological-block count.
- The current `scripts/validate_phase7_results.py` explicitly enforces that equality only for P08/P09 because P10's registered abstention mask can remove every eligible metric observation from a chronological block.
- The production `scripts/run_phase7_ensemble.py` currently attaches the shared regime diagnostics to P08/P09/P10, while its P10 `chronological_blocks` uses the candidate-specific abstention mask. The independent auditor reconciles the shared regime diagnostics and P10 block metrics separately but does not explicitly enforce the frozen spec's stated count equality for P10.
- This is a **possible protocol/diagnostic-definition inconsistency**, not yet a finding that Run #994's eventual artifact fails. Do not silently amend the spec or disable the check. The tester must determine, from the literal frozen text and fresh artifact, whether (a) the implementation must retain matching P10 diagnostic blocks while preserving P10 abstention semantics, or (b) a formal pre-registered specification amendment is required. Any amendment needs its own tester approval and cannot be applied post hoc to justify results already examined.
- Run #994 is already executing immutable source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`; no code/spec change has been made to that run. The tester report must document this point and keep scientific promotion/Phase 8 blocked if unresolved.


## 2026-10-09 23:20 IST — Resume checkpoint

- The authorized empirical target Run #994 remains `in_progress` on immutable source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`; ensemble step started 2026-10-09 16:15:48 UTC and has not advanced to validation. The GitHub job log endpoint currently returns BlobNotFound and no artifacts are published. No metrics accepted.
- Developer correction commit `39e964d4ae99bb02b113fa4eabecd91c9af46c16` adds P10 candidate-specific regime-diagnostic filtering, P08/P09/P10 equality validation, and a fully abstained-block regression fixture. Developer workflow run #1068 passed its regression job; empirical/tester-gated jobs were skipped, so this is not independent approval or an empirical run.
- Correction has been submitted to the isolated tester branch in `research/gates/PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md` for independent review. No change was made to Run #994's source or protocol.
- Gate state: tester review pending; Run #994 artifact audit pending; Phase 8 blocked.


## 2026-10-10 — Exact-snapshot gate remains closed

Tester static review accepted the P10 diagnostic correction in commit 39e964d for a future empirical run only. However, the correction approval manifest was restored to the last verified snapshot because the attempted new report digest and protected hashes did not pass a second verification. Current developer HEAD is not authorized for a fresh empirical execution. Do not set empirical_authorized or proceed until the exact tester report/manifest are byte-identical across branches and all protected SHA-256 values are independently verified. Run #994 remains immutable and non-significant; no strategy selected.
