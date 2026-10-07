# Phase 5 Family D — Run 6 Tester Follow-up

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer commit: `dd10674f002286374ae179b346f0522c24532e97`
Hosted run: #6 / `37595617781`

## Gate result

**REQUEST CHANGES — INTRADAY TIMESTAMP HANDLING**

## Finding

The Family D regression suite passed. During empirical execution, the intraday walk-forward cutoff failed because a timezone-naive `to_datetime64()` value was compared to timezone-aware decision timestamps inside `np.searchsorted`.

The stack trace identifies `scripts/run_phase5_family_d.py` at the intraday `train_end` calculation. No empirical result artifact was produced.

## Required corrective evidence

The developer has now added a nanosecond-based timezone-safe cutoff helper and a regression test covering both timezone-naive and Asia/Kolkata timezone-aware timestamps. A fresh hosted run must demonstrate that the empirical suite reaches schema validation and artifact creation.

No Family D result is accepted from run #6.

## Tester instruction to developer

Submit the timezone-safe correction on the developer branch, rerun the complete hosted Family D workflow, and preserve run #6 as rejected evidence.

## Developer instruction to tester

Independently inspect the next run's artifact, including timestamp handling, chronological purge, D13-D15 session-local behavior, schema completeness, numerical stability, and whether any method is silently reported as executed with zero valid observations.
