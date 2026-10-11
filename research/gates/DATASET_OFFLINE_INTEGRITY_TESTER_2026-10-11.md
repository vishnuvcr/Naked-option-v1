# Tester Report — Offline Dataset Artifact Integrity Audit

- Review date: 2026-10-11
- Branch: `phase-07-tester`
- Reviewer qualification: this is a tester-role check performed in the same connected assistant session, not a separate human identity or independent AI reviewer.
- Artifact ZIP SHA-256 reviewed: `aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216`
- Developer audit: `research/data/DATASET_OFFLINE_INTEGRITY_AUDIT_2026-10-11.md`

## Checks reproduced

1. ZIP CRC/member test: PASS; no corrupt member was reported.
2. ZIP member count: 60.
3. Manifest-declared encrypted data parts: 57; missing parts: 0.
4. Each of the 57 encrypted parts was checked against manifest encrypted byte size and SHA-256: 0 mismatches.
5. Sum of manifest part row counts: 8,894,387.
6. Row arithmetic: 8,490,723 option rows + 403,664 spot rows = 8,894,387 total rows.
7. Spot-join arithmetic: 7,591,172 matched + 899,551 missing = 8,490,723 option rows.
8. Gap-fill metadata: 41 of 47 requests succeeded and 6 failed with `response_row_cap_exceeded`.
9. Manifest status remains `PARTIAL_GRID` / `SPOT_GAPFILL_PARTIAL`.

## Verdict

**PASS WITH SCOPED RESTRICTIONS — archive and manifest integrity only.**

The artifact's archive structure and encrypted-part hashes are internally consistent. This is not a dataset-completeness or market-data-semantic pass. The payload was not decrypted, so this report does not validate actual timestamp order, duplicate keys, OHLC inequalities, feature missingness, option-contract mapping, target construction, or leakage-safe model rows.

The 899,551 unmatched option rows and six failed spot windows are substantive coverage limitations. The reported `downloaded_bytes` aggregate excludes the six rejected response bodies and must not be treated as a full wire-byte count.

## Authorization boundary

- Data collection remains closed as requested by the user; no new source requests.
- No model fitting/scoring or holdout access is authorized by this report.
- No option strategy or P&L test is authorized by this report.
- Any prediction run must wait for a separate data-readiness/model gate and must state the precise eligible sample and exclusions.

**Tester → Developer:** Preserve the partial-coverage limitations and keep empirical gates closed until the exact data-readiness evidence and separate model gate pass.

**Developer → Tester:** Any future change to the dataset, parser, or eligibility rules requires a fresh exact-snapshot review.
