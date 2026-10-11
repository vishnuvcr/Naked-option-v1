# One-Use Metadata Scan Adapter Proposal R1

Date: 2026-10-11

**Design only — no cached-file scan is authorized.**

## Purpose

The prospective boundary scanner passed synthetic tests, but the CLI has no real-file path. This proposal defines a narrowly scoped adapter for one metadata-only scan of the existing cached composite, after separate implementation and execution reviews.

## Allowed fields

Application logic may use only row type, timestamp epoch, session date, record offsets/lengths, and raw bytes for streaming integrity hashes. It must not access or calculate with prices, option quotes, features, Greeks, sentiment, labels, or holdout outcomes. No source requests, downloads, fitting, scoring, strategy/P&L or trading.

## Authorization contract

A tester-owned decision must pin the exact developer commit, scanner/test/schema/workflow blobs, dataset hash and bounds, cached calendar/input-manifest hashes, one-use nonce, output allowlist, and exact allowed scope. Missing/stale hashes, mismatched branch head, or a workflow attempt other than 1 must fail closed.

## Durable one-use control

Before opening the dataset, the workflow must check for a consumed marker on `phase-07-developer`. If absent, it writes a sanitized marker containing only the nonce, authorization hash, dataset hash, reviewed commit and run ID. An existing marker, concurrent-write conflict, changed commit or rerun blocks execution. A failure after consumption does not restore the nonce; a fresh tester decision is required.

## Validation gates

1. Implement the adapter and workflow; synthetic CI must not pass a dataset path.
2. Test stale hashes, replay, attempt mismatch, branch-head mismatch, marker race, missing calendar, malformed rows, field allowlist, offsets and streaming suffix hash.
3. Pass hosted synthetic CI.
4. Obtain an exact-hash tester implementation decision.
5. Only then request a separate tester-owned execution decision for one cached-file scan.
6. Review the sanitized boundary result before any target labels or model experiments.

## Failure policy

Any mismatch blocks before file open. Never alter the 70/15/15 split or the 252/250 thresholds to clear a failure. Do not suppress errors or expose raw rows in logs.

## Out of scope

Model fitting/tuning/scoring, holdout value interpretation, source downloads, strategy/P&L and trading.

**Developer → Tester:** Review this design only; no implementation or scan authorization is implied.  
**Tester → Developer:** Approve/request changes on the exact proposal/scope hashes and require a separate execution decision after implementation review.
