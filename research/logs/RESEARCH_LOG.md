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


## 2026-10-07 — Phase 1 literature audit

- Added 36 evidence targets spanning methodological finance literature, NIFTY/India-specific research, official NSE/SEBI/Paytm Money sources, recent preprints and open-source replications.
- Registered H01–H20 before current-repository empirical trading results.
- Main methodological conclusion: raw classification accuracy is insufficient; the research must connect forecast probability to net option break-even after IV/theta/costs.
- Recent NIFTY-specific claims from 2025–2026 are treated as replication targets, not facts.


## 2026-10-07 — Phase 1 tester REQUEST_CHANGES and developer correction

- Tester requested a reproducible literature search protocol, machine-readable literature registry, and README navigation links.
- Added `research/literature/LITERATURE_SEARCH_PROTOCOL.md` with actual search surfaces, representative exact queries, screening criteria, evidence classes and limitations.
- Added `research/literature/LITERATURE_REGISTRY.csv` with source IDs and verification status.
- Updated README to link the new artifacts.
- Phase 1 remains gated pending fresh tester review.

## 2026-10-07 — Phase 1 tester re-review correction

- Added explicit related-method, related-hypothesis and replication-requirement fields to the literature CSV registry.
- Normalized the error log so appended rows are real Markdown table rows rather than literal escape sequences.
- Phase 1 remains gated pending tester confirmation.

## 2026-10-07 — Phase 1 literature registry parse correction

- Tester found one malformed CSV row caused by unescaped commas in a paper title.
- Corrected the row using CSV quoting.
- Added `scripts/validate_literature_registry.py` and wired it into the automatic/manual research protocol workflow.
- Phase 1 remains gated pending tester recheck.

## 2026-10-07 — Phase 1 gate passed

- Independent tester final report passed Phase 1.
- Phase 1 evidence map, search protocol, hypothesis catalog and finite method registry are frozen as the starting research universe.
- Advanced to Phase 2: data acquisition, point-in-time validation and composite-source reconciliation.

## 2026-10-07 — Phase 2 tester REQUEST_CHANGES and correction

- Tester required explicit BSE comparator sources, official NSE contract/lot-size source, live official option archive acquisition, raw-data cache population, snapshot hashing, and optional HF metadata access.
- Added BSE/NSE source rows, official 05-Jul-2024 legacy and 08-Jul-2024 UDiFF acquisition, schema validation, raw cache usage, snapshot manifest generation and HF dataset probing via HF_TOKEN.
- Phase 2A remains gated pending independent tester recheck.

## 2026-10-07 — Phase 2B acquisition/reconciliation package submitted

- Added global source coverage and conservative availability rules.
- Added actual Hugging Face research-reference acquisition and official-vs-derived reconciliation.
- Added static syntax/workflow validation to prevent silent CI failures.
- Submitted Phase 2B to independent tester; no predictive labels/models may begin until data gate passes.

## 2026-10-07 — Phase 2B tester REQUEST_CHANGES and correction

- Tester identified a serious integrity flaw: the first reconciliation pass reported quality metrics without enforcing them, silently collapsed duplicate intraday keys, compared a weekly derived file against all official expiries, and skipped underlying reconciliation.
- Corrected the reconciliation logic to aggregate the derived intraday source to the final bar per contract, scope to the represented expiry, detect ties/duplicates, enforce 95% key coverage and 99% close tolerance, and compare the underlying value.
- Added global-source endpoint probing to the automatic workflow.
- Phase 2B remains gated pending fresh tester review.
