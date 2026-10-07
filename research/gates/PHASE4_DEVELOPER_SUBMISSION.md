# Phase 4 Developer Submission — Family B Classical

## Scope

Family B methods B01-B13 are frozen in `research/phase4/CLASSICAL_PROTOCOL.md`.

## Gate requirements

- fixed formulas and thresholds;
- no result-driven parameter optimization;
- daily and intraday testing where applicable;
- explicit BLOCKED_DATA/NOT_APPLICABLE dispositions;
- result denominators and confusion counts reconcile;
- independent tester re-review before another family starts.

## Current status

The Family B workflow and schema gate are implemented. Empirical results are pending the hosted run and tester reproduction.

## Developer instruction to tester

Independently reconstruct the Family B B01-B13 metrics from the immutable workflow artifact. Check formulas, point-in-time timing, opening-range and prior-session pivot constructions, denominator reconciliation, and any claims of predictive advantage. Issue PASS/REQUEST CHANGES before Family C starts.
