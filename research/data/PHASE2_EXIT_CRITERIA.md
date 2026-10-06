# Phase 2 Exit Gate

Phase 2 passes only when all applicable criteria are green:

1. Canonical NIFTY underlying snapshot acquired and hashed.
2. NIFTY option data acquired for the research window or documented source-limited subset.
3. Option schema reconciled across legacy and UDiFF formats.
4. Contract/expiry/strike/option-type keys are unique.
5. Historical lot-size mapping is effective-dated and reconciled.
6. India VIX snapshot is aligned.
7. FII/FPI/DII data availability rule is established.
8. At least one global-market layer is acquired, hashed, aligned to IST and ruled safe for overnight-only use.
9. A historical/effective-dated NIFTY lot-size field is validated against official data.
10. India VIX snapshot acquisition/availability is validated.
11. FII/FPI/DII snapshot acquisition/availability is validated or conservatively quarantined.
12. US Treasury/global-source URLs are either working or explicitly quarantined with reason.
13. Missing-value/staleness rules are deterministic.
14. Composite-source overlap checks pass.
15. PIT leakage test suite passes.
16. Cached snapshot is reproducible from manifest.
17. No paid source is required before free alternatives are ruled out.
18. Tester independently reproduces the quality checks.
19. README, STATUS, research log and error log are updated.
