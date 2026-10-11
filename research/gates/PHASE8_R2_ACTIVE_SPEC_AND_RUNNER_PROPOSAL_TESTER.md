# Tester Review — Phase 8 R2 Active-Spec and Runner Proposal

**Decision: PASS WITH SCOPED RESTRICTIONS — proposal only**  
Date: 2026-10-11  
Developer proposal snapshot: `01f5fd01e5c9ab556d4036986718b8db3121f239`  
Proposal: [PHASE8_R2_ACTIVE_SPEC_AND_RUNNER_PROPOSAL.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-developer/research/gates/PHASE8_R2_ACTIVE_SPEC_AND_RUNNER_PROPOSAL.md)  
Scope JSON: [PHASE8_R2_ACTIVE_SPEC_AND_RUNNER_SCOPE.json](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-developer/research/gates/PHASE8_R2_ACTIVE_SPEC_AND_RUNNER_SCOPE.json)

## Independent findings

1. **R2 identity is coherent.** The proposal carries the accepted Run #994 identity: workflow run 37957677656, source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`, forecast artifact ID 11638738288, archive SHA-256 `3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9`, embedded manifest SHA-256 `f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091`, aggregate SHA-256 `96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39`.
2. The earlier R1 Run #654 artifact remains historical lineage. It is appropriate to correct active spec prose via a versioned addendum so older approval records are not silently overwritten.
3. **P10 abstention must be added.** The exact Run #994 source declares P05 [0.45, 0.55], P06 [0.40, 0.60] and P10 [0.45, 0.55]. Current Phase 8 engine mapping only recognizes P05/P06. P10 values from 0.45 through 0.55 inclusive must be no-trade. Unit tests must check both boundary values and interior values.
4. The proposed composite identity agrees with the existing exact offline workflow: artifact 11698879857 from run 38131641336, gzip SHA-256 `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5`, canonical decoded CSV SHA-256 `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`, 8,999,865 rows, 47 columns, 61 encrypted monthly parts.
5. The proposal accurately retains known limitations rather than implying complete history: 19,021 unmatched OPTION rows across 421 timestamps; 24,847 weekend-review flags; masked invalid/missing spot and volume observations; and raw expiry/TTE/Greek/rate/dividend fields that are not source-populated. Rule-derived expiry/Greek/moneyness fallback must carry provenance flags.
6. Preserving all 4,800 configurations, four cost scenarios, Paytm Money fee fallback, holdout restrictions and the existing data-quality thresholds is appropriate. The output must keep the status of all cells and not discard failed/blocked configurations.
7. The official/secondary source sample audit is not a full contract-master or bid/ask-history proof. Q1/OHLC proxy results must stay **non-quote-executable** and cannot qualify for final strategy promotion on P&L alone.

## Restrictions / required implementation checks

- This review approves the **proposal only**. No code implementation has yet passed this review.
- The actual runner must validate its input hashes, load only saved R2 panels, use the correct P05/P06/P10 abstention rules, preserve point-in-time contract selection, enforce one-minute/15-minute execution windows, handle identical-vs-conflicting duplicate contract/timestamp records deterministically, and emit exactly 4,800 cell records.
- The cost tests must independently verify commission, dated transaction/IPFT, STT, SEBI fee, stamp duty, GST, Q1 spread and incremental slippage. The same cost scenario must not be counted twice in both fill prices and cost ledger.
- Missing/derived expiry and lot-size identity must be separately recorded. A proxy track may be exploratory only; it cannot be silently mixed with strict data-quality-passing rows or promoted as quote-executable.
- Real empirical option P&L remains disabled until the exact implementation/hash, synthetic CI, cached composite preflight and separate empirical-authorization file all pass.
- The earlier non-reproduced daily H=1 source-alignment failure remains a logged anomaly. The accepted forecast run passed, but the discrepancy must not be described as proven harmless.
- The reviewer is on the role-separated tester branch in the same connected ChatGPT session, not an external human/model instance.

## Authorization

**Authorized:** versioned R2 spec clarification and code implementation; synthetic runner testing and a metadata-only/validation dry-run that cannot emit empirical P&L.

**Not authorized:** real 4,800-cell P&L, holdout access, selection of a winner, or strategy promotion.

**Tester → Developer:** implement the versioned addendum and P10 abstention tests, submit exact code hashes, and keep empirical authorization false.  
**Developer → Tester:** independently recalculate cost arithmetic and grid completeness, verify the cache is the exact pinned artifact and verify that any proxy-only cell is explicitly labelled before considering the next gate.
