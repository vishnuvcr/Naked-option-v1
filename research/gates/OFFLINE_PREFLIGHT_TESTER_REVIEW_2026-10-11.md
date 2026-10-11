# Tester review — offline preflight

Date: 2026-10-11
Developer commit reviewed: c866ba5f5e125f693c5353f5c9f70d0d94514078

## Decision
REQUEST CHANGES. This is a tester-role review in the same connected assistant session, not an external independent audit. No successful CI receipt for the latest snapshot was verified here, and the actual CSV is not mounted in this execution environment.

## Findings
1. No real-file audit was run; metadata does not prove the actual file passes today.
2. Structural scanner covers SHA-256, full gzip read, schema/row count, blank counts and optional recognized composite-key duplicates.
3. Timestamp extrema are lexical only. Timestamp parsing/order, session calendars, exact spot joins, OHLC invariants and leakage checks remain unimplemented.
4. Add tests for corrupt/truncated gzip, malformed row widths, duplicate recognized composite keys, absent key fields, cleanup after failure, and nested report directory creation.
5. Confirm the synthetic Actions workflow passes on the exact final commit before resubmission.
6. Review third-party action pinning against repository security policy.

## Permissions
Proposal: design only. Real-file preflight: NOT AUTHORIZED. Fitting/scoring: CLOSED. Holdout: CLOSED. New source requests: CLOSED. Strategy/P&L: CLOSED.

Tester → Developer: Correct these issues, attach a successful synthetic CI receipt and resubmit exact hashes.
Developer → Tester: Review the corrected exact snapshot before any real-file preflight execution.
