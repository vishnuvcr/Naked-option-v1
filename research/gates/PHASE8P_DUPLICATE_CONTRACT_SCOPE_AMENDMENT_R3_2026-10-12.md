# Phase 8P — Repeated Economic Contract-Time Rows Amendment R3
Date: 2026-10-12
Applies to: approved scope R3, exact code snapshot a5a38e3592234aea9052e697416c8154c6f8e8f8
Status: **CORRECTED PROPOSAL SUBMITTED FOR INDEPENDENT TESTER SCOPE REVIEW — NO NEW DATA RUN OR MODEL FIT AUTHORIZED**

## Why this amendment is required
The schema-only preflight against the fixed, checksum-verified artifacts terminated with the aggregate-only symbolic gate code `DUPLICATE_OPTION_CONTRACT_TIMESTAMP_ACROSS_PARTS`. The two non-accepting attempts were developer runs [#38203577299](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38203577299) and [#38203641510](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38203641510). They did not produce a valid schema/coverage table, and no model was fitted.

The earlier source-composite audit tested a different source-record uniqueness key:
`(timestamp_epoch, row_type, source_request_id, expiry_flag, expiry_code, requested_relative_strike, option_type)`; its repair report had `duplicate_composite_keys=0`. The current prediction builder's rejection guard keys on `(timestamp_epoch, expiry_date, expiry_flag, expiry_code, returned_strike, option_type)` and omits both underlying and collection provenance. The amended economic key below is deliberately more explicit: `(underlying, Greek bar-end instant, normalized expiry date, returned strike, normalized option side)`, with `expiry_flag` and `expiry_code` moved into the conflict-checked signature. Therefore the prior source audit and the current preflight guard are checking different notions of duplication. The current guard is correct to refuse silent multiplicity but has not yet established whether those rows are economically identical.

## Purpose and narrow scope
Resolve duplicate *economic contract-time* rows only for constructing in-memory features. The accepted Greek artifact and all 61 encrypted parts remain immutable; no source data, row counts, encryption or source manifest are rewritten. This is a data-modeling/canonicalization rule, not a change to prediction targets, horizons, estimators, split plan, metric family or holdout policy.

## Frozen economic key and valuation timestamp
Normalize the source bar-start epoch to integer UTC seconds, validate the registered 60-second Greek valuation offset, canonicalize the expiry to a date and normalize known option-side aliases. Define the economic key:
`(underlying, greek_valuation_epoch_seconds, normalized_expiry_date, returned_strike, normalized_option_type)`.

`expiry_flag` and `expiry_code` are signature fields, not key fields: if the same economic key has different flag/code values, that is a conflict to report and block, not a second economic contract. Different underlying, valuation instant, actual expiry date, returned strike or normalized side always form different keys.

Requirements:
- The bar-end/valuation epoch is source `timestamp_epoch + 60 seconds`; exact matching remains mandatory. No nearest/as-of join, forward fill, or time shift is allowed.
- `underlying`, source timestamp, expiry/date identity, returned strike and option side must be present and parseable. Missing or ambiguous key members mean `BLOCKED_DATA`, never a shared synthetic MISSING key.
- Normalize known side aliases only through the already-approved fixed CE/PE mapping; unknown sides are blocked from the Greek aggregation rather than merged into CE or PE.

## Frozen economic-equivalence comparison
For each repeated economic key, compare every value in this fixed economic signature (allowing exact numeric equality after numeric parsing; two missing values compare equal only when both are truly missing):
- Underlying and session/timestamp semantics: `underlying`, `timestamp_epoch`, `timestamp_utc`, `timestamp_ist`, `session_date`, `row_type`.
- Contract/expiry identity and valuation assumptions: `expiry_date`, `expiry_mapping_source`, `expiry_flag`, `expiry_code`, `returned_strike`, `option_type`, `time_to_expiry_years`, `greek_valuation_offset_seconds`, `risk_free_rate_decimal`, `risk_free_rate_source`, `dividend_yield_decimal`, `dividend_yield_source`, `greek_assumption`.
- Recorded market inputs and source/cache metadata: `option_open`, `option_high`, `option_low`, `option_close`, `option_volume`, `open_interest`, `implied_volatility`, `rolling_spot`, `nifty_open`, `nifty_high`, `nifty_low`, `nifty_close`, `nifty_volume`, `spot_join_status`, `spot_valuation_source`, `source_provider`, `source_endpoint`, `cache_status`.
- Greek/model outputs and quality: `greek_implied_volatility`, `greek_iv_source`, `delta`, `gamma`, `theta_per_day`, `vega_per_1pct_iv`, `rho_per_1pct_rate`, `greek_model`, `greek_status`, `data_quality_flags`.

Only four collection-provenance fields may vary without making an otherwise identical economic row conflicting: `source_request_id`, `requested_relative_strike`, `request_scope_sha256`, and `response_sha256`. No other varying field is silently ignored. If schema evolves or a signature column is missing, block and request review rather than defaulting to a smaller signature. Date normalization and option-side normalization are fixed functions with explicit synthetic fixtures. `timestamp_utc` and `timestamp_ist` normalize to the same canonical UTC instant and must agree with the epoch timestamp; they are not compared as raw formatting strings. Numeric values compare exactly after canonical numeric parsing; other strings compare exactly after type-specific normalization. Two missing values compare equal only when both are missing, but key fields may never be missing.

## Frozen handling rule
1. First pass/diagnostic counts all repeated economic keys and partitions them into (a) repeated rows with identical economic signatures and (b) conflicting signature groups.
2. If any group conflicts on any economic signature field, emit `BLOCKED_DATA` / `DUPLICATE_CONTRACT_INPUTS_CONFLICT`; report only aggregate counts, a sorted list of conflicting field names and hashes/identities. Do not log or upload raw rows, contract values, per-contract details, decrypted data or keys. Do not average, select the latest row, or choose a source based on model performance.
3. If all repeated groups have identical economic signatures, select one deterministic representative per economic key for the *in-memory feature aggregate only*. The method must be independent of labels, future returns, model metrics and row order (e.g., sort on a hash of the four permitted provenance fields, then select the first identical-signature row).
4. Report aggregate duplicate diagnostics: raw option rows scanned, exact matched option rows, number of unique economic contract keys at requested instants, repeated groups, extra repeated records, identical-signature repeat groups/records, conflicting groups/records, signature comparison fields, and a hash of the canonicalization specification. A successful canonicalization cannot alter the encrypted source artifact or its row-count manifest.
5. Recalculate Greek feature counts, side medians, OI/volume ratios, provenance proportions and exact-join rates using unique economic contracts; publish those counts beside raw matched-row counts. Coverage claims remain about the visible PARTIAL_GRID only.

## Synthetic tests required before reviewer approval
- Two rows with identical economic fields and different `source_request_id`/`requested_relative_strike` are counted as one economic contract; results are invariant to input order and the selected representative.
- Duplicate rows that differ in `option_close`, `open_interest`, `option_volume`, `implied_volatility`, `expiry_date`, `expiry_mapping_source`, `greek_status`, a Greek value or data-quality flags are blocked with the named conflicting field(s).
- The economic key separates different underlying, expiry, strike or CE/PE side; it uses exact bar-end valuation time and never merges adjacent timestamps.
- Missing/unparseable key or signature fields fail closed.
- Deduplication counts and canonicalization are invariant under row permutation; no label or prediction columns are part of the signature or decision rule.
- Output contains aggregate counts and hashes only; test fixtures verify no raw values or contract rows are serialized.

## Restrictions unchanged
- Only the pinned, immutable Greek artifact and frozen Run #994 prediction panels are allowed; no new external source request.
- No holdout access, model fitting, P&L, transaction cost/slippage/brokerage modelling, strategy testing or strategy promotion.
- A new code snapshot requires a new exact tester code gate. The preflight executor and request must then be re-pinned/re-reviewed to use that exact code snapshot before another artifact run.
- Any unresolved conflicting duplicate rows leave the preflight blocked. Do not infer predictive value from a failed preflight.

**Developer → Tester:** independently review this proposed economic-duplicate rule and fixed signature field list. Approve scope amendment only or request concrete changes; this proposal does not authorize code, data access or model fitting.

**Tester → Developer:** preserve the original R3 scope and failed preflight receipts; implement only after scope amendment PASS, with synthetic tests and a new exact code-only review before any next data run.
