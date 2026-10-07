# Phase 6 Empirical Run Failure — Tester Gate

**Status: REQUEST CHANGES**

## Run
- Workflow run: 37668947725
- Empirical job: 112955675058
- Developer commit under test: 85c1b8db633dc1fb79f3426ab0b065e068efc2aa

## Finding
The Phase 6 empirical job failed before producing a result artifact. The traceback is:

`AttributeError: 'DatetimeIndex' object has no attribute 'iloc'`

at `scripts/run_phase6_novel.py:616`, where the intraday cutoff uses `decision_times.iloc[rows[0]]`.

The runtime object is a pandas `DatetimeIndex`; positional access must use normal integer indexing (for example `decision_times[rows[0]]`) or an explicitly converted Series.

## Impact
No Phase 6 empirical results are evidence from this run. Schema validation and artifact upload were skipped. The failure is deterministic at the intraday path and blocks the Phase 6 empirical gate.

## Required developer action
1. Correct the DatetimeIndex positional access without changing the frozen Phase 6 method definitions.
2. Add/retain a regression test covering intraday cutoff construction with a DatetimeIndex.
3. Re-run the regression suite.
4. Obtain tester approval for the corrected implementation.
5. Execute a fresh full empirical Phase 6 run; do not reuse partial output.

## Tester conclusion
**REQUEST CHANGES. No method is promoted. No empirical metric is accepted.**
