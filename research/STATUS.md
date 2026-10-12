# Research Status

## Phase 8P R2 review state — deferred until acquired results (2026-10-13)

- The historical R3 REQUEST CHANGES decision remains preserved; **no new independent review is due at this intermediate step** under the latest user instruction.
- Tester review is deferred until the complete planned prediction-results bundle is acquired, frozen and hashed, and the formal acquired-results request is submitted.
- The developer's T2 bootstrap and T3 pilot-scope corrections are recorded for inclusion in that eventual consolidated review. The tester-side audit harness and result-hash validation are ready, but no review verdict is being issued now.
- See [cadence deferral memo](research/gates/PREDICTION_REGISTRY_REVIEW_CADENCE_DEFERRAL_2026-10-13.json) and [cadence policy](governance/TESTER_REVIEW_CADENCE_POLICY_2026-10-13.md).
- No new market-data access, fit, holdout access, option P&L, or method ranking is claimed by this status update.


## Phase 8P prediction registry gate — 2026-10-13

- **Tester decision: REQUEST CHANGES.** See [R3 independent review](research/gates/PREDICTION_REGISTRY_V2_R2_INDEPENDENT_TESTER_REVIEW_R3_2026-10-13.md) and [machine decision](research/gates/PREDICTION_REGISTRY_V2_R2_INDEPENDENT_TESTER_DECISION_R3_2026-10-13.json).
- T2: degenerate moving-block bootstrap inference is not identifiable when all bootstrap estimates coincide (including a fold with exactly one admissible block); the utility must fail closed instead of emitting the minimum p-value and zero-width interval.
- T3: only two target labels are present; the full frozen set of intraday and positional horizons needs to be included or the registry scope must be formally narrowed before fitting.
- The tester-owned audit script/workflow has been committed to check all method/configuration/compatibility shards and semantic linkage. The hosted audit result has not yet been observed; the full independent reconstruction is not signed off.
- No market data, estimator, outer-fold selection or holdout was accessed.


| Phase | Status | Gate |
|---|---|---|
| Phase 0 Governance/bootstrap | PASSED | tester report archived |
| Phase 1 Literature/method registry | PASSED | final tester gate passed |
| Phase 2 Data engineering/PIT | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived |
| Phase 3 Labels/baselines | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived; B9/B10 blocked |
| Phase 4 Single-family methods | PASSED WITH SCOPED RESTRICTIONS | Family B and Family C tester gates archived |
| Phase 5 Statistical/ML | **PASSED WITH SCOPED RESTRICTIONS** | Family D run #23 immutable artifact passed independent tester gate; no model promoted; downstream economic/robustness/fresh-forward gates remain mandatory |
| Phase 6 Novel methods | **WORKFLOW GATE PASSED — FRESH HOSTED RUN AUTHORIZED** | Tester independently approved the typed workflow-call authorization correction; no empirical artifact accepted yet |
| Phase 7 Ensemble/regime | BLOCKED | freeze gate |
| Phase 8 Long-option execution | **ARTIFACT AUDIT PASSED — TRADING GATES BLOCKED** | Tester-owned decision PASS_WITH_SCOPED_RESTRICTIONS; see PHASE8_GREEK_ENRICHMENT_ARTIFACT_REVIEW_R1_2026-10-12.md |
| Phase 9 Robustness/statistics | BLOCKED | CPCV/DSR/PBO gate |
| Phase 10 Fresh-forward | BLOCKED | untouched-forward gate |
| Phase 11 Manuscript/final conclusion | BLOCKED | final tester sign-off |

Last updated: 2026-10-13 (tester review deferred until results acquisition)

## Phase 8P prediction sub-study — 2026-10-12 current state

