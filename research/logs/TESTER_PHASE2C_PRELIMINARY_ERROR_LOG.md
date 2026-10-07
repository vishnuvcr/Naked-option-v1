# Tester Phase 2C Preliminary Error Log

| Date | Phase | Finding | Severity | Disposition |
|---|---|---|---|---|
| 2026-10-07 | 2C | Year acquisition uses a percentage coverage rule without automatic NSE holiday-calendar classification | Medium | Keep data gate open; require unresolved-date classification in final review |
| 2026-10-07 | 2C | Historical lot-size coverage is incomplete for legacy-era rows | Medium | Keep unresolved regimes quarantined until independently verified |
| 2026-10-07 | 2C | Developer run #14 failed because legacy option expiries were parsed as ISO only, non-option NIFTY rows were counted as invalid options, and VIX date formats were too narrowly parsed | Independent tester review of correction commit a3355a28da573adc096c5f8ac1920f73ce5b5525 | Correction is logically appropriate; final data gate remains open until hosted artifact reproduction |
