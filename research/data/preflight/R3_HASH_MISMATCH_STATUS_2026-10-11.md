# Research status addendum — R3 audit failed closed on compressed hash (2026-10-11)

## Confirmed run outcome
- Audit run [38144072524](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38144072524) failed at the structural scanner with `INPUT_SHA256_MISMATCH`.
- Exact authorization, source artifact lineage, download and SHA checks for all 61 encrypted pieces, decryption, and merge row count (8,999,865) passed.
- Cleanup passed: the runner confirmed no plaintext CSVs or temporary SQLite files remained.
- No scanner report was uploaded; duplicate-key count, raw CSV hash and data-readiness status remain unknown.

## Correction
The scanner was checking the compressed container SHA after re-compressing monthly parts; gzip metadata such as the modification timestamp can change that hash even when decompressed content is identical. This hypothesis will be tested, not assumed: next scanner revision will hash the full decompressed CSV byte stream and compare against pinned uncompressed SHA `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`, while separately reporting compressed SHA and match status. Raw-content mismatch will remain a failure.

The single-use R3 authorization is consumed. Any code/workflow/report-schema changes must pass synthetic CI and a fresh tester exact-hash gate before an R4 scan. All modelling, holdout, source-request and strategy/P&L gates remain CLOSED.

**Developer → Tester:** Independently review content-hash logic, sanitizer changes, tests, and the R3 failure log.
**Tester → Developer:** Issue fresh one-use authorization only for the exact revised snapshot; do not accept the dataset until R4's completed report and cleanup evidence are reviewed.
