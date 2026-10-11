# Tester review — CSV key-schema preflight correction

Date: 2026-10-11
Gate: `REAL_FILE_PREFLIGHT_IMPLEMENTATION`
Developer snapshot reviewed: `phase-07-developer`, code snapshot ending at commit `83c60b52c79f0c6caf27947f014a375ab4470aa2`
Validation PR: [#15](https://github.com/vishnuvcr/Naked-option-v1/pull/15)
Hosted synthetic test run: [38140375493](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38140375493) — **success**.
Supplemental earlier batch-boundary test run: [38140046876](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38140046876) — **success**; its explicit 10,000-row batch-boundary fixture was on the prior scanner blob, before only key-value normalization was expanded.

## Decision
**CODE REVIEW PASS WITH SCOPED RESTRICTIONS; EXECUTION NOT YET AUTHORIZED.**

The implementation is suitable for a single exact-lineage, metadata-only structural audit, subject to a fresh machine-readable tester decision. Updating the machine-readable authorization file was blocked by the repository tool's safety controls in this turn. The prior decision remains stale for the current scanner hash, so the real-file workflow must not be run or treated as authorized. This review does **not** claim the data passed, and it does not authorize model fitting/scoring, holdout access, new market-data requests, strategy testing, or P&L work.

## Independent review findings
- The actual data header uses `timestamp_epoch,row_type,underlying,expiry_code,returned_strike,option_type`; the revised scanner recognizes separate OPTION and SPOT key groups.
- OPTION rows cannot fall back to the shorter SPOT key group when contract fields are incomplete; they are classified as incomplete instead.
- Timestamp values are canonicalized numerically. `returned_strike` is now canonicalized as a finite numeric value, and row type, option type, underlying, instrument type, and symbol are normalized to uppercase for composite-key comparison. This prevents common textual format/case differences from evading duplicate detection.
- SQLite duplicate counting batches up to 10,000 keys at a time. The insertion delta method counts duplicate rows as batch size minus successfully inserted rows; duplicates within a batch and across prior committed batches are ignored by the primary-key index and included in the duplicate-row count.
- Synthetic fixtures cover duplicate OPTION keys, duplicate SPOT keys, mixed OPTION/SPOT rows, incomplete OPTION keys, and canonical strike/case variants. The latest hosted test suite passed.
- The existing audit authorization helper fails closed on a stale decision blob, any hash mismatch among its required paths, missing required files, wrong gate, or insufficient scope.
- The production audit workflow is pinned to the specific derived artifact/run and expected CSV SHA, and its result upload is metadata-only. Report upload is conditioned to run even if the scanner returns a non-pass status, when the report exists. Cleanup verifies that plaintext CSVs and temporary SQLite files are removed.
- Supporting schema test file blob is included below as reviewed evidence. The real-file workflow's enforced `--reviewed-files` list continues to hash-check its 11 runtime-required files; the schema-only test itself does not execute in the real-file job, and is separately covered by the successful offline-test workflow.

## Exact reviewed file hashes

```json
{
  ".github/workflows/phase-07-real-file-preflight-audit.yml": "a0bf00cad4e7f29f79a353c1c7353c116038dfc5",
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

## Conditions on this authorization
1. The run must use the exact expected encrypted dataset lineage and expected merged CSV SHA. No substitute file or new data request is authorized.
2. Publish only the scanner's sanitized metadata report and preserve the run/receipt lineage.
3. Independently inspect the resulting report status, duplicate/incomplete-key counts, row/column totals, timestamp errors, key-group coverage, and artifact SHA before deciding whether data readiness passes.
4. Verify cleanup confirmation from the hosted job logs. A success exit alone is not sufficient.
5. Preserve any non-pass result as a research result. Do not fit models or open holdout/strategy gates until a separate downstream decision has been issued.

**Tester → Developer:** Keep the data workflow untriggered until the machine-readable decision can be updated through an allowed repository action. Then submit an R3 request bound to that decision and these exact hashes; after a run, submit the receipt/report and cleanup evidence for a separate data-readiness review.
**Developer → Tester:** Preserve the successful synthetic test evidence, record the authorization-write blocker, and keep modelling, holdout, source requests and strategy/P&L closed.
