# Independent tester review — R4 report rejected pending canonical-key correction

Date: 2026-10-11
Run: [38146429502](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38146429502)
Sanitized receipt: `research/data/preflight/REAL_FILE_PREFLIGHT_RECEIPT_RUN_38146429502.json` on `phase-07-developer`, blob `2798ab1988ef35d148b1903323f94c030cb60b4c`.

## Decision
**REQUEST CHANGES — do not accept the R4 duplicate-key result and do not open modelling.**

## Findings independently checked
- Data integrity: decoded CSV SHA-256 matched the pinned value `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`; gzip CRC/integrity passed; the compressed-container SHA mismatch is expected to be diagnostic when the content SHA matches.
- Structural totals: 8,999,865 rows, 47 columns, 0 row-width errors, 0 timestamp parse errors; row types reconcile exactly to 8,490,723 OPTION + 509,142 SPOT. Report says 0 incomplete composite-key rows.
- Cleanup: the workflow final cleanup step passed and confirmed no plaintext CSV or SQLite temporary files remained.
- **Duplicate-key logic flaw:** the current preflight scanner keys OPTION rows on `timestamp_epoch,row_type,underlying,expiry_code,returned_strike,option_type`, but the repository’s established canonical row identity is defined in `scripts/run_nifty_1m_composite_dataset.py::_row_key`, `scripts/audit_nifty_1m_composite_values.py::ROW_KEY_FIELDS`, and `scripts/validate_repaired_nifty_1m_composite.py`: `(timestamp_epoch,row_type,source_request_id,expiry_flag,expiry_code,requested_relative_strike,option_type)`. Omitting request ID/expiry flag/requested-relative-strike and substituting returned strike changes the identity and can count separate valid requests as duplicates. The R4 result `4,148,431` is therefore **not accepted as a true duplicate count** until the scanner uses the established key.
- Data coverage concern: the report shows `expiry_date` and `time_to_expiry_years` blank for all 8,999,865 rows and Greeks/rate/dividend fields blank for all rows. These omissions need independent interpretation/repair before model design. This structural scan does not establish that those fields should be populated for every record; however the current dataset is not cleared for modelling until option expiry/target-dependent-field availability is understood.

## Developer requirements
1. Replace the OPTION key with the project’s canonical 7-field identity above; do not invent a substitute key.
2. Keep SPOT epoch uniqueness as a separate check (the existing validation script counts duplicated SPOT timestamps separately).
3. Add synthetic regression tests: same contract returned by different request IDs/requested-relative-strike must not collide; true repeated OPTION identity must count; repeated SPOT epoch must count; incomplete OPTION identity must be not-estimable/flagged.
4. Re-run hosted synthetic CI. This request-changes decision invalidates R4 as a data-readiness result. The R4 one-use request is spent; a new R5 exact-hash tester decision and one-use request are required after code/test review.
5. After R5, inspect the duplicate report and option expiry feature coverage, then issue a separate data-readiness decision. No model/holdout/strategy/P&L work is authorized before that decision.

**Tester → Developer:** Correct key identity to the canonical repo key, add the listed edge-case fixtures, and submit a new snapshot for independent review.
**Developer → Tester:** Do not reuse the R4 count or authorization; review the corrected key schema and hosted CI before R5 approval.
