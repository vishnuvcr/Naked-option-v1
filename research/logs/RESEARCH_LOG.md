# Research Log

## 2026-10-07 — Bootstrap

- Confirmed the GitHub repository `vishnuvcr/Naked-option-v1` exists and is currently empty.
- Reviewed Project-attached prior research artifacts.
- Recovered prior evidence that next-day NIFTY direction had failed an untouched holdout in an earlier study, while volatility-state prediction looked stronger.
- Decided not to inherit any prior result as final evidence.
- Created a finite, pre-registered method registry focused specifically on NIFTY direction and long-only option buying.
- Added tester/developer governance requirements.
- Next action: create developer/tester branches and Phase 0 workflows, then begin Phase 1 literature/source audit.

## Conversation continuity policy

The repository records research decisions, user requirements, experiment outcomes and errors. Private hidden chain-of-thought is not copied into repository artifacts. Reproducible scientific rationale is recorded as explicit decisions and protocol text instead.


## 2026-10-07 — Family D run #23 independent artifact audit
- Fresh developer run #23 (`37642007846`) completed successfully after the tester-approved D13-D15 correction.
- Artifact `phase5-family-d-results` (ID `11499450561`) was downloaded and its SHA-256 independently matched the published digest `27ca6cbc6e1653d40e2d896a81211c97a8d5e70543cf37ad9f402597eee306d8`.
- All 150 D-method/horizon cells were present and EXECUTED. Independent numerical reconciliation found no contradictions between sample counts, confusion matrices, accuracy, balanced accuracy, positive rate, probability-bin counts or metric bounds.
- D07 calibration isolation and post-cutoff label invariance were supported by the submitted implementation and passing regression suite.
- D13-D15 intraday coverage was restored: every registered horizon had non-zero observations, consistent with full 1-minute causal sequence construction and hourly-grid mapping.
- D05/D06 identical outputs were recorded as a non-blocking consequence of the explicitly frozen identical HistGradientBoosting surrogate definition.
- Gate disposition: **PASS WITH SCOPED RESTRICTIONS**. No strategy promotion; downstream economic, robustness, multiplicity and fresh-forward gates remain mandatory.
- Gate report: `research/gates/PHASE5_FAMILY_D_RUN23_TESTER.md`.


## 2026-10-07 — Phase 6 method-spec re-review
- Tester re-audited the corrected Phase 6 specification.
- The prior I07 PE direction error and I03 raw-volatility scaling problem were fixed; deterministic rank binning and estimator edge guards were also sufficient.
- Tester disposition: **APPROVED FOR PHASE 6 IMPLEMENTATION AND PRE-EMPIRICAL TESTING**.
- The next required gate is code/regression inspection before any empirical run.


## 2026-10-07 — Phase 6 implementation tester review
- Independent tester reviewed the developer implementation package without modifying developer code.
- Found a definite E06 NameError path from inconsistent `train_sorted`/`train_reference` naming.
- Required a stronger E06 training-cutoff invariance test, exact E07 composite definition, and stronger schema validation.
- Tester gate: **REQUEST CHANGES**. Empirical execution remains blocked.
