# Independent Tester Decision — One-Use Duplicate Diagnostic Execution Authorization R1

Date: 2026-10-12  
Decision: **PASS_ONE_TIME_DUPLICATE_DIAGNOSTIC_EXECUTION_ONLY**  
Reviewer role: isolated `phase-08-prediction-tester` branch

## Exact request and approval chain

- One-use developer request: `research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTION_AUTHORIZATION_REQUEST_R1_2026-10-12.json`, blob `bfb186fba597acdd831f8d854471d9b6d0adde36`.
- Executor workflow: `.github/workflows/phase8p-duplicate-diagnostic-execution.yml`, blob `398063be2215dbed40c123521bf2868b0bcdb6a3`.
- Exact executor workflow request R2: `research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_REVIEW_REQUEST_R2_2026-10-12.json`, blob `252536eb06b0bf0d4d6f10d00e802cd481b3a94b`.
- Independent workflow-only decision R2: `research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_TESTER_DECISION_R2_2026-10-12.json`, blob `8d39ad104c519b79bfe47f6731bac101a0798347`; report blob `08db2668f24ddc6b24c24ebeb38d74c3ea39620d`.
- R4 code-only decision blob `469fe821a1f735051a9db0ea2a02f14881922dfc`; R4 scope-only decision blob `ee9fb7e4cc2030a532b358e450ca1e4f0325d91b`.
- Approved developer implementation commit: `8f8d513330d1cb064b4d3ffe9933f8e8014f2850`.
- Input artifact: Actions artifact ID `11723198817`; expected ZIP SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`.

## Review checks

The execution request is in `PENDING_ONE_TIME_EXECUTION_AUTHORIZATION` state; its request-level permissions are all false. The workflow-only decision expressly does not grant execution. The executor requires this separate tester-created final authorization and checks its exact request/workflow/decision/code/artifact/nonce pins and expiry before it can set `run_authorized=true`.

The authorization is limited to a single read/decryption of the pinned encrypted composite artifact solely to run the exact R4 hash/count diagnostic. It may emit aggregate counts, schema/signature hashes, and conflicting column names only. It may not delete, deduplicate, canonicalize, or write source records. It may not construct features, fit any model, read a holdout, request outside market data, calculate option P&L, or promote a strategy. No raw rows, keys, contract identifiers, prices, features, labels, decrypted tables, or source ZIP may be uploaded.

A unique nonce `PHASE8P_DUP_DIAG_EXEC_20261012_R1_8F8D5133` is valid once only. The executor rejects workflow reruns and previously consumed nonces, checks and commits the nonce to a permanent developer-branch ledger before cache restore/download, then verifies the pinned artifact digest and exact code snapshot before the scan. The current pre-authorization run #38206772233 completed safely with every data step skipped; it is not a data result.

## Authorization window

- Issued: `2026-10-12T05:12:44Z`
- Expires: `2026-10-12T17:12:44Z`
- Maximum uses: 1
- Single use: true

## Decision

The one-use authorization is **approved** for this exact execution bundle, and for no other code, artifact or purpose.

Permission flags: real artifact access = true; real artifact decryption = true; pinned duplicate diagnostic = true; deduplication = false; model/feature fitting = false; holdout access = false; external market-source requests = false; raw/decrypted data upload = false; option P&L = false; strategy promotion = false.

**Tester → Developer:** trigger only the pinned workflow with this exact authorization. Preserve the permanent nonce ledger and the complete aggregate receipt. After completion, submit the report hash and aggregate report for a new independent data-result gate. Do not fit a model yet.

**Developer → Tester:** run the one-use workflow only; then stop before any feature preflight/model fit and return the exact diagnostic report artifact ID, ZIP digest, internal report SHA-256 and sanitized aggregate contents for the next tester gate.
