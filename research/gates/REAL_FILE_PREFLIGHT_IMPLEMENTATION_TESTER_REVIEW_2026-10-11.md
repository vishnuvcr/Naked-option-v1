# Tester review — real-file preflight implementation

Date: 2026-10-11
Developer PR: [#10](https://github.com/vishnuvcr/Naked-option-v1/pull/10)
Exact reviewed PR head: `7a430ba836e1169e9761298ca544f2fab3dc569e`
Synthetic CI run: [38137514604](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38137514604) — success.
Gate: `REAL_FILE_PREFLIGHT_IMPLEMENTATION`.

## Decision
**PASS WITH SCOPED RESTRICTIONS — real-file structural preflight only.**

This decision authorizes a single exact-lineage structural audit on the ephemeral GitHub Actions runner. It does not authorize model fitting, prediction scoring, holdout access, new market-data requests, or strategy/P&L work.

## Exact files reviewed
```json
{
  ".github/workflows/phase-07-real-file-preflight-audit.yml": "a0bf00cad4e7f29f79a353c1c7353c116038dfc5",
  ".github/workflows/phase-07-offline-preflight-tests.yml": "2da382b39a8b69e03e1ef3f724a2ee5211f2e0f2",
  "scripts/offline_dataset_preflight.py": "07aa68b638c8c189bc94e083866368dd00723b4a",
  "scripts/test_offline_dataset_preflight.py": "5ae5df68fde13ee5a723e710b1ba83b7ffb99564",
  "scripts/validate_real_file_preflight_authorization.py": "2f8174c320188c79257ca1b14c683f509a66227e",
  "scripts/test_validate_real_file_preflight_authorization.py": "c21fa939ba66d15ff2b5a4408e1384117bc80e80",
  "scripts/check_workflow_action_pinning.py": "cc6ecc45fd78470d838debc19f5b835369acb1d3",
  "scripts/test_workflow_action_pinning.py": "e414c5cea4d71586ad80f9b5b0b85cbd79a3dade",
  "scripts/decrypt_nifty_1m_composite.py": "6ba27b65548b9197e0db35deeafcedbade6ca445",
  "requirements-composite.txt": "8c74241f2035a3e388087078be5e5aaf846addca",
  "research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json": "66683afe7c498a6b52d7863a0da0c4f7a47734c8"
}
```

## Review findings
- The audit is bound to the source repair run, exact source SHA, derived artifact ID/name, parent artifact lineage and expected 61-part manifest. Each encrypted part's size/hash is checked before decryption.
- The existing decrypt utility validates encrypted and plaintext-part hashes. The secret is passed only as a step-scoped environment variable; no token is written to disk or printed.
- The merged CSV.GZ is checked against the exact expected SHA-256, 8,999,865 rows and 47 columns. The scanner consumes the full gzip stream and validates row widths, duplicate headers, timestamps and recognized composite-key uniqueness.
- The scanner reports selected key-group coverage and incomplete-key counts; absent schemas, duplicates, incomplete identifiers and timestamp parse errors fail or enter a review state.
- Only sanitized metadata JSON is uploaded, with short retention. No plaintext CSV or raw row values are uploaded.
- The workflow has immutable SHA-pinned actions, minimum `actions: read` / `contents: read` permissions, and a manual dispatch option. Real data is not downloaded unless the tester decision's blob hash, explicit execution request, verdict, gate name and every reviewed file blob hash match.
- Cleanup runs with `always()`, removes the encrypted bundle, decrypted monthly parts, merged CSV.GZ and SQLite temporary files, and fails if plaintext/temporary files remain.
- Exact-snapshot synthetic CI passed after corrections. Earlier failed runs are retained as failures and were not used as acceptance evidence.

## Execution authorization
`real_file_preflight_execution_authorized = true` for the exact file list above only. The developer must merge this snapshot without changing any reviewed file blobs, then add an execution request that pins this tester decision's blob SHA. Any changed reviewed file invalidates authorization automatically.

## Restrictions after audit
A structural PASS is not modelling readiness. The result must still be reviewed for actual header semantics, per-key-group coverage, unmatched spot rows, OHLC validity, session/calendar correctness, target timing and leakage safety. Do not fit a model or touch holdout data until a separate target/split contract gate passes.

Tester → Developer: Merge only if the reviewed file blobs are unchanged, then submit an execution request referencing this decision blob SHA. After the audit, publish the sanitized report and request a separate data/target-readiness review.
Developer → Tester: Keep modelling, holdout, source requests and strategy/P&L closed; independently review the exact audit report before any next gate.
