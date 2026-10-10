# PPR-4 Tester Review — User-Directed Dhan Acceptance and Open-Source Continuation Plan

**Review date:** 2026-10-11  
**Branch:** `phase-07-tester`  
**Submission:** `research/gates/PHASE7_PPR4_USER_DIRECTED_CONTINUATION_DEVELOPER_SUBMISSION.md`  
**Decision:** **REQUEST CHANGES — durable cache and acquisition budget need operational definitions**  
**Allowed now:** plan/policy amendments and offline tests only. No live requests, downloads, model-panel acceptance, fitting/scoring or holdout access are authorized.

## Exact reviewed pins

| Artifact | Developer blob SHA |
|---|---|
| User acceptance waiver | `7979a8e3212e874489c5f3b2e59f96307e436ae6` |
| Continuation policy | `bf153f8072190ee2efeeb4f1518a4fb00ed60c02` |
| Acquisition/fallback plan | `4091c54dd660d385583fb72b9eb354edf6aeaa87` |
| Source supplement | `067a967d07faa6a39d703c2832e5c221ae08efc1` |
| Validator / tests / workflow | `76dae37749a24ce1a510966f193d8747f5862669` / `8d93937d98e7afe79b6db694b2ab22dcd4c3bd41` / `2219fe01d0e8aa9ba39901f2eb76383bd7c3e989` |
| Research plan amendment | `c38df3ed1a30f278ec7b2b49929e2faf7d995ab3` |
| Developer submission | `bafd7e14e0cd35ec22737f3ffb637df35dcd6993` |

## Findings that pass

1. The Dhan user waiver explicitly accepts the sample for development use and waives further Dhan-versus-NSE/third-party price-value reconciliation. Historical tester records remain intact.
2. Missing-source handling is correctly family-local: try predeclared free alternatives, preserve lineage for composites, mark only the affected family/cells `NOT_ESTIMABLE` if exhausted, and continue unrelated work. No fabricated prices, zero-filled quotes or silent proxy renaming.
3. The prior one-use Dhan authorization remains spent and is not reused.
4. Token is planned as runtime-only; no token value is persisted or logged.
5. [Offline run 38078187293](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38078187293), trigger commit `a2fe4e2462060bee20bee16ade66169cea70a12d`, passed compilation, all four tests and the consistency validator. It did not access a data source, read market rows or fit models. Earlier failures remain logged.
6. The source plan keeps CDSL/SEBI FPI-only series distinct from DII and aggregate institutional-flow series.

## Required corrections (two P1 findings)

### P1 — Durable cache must not depend on expiring Actions artifacts

The plan allows large shards to be kept as workflow artifacts, but those are temporary and unsuitable as the authoritative project cache.

**Correction required:** define a persisted-cache hierarchy: (1) commit small redistributable data and manifests under `data/cache` where license/size permits; (2) store large redistributable objects in a durable repository-controlled location such as versioned GitHub Release assets or approved Git LFS objects and record immutable object URL/ID, hash, size, license, source revision, row/schema/date counts in Git; (3) treat Actions artifacts as temporary diagnostics only; (4) before download, verify and reuse persisted/cache-hit objects and only acquire missing/invalid approved shards; (5) when terms prohibit redistribution/storage, keep provenance and checksum metadata only and document that the data itself is not persistently cached.

### P1 — The exact manifest needs hard aggregate bounds, not just provider windows

A five-year rolling-options pull could expand greatly when multiplied by expiry types, sides and strikes even when each request respects the 30-day limit.

**Correction required:** specify that each exact source manifest must freeze, *before the first call*, maximum request count per source and aggregate run, per-response and aggregate bytes, maximum rows/shard where supported, date-shard ordering, and an explicit options inclusion grid (expiry selection, side and strike/relative-strike span). The initial live wave must have a bounded request budget. Hitting a cap means stop that source/family and use the next free fallback, not bypass a provider cap or silently expand scope. Any wider history/contract grid needs a new manifest and tester pass.

## Constraints retained

- This review does **not** reinstate cross-source price-value reconciliation; the user waiver remains in force.
- Missing data must not stop unrelated research or other feature families.
- The prospective holdout remains 252 future NSE decision-origin sessions plus a 10-session maturity tail, to be materialized after final freeze; this review does not change that design.
- No new data operation is approved here. Once the plan fixes these two P1 items and exact-snapshot offline tests pass, the next scope can be drafting the exact source-by-source acquisition manifest and guarded workflow only. Those exact artifacts require their own tester review before any live request.

**Decision: REQUEST CHANGES.** The user-directed research policy is acceptable in principle; make persistence and aggregate budgets enforceable before preparing the acquisition manifest.

**Developer → Tester:** Amend the two P1 items, preserve the no-cross-check waiver/no-source-stop rule, rerun the exact-snapshot tests and resubmit current protected-file pins.  
**Tester → Developer:** Do not run live requests from this plan-only review; re-review the corrected snapshot before authorizing the next drafting step.
