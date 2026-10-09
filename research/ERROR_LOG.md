# Repository Error Log Index

This file is the main-branch entry point for recorded errors and corrections. Entries are append-only; do not erase failed attempts or treat failed workflows as scientific evidence.

## 2026-10-09 — Main-branch protocol checks

- **Failure series:** Research Protocol Check #1002 through #1007 failed at `scripts/validate_protocol.py` on `main`; no Phase 6/7/8 scientific job was authorized by these failures.
- **Initial cause:** required protocol/literature validation files and the literature registry were missing from the default branch, although they existed on the isolated phase developer branch. They were restored to `main`.
- **Residual cause:** the plan described an “untouched forward validation” segment while the protocol validator required the term “untouched holdout”. The plan was clarified to state that the reserved forward segment is the untouched holdout; the scientific selection rules were not changed.
- **Verification:** Research Protocol Check #1008 passed repository-contract validation and literature-registry validation. Later main-branch records were also updated to preserve current Phase 7 status.
- **Disposition:** infrastructure/documentation defect, not an empirical result. Failed runs remain failed and no strategy/metric is promoted from them.

## Detailed logs

- [Main-branch CI error table](logs/ERROR_LOG.md) — errors found on the default branch, including the missing-validator and terminology-mismatch incidents.
- [Full research error history on the isolated developer branch](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/ERROR_LOG.md) — detailed phase/run error history and prevention notes.
- [Current phase status on developer branch](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/STATUS.md).
- [Detailed research log on developer branch](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md).

## Current distinction

A GitHub Actions protocol/validator failure is an engineering or governance failure, not a trading-performance result. A successful protocol gate likewise does not validate a strategy. Phase 7 Run #994 remains the only current empirical target until its model execution, schema validation, artifact upload and separate independent tester audit all complete.
