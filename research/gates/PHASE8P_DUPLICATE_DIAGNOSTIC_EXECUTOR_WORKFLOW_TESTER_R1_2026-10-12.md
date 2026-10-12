# Independent Tester Report — One-Use Duplicate Diagnostic Executor Workflow R1

Date: 2026-10-12  
Reviewer role branch: `phase-08-prediction-tester`  
Developer role branch: `phase-08-prediction-developer`

## Decision

**PASS_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_ONLY.**

This permits use of the exact reviewed executor workflow only after a distinct, separately pinned one-use execution authorization is approved. It does **not** authorize artifact retrieval, decryption, diagnostic execution, deduplication, feature construction, model fitting, holdout access, option P&L, or strategy promotion.

## Exact snapshot pins

- Executor workflow: `.github/workflows/phase8p-duplicate-diagnostic-execution.yml`, blob SHA-1 `e1832072723a46a2688af83eb0346207325069a0`.
- Developer workflow-review request: `research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_REVIEW_REQUEST_R1_2026-10-12.json`, blob SHA-1 `fa3ae648d9da23649ad3db62c28456c032069a06`.
- Approved R4 developer code commit: `8f8d513330d1cb064b4d3ffe9933f8e8014f2850`.
- R4 code-only decision blob: `469fe821a1f735051a9db0ea2a02f14881922dfc`.
- R4 tester report blob: `0a1ede135fa30477ea8e4cd1643d395eead49a10`.
- R4 scope-only decision blob: `ee9fb7e4cc2030a532b358e450ca1e4f0325d91b`.
- Tester audit script: `scripts/phase8p_duplicate_diagnostic_execution_audit.py`, blob SHA-1 `378c342a21b48bdaa348b3194a38e06ce2ef8d58`.
- Tester review workflow: `.github/workflows/phase8p-duplicate-diagnostic-execution-review.yml`, blob SHA-1 `46e7f6cea78264e073ccc4598bbbc177f39a2976`.

## Independent execution evidence

- Tester review run [#38206319754](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206319754) completed successfully: **31/31 checks passed**, no failed checks.
- Receipt artifact [11727591616](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206319754/artifacts/11727591616), ZIP SHA-256 `3009787cfb7abf9f04ca2abf695d1ffabbd9c77e26e2fe0b9303beda48f56d11`.
- I independently downloaded the *review receipt only* and verified its local archive SHA-256. The JSON report in the archive says `PASS_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_ONLY`, `checks_passed=31`, `checks_total=31`, `failures=[]`, and `real_artifact_accessed=false`. This archive contains no market data.

## Checks verified

1. The YAML parses; the workflow includes a manual dispatch button and its automatic developer-branch path trigger. The manual boolean defaults to false.
2. The executor is serialized through a concurrency group and explicitly states least-privilege Actions permissions.
3. The exact workflow and request blob pins match the submitted request. The R4 code-only PASS and R4 scope-only decision/report hashes match the tester branch’s immutable files.
4. The workflow requires two distinct approvals in sequence: (a) a workflow-only tester PASS pinned to the exact workflow/request/code/artifact; and (b) a separate one-use execution authorization. Workflow review approval explicitly cannot grant artifact access.
5. Missing/pending workflow approval or missing/pending execution authorization leads to a successful safe no-op with `run_authorized=false`; stale or mismatched decisions fail closed before cache restoration or artifact download.
6. The fixed developer commit and diagnostic blobs are checked before data access. The exact source artifact ID and ZIP SHA-256 are checked before running the diagnostic. The diagnostic itself verifies the pinned identity before opening the archive.
7. The single-use nonce is checked against the permanent developer-branch ledger, and the ledger commit is placed before cache restore/download. Workflow reruns and previously consumed nonces are rejected.
8. The pinned encrypted ZIP is the only item stored in the repository-scoped artifact cache. The pinned code is checked out in a detached worktree before data access.
9. `HF_TOKEN` is injected only into the already-authorized diagnostic step; it is not available to the gate, download, or cache steps. The signed redirect location is captured by the shell but not echoed. No shell tracing is enabled.
10. Output uses an explicit schema allowlist, rejects schema drift, removes the raw diagnostic JSON, and uploads only the allowlisted aggregate report and hash receipts. No raw rows, option-contract keys/identifiers, prices, labels, features, plaintext tables, URLs or tokens are intended in output.
11. Model fit, holdout, external-source access, deduplication, option P&L, strategy promotion and raw/decrypted-data upload remain false.

## Safe no-op and failed-closed history

- Run [#38205955895](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205955895) completed safely with the workflow-review request absent. All cache, download and diagnostic steps were skipped.
- Run [#38206043280](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206043280) completed safely with the current review request present but the independent tester approval absent. Log: `SAFE_NOOP_BEFORE_ARTIFACT_ACCESS: independent tester has not approved this exact execution workflow`. All data-access steps were skipped.
- Runs [#38205997072](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205997072) and [#38206009396](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206009396) failed closed before data access due to initial request/schema pinning mistakes (the workflow expected a top-level nonce, then top-level decision/report/scope blob keys). Those request-contract mismatches were corrected, the failures were retained, and the corrected run #38206043280 safely no-opped. They are not empirical evidence and do not indicate artifact contents.

## Required next gate: one-use execution authorization

Before any real artifact access, the developer must submit a distinct request for **one** diagnostic execution. The tester must review that bundle independently and, if every pin and safeguard matches, create the execution authorization JSON on the tester branch. The authorization must:
- bind the exact workflow blob, exact executor request blob, this workflow-only decision blob, R4 code and scope decisions, developer code commit, artifact ID and SHA-256, and the frozen nonce;
- have `max_uses=1`, `single_use=true`, and a validity window no longer than 24 hours;
- set only real artifact access/decryption/diagnostic permission true, while keeping deduplication, feature/model fit, holdout access, external market-source requests, raw/decrypted-data upload, option P&L and strategy promotion false;
- be committed to the tester branch; the developer workflow must still check its exact blob before it may consume the nonce and retrieve the artifact.

## Authorization flags

- Executor workflow approval: **PASS, workflow only**
- Real artifact access/decryption: **false**
- Real diagnostic execution: **false**
- Deduplication: **false**
- Model fitting / holdout: **false**
- Option P&L / strategy promotion: **false**

**Tester → Developer:** preserve this exact workflow-only PASS; submit the separate one-use diagnostic execution authorization request. Do not download or decrypt the artifact yet.

**Developer → Tester:** prepare the execution authorization bundle pinned to this report/decision and all exact source/code/artifact/nonce hashes. Keep all data steps blocked until the tester separately approves that one-use request.
