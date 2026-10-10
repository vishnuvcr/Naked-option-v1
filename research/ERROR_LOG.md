# Error Log

## 2026-10-07 — Phase 6 Run 37668947725
- Category: implementation/runtime
- Component: scripts/run_phase6_novel.py intraday cutoff construction
- Symptom: AttributeError: 'DatetimeIndex' object has no attribute 'iloc'
- Location: line 616 at commit 85c1b8db633dc1fb79f3426ab0b065e068efc2aa
- Impact: empirical suite terminated before artifact creation; no metrics accepted.
- Root cause: invalid positional indexing API for pandas DatetimeIndex.
- Correction: use DatetimeIndex[...] and add explicit regression coverage.
- Prevention: tester approval required before fresh empirical execution.

## 2026-10-08 — Phase 6 fresh run 575 residual cutoff defect
- Category: implementation/runtime
- Component: scripts/run_phase6_novel.py later global-I03 cutoff path
- Symptom: residual use of `decision_times.iloc[rows[0]]` on a pandas DatetimeIndex remained after the earlier cutoff correction.
- Location: commit 9b9b7914f82993505ec4f2f0c3aac0b3d6732521, current file line 721.
- Impact: fresh hosted run 575 (37678088131) is classified as non-evidence because the same AttributeError would occur when the global-I03 path is reached; no metric may be accepted.
- Root cause: incomplete search/coverage of all DatetimeIndex positional accesses during the prior correction.
- Proposed correction: replace the residual access with DatetimeIndex[...] and add regression coverage plus a source-level assertion forbidding `decision_times.iloc`.
- Prevention: tester approval is required before the developer branch is advanced for a fresh empirical run.

## 2026-10-08 — GitHub live-log visibility error during Phase 6 run 575
- Category: infrastructure/tooling
- Component: GitHub Actions live-job log retrieval
- Symptom: fetching logs for in-progress empirical job 112986961991 returned HTTP 404 BlobNotFound.
- Impact: no scientific impact; live job-step status remained available through the workflow-jobs endpoint.
- Disposition: infrastructure-only visibility issue; no metric or result was inferred from missing logs.

## 2026-10-08 — Developer tooling edit attempt
- Category: developer/tooling
- Symptom: first detached-commit construction attempt failed due to a JavaScript template-literal escaping error while assembling the multi-file tree.
- Impact: no repository change; the intended correction was not written by that failed call.
- Disposition: corrected in the subsequent repository operation; no scientific impact.

## 2026-10-08 — Developer detached correction indentation defect
- Category: developer/code assembly
- Component: proposed detached Phase 6 correction commit `1aa8be846348f9e8341d572cd3289cd12ee89045`
- Symptom: the corrected `cutoff = decision_times[...]` line was initially emitted at the wrong indentation level because the replacement omitted the source line's existing leading whitespace.
- Impact: the proposed detached commit was rejected before tester submission; developer branch was not advanced and no workflow was triggered by this flawed object.
- Correction: rebuilt the detached commit with the cutoff line correctly nested inside the `if intraday:` block.
- Prevention: inspect the exact changed source lines in the detached commit before tester review.

## 2026-10-08 — Phase 6 run 578 regression arithmetic defect
- Category: tester/regression-fixture arithmetic
- Component: scripts/test_phase6_novel.py global-I03 cutoff regression
- Symptom: regression expected `decision_times[4] - 120 minutes` to equal 11:00, but the fixture starts at 09:15 with hourly spacing, so decision_times[4] is 13:15 and the correct result is 11:15.
- Hosted run: Research Protocol Check #578 (`37680279189`), job `112994273676`.
- Impact: mandatory regression failed; empirical job was skipped; no Phase 6 artifact or metric was generated/accepted.
- Root cause: arithmetic error in the newly added regression expectation, not in the production cutoff implementation.
- Correction: update the expected timestamp to 11:15 and preserve the production change unchanged.
- Prevention: independently recompute fixture timestamps for every explicit time-delta assertion before the next hosted run.

## 2026-10-08 — Phase 6 Run #581
- No execution error occurred. Protocol, regression, empirical suite, schema validation and artifact upload all passed.
- The independent tester nevertheless recorded a scientific caution: raw maxima across 140 executed cells are not treated as discoveries because multiple-comparison and downstream trading gates remain outstanding.

## 2026-10-08 — Phase 7 Run #600 workflow dependency failure
- Category: infrastructure/workflow
- Component: `.github/workflows/phase-07-ensemble.yml`
- Symptom: regression job failed at `pip install -r requirements.txt` because the repository has no root requirements.txt.
- Hosted run: Research Protocol Check #600 (`37716619573`), job `113114446777`.
- Impact: regression suite skipped; empirical job skipped; no Phase 7 metric or artifact generated.
- Root cause: Phase 7 workflow incorrectly assumed a repository-level requirements file instead of following the established explicit dependency installation used by Phase 6.
- Correction: install numpy, pandas, scikit-learn and pyarrow explicitly and add canonical cached-data restoration/acquisition steps.
- Disposition: non-evidence infrastructure failure; tester gate `research/gates/PHASE7_RUN600_WORKFLOW_FAILURE_TESTER.md` = REQUEST CHANGES.

## 2026-10-08 — Phase 7 Run #608 regression harness defect
- Category: regression/test-harness
- Component: `scripts/test_phase7_ensemble.py`
- Symptom: `NameError: __file__ is not defined` when executing the production module source via `exec()`.
- Hosted run: Research Protocol Check #608 (`37716925536`), regression job `113115445197`.
- Impact: regression assertions did not execute; empirical job was skipped; no Phase 7 artifact or metric was generated.
- Root cause: synthetic namespace omitted the production module's `__file__` variable.
- Correction: supply deterministic `__file__` and assert the initialization path.
- Disposition: non-evidence; tester gate `PHASE7_RUN608_REGRESSION_TESTER.md` = REQUEST CHANGES.

