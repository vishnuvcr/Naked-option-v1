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
- Disposition: non-evidence; tester gate `research/gates/PHASE7_RUN608_REGRESSION_TESTER.md` = REQUEST CHANGES.

## 2026-10-08 — Phase 7 Run #608 P07 fixture defect
- Category: regression/test-fixture
- Component: `scripts/test_phase7_ensemble.py` P07 causal stacking test
- Symptom: fixture asserted all predictions through row 219 were NaN, although rows 200-219 have exactly 200 prior observations and satisfy the frozen training minimum.
- Impact: the corrected harness would have failed its own P07 boundary assertion; no new hosted execution was authorized from that faulty fixture.
- Correction: require NaN only for rows 0-19 and finite predictions for rows 200-219.
- Disposition: tester gate `research/gates/PHASE7_RUN608_REGRESSION_FIXTURE_APPROVAL_TESTER.md` = PASS.

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
- Disposition: non-evidence; tester gate `research/gates/PHASE7_RUN622_REGRESSION_TESTER.md` = REQUEST CHANGES.

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

## 2026-10-08 — Phase 8 specification tester gate REQUEST CHANGES
- Category: protocol/reproducibility
- Component: Phase 8 long-option execution specification
- Independent tester identified ten issues before empirical authorization: undefined liquidity tie-break, unfrozen fill tolerances, non-numeric data-quality thresholds, unspecified historical Paytm brokerage fallback, incomplete Black–Scholes fallback inputs, unspecified Run #654 reconstruction tolerance, implicit rather than explicit 4,800-cell universe, non-auditable anomaly-concentration rule, missing option P&L block definition, and missing overlap-signal reset behavior.
- Impact: empirical execution remained blocked; no strategy evidence was generated.
- Correction: developer froze deterministic values and statuses in the current Phase 8 method/data specifications.
- Disposition: fresh tester re-review required; no parameter or threshold was selected from empirical Phase 8 results.

## 2026-10-08 — Phase 8 specification correction closed
- The ten reproducibility findings from the first tester review were corrected in the current lineage.
- No empirical option P&L was generated before re-approval.
- Tester gate `PHASE8_SPEC_APPROVAL_TESTER.md` = PASS WITH SCOPED RESTRICTIONS.
- Remaining restrictions are explicitly frozen and are not to be changed from early Phase 8 results.

## 2026-10-08 — Phase 8 execution-engine regression harness defect
- Category: regression/test-harness
- Component: `scripts/test_phase8_execution_engine.py`
- Symptom: `test_trading_session_dte_is_timezone_agnostic()` called `trading_session_dte()` without importing it.
- Impact: the hosted Phase 8 regression suite would raise `NameError`; no empirical option P&L is authorized and no result is evidence.
- Tester gate `PHASE8_EXECUTION_ENGINE_APPROVAL_TESTER.md` = **REQUEST CHANGES**.
- Correction: developer added the explicit `trading_session_dte` import in commit `fa3f9108eb99ce723a19b6fa3031782ae3e0cb02`.
- Fresh hosted regression and independent re-review are required before the workflow/data gate can pass.


## 2026-10-08 — Phase 8 Run #742 reconstruction regression harness defect
- Category: tester/regression-harness
- Component: `scripts/test_phase8_reconstruction.py`
- Hosted run: Research Protocol Check #742 (`37815078803`), job `113441708126`.
- Symptom: `NameError: name '__file__' is not defined` while AST-executing `scripts/reconstruct_phase7_predictions.py`.
- Impact: mandatory reconstruction regression failed before Run #654 reconstruction; the workflow/data gate failed closed. No option P&L was generated or accepted.
- Root cause: the test namespace passed to `exec()` omitted the `__file__` value required by the production module for repository-root path resolution.
- Independent tester disposition: REQUEST CHANGES at `research/gates/PHASE8_RUN742_WORKFLOW_DATA_TESTER.md`.
- Correction: test harness now executes the source with explicit `__file__ = str(SRC)` and a non-main `__name__`, with deterministic regression coverage for both values.
- Prevention: AST-executed production modules must receive the same path context required by normal script execution; tester must re-run the complete hosted workflow/data gate before empirical authorization.


