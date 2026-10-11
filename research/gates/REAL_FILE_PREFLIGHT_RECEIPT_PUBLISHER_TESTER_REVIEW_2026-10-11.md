# Tester review — sanitized preflight receipt publisher

Date: 2026-10-11
Developer PR: [#11](https://github.com/vishnuvcr/Naked-option-v1/pull/11)
Exact reviewed head: `5d2c0c8fbd66ea0d348943c79f55eb95b4088d5b`
The repository's Research Protocol Check run [38138028649](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38138028649) passed its repository-contract and literature-registry jobs. The publisher's dedicated unit-test workflow has not been independently verified on a completed hosted run yet.

## Decision
**PASS WITH SCOPED RESTRICTIONS — receipt publishing only.**

## Reviewed file hashes
```json
{
  ".github/workflows/phase-07-publish-preflight-receipt.yml": "2b7397fefa47b23ea0066a65da2246e3e0a2e97b",
  ".github/workflows/phase-07-receipt-publisher-tests.yml": "3f6a7020ea1ed39414200c71a3488061563d144c",
  "scripts/publish_preflight_receipt.py": "c3b8e174d2eff67799600171882600222dd7876c",
  "scripts/test_publish_preflight_receipt.py": "62663269184cbc0efa656443c71ef707046f73ce",
  "scripts/test_receipt_workflow_policy.py": "47e624abe52fbcfbe9a53b90ded7df1f21f49e72"
}
```

## Findings
- The publisher selects only completed runs of the exact named audit workflow on `phase-07-developer`; manual run IDs are required to be numeric and are checked against the returned run metadata.
- It downloads only the expected sanitized-report artifact for that run.
- The receipt builder rejects unknown report fields, validates the expected dataset filename, row/column counts, hash format, schema/count types, key metadata and a fixed allowlist of limitation text. Non-pass scan outcomes are not labeled as clean passes.
- The publisher uses only `GITHUB_TOKEN`, with `actions: read` and `contents: write`; the only write path is a per-run JSON receipt under `research/data/preflight/` on the developer branch. No market-data secret is present.
- The workflow supports automatic publication on audit completion and recovery on its main-branch push/manual dispatch. It does not itself decrypt data or run a market-data request.

## Restrictions
- This decision authorizes only the sanitized receipt publisher. It does not certify the underlying audit result or authorize modelling.
- Dedicated receipt tests should run after the workflow is present on the default branch. Any failed test must be fixed and logged; the published receipt must be inspected before accepting the real-file gate.
- Model fitting/scoring, holdout access, new source requests and strategy/P&L remain CLOSED.

Tester → Developer: Merge only this receipt publisher snapshot, verify its dedicated CI result, and inspect the published receipt before declaring the data gate complete.
Developer → Tester: Submit the receipt JSON and its blob hash for independent review; keep all downstream gates closed.
