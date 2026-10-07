# Phase 6 Regression Failure — Tester Review

**Status: REQUEST CHANGES**

## Independent finding

Fresh hosted Research Protocol Check run #578 (`37680279189`) on the tester-approved Phase 6 cutoff correction passed repository validation, data acquisition and source checks, but the mandatory Phase 6 regression suite failed at `scripts/test_phase6_novel.py:64`.

The failing assertion was:

`global_i03_cutoff = decision_times[4] - pd.Timedelta(minutes=120)`

followed by an expected timestamp of `2026-01-01 11:00`.

With `decision_times = pd.date_range("2026-01-01 09:15", periods=5, freq="h")`, `decision_times[4]` is 13:15, so subtracting 120 minutes yields **11:15**, not 11:00.

## Consequence

Run #578 is **NON-EVIDENCE**. The empirical job was skipped because the regression gate failed. No scientific metric or artifact was produced or accepted.

## Required developer correction

1. Correct the regression expectation to the mathematically correct 11:15 result (or use an equivalent invariant assertion).
2. Recheck all timestamp arithmetic in the new cutoff regression fixture for exact consistency with the intended 15/120-minute horizons.
3. Do not alter the production Phase 6 method definitions, labels, horizons, training rules, or cost rules.
4. Submit the corrected regression back for independent tester approval before advancing the developer ref for another hosted execution.

**Tester disposition:** REQUEST CHANGES — fresh empirical execution remains blocked until the regression correction passes independent review.