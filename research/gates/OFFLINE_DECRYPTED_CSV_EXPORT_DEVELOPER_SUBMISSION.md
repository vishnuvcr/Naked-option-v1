# Developer Submission — Offline Decrypted CSV Export

## Goal
Provide the user a downloadable, decrypted, unencrypted single CSV containing the already tester-reviewed derived dataset, for offline storage. No plaintext dataset is committed to the repository.

## Exact source pins
- Accepted repair run: 38131641336, head SHA `5e769cd4b19887311213baf16eb81b97416322d7`.
- Derived artifact: 11698879857, `nifty-1m-derived-repaired-r2-38126168547`.
- Source parent artifact: 11696937921, SHA-256 `5337b545a0b95b943fc3de4f39b00c5d857a656fc663a9387a564aaf288af80b`.
- Manifest must identify the expected derived dataset, exactly 61 encrypted monthly parts, and 8,999,865 total rows. Every encrypted part SHA-256/size is checked before decrypt; the existing decrypt helper then verifies authentication and every plaintext-gzip SHA-256.

## Implementation
- New helper: `scripts/export_decrypted_nifty_1m_csv.py`.
- Regression tests: `scripts/test_export_decrypted_nifty_1m_csv.py`.
- Workflow: `.github/workflows/export-decrypted-nifty-dataset.yml`.
- Only `HF_TOKEN` in runner environment supplies the existing decryption key derivation. It is never printed or saved.
- Exports one `nifty_1m_composite_repaired.csv`, plus aggregate `EXPORT_MANIFEST.json` and `README_OFFLINE.txt`, as a GitHub Actions artifact with 90-day retention. No output CSV is written to a repository path.
- The merged CSV is streamed month-by-month; headers/schema, each monthly row count, total row count, and OPTION/SPOT row-type totals are checked.
- Scratch bundle and decrypted monthly files are removed and checked before upload. The intended CSV is kept only for the artifact-upload step and removed when the hosted runner is discarded.
- Workflow runs automatically when promoted to main and also has a manual dispatch button.

## Explicit coverage caveats
The accepted repair artifact preserves 8,490,723 OPTION and 509,142 SPOT rows (8,999,865 total). It retains 19,021 unmatched OPTION rows blank for underlying OHLCV and 24,847 weekend-session review flags. The CSV is unencrypted for user offline storage; this is not a prediction/model/strategy result.

## Reviewer instructions
**Developer → Tester:** Independently review lineage pins, artifact preflight, checksum/decryption path, no-secret/no-repo-plaintext invariant, streaming CSV schema and row reconciliation, cleanup/upload gates, and regression tests. Return REQUEST_CHANGES for any bypass or unstated missingness.

**Tester → Developer:** Approve only the exact content hashes. After main promotion, verify the actual export artifact and report counts/CSV digest from hosted logs. Do not authorize modeling.
