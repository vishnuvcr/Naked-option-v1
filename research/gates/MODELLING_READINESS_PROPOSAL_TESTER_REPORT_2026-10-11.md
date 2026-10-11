# Tester report — modelling-readiness and prediction continuation proposal

Date: 2026-10-11
Role: Tester branch review
Developer proposal: `research/gates/MODELLING_READINESS_AND_PREDICTION_CONTINUATION_PROPOSAL_2026-10-11.md`
Developer commit: `fb7d6b107ce601639af4ea8aeacc5b2547eb5834`

## Decision
**PASS WITH SCOPED RESTRICTIONS — proposal design only.**

This is a tester-role review in the same connected assistant session, not an external human or separate model audit. The decision does not authorize data preflight execution, model fitting, model scoring, holdout access, additional data requests, or option strategy/P&L tests.

## Checks
- The plan keeps the 8,999,865-row / 47-column export out of repository history and treats the supplied SHA-256 as an assertion to verify against the actual local file.
- It explicitly retains 19,021 unmatched option rows across 421 timestamps and 24,847 weekend-session review flags; it does not silently approximate joins or fabricate missing data.
- It separates data readiness, prediction, untouched holdout, and later option economics into distinct permissions.
- It proposes chronological walk-forward validation and purging/embargo, and prohibits retroactively calling historical observations an untouched holdout.
- It names baseline-relative paired comparisons, dependence-aware uncertainty, familywise multiplicity correction, calibration metrics, per-class results, and reporting of failed/negative attempts.
- It marks unsupported feature families NOT_ESTIMABLE instead of silently substituting proxies.
- It has a finite stopping rule and distinguishes predictive accuracy from after-cost trading profitability.

## Required corrections / conditions before Phase A execution
1. **Artifact access is unproven in this review.** The prior export was verified in the user's workspace, but this review cannot read the 4.75 GB CSV itself. The next workflow must fail closed unless the exact file exists and its gzip integrity, SHA-256, row count, and schema are reverified.
2. **Define target semantics before fitting.** The Phase B contract must state decision timestamp, next eligible observation, horizon endpoints, close/return definition, flat/threshold rule, label maturity, and handling of session boundaries/overnights. No fitting before that contract is reviewed.
3. **Prevent shared-origin leakage.** Ensure all contracts from a timestamp remain in the same fold; split by decision origin/session, not by option row. Fit transforms and feature selection only inside each training fold.
4. **Predeclare the comparison family.** Freeze all methods × horizons × target definitions and the global fit budget before any evaluation. Include the exact correction procedure and null/bootstrap implementation in executable tests.
5. **Holdout protection.** Verify that no code path can read or score the prospective holdout before configuration freeze, and that a single final evaluation is enforced.
6. **Tester independence limitation.** Repository branch isolation is useful but does not make this same-session review a truly independent person/model. Reports must state that limitation.

## Gate permissions
- Proposal design: PASS WITH SCOPED RESTRICTIONS.
- Phase A local data preflight: NOT AUTHORIZED by this report; submit exact-snapshot implementation and test fixtures for review first.
- Target/split contract: DESIGN ONLY; requires separate exact-snapshot review.
- Model fitting/scoring: CLOSED.
- Untouched holdout: CLOSED.
- New market-data requests: CLOSED.
- Option strategy/P&L: CLOSED.

## Next developer action
Implement Phase A as a bounded, chunked, offline-only preflight with tests for digest mismatch, corrupt gzip, schema drift, row-count mismatch, duplicate keys, timestamp order, invalid OHLC/volume flags, and no plaintext artifact publication. Submit exact commit, workflow blob, test receipt, and sanitized expected-output schema for a fresh tester decision.

**Tester → Developer:** Do not start Phase A execution or fitting from this proposal-only pass; submit the exact preflight implementation and test evidence for review.
**Developer → Tester:** Review the next immutable snapshot and keep model/holdout/strategy permissions closed unless explicitly granted by the new decision.
