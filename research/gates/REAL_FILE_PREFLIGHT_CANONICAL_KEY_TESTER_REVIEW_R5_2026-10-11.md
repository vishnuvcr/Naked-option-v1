# Independent tester review — canonical option request identity (R5)

Date: 2026-10-11
Gate: `REAL_FILE_PREFLIGHT_IMPLEMENTATION`
Developer reviewed code snapshot: `387ef2e7eb0df72e6e5bf1651908e3b9a4d8c7ce`
Hosted synthetic CI:
- [Offline preflight tests run 38147564246](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38147564246) — **success, 50 tests passed**.
- [Exact-file audit workflow run 38147564314](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38147564314) — synthetic authorization/pinning/tests passed; real-file steps correctly skipped because R4 request was marked consumed.

## Decision
**PASS WITH SCOPED RESTRICTIONS — authorize one R5 exact-lineage, metadata-only structural preflight with canonical duplicate identity.**

This approves one scan under the same exact pinned encrypted-derived artifact lineage, with the corrected option/spot key definitions. It does not certify data readiness or open modelling/holdout/strategy/P&L.

## Why R4 duplicate count is not accepted
R4 reported 4,148,431 duplicate rows using the key `timestamp_epoch,row_type,underlying,expiry_code,returned_strike,option_type`. That identity did not match repository-defined row identity and omitted fields that distinguish requests. Do not reuse that count as a validated result.

The established identity is defined independently in:
- `scripts/run_nifty_1m_composite_dataset.py::_row_key`
- `scripts/audit_nifty_1m_composite_values.py::ROW_KEY_FIELDS`
- `scripts/validate_repaired_nifty_1m_composite.py`

Canonical OPTION key:
`timestamp_epoch,row_type,source_request_id,expiry_flag,expiry_code,requested_relative_strike,option_type`.

SPOT timestamp uniqueness is a separate check, matching the production validator's separate spot-epoch set/primary key.

## Corrected implementation findings
- Preflight now selects the official seven-field OPTION request key only when the actual canonical composite schema is present.
- SPOT rows use a separate timestamp-only uniqueness key; they do not enter the OPTION request-key group.
- The one-column SPOT identity is not a general fallback on legacy schemas: canonical groups are selected only when the required actual schema fields exist; legacy synthetic schemas retain their prior composite-key alternatives.
- Synthetic regression tests explicitly cover: same returned strike/time but distinct request IDs and requested-relative-strike selectors (not a false duplicate), a truly repeated canonical OPTION key, repeated SPOT epoch, incomplete OPTION identity (flagged without fallback), and duplicate detection across the 10,000-row batch boundary.
- Existing gzip-content SHA verification remains fail-closed. R4 established that the decoded content hash matches the pinned SHA, but row-key logic must be rerun after this correction to produce an accepted duplicate count.
- The row/column width, timestamp, raw content SHA and cleanup checks from R4 are valid evidence for that exact immutable dataset artifact, but its duplicate count is not accepted under this review.
- The R4 report shows `expiry_date`, `time_to_expiry_years`, Greeks, and rate/dividend fields blank throughout. This review does not call these harmless: after R5, a distinct data-readiness review must assess whether sufficient option/expiry information exists for the proposed prediction targets. Even a corrected duplicate scan PASS is not modelling approval.

## Exact reviewed file hashes

```json
{
  ".github/workflows/phase-07-real-file-preflight-audit.yml": "351a1f9df2907573a90995cf0aa604f38e903ce2",
  ".github/workflows/phase-07-offline-preflight-tests.yml": "ad78b0f3fbf4f77e79dc95657df4fad731b67d7b",
  "scripts/offline_dataset_preflight.py": "6d62b226c2ab6d75c74a8c1cd49e635c06ee739c",
  "scripts/test_offline_dataset_preflight.py": "fa0428de6bce37890511b39c6fb54c3ad34a1ffb",
  "scripts/test_offline_dataset_actual_schema.py": "f4cf2945b3371497596f9408eb7e7f0e4fde71e1",
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

## R5 constraints
1. Recheck every exact hash listed above immediately before setting the R5 request true.
2. Use the existing exact source run/artifact ID, encrypted parent lineage, all 61 part hashes, and pinned decoded content SHA. No alternate dataset or hash bypass.
3. Upload only the sanitized report; verify runner cleanup after the scan.
4. Inspect the new official-key duplicate count, incomplete-option count, and separate SPOT epoch duplicate count.
5. Issue a separate data-readiness decision after R5. Review option expiry/target feature availability before model design.

**Tester → Developer:** The R5 authorization applies only to these exact hashes and one run. The R4 count is superseded for duplicate-key interpretation.
**Developer → Tester:** Recheck all listed hashes, submit the one-use R5 request, and return the sanitized report plus cleanup evidence for a separate data-readiness review.
