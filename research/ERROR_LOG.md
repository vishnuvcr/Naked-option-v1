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


## 2026-10-11 — R2 audit and all-date offline diagnostic activation
- Audit run [38126839141](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38126839141) published the sanitized report after the earlier non-fast-forward failure. Its final job was marked failure because the audit status is **FAIL**, not because artifact verification/decryption failed.
- Dataset status: 8,490,723 option rows; 509,142 spot rows; 8,471,702 exact matches; 19,021 unmatched; 714 semantic error occurrences; duplicate option keys and spot epochs=0. Keep `PARTIAL_GRID` and all modelling gates closed.
- R2 window diagnostic is committed: [report](https://github.com/vishnuvcr/Naked-option-v1/blob/main/research/data/SPOT_PATCH_TIMESTAMP_ALIGNMENT_RUN_38126168547.json). It found zero unmatched options in the patched week and zero intersection between new R2 spot timestamps and the unmatched-option set.
- A previous push of the sanitized reports failed on non-fast-forward, and generated README/status links with local runner paths. Both errors were logged; a later rerun committed the result, and the link path was corrected.
- New offline mapping code is validated by the passing full offline suite [38127552962](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38127552962). The standalone map workflow is being added; it reads only encrypted artifact 11696937921, emits date/count/offset aggregates, and makes no live request.
- Tester post-run decision is REQUEST CHANGES; the R2 marker is spent. No additional Dhan requests, models, holdout or strategy testing are authorized.


## 2026-10-11 — Earlier derived-repair report is not the final validated output
- Category: research acceptance / stale artifact report
- Component: Phase 7 derived dataset repair report and hosted workflow.
- Symptom: prior successful run [38130635408](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38130635408) published encrypted artifact 11698138685, but the currently committed report lacks the `post_repair_validation` block emitted by the newly integrated implementation.
- Impact: the older “DERIVED_REPAIR_COMPLETE” label alone does not satisfy the current acceptance gate. It must not authorize dataset promotion or modelling.
- Disposition: exact source artifact remains pinned and immutable; rerun [38131641336](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336) is executing the updated path. At this log update, repair itself is still in progress; no current-run output/cleanup result is claimed.
- Required verification: confirm 8,999,865 preserved rows across 61 parts, manifest and encrypted hashes, independent post-repair audit summary, cleanup proof, then obtain tester review of this exact output. Model fitting, holdout access, source/API requests, and strategy/P&L testing remain closed.
