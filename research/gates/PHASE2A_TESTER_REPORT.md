# Phase 2 Tester Report — Data Architecture / Initial Audit Gate

## Scope

Independent review of the Phase 2 developer package before empirical data acquisition proceeds.

## Checks

| Check | Result | Finding |
|---|---|---|
| Canonical schema defined | PASS | Underlying/options/contract/cross-market/flow/news layers include timestamps, availability and provenance. |
| PIT rules | PASS | Availability-time rule, contract existence, lot-size dating, global time zones, news publication and no-forward-fill controls are explicit. |
| Phase 2 exit criteria | PASS | Exit requirements are comprehensive and tester-dependent. |
| Free/official-first source hierarchy | PASS | Official NSE plus multiple free/open derived datasets are prioritized. |
| Hugging Face integration requirement | PASS IN POLICY | HF_TOKEN use is documented as an optional bulk-download accelerator. |
| Source discovery breadth | **REQUEST ADDITION** | BSE SENSEX and BSE derivatives sources should be represented explicitly for the user's requested NSE/BSE cross-market coverage. |
| Contract/lot-size source | **REQUEST ADDITION** | Add NSE contract-information/permitted-lot-size primary source explicitly; it is central to PIT contract mapping. |
| Actual raw-data cache implementation | **FAIL** | CACHE_POLICY promises raw-data caching, but the Phase 2 workflow currently caches only pip packages. No raw-source cache path is populated. |
| Immutable snapshot manifest generation | **FAIL** | Snapshot policy is specified but no script currently emits snapshot IDs, hashes, row counts and coverage. |
| Real source acquisition | **PENDING** | Current workflow probes endpoints and validates a synthetic PIT fixture, but it does not yet acquire an official NIFTY option archive sample. |
| Source probe logic | PASS WITH LIMITATION | Probes are small GET samples and do not validate file payload schemas. |
| Synthetic PIT test | PASS | Fixture contains both future-availability and future-observation cases. |
| Automatic/manual workflow | PASS | Push/PR + workflow_dispatch are present. |

## Gate decision

**REQUEST CHANGES — Phase 2A is not passed yet.**

The research architecture is acceptable, but the implementation must demonstrate actual source acquisition, raw-data caching, snapshot hashing, and BSE/lot-size source coverage before the data-engineering gate can pass.

## Developer-required corrections

1. Add explicit BSE SENSEX historical index and BSE derivatives historical sources to the source manifest.
2. Add NSE contract-information/permitted-lot-size source to the primary-source registry.
3. Implement a deterministic small official-source acquisition sample covering both the legacy F&O bhavcopy and post-July-2024 UDiFF formats. NSE officially states the old F&O bhavcopy was discontinued from 8 July 2024 and replaced by F&O-UDiFF Common Bhavcopy Final. citeturn197683search0turn197683search3
4. Add an actual `actions/cache` path for raw/cache data and make acquisition populate it.
5. Add a snapshot manifest generator with SHA-256, source ID, date, byte count, row count/schema evidence and parser version.
6. Preserve raw data outside Git history unless redistribution terms clearly permit committing it.

## Tester instruction to developer

Implement these changes as the next Phase 2 submission, run the deterministic validators, and resubmit the same branch for independent review. Keep all prior tester reports and error logs unchanged.
