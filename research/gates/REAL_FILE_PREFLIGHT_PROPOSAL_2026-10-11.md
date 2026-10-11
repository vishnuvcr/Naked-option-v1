# Proposal — exact-file offline dataset preflight

Date: 2026-10-11
Branch role: developer proposal only.
Prerequisite gate: synthetic preflight code gate passed at exact snapshot `0e9b5f592f8004022576598936a7f24a8268caca`; Actions run 38135712550. Tester decision is scoped to synthetic code validation.

## Research question
Can the exact repaired NIFTY composite CSV.GZ be structurally audited inside an ephemeral, credential-minimal GitHub Actions runner, with only sanitized metadata retained, before any prediction model is fitted?

## Aim and objectives
1. Recreate the same merged compressed CSV from the pinned encrypted repaired artifact lineage already used by the offline export workflow.
2. Verify source run ID, source head SHA, artifact ID/name/expiry/size, derived manifest lineage, all 61 encrypted part hashes and sizes, and the expected merged SHA-256.
3. Run the bounded-memory preflight against the exact expected file (8,999,865 rows; 47 columns; SHA-256 `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5`).
4. Retain only a sanitized JSON report containing file metadata, row/column counts, null counts, timestamp parse counts/range, key-schema coverage, duplicate-key counts and explicit restrictions. Never retain raw market rows or values.
5. Verify cleanup of all plaintext CSV/CSV.GZ files, decrypted monthly parts, temporary SQLite files and any transient keys, including on failed runs.

## Method
- Source lineage: reuse the exact source artifact and checks in `.github/workflows/export-repaired-dataset-offline.yml`; do not call any market-data API and do not refetch options.
- Decryption: execute the existing repository decryption tool using the existing `HF_TOKEN` secret only within the runner. Never echo or log the token. Use only `contents: read` and `actions: read` GitHub permissions where possible.
- Workflow supply chain: pin every external action to an official full 40-character commit SHA; add an allowlist guard; retain a manual dispatch trigger and an automated trigger limited to the developer branch. Avoid giving this job write permission to repository contents.
- Audit: execute `scripts/offline_dataset_preflight.py` with the expected digest, row count and column count explicitly set. Keep the temporary SQLite database on runner-local disk; verify it is removed.
- Report: upload a single metadata-only JSON artifact with short retention, and optionally commit a sanitized summary on the developer branch only after the run result has been validated. No plaintext dataset upload or commit.
- Cleanup: use an `if: always()` cleanup step; fail the job if any plaintext data file or SQLite temp file remains.

## Statistical and data-quality interpretation
This is not a prediction experiment. It generates no target labels, features, fitted models, forecast metrics or trading returns. It cannot establish:
- exact spot-option join correctness or the meaning of unmatched timestamps;
- session/calendar validity, OHLC semantics, market-data completeness or point-in-time safety;
- target timing, feature leakage, model generalization or economic profitability.

The scanner must report unestimable composite-key checks, incomplete keys, duplicate keys, and timestamp parse errors as non-pass/review states. The actual dataset header must be inspected before interpreting which composite key schema is appropriate for spot and option rows.

## Acceptance criteria
- Exact pinned source run/artifact lineage passes.
- The decrypted merged file matches expected SHA-256, row count and column count.
- Full gzip CRC/trailer and CSV structure pass.
- Synthetic CI passes on the exact workflow/scanner hashes.
- Tester issues an exact-SHA `PASS_WITH_SCOPED_RESTRICTIONS` for this data audit workflow.
- Workflow completes and publishes only a sanitized report, confirms cleanup, and logs all errors/outcomes.
- No fitting, holdout access, source request, or strategy/P&L work occurs in this gate.

## Bounded retry policy
Maximum two code/workflow repair submissions for this exact gate. A failed source artifact check, hash mismatch, missing secret, decryption error or cleanup failure is logged and fails closed. No alternate artifact or new source is silently substituted. At the retry limit, retain the failed report and stop this gate pending a new explicit proposal.

## Current blocker
The actual CSV.GZ is not present in the current assistant execution runtime. The existing encrypted one-time export artifact was encrypted to a one-time key whose private key was removed; it must not be treated as decryptable now. The proposal therefore regenerates the CSV from the original pinned encrypted derived artifact in a fresh runner, rather than attempting to reuse that one-time export artifact.

## Permissions requested from tester
Approve design only for implementing and testing this isolated audit workflow. Execution on the real dataset must remain separately gated by an exact-snapshot review. This proposal does not request model fitting, holdout access, new data acquisition or strategy/P&L permission.

Developer → Tester: Review source lineage, privacy/cleanup, action pinning, scanner semantics and bounded retry conditions. Return a scoped decision tied to this exact proposal blob.
Tester → Developer: Do not implement or run the real-data audit until this proposal has an exact-snapshot tester decision.
