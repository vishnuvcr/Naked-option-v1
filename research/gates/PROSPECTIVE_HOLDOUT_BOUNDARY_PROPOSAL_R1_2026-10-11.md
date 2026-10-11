# Prospective Holdout Boundary Proposal R1 — 2026-10-11

## Purpose

The Phase 7 PPR-4 metadata audit found no machine-readable holdout boundary. The approved MR-0–MR-5 feasibility runner therefore remains unable to enter empirical mode. This proposal defines a separate, bounded gate to create a prospective chronological split from the already-cached composite without reading prices, option quotes, features, labels, or holdout outcomes.

**This document is design only. It does not authorize execution on the composite.**

## Research question

Can a deterministic metadata-only scan of the pinned composite establish reproducible train, validation, and sealed-holdout byte boundaries while proving chronological ordering and preventing holdout-value access?

## Objectives

1. Pin the existing dataset identity, decoded-content hash, expected row/column counts, and input manifest.
2. Determine row offsets and session ordering using only the minimum metadata fields: row type, timestamp epoch, and session date.
3. Create a prospective chronological split before target labels or model outcomes are computed.
4. Enforce label-endpoint purge rules for every candidate horizon: training labels must end within train; validation labels must end within validation; no label may cross into holdout.
5. Produce a compact manifest with byte offsets, session boundaries, row counts, row-type counts, chronology checks, and hashes. Do not include price, quote, feature, or label values.
6. Require exact-hash tester review of the manifest and scanner before any downstream gate.

## Proposed split rule

- Split on unique ordered NSE sessions, not random rows.
- Candidate chronological allocation: earliest 70% of sessions for training, next 15% for validation, final 15% for sealed holdout, using deterministic integer rounding documented in code.
- Enforce at least 252 eligible training origins and at least 250 common validation origins after endpoint purging; if these are not met, report `NOT_ESTIMABLE` and do not move boundaries to improve results.
- Boundaries must be byte offsets immediately after complete CSV records. The manifest must hash the exact prefix and suffix byte ranges, but must never contain the underlying row text.
- The holdout boundary is locked before price/option values, targets, or model results are read. No model-selection, tuning, or strategy/P&L use of holdout data is permitted.

## Methodology

1. **Preflight:** verify dataset hash and dimensions against the existing pinned receipt. No row values are processed in this step.
2. **Metadata scan:** stream the file as CSV records and use only the configured indices for row type, timestamp, and session date. Never access, print, log, or retain price/quote/feature columns. Keep only ordered session IDs, record offsets, row counts, and chronology diagnostics.
3. **Boundary selection:** compute 70/15/15 session indices once from the ordered unique sessions. Determine byte offsets from record boundaries and record the rule/version.
4. **Purge proof:** calculate horizon endpoint session indices from the calendar/session list, not prices. Prove that all training and validation origin/endpoint pairs remain inside their split; exclude crossing origins.
5. **Integrity:** record source hash, manifest hash, scanner code hash, row counts, byte offsets, session boundaries, and hash of the holdout byte range. Do not expose raw row contents.
6. **Cleanup:** discard temporary row buffers and any transient copies; emit only the sanitized boundary manifest.
7. **Tester gate:** independently recompute the session allocation, byte offsets, counts, hashes, purge checks, and output allowlist against the exact developer snapshot.

## Statistical analysis

This gate is not a prediction experiment. No accuracy, F1, AUC, return, win rate, or P&L metric will be computed. The only quantitative checks are counts, ratios, date order, byte-offset integrity, hash integrity, and split-specific eligible-origin counts.

## Pass/fail criteria

**PASS_WITH_SCOPED_RESTRICTIONS** only if:
- input identity and row structure match the pinned receipt;
- session dates are parseable and chronologically ordered;
- all byte boundaries land on complete record boundaries;
- computed session allocations follow the frozen rule exactly;
- no prohibited value/label field is read by application logic or emitted in outputs;
- endpoint purge rules pass;
- manifest counts and hashes reconcile; and
- the independent tester approves the exact hashes.

Otherwise the result is `REQUEST_CHANGES` or `BLOCKED`. No fallback to random splits, inferred dates, or altered split ratios is permitted.

## Explicitly out of scope

- Reading or summarizing holdout prices, option quotes, feature values, or labels.
- Model fitting, tuning, scoring, forecasting, strategy testing, transaction-cost analysis, P&L, or trading.
- New downloads, source requests, use of paid data, or secrets.
- Treating the split manifest as authorization for any later empirical scope.

## Deliverables

- Metadata-only scanner and synthetic regression tests.
- Synthetic-only GitHub Actions workflow with manual dispatch.
- Exact-hash tester review and decision.
- If approved, a separate execution-authorization record before running the scanner on the cached composite.
- Sanitized boundary manifest and audit log, only after that separate authorization.

## Role handoff

**Developer → Tester:** Review this proposal and scope only; do not authorize data execution.  
**Tester → Developer:** Approve or request changes on exact proposal/scope hashes; no later scope is implied by a design pass.
