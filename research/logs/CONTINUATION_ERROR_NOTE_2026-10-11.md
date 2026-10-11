# Continuation issue note — 2026-10-11

1. A lookup for a presumed modelling-readiness proposal path returned 404 because that exact file did not exist. No repository data was changed by the failed read. A new explicitly named proposal was created instead.
2. The verified 4.75 GB plaintext CSV is not present in the current execution container's mounted files. Therefore this session cannot recompute the digest or run row-level checks against it. Repository export metadata is not a substitute for actual local-file validation.
3. No scientific result is inferred from the missing local file. Model fitting/scoring, holdout access, new market-data requests and strategy/P&L remain closed until their separate gates pass.

This note records actionable limitations, not a claim that the dataset itself is corrupt.