## 2026-10-08 — Phase 8 Run #746 reconstruction regression failure
- Category: regression/test-harness
- Hosted run: Research Protocol Check #746 (`37815192558`), phase8 regression job `113442117175`.
- Symptom: `NameError: name '__file__' is not defined` while the reconstruction regression executed `scripts/reconstruct_phase7_predictions.py` through its test harness.
- Impact: workflow-contract regression passed; reconstruction regression failed; execution-engine regression was skipped; free-source audit independently passed; no reconstruction artifact or option P&L was generated.
- Root cause: the reconstruction test harness did not provide a sufficiently explicit module execution context on the hosted path.
- Correction: tester-approved harness correction now sets `__file__`/`__name__`, compiles once and executes with the same namespace as globals and locals, with explicit context assertion.
- Disposition: Run #746 is **NON-EVIDENCE**. Tester gate `research/gates/PHASE8_RUN746_RECONSTRUCTION_APPROVAL_TESTER.md` authorizes a fresh engineering run only.


## 2026-10-08 — Phase 8 Run #759 execution-engine fixture failure
- Hosted run: Research Protocol Check #759 (`37815524247`).
- Workflow contract and reconstruction regression passed; free-source audit passed.
- Execution-engine regression failed at `test_contract_selection_tie_break` because the fixture used a 21-session expiry distance while requesting D0; the frozen DTE rule places 21 in D3.
- Classification: **test fixture defect / non-evidence**, not engine or trading evidence.
- Correction: test now explicitly asserts the 21-session distance and requests D3; no engine/cost logic changed.
- Tester approval: `research/gates/PHASE8_RUN759_ENGINE_FIXTURE_APPROVAL_TESTER.md`.


## 2026-10-08 — Phase 8 Run #765 execution-engine moneyness fixture defect
- Category: tester/regression-harness arithmetic
- Component: `scripts/test_phase8_execution_engine.py` moneyness-fallback fixture.
- Hosted run: Research Protocol Check #765 (`37815717928`), Phase 8 regression job.
- Symptom: `test_moneyness_fallback_does_not_compare_to_delta_target` asserted PASS but `choose_contract()` returned a non-PASS status.
- Root cause: the fixture used expiry 2026-10-30 and decision date 2026-10-01 with a business-day session calendar, yielding 21 trading sessions (D3) while the test requested D1.
- Impact: mandatory execution-engine regression failed; no empirical option P&L was generated or accepted.
- Independent tester disposition: REQUEST CHANGES at `research/gates/PHASE8_RUN765_MONEYNESS_TESTER.md`.
- Correction: change only the fixture from D1 to D3 and explicitly assert the 21-session DTE; production execution logic is unchanged.
- Tester approval: `research/gates/PHASE8_RUN765_MONEYNESS_APPROVAL_TESTER.md` = PASS.


## 2026-10-08 — Phase 8 Run #767 execution-engine fixture failure
- Hosted run: Research Protocol Check #767 (`37815745993`).
- Workflow contract and reconstruction regression passed; free-source audit completed successfully.
- Execution-engine regression failed because the fallback test requested D1 for a 21-session expiry distance; the frozen DTE convention maps 21 sessions to D3.
- Classification: **test fixture defect / non-evidence**.
- Correction: both fallback test calls now use D3 and explicitly assert the 21-session mapping; engine/cost logic unchanged.
- Tester approval: `research/gates/PHASE8_RUN767_ENGINE_FIXTURE_APPROVAL_TESTER.md`.


## 2026-10-08 — Phase 8 Run #783 reconstruction Git-blob hash defect
- Category: implementation/reproducibility integrity
- Component: `scripts/reconstruct_phase7_predictions.py::git_blob_sha`.
- Hosted run: Research Protocol Check #783 (`37815994871`), forecast-reconstruction job `113445754578`.
- Symptom: reconstruction rejected the current `run_phase7_ensemble.py` source with `RECONSTRUCTION_ERROR: Phase 7 source blob mismatch`.
- Independent verification: the current source blob SHA is exactly the frozen manifest value `399ad338a409b6faf56c3ee243f2643cc89f162a`.
- Root cause: the Git object header used the literal byte sequence `\\x00` rather than the required NUL byte `0x00`, causing an incorrect SHA-1 calculation.
- Impact: forecast-panel validation was skipped; Run #783 is non-evidence for reconstruction; no empirical option P&L was generated or accepted.
- Tester disposition: REQUEST CHANGES at `research/gates/PHASE8_RUN783_RECON_HASH_TESTER.md`.
- Correction: use a real NUL byte in the Git blob header and add a deterministic empty-blob SHA regression test.
- Tester approval: `research/gates/PHASE8_RUN783_RECON_HASH_APPROVAL_TESTER.md` = PASS.
- Prevention: test cryptographic/integrity helpers against canonical known vectors before hosted reconstruction.


