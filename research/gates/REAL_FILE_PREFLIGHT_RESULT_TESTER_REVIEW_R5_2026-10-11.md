# Tester Review — R5 Canonical-Key Structural Audit Result

Date: 2026-10-11 UTC  
Gate: `REAL_FILE_PREFLIGHT_RESULT_AUDIT`  
Developer run snapshot: `534f3cd5a4329b5e45fa38a1b507ebce6bcf027c`  
Workflow: [38147761301](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38147761301) — success  
R5 implementation decision: [R5 canonical-key review](REAL_FILE_PREFLIGHT_CANONICAL_KEY_TESTER_REVIEW_R5_2026-10-11.md) and [machine-readable authorization](REAL_FILE_PREFLIGHT_CONTENT_HASH_TESTER_DECISION_R5_2026-10-11.json).

## Decision

**PASS WITH SCOPED RESTRICTIONS — exact-lineage structural preflight result only.**

The result supersedes R4 **only for duplicate-key interpretation** and proves the R5 scanner completed on the pinned content. It does not establish full market-semantic validity, prediction-target correctness, point-in-time leakage safety or model readiness. No prediction fitting/scoring, holdout access, new source-data requests, or option strategy/P&L work is authorized by this result.

## Exact-snapshot review

- R5 approval was accepted by the workflow with `authorized: true` and `EXACT_APPROVAL_MATCHED`.
- All **17/17** file blobs in the tester's R5 authorization match the reviewed hashes at developer snapshot `534f3cd5a4329b5e45fa38a1b507ebce6bcf027c`; zero mismatches.
- The workflow confirmed the exact repaired source run/artifact, parent lineage and all **61 encrypted parts** before decryption/merge.
- Synthetic authorization/regression job and real-file audit job both concluded **success**.
- Sanitized report artifact: [11705154936](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38147761301/artifacts/11705154936), name `phase07-offline-preflight-metadata-38147761301`, 1,639-byte ZIP. Downloaded ZIP SHA-256 `ec4f7b99c37bc7a4c897860f6b176ceb215e67c2b18e542644470e21c62ac1d7`, matching the Actions artifact digest.
- Job log explicitly records `PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS`, decoded-content SHA match, report upload and `PASS: plaintext CSV and temporary SQLite files removed.`

## Recomputed structural reconciliation

| Check | R5 result | Tester interpretation |
|---|---:|---|
| Decoded CSV SHA-256 | `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204` | Exact pinned content match |
| Gzip CRC / integrity | PASS | Full compressed stream read validated |
| Rows / columns | 8,999,865 / 47 | Matches pinned expectation |
| OPTION rows | 8,490,723 | Canonical OPTION group |
| SPOT rows | 509,142 | Separate SPOT epoch group |
| OPTION + SPOT | 8,999,865 | Exact reconciliation |
| Row-width errors | 0 | Structural check passes |
| Timestamp parse errors | 0 | Structural check passes |
| Incomplete composite keys | 0 | All records assigned to a complete applicable key |
| Duplicate key rows | 0 | Canonical OPTION and SPOT key groups passed |
| Cleanup | PASS | Plaintext CSV and SQLite temporary files removed |

The reported key groups are the official seven-field OPTION identity `timestamp_epoch,row_type,source_request_id,expiry_flag,expiry_code,requested_relative_strike,option_type` and separate SPOT identity `timestamp_epoch`. This matches the production collector's `_row_key`, audit's `ROW_KEY_FIELDS`, and repair validator's key. The 4,148,431 count from R4 is **rejected and must not be repeated**.

The compressed-container digest did not equal the original expected gzip-container digest; the decoded CSV SHA matched exactly and gzip integrity passed. Under the reviewed protocol, container hash is diagnostic because recompression metadata may change. This is not a decoded-content mismatch and no hash bypass occurred.

Timestamp epoch bounds in the report: 1,633,923,960 to 1,791,540,540. The scan did not test official-session membership, target labels, OHLC semantics, joins or leakage.

## Coverage findings that remain open

The report has 8,999,865 blanks in each of `expiry_date`, `expiry_mapping_source`, `time_to_expiry_years`, `greek_assumption`, `delta`, `gamma`, `theta_per_day`, `vega_per_1pct_iv`, `rho_per_1pct_rate`, `risk_free_rate_decimal`, `risk_free_rate_source`, `dividend_yield_decimal`, and `dividend_yield_source`. These fields are **not available in this snapshot** and cannot be used as features or used to claim Greeks/pricing support.

The previously accepted derived-repair audit remains restricted: 19,021 OPTION rows are unmatched across 421 timestamps, 24,847 rows retain `REPAIR_WEEKEND_SESSION_REVIEW_REQUIRED`, and masked values include 382 joined OPTION rows affected by invalid source-spot OHLC, 12 standalone SPOT OHLC rows, 309 SPOT volume values and 11 OPTION volume values. Those counts come from the separately reviewed repair audit; this structural scanner did not re-establish their semantics.

Other reported blank counts include 19,415 values each for NIFTY open/high/low/close and 19,330 for NIFTY volume. Before feature/target construction, the readiness review must reconcile these with unmatched-join coverage, masked OHLC, and the exact eligible row set rather than assuming missingness is random.

## Next gate and permissions

A **separate exact-snapshot modeling-readiness proposal and tester decision** are required before any fitting. It must explicitly define:
1. Eligible SPOT rows, exchange-session/weekend exclusions and target-label construction.
2. Treatment of unmatched OPTION rows and missing/masked OHLCV, with no interpolation, forward-fill of labels, or nearest-time joins.
3. Feature-family eligibility for absent expiry-date/TTE/Greeks/rate/dividend fields.
4. Chronological train/validation/test splits and leakage checks, including label overlap and session gaps.
5. Required deterministic semantic tests and sanitized coverage tables.
6. The relationship to the paper-replication protocol: the target contract is still `PROPOSED_NOT_AUTHORIZED` and the paper-replication amendment still prohibits empirical execution until its own gates pass.

Permissions after this decision: structural scan **PASS WITH SCOPED RESTRICTIONS**; data/model readiness **PENDING**; fitting/scoring **CLOSED**; holdout **CLOSED**; new source requests **CLOSED**; strategy/P&L **CLOSED**.

## Reviewer independence note

This review was performed in the repository's tester-role branch using exact file-blob comparisons and recomputation of report totals. It is still the same connected assistant session, not a separate human or external-model review; the repository must not represent it as a human audit.

**Tester → Developer:** Record this scoped R5 result in README/status/logs and submit the readiness proposal, without changing any R5-reviewed runtime code.

**Developer → Tester:** Review the exact readiness-proposal hashes and its deterministic tests; do not authorize modeling from the structural report alone.
