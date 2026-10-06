# Tester Phase 2 Final Error Log

| Date | Phase | Finding | Status/Disposition |
|---|---|---|---|
| 2026-10-07 | 2C | Stooq returned a truncated S&P 500 CSV in hosted CI | Fixed by switching active acquisition to Yahoo Finance chart endpoint; Stooq retained as fallback |
| 2026-10-07 | 2C | Global manifest temporarily mismatched active provider names and acquisition provider | Fixed; S25-S28 now identify Yahoo Finance and S36-S39 identify Stooq fallback |
| 2026-10-07 | 2C | India VIX current endpoint exposes no publication timestamp field in snapshot | Quarantined for same-day historical PIT use; next phase must use historical/timestamped data or exclude |
| 2026-10-07 | 2C | FII/DII current endpoint does not provide historical publication timestamp | Conservatively treated as next-session information |
| 2026-10-07 | 2C | S31 ATM files lack sufficient contract/expiry semantics for comparable reconciliation | Quarantined; no predictive use |
| 2026-10-07 | 2C | Successful final hosted run confirms Phase 2 technical gate | Phase 2 PASS WITH SCOPED RESTRICTIONS |