## 2026-10-09 — Phase 8 Run #792 aggregate reconstruction mismatch
- Category: numerical reproducibility / forecast reconstruction
- Hosted run: Research Protocol Check #792 (37816655061), attempt 2, developer head `0c5712447239aec30071463a035fffafb5f7cd22`.
- Protocol, regression, free-source audit and immutable Run #654 artifact verification passed; forecast reconstruction failed at intraday H=60.
- Exact mismatches under frozen absolute tolerance 1e-9: P07 chronological block 33 Brier actual 0.24826251044249387 vs reference 0.2482625195704263; block 55 actual 0.2516896144466539 vs reference 0.2516896166236784.
- Impact: Run #792 is NON-EVIDENCE; forecast panel validation and empirical authorization were skipped; no option P&L was generated.
- Tester gate `research/gates/PHASE8_RUN792_RECON_METRIC_TESTER.md` on `phase-08-tester` = REQUEST CHANGES.
- Required: diagnose reproducibility/runtime/aggregation cause, preserve frozen tolerance and source artifact, add regression coverage, obtain tester approval, then rerun complete gate.

## 2026-10-09 — Run #792 numerical reproducibility diagnosis checkpoint
- Run #792 failed at intraday H=60 P07 chronological-block Brier reproduction; absolute differences approximately 9.13e-9 and 2.18e-9 exceed frozen 1e-9 tolerance.
- Developer compared hosted logs: Run #654 used Python 3.11.16 and Run #792 Python 3.11.17; both report NumPy 2.4.6, pandas 3.0.6, scikit-learn 1.9.1, SciPy 1.17.1, pyarrow 25.0.1 and threadpoolctl 3.7.0.
- Root cause is not yet proven; native numerical-library/runtime or solver reproducibility remain hypotheses only.
- Diagnosis recorded at `research/gates/PHASE8_RUN792_RECON_DEVELOPER_DIAGNOSIS.md`. Tester review is required before code changes. Do not widen tolerance or authorize option P&L.

## 2026-10-09 — Phase 8 Run #807 repeated reconstruction mismatch
- Category: scientific reproducibility / metric reconstruction
- Component: `scripts/reconstruct_phase7_predictions.py`, aggregate reproduction for immutable Phase 7 Run #654
- Hosted run: Research Protocol Check #807, run ID 37876792124, developer head `559af131d75a6fc256afd9ba09eb2792653fea8c`.
- Symptom: reconstruction failed again despite Python 3.11.16 pin and single-thread numerical-library controls.
- Exact mismatches under frozen absolute tolerance 1e-9: intraday H=60 P07 block 33 actual Brier 0.24826251046324826 vs reference 0.2482625195704263; block 55 actual 0.2516896144464828 vs reference 0.2516896166236784.
- Upstream protocol, regression, free-source audit, immutable Run #654 artifact integrity, and execution-engine regression passed. Forecast panel validation and empirical authorization were skipped.
- Impact: Run #807 is NON-EVIDENCE for forecast reconstruction; no option P&L or 4,800-cell empirical grid was produced.
- Tester gate `research/gates/PHASE8_RUN807_RECON_TESTER.md` = REQUEST CHANGES.
- Root cause remains unproven. Required next step: reproduce aggregation from immutable per-row predictions/labels and frozen aggregation code, add historical-path regression coverage, and resubmit for tester review. Do not alter reference values, round metrics, or relax tolerance.


## 2026-10-09 — Phase 8 Run #822 follow-up / reference artifact limitation
- Category: numerical reproducibility / research artifact design
- Component: Phase 8 reconstruction of P07 intraday H=60 chronological-block Brier values from Phase 7 Run #654.
- Symptom: Run #792 and #807 reproduced two Brier values outside the frozen absolute tolerance 1e-9 despite matching reported Python/scientific package versions in the relevant attempts; Run #807 also used single-thread numerical controls. Runner-image releases differed between Run #654 (Ubuntu 24.04 image 20260927.320.1) and Run #807 (20261004.327.1).
- Additional checks: Run #654 and #807 logs report the same Hugging Face revision and normalized intraday source SHA-256; Phase 3/6 dependency code blobs checked against Run #654 also match.
- Root cause: not proven. Runtime/runner-image numerical drift is plausible, but current evidence does not establish it conclusively.
- Structural limitation: Run #654's immutable artifact contains aggregate result JSON only, not the row-level forecast panel needed to validate historical predictions without re-fitting.
- Disposition: retain the mismatch as a fail-closed blocker. Proposal research/gates/PHASE8_RUN822_FOLLOWUP_PROPOSAL.md requests a new versioned same-run artifact with row-level predictions and runtime/source fingerprint, leaving Run #654 immutable. Tester approved the proposal only with scoped restrictions; separate Phase 7 code review and artifact audit are mandatory.
- Prevention: future research reference artifacts must preserve the exact prediction panel, labels, timestamps, block membership, data/code hashes and runtime fingerprint used to produce published aggregates. Never relax tolerance or overwrite the historical reference to hide replay differences.

