# Receipt publisher synthetic CI submission

Date: 2026-10-11
Scope: test only the sanitized report publisher, its schema allowlist and workflow permission/action policy. No market-data download, decrypt, model fitting or strategy execution is in scope.

The workflow publishes a receipt only after a completed audit run, and its output is a single metadata-only JSON file on `phase-07-developer`. It uses the built-in `GITHUB_TOKEN` with `actions: read` and `contents: write` because a cross-branch receipt commit is its sole write operation. The publisher validates report fields against an allowlist before committing.

Developer → Tester: Review exact source/workflow/test hashes and the successful synthetic CI receipt.
Tester → Developer: Reject any extra secret, unpinned action, broad write path or report field outside the allowlist.
