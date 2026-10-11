# Tester Review — MR-0 to MR-5 Feasibility Run Proposal R5

**Date:** 2026-10-11  
**Verdict:** PASS_WITH_SCOPED_RESTRICTIONS — proposal/design only  
**Developer proposal blob:** `915aeaca6564be7ed11299e93834d5c8b28aafa6`  
**Developer scope blob:** `bb08010a43dd499da38443b55d2fa77e9c210095`

## Review

The proposal defines a finite MR-0–MR-5 sequence for cached provenance, session/timestamp semantics, target endpoint feasibility, feature-family availability, split/leakage/holdout exclusion and final tester acceptance. It pins the canonical dataset identity and decoded content hash, uses observed NSE-session horizons (1/2/3/5/10), preserves the frozen direction-label tolerance, disallows new source requests and prevents model fitting/scoring or holdout observation access during feasibility work.

The proposal requires bounded-memory execution, fail-closed behavior for missing provenance or ambiguous timestamps, metadata-only artifacts, both Python sanitizer and JSON Schema validation, cleanup evidence, error/status/log updates, and a single bounded attempt followed by a tester decision.

## Restrictions

This is a **design approval only**. It does not authorize implementation execution against real data. Before any empirical run, the developer must submit exact hashes for the runner, tests, workflow, schema, dataset receipt and source/calendar manifest; the tester must review the exact snapshot and approve one-use execution. If cached calendar/source-vintage evidence is absent, the correct outcome is a blocked/not-estimable report, not external data collection. Holdout isolation must be proven from metadata; otherwise MR-4 blocks. Any implementation must actually enforce the report schema rather than merely storing it.

**Tester → Developer:** Implement only the approved bounded metadata-only feasibility runner and synthetic tests, then submit exact hashes for a new implementation review. Do not execute the real dataset yet.  
**Developer → Tester:** Independently review implementation hashes, workflow permissions, input lineage, report sanitizer/schema enforcement and cleanup behavior before authorizing one run.
