# Tester Phase 3 Empirical Error Log

| Date | Phase | Severity | Finding | Required correction |
|---|---|---|---|---|
| 2026-10-07 | 3 | High | Intraday B8 uses prior-row labels whose H-minute future endpoint may occur after the current decision timestamp | Restrict historical labels by label-end < decision timestamp |
| 2026-10-07 | 3 | Medium | Probability-bin future-return counts are not based on the same evaluation mask as metric n | Apply identical valid-row mask or explicitly separate denominators |
| 2026-10-07 | 3 | Medium | Result-schema validator does not test B8 PIT safety or probability-bin denominator consistency | Add static/schema regression checks |
