# Independent Tester Report — One-Use Duplicate Diagnostic Executor Workflow R2

Date: 2026-10-12  
Tester role branch: `phase-08-prediction-tester`  
Developer role branch: `phase-08-prediction-developer`

## Decision

**PASS_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_ONLY.**

This decision approves only the exact executor workflow and its request binding. It does **not** grant permission to retrieve or decrypt the source artifact, run the duplicate diagnostic, deduplicate rows, build empirical features, fit models, access a holdout, compute option P&L, or promote a strategy. Execution requires a separate, expiring, one-use authorization file on the tester branch.

## Exact snapshot pins

- Executor workflow: `.github/workflows/phase8p-duplicate-diagnostic-execution.yml`, blob SHA-1 `398063be2215dbed40c123521bf2868b0bcdb6a3`.
- R2 developer workflow-review request: `research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_REVIEW_REQUEST_R2_2026-10-12.json`, blob SHA-1 `252536eb06b0bf0d4d6f10d00e802cd481b3a94b`.
- Superseded R1 request blob: `fa3ae648d9da23649ad3db62c28456c032069a06`; R1 workflow-only decision remains in its original file and is not reused for R2.
- Approved R4 developer code commit: `8f8d513330d1cb064b4d3ffe9933f8e8014f2850`.
- R4 code-only decision blob: `469fe821a1f735051a9db0ea2a02f14881922dfc`.
- R4 code-review report blob: `0a1ede135fa30477ea8e4cd1643d395eead49a10`.
- R4 scope-only decision blob: `ee9fb7e4cc2030a532b358e450ca1e4f0325d91b`.
- Tester audit script: `scripts/phase8p_duplicate_diagnostic_execution_audit.py`, blob SHA-1 `daf4a4aeb65efaeebcf04b9d7593dc7bcb2fa58`.
- Tester review workflow: `.github/workflows/phase8p-duplicate-diagnostic-execution-review.yml`, blob SHA-1 `46e7f6cea78264e073ccc4598bbbc177f39a2976`.

## Independent verification

- Tester run [#38206600329](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206600329) completed successfully with **33/33 checks passed**, no failures.
- Review artifact [11727980780](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206600329/artifacts/11727980780), archive SHA-256 `0522c85f76d7c98b3ffe6475b1b97f5675ce3c4047819d3faa7665f21f030599`.
- The receipt reports `PASS_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_ONLY`, 33/33, `failures=[]`, `real_artifact_accessed=false`, `real_diagnostic_authorized=false`, and `model_fitted=false`.
- The receipt was downloaded and its archive SHA-256 checked; only reviewer JSON was downloaded, not market data.

## Scope of checks

1. The YAML is valid, has automatic push and manual dispatch triggers, explicit permissions, and a serialized concurrency group.
2. The workflow and the R2 request pin each other exactly. The request pins the R4 developer commit, R4 code-only decision/report, and R4 scope-only decision.
3. The workflow-only approval must be a distinct tester file that names the exact R2 workflow/request blob hashes. It cannot grant execution permission.
4. A second, separate developer-side execution authorization request is required and hash-bound. The workflow checks its pending status and exact pin/scope fields, computes its blob hash, and requires the final one-use tester authorization to include that same `execution_authorization_request_blob_sha1`. The nonce receipt also records that request hash.
5. The two approval files are distinct: workflow review PASS, then final one-use execution authorization. Missing or pending approvals safely no-op before cache restore/download; stale/mismatched values block.
6. The one-use nonce is checked against the permanent append-only developer ledger and committed to it before cache restore/download. The workflow rejects non-first attempts and any nonce already in the ledger.
7. The developer's exact approved code snapshot and file blobs are checked out/validated in a detached worktree before artifact retrieval. The encrypted source artifact ID and SHA-256 are verified before the diagnostic starts; the diagnostic verifies artifact identity before opening the archive.
8. The exact R4 manifest-bound signature/diagnostic is the only executable scope. No deduplication or model code is invoked.
9. `HF_TOKEN` is available only to the authorized diagnostic invocation, not to the approval gate or download/cache steps. Artifact redirect locations are captured rather than echoed; shell tracing is absent.
10. The output schema is allowlisted. Unexpected schema/status/source identity/permission flags fail closed. The raw diagnostic report is removed, and only the aggregate report plus receipts may be uploaded.
11. Deduplication, model fit, holdout access, external market-source requests, raw/decrypted upload, option P&L, and strategy promotion remain false throughout the executor workflow.

## Reviewer failure and correction retained

- R1's approval is not reused for the modified workflow. The developer added the hash of the separate execution authorization request into the eventual final authorization contract.
- The first R2 tester attempt [#38206552763](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206552763) returned 31/32. It found that the copied R2 request still named the R1 workflow-approval path. This was a real request-contract mismatch, not a reason to waive the check.
- The developer corrected the approval-path field, the tester audit gained an explicit R2 path assertion, and run #38206600329 passed 33/33.
- The executor workflow's R2 safe no-op run [#38206533110](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206533110) completed successfully. Its log says `SAFE_NOOP_BEFORE_ARTIFACT_ACCESS: independent tester has not approved this exact execution workflow`; the nonce ledger, cache, download and diagnostic steps were all skipped.
- Earlier schema failures #38205997072/#38206009396 remain documented as fail-closed, non-scientific evidence. No data was downloaded or decrypted in any of these attempts.

## Required next gate: explicit one-use execution authorization

The developer must submit a separate request file `research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTION_AUTHORIZATION_REQUEST_R1_2026-10-12.json` on the developer branch. It must pin:
- this R2 workflow blob and R2 request blob;
- this R2 workflow-only decision/report blob;
- R4 code-only decision/report and R4 scope-only decision blobs;
- the immutable developer code commit and source artifact ID/SHA-256;
- the frozen execution nonce `PHASE8P_DUP_DIAG_EXEC_20261012_R1_8F8D5133`;
- the exact allowed operation (one diagnostic read/scan producing aggregate hashes/counts only), expiration no longer than 24 hours, and `max_uses=1`.

Until the independent tester reviews that request, the final tester-side execution authorization file must not exist. After approval, the final authorization must include `decision=PASS_ONE_TIME_DUPLICATE_DIAGNOSTIC_EXECUTION_ONLY`, `single_use=true`, `max_uses=1`, timezone-aware issued/expiry timestamps within 24 hours, and the exact `execution_authorization_request_blob_sha1`. Only the three read/diagnostic permissions may be true: real artifact access, real artifact decryption, and real diagnostic execution. All other permission flags remain false.

## Authorization flags

- Executor workflow: **PASS for this exact R2 snapshot**
- Separate one-use execution authorization: **not yet granted**
- Source artifact access/decryption: **false**
- Duplicate diagnostic run: **false**
- Deduplication/model/holdout/P&L/strategy promotion: **false**

**Tester → Developer:** preserve R2 PASS and #38206552763 as a corrected request-contract failure; submit the separate pinned one-use diagnostic execution authorization request. Do not access the source artifact yet.

**Developer → Tester:** independently review the execution request and only create a final tester-side authorization if all pins, scope, nonce, expiry, and single-use controls match.