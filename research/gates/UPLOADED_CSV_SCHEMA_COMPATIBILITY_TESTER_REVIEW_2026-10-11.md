# Independent tester review — uploaded CSV preliminary check

Date: 2026-10-11
Developer preliminary report: [UPLOADED_CSV_PRELIMINARY_CHECK_2026-10-11.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/data/preflight/UPLOADED_CSV_PRELIMINARY_CHECK_2026-10-11.md)
Gate: `REAL_FILE_PREFLIGHT_SCHEMA_COMPATIBILITY`

## Decision
**REQUEST CHANGES — do not accept the data-readiness gate.**

## Independently reviewed facts
- The developer report records SHA-256 `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5`, 8,999,865 rows, 47 columns, 8,490,723 OPTION rows and 509,142 SPOT rows, and zero width mismatches. The assistant-side mounted file checksum and full streaming width scan corroborate these counts.
- The actual schema contains `timestamp_epoch,row_type,underlying,expiry_code,returned_strike,option_type`; it does not contain the field names in the current generic `KEY_GROUPS` definitions (`instrument_type,symbol,expiry,strike,security_id`).
- The production scanner explicitly returns `PREFLIGHT_REVIEW_DUPLICATE_CHECK_NOT_ESTIMABLE` when no recognized composite key group exists. That is appropriately fail-closed, but it does not establish duplicate-key uniqueness for this actual schema.
- The local SQLite-backed uniqueness scan timed out; therefore there is no independently verified duplicate count. No uniqueness PASS is accepted.
- These checks do not establish OHLC correctness, exact spot-option joins, session/calendar correctness, target validity, leakage safety, or strategy profitability.

## Required developer corrections
1. Add a schema-specific key group for OPTION rows using the actual canonical fields: `timestamp_epoch,row_type,underlying,expiry_code,returned_strike,option_type`.
2. Add a separate SPOT key group using `timestamp_epoch,row_type,underlying`; ensure the selection logic handles OPTION and SPOT rows without collisions or treating blank option identifiers as complete keys.
3. Add regression fixtures for both actual row types, duplicate option key, duplicate spot key, and valid mixed option/spot data; assert exact duplicate and incomplete-key counts.
4. Re-run the scanner on the uploaded exact SHA with sufficient time and bounded disk-backed memory. Publish only sanitized metadata and verify temporary database cleanup.
5. Because the existing authorization pins exact file hashes, any change to the reviewed scanner/workflow invalidates that authorization. Submit the corrected exact snapshot for a new tester decision before running the real-file workflow.
6. Update the developer status, error log, and chat log; do not alter tester-owned files from the developer role.

## Restrictions
- No model fitting/scoring, holdout access, additional source requests, or strategy/P&L testing.
- This report is a data-structure gate decision only, not a judgement about whether a profitable strategy exists.

**Tester → Developer:** Correct schema-specific duplicate-key handling and submit the exact changed files for a fresh independent review; do not reuse the old exact-hash authorization.
**Developer → Tester:** Review the corrected snapshot and its regression coverage before any new real-file audit is authorized.
