# Tester Report — Derived Dataset Repair Pipeline

- Review date: 2026-10-11 UTC
- Exact developer commit reviewed: `b1cb16e38e8c510412d1329f63eb70a2f76058e5`
- Offline pipeline suite: [38129565390](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38129565390) — success
- Protocol check: [38129565580](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38129565580) — success
- Reviewer independence caveat: this tester-role review is in the same connected assistant session, not a separate human or independent AI reviewer.

## Exact files reviewed

| File | Blob SHA |
|---|---|
| `scripts/repair_nifty_1m_composite_values.py` | `088f2f2ef231c62d38fc8e043983baab278bf6a1` |
| `scripts/test_repair_nifty_1m_composite_values.py` | `7feec4ab65a82d202192ff7f83453d898ee27037` |
| `.github/workflows/phase-07-nifty-1m-composite-tests.yml` | `43219ac101bd8965a7cd55441b5820ba11a6e7d0` |

## Review findings

1. **Source immutability — PASS BY CODE REVIEW.** The repair script reads decrypted copies and writes a separate derived output directory. It never overwrites source monthly parts.
2. **Exact join rule — PASS BY CODE REVIEW.** Joined NIFTY OHLCV values are reconciled only against the standalone SPOT row with the identical epoch. It never nearest-time joins, shifts timestamps, or interpolates.
3. **Invalid OHLC — PASS WITH RESTRICTIONS.** Invalid standalone spot OHLC is masked to missing. Joined option rows for that same epoch are also masked. Invalid option OHLC is masked. The script does not invent, swap, clamp, or extend OHLC values.
4. **Negative volume — PASS WITH RESTRICTIONS.** Negative/unparseable option volume is masked to missing. Joined NIFTY volume is sourced from the exact-epoch standalone SPOT row if valid; invalid spot volume is masked, not set to zero.
5. **Unmatched rows — PASS.** Rows marked `NO_EXACT_TIMESTAMP_SPOT_MATCH` remain unmatched and underlying OHLCV stays blank. No fabricated fill is attempted.
6. **Encryption — PASS BY CODE REVIEW.** Derived monthly gzip parts are encrypted using the repository's existing AES-GCM format and key derivation. Only the encrypted parts, manifest, and sanitized aggregate report should be published.
7. **Synthetic regression tests — PASS.** Four tests cover exact-epoch reconciliation, masking invalid spot OHLC/volume, negative option volume masking, unmatched row preservation, encrypted-output readability and input/output path separation.
8. **Remaining operational gate — NOT YET PASSED.** This report does not establish the latest artifact's provenance distribution or actual derived-output counts. The hosted repair workflow must run against the exact approved artifact, verify hashes and row counts, remove plaintext, and publish its aggregate report. A new tester review must check the actual output counts before any modelling dataset is selected.

## Verdict

**PASS WITH SCOPED RESTRICTIONS — synthetic repair code and encryption path only.**

Do not promote a derived dataset to model fitting based only on this report. The current source has 19,021 unmatched option rows; these remain unmatched unless an exact timestamp source is already present. The derived dataset is a quality-controlled candidate with explicit missingness, not a complete dataset.

**Tester → Developer:** Run the repair against the fixed patch artifact only after the value-provenance diagnostic completes; verify encrypted part hashes, unchanged row counts, correction counts and cleanup logs.

**Developer → Tester:** Review the actual sanitized repair report and derived manifest at the exact output SHA; model, holdout and strategy gates remain closed pending that review.
