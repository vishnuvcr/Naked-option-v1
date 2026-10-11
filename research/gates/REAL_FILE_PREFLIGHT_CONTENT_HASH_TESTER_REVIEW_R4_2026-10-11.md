# Independent tester review — R4 exact-content-hash preflight

Date: 2026-10-11
Gate: `REAL_FILE_PREFLIGHT_IMPLEMENTATION`
Code snapshot anchor: `8346d95f3ea81f01bb8e83db9fc9a4b4929dd1af` (file-level authorization; status/log-only commits do not change the reviewed file blobs)
Offline synthetic CI: [run 38146005545](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38146005545) — success.
Real-file gate synthetic authorization CI: [run 38146005462](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38146005462) — success; real-file steps were skipped because the spent R3 request was false and R4 authorization was not yet present.
R3 actual audit: [run 38144072524](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38144072524) — failed closed at the compressed container SHA check before structural scanning; cleanup verified.

## Decision
**PASS WITH SCOPED RESTRICTIONS — authorize one R4 exact-lineage, metadata-only real-file structural audit.**

This authorizes one run of the existing exact-lineage workflow on its pinned encrypted-derived dataset artifact, using the revised decoded-content SHA gate. It does not certify the dataset before the report exists, and does not authorize modelling, holdout access, new source-data requests, strategy testing, or P&L.

## Independent technical findings
- Scanner hashes the entire decompressed gzip payload in streaming blocks, independent of gzip header/mtime/container metadata. The decoded byte SHA must equal pinned `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`. A mismatch yields `PREFLIGHT_FAIL_UNCOMPRESSED_SHA256`; a container-hash mismatch alone is diagnostic when the decoded content hash matches.
- An earlier expected uncompressed-byte value was not traceable to a trusted reference field and has been removed as a required expectation. The scanner reports actual decoded size; it compares size only if a verified reference is provided. The receipt publisher accepts a null expected byte count only when decoded SHA is explicitly true. If expected size is present, type/range/match checks remain strict.
- Row-width and row-count mismatches now create structured, sanitized non-pass reports rather than raising before a report can be uploaded. Gzip corruption/decoded-content mismatch remain non-pass/fail-closed.
- The actual composite header now receives distinct OPTION and SPOT keys; incomplete option contract identifiers cannot fall back to the shorter SPOT key; strike/time/categorical variants are normalized for duplicate comparison; SQLite insertion is batched.
- The receipt publisher's optional-size correction merged to main through [PR #19](https://github.com/vishnuvcr/Naked-option-v1/pull/19), commit `008586fdbf87dfafb7e27468e569ba32d85e4366`. Its synthetic test is included in the current developer offline suite.
- Hosted tests passed against the current file snapshot: run 38146005545 passed the offline synthetic suite; run 38146005462 passed the audit workflow's synthetic authorization suite. A prior additional batch-boundary fixture passed in run [38140046876](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38140046876); the 10,000-row batching/counting operation remains unchanged.
- The separate helper workflow `.github/workflows/phase-07-receipt-publisher-tests.yml` is producing failed run metadata with zero discoverable jobs on developer pushes. This is logged as a separate CI/workflow anomaly; the exact same publisher and workflow-policy tests ran successfully within the established developer offline suite. It is not used as the actual data-audit result.
- Exact source run/artifact lineage remains pinned to the prior approved source run, encrypted artifact ID and all 61 part hashes. The R4 run must still prove the content hash, row and column totals, schema, timestamps, key completeness/duplicates, and plaintext/temp cleanup.

## Exact reviewed file hashes

```json
{
  ".github/workflows/phase-07-real-file-preflight-audit.yml": "bc8364dd8b5c8d988339a86f87b1ee1054bd895a",
  ".github/workflows/phase-07-offline-preflight-tests.yml": "ad78b0f3fbf4f77e79dc95657df4fad731b67d7b",
  "scripts/offline_dataset_preflight.py": "e6578efab385502ef057181f1e97a8d2e3a104d3",
  "scripts/test_offline_dataset_preflight.py": "fa0428de6bce37890511b39c6fb54c3ad34a1ffb",
  "scripts/test_offline_dataset_actual_schema.py": "0616d78261d6b4b8b2a655169e939203d06d2c69",
  "scripts/validate_real_file_preflight_authorization.py": "2f8174c320188c79257ca1b14c683f509a66227e",
  "scripts/test_validate_real_file_preflight_authorization.py": "c21fa939ba66d15ff2b5a4408e1384117bc80e80",
  "scripts/check_workflow_action_pinning.py": "cc6ecc45fd78470d838debc19f5b835369acb1d3",
  "scripts/test_workflow_action_pinning.py": "e414c5cea4d71586ad80f9b5b0b85cbd79a3dade",
  "scripts/publish_preflight_receipt.py": "3f72a86f4261180cb578c84c1058e6ca5d963a66",
  "scripts/test_publish_preflight_receipt.py": "8d972ac0478de1b393d6e5bbeb9e2f19c51832bc",
  "scripts/test_receipt_workflow_policy.py": "47e624abe52fbcfbe9a53b90ded7df1f21f49e72",
  ".github/workflows/phase-07-publish-preflight-receipt.yml": "2b7397fefa47b23ea0066a65da2246e3e0a2e97b",
  ".github/workflows/phase-07-receipt-publisher-tests.yml": "3f6a7020ea1ed39414200c71a3488061563d144c",
  "scripts/decrypt_nifty_1m_composite.py": "6ba27b65548b9197e0db35deeafcedbade6ca445",
  "requirements-composite.txt": "8c74241f2035a3e388087078be5e5aaf846addca",
  "research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json": "66683afe7c498a6b52d7863a0da0c4f7a47734c8"
}
```

## R4 execution conditions
1. The workflow's own authorization validator must report `authorized=true` for the R4 decision blob and all exact file hashes.
2. The source export run, artifact ID/name, parent lineage, encrypted part hashes and output dataset identity must remain exactly pinned.
3. The raw uncompressed CSV SHA must match the pinned content hash; no substitution or hash bypass is permitted.
4. Report the compressed container SHA separately, as diagnostic metadata only.
5. Independently inspect data row/column counts, per-row widths, OPTION/SPOT counts, timestamp parse errors, duplicate key count, incomplete-key rows, key-group field coverage, and all status flags.
6. Verify the final cleanup step removes plaintext CSVs and SQLite temp files.
7. Store the sanitized report/receipt and issue a separate data-readiness decision. Even a structural PASS does not itself grant modelling/holdout/strategy permissions.

**Tester → Developer:** R4 authorization is scoped to this exact frozen snapshot and one run only. Recheck every blob SHA and bind the request to the decision blob before triggering.
**Developer → Tester:** Submit the completed report/receipt and cleanup proof after R4; do not fit models or open holdout/strategy gates until the separate data-readiness verdict is issued.