## 2026-10-08 — Phase 7 Run #608 P07 fixture defect
- Category: regression/test-fixture
- Component: `scripts/test_phase7_ensemble.py` P07 causal stacking test
- Symptom: fixture asserted all predictions through row 219 were NaN, although rows 200-219 have exactly 200 prior observations and satisfy the frozen training minimum.
- Impact: the corrected harness would have failed its own P07 boundary assertion; no new hosted execution was authorized from that faulty fixture.
- Correction: require NaN only for rows 0-19 and finite predictions for rows 200-219.
- Disposition: tester gate `PHASE7_RUN608_REGRESSION_FIXTURE_APPROVAL_TESTER.md` = PASS.

## 2026-10-08 — Phase 7 Run #614
- Category: regression/test-harness
- Hosted run: Research Protocol Check #614 (`37717431486`), regression job `113117063695`.
- Symptom: the developer branch at run time still contained the unfixed `ns={}` execution namespace, causing the same `NameError: __file__ is not defined`.
- Impact: regression failed; empirical job skipped; no artifact or metric accepted.
- Root cause: approved corrections had not yet been applied to the actual developer branch when Run #614 started.
- Correction: applied directly to the live developer branch with commit `84ffd525cc3ae77571a0cb38d24047b3de7b473e`.
- Disposition: non-evidence; fresh hosted verification required.

## 2026-10-08 — Phase 7 Run #622 regression signature defect
- Category: regression/test-harness
- Component: `scripts/test_phase7_ensemble.py` family-bootstrap call
- Symptom: `TypeError: family_bootstrap() takes 4 positional arguments but 5 were given`.
- Hosted run: Research Protocol Check #622 (`37717651173`), regression job `113117787284`.
- Impact: regression failed after reaching numerical tests; empirical job was skipped; no Phase 7 artifact or metric was accepted.
- Root cause: regression fixture retained an obsolete `blocks` argument after the production function signature was simplified to `(y, candidates, baseline, block_len)`.
- Correction: remove the stale argument and add a signature assertion.
- Disposition: non-evidence; tester gate `PHASE7_RUN622_REGRESSION_TESTER.md` = REQUEST CHANGES.

## 2026-10-08 — Phase 7 Run #635 detector sequencing issue
- Category: workflow trigger sequencing
- Hosted run: Research Protocol Check #635 (`37719802712`).
- Symptom: protocol and detector jobs passed but `phase7-ensemble-gated` was skipped.
- Root cause: the Run 628 tester approval gate was archived before the detector-path commit, so the current push diff contained only workflow changes and no allowed Phase 7 science-path file; the detector intentionally uses the immediate push diff to decide whether to launch.
- Impact: no regression or empirical execution; no scientific result; Run #635 is non-evidence.
- Correction: use a harmless, non-scientific test-file comment after the approved detector correction to trigger the gated workflow.

## 2026-10-08 — Phase 7 Run #637 repeated horizon-capture defect
- Category: developer branch-lineage / production data-mapping
- Hosted run: Research Protocol Check #637 (`37719955436`), empirical job `113125225580`.
- Symptom: `KeyError: ('2','E01')` after regression passed; the hosted branch still contained `H=horizons[0]` in `capture_scope`.
- Root cause: the previously approved horizon-capture correction was not present in the branch commit used for Run #637; later detector/trigger commits were based on an older lineage.
- Impact: no Phase 7 artifact or scientific metric; Run #637 is **NON-EVIDENCE**.
- Correction: reapply the exact tester-approved current-horizon binding on the current branch and retain direct multi-horizon regression coverage.
- Prevention: verify production diff against the tester-approved correction commit before every gated empirical trigger.

## 2026-10-08 — Phase 7 Run #645 closure regression defect
- Hosted run #645 (`37723044460`) failed regression with `UnboundLocalError` because `H=H` was placed inside the nested capture hook.
- Tester requested an explicit `current_h=H` closure binding.
- A first automated reconstruction was malformed by indentation and was discarded before branch advancement.
- The current correction rebuilds `capture_scope` explicitly with correct scope and `try/finally` restoration.

## 2026-10-08 — Phase 7 Run #650 tester findings
- Artifact `11532515562` was complete but not final evidence.
- Family bootstrap was non-overlapping rather than the frozen moving-block bootstrap.
- P08/P09/P10 regime diagnostic list had one extra terminal entry at daily +10 relative to candidate chronological metric blocks.
- Tester froze the correction rules before implementation.


## 2026-10-08 — Phase 7 Run #654 audit closure
- Category: audit/scientific validation
- Hosted run: Research Protocol Check #654 (`37763242007`).
- Symptom: no runtime or workflow error; all mandatory jobs completed successfully and the immutable artifact was uploaded.
- Independent audit findings: all 100 candidate cells executed; arithmetic/schema checks passed; corrected moving-block bootstrap and regime-diagnostic reconciliation matched the frozen correction gate.
- Statistical disposition: none of the ten layer/horizon family tests produced a p-value below 0.05; no Phase 7 candidate is promoted.
- Scoped audit restrictions recorded by the tester: P05/P06 chronological diagnostics are full-series rather than trade-only, and the intraday P08/P09/P10 regime inputs are computed on the one-minute causal path at hourly decision rows; neither may be tuned from Run #654 outcomes.
- Disposition: **PASS WITH SCOPED RESTRICTIONS**. Run #654 is accepted technical evidence; downstream option execution, cost, robustness and fresh-forward gates remain mandatory.


