# Phase 6 Regression Arithmetic Correction — Tester Approval

**Status: PASS — correction approved for fresh empirical execution**

## Independent review

Tester reviewed detached developer commit `1a956f930b11850fb238ea3352565b36a7337395` against the failed hosted run #578 (`37680279189`) and the tester request-changes gate.

- The only scientific-code change is the regression fixture expectation: 13:15 minus 120 minutes is 11:15.
- The production Phase 6 cutoff implementation is unchanged by this correction.
- The earlier 15-minute cutoff assertion remains mathematically correct: 09:15 + 2 hours = 11:15, minus 15 minutes = 11:00.
- The later global-I03 fixture is now exactly consistent with the declared 120-minute subtraction.
- The accompanying error/status/research/chat/README records correctly classify run #578 as non-evidence and do not introduce any scientific result.
- No frozen Phase 6 method, label, horizon, training boundary, seed, or cost rule was changed.

## Approval scope

This gate approves the regression-fixture correction for **one fresh hosted empirical execution**. It does not approve any Phase 6 metric, model, or strategy. The next hosted run must pass the full regression suite and then receive separate independent artifact-level scientific review.

Run #578 remains non-evidence and must not be reclassified.

**Tester → Developer:** Archive this gate on the developer branch, then advance the developer ref and allow the fresh gated run. If the next regression or empirical execution exposes another defect, stop promotion, log it, and resubmit for tester review.