- Duplicate-diagnostic **code-only gate: PASS** for developer commit `aae250d8a34989ebe0bd901e1d6b7d9aa0ec5a5f`; independent tester workflow [#38204532045](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204532045) passed 19/19 checks.
- Immutable tester report: [PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_R1_2026-10-12.md](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_R1_2026-10-12.md); machine decision: [PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_DECISION_R1_2026-10-12.json](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_DECISION_R1_2026-10-12.json).
- Tester workflow defects (stale R2 request path; then redundant same-path copy) were corrected on this tester branch and logged. The failed runs remain non-evidence.
- **Real-data diagnostic remains BLOCKED / NOT AUTHORIZED.** No encrypted artifact was accessed or decrypted by the code gate; no duplicate report, feature fit, holdout read, option P&L or strategy promotion occurred.
- Next step: developer submits a separate one-use diagnostic authorization request that pins the exact approved code/test snapshot, this tester decision, encrypted artifact ID/digest, output schema and no-replay policy. Independent review of that authorization is required before any artifact access. The data gate must then be independently reviewed again.

**Tester → Developer:** preserve the code-only PASS and submit the separate diagnostic authorization request; do not run the encrypted artifact scan before that gate passes.
**Developer → Tester:** review only the exact one-use authorization request when submitted; after an authorized run, independently inspect its aggregate report and report hash.

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


## 2026-10-11 — Phase 8 Run #994 saved forecast gate passed

- Developer commit `3fe13c49ed29e77b001485abe50b2d41dbb6c160`, hosted run [38157819076](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38157819076) completed successfully.
- Tester reviewed exact output artifact `11709261335` (SHA-256 `249afea08ced49517a44744053afa382ce05165f53d0d23c5aac860a0c54214c`) and independently recomputed every panel digest.
- Decision `research/gates/PHASE8_RUN994_SAVED_FORECAST_R2_TESTER_DECISION.json`: PASS WITH SCOPED RESTRICTIONS. Ten cells, 50,555 rows, all cells reproduced at absolute tolerance 1e-9.
- No empirical P&L or 4,800-cell grid executed; no strategy is promoted. Before any option P&L, developer must version the Phase 8 spec to remove stale Run #654 wording and submit the no-refit runner for exact code/test review.


## 2026-10-11 — Phase 8 R2 code-only review: REQUEST CHANGES

- Tester reviewed developer snapshot `6e1fe57ce0e1e21e82c676cf8bf2fcbb3561df11`, hosted synthetic run [38163364534](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38163364534), and exact 15-file hash set.
- Decision [PHASE8_AUTH_HASH_AND_GAP_SUMMARY_TESTER_DECISION_R2_2026-10-11.json](research/gates/PHASE8_AUTH_HASH_AND_GAP_SUMMARY_TESTER_DECISION_R2_2026-10-11.json) = **REQUEST_CHANGES**. The immutable source-hash correction and matching test are correct; however, the critical-data-gap summary has a missing-header truthiness bug which can label all expiry fields blank when only one required header is missing.
- Developer submitted the per-field predicate correction and mixed-header/zero-row regression in commits `8511ba7` and `4d93085`. A fresh hosted synthetic gate is required before resubmission.
- R1 remains consumed/disabled; this review is code-only and grants no new data access, option P&L, holdout, source request or strategy promotion.




## 2026-10-11 — Phase 8 corrected snapshot accepted with restrictions

- Hosted [run #38163678060](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38163678060) passed the exact synthetic contract suite for developer-tested commit `4d93085519675484570bb054cbedb1c2405708f0`. The metadata-only cached-data job was skipped because R1 remains disabled and consumed.
- New decision [R3 tester report](research/gates/PHASE8_AUTH_HASH_AND_GAP_SUMMARY_TESTER_REVIEW_R3_2026-10-11.md) and [machine decision](research/gates/PHASE8_AUTH_HASH_AND_GAP_SUMMARY_TESTER_DECISION_R3_2026-10-11.json): **PASS WITH SCOPED RESTRICTIONS** for the exact code/test snapshot only.
- No real-data scan, option P&L, holdout access, new-source request or strategy promotion was authorized. Expiry metadata, lot/tick history and executable bid/ask gaps still block execution. The independent daily H=1 numerical-comparison anomaly remains open.


## 2026-10-11 — New tester gate: daily H=1 future-return ULP mismatch

- Independent review of [run #38162517430](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38162517430) found 64 exact-float mismatches in the daily H=1 source-derived `future_return` comparison; reported max absolute difference is `3.469446951953614e-18`.
- Report: [PHASE8_H1_FUTURE_RETURN_ULP_TESTER_REVIEW_R1_2026-10-11.md](research/gates/PHASE8_H1_FUTURE_RETURN_ULP_TESTER_REVIEW_R1_2026-10-11.md). Decision: **REQUEST_CHANGES**; machine gate [JSON](research/gates/PHASE8_H1_FUTURE_RETURN_ULP_TESTER_DECISION_R1_2026-10-11.json).
- Requested correction: bounded 2-ULP exact-or-near-equality for source-derived float64 `future_return` only, with ULP diagnostics and synthetic tests for 1/2/3 ULP cases and non-finite/sign errors. Preserve exact label/timestamp checks, metric aggregate tolerance, source pins and immutable Run #994 artifact. Hosted evidence must prove all observed mismatches are within 2 ULP; otherwise remain blocked.
- This is not strategy evidence and grants no option P&L, holdout access, source-data request or strategy promotion.


## 2026-10-12 — Tester gate PHASE8_GREEK_ENRICHMENT_R1

- Exact developer snapshot reviewed: 467a08195bb5031bf73eb01fc86f2129f9776227.
- Workflow [#38168820750](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38168820750) passed exact four-blob checks, ran the developer synthetic suite in an isolated worktree, and passed 162 independently generated CE/PE Black–Scholes reference cases including IV inversion, Greek sign/bounds, finite-difference Delta/Gamma/Vega and invalid-premium rejection.
- Decision: [machine JSON](research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_DECISION_R1_2026-10-12.json) = PASS_WITH_SCOPED_RESTRICTIONS; [review report](research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_REVIEW_R1_2026-10-12.md).
- Scope authorized: only public HF NIFTY minute spot + dated NIFTY expiry partition-list retrieval and enrichment of the existing encrypted cached partial grid. No Dhan API, P&L, holdout, strategy promotion, commercial use or plaintext output is authorized.
- Developer hosted run [#38168504700 attempt 2](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38168504700) is currently restoring the pinned source artifact, has successfully fetched HF spot/expiry metadata, and is executing the enrichment/re-encryption step. Final output coverage, row hashes and encryption checks remain pending.

**Tester → Developer:** independently verify the terminal artifact, coverage report, row preservation, encrypted-part hashes and unresolved-Greek statuses before accepting delivery.

**Developer → Tester:** report terminal run outcome and preserve the partial-grid / proxy / non-commercial restrictions in all final references.


## 2026-10-12 — Phase 8 Greek enrichment R2 tester decision
- Canonical independent tester workflow [#38194602133](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38194602133) passed exact four-file blob pins, the developer synthetic suite, and 162 independently coded Black-Scholes/finite-difference CE/PE cases. Exact developer snapshot: `6ebb54bdbbc7ed0198d23d0b555aea547a127f9f`.
- Decision: [R2 machine JSON](research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_DECISION_R2_2026-10-12.json) and [R2 review report](research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_REVIEW_R2_2026-10-12.md): **PASS_WITH_SCOPED_RESTRICTIONS**.
- The developer run [#38194592152, attempt 2](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38194592152) passed authorization, cached-source integrity, and HF metadata/spot retrieval. As of this status update, the 61-part enrichment/re-encryption step remained in progress; output rows, encrypted hashes and coverage were not yet accepted.
- A second, duplicate workflow had a stale R1 path and failed its pin gate. It was removed and logged; it did not request source data and does not supersede the canonical passing decision.
- Scope restrictions remain: public HF spot plus expiry file-list enrichment only; no Dhan API call, empirical option P&L, holdout access, strategy promotion, commercial use, or plaintext upload.


## 2026-10-12 — Phase 8 Greek enrichment R2 tester decision
- Canonical independent tester workflow [#38194602133](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38194602133) passed exact four-file blob pins, the developer synthetic suite, and 162 independently coded Black-Scholes/finite-difference CE/PE cases. Exact developer snapshot: `6ebb54bdbbc7ed0198d23d0b555aea547a127f9f`.
- Decision: [R2 machine JSON](research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_DECISION_R2_2026-10-12.json) and [R2 review report](research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_REVIEW_R2_2026-10-12.md): **PASS_WITH_SCOPED_RESTRICTIONS**.
- The developer run [#38194592152, attempt 2](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38194592152) passed authorization, cached-source integrity, and HF metadata/spot retrieval. As of this status update, the 61-part enrichment/re-encryption step remained in progress; output rows, encrypted hashes and coverage were not yet accepted.
- A second, duplicate workflow had a stale R1 path and failed its pin gate. It was removed and logged; it did not request source data and does not supersede the canonical passing decision.
- Scope restrictions remain: public HF spot plus expiry file-list enrichment only; no Dhan API call, empirical option P&L, holdout access, strategy promotion, commercial use, or plaintext upload.


## 2026-10-12 — Phase 8 R2 terminal failure and R3 review opened
- Developer run [#38194592152 attempt 2](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38194592152) failed at terminal row-count validation with `source=None output=8999865`. The final validation and upload were skipped; no enriched artifact was uploaded.
- Root cause: input manifest lacked top-level `rows_preserved`; counts were available per part. R1 had failed at the same point and the R2 synthetic tests did not model this manifest schema.
- Developer R3 snapshot [f556c7b44088f18551453c36f78e8d5de7fe141e](https://github.com/vishnuvcr/Naked-option-v1/commit/f556c7b44088f18551453c36f78e8d5de7fe141e) now sums part row counts, validates optional aggregate fields, adds fixtures for missing/matching/mismatching and malformed counts, and checks 8,999,865 rows before any external HF request.
- Tester R3 workflow has been prepared to pin that exact snapshot and adds an independent count-sum audit alongside the 162-case independent Greek formula audit. R3 decision is not yet available; source access remains blocked until it is recorded.
- Restrictions unchanged: no Dhan API, P&L, holdout, strategy promotion, commercial use or plaintext upload.


## R3 exact-snapshot review preparation — 2026-10-12
- Candidate developer head: `f556c7b44088f18551453c36f78e8d5de7fe141e`. Tester request will pin four exact blobs and test the final head, including the second commit that hardened the preflight environment handling.
- R2 is rejected as a dataset-delivery attempt: terminal row-count error, no validation and no artifact. The previous R2 formula pass is not acceptance of the dataset and must not authorize R3.
- The canonical tester workflow has been changed to R3 paths, and the independent audit now independently checks valid/invalid per-part row count manifest cases. R3 request/decision/report will be committed only after confirming the exact candidate hashes.
- No HF data requests or enrichment are permitted for the current developer candidate until the R3 decision matches the exact pinned snapshot.


## 2026-10-12 — Phase 8 Greek enrichment R3 exact-snapshot decision
- Canonical tester workflow [#38195900109](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38195900109) succeeded. Exact candidate SHA and four developer blob hashes passed. Developer synthetic tests passed. Independent suite passed 162 CE/PE Black-Scholes / finite-difference cases and separately passed manifest-count auditing (2 valid fixtures; 4 invalid fixtures rejected).
- Decision: **PASS_WITH_SCOPED_RESTRICTIONS** for developer snapshot `f556c7b44088f18551453c36f78e8d5de7fe141e`: [machine JSON](research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_DECISION_R3_2026-10-12.json) · [review report](research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_REVIEW_R3_2026-10-12.md).
- This is a code/source-access gate only, not acceptance of a dataset. Developer run [#38195812828 attempt 2](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38195812828) is running after the decision. Tester must separately inspect any terminal encrypted artifact and its coverage report.
- Restrictions unchanged: no Dhan API, historical option P&L, holdout, strategy promotion, commercial use or plaintext publication; the HF partial grid and CC-BY-NC-4.0 research-only licensing limitations remain.


## 2026-10-12 — Independent artifact-delivery gate prepared
- A separate tester-owned workflow and synthetic-tested audit script now exist for the final R3 uploaded bundle. It verifies source run/commit/artifact identity, ZIP CRC, all 61 encrypted chunk hashes, exact per-part row sums, manifest/coverage agreement, Greek status/expiry/IV count totals, source attribution/license/revision, and absence of plaintext files.
- Artifact gate request intentionally remains absent until a successful developer artifact ID is available. No artifact-level decision has been issued yet; code-only R3 approval does not equal dataset acceptance.


## 2026-10-12 — R3 developer artifact available for independent review
- Developer run [#38195812828 attempt 2](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38195812828) completed successfully at the exact approved SHA `f556c7b44088f18551453c36f78e8d5de7fe141e`. Its final row/hash/encrypted-only validation passed and artifact upload succeeded.
- Artifact: ID `11723198817`, name `nifty-1m-greeks-enriched-r3`, 1,610,370,340 bytes; uploaded ZIP SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`.
- Developer-reported counts: 8,999,865 rows preserved; 61 encrypted monthly parts; 8,418,616 option rows with Delta; zero exact-timestamp spot misses; zero unmapped expiries under the current proxy rules. These are pending independent ZIP/coverage audit.
- Artifact review workflow and synthetic auditor are on this branch. The artifact request JSON will pin exact developer run, snapshot, artifact ID/name, ZIP digest and expected row totals. Code-only R3 PASS is not a data-delivery PASS.


## 2026-10-12 — Tester artifact workflow no-job failure and simplified retrial
- Runs #38196504082, #38196604819, #38196664518 and #38196699993 failed before creating any jobs; no independent artifact audit or decision was produced. This is a workflow orchestration failure, not a dataset validation result.
- Replaced the layered inline workflow with a compact workflow calling `scripts/run_phase8_greek_artifact_tester.py`, which validates the exact approved R3 code decision and artifact identity/digest, executes synthetic rejection tests, downloads and hashes the ZIP, checks archive CRC, performs the actual ZIP/manifest/coverage audit, and writes the tester decision and logs.
- Request revision 2 retriggers the same exact immutable artifact (developer run 38195812828, artifact 11723198817, ZIP SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`). Artifact review remains pending until the new workflow produces an actual decision.

## 2026-10-12 — Phase 8 Greek-enrichment artifact audit R1 (workflow 38197110523)
- Decision: REQUEST_CHANGES.
- Developer run 38195812828; artifact ID 11723198817.
- Artifact not accepted; see tester report findings.
- Trading/economic gates remain blocked.


## 2026-10-12 — R3 artifact tester download authentication correction (revision 3)
- Tester run #38197110523 created a job; exact source identity and synthetic auditor fixtures passed, but artifact download failed with HTTP 401 before the actual ZIP audit. Decision is REQUEST_CHANGES; this is a tester download plumbing defect, not a data-integrity finding.
- Corrected the tester's redirect handling: authenticated request to the GitHub artifact API obtains a short-lived signed URL, and the second request downloads from that URL without reusing API credentials. Request revision 3 retriggers the same immutable artifact ID and digest.
- Artifact remains pending independent ZIP/hash/coverage acceptance.

## 2026-10-12 — Phase 8 Greek-enrichment artifact audit R1 (workflow 38197317740)
- Decision: PASS_WITH_SCOPED_RESTRICTIONS.
- Developer run 38195812828; artifact ID 11723198817.
- Encrypted part hashes, row counts, coverage and no-plaintext conditions passed.
- Trading/economic gates remain blocked.


## 2026-10-12 — Phase 8P Greek prediction code gate
- Scope R3: PASS for scope only.
- Developer synthetic suite: PASS on the submitted code/test blobs.
- Independent tester code review R1: **REQUEST_CHANGES**; 9/13 independent checks passed.
- Blockers: missing end-to-end pipeline and artifact-bound aggregate outputs; caller-controlled fit authorization; missing chronological block-order validation; mixed OPTION/SPOT snapshot helper fails on normal SPOT NaN Greek offsets; no daily-specific feature path/time mapping; preflight does not cryptographically bind artifact IDs/hashes, label-maturity proof and protected-holdout mask.
- Status: **CODE GATE BLOCKED**. Real artifact access/decryption, empirical fitting, holdout use, option P&L and strategy promotion remain prohibited.
- See [tester review](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-tester/research/gates/PHASE8P_CODE_REVIEW_TESTER_R1_2026-10-12.md) and [machine decision](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-tester/research/gates/PHASE8P_CODE_REVIEW_TESTER_DECISION_R1_2026-10-12.json).

**Tester → Developer:** fix F1–F6 and resubmit an exact new snapshot; empirical gates remain locked.
**Developer → Tester:** preserve R1 unchanged and independently rerun hashes, formula signs, snapshot edge cases, time/split guards and full pipeline synthetic coverage.


## 2026-10-12 — Phase 8P code review R2 decision and handoff
- Independent audit of developer snapshot `a5a38e3592234aea9052e697416c8154c6f8e8f8` passed 16/16 checks at [tester workflow #38201657383](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38201657383). Decision `PASS_FOR_CODE_ONLY` and report R2 are committed on this tester branch.
- This approval permits a separately reviewed schema-only preflight for the two exact pinned artifacts, not empirical model fitting. The existing preflight workflow proposal is under review and no artifacts have been opened by this step.

**Tester → Developer:** review preflight workflow before artifact download; independently assess its aggregate report afterwards.
**Developer → Tester:** preserve R1 REQUEST_CHANGES; use R2 only for the exact approved code snapshot and do not run models until separate preflight decision.


## 2026-10-12 — Phase 8P preflight executor workflow R2 approved
- Independent tester workflow [#38202785798](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38202785798) passed 29/29 static/security/synthetic checks on developer workflow blob 474712e945dfaef83c814c9e17d1513ad44a3152.
- Decision: PASS_PREFLIGHT_WORKFLOW_ONLY. Human report and machine decision are recorded at research/gates/PHASE8P_PREFLIGHT_WORKFLOW_TESTER_R2_2026-10-12.md and research/gates/PHASE8P_PREFLIGHT_WORKFLOW_TESTER_DECISION_R2_2026-10-12.json. Decision blob: 0f7cf48945704e9498b7e149a7ae71a820809070.
- Review receipt artifact 11725568231; SHA-256 cbb785ad9832b928b7424f6e3c4323a85112e3d7377ab92d5222dd6a84265260.
- The authorized developer request was updated only to permit schema/coverage preflight. Run [#38202961271](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38202961271) is queued. No model fit is authorized; independent review of the resulting report is mandatory.

**Tester → Developer:** verify the exact approval blob before artifact download; submit the aggregate-only report for a new independent data-preflight decision.
**Developer → Tester:** keep empirical fitting blocked until the report's exact artifact identities, schemas, target maturity, protected split and coverage are reviewed.


## 2026-10-12 — Phase 8P preflight data gate R1: BLOCKED_DATA
- Independent report review [#38203737398](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38203737398) verified the aggregate artifact digest and both pinned input artifact hashes.
- Decision: BLOCKED_DATA. Report artifact 11726646000, SHA-256 b12cf1a2f9bc4b20d01aa39df6c74f16898ee454f8e16cb29455e816d8d3ae92. Tester review receipt 11726521340, SHA-256 81b6d1818715cb1c46e29b93f66d150dd434b25fdaa03723d3040786e17de924.
- Exact symbolic blocker: DUPLICATE_OPTION_CONTRACT_TIMESTAMP_ACROSS_PARTS. Coverage panel count is zero because the feature-frame builder stops at the first repeated key. The report does not establish whether duplicates are exact repeated rows or conflicting observations.
- No model fit, holdout metrics, external source request, option P&L or strategy promotion occurred. Keep fitting blocked.
- [Human report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-tester/research/gates/PHASE8P_PREFLIGHT_DATA_TESTER_R1_2026-10-12.md) · [Machine decision](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-tester/research/gates/PHASE8P_PREFLIGHT_DATA_TESTER_DECISION_R1_2026-10-12.json)

**Tester → Developer:** add a hash/count-only duplicate-key diagnostic and synthetic fixtures; do not silently drop duplicates.
**Developer → Tester:** submit the exact diagnostic code/test snapshot for an independent code gate before using it on the encrypted input.


## Phase 8P duplicate diagnostic R4 — independent code-only gate PASS (2026-10-12)

- Decision: **PASS_FOR_DUPLICATE_DIAGNOSTIC_CODE_ONLY** for exact developer commit `8f8d513330d1cb064b4d3ffe9933f8e8014f2850`.
- Independent tester workflow [#38205506563](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205506563): **29/29 checks passed**. Receipt artifact [11726624314](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205506563/artifacts/11726624314), ZIP SHA-256 `464d9bffb484210a3aac1e821b78828b5016394afbf07740cd1fc0e566591bac`.
- [R4 tester report](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_R4_2026-10-12.md) and [machine decision](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_DECISION_R4_2026-10-12.json) pin six exact source/test/workflow blobs and the scope-only amendment decision.
- The R4 implementation binds schema to the artifact manifest, compares every present column except four allowed provenance fields, validates timestamp/header semantics, blocks conflicts, and emits aggregate-only diagnostics in synthetic tests. **No real artifact was accessed or decrypted.**
- Retry runs #38205280084 (stale R3 workflow request) and #38205378764/#38205429386 (brittle static audit assertions) remain non-evidence. They are preserved in the error log; corrected run #38205506563 is authoritative for this code gate.
- **Next gate: separate one-use execution workflow/request review.** It must pin this decision, exact code commit and hashes, artifact ID+digest, aggregate-only output schema, no-replay safeguards and disabled model/holdout/P&L flags. No real data access, feature preflight, model fitting, holdout review or strategy work is permitted until that workflow independently passes.

**Tester → Developer:** preserve this exact code-only PASS and historical failed runs; submit the separate one-use executor workflow/request for tester review. Do not open the artifact.
**Developer → Tester:** independently check authorization ordering, artifact identity, scope flags, output redaction, no-replay and immutable report hashing; reject any workflow that can access the artifact before the approval gate.


## Phase 8P duplicate executor workflow R1 — independent tester PASS (2026-10-12)

- Decision: **PASS_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_ONLY** for workflow blob `e1832072723a46a2688af83eb0346207325069a0` and developer request blob `fa3ae648d9da23649ad3db62c28456c032069a06`.
- Tester run [#38206319754](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206319754): **31/31 checks passed**, no failures. Receipt artifact [11727591616](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206319754/artifacts/11727591616), ZIP SHA-256 `3009787cfb7abf9f04ca2abf695d1ffabbd9c77e26e2fe0b9303beda48f56d11`.
- [Tester report](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_TESTER_R1_2026-10-12.md) and [machine decision](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_TESTER_DECISION_R1_2026-10-12.json) pin exact workflow/request, R4 code and scope decisions, and the review receipt.
- Safe no-op checks [#38205955895](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205955895) (request absent) and [#38206043280](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206043280) (independent workflow approval absent) completed without cache restore, artifact download, nonce consumption or diagnostic execution.
- Initial fail-closed request-schema errors #38205997072 and #38206009396 remain documented; request schema was corrected and the safe no-op path reverified.
- **Real artifact access/decryption is still blocked.** Workflow-only approval is distinct from the required one-use execution authorization. No duplicate counts, model fit, holdout, option P&L or strategy outcome exists.
- Next: developer submits a distinct one-use execution-authorization request; tester independently reviews it and only then can create the short-lived, max-use-1 authorization file. The first subsequent executor run must record the nonce in the permanent ledger before any cache/download.

**Tester → Developer:** preserve this exact workflow-only PASS; submit the separate one-use execution authorization request. No artifact access yet.
**Developer → Tester:** pin this decision/report, exact workflow/request, R4 code/scope and artifact identity in the one-use request; leave execution permissions closed in that request.


## Phase 8P — one-use duplicate diagnostic authorized and running (2026-10-12)

- Tester code gate R4 remains PASS (29/29); executor workflow R2 remains PASS (33/33).
- One-use execution authorization: [tester report](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTION_AUTHORIZATION_TESTER_R1_2026-10-12.md) and [authorization JSON](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTION_AUTHORIZATION_R1_2026-10-12.json). Permission is limited to the pinned aggregate-only duplicate diagnostic.
- Developer run [#38207005953](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38207005953) passed authorization, consumed the nonce before data retrieval, restored cache and verified source ZIP hash. Its diagnostic step is currently running; no report/result has been accepted yet.
- Model fit, holdout, deduplication, external source queries, option P&L and strategy promotion remain prohibited until an independent reviewer passes the exact output report.

**Tester → Developer:** finish only the authorized duplicate scan and publish the pinned aggregate result.
**Developer → Tester:** review run report and digest before any feature preflight or model fitting.


## Phase 8P — real duplicate diagnostic R1 failed technically (2026-10-12)

- Developer run [#38207005953](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38207005953) passed its one-use authorization gate, consumed the nonce before source access, restored the cached encrypted ZIP and verified the pinned source hash.
- The diagnostic step terminated with exit code 143 and GitHub runner-shutdown message after approximately 12 minutes. No sanitized aggregate report or output artifact was produced.
- Decision: **NO DATA RESULT / NO MODEL AUTHORIZATION**. This is a technical runner failure, not evidence about duplicate frequency or market predictability. The consumed nonce R1 is not reusable.
- The developer must submit a new exact executor revision and request with a new nonce; the tester must independently approve the workflow/request and then issue a separate one-use execution authorization before data access. Preserve run R1 and its failure log.

**Tester → Developer:** submit a fresh, exact one-use executor revision; do not reuse R1 nonce or infer data findings.
**Developer → Tester:** keep all model/holdout/P&L/strategy gates closed until the new aggregate report is independently accepted.


## Review cadence amended by user — 2026-10-13

- Independent tester review is deferred until the planned research results are acquired, frozen, and indexed. The tester branch will not issue per-step scientific reviews.
- The existing R2 R3 REQUEST CHANGES record remains in the historical audit trail; it does not trigger another review before the results bundle exists.
- The tester workflow triggers only on the formal acquired-results request and verifies the exact source commit, changed-source blob IDs, and the result-bundle manifest hashes. A manual dispatch remains available for that post-acquisition gate.
- The tester role is dormant until the developer submits the complete bundle. See [cadence policy](governance/TESTER_REVIEW_CADENCE_POLICY_2026-10-13.md).
