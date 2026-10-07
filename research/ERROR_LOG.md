# Error Log

## 2026-10-07 — Phase 6 Run 37668947725
- **Category:** implementation/runtime
- **Component:** `scripts/run_phase6_novel.py` intraday cutoff construction
- **Symptom:** `AttributeError: 'DatetimeIndex' object has no attribute 'iloc'`
- **Location:** line 616 at developer commit 85c1b8db633dc1fb79f3426ab0b065e068efc2aa
- **Impact:** empirical suite terminated before producing Phase 6 artifact; no metrics accepted.
- **Root cause:** positional indexing API mismatch for a pandas DatetimeIndex.
- **Correction required:** use DatetimeIndex positional indexing correctly and add regression coverage.
- **Prevention:** tester gate blocks progression until corrected code passes regression and a fresh empirical execution completes.
