# Independent tester review — schema-corrected real-file preflight (R2)

Date: 2026-10-11
Gate: `REAL_FILE_PREFLIGHT_IMPLEMENTATION`
Developer snapshot: `0cfdbdafd468723c473b806b11c9bada0933432c`
Current hosted synthetic test: [run 38143775160](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38143775160) — success.
Earlier actual-schema/canonicalization suite: [run 38140375493](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38140375493) — success.
Supplementary batch-boundary regression: [run 38140046876](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38140046876) — success on the earlier scanner revision, with insertion-batching logic unchanged by later key normalization.

## Decision
**PASS WITH SCOPED RESTRICTIONS — authorize one exact-lineage, metadata-only real-file structural preflight.**

This authorizes exactly one structural scan of the already-pinned encrypted-derived dataset lineage after the workflow's own synthetic authorization test job passes. It does not assert that the dataset will pass. It does not authorize model fitting/scoring, holdout access, new market-data requests, strategy/P&L work, or dataset promotion.

## Exact file hashes reviewed

```json
{
  ".github/workflows/phase-07-real-file-preflight-audit.yml": "2975cd44570ce9e14ae96756a1d900e7ab89a97d",
  ".github/workflows/phase-07-offline-preflight-tests.yml": "2e3feaf8cd0edd39283d9ee675c9c52e4b75aaa8",
  "scripts/offline_dataset_preflight.py": "4893d8e93b2141802d2f343604d3e5f77c42366b",
  "scripts/test_offline_dataset_preflight.py": "5ae5df68fde13ee5a723e710b1ba83b7ffb99564",
  "scripts/test_offline_dataset_actual_schema.py": "0616d78261d6b4b8b2a655169e939203d06d2c69",
  "scripts/validate_real_file_preflight_authorization.py": "2f8174c320188c79257ca1b14c683f509a66227e",
  "scripts/test_validate_real_file_preflight_authorization.py": "c21fa939ba66d15ff2b5a4408e1384117bc80e80",
  "scripts/check_workflow_action_pinning.py": "cc6ecc45fd78470d838debc19f5b835369acb1d3",
  "scripts/test_workflow_action_pinning.py": "e414c5cea4d71586ad80f9b5b0b85cbd79a3dade",
  "scripts/decrypt_nifty_1m_composite.py": "6ba27b65548b9197e0db35deeafcedbade6ca445",
  "requirements-composite.txt": "8c74241f2035a3e388087078be5e5aaf846addca",
  "research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json": "66683afe7c498a6b52d7863a0da0c4f7a47734c8"
}
```

## Independent findings
- Actual OPTION key: `timestamp_epoch,row_type,underlying,expiry_code,returned_strike,option_type`.
- Actual SPOT key: `timestamp_epoch,row_type,underlying`.
- OPTION records cannot fall back to the shorter SPOT key if the contract fields are incomplete.
- Numeric timestamp/strike values are canonicalized; row-type, option-type, underlying and compatibility categorical values are normalized for key comparison.
- SQLite key insertions use bounded 10,000-key batches with `INSERT OR IGNORE`; duplicate-row count is calculated as offered rows minus successful inserts, including repeats within and across batches.
- Synthetic coverage includes duplicate option and spot keys, mixed row types, incomplete option identifiers, and canonical numeric/case variants. CI passed.
- The real-file workflow uses immutable action SHA pins, exact source run/artifact lineage and expected compressed-file SHA-256/row/column expectations. The schema test file was added to the authorization helper's exact-file list and to the workflow's synthetic test command. The decision path now points to this versioned R2 decision rather than the stale R1 decision.
- The audit only publishes the sanitized report, then checks cleanup of plaintext and SQLite temporary files. The report/cleanup evidence will be reviewed after execution; a structural PASS remains insufficient for model readiness.

## Post-run acceptance requirements
1. Check the workflow's machine-readable exact-hash authorization output was `authorized=true`.
2. Verify source run/artifact lineage and merged CSV SHA-256.
3. Inspect report row/column totals, full-scan width count, gzip integrity, timestamp parse errors, OPTION/SPOT counts, key-group coverage, incomplete-key rows and duplicate-key count.
4. Verify plaintext/temporary cleanup in the final cleanup step/job log.
5. Record a separate data-readiness decision; if any duplicate, incomplete key, timestamp or schema issue remains, retain a non-pass status and keep downstream gates closed.

**Tester → Developer:** Issue an R3 execution request bound to the machine-readable R2 decision blob and these hashes. Submit the resulting sanitized receipt/report and cleanup confirmation for a separate data-readiness review.
**Developer → Tester:** Do not fit models, access holdout, request new data, or test strategies until the result is independently accepted by the next gate.
