# Research Status

| Phase | Status | Gate |
|---|---|---|
| Phase 0 Governance/bootstrap | PASSED | tester report archived |
| Phase 1 Literature/method registry | PASSED | final tester gate passed |
| Phase 2 Data engineering/PIT | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived |
| Phase 3 Labels/baselines | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived; B9/B10 blocked |
| Phase 4 Single-family methods | PASSED WITH SCOPED RESTRICTIONS | Family B and Family C tester gates archived |
| Phase 5 Statistical/ML | **PASSED WITH SCOPED RESTRICTIONS** | Family D run #23 immutable artifact passed independent tester gate; no model promoted; downstream economic/robustness/fresh-forward gates remain mandatory |
| Phase 6 Novel methods | **WORKFLOW GATE PASSED — FRESH HOSTED RUN AUTHORIZED** | Tester independently approved the typed workflow-call authorization correction; no empirical artifact accepted yet |
| Phase 7 Ensemble/regime | **BLOCKED — CORRECTION AUTHORIZATION REQUEST CHANGES** | Four result defects have a developer correction, but the correction-specific approval is not bound to the exact reviewed source snapshot; see [correction review](gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md) |
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


## 2026-10-09 — Phase 7 Run #925 independent empirical gate

- Runs #852, #924 and #925 all completed with artifacts; #925 (run ID `37914905848`) was selected for the frozen-source audit.
- Independent audit executed on tester workflow Run #943 (`37935031119`) and downloaded the immutable reference/result artifacts for source commit `682eadf2a9eb4de250bc3db27d02e57f88687fa1`.
- Artifact, code and source hashes, ten panel identities, source-derived timestamps/labels/future returns and row-level source alignment reconciled.
- Corrected audit disposition: **REQUEST CHANGES** (2,775 checks passed; 323 checks failed). Key causes: omitted P10 abstention, non-finite volatility/trend observations entering the low/low state, P05/P06 per-block diagnostics ignoring abstention masks, and family-bootstrap invalid rows being treated as zero differentials.
- Tester report: [PHASE7_RUN925_EMPIRICAL_TESTER.md](gates/PHASE7_RUN925_EMPIRICAL_TESTER.md).
- Run #925 is non-accepted evidence. No Phase 7 metric/model/strategy is promoted. Phase 8 option-execution research remains blocked until a corrected fresh empirical run receives an independent pass.


## 2026-10-09 — Review of Phase 7 correction submission

- Developer source fixes for P10 abstention, finite regime-state eligibility, candidate-masked block diagnostics and family-bootstrap missingness were confirmed by independent code inspection; targeted regression cases and hosted Run #964 passed.
- Tester found the correction-specific workflow gate only checks approval text/file presence. It does not bind approval to the exact source/workflow/protocol revision, so later changes could reuse a stale PASS.
- Gate report [PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md](gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md) = **REQUEST CHANGES — authorization binding**.
- Runs `37935752265` and `37935794939` started empirical execution before the binding guard existed and are **NON-EVIDENCE**.
- Phase 7 remains blocked; Phase 8 must not start. Developer must bind the tester approval to an exact reviewed code snapshot and add positive/negative tests before the tester can approve fresh execution.


## 2026-10-09 — Generic approved-run tester audit entry point

- Preserved the legacy Run #925 audit as a historical, manually dispatched re-audit only; branch pushes no longer trigger it.
- Added `scripts/audit_phase7_artifact.py`, an independently held generic entry point with the same frozen numerical and data-integrity checks, parameterized by expected run ID and exact source commit.
- A separate main-branch orchestrator will invoke this pinned tester script automatically after a successful `Research Protocol Check` on `phase-07-developer` completes, but only if that exact run has both `phase7-ensemble-results` and `phase7-ensemble-reference` artifacts. It will also expose a manual run-ID input.
- The orchestrator checks out this tester code at a fixed commit before executing it, downloads only the source run's artifacts, publishes the full JSON/Markdown tester report onto this tester branch, and fails the final gate unless the report says PASS. It does not use model selection logic or modify developer forecast code.
- This commit adds the generic audit entry point and records the separation rule; it is not an empirical result. The legacy pinned Run #925 audit remains available via manual `workflow_dispatch` only.


