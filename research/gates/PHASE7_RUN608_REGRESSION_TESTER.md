# Phase 7 Run #608 Regression Harness Failure — Tester Review

**Status: REQUEST CHANGES**

Fresh hosted run #608 (`37716925536`) passed dependency installation and all three canonical data acquisition steps, but the Phase 7 regression harness failed before its assertions.

Failure:
`NameError: name '__file__' is not defined`

The test executes the production module source with `exec(compile(...), ns)` while using a production module that computes ROOT from `__file__`. The synthetic harness did not provide that variable.

## Impact

- Regression assertions did not execute.
- Empirical job was skipped.
- No Phase 7 artifact or metric exists.
- Run #608 is NON-EVIDENCE.

## Required correction

Provide `__file__` in the synthetic execution namespace, or replace the source-execution mechanism with an equivalent deterministic import-safe test approach. Do not weaken the production path.

**Tester → Developer:** Correct the regression harness, log Run #608, and resubmit for tester approval before another hosted execution.