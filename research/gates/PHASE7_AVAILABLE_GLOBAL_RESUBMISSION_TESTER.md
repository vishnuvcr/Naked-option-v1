# Independent Tester Resubmission — Phase 7 Available-Data Prediction Extension

**Static source review:** PASS WITH SCOPED RESTRICTIONS  
**Empirical execution authorization:** NOT AUTHORIZED  
**Review date:** 2026-10-10  
**Scope:** correction review of the developer’s previously rejected Phase 7 extension. This is a static exact-file review only; no claim is made that hosted tests executed or passed.

## Exact current file blobs reviewed

- Frozen prediction specification: research/phase7/AVAILABLE_DATA_PREDICTION_SPEC.md — 71d2d8a9cfef5c138a75715c88bd2f17be3a2afc
- Source acquisition: scripts/acquire_global_history.py — 401fdacd3aa562b4907d422eb296fec502aa8f3c
- Predictor/panel writer: scripts/run_phase7_available_global.py — eec628a0c4760e862c2107ecb4b3262c29da2150
- Predictor regressions: scripts/test_phase7_available_global.py — 34dd77ce9f16e339a5785f3ee337bd8a29b1e7c5
- Result/panel validator: scripts/validate_phase7_available_global_results.py — 6654b8f083083b666be3ee796a53687e64ce4389
- Validator regressions: scripts/test_validate_phase7_available_global_results.py — 04da3f067a80270a09369104937af4d2989be2ff
- Hosted workflow: .github/workflows/phase-07-available-global.yml — c6fbf25e62a9882064cc350d558fd560f3afce35
- Pinned requirements: requirements-phase7-available.txt — f54f873bbba4cfd010cabc32bb4432f581520e7f

## Independent static checks

1. **G13 contract alignment:** the current source constructs the global equity composite from raw one- and five-session log-return columns. It uses skipna=False, so a missing member does not silently alter the frozen constituent set.
2. **Multiple-testing correction:** the adjustment helper uses the five registered horizons, independent of the number of horizon tests actually available. family_tests_executed and registered_family_size are reported separately.
3. **Paired baseline comparisons:** each executed candidate carries a baseline comparison calculated with the candidate’s eligible rows. The full baseline remains a separate, feature-mask-independent diagnostic.
4. **Independent output reconciliation:** the summary artifact records the forecast-panel path and SHA-256; the workflow retains the panel. The validator checks panel SHA, date/horizon/method uniqueness, return-sign/label consistency, candidate probabilities/abstentions, baseline probabilities, recomputed candidate/baseline metrics, predicted-up average return, and reproduced common-row family improvements/bootstrap p-values.
5. **Regression coverage:** current validator test source contains 11 named check functions, including synthetic valid-panel reconciliation and negative mutations of predictions, baseline probabilities, availability flags and family p-values. This is a source count, not a claim that the functions ran successfully.
6. **Workflow wiring:** current YAML contains both regression invocations, the standalone validator, workflow_dispatch, row-level panel artifact upload, and the result validator in the protected snapshot/approval paths.
7. **Scope and label preservation:** the corrected files do not change the registered 1/2/3/5/10-session label horizons, candidate universe, strict prior-session join, walk-forward purge, model settings, family bootstrap parameters or untouched-holdout boundary.
8. **Fail-closed state:** lookup for research/gates/PHASE7_AVAILABLE_GLOBAL_APPROVAL.json returns NOT_FOUND. No empirical approval manifest exists in the developer branch.

## Required execution restriction

The repository status API and workflow-run lookup returned empty lists for the reviewed predictor, validator and regression-test commits. The current connector exposes no general workflow-run listing or dispatch action, and a direct public Actions/API lookup was inaccessible. These results do not establish that the workflow failed; they also do not establish that it passed. The independent tester therefore cannot certify runtime/import/YAML success from static code alone.

The developer's corrections address the five findings in the initial REQUEST CHANGES report at the source level. However, the gate cannot advance to empirical execution until the actual automatic hosted regression run is observable and green, or an equivalent trusted execution record is provided and linked in the repository. The manual trigger remains available in the workflow, but this report does not ask the user to run it.

## Decision

**PASS WITH SCOPED RESTRICTIONS for static source review only. Empirical execution remains NOT AUTHORIZED.** No result exists to accept, no candidate is promoted, and no option-strategy phase is opened.

**Tester → Developer:** Preserve the protected-file hashes from a real workflow run, add the run URL/ID and regression summaries to the developer handoff, then request one more tester gate report. Do not create an execution-approving JSON while CI is unverified.

**Developer → Tester:** Keep the workflow fail-closed. Once the automatic/manual workflow result is accessible, verify the exact commit and all protected SHA-256 values, inspect both regression summaries and output-validation behavior, and return a separate execution-gate decision. Do not advance to option strategies.
