# Phase 2 Data Directory

This directory intentionally keeps small manifests/fixtures in Git and uses reproducible caches/artifacts for larger source files.

The canonical raw/derived dataset must never be used without a matching snapshot manifest and hash.

## Intended layout

- `data/manifests/` — snapshot manifests
- `data/fixtures/` — deterministic synthetic tests
- `data/cache/` — cache marker/configuration only
- `data/reports/` — compact validation reports