## 2026-10-09 — Phase 7 reference artifact manifest test fixture failure
- Category: regression/test fixture
- Component: scripts/test_phase7_reference_artifact.py and run_phase7_ensemble.write_reference_manifest.
- Hosted runs: #835 (37912125332), #837 (37912165684), #838 (37912206197); the first and follow-up attempts failed the new regression step before the empirical job. Run #831 (37912024282) is non-evidence for the new artifact because it started before the tester gate was archived.
- Symptom: `ValueError` from `aggregate_path.relative_to(ROOT)` because the manifest test's second temporary directory remained under `/tmp`, outside repository ROOT.
- Root cause: the first fixture path was moved under `data/reports`, but the second fixture occurrence was not updated in the same edit.
- Correction: update the second temporary-directory call to use `dir=ROOT / "data" / "reports"` in commit `14d20380632e365b2a0b6b63afe58f2775375950`.
- Prevention: search all occurrences of fixture constructors after scripted edits and ensure manifest paths obey production path assumptions. A fresh hosted run must pass before accepting the output contract.

## 2026-10-09 — Phase 7 reference artifact regression correction verified
- Hosted run: Research Protocol Check #852 (`37912587739`), developer head `ac6b30090e5146d527bb0af6dd9352a9b6a7fc93`.
- Result: original Phase 7 regression and new reference-artifact regression both PASS; tester authorization gate PASS.
- The prior fixture defect is considered corrected for this code path. Earlier failed runs remain non-evidence and are not overwritten.
- Empirical execution is still in progress; artifact integrity and scientific acceptance remain pending separate tester audit.

## 2026-10-09 — Phase 7 reference artifact runs remain active without artifacts
- Category: workflow/runtime observability; root cause not yet established.
- Components: GitHub Actions runs #852 (37912587739), #924 (37914896724), and #925 (37914905848), empirical job `python scripts/run_phase7_ensemble.py`.
- Symptom: repeated live polls show all three workflow runs and empirical jobs still `in_progress`; no artifacts are listed. Run #852's run metadata remains stale at 09:39:25 UTC. Live log requests for active jobs have returned `BlobNotFound`.
- Impact: immutable reference panels and manifest are unavailable for audit, so no new Phase 7 results can be accepted and Phase 8 remains blocked.
- Evidence classification: unknown/still running; do not label as success or failure based only on missing logs or stale metadata.
- Immediate prevention: do not spawn additional competing empirical runs. Reconcile the first completed attempt and inspect its artifact. If execution remains unbounded, amend the workflow with explicit job timeout and periodic progress checkpoints after tester review; ensure failure uploads diagnostics and partial outputs are clearly marked non-evidence.


## 2026-10-09 — Phase 7 Run #925 independent empirical tester REQUEST CHANGES

