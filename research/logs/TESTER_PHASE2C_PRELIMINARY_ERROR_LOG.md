# Tester Phase 2C Preliminary Error Log

| Date | Phase | Finding | Severity | Disposition |
|---|---|---|---|---|
| 2026-10-07 | 2C | Year acquisition uses a percentage coverage rule without automatic NSE holiday-calendar classification | Medium | Keep data gate open; require unresolved-date classification in final review |
| 2026-10-07 | 2C | Historical lot-size coverage is incomplete for legacy-era rows | Medium | Keep unresolved regimes quarantined until independently verified |
| 2026-10-07 | 2C | Developer run #14 failed because legacy option expiries were parsed as ISO only, non-option NIFTY rows were counted as invalid options, and VIX date formats were too narrowly parsed | Independent tester review of correction commit a3355a28da573adc096c5f8ac1920f73ce5b5525 | Correction is logically appropriate; final data gate remains open until hosted artifact reproduction |

| 2026-10-07 | 2C | Run #17 failed because global-source acquisition assumed any HTTP response contained usable dated observations | The response was schema-valid enough to pass length checks but contained no usable date rows for at least one source, causing min() on an empty list | Tester accepts the developer fix that uses the previously validated Stooq endpoint, filters locally to the frozen window, and explicitly fails on zero observations | Hosted execution pending |

| 2026-10-07 | 2C | Static validator retained a nonexistent completeness-script marker and failed run #26 after all data jobs passed | Governance contract lagged behind the active Phase 2C workflow | Developer removed the stale marker and kept the active Phase 2C marker suite intact | Hosted rerun pending |
| 2026-10-07 | 2C | Seven legacy Tradetron strategy inputs contain short legs/spreads and cannot be final naked-long strategies | User-supplied historical templates violate the primary execution constraint by design | Tester approves component-mining/ablation treatment only; no historical performance is transferred to final candidates | No gate impact |
