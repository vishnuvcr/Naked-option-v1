# Error Log

## 2026-10-07 — Phase 6 Run 37668947725
- Category: implementation/runtime
- Component: scripts/run_phase6_novel.py intraday cutoff construction
- Symptom: AttributeError: 'DatetimeIndex' object has no attribute 'iloc'
- Location: line 616 at commit 85c1b8db633dc1fb79f3426ab0b065e068efc2aa
- Impact: empirical suite terminated before artifact creation; no metrics accepted.
- Root cause: invalid positional indexing API for pandas DatetimeIndex.
- Correction: use DatetimeIndex[...] and add explicit regression coverage.
- Prevention: tester approval required before fresh empirical execution.
