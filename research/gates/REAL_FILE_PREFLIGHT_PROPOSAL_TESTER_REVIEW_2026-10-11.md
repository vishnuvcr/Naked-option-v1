# Tester review — exact-file offline preflight proposal

Date: 2026-10-11
Developer proposal path: `research/gates/REAL_FILE_PREFLIGHT_PROPOSAL_2026-10-11.md`
Reviewed proposal blob SHA: `a007d5bea5ddf0ff804cbb381eedbd47296296db`
Prerequisite synthetic CI run: [38135712550](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38135712550), successful.
Source lineage inspected: `.github/workflows/export-repaired-dataset-offline.yml`, `scripts/decrypt_nifty_1m_composite.py`, and `research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json`.

## Decision
**PASS WITH SCOPED RESTRICTIONS — design/implementation planning only.**

This approval permits the developer to implement the isolated audit workflow and add synthetic workflow tests. It does **not** authorize execution on the real dataset. A fresh exact-source/workflow/test snapshot must be reviewed before any decrypt/audit job is run.

## Review findings
- Proposal pins source lineage to repair run 38131641336, artifact 11698879857, parent artifact 11696937921 and its recorded SHA, with 61 encrypted monthly parts and manifest-level hashes.
- Existing decryption utility derives its decryption key from `HF_TOKEN` in process memory, validates each encrypted-part hash and each decrypted gzip hash, and does not write the token to disk.
- Existing one-time export artifact 11699299285 cannot be assumed decryptable because its private key was intentionally removed. Proposal correctly requires regeneration from the original encrypted derived artifact.
- Expected merged CSV.GZ SHA, row count and column count are specified. The scanner reads the complete gzip stream, validates CSV width and count, and emits metadata rather than raw market rows.
- Workflow must pin all external actions, use minimum GitHub token permissions, keep secrets out of command output, and upload only a short-retention sanitized report.
- Cleanup must be unconditional and must explicitly check for plaintext CSV, monthly plaintext parts, merged CSV.GZ and temporary SQLite files. If cleanup fails, the job must fail and must not publish a success decision.
- The proposal correctly separates this structural audit from modelling-readiness, exact join semantics, market session validity, labels, leakage, model performance and strategy economics.

## Required before execution
1. Implement the workflow and policy guard on the developer branch; keep the real-file run disabled by default.
2. Add synthetic tests for artifact lineage mismatch, part-count/hash mismatch, wrong merged SHA/row/column counts, cleanup-on-failure and report redaction.
3. Confirm the exact manifest header and selected composite-key logic before interpreting duplicate-key results; report per-key-group coverage rather than presenting one generic pass as proof of unique economic instruments.
4. Publish no source rows, option prices, spot prices, secrets or plaintext files to logs or artifacts.
5. Submit the exact code/workflow hashes for a new tester review. Only a subsequent explicit tester decision may authorize the actual file scan.

## Scope
- Proposal design: PASS.
- Implementation/test work: AUTHORIZED.
- Actual dataset decryption and scan: **NOT AUTHORIZED YET**.
- Model fitting/scoring, holdout, new source requests and strategy/P&L: **CLOSED**.

Tester → Developer: Implement the isolated workflow with synthetic tests, then resubmit exact hashes; do not run the real-file job before the next tester decision.
Developer → Tester: Review the implemented workflow and test evidence, and separately decide whether the exact-file audit may execute.
