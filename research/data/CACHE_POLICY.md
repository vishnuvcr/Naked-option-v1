# Data Cache and Snapshot Policy

## Principle

Do not re-download unchanged research data on every workflow run.

## Layers

1. **Git repository:** schemas, source manifests, transformation code, small synthetic fixtures, snapshot manifests and SHA-256 hashes.
2. **GitHub Actions cache:** raw-download cache keyed by source + period + manifest version.
3. **Hugging Face cache:** optional bulk-download accelerator using the repository secret `HF_TOKEN`; only used for public datasets already approved in the source manifest.
4. **Workflow artifacts:** validation reports and compact sample datasets.
5. **External source:** fallback only when the local/Actions cache has a miss.

## Immutable snapshot rule

Every accepted dataset snapshot gets:
- snapshot ID;
- source IDs;
- acquisition timestamp;
- date coverage;
- row count;
- SHA-256;
- parser/version;
- data-quality report;
- license/provenance note.

## Licensing rule

Large NSE-derived raw files are not committed blindly to Git. The repository stores manifests/hashes and the workflow cache/artifact policy stores data only where redistribution terms permit. If a source cannot legally be retained, the manifest records the reproducible acquisition recipe and hash rather than copying the raw dataset.

## Cache invalidation

A cache is invalidated only when one of:
- source URL/schema changes;
- parser version changes;
- source manifest changes;
- PIT/normalization rules change;
- a data-quality defect requires re-acquisition.
