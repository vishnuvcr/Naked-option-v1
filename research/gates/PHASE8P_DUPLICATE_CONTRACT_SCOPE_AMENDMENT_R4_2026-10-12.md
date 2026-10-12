# Phase 8P — Manifest-Bound Contract Signature and Schema Amendment R4
Date: 2026-10-12
Applies to: approved Greek prediction scope R3 and duplicate-contract scope amendment R3
Status: **SUBMITTED FOR INDEPENDENT TESTER SCOPE REVIEW — NO ARTIFACT ACCESS OR MODEL FIT AUTHORIZED**

## 1. Reason for R4
The R3 duplicate-contract implementation added an exact set check based on a developer-authored list of columns. Its synthetic regression run [#38204234797](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204234797) failed because the existing older mixed OPTION/SPOT fixture did not model the complete source schema. More importantly, the developer list included several fields whose presence in the frozen, encrypted source manifest had not been independently established. Treating that guess as authoritative would risk either false schema failures or overlooking actual fields.

The earlier preflight runs [#38203577299](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38203577299) and [#38203641510](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38203641510) remain non-accepting diagnostics, not prediction results. The latter correctly reached `DUPLICATE_OPTION_CONTRACT_TIMESTAMP_ACROSS_PARTS`, but did not publish a valid coverage table. No empirical model has been fitted.

## 2. Revised authoritative schema contract
The immutable accepted Greek artifact's own `dataset_manifest.json` `columns` list shall be the authoritative exact schema, because it is part of the ZIP pinned to SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`. No schema will be guessed from a convenience fixture or inferred by dropping unknown columns.

Before using any part for feature construction:
1. Verify the pinned whole-artifact ZIP hash and exact artifact ID as already required.
2. Read the manifest without writing decrypted rows to disk. Verify that `columns` is a nonempty list of unique nonempty strings and compute SHA-256 of its canonical JSON representation.
3. Assert the frozen manifest's complete column list is the exact expected ordered list for every decrypted part. Missing, additional, duplicated, or reordered headers block with a safe schema error. The artifact ZIP digest remains the outer immutable identity gate.
4. Require the semantic/key input fields listed below. Do not require both UTC and IST textual timestamps if the source schema contains only one; at least one of `timestamp_utc` or `timestamp_ist` must be present. If both exist, both must normalize to the same instant as `timestamp_epoch`.
5. Define the per-row economic signature dynamically as **every actual manifest column except the permitted provenance-variance fields that are present in that manifest**. Thus every unfamiliar field is compared, never ignored. Report the manifest schema hash and actual ordered column-set count. A changed artifact manifest/columns cannot be silently accepted because the input ZIP identity is immutable and verified.

## 3. Required semantic fields
The manifest must contain all of these non-provenance fields before canonicalization:
- Key identity: `row_type`, `underlying`, `timestamp_epoch`, `expiry_date`, `returned_strike`, `option_type`.
- Expiry/provenance quality: `expiry_flag`, `expiry_code`, `expiry_mapping_source`.
- Option market inputs: `option_close`, `option_volume`, `open_interest`, `implied_volatility`.
- Underlying/spot values available on the row when the schema defines them: `rolling_spot`, `nifty_close`, `spot_join_status`, `data_quality_flags`.
- Greek calculation: `greek_valuation_offset_seconds`, `time_to_expiry_years`, `risk_free_rate_decimal`, `dividend_yield_decimal`, `greek_implied_volatility`, `greek_iv_source`, `delta`, `gamma`, `theta_per_day`, `vega_per_1pct_iv`, `rho_per_1pct_rate`, `greek_model`, `greek_status`.

If one of the row-level values is missing because the value itself is unavailable, the column must still exist and the field is canonicalized as missing. A missing *column* is a schema failure. Extra columns from the pinned manifest are automatically part of the economic signature, even if R4 does not list their names individually.

## 4. Frozen economic key and timestamp semantics
Canonical key:
`(underlying, greek_valuation_epoch_seconds, normalized_expiry_date, returned_strike, normalized_option_type)`.

- Normalize source start epoch to integer UTC seconds. Validate the manifest's `greek_valuation_offset_seconds` is exactly 60 seconds on selected OPTION rows; the valuation instant is source timestamp + 60 seconds.
- Normalize side only through the fixed aliases CE/CALL/C and PE/PUT/P; unknown side blocks.
- Normalize expiry to a date. `expiry_flag` and `expiry_code` are signature fields rather than key fields. If same canonical economic key has conflicting flag/code/expiry mapping, block with the names of the fields.
- At least one of the manifest columns `timestamp_utc`, `timestamp_ist` must exist. If either is present, normalize it to UTC and prove it equals `timestamp_epoch`; if both are present, they must both agree. Do not require a representation not present in the immutable source schema.
- Missing/invalid key values, timestamp contradictions, unregistered offsets, or duplicate/ambiguous column headers fail closed.

## 5. Full signature and exact duplicate policy
All manifest columns except the following fields **when present** participate in the signature:
- `source_request_id`
- `requested_relative_strike`
- `request_scope_sha256`
- `response_sha256`

The four excluded fields only describe how a row was collected. Their presence is optional in a schema if they are not in the pinned manifest; if any is present, it is the only permitted source of row-to-row variance for otherwise identical economic rows. No other extra field may be excluded.

Canonicalization:
- Numeric values are parsed to finite numbers where the field is numerically typed, with missing compared equal only to missing.
- Timestamp and date fields use frozen UTC/date normalization. Categoricals use frozen uppercase/trim rules where semantically defined. Other fields compare using strict deterministic type-preserving normalization; any discrepancy is treated as a conflict rather than coerced away.
- For a repeated economic key, compare every signature field. Exact signature equality permits deterministic selection of one in-memory representative, chosen by hash of the allowed provenance fields, independent of input order.
- Any signature difference yields `BLOCKED_DATA` / `DUPLICATE_CONTRACT_INPUTS_CONFLICT`; do not average, select latest, suppress a non-provenance difference, or choose based on future labels/model results.
- The encrypted source artifact, 61 encrypted parts, rows and manifest are immutable; deduplication exists only in the feature-building view.

## 6. Diagnostics and output
The aggregate-only report must include:
- pinned input artifact IDs and SHA-256 values;
- manifest column count/order hash and schema-check status;
- option rows scanned, raw matched rows and unique economic contract keys;
- repeated economic key groups and extra records;
- groups/records whose signature agrees and groups/records with conflicts;
- sorted conflicting field *names only*;
- canonicalization policy version/hash and explicit statements that raw row values were not emitted and no plaintext upload occurred.

Do not include raw rows, per-contract keys/values, feature arrays, decrypted part filenames in diagnostics beyond the already-approved artifact identity, or key material. A `BLOCKED_DATA` diagnostic is a valid stop result, but not a prediction result.

## 7. Synthetic regression cases required
- Full manifest-bound schema with OPTION and SPOT rows; SPOT rows do not require Greek valuation offsets.
- Same economic row with differing permitted provenance is counted and deterministically reduced in-memory; feature outputs/summary hashes are invariant to input row order.
- Conflicts in option close, option volume, open interest, IV, expiry date/flag/code/source, Greeks, quality flags and any additional manifest signature field block with the field name only.
- Missing/extra/reordered/duplicate columns block; missing value in a present column is distinct from missing column.
- Underlying, valuation instant, expiry date, strike and CE/PE side create distinct keys; timestamp epoch and any UTC/IST fields must agree.
- Unknown option side, missing key members and invalid/mismatched timestamp data block.
- Aggregate diagnostic contains counts/hashes only, no contract/market values, raw rows or per-row features.

## 8. Restrictions unchanged
- Only the existing immutable Greek artifact and existing frozen Run #994 prediction artifact may be used for the later schema preflight.
- This amendment approves no code, data rerun, model fit, holdout, external market source, P&L, execution-cost/slippage/brokerage assessment or strategy promotion.
- The developer must implement R4 plus synthetic tests, obtain a new exact-snapshot independent code PASS, update the preflight executor and obtain another independent workflow PASS, then produce an aggregate schema/coverage report. The report itself still requires a distinct tester decision before any model fit.

**Developer → Tester:** independently review the manifest-bound exact-schema rule, mandatory semantic fields, conditional timestamps, dynamic signature and four provenance exclusions. Approve scope amendment only or request concrete corrections.

**Tester → Developer:** preserve R1–R3 and the failed synthetic run as history. Do not access artifacts or run models until this scope amendment, exact code gate and revised preflight workflow gate are each approved.
