# Error Log

| Date | Phase | Error | Cause | Fix | Regression test |
|---|---|---|---|---|---|
| 2026-10-07 | 0 | Repository has no files/commits | New target repo is empty | Bootstrap governance files before branching | Pending |
| 2026-10-07 | 0 | Prior research repo and target repo differ | Project artifacts refer to an earlier market-inefficiency project | Treat prior artifacts as evidence inputs; rebuild canonical state here | Pending |

New errors must be appended, never overwritten.

| 2026-10-09 | Governance/CI | Main-branch Research Protocol Check #997 failed before protocol/literature validation | The workflow invoked `scripts/validate_protocol.py` and `scripts/validate_literature_registry.py`, but the default branch did not contain these validator scripts or the literature registry even though phase branch did | Copied the exact phase-07-developer validator scripts and CSV registry onto main; rerun CI and verify repository contract passes | Pending hosted rerun |

| 2026-10-09 | Governance/CI | Protocol validation still failed after missing files were restored | The plan used “untouched forward validation” while validator required exact phrase “untouched holdout” | Added a precise terminology note defining the untouched holdout as the reserved forward segment, without changing selection rules | Fresh hosted protocol run pending |

| 2026-10-09 | Phase 7 | Run #925 independent audit found four repeated protocol/implementation mismatches | P10 abstention absent, regime training counted missing features, chronological block diagnostics skipped candidate masks, and family differentials treated non-evaluable rows as zero | Corrected the implementation and added regression tests without changing the frozen method specification; Run #994 is the fresh authorized execution | Tester must independently validate all 10 panels, 100 metric cells and 10 family tests before Phase 8 |


| 2026-10-09 | Phase 7 | Potential mismatch between frozen regime diagnostic count invariant and P10 abstention-masked chronological diagnostics | Frozen spec names P08/P09/P10 count equality; validator now enforces only P08/P09 because P10's abstention can empty a block; current shared regime diagnostics may still retain it | No post-hoc change made. Sent to independent tester for explicit adjudication against exact artifact; any spec change needs separate pre-registered approval before any fresh run | Run #994 pending, no result accepted; Phase 8 blocked |
