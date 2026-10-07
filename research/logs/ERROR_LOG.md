# Error Log

| Date | Phase | Error | Cause | Fix | Regression test |
|---|---|---|---|---|---|
| 2026-10-07 | 0 | Repository has no files/commits | New target repo is empty | Bootstrap governance files before branching | Pending |
| 2026-10-07 | 0 | Prior research repo and target repo differ | Project artifacts refer to an earlier market-inefficiency project | Treat prior artifacts as evidence inputs; rebuild canonical state here | Pending |

New errors must be appended, never overwritten.

| 2026-10-07 | 6 | Phase 6 reusable workflow invalid job-level hashFiles gate | Empirical job authorization used hashFiles in jobs.<job_id>.if, a disallowed Actions context | Workflow failure runs classified non-evidence; replace with workflow_call boolean input and caller-side authorization output | Pending developer correction/tester re-review |
