# Error Log — Phase 1 Literature Supplement

This branch-specific record documents defects found while preparing the 2026-10-10 uploaded-PDF literature supplement. Historical errors from later phases remain in the canonical project error log on phase-07-developer.

## 2026-10-10 — Pre-existing literature registry field displacement (L003)

- **Category:** bibliography/schema semantics.
- **Component:** research/literature/LITERATURE_REGISTRY.csv, record L003.
- **Symptom:** The row had 11 fields, so the original row-length validator did not flag it, but the DOI appeared in the hypotheses field and method/hypothesis data appeared in the URL/status columns.
- **Root cause:** The registry validator verifies CSV parseability, field count, source ID uniqueness and a minimum record count; it does not validate field semantics such as URL and verification-status positions.
- **Impact:** A reader or downstream consumer could misinterpret the source reference and method mapping for the White/Sullivan/Timmermann literature entry.
- **Correction:** Restored the DOI to url_or_doi, verified to verification_status, B01-B13|J01-J07 to related_methods and H01|H13 to related_hypotheses. The literature supplement adds L037-L051 with fields aligned to the documented 11-column header.
- **Prevention:** Tester must validate both CSV row count and field semantics, including a URL pattern check and allowed verification-status check. Consider strengthening scripts/validate_literature_registry.py after independent review.
- **Disposition:** Corrected on phase-01-developer before independent tester review. Do not treat the literature supplement as an empirical result.
