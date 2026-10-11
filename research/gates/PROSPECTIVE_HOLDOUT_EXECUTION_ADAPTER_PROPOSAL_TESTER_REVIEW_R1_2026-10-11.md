# Tester Review — One-Use Metadata Scan Adapter Proposal R1

Date: 2026-10-11

**Verdict: PASS_WITH_SCOPED_RESTRICTIONS — design only**

Reviewed developer commit: `50bffc2855ee3ec08a6a73e023ade71127c977fb`

Exact reviewed blobs:
- Proposal: `59ce8b873a2bd99734196f7c0526ea49db8151ca`
- Scope JSON: `e69b679fe5142f37cfd320b43ad3ee39c8f35e17`

## Findings

The design separates implementation approval from a one-use execution decision and requires the authorization marker to be persisted before opening the cached file. It restricts application logic to session/timestamp metadata, offsets, row counts, and streaming byte hashes. It also makes failures consume the authorization rather than silently retrying.

## Implementation conditions

1. The workflow's write permission must be limited to `phase-07-developer` and only the consumed-marker path; do not grant broad repository write access to the scanner process.
2. Marker creation must be atomic. If the push loses a race or the current branch head changes, abort before opening the dataset.
3. Validate the exact scanner, tests, schema, workflow, dataset, calendar and input-manifest hashes before marker creation.
4. The marker must not include raw rows, feature values, quotes, labels, secrets, or other payloads.
5. Keep the CLI disabled in the synthetic workflow. The workflow must require a fresh, exact-hash tester execution decision distinct from this design pass and from the implementation pass.
6. The dataset scan may only generate the sanitized metadata boundary manifest. It cannot authorize model fitting or holdout-value use.

## Decision

**Allowed:** implement the adapter and synthetic tests on the developer branch; submit exact hashes for implementation review.

**Not allowed:** scanning the cached composite or accessing market/holdout values. This decision is design-only.

**Tester → Developer:** Implement the constrained adapter and prove replay/race protection in synthetic tests.  
**Developer → Tester:** Submit exact hashes and hosted CI evidence; do not run the cached file before a separate execution decision.
