# Phase 8P — Schema-Only Preflight Executor Proposal R1
Date: 2026-10-12
Role: developer branch
Status: **SUBMITTED FOR INDEPENDENT TESTER WORKFLOW REVIEW — NO ARTIFACT DOWNLOAD YET**

## Purpose
Add an automated, manually dispatchable workflow that runs only the already-reviewed schema/coverage-only preflight from the exact code snapshot accepted by code gate R2. It must not fit a model or compute prediction performance.

## Exact inputs
- Approved code snapshot: `a5a38e3592234aea9052e697416c8154c6f8e8f8`
- Module blob: `1de7f9e4bce0ee3ddf7dfa0d0b10282a7f0a5c8d`
- Code-only tester decision R2: `research/gates/PHASE8P_CODE_REVIEW_TESTER_DECISION_R2_2026-10-12.json`, blob `a23774dd9bf476f4e0fa3e1edf2d540bbd548c7b`
- Greek artifact ID 11723198817, SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`
- Forecast artifact ID 11638738288, SHA-256 `3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9`

## Flow
1. Push or manual trigger selects only this schema-only workflow.
2. Before data access, verify the exact workflow blob, a tester-owned workflow approval, the code-only tester decision blob, the immutable developer snapshot/module hash, and both artifact IDs/digests in the request.
3. Restore the encrypted Greek ZIP from the exact-digest cache; if the cache misses, download only that artifact through the GitHub Actions artifact API and verify SHA-256.
4. Download the exact frozen Run #994 artifact to ephemeral runner temp storage only; verify its immutable SHA-256. Do not cache this label/prediction bundle.
5. Run `--run-preflight` from a detached worktree at the exact approved code snapshot. The existing module's code gate checks the exact tester decision. Supply `HF_TOKEN` only as an environment secret for the existing decryption key derivation; never print it or pass it on the command line.
6. Persist only the aggregate preflight report and artifact hash receipt. Upload no ZIPs, raw rows, decrypted data, feature vectors, label arrays or keys. Remove forecast ZIP and temporary logs afterward; retain only the encrypted Greek ZIP in the Actions cache.
7. A BLOCKED report is a valid scientific outcome and must not be bypassed. A runtime failure uploads a sanitized BLOCKED receipt and fails the workflow.
8. A separate tester gate must independently inspect the exact report hash and determine whether the holdout/label-maturity/data-coverage contracts pass. No model fitting occurs in this workflow.

## Non-authorizations
No external market source calls (NSE, BSE, HF dataset refresh, Dhan or other vendor), no new data collection, no model fit, no protected holdout evaluation/metrics, no option P&L, execution/fees/slippage modelling or strategy promotion. This does not amend the approved research scope; it executes the pre-registered preflight gate.

**Developer → Tester:** review the workflow and proposal against the exact code decision, artifact pins, token handling, cache policy, fail-closed holdout/label rules, output paths and absence of any model-fit step. Approve executor workflow only or request changes.
**Tester → Developer:** do not create the authorized execution request or download the artifacts until this exact workflow blob receives PASS_PREFLIGHT_WORKFLOW_ONLY.
