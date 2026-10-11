# Tester Report — Offline CSV Export Result

- Review date: 2026-10-11 UTC
- Export workflow run: [38133038676](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38133038676) — **success**, all 14 workflow steps succeeded.
- Ciphertext-only Action artifact: [11699299285](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38133038676/artifacts/11699299285), `nifty-repaired-offline-encrypted-38133038676`, 230,930,593 bytes, retention one day.
- Source repair output: run 38131641336 / artifact 11698879857; source rows and repair policy unchanged.
- Scope: verification of this requested one-time offline export only. This does not authorize model, holdout, or strategy/P&L work.

## End-to-end validation

1. Export workflow pinned and verified the exact successful source run/commit/artifact.
2. All 61 encrypted monthly parts passed file-set, byte-length and SHA-256 checks before decryption. Repository decrypt utility checked their authenticated encryption and decrypted gzip SHA-256 digests.
3. The merge produced one CSV.GZ with a single header, 8,999,865 data rows and 47 columns. The hosted full-file CSV parser completed and reported the same data-row count and header width. Workflow report SHA-256 for the merged CSV.GZ is `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5`.
4. The CSV.GZ was encrypted to a one-time public key; only the ciphertext payload, wrapped AES key and metadata were uploaded. Plaintext CSV/CSV.GZ was not uploaded or committed.
5. Locally, the downloaded ciphertext package's hashes were checked, the AES key was unwrapped with the matching temporary private key, and the authenticated payload was decrypted. The resulting CSV.GZ size is 230,858,600 bytes and its SHA-256 exactly matches the hosted manifest above.
6. The CSV was expanded to 4,747,892,392 bytes. Physical line count is exactly 8,999,866 (one header + 8,999,865 data records); header has 47 columns and contains required columns `row_type`, `timestamp_epoch`, `session_date`, and `spot_join_status`.
7. Whole-file width validation passed in two consecutive parser-validated segments covering the first 8,000,000 records and final 999,865 records, each using the C-engine CSV parser. No uneven-width/bad CSV row was reported. The expanded CSV SHA-256 is `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`.
8. Gzip integrity check passed. Temporary RSA private-key material and temporary helper/encrypted package files were removed from the local working directory after verification. The CSV and compressed CSV remain for user download.
9. One local Python validation attempt exceeded the tool command wall-clock timeout before printing a final summary; the existing expanded output was then verified with byte-level hashes, exact line count and two adjacent C-engine parsing segments. This was a local validation execution timeout, not a GitHub workflow failure or evidence of dataset corruption.

## Output metadata

| Output | Bytes | SHA-256 |
|---|---:|---|
| `nifty_repaired_composite_2021-10_to_2026-10.csv.gz` | 230,858,600 | `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5` |
| `nifty_repaired_composite_2021-10_to_2026-10.csv` | 4,747,892,392 | `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204` |

Local verification manifest: `nifty_repaired_composite_offline_manifest.json`, SHA-256 `ac9736c6c757c9624dc9ddbf8acf1e016faa44dd0e37d76a0a7b340ce3fe6254`.

## Residual research coverage restrictions (unchanged)

- 19,021 option rows remain unmatched across 421 timestamps.
- 24,847 rows retain weekend-session review flags.
- Invalid OHLC/volume values were masked as missing during the earlier repair; no rows were deleted and no approximate timestamp joins were performed.
- These coverage limitations remain visible in the CSV. Exporting the file did not resolve or reinterpret them.

## Decision

**PASS WITH SCOPED RESTRICTIONS — offline file generation, decryption and integrity validation only.**

The requester now has both a single compressed CSV and a plain CSV copy. This is not an approval of prediction modelling or strategy results. The plaintext is not stored in the public repository or in the GitHub Actions artifact; the one-day Action artifact remains encrypted-only. No new source request, model fit, holdout access or strategy/P&L test occurred.

**Tester → Developer:** Mark export status complete; publish the verified filenames, byte sizes, hashes, row/column counts and retention/privacy detail in README/status/logs. Do not commit plaintext or private key material.

**Developer → Tester:** Confirm final links and metadata remain consistent; keep all research model/holdout/strategy gates unchanged.
