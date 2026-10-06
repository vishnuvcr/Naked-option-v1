# Tester Phase 2B Error Log — Re-Review

| Date | Phase | Finding | Severity | Required action |
|---|---|---|---|---|
| 2026-10-07 | 2B | Reconciliation did not enforce acceptance thresholds | Critical | Make the job fail when thresholds are breached |
| 2026-10-07 | 2B | Duplicate keys silently overwritten | Critical | Count and fail duplicates |
| 2026-10-07 | 2B | Weekly HF reference not scoped to its expiry before coverage testing | High | Match official rows to selected HF expiry |
| 2026-10-07 | 2B | Underlying spot not cross-compared | High | Compare spot with an explicit tolerance/coverage rule |
| 2026-10-07 | 2B | Global manifest not probed by CI | Medium | Add global source probe |
| 2026-10-07 | 2B | Missing core prices were skipped rather than thresholded | High | Report and fail on core-price missingness |

New findings must be appended.
