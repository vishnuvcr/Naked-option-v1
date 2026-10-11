# Error log addendum — R3 compressed SHA mismatch (2026-10-11)

- Category: data-integrity gate / hash contract.
- Run: [38144072524](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38144072524).
- Passed: exact tester-decision/request hash authorization, source run/artifact lineage, download of the exact 61-part encrypted artifact, encrypted part SHA/size checks, successful decryption of all 61 parts, and row merge count of 8,999,865. Final cleanup step passed and confirmed no plaintext CSV or temporary SQLite files remained.
- Failure: scanner exited at the first compressed-file hash check with `INPUT_SHA256_MISMATCH`; no metadata report was emitted and no uniqueness/data-readiness result was produced.
- Diagnosis: the workflow re-creates the merged gzip stream from exact, individually hash-verified monthly gzip parts. Gzip headers can carry creation-time metadata, so a recompressed byte-stream SHA is not a stable logical-content identity. The current workflow nevertheless compares this new gzip byte hash with the previously exported gzip hash. This is a gate-design flaw, not yet proof that the decompressed CSV bytes match.
- Correction plan: preserve exact source-artifact/part lineage checks; compute and compare the SHA-256 of the full uncompressed CSV byte stream against the previously verified pinned content SHA `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`; report the actual compressed hash and expected-compressed-hash match separately; only continue as a pass if the raw content hash and expected byte count match. A raw content mismatch must produce an explicit reportable FAIL. Keep all result publishing metadata-only.
- Authorization: the R3 single-use audit has been consumed. Scanner/workflow/receipt schema changes require fresh synthetic CI, a fresh exact-hash tester decision, and a new one-use execution request. Do not reuse R3 or infer a duplicate count.

**Developer → Tester:** Review the compressed-vs-uncompressed identity correction and tests before authorizing a new scan.
**Tester → Developer:** Keep model, holdout, new source-request and strategy/P&L gates closed until a fresh exact-hash approval and full data report pass.
