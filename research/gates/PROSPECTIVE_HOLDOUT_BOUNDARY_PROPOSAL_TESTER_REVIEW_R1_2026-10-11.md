# Tester Review — Prospective Boundary Proposal R1

Date: 2026-10-11

**Verdict: PASS_WITH_SCOPED_RESTRICTIONS — design only**

Reviewed developer commit: `cd264e49e820dac7f55d587bccc4ee97c137b39a`

Exact reviewed blobs:
- Proposal: `8af859743457896591ed1f021abe546c24200069`
- Scope JSON: `4700a46ca15461c21c12a948767b3933254b67bd`

## Findings

The proposal specifies a deterministic chronological allocation of unique sessions (70% train, 15% validation, 15% sealed final period), label-endpoint purging, byte-offset boundaries, streaming integrity hashes, and sanitized outputs. It prohibits model fitting/scoring, source requests, and any strategy/P&L work.

The implementation must:
1. Use only row type, timestamp, session date, offsets and record lengths in application logic.
2. Never log raw rows or export price, quote, feature or label values.
3. Use documented rounding for the session allocation and never move boundaries after viewing outcomes.
4. Compute endpoint purging from session indices for every fixed horizon.
5. Hash the final byte range in a streaming digest without decoding/materializing it.
6. Fail closed on malformed rows, ambiguous ordering, or purge failures.

## Scope

Allowed: implement the scanner and synthetic tests on `phase-07-developer`, then resubmit exact hashes for implementation review.

Not allowed: scanning the cached dataset, reading market/holdout values, fitting/scoring models, new source requests, strategy/P&L or trading. This decision is design-only and does not authorize execution.

**Tester → Developer:** Implement the approved metadata-only design with synthetic fixtures only.
**Developer → Tester:** Submit exact implementation hashes and hosted synthetic results; do not infer execution permission.
