# Continuation checkpoint

Registry integrity is blocked: 550/1000 method records are sharded, and config SHA-256 contract is unresolved. No fitting or holdout access.
# Continuation checkpoint

The developer branch now contains guarded automated repairs for the two registry integrity defects:

- Missing method shards are generated from the canonical master only after validating the exact 1,000 ordered PM0001–PM1000 IDs. Existing shards are compared to their master slices and never overwritten if mismatched.
- Config SHA-256 semantics are now explicit: exact committed shard file bytes. Digests are regenerated only after record count, unique-ID, and first/last-ID checks.

Next gate: confirm the hosted integrity audit passes, inspect its pinned artifacts, then obtain independent tester approval. No empirical fitting or holdout access until that gate passes.
