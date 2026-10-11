# Offline Dataset Artifact Integrity Audit — 2026-10-11

## Scope

Offline inspection of the already collected GitHub Actions artifact only. No network/data-source requests were made. The ZIP contains encrypted market-data parts; no plaintext prices were decrypted or independently inspected. This audit establishes archive/manifest integrity, not market-data correctness or analysis readiness.

## Artifact identity

- Local artifact: `nifty-spot-recovery.zip`
- SHA-256: `aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216`
- Size: 229,145,190 bytes
- ZIP members: 60
- ZIP CRC/member integrity test: passed (`testzip() = None`)
- Manifest-declared encrypted data parts: 57
- Missing parts: 0
- Encrypted part size/SHA-256 mismatches against manifest: 0
- Sum of manifest monthly part row counts: 8,894,387

## Manifest reconciliation

| Measure | Manifest value | Audit result |
|---|---:|---|
| Option rows | 8,490,723 | Reconciles |
| Spot rows | 403,664 | Reconciles |
| Combined rows | 8,894,387 | Reconciles to monthly-part row-count sum |
| Spot joins matched | 7,591,172 | Recorded metadata |
| Spot joins missing | 899,551 | Recorded metadata |
| Matched + missing | 8,490,723 | Reconciles to option-row total |
| Planned spot gap-fill requests | 47 | Recorded metadata |
| Successful spot gap-fill requests | 41 | Recorded metadata |
| Failed spot gap-fill requests | 6 | Recorded metadata |
| Historical option request grid | `PARTIAL_GRID` | Not complete |
| Spot recovery status | `SPOT_GAPFILL_PARTIAL` | Not complete |
| Observed trading sessions | 1,081 | Recorded metadata |

The six failed gap-fill windows are recorded as `response_row_cap_exceeded` despite HTTP 200. Their existence means the source returned a response but the collector rejected it under its row cap; they are not successful data coverage.

## Request/error metadata

- Manifest summary records 7,481 failed responses/quality events before adding the six failed gap-fill requests; its aggregate `failed_request_or_quality_event_count` is 7,487.
- Across the coverage/error JSON, a scan of list entries found 9,781 error-bearing records. This count is **not** interchangeable with the manifest's failed-event counter: request results and error log entries overlap and have different aggregation semantics.
- Frequent recorded reasons in the scanned error-bearing records include `http_status_400`, `option_parse_error_ValueError`, 61 `unexpected_ValueError` records from an earlier spot collection attempt, and six `response_row_cap_exceeded` gap-fill failures.
- The manifest's `downloaded_bytes` counter is 21,731,367, but it omitted the six rejected response bodies. The prior audit estimated those six bodies at a combined 6,517,187 bytes, so the successful-response counter is not a complete wire-byte total. Do not infer that the aggregate cap was exceeded without additional evidence.

## Verdict

**Archive integrity: PASS. Manifest/part-count reconciliation: PASS. Dataset completeness/readiness: FAIL / NOT ESTABLISHED.**

The archive is intact and all encrypted monthly-part hashes/sizes match the manifest. However, the historical option request grid is partial, six spot recovery windows remain failed, and 899,551 option rows have no matched spot observation. Since the data values remain encrypted in this audit, this does not validate timestamp monotonicity, duplicate prices, OHLC inequalities, actual missingness by feature, or leakage-safe row construction.

## Next permitted step

1. Tester branch to review this exact report and the manifest/coverage metadata.
2. If scoped tester review accepts the metadata reconciliation, determine the allowed modeling universe from rows that already have sufficient observed target/features; record exclusions and missingness before fitting.
3. Keep model fitting/scoring, holdout access, and strategy/P&L testing blocked unless their separate exact-snapshot gates authorize them. Do not launch further collection under the user's “Data collection is over” instruction.

## Role handoff

**Developer → Tester:** Recompute ZIP hash/member integrity, all 57 part hashes/sizes, monthly row sum, join arithmetic, and failed-window status. Report only what encrypted metadata supports.

**Tester → Developer:** Return a scoped artifact-integrity/readiness report on `phase-07-tester`. Do not treat archive integrity as proof of complete coverage or permission to fit models.
