# Tester review — corrected offline preflight snapshot

Date: 2026-10-11
Developer snapshot reviewed by source inspection: scanner commit `6f11cc93f49e407c957ab843ea60311c41dba01f`, test commit `f6284c458f408728a00f60673948d0fc35f5a417`.

## Decision
REQUEST CHANGES — code inspection only. No successful CI receipt for the exact final snapshot was verified, and the actual 4.75 GB CSV is not mounted in the tester execution environment. This is not an independent external review; developer and tester roles run in the same connected assistant session.

## Checks
- Scanner uses SHA-256 before parsing, consumes the gzip stream, checks duplicate headers/expected width/row count, counts null-like values, and uses SQLite for recognized composite-key duplicate detection.
- SQLite cleanup is now in a `finally` block, including error paths.
- Timestamp extrema are parsed numerically for `timestamp_epoch` and through ISO parsing for other recognized timestamp names; nonblank parse failures are counted. This is not a trading-session/calendar validation.
- Missing recognized key schemas are reported as NOT_ESTIMABLE. Incomplete composite keys are excluded rather than falsely claimed unique.
- Duplicate composite keys now set `PREFLIGHT_FAIL_DUPLICATE_KEYS` and the CLI exits nonzero. A regression assertion was added.
- Synthetic tests cover gzip corruption/truncation, row width, duplicate headers, wrong column count, row count, digest mismatch, duplicate/incomplete/absent keys, timestamp parse errors, nested report paths and SQLite cleanup.

## Remaining blockers
1. Verify the workflow ran successfully on exact developer snapshot `f6284c458f408728a00f60673948d0fc35f5a417`. The available connector query did not return a verifiable run receipt; do not infer pass from the commit.
2. Confirm action pinning policy. The attempted workflow-file edit was blocked and no action-pin change was committed.
3. Execute the real-file audit only after an authorized, exact-snapshot tester pass and when the CSV is actually available to the runner. Do not commit or upload plaintext data.
4. A structural scan is not modelling readiness: exact join coverage, session semantics, OHLC semantics, target timing and leakage checks remain a separate gate.

## Permissions
Proposal: design only. Synthetic CI: not verified. Real-file preflight: NOT AUTHORIZED. Fitting/scoring: CLOSED. Holdout: CLOSED. New source requests: CLOSED. Strategy/P&L: CLOSED.

Tester → Developer: Provide a successful synthetic CI receipt tied to the final code/test/workflow snapshot; address the action-pinning policy through the approved repository mechanism.
Developer → Tester: Keep real-file preflight and every downstream permission closed until the exact snapshot and CI evidence pass review.
