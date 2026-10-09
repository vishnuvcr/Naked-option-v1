# Error Log

| Date | Phase | Error | Cause | Fix | Regression test |
|---|---|---|---|---|---|
| 2026-10-07 | 0 | Repository has no files/commits | New target repo is empty | Bootstrap governance files before branching | Pending |
| 2026-10-07 | 0 | Prior research repo and target repo differ | Project artifacts refer to an earlier market-inefficiency project | Treat prior artifacts as evidence inputs; rebuild canonical state here | Pending |

New errors must be appended, never overwritten.

| 2026-10-09 | Governance/CI | Main-branch Research Protocol Check #997 failed before protocol/literature validation | The workflow invoked `scripts/validate_protocol.py` and `scripts/validate_literature_registry.py`, but the default branch did not contain these validator scripts or the literature registry even though phase branch did | Copied the exact phase-07-developer validator scripts and CSV registry onto main; rerun CI and verify repository contract passes | Pending hosted rerun |

| 2026-10-09 | Governance/CI | Protocol validation still failed after missing files were restored | The plan used “untouched forward validation” while validator required exact phrase “untouched holdout” | Added a precise terminology note defining the untouched holdout as the reserved forward segment, without changing selection rules | Fresh hosted protocol run pending |
