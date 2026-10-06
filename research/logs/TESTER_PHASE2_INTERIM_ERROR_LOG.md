# Tester Phase 2 Interim Error Log

| Date | Phase | Finding | Severity | Action |
|---|---|---|---|---|
| 2026-10-07 | 2 | Primary derived source passes practical corroboration but not strict 0.25% equality | Medium | Keep canonical NSE data primary; retain strict metric in manuscript |
| 2026-10-07 | 2 | S31 ATM files lack explicit expiry field and are not comparable without contract semantics | High | Quarantine as validation evidence |
| 2026-10-07 | 2 | US Treasury source URL returned 404 | Medium | Correct official endpoint before data use |
| 2026-10-07 | 2 | Global sources were probed but not historically acquired/aligned | Medium | Add real cached global reference |
| 2026-10-07 | 2 | India VIX historical snapshot not yet demonstrated in Phase 2 | High | Add point-in-time historical snapshot test |
| 2026-10-07 | 2 | Official lot-size mapping not yet demonstrated by executable validator | High | Add effective-dated lot-size validation |
