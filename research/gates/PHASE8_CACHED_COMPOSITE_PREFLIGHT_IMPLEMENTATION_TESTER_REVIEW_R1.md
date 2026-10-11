# Tester Implementation Review — Phase 8 Cached Composite Preflight R1

**Decision: PASS WITH SCOPED RESTRICTIONS — one metadata-only preflight**
Date: 2026-10-11  
Reviewed developer snapshot: `0bcb59f115bdf72474e5231076f31616242b66a9`  
Hosted contract run: [38161419163](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38161419163) — SUCCESS  
Proposal-level approval: `PHASE8_CACHED_COMPOSITE_PREFLIGHT_TESTER_DECISION_R1.json`

## Exact snapshot and test evidence

The following 15 required workflow/code/dependency/spec/data-contract blob IDs were queried from `phase-08-developer` and recorded exactly in the companion JSON decision. They cover the workflow, runner, execution engine, both of their test files, decryptor, encrypted-part validator and tests, request authorizer and tests, pinned dataset manifest, frozen forecast manifest, active Phase 8 method spec, cost schedule, and cryptography requirements.

The hosted run passed:
- encrypted-part bundle synthetic validation;
- exact reviewer-authorization and disabled-request tests;
- 4,800-parent-configuration grid completeness;
- existing execution-engine / transaction-cost arithmetic regressions;
- the no-refit runner synthetic self-test;
- exact Git blob pins for the 61-part dataset manifest and Run #994 forecast manifest;
- the authorization job in default-disabled mode.

The real cached-composite job was **skipped** because `requested=false`. This is intended. No cached composite artifact was downloaded or decrypted by this hosted run.

## Findings and restrictions

1. **Source identity remains pinned.** The proposal and implementation use existing composite artifact 11698879857 from run 38131641336, canonical CSV SHA-256 `cbd3c51bcaecef0572b1f0727b82ccc4f8f624469a256a6a440327c83b03204`, 8,999,865 rows and 61 encrypted parts. The active forecast artifact is Run #994 artifact 11638738288, previously independently accepted for reproducibility.
2. **Encrypted parts are validated before decryption.** The validator enforces the checked-in manifest identity, parent lineage, exact part set, safe filenames, byte sizes, encrypted SHA-256 values and expected total row count. The original decryptor was copied byte-for-byte from the already reviewed Phase 7 source; each decrypted gzip is revalidated against its pinned part digest before merging.
3. **Exact one-use marker is required.** The preflight job now commits a durable `PHASE8_CACHED_COMPOSITE_PREFLIGHT_CONSUMED_R1.json` marker to `phase-08-developer` before it opens plaintext or scans CSV content. A second run sees the marker and fails closed. The latest synthetic workflow test asserts ordering, marker existence logic, branch push, and that the marker does not itself match the workflow trigger paths.
4. **Snapshot reauthorization is repeated immediately before marker creation.** The job fetches the latest developer ref and tester decision, then requires the current blob IDs to match the exact reviewer decision. If the branch changes in flight, the marker push cannot fast-forward or authorization checks fail; it must not proceed to decryption.
5. **Least privilege is scoped.** Top-level workflow permissions are `actions: read`, `contents: read`; only the cached-preflight job has `contents: write` to commit the one-use marker. The secret is passed only to the decrypt step and never printed/written.
6. **Output/cleanup are bounded.** The workflow's output is a metadata-only artifact (report JSON and 4,800-row configuration matrix), with short retention. Decrypted monthly parts, merged CSV, encrypted download, forecast archive/unpacked forecast and report directory are removed in an unconditional cleanup step and checked for absence.
7. **It is not a trading test.** The runner is called only in `--mode preflight`, expects `FORECAST_PASS_OPTION_DATA_GATE_BLOCKED`, and asserts 4,800 configurations remain `INELIGIBLE`, strict fixed-contract readiness false, P&L false and strategy promotion false. No holdout access or new market-source requests are authorized.
8. The known daily H=1 source-alignment mismatch in an earlier attempt did not recur in the accepted forecast run and remains a logged anomaly.
9. Role-separated developer/tester branches exist, but this is a tester-role review within the same ChatGPT session, not an independent external human/model replication.

## Authorization

Approved only: change the request file's activation bit to request **one** metadata-only cached-composite preflight, copying the exact reviewed code blob dictionary into the request. Do not modify any reviewed blob. The authorization gate checks all reviewed files, immutable input identity and every P&L/holdout/new-source/promotion flag. If preflight fails, its durable marker remains consumed; a new versioned request/review is required rather than replaying R1.

**Not approved:** real option P&L, any opening of the final holdout, changing forecast methods/cost assumptions, provider downloads/source discovery, or strategy promotion.

**Tester → Developer:** Enable only the R1 metadata request with these exact blobs. Verify the hosted run commits the marker before decryption, checks all part hashes and canonical CSV SHA/row/type counts, emits metadata only and completes unconditional cleanup.

**Developer → Tester:** Submit the immutable run ID/artifact ID and exact report hashes. Do not interpret all-INELIGIBLE cells as a strategy result; they are a strict data-readiness gate.
