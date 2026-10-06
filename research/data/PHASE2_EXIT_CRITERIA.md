# Phase 2 Exit Gate

Phase 2 passes only when all applicable criteria are green:

1. Canonical NIFTY underlying snapshot acquired and hashed.
2. NIFTY option data acquired for the research window or documented source-limited subset.
3. Option schema reconciled across legacy and UDiFF formats.
4. Contract/expiry/strike/option-type keys are unique.
5. Historical lot-size mapping is effective-dated and reconciled.
6. India VIX snapshot is aligned.
7. FII/FPI/DII data availability rule is established.
8. At least one global-market layer is aligned to IST without look-ahead.
9. Missing-value/staleness rules are deterministic.
10. Composite-source overlap checks pass.
11. PIT leakage test suite passes.
12. Cached snapshot is reproducible from manifest.
13. No paid source is required before free alternatives are ruled out.
14. Tester independently reproduces the quality checks.
15. README, STATUS, research log and error log are updated.