## 2026-10-09 — Phase 8 saved-panel validator regression
- Category: regression verification
- Component: scripts/validate_phase7_reference_panels.py and scripts/test_phase8_reference_panels.py.
- Hosted workflow: `Phase 8 Saved-Panel Validator Regression`, run ID `37912665449`.
- Result: SUCCESS; synthetic saved-panel metrics, chronological-block diagnostics and family-bootstrap comparison passed without re-fitting model predictions.
- Scope: this validates the synthetic path only. It does not prove the validator accepts the future Phase 7 artifact, does not amend the frozen manifest, and does not authorize empirical option execution.
- Remaining gate: verify code-file hashes against the immutable artifact commit and independently audit all ten real panels/aggregate metrics after the new Phase 7 artifact is uploaded.

## 2026-10-09 — Phase 8 saved-panel validator integration contract correction
- Category: validator/workflow interface
- Component: `scripts/validate_phase7_reference_panels.py` output manifest.
- Finding: the existing `scripts/validate_phase8_forecast_panel.py` expects a `prediction_files` array containing path, rows, layer and horizon. The new validator initially emitted the copied files only in a `cells` array.
- Correction: added the `prediction_files` contract while retaining detailed cell diagnostics; commit `cf5244352bb08d89525400a8c1a29595d196e749`.
- Follow-up: added immutable Git commit code-hash verification and a regression that confirms correct hashes pass and tampered hashes fail. Hosted dedicated validator regression run `37913188030` completed SUCCESS.
- Scope: synthetic regression only. The production workflow must fetch the reference commit before validation; the real Phase 7 artifact still requires an independent audit.

## 2026-10-09 — Phase 8 code-hash verifier exposed stale synthetic fixture
- Category: regression/test fixture sequencing
- Component: `scripts/test_phase8_reference_panels.py` full artifact fixture after adding immutable Git-commit code-hash checks.
- Hosted run: dedicated validator run ID `37913154487` (commit `8a26f2ef3c2f4841be108cede9db830ccab75b77`) failed because the synthetic artifact uses a fake commit SHA and the test had not yet stubbed the code-hash verifier.
- Root cause: the production validator correctly failed closed when the synthetic fixture's commit was unavailable; the test fixture had not been adapted to the new production contract.
- Correction: isolate the synthetic artifact-directory test from real Git verification, and add a separate unit test against the current real Git commit that proves valid hashes pass and a tampered hash is rejected. Hosted run `37913188030` passed.
- Disposition: run `37913154487` is non-evidence; no production artifact or research result was accepted.


## 2026-10-09 — Phase 8 validator loaded the wrong branch's metric module
- Category: research integrity / version provenance
- Component: `scripts/validate_phase7_reference_panels.py` and Phase 8 reconstruction workflow.
- Detection: branch comparison showed `scripts/run_phase7_ensemble.py` has different Git blob IDs on `phase-07-developer` and `phase-08-developer`. The validator verified source code hashes against the manifest commit but then imported the local Phase 8 checkout's module for metric recomputation. Thus the checked code could differ from the code actually used to recompute metrics.
- Root cause: verification and execution were separate: hashes were verified from `git show`, while Python imported by module name from the current working tree.
- Correction: validator now loads and executes the exact `scripts/run_phase7_ensemble.py` bytes from the manifest commit, after hash verification. The Phase 8 reconstruction job now fetches full Git history (`fetch-depth: 0`) so the source commit can be retrieved. Regression added to load the immutable metric module and exercise hash tamper rejection.
- Validation status: dedicated hosted regression run `37913662777` still in progress at log time. Fix is not considered validated until hosted tests pass and an independent tester reviews it.
- Prevention: for reproducible research, the implementation whose hash is checked must be the same implementation that is executed; never rely on current-branch imports after validating a different commit.

## 2026-10-09 — Resolution status: validator metric-code source mismatch
- The identified mismatch between Phase 7 and Phase 8 `run_phase7_ensemble.py` implementations is corrected at code level: validator loads the exact source module bytes from the manifest commit after SHA-256 verification.
- Dedicated hosted regression `37913662777` = SUCCESS. Tester reviewed the fix and approved with scoped restrictions in `research/gates/PHASE8_PANEL_VALIDATOR_CODE_TESTER.md`.
- The defect is closed for the synthetic code path only. Real-artifact audit remains pending, and no new reference artifact or Phase 8 manifest change is accepted until the post-run audit passes.