## 2026-10-09 — Legacy Run #925 audit now requires explicit manual opt-in

The tester workflow's manual button now exposes boolean input `run_legacy_run925_audit`, default false. The legacy pinned Run #925 audit runs only when the user deliberately selects that opt-in. All normal tester branch pushes and ordinary manual protocol-validation runs skip the historical audit. Approved fresh-run audits are handled separately by the main-branch workflow, which pins the generic tester script from commit 50334eb728a85ae8ca88f9ded5246b867c9cb56f and publishes each exact-run report to this isolated tester branch.

This workflow-only safety change does not alter the frozen metric calculations or any empirical data.


## 2026-10-09 — P10 regime diagnostic block-count contract review

Static tester report: `research/gates/PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md` = **REQUEST CHANGES FOR SCIENTIFIC PROMOTION**. The frozen spec requires P08/P09/P10 regime-diagnostic block counts to equal candidate chronological-block counts, but the current validator only enforces P08/P09 while P10 abstention can empty blocks. Run #994 remains immutable and may still finish for exact-artifact audit; no metric or strategy may be promoted while this protocol/code mismatch remains unresolved. A future implementation or formally approved pre-registered spec amendment must be independently reviewed before another run.


## Run #37957677656 independent empirical artifact audit

- Source run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656
- Developer commit: b50be8cfa1ebe008a800e65a53f9c0fb2581aecb
- Decision: **PASS WITH SCOPED RESTRICTIONS — artifact integrity, source alignment, metric reconciliation and family inference**
- Checks: 3098 passed / 0 failed
- Report: research/gates/PHASE7_RUN_37957677656_EMPIRICAL_TESTER.md and JSON companion.
- Scientific promotion: **NOT GRANTED by the technical audit alone**. Phase 8 stays blocked unless the empirical gate passes and all remaining data/cost gates pass.

## 2026-10-10 — Independent tester disposition

- Run #994 exact artifact audit: PASS WITH SCOPED RESTRICTIONS, 3,098 passed / 0 failed.
- All ten family-level tests non-significant (p=.262–1.000); no strategy promoted.
- Static review of developer commit 39e964d: PASS for future runs only; P10 diagnostic records are filtered to eligible chronological blocks, inclusive abstention endpoints are tested, and validator equality restored. Does not alter immutable Run #994.
- A fresh authorized run with corrected source is required before any Phase 8 decision; options point-in-time data and net-of-cost execution tests remain unpassed.
- Audit workflow fallback-report shell syntax defect after report generation was logged and fixed on main; verify the fixed success/fallback paths in a subsequent workflow run.


## 2026-10-10 — P10 correction review versus execution authorization

Static review of developer commit 39e964d passed for a future run only. The correction-specific approval report/manifest on both branches were restored to the last verified snapshot after the attempted updated SHA values failed an independent digest check. Therefore the current corrected developer HEAD is **not authorized for empirical execution** yet. Tester → Developer: regenerate/verify the report digest and all 25 protected-file hashes, synchronize identical report/manifest bytes to both branches, and require hosted validator PASS before running. Run #994 remains unchanged; no strategy promoted.


## 2026-10-10 — Corrected Phase 7 snapshot reviewed (static only)

- New report: [PHASE7_AVAILABLE_GLOBAL_RESUBMISSION_TESTER.md](gates/PHASE7_AVAILABLE_GLOBAL_RESUBMISSION_TESTER.md).
- **Disposition: PASS WITH SCOPED RESTRICTIONS for static source review only; empirical execution remains NOT AUTHORIZED.**
- Static review found the requested formula and output-audit corrections present in the current file blobs: raw-return G13/fixed constituent set, five-horizon Bonferroni, candidate-paired baseline metrics, row-level forecast output with SHA provenance, and result/panel reconstruction checks.
- The regression test file contains 11 named checks, but the reviewer did not execute them or see a hosted run result. Status/workflow-run queries returned empty collections; this is not evidence of either success or failure.
- Developer must keep the authorization manifest absent and obtain an observable, green hosted regression result before requesting the empirical gate.


