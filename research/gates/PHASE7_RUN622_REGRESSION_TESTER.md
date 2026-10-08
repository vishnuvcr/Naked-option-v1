# Phase 7 Run #622 Regression Failure — Tester Review

**Status: REQUEST CHANGES**

Fresh hosted Research Protocol Check run #622 (`37717651173`) successfully executed dependency installation and all canonical data acquisition steps.

The regression suite now reached its numerical assertions, but failed on a stale test call:

`TypeError: family_bootstrap() takes 4 positional arguments but 5 were given`

The production function currently has signature `family_bootstrap(y, candidates, baseline, block_len)`, while the regression test still passes an extra `blocks` argument.

## Impact
- Regression failed.
- Empirical job was skipped.
- No Phase 7 artifact or scientific metric exists.
- Run #622 is **NON-EVIDENCE**.

## Required correction
Update the regression call to the current frozen function signature and add a source-level signature assertion so this mismatch cannot recur. Do not change the scientific family-bootstrap definition.

**Tester → Developer:** Correct the stale regression call, log Run #622, and resubmit the hosted regression gate.