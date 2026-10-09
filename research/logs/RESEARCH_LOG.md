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


## 2026-10-09 — Protocol workflow repair and Run #994 checkpoint

- Research Protocol Check #997 (`37959386545`) failed in `Validate repository contract` because main lacked `scripts/validate_protocol.py`; this was confirmed from the exact GitHub Actions job log, not inferred from the run summary.
- Synced the missing validator scripts and literature registry from `phase-07-developer` to `main` without changing the research protocol or scientific implementation. Commits: `ed846e48b4129ce72bd759ca7e754b58b692cb44`, `b8f96b1d63e1bc325970797902b459983e3f9169`, `37149b5639215031f653990959b53ed8f6251c09`.
- Run #994 (`37957677656`) remains in progress at `scripts/run_phase7_ensemble.py`; regression and the exact-snapshot authorization gate passed. No artifacts or accepted metrics are available at this checkpoint.
- Run #925 remains rejected/non-evidence. Phase 7 promotion and Phase 8 remain blocked until the fresh run is complete and independently audited.


## 2026-10-09 — CI repair verified

- Main Research Protocol Check #1008 (`37960307076`) passed repository contract and literature registry validation.
- The repair was infrastructure-only; phase authorization and scientific status are unchanged.
- Run #994 still has no published artifacts at the latest query, so no empirical results are accepted and the tester audit cannot yet begin.
 
## 2026-10-09 — Approved tester-audit workflow preflight verified

- Automatic workflow run #1 was triggered following a successful documentation-only developer protocol run #1033.
- Preflight found no phase7-ensemble-results artifact and correctly skipped the independent calculation; no Phase 7 evidence or tester approval was produced.
- The workflow was tightened afterwards to require exact upstream workflow identity, branch, successful completion, source SHA and both required artifact names. The manual path has the same controls and requires a run ID.
- This validates only the no-artifact safety path. Run #994 remains the active empirical target and still has no artifact published.


 
## 2026-10-09 — Run #2 verified identity and no-artifact guard

- Workflow run #2 checked source run #1037. The exact Research Protocol Check name, phase-07-developer branch, completed-success status and source SHA passed; the expected aggregate artifact count was zero, so the independent audit correctly did not run.
- This verifies preflight safety only, not data/model performance. The newly triggered audit workflow runs for later documentation commits should likewise skip until the empirical run uploads both required artifacts.
- Run #994 is still running at the model script; Phase 8 remains gated.


## 2026-10-09 — Phase 7 implementation correction versus frozen specification

A direct comparison of the exact Run #925 source commit (`682eadf2a9eb4de250bc3db27d02e57f88687fa1`) and Run #994 source commit (`b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`) found the Phase 7 method-spec file is identical at both commits (blob SHA `964b323f5ed86b12f743dea1c9b842aba166996a`). The implementation changed to address the tester's four material findings: P10's inclusive [0.45, 0.55] abstention mask; excluding rows with non-finite volatility/trend from regime counts; retaining non-evaluable rows as NaN in family-bootstrap Brier differentials; and applying each candidate's eligible-row mask to chronological block diagnostics. Explicit regression coverage was added, and the current result validator keeps the P08/P09 regime diagnostic invariant while permitting P10's abstention-masked block-count difference.

These are implementation repairs toward the frozen specification, **not a passing result**. Run #994 is still active and has no published aggregate or row-level artifacts at the last poll. No metric or strategy is accepted. Its artifacts must pass the independent tester workflow before Phase 8 can be considered.


## 2026-10-09 — Open independent review: P10 diagnostic block-count interpretation

The frozen Phase 7 spec says P08/P09/P10 regime diagnostic block counts must equal candidate chronological block counts. The validator currently enforces the equality only for P08/P09 because P10's registered abstention can remove all candidate-eligible rows from a test block. The source/audit pair therefore needs explicit tester adjudication: satisfy both frozen rules in implementation, or submit a formally pre-registered tester-approved amendment before any future run. Run #994 is immutable and still active with no artifact; no post-hoc change is allowed. Full note: https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/ERROR_LOG.md.


 
## Independent tester finding — P10 diagnostic block invariant (2026-10-09)

The isolated tester branch has issued [PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md) = **REQUEST CHANGES FOR SCIENTIFIC PROMOTION** for a static consistency issue: the frozen spec includes P10 in the regime-diagnostic/chronological-block count equality, while the current validator enforces this invariant only for P08/P09 because P10 abstentions can empty a block. Run #994 may complete and be audited as the already-running immutable execution, but no metric, method or strategy may be promoted until this issue is resolved through an implementation correction or a separate pre-registered tester-approved spec amendment. Phase 8 remains blocked.