## 2026-10-10 — Phase 7 available-data acquisition review

- Hosted regression evidence is now observable: [Run #37](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37990522933) succeeded, with 11 predictor regressions and 11 result-validator regressions passing.
- The authorization job correctly failed closed because no independent approval manifest was mirrored; empirical prediction job was skipped.
- Fresh tester review of the current workflow/acquisition snapshot found that NIFTY acquisition always downloads and overwrites the restored cache rather than validating and reusing a valid cached CSV/manifest.
- **Disposition:** REQUEST CHANGES for empirical execution. No prediction result or metric exists for this extension. Developer must add a cache-reuse implementation and no-network regression tests, protect those tests, and resubmit.


## 2026-10-10 — Phase 7 acquisition follow-up gate

- [Run #40](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37992378927) passed 4 acquisition/cache checks, 11 predictor checks and 11 result-validator checks. Authorization remained correctly closed; no empirical job ran.
- Independent tester review found additional point-in-time risks: UTC calendar-date conversion instead of exchange-local session dates, a UTC chart cutoff inconsistent with the IST completion rule, same-day cache rows accepted before close, and official overlap manifest values not checked against CSV rows.
- **Gate status: REQUEST CHANGES; empirical execution NOT AUTHORIZED.** Fix date/time alignment and overlap consistency, add targeted tests, then submit a fresh exact snapshot.


## 2026-10-10 — Current Phase 7 tester gate status

- Run #43: [37992695619](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37992695619), SUCCESS; 8/8 acquisition/cache tests, 11/11 predictor tests, 11/11 validator tests.
- Latest exact-snapshot report: PASS WITH SCOPED RESTRICTIONS, one Phase 7 empirical prediction batch only.
- Developer branch has the identical tester report mirrored, but the hash-bound execution approval manifest has not been created because its write was blocked by platform safety checks.
- Empirical execution has not started; there are no new prediction results to audit. Phase 8 remains blocked.


## 2026-10-10 — Independent tester completed Run #44 artifact audit

- Run #44 [38018506915](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915) completed successfully in all jobs. Artifact ID 11657636547, SHA-256 `63b607db7227cdd91f3a62a0a8ca5f0b010d12c3bad1848ebbd9f59961804891`.
- Independent structural and metric audit passed: 91,988 rows, zero duplicate row keys, zero invalid probabilities, zero missing candidate labels/returns/probabilities, zero target-sign mismatches, and candidate metrics plus all five family p-values reproduced.
- Family p-values at 1/2/3/5/10 sessions: 0.9840/0.8882/0.6786/0.7745/0.9800; all Bonferroni-adjusted p-values 1.0.
- **Decision:** data/result integrity passes; no candidate promoted. Phase 8 and strategy development remain blocked.
- Full report: `research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md`.


## 2026-10-10 — Extension 2 specification gate: REQUEST CHANGES

- Independent review of `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md` returned REQUEST CHANGES before any data acquisition.
- Blocking points: legacy F&O bhavcopy/UDiFF transition coverage, undefined FII/DII normalization denominator, ambiguous F04/F05 arithmetic, non-canonical sector index identity, and incomplete deterministic treatment of candidate abstentions in the global bootstrap.
- No source data were downloaded, no feature table was created, and no model was fit.
- Full review: `research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SPEC_TESTER.md`.


## 2026-10-10 — Gate A sampler code review: REQUEST CHANGES

- Tester reviewed sampler blob `a35178de4c32a9f86ae1b710a14fd2a8eb7ec072` and offline tests blob `eac0e4289ebb6321c08677cc2301c8fc60aa0e13`.
- Blocking issue: archive trade-date validation checks only the first row in legacy and UDiFF files. A mixed-date archive could pass.
- Required: validate every row's trade date, record distinct date count, and add mixed-date negative fixtures for both formats.
- No workflow ran and no source sample was downloaded.
