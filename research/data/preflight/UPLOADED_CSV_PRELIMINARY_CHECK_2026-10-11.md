# Uploaded CSV preliminary structural check — 2026-10-11

## Scope and provenance
- User supplied `nifty_repaired_composite_2021-10_to_2026-10.csv.gz` in the conversation workspace.
- Local path was read directly from the uploaded-file mount: `/mnt/data/nifty_repaired_composite_2021-10_to_2026-10.csv.gz`.
- File size: 230,858,600 bytes.
- SHA-256: `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5`, matching the previously pinned export/manifest hash.
- `gzip -t`: PASS (gzip stream/trailer integrity).
- This is a preliminary developer-side structural check, not the tester-approved GitHub Actions gate receipt and not modelling-readiness approval.

## Checks actually completed
- CSV header has 47 columns.
- Full streaming CSV width scan reached EOF: 8,999,865 data rows; 0 rows had a field count other than 47.
- Full streaming row-type/timestamp/key-field-presence scan reached EOF:
  - `OPTION`: 8,490,723 rows.
  - `SPOT`: 509,142 rows.
  - `timestamp_epoch` blank: 0.
  - `underlying` blank: 0.
  - `OPTION` rows missing any of `expiry_code`, `returned_strike`, `option_type`: 0.
  - `SPOT` rows missing `underlying`: 0.
  - `timestamp_epoch` minimum: 1,633,923,960.
  - `timestamp_epoch` maximum: 1,791,540,540.
- Actual schema includes `timestamp_epoch,row_type,underlying,expiry_code,returned_strike,option_type`. It does not include the generic scanner alternatives `instrument_type,symbol,expiry,strike,security_id`; the tester must ensure duplicate-key logic selects a key schema matching the actual header before any duplicate-check result is accepted.

## Incomplete checks / restrictions
- A full SQLite-backed unique-key scan was attempted locally but did not finish within the execution time limit. No duplicate-key count is asserted.
- This report does not validate OHLC semantics, exact spot-option join correctness, session calendars, target definitions, look-ahead/leakage, or strategy profitability.
- This report does not confirm hosted-run cleanup or the published sanitized receipt.
- Model fitting/scoring, holdout access, additional market-data requests, and strategy/P&L remain CLOSED pending independent tester review and a separately approved next gate.

## Requested independent tester checks
1. Independently confirm the uploaded file hash, row/column counts and row-type counts from this report.
2. Review whether the production preflight scanner's duplicate-key schema recognizes the actual column names. If it does not, issue REQUEST CHANGES and ask developer to submit a separately versioned, exact-hash-reviewed correction; do not reinterpret a non-estimable duplicate check as PASS.
3. Decide whether these preliminary checks can be accepted as supplemental evidence only; do not grant modelling or holdout permissions on this report alone.

**Developer → Tester:** Review this report independently, verify the exact hash/count claims, and explicitly assess the scanner/header mismatch and unfinished uniqueness check.
**Tester → Developer:** Return a written PASS/REQUEST CHANGES report on the tester branch; keep all modelling, holdout and strategy/P&L gates closed until the full data-readiness gate is passed.
