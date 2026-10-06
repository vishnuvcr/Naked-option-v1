# Phase 2B Reconciliation Protocol

## Canonical principle

Official NSE/BSE observations are canonical wherever available. Derived/open datasets are used to:
- discover missing dates/contracts;
- validate independent implementations;
- fill documented gaps only after passing reconciliation.

## Official option cross-check

For each matched date:
1. Normalize expiry, strike and option type.
2. Build deterministic contract key.
3. Compare close, OHLC, volume and OI.
4. Compare underlying value.
5. Record missing keys in each source.
6. Preserve source IDs and hashes.

### Default acceptance thresholds

A derived dataset may be considered a validation match only if:
- contract-key duplicate rate = 0;
- core-price missingness on active matched rows = 0;
- >= 95% of contract keys match in both directions after scoping the official side to the expiry represented by the derived weekly file;
- >= 99% of matched close values are equal within one minimum tick or 0.25% (whichever is larger);
- >= 99% of matched underlying values are within 1.0 index point;
- no unexplained date/time-zone offset remains;
- discrepancies are logged by field and contract.

The derived source is never promoted to canonical solely because it passes one date.

## Derived-source validation universe

For an independently derived dataset that intentionally contains a restricted moneyness range, coverage is evaluated on a pre-declared liquid validation band:
`abs(log(strike / official_spot)) <= 0.05`.
This is not a relaxation of the canonical-data completeness requirement; it explicitly separates full official coverage from partial-data cross-validation. Any use of derived data outside this band is prohibited until independently validated.

## Composite-source rule

A composite record must retain:
- primary source;
- fallback source(s);
- reason for fallback;
- row-level conflict flag;
- snapshot hashes.

No silent averaging of conflicting prices.

## Historical lot size

Lot size comes from effective-dated official contract information. Any derived lot-size table is a cross-check only.

## Legacy-to-UDiFF boundary

The 05-Jul-2024 legacy sample and 08-Jul-2024 UDiFF sample are mandatory schema-boundary fixtures. Both must normalize to the same canonical option schema without ambiguous field mappings.
