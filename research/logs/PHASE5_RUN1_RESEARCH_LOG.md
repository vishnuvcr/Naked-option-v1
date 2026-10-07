# Phase 5 Family D — Research Log Addendum

## 2026-10-07 — Run 1 rejected before empirical execution
Hosted Family D run #1 reached data acquisition successfully but failed at the mandatory regression suite. No Family D empirical result is accepted.

## 2026-10-07 — Independent tester request changes
Tester branch `phase-05-tester` issued `research/gates/PHASE5_RUN1_TESTER.md` with REQUEST CHANGES. The material findings were incomplete regression coverage, generic probability assertion diagnostics, and non-conforming D13-D15 sequence implementations.

## 2026-10-07 — Developer correction set
The developer corrected the sequence representations, added session-local grouping, added training-only calibrated stacking for D07, enforced chronological intraday training cutoffs using decision timestamps, and expanded the regression suite.

## Current state
Corrected hosted run is in progress on developer commit `f80b08d9a4d9f244e3e9f1c8563d6cebb5d3c94b`. Research remains in Phase 5 and no empirical Family D result is accepted yet.
