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


## 2026-10-10 — User-supplied PDF literature extension

- Reviewed 15 unique attached PDFs, counting re-uploaded copies of the same named documents once.
- Added structured source-by-source appraisal at research/literature/UPLOADED_PDF_REVIEW_2026-10-10.md and registry entries L037–L051.
- Checked publication/DOI pages where a stable record was available. Where source code, underlying data, exact test-split logic or a comparable metric definition was not present, logged that as a limitation rather than filling the gap.
- Key methodological lead: Sain and Singh (2026) uses a Naive Persistence comparator and multiple 5/10/20-year windows; its reported linear-model stability motivates stronger naive-baseline and rolling-origin checks, but only its own setting is covered by its claim.
- Other papers provide candidate model/feature families (ANN/RNN/LSTM/GRU/CNN/TCN, time-aligned sentiment, FII/DII, India VIX, PCR and USD/INR) but do not alter project results.
- The 2025 moving-average study reports t = -1.271, p = 0.1079 for its crossover comparison, not statistically significant at 5%.
- Options-strategy papers are marked as adjacent/contextual only. The active extension remains prediction-only; no Phase 8 work was opened.
- The research plan and frozen Phase 7 available-data specification were not changed. The literature update should receive an independent tester check for claims, bibliography and registry schema.
- No new code error or empirical metric was created by this review.