- Category: protocol/metrics/inference implementation
- Component: `scripts/run_phase7_ensemble.py` and independent artifact audit
- Hosted empirical run: [Run #925](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37914905848), immutable source commit `682eadf2a9eb4de250bc3db27d02e57f88687fa1`.
- Tester audit workflow: [Run #943](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935031119).
- Symptom: corrected independent audit recorded 2,775 passed checks and 323 failed checks across 10 panels. The failures cluster into four root causes, rather than 323 separate defects.
- Root causes: P10's frozen abstention range [0.45, 0.55] is missing from the production abstention registry; NaN volatility/trend inputs are classified as low/low regime state; P05/P06 chronological diagnostics ignore candidate abstention masks; family-bootstrap differential vectors treat non-evaluable rows as zero for abstaining candidates.
- Impact: metrics and inferential outputs are not reconciled to the frozen Phase 7 specification. Run #925 is **NON-ACCEPTED EVIDENCE**; no Phase 7 metric, model or strategy is promoted, and Phase 8 stays blocked.
- Tester disposition: `research/gates/PHASE7_RUN925_EMPIRICAL_TESTER.md` = **REQUEST CHANGES**; the independent tester report is archived in this developer branch without modifying scientific implementation.
- Required correction: fix the four findings and add tests for P10 interval edges, finite regime-state eligibility, candidate-consistent block metrics, and missing-versus-zero bootstrap differential semantics. Do not change the frozen research specification, registered candidate universe, horizons, seed, block lengths, 500 bootstrap replications or thresholds.
- Prevention: tester code approval is mandatory before a fresh empirical run; a new immutable artifact must pass independent source/hash/metric/family reconciliation before phase progression.


## 2026-10-09 — Stale Phase 7 code approval allowed premature empirical workflow dispatch

- Category: workflow authorization/orchestration
- Component: `.github/workflows/research-protocol.yml` and `.github/workflows/phase-07-ensemble.yml`.
- Symptom: the pre-Run-925 `PHASE7_CODE_APPROVAL_TESTER.md` file was treated as sufficient empirical authorization after a newer tester report had issued REQUEST CHANGES. Separately committing the production correction and its regression tests triggered multiple workflows before the correction-specific gate was added.
- Affected runs: [Run from correction commit](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935752265) and [run from correction plus tests](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935794939). They started empirical jobs without tester review of the corrections and are **NON-EVIDENCE**, regardless of completion/artifacts. No result from either run may be selected or used for inference.
- Root cause: caller authorization depended on a stale approval file's existence and the reusable workflow checked only the older artifact-output code review, not the correction-specific gate.
- Correction: all current/manual/automatic Phase 7 empirical paths now require `research/gates/PHASE7_RUN925_CORRECTION_CODE_TESTER.md` to contain both `Decision: PASS WITH SCOPED RESTRICTIONS` and `fresh empirical execution only`. The validator/test changes remain under independent review; the fresh-run gate is intentionally absent pending tester approval.
- Limitation: the connected GitHub operations do not expose an Actions-cancel operation, so already-started jobs could not be stopped through this session. They are explicitly classified as non-evidence; subsequent workflows use the stricter gate.
- Prevention: batch source/test/workflow changes before a single commit where practical; make all empirical authorization decisions correction-specific and require the newest independent tester PASS at both the caller and reusable-workflow layers.


## 2026-10-09 — Tester REQUEST CHANGES: correction approval not bound to exact code snapshot

- Category: workflow authorization/gate integrity
- Component: `.github/workflows/research-protocol.yml` and `.github/workflows/phase-07-ensemble.yml`.
- Tester review: `research/gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md` = **REQUEST CHANGES**.
- Finding: the correction-specific tester PASS is currently checked only by file presence and two text phrases. It is not tied to the exact approved source/test/validator/spec/workflow snapshot. A future protected-code commit could inherit a stale PASS and trigger empirical execution.
- Impact: no new Phase 7 empirical execution is authorized, and Phase 8 remains blocked.
- Required fix: embed the exact reviewed commit plus hashes for protected files in the correction approval manifest; both automatic and manual workflow paths must verify those hashes before authorization. Add positive and negative tests (matching snapshot authorizes; changed protected file rejects).
- The earlier attempts `37935752265` and `37935794939` remain NON-EVIDENCE. The reviewer confirmed the four scientific code corrections and hosted regression, but withheld approval because of this workflow-safety flaw.


## 2026-10-09 — Snapshot-bound tester authorization added

- Category: workflow gate hardening / prevention of stale approval reuse.
- Correction: commit `b9fc7c9e7c77efb5149d35e31509251f701122ce` adds `scripts/validate_phase7_correction_approval.py`, `scripts/test_phase7_correction_approval.py`, and requires this validator in both the automatic protocol caller and the manual/reusable Phase 7 workflow.
- Approval now requires exact protected-file SHA-256 coverage, a reviewed commit ancestor, exact agreement between tester-branch and developer-branch report/manifest bytes, and a report hash matching the manifest. Missing report/manifest or a mismatch denies authorization.
- Hosted Run #981 passed protocol and all regression suites; empirical and approval jobs were skipped because no tester approval exists. This is expected fail-closed behavior, not an empirical outcome.
- Pending: independent tester must inspect the exact commit and approve or request changes. No fresh empirical run until that review passes.


## 2026-10-09 — Phase 7 Run #989 correction-approval regression fixture
- Hosted run: [Research Protocol Check #989](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37953177951), run ID `37953177951`, developer commit `2434bbeb2cd37aa05e4639298fd59cddcf1c88a1`.
- Upstream protocol and standard Phase 7 regression checks passed; the correction-approval test failed before artifact regression or any empirical execution.
- Exact failure: `scripts/test_phase7_correction_approval.py::test_both_execution_workflows_use_snapshot_validator` asserted that the bare basename `PHASE7_REFERENCE_ARTIFACT_CODE_TESTER.md` was an exact member of `approval.PROTECTED_FILES`.
- Root cause: Python tuple membership performs exact element equality. The registered element is the full repository path `research/gates/PHASE7_REFERENCE_ARTIFACT_CODE_TESTER.md`; the guard itself already lists that full path.
- Developer correction: change the regression assertion to the full path. This is a test-fixture correction only; no scientific method, forecast, label, candidate logic, metric, or authorization scope changes.
- Disposition: Run #989 is non-evidence for all scientific purposes. No empirical phase-7 job ran, no Phase 7 metric was accepted, and Phase 8 remains blocked. Fresh hosted regression plus independent tester review of the corrected snapshot are required.


## 2026-10-09 — Phase 7 Run #992 rejected stale/malformed snapshot approval

- Category: gate-validation / approval-manifest transcription.
- Hosted run: [Research Protocol Check #992](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957038797), developer commit `8fd1fb24f9760f637fe1c623eb2364516e8b308b`.
- Protocol and all Phase 7 regression checks passed, but the fail-closed approval validator denied authorization. It detected that the report's commit/scope lines did not match the required literal format, the report digest did not match those report bytes, and one Phase 6 spec SHA-256 was transcribed incorrectly.
- No phase-7 authorization or empirical job ran; Run #992 is non-evidence and no metric/artifact is accepted from it.
- Correction: the isolated tester branch now stores a corrected report (exact required commit line and explicit `fresh empirical execution only` scope) and matching manifest digest/hash; the Phase 6 spec digest was recomputed and corrected. The exact tester blobs are being mirrored unchanged to the developer branch.
- Prevention: after copying any tester manifest/report, run the hosted fail-closed validator and inspect its emitted errors before treating approval as active. Approval applies only if every hash and bytewise comparison passes.


## 2026-10-09 — Tester branch Run #993 re-audited the rejected Run #925 artifact

- Category: prior empirical artifact audit / intentionally preserved rejection.
- Hosted tester run: [Research Protocol Check #993](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957295201), tester commit `8df090c40aef70bad0c5c9c56b9f4e41bcd58bad`.
- The change on the independent tester branch automatically re-ran the immutable Run #925 artifact audit. It again returned **REQUEST CHANGES**, with 2,775 checks passed and 323 failed, consistent with the already-recorded P10 abstention, regime non-finite, P05/P06 mask and family-bootstrap missingness findings.
- This is the old rejected artifact, not the new correction-code approval and not the fresh empirical run. Run #925 remains non-evidence; no strategy or metric is promoted from this audit.

## 2026-10-09 — Phase 7 Run #994 passed snapshot validation; empirical execution active

- Hosted run: [Research Protocol Check #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656), developer commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- Protocol, Phase 7 regression, correction-approval regression and reference-artifact regression completed successfully.
- The tester-authorization job passed, so the exact report/manifest copies, reviewed-commit ancestry and all 25 protected-file hashes validated in the hosted checkout.
- The single authorized empirical job is **in progress**. No artifact or metric is accepted until the empirical job, validator and separate independent post-run tester audit finish.


## 2026-10-09 — Run #994 live-log observability check while empirical process remains active

- Category: infrastructure observability; no scientific conclusion.
- Run: [Research Protocol Check #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656), immutable execution commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- Empirical job `113912548214` remains `in_progress` at `scripts/run_phase7_ensemble.py`, started 2026-10-09 16:15:48 UTC. Validation and artifact upload are still pending.
- Live job-log retrieval returned GitHub `BlobNotFound` while the job is active. The last metadata timestamp is unchanged, but the job remains active and has not reached a terminal state.
- Runtime reference: the earlier completed empirical script in Run #925 ran 2026-10-09 10:01:46–11:55:06 UTC (1h 53m 20s). Run #994 is still inside that observed runtime window.
- Disposition: do not classify as a failure or launch a duplicate while active. Recheck the same immutable run and inspect its artifact if/when it completes.



## 2026-10-09 — Phase 8 candidate dataset quality risk: suspicious HF field extrema

- Category: source/data-quality risk; not yet proven to be a production defect.
- Candidate: https://huggingface.co/datasets/artist-23/nifty-options-data
- Observable preview summary: 33,963,731 rows; volume range includes -4,288,892,671 to 1.44 billion and IV reaches 4,540. These values warrant checking Parquet source values, units, parsing/overflow, and exchange overlap before use.
- Related provenance issue: https://huggingface.co/datasets/codepyx23/india-index-options-1m/blob/main/README.md labels it a duplicate of https://huggingface.co/datasets/thetrademarkk/india-index-options-1m. Both list CC-BY-NC-4.0, so they must not be counted as independent data sources or treated as unrestricted commercial data.
- Impact: none on current Phase 7 run; no data has been imported or accepted from these preview checks.
- Required test before future Phase 8 use: validate OHLC inequalities, positive premium, non-negative volume/OI where present, IV units/ranges, timestamp/contract uniqueness and official NSE overlap; preserve invalid row reason codes and immutable hashes. Do not silently clamp, impute or discard rows.
- Disposition: candidate only; Phase 8 remains gated.


## 2026-10-09 — Candidate data-source provenance caution: HF minute spot mirror

- Category: pre-gate source provenance/coverage risk, not accepted data defect.
- Candidate pages: https://huggingface.co/datasets/Hitjob-Done/indian-stock-market-minute-data and https://huggingface.co/datasets/xxparthparekhxx/indian-stock-market-minute-data.
- Card reports minute/day OHLCV, NIFTY_50 and MIT license, but loading examples point to another dataset owner and timestamp basis is UTC. Do not count mirror/reupload sources as independent evidence without content-hash/lineage comparison. Spot-only; not a substitute for historical option premiums or quotes.
- Disposition: no download/merge and no scientific impact. Require NIFTY_50 shard coverage, license/provenance, IST conversion, official NSE overlap and immutable hashes before admission.


## 2026-10-09 — Data governance constraint identified for public research repository

- Category: source licensing / research reproducibility constraint, not a market-data numerical error.
- Official sources: https://www.nseindia.com/static/market-data/nse-data-policy and https://www.nseindia.com/static/nse-copyright. NSE/NSE Data retain market-data ownership and redistribution is governed by the relevant agreement; public website terms restrict reproduction/storage elsewhere except within stated limits.
- Risk: committing raw NSE bhavcopy or publishing row-level options data to this public repo may conflict with applicable terms if permission is absent. A successful download or freely accessible URL is not proof of redistribution rights.
- Prevention: keep source lineage, date ranges, schema, SHA-256 hashes, license status, reconciliation results and permitted summaries public; only cache/persist raw source bytes in storage whose access/redistribution is permitted. Check Actions cache/artifact visibility. Obtain a specific licence/permission before public redistribution if needed.
- Disposition: no raw market data committed as part of this checkpoint; Phase 8 specification/workflow not changed. Tester to independently review the data-retention path before any bulk-source workflow is expanded.


## 2026-10-09 — Candidate strategy/code repository provenance caution

- Category: external-method / source-lineage caution, not a confirmed code defect.
- Candidate `kfinance/nifty-iv-event-vol-tracker` reports an overnight straddle backtest based on NSE F&O bhavcopy and event-vol/IV analysis. It remains an unverified strategy lead; the project's readme reports are not accepted metrics.
- Candidate `SantoshSrinivas79/NSE-FNO-Data-bank` publicly stores NSE EOD archives. The fact that a dataset is publicly browsable or mirrored in GitHub does not grant permission to redistribute raw NSE data into this repository.
- Prevention: no result import/promotions; independently fetch or reproduce allowed inputs, verify source provenance and exclude synthetic samples, use chronological holdout, and test actual transaction costs. Keep research hypotheses pre-registered on a separate tester-reviewed gate.
- Disposition: no data copied/downloaded; current Phase 7 run unaffected, Phase 8 gate still closed.

## 2026-10-09 — Preventive control: dynamic tester audit and stale-run protection

- Workflow design defect found: the historical tester job was pinned to Run #925 and previously ran on every tester-branch push, repeatedly auditing a rejected artifact rather than the current target.
- Correction: the legacy audit is manual-only and has an explicit boolean opt-in. A new default-branch workflow now selects a completed successful developer run by immutable run ID/commit, requires both expected immutable artifacts, executes a fixed tester-code commit, and stores pass/fail reports on the separate tester branch. A failed or missing audit report is converted into a durable REQUEST CHANGES report and the gate fails closed.
- No science/forecast logic or protected method files changed. Run #994 remained the only active empirical target; no result is accepted until the current audit workflow runs after its artifacts exist.

## 2026-10-09 — Root causes addressed in the Run #994 implementation before fresh execution

- Run #925 independent audit returned REQUEST CHANGES (2,775 checks passed, 323 failed). The exact code delta to Run #994, while leaving the Phase 7 specification byte-identical, adds the required P10 abstention interval, prevents missing regime features from being counted in low/low regimes, preserves unevaluable candidate rows as NaN in family bootstrap differentials, and applies candidate-specific eligibility masks to block diagnostics.
- Added regression coverage for those defects and adjusted the validator's P10 block-count invariant accordingly. These changes target the frozen protocol; they do not constitute a passing empirical result.
- Run #994 is still in progress; no artifacts/metrics have been accepted. If any analogous inconsistency remains, the dynamic tester audit must record REQUEST CHANGES and the developer must repair without changing the protocol.

## 2026-10-09 — Open protocol consistency risk: P10 diagnostic block counts

- The frozen Phase 7 spec requires P08/P09/P10 regime diagnostic block counts to equal candidate chronological block counts, but the current schema validator enforces this only for P08/P09 because P10 abstentions can remove all eligible metrics from a block.
- The production output carries shared P08/P09/P10 regime diagnostics, while P10 chronological metrics apply abstention. The independent auditor does not currently explicitly gate the P10 count invariant.
- No post-hoc spec or result change is authorized. Tester must resolve the literal-spec interpretation against the fresh artifact, record PASS or REQUEST CHANGES, and require a pre-registered tester-approved amendment if the protocol itself must change. Run #994 is unchanged and Phase 8 remains blocked.


## 2026-10-09 — Available-data prediction extension: first regression fixture failure
- Category: regression-fixture expectation
- Component: `scripts/test_phase7_available_global.py::check_strict_asof_excludes_same_date`
- Hosted workflow: [Phase 7 Available-Data Prediction Extension run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37983764374).
- Symptom: the assertion expected a missing value for target date 2024-01-02, although the source had a valid 2024-01-01 observation.
- Root cause: the test incorrectly required no history rather than checking that the same-date source value (2024-01-02) is excluded and the latest strictly prior source row is selected.
- Impact: mandatory regression failed before any empirical execution. No predictor metrics were generated or accepted.
- Correction: assert that target dates Jan 2, Jan 3 and Jan 4 use source values from Jan 1, Jan 2 and Jan 3 respectively.
- Prevention: construct as-of fixtures with an explicit expected previous-row mapping and separately assert same-date exclusion before enabling empirical jobs.
- Scientific disposition: no impact on empirical evidence because the research execution was not authorized and the empirical job was skipped.


## 2026-10-09 — Available-data prediction extension: candidate-map fixture construction failure
- Category: regression-fixture construction
- Component: `scripts/test_phase7_available_global.py::check_registry_has_explicit_blocked_status`
- Hosted workflow: [Phase 7 Available-Data Prediction Extension run #3](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37983879350).
- Symptom: test fixture construction raised `ValueError: If using all scalar values, you must pass an index`.
- Root cause: a dictionary mapping candidate source IDs to one-row feature DataFrames was incorrectly wrapped as a single pandas DataFrame.
- Impact: regression suite stopped before empirical execution; no empirical predictions were generated or accepted.
- Correction: retain the fixture as a dictionary of aligned feature DataFrames, matching the production `source_map` contract.
- Prevention: regression fixtures must match function signatures and container types exactly; execute the complete suite after every fixture change.
- Scientific disposition: no empirical impact; tester authorization and empirical run remain gated.


## 2026-10-10 — Available-data prediction extension: benchmark/mask isolation correction before tester gate
- Category: scientific methodology / benchmark alignment
- Component: scripts/run_phase7_available_global.py, walk_forward_probabilities
- Discovery: static review found the candidate's historical-rate benchmark was computed only when that candidate's feature vector was complete. If candidates had different missing-feature masks, their supposed common baseline could differ.
- Risk: the family Brier improvement comparison could be confounded by candidate-specific benchmark probabilities on rows that differ in feature availability.
- Correction: compute the historical positive-rate benchmark from all eligible, purged training labels independently of feature completeness; keep the candidate model fit/prediction masked by feature availability; add a deterministic regression test comparing baselines under altered feature masks.
- Prevention: any future candidate-specific feature mask must not alter the comparator's training labels or predictions. Maintain a benchmark-invariance test across candidate families.
- Disposition: found and corrected before tester authorization and before any empirical execution. No scientific result was generated from the defective version.


## 2026-10-10 — Literature registry semantic column displacement

- **Category:** research metadata / registry validation.
- **Component:** phase-01-developer research/literature/LITERATURE_REGISTRY.csv, record L003.
- **Symptom:** The record parsed into 11 columns but its URL, verification status, method families and hypotheses were shifted across fields.
- **Root cause:** The CSV validator checks header, field count, unique source IDs and minimum record count, but does not validate whether the URL column contains a URL or the status/method fields use appropriate values.
- **Correction:** The literature developer branch corrected L003; new PDF records L037-L051 were added in header-aligned order. A separate Phase 1 error log now documents the same defect.
- **Prevention:** The independent reviewer should validate URL/status/method semantics; a validator enhancement should be made only after a separate code review and must remain independent of empirical selection.
- **Disposition:** Corrected as a documentation/metadata issue; no model or empirical result changed. Available-data empirical execution remains blocked until its own independent exact-snapshot gate passes.


## 2026-10-10 — Phase 7 extension: independent tester found specification/inference gaps

- **Category:** research-method implementation / statistical validation.
- **Component:** scripts/run_phase7_available_global.py, scripts/test_phase7_available_global.py, result validation workflow.
- **Symptom A:** G13 used standardized ret1/ret5 z-scores when the frozen spec declared raw 1-/5-session log returns. The pandas mean skipped missing sources, allowing row-wise constituent count to vary.
- **Correction A:** changed G13 to the raw-return formula and used skipna=False so any missing frozen constituent makes that row unavailable. Added a test where raw and z-score values differ and one constituent is missing.
- **Symptom B:** horizon Bonferroni correction multiplied by the number of family tests that executed, rather than the registered five horizons.
- **Correction B:** introduced a deterministic helper applying the fixed factor len(HORIZONS)=5 and reports executed test count separately. Added a fixture where only one horizon p-value is available.
- **Symptom C:** the top-level baseline metric included held-out rows where the candidate feature was missing, while candidate headline metrics did not, making direct cell-to-cell comparisons ambiguous.
- **Correction C:** retained mask-independent causal baseline predictions, added paired baseline metrics and Brier improvement on the exact candidate rows, and clarified the distinction between full baseline and paired comparisons.
- **Symptom D:** the workflow's inline validation omitted the _BASELINE cell, exact paired row counts, complete family-inference/Bonferroni checks and required reasons for blocked cells.
- **Correction D:** added scripts/validate_phase7_available_global_results.py and scripts/test_validate_phase7_available_global_results.py; included them in automatic/manual workflow regression, protected hashes and approval path set.
- **Symptom E:** the frozen spec numbered two data rules as item 7.
- **Correction E:** numbering was corrected without changing the scientific method.
- **Prevention:** tester approval is required for the exact new hashes; regression success alone is insufficient. The current request-changes report remains active until a fresh report passes.
- **Scientific disposition:** all fixes were made before any empirical run from this available-data extension. No new metrics were generated, and no model or strategy was promoted.


## 2026-10-10 — Row-level forecast evidence missing from initial extension output

- **Category:** research reproducibility / output lineage.
- **Component:** scripts/run_phase7_available_global.py and result artifact contract.
- **Symptom:** The summary JSON held only aggregate metrics, so an independent reviewer could not directly recompute the candidate-specific held-out score, paired baseline score, or the maximum-statistic moving-block family test from the stored output alone.
- **Root cause:** initial output schema recorded aggregate result cells and source hashes but did not preserve per-date predicted probabilities and realized labels.
- **Correction:** added the row-level CSV panel data/reports/available_global_prediction_panels.csv, recorded its path/SHA-256 in JSON provenance, included it in the hosted artifact upload, and extended the standalone validator to recompute candidate/baseline metrics, paired comparisons, common-row family improvements and bootstrap p-values.
- **Prevention:** do not accept summary-only artifacts for empirical promotion; all future forecast results need immutable row-level outputs with hash-based provenance and an independent reconciliation gate.
- **Disposition:** fixed in the developer branch before any empirical run from the available-data extension. No result was generated; the independent tester must re-review the exact updated snapshot and hosted regressions.


## 2026-10-10 — Row-level panel integrity hardening and unverified hosted run

- **Category:** result reproducibility / test gate.
- **Component:** scripts/run_phase7_available_global.py, scripts/validate_phase7_available_global_results.py and their regression test.
- **Correction:** write panel float values with 17 significant digits; validate every candidate's paired baseline value against the baseline panel, reconcile predicted-UP mean future log return, reject invalid availability flags and method/row-type values, ensure empty panels cannot support an executed family result, and test for deliberate baseline/p-value mutations.
- **Residual gate blocker:** the connected status lookup returns empty check collections for the corrected commits and no general workflow-run listing/dispatch action is exposed. This is a visibility blocker, not proof that the workflow failed or passed. Do not claim successful CI and do not authorize empirical execution until an actual hosted regression pass is observable.
- **Disposition:** no prediction result was generated; no authorization manifest was created.


## 2026-10-10 — Empirical gate held due unavailable hosted-run evidence

- **Category:** gate evidence / execution observability.
- **Finding:** latest commit-status and commit-workflow-run lookups returned empty lists; the available repository connector has no general workflow-run listing/dispatch action in its exposed tool set.
- **Interpretation:** this does not prove the hosted regression workflow failed or passed. It prevents independent confirmation that the current protected snapshot ran and passed.
- **Decision:** tester allows static-source review only and explicitly withholds empirical execution authorization. No approval JSON was created, no empirical predictions were generated, and no result was promoted.
- **Required resolution:** make a real hosted run record, run URL/ID, exact commit, protected SHA-256 output, both test-suite summaries and artifact validation summary accessible, then request a separate tester execution gate. Do not substitute a code-level assertion or source hash for runtime evidence.


## 2026-10-10 — Phase 7 cache/timezone repair and current gate

- **Run #41** (37992643952) failed in regression-only mode because the acquisition test fixture did not include the newly required `exchange_timezone` manifest field. The cache validator correctly rejected the fixture; the fixture manifest was updated.
- **Run #42** (37992676463) failed in regression-only mode because a reacquisition fixture mocked official close=1.0 while the generated CSV close was approximately 10,000. The stricter validator correctly rejected the inconsistent overlap record; tests were corrected to generate internally consistent comparisons.
- **Run #43** (37992695619): SUCCESS. 8/8 NIFTY acquisition/cache checks passed, 11/11 predictor checks passed, and 11/11 result-validator checks passed. The empirical job remained skipped because the authorization manifest was absent.
- The independent tester issued PASS WITH SCOPED RESTRICTIONS authorizing one exact-snapshot Phase 7 prediction batch only; report mirrored on developer branch in commit 119827f09b282b3c4d51c1fb2d73329bfe81932d. Protected SHA-256 values are recorded in the tester report.
- **Current blocker:** the attempted write of `research/gates/PHASE7_AVAILABLE_GLOBAL_APPROVAL.json` was blocked by the platform safety checks. The file remains absent and no prediction batch ran. Do not bypass the protected authorization gate via an alternate trigger.
- These CI failures are fixture-only non-evidence, and Run #43 is regression evidence only. No empirical prediction metrics were generated; no model or strategy was promoted.


## 2026-10-10 — Run #44: no candidate passes family-level inference

- [Run #44](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915) completed all jobs successfully. The empirical prediction suite ran; complete result grid validation and immutable artifact upload passed.
- Independent artifact audit checked the ZIP and internal file hashes, 91,988 panel rows, duplicate keys, probability bounds, target signs, missing predictions/labels/returns, every reported candidate metric, and all five family bootstrap p-values. No metric mismatch or panel integrity defect was found.
- **Scientific disposition:** no model promoted. Raw family p-values for horizons 1/2/3/5/10 were 0.9840, 0.8882, 0.6786, 0.7745 and 0.9800; all Bonferroni-adjusted values were 1.0.
- **Cache note:** all 11 global source manifest records have `cache_hit: false`; existing cache entries were rejected under current validation and reacquired. The current data/schema were uploaded to the workflow cache at job completion. Verify cache reuse on any future authorized run.
- Artifact ID `11657636547`; artifact SHA-256 `63b607db7227cdd91f3a62a0a8ca5f0b010d12c3bad1848ebbd9f59961804891`.
- No options strategy, Paytm Money execution cost, slippage, brokerage, or trading P&L was tested. Phase 8 remains blocked; do not interpret green workflow status as predictive significance.


## 2026-10-10 — Next prediction family proposed; empirical execution remains closed

- Run #44 completed and was independently audited. All five horizon family tests were non-significant and no candidate was promoted.
- Developer proposed Extension 2 using the already registered G03/G14/G15/G17/F03/F04/F05 methods. It targets official NSE sector index, Advances/Declines, FII/FPI/DII and F&O UDiFF bhavcopy data.
- Proposal: `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md`; handoff: `research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_DEVELOPER_SUBMISSION.md`.
- Source pages were identified, but full-history acquisition, feature generation and model fitting have **not** started. Awaiting independent tester spec review.
- The single global max-statistic family test across 35 method/horizon cells is registered in the proposal to reduce selection across methods and horizons. Any change requires a versioned spec amendment before results are viewed.


## 2026-10-10 — Extension 2 spec REQUEST CHANGES corrected

- Corrected the five tester findings: legacy-to-UDiFF archive boundary, flow normalization, exact OI/volume formulas, canonical sector index names, and missing-forecast global bootstrap behavior.
- Updated spec blob: `7f6cc6e86556db3da9f87c23c0e183bcb3282310`.
- Resubmitted for independent tester review. No source feasibility downloads or model fitting occurred. This remains a pre-implementation gate; no empirical authorization is implied.


## 2026-10-10 — Gate A Run #1: unresolved source coverage

- F&O samples succeeded from official NSE archives: legacy 2024-07-05 and UDiFF 2024-07-08, both single-date schema-valid files.
- The attempted sector-history API returned generic HTML; historical index CSV archive not yet sampled.
- NSE FII/DII API provided only current date records; current free GitHub mirror has 164 dated rows (2026-01-14 through 2026-09-30), below the registered 500-common-date minimum.
- Official Advances/Declines page yielded no dated historical table in the bounded sample.
- Tester disposition REQUEST CHANGES. Do not declare these datasets unavailable; search additional free sources and sample official daily index/equity CSVs. No full-history acquisition or model fitting occurred.
- Full report: `research/results/PHASE7_EXTENSION2_GATE_A_RUN1.md`.


## 2026-10-10 — Gate A sampler v2 Run #1 regression failure

- [Run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38019728293) failed during offline regression because the FII/DII date validator used an over-escaped ISO-date regex. The first six v1 tests passed; v2 stopped before any live source request.
- Corrected sampler blob: `fb83fe5e880a26134a765a0426f7aa85380272fb`.
- The workflow's push trigger is now gated on `research/gates/PHASE7_EXTENSION2_SOURCE_SAMPLER_V2_APPROVAL.json`; a code push alone cannot trigger source requests. Manual dispatch remains available after independent approval.
- No live data was downloaded, and no model/feature work occurred. Current exact sampler is back for tester review.


## 2026-10-10 — Extension 2 Gate A v2 exact-snapshot review mismatch

- Prior tester PASS reviewed v2 sampler blob `4c69b20e3eb4a6a0f99c6f0137de06806a13ff1f`; current sampler blob is `fb83fe5e880a26134a765a0426f7aa85380272fb` after the date-regex correction. Prior PASS is not an exact-snapshot approval for the current code.
- Current workflow blob `c535610e69c2e90934ab4e59d754b584e29ff6ec` adds a separate offline-regression job and a fail-closed exact tester-report/manifest/hash gate on both push and manual source-sampling triggers.
- Run #1 / 38019728293 failed in offline tests before any source requests; the fetch and artifact-upload steps were skipped.
- No current approval manifest exists and no live source was fetched. Await exact-snapshot independent re-review and successful hosted tests.


## 2026-10-10 — Gate A workflow exact-report enforcement strengthened

- Replaced workflow blob `c535610e69c2e90934ab4e59d754b584e29ff6ec` with `fdc0a6bef97796b38424048304b704d86f80c450`.
- The approval guard now validates the current scoped decision line, explicit no-full-history/no-model-fitting statements, exact tester report digest, protected content hashes, Git blob IDs quoted in the report, and reviewed-commit ancestry.
- This closes the risk of a historical PASS in a report authorizing a later sampler/workflow version.
- No sample is permitted until the independent tester reviews the current exact snapshot. No data was fetched by this change.


## 2026-10-10 — Gate A workflow source-coverage defect corrected

- Static audit found the v2 source job ran only `phase7_extension2_source_feasibility_v2.py`, which samples official index CSV, cash-equity bhavcopy and FII/DII data but not the required F&O archive format boundary.
- The workflow was corrected at blob `1d8991255ff284c6b9cb20c4071ab56555d18dc6` to run both bounded samplers and upload both source reports. No data fetch occurred during the fix.
- This is a pre-run coverage defect. The new workflow needs an exact-snapshot tester code-gate pass before any source request.


## 2026-10-10 — Protocol-check scope clarification

- Research Protocol Check `38020253978` succeeded on the current documentation head, but its jobs cover repository contract and literature registry validation only.
- It does not run `test_phase7_extension2_source_feasibility.py` or `test_phase7_extension2_source_feasibility_v2.py`, nor does it prove source-sampling correctness.
- Do not cite this success as Gate A regression evidence. The current v2 workflow must run its offline tests and exact approval validation before source sampling.
