# GitHub Actions supply-chain policy

Date adopted: 2026-10-11
Scope: Phase 7 prediction-preflight workflows; use as the default for future research workflows unless a stricter repository policy exists.

## Requirements
1. External actions in new or modified workflows must be pinned to a full 40-character commit SHA from the action's official repository. Mutable branch/tag refs such as `@v7` or `@main` are not accepted.
2. Retain a human-readable release comment after each SHA. Record the upstream repository, release tag and commit SHA in the change log or policy allowlist.
3. Use the minimum `GITHUB_TOKEN` permissions. Synthetic preflight tests need only `contents: read`; do not provide market-data secrets, write permissions, plaintext datasets or credentials to this workflow.
4. Workflows must separate synthetic code tests from access to the actual dataset. The synthetic workflow must explicitly assert the real CSV, compressed CSV and local `.env` are absent.
5. Every workflow must support both its normal automated trigger and `workflow_dispatch`. A commit is not evidence of execution; record a verifiable Actions run ID and result.
6. Pin updates must be checked on the official action's repository and tested in a successful run before a workflow is considered gate-ready.

## Current Phase 7 preflight action allowlist
- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` — `v7.0.1`; upstream commit [3d3c42e5aac5ba805825da76410c181273ba90b1](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1).
- `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97` — `v7.0.0`; upstream commit [5fda3b95a4ea91299a34e894583c3862153e4b97](https://github.com/actions/setup-python/commit/5fda3b95a4ea91299a34e894583c3862153e4b97).

GitHub recommends full-length commit-SHA pinning because it is the way to reference action releases immutably; see the [official secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use). The two pins above were looked up against the official `actions/checkout` and `actions/setup-python` repositories on 2026-10-11.

## Enforcement and limits
`scripts/check_workflow_action_pinning.py` checks the current Phase 7 preflight workflow against the approved owner/repository/SHA/version allowlist. This is a static policy guard, not a proof that the upstream action is harmless or that CI ran. Keep the pin allowlist synchronized with this file and re-check upstream provenance on any update.

Developer → Tester: Verify the upstream pins, policy guard and exact workflow snapshot before accepting the CI gate.
Tester → Developer: Reject unpinned or unapproved actions and do not infer test success from commits alone.
