# Phase 8P — Manifest-Bound Contract Signature and Schema Amendment R4
Date: 2026-10-12
Status: **SUBMITTED FOR INDEPENDENT TESTER SCOPE REVIEW — NO ARTIFACT ACCESS OR MODEL FIT AUTHORIZED**

## Why R4 is needed
The implementation's new exact-column-set check failed its synthetic run #38204234797 because the older fixture did not model the full input. More importantly, the prior amendment listed several fields as mandatory without proving that they exist in the frozen artifact's source schema. We should not fix that by weakening the real-data guard or inventing a new schema. Preflight runs #38203577299 and #38203641510 remain non-accepting data-gate diagnostics; no model was fitted.

## Authoritative schema
The encrypted Greek artifact's immutable `dataset_manifest.json` `columns` list is the sole exact input schema. The enclosing artifact remains pinned to ID 11723198817 / ZIP SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`.

Before processing rows:
1. Validate that manifest columns are a nonempty ordered list of unique nonempty strings and hash the canonical JSON representation.
2. Verify each decrypted part's ordered column list exactly equals the manifest list; missing, extra, duplicate or reordered headers block.
3. Require the core semantic fields below. Any remaining columns in the immutable manifest are automatically included in the duplicate signature; unknown fields are never dropped.
4. The artifact ZIP hash and manifest lineage remain immutable. A changed artifact/schema must fail the pinned-artifact gate; a code change that weakens schema comparison requires a new review.

## Core required semantic fields
The manifest must include:
- Key: `row_type`, `underlying`, `timestamp_epoch`, `expiry_date`, `returned_strike`, `option_type`.
- Expiry and eligibility: `expiry_flag`, `expiry_code`, `expiry_mapping_source`, `data_quality_flags`, `greek_status`.
- Economic inputs: `option_close`, `option_volume`, `open_interest`, `implied_volatility`, `rolling_spot`, `nifty_close`, `spot_join_status`.
- Greeks/assumptions: `greek_valuation_offset_seconds`, `time_to_expiry_years`, `risk_free_rate_decimal`, `dividend_yield_decimal`, `greek_implied_volatility`, `greek_iv_source`, `delta`, `gamma`, `theta_per_day`, `vega_per_1pct_iv`, `rho_per_1pct_rate`, `greek_model`.

At least one timestamp text field (`timestamp_utc` or `timestamp_ist`) must be present. If both exist, both must normalize to the same UTC instant as the epoch. Do not require both where the frozen schema contains only one. A missing *value* may be represented as missing, but a required *column* absent from the manifest blocks.

## Economic key and signature
Canonical economic key:
`(underlying, greek_valuation_epoch_seconds, normalized_expiry_date, returned_strike, normalized_option_type)`.

Normalize source bar-start epoch to integer UTC seconds, validate the selected OPTION row's valuation offset as exactly 60 seconds, and use start + 60 seconds as Greek valuation instant. Normalize expiry date; accept only fixed CE/CALL/C and PE/PUT/P aliases. Expiry flag and code remain in the signature, not the key; conflicting flag/code/mapping fields on one economic key block.

The complete signature is **all columns from the actual pinned manifest except these collection-provenance columns, when present**:
`source_request_id`, `requested_relative_strike`, `request_scope_sha256`, `response_sha256`.
Those four fields may vary across repeat rows; they are not key/economic fields. Every other column—including columns not individually listed above—must compare equal after fixed canonicalization. Numeric values compare as parsed numeric scalars, known timestamps as UTC instants, date fields as dates, CE/PE aliases through the frozen side mapping, and remaining values strictly after trim/type normalization. Missing equals missing only; a missing key field, invalid timestamp, unrecognized side or unparseable key blocks.

For a repeated key, compare all signature columns. If all match, select one deterministic in-memory representative using a hash of the allowed provenance values, independent of row order. If any signature field differs, emit `BLOCKED_DATA` / `DUPLICATE_CONTRACT_INPUTS_CONFLICT`; do not average, pick latest, silently ignore fields or use prediction results to choose. The encrypted source rows, parts and manifest remain immutable.

## Aggregate-only diagnostic
Report the column count and schema hash; option rows scanned; raw exact-time rows; unique economic contract keys; repeated key groups and extra rows; identical signature groups/records; conflicting groups/records; sorted conflict field names; canonicalization policy version/hash; and explicit no-raw-values/no-plaintext-upload flags. Do not include contract keys, source rows, prices, features, labels, decrypted tables or secret-derived material.

## Required synthetic-only tests
- Valid full-schema fixture with OPTION and SPOT; SPOT rows without Greek offsets do not fail.
- Exact duplicate rows with differing allowed provenance yield one in-memory contract, stable counts and identical summaries under reversed row order.
- Conflicts in option close/volume, open interest, IV, expiry mapping/flag/code, Greek value/status, quality flags and an additional manifest column block and name the field only.
- Missing/extra/reordered/duplicate columns block; missing value vs missing column is distinguished.
- Key separation by underlying, valuation instant, expiry date, strike and CE/PE; UTC/IST fields, when present, must agree with epoch.
- Unknown side and missing/unparseable key fields block.
- Output has only aggregate counts, field names, and hashes; no raw record or market value is serialized.

## Restrictions
R4 authorizes scope only. Implementation requires a new exact-snapshot independent code-only gate. The preflight workflow must then be updated and independently approved against that exact code snapshot before another artifact run. The next run may only produce an aggregate schema/coverage report; a separate tester decision must approve that report before any model fitting. No holdout access, new source requests, option P&L, transaction-cost/slippage/brokerage simulation or strategy promotion is authorized.

**Developer → Tester:** independently review manifest-bound schema semantics, required fields, timestamp representation handling, the four provenance exclusions and dynamic signature. Approve the scope amendment only or request specific changes.

**Tester → Developer:** preserve R1–R3 and the failed synthetic CI run. No artifact run or model fit is permitted until R4, exact code and revised preflight workflow gates pass.
