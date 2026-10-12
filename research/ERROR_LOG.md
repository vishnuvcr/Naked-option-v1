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


## 2026-10-11 — Run #994 saved-panel R2 audit disposition

- Category: gate disposition / reproducibility
- Exact run: 38157819076; developer commit: 3fe13c49ed29e77b001485abe50b2d41dbb6c160.
- Outcome: hosted protocol, regression, free-source audit, artifact integrity and real saved-panel metric validation all passed. Ten panel hashes recomputed correctly and all 50,555 rows were present.
- Earlier daily H=1 future-return source-alignment failure did not recur in the accepted run; preserve it as a non-reproduced anomaly, not as proof of either data failure or a harmless issue.
- Tester decision: PASS WITH SCOPED RESTRICTIONS for reproducibility only; empirical option execution, holdout access and strategy promotion remain unauthorized.


## 2026-10-11 — Tester R2 request-changes finding: mixed expiry metadata

- Reviewed exact developer snapshot `6e1fe57ce0e1e21e82c676cf8bf2fcbb3561df11` and hosted run [38163364534](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38163364534), whose synthetic jobs passed while the data job remained skipped.
- Finding: using the list `missing_expiry_columns` as a truth-value within each iteration of `all(...)` makes a single absent header look as though every required expiry field was blank across all option rows. This breaks the output field's semantics and could misstate data diagnostics.
- Reported in [R2 tester report](research/gates/PHASE8_AUTH_HASH_AND_GAP_SUMMARY_TESTER_REVIEW_R2_2026-10-11.md); decision **REQUEST_CHANGES**. The developer has since changed the predicate and added mixed-header/zero-row tests; new hosted validation is pending.
- No P&L, holdout, new-source request or strategy promotion is covered by this code-only review.


## 2026-10-11 — Phase 8 data-gap summary correction retested and accepted with restrictions

- Developer fixed the global missing-header truthiness flaw identified in the R2 review. The all-blank flag now requires option rows > 0, all expiry headers present and every required expiry field blank in every option row.
- Mixed-header and zero-row regression fixtures were added. Hosted run [38163678060](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38163678060) passed all contract and synthetic tests; the real-data job was skipped.
- Exact-pinned R3 decision: [tester report](research/gates/PHASE8_AUTH_HASH_AND_GAP_SUMMARY_TESTER_REVIEW_R3_2026-10-11.md), [machine decision](research/gates/PHASE8_AUTH_HASH_AND_GAP_SUMMARY_TESTER_DECISION_R3_2026-10-11.json), PASS WITH SCOPED RESTRICTIONS.
- No empirical P&L or source scan was authorized. The R1 request is consumed/disabled; expiry/lot/tick/bid-ask limitations and the separate daily H=1 precision anomaly remain unresolved.


## 2026-10-11 — Tester opened separate H1 future-return floating-point gate

- Run [38162517430](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38162517430), job `114538420772`, failed source alignment on daily H=1: 64 values differ under exact `np.array_equal`; maximum absolute difference `3.469446951953614e-18`.
- Immutable source/forecast hash checks passed beforehand; daily label formula and historical source code match. The observed scale is consistent with floating-point rounding but that alone does not prove every value lies within a narrow bound.
- Tester report [R1](research/gates/PHASE8_H1_FUTURE_RETURN_ULP_TESTER_REVIEW_R1_2026-10-11.md) requests an exact-or-at-most-two-ULP float64 comparator for `future_return` only, plus actual max-ULP diagnostics and deterministic edge tests. Labels/timestamps, aggregate tolerance, source pins and artifact must remain unchanged.
- Decision is REQUEST_CHANGES until hosted reconstruction demonstrates every observed row is within 2 ULP. If not, remain blocked and diagnose.
- No option P&L, holdout, new-source request, artifact modification or strategy promotion authorized.


## 2026-10-12 — Tester workflow YAML/report indentation defect

- Category: tester workflow authoring/CI control.
- Component: .github/workflows/phase8-greek-enrichment-tester.yml.
- Symptom: initial tester workflow pushes produced failed workflow runs with zero jobs. Inspection showed a multiline Markdown report string outdented the YAML shell block.
- Correction: workflow commit 26bcbaaf35696cb6ce3c424cda48075042d953c9 builds the report from a list of Python strings so every source line remains inside the YAML run-block. The request commit then triggered a properly named workflow.
- Verification: isolated tester workflow run #38168820750 passed blob-pin validation, developer synthetic tests and 162 independent CE/PE formula cases; tester report and machine decision were committed successfully to phase-08-tester.
- Impact: no source-data request was made during the invalid-workflow attempts.


## 2026-10-12 — Duplicate Phase 8 R2 tester workflow triggered on the same request
- Category: tester workflow control / duplicate execution.
- Component: `.github/workflows/phase8-greek-enrichment-tester-r2.yml`.
- Symptom: run [38194602150](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38194602150) was triggered alongside canonical tester run [38194602133](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38194602133). The duplicate workflow retained an R1 scope-request path while the R2 request was active, so its pin gate failed and its synthetic/formula audits were skipped. Its attempt to write the same decision/report paths then failed. 
- Impact: no source-data request was made by the duplicate run. The canonical R2 workflow independently passed the exact four-blob pins, developer synthetic suite and 162-case independent Black-Scholes audit; its machine decision is the only accepted decision. The duplicate failure does not supersede that decision.
- Correction: removed the duplicate `.github/workflows/phase8-greek-enrichment-tester-r2.yml` from `phase-08-tester`; retain `.github/workflows/phase8-greek-enrichment-tester.yml` as the sole canonical workflow for the R2 request path.
- Prevention: one canonical tester workflow per gate/request; audit workflow trigger paths and unique decision/report write ownership before pushing a request.


## 2026-10-12 — Phase 8 R2 terminal row-count failure
- Category: manifest schema / failed acceptance gate.
- Hosted run [#38194592152 attempt 2](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38194592152) ended with `ValueError: row count changed: source=None output=8999865`; the row/hash validation and upload steps were skipped.
- Root cause: cached manifest did not provide top-level `rows_preserved`, although per-part `row_count` values were available. R1 experienced the same terminal failure. R2 was therefore non-evidence for data delivery.
- R3 requires per-part row-count summation, checks optional top-level total consistency, includes independent malformed-count regression cases, and adds a pre-HF guard for exactly 8,999,865 rows. No data request is approved under R3 until the exact snapshot receives a PASS decision.
