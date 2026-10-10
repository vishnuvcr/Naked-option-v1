# PPR-4 Tester Review 2 — Dhan-First Composite Dataset Plan

**Review date:** 2026-10-11  
**Branch:** `phase-07-tester`  
**Decision:** **PASS WITH SCOPED RESTRICTIONS — PLAN AND POLICY ONLY**  
**Allowed next step:** prepare the exact source-by-source acquisition manifest, resumable collector/exporter workflow, and offline tests, then submit that exact snapshot to the tester. This report does not authorize the live requests.

## Exact reviewed developer snapshot

| Artifact | Blob SHA |
|---|---|
| User Dhan-acceptance waiver | `7979a8e3212e874489c5f3b2e59f96307e436ae6` |
| Continuation policy | `21b3ea61c71e23b727dfba6aea5c3767fae31a62` |
| Dhan-first acquisition/fallback plan | `965f553461f56026d79764540d0b9c38403a2e6e` |
| Source supplement CSV | `067a967d07faa6a39d703c2832e5c221ae08efc1` |
| Validator | `87093742919099604dacecb640ea8d5a6b242a07` |
| Regression tests | `4a3fdb6f2c31ad5dc616b27eeba732dafb708ec0` |
| Offline workflow | `2219fe01d0e8aa9ba39901f2eb76383bd7c3e989` |
| Submission | `9408ca8182d005014baa2557d17d57520c06363c` |
| Developer branch head | `e0e5230c04ec6c4db971d7edd3b62f217d944545` |

## Independent validation

1. The Dhan value cross-check waiver is explicit and does not erase/rewrite the earlier tester report. No further Dhan-vs-NSE/third-party price-value reconciliation is required for accepting Dhan output under the user's directive.
2. Source absence is a local fallback/coverage issue, not a global stop. Free alternatives are ordered before paid sources. FPI-only sources are not renamed as DII or total institutional flow. Missing values are never automatically converted to prices/quotes of zero.
3. The durable-cache defect is resolved: Git cache for smaller redistributable objects, repository-controlled versioned Release/LFS for larger redistributable objects, provenance-only where storage is prohibited, and Actions artifacts explicitly temporary. Cache hits must be verified and reused before downloads.
4. The parent plan freezes numerical request/byte/row budgets and a deterministic options grid. The arithmetic checks: 61 30-day date chunks × 2 expiry flags × 3 expiry codes × 11 relative strikes × 2 option types = **8,052** potential rolling-option requests, below the **8,100** cap. With 70 intraday, 40 daily and at most 20 other-source requests, the upper sum is 8,182, below the 8,250 daily Dhan-plan ceiling. A future exact manifest must enumerate the actual request keys and may choose a strictly smaller grid.
5. [Offline run 38078480503](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38078480503) passed the local policy validator and all four tests at branch head `e0e5230c04ec6c4db971d7edd3b62f217d944545`. It made no source requests and opened no market rows.
6. The plan correctly separates historical option information from Greeks: the rolling historical endpoint documents OHLC/IV/OI/volume/strike/spot/timestamps but not stored historical delta/gamma/theta/vega. Those Greek fields must either be derived from the historical inputs using a disclosed, versioned model and effective-dated expiry/rate assumptions, or remain null where required inputs are unavailable. Current Option Chain Greeks must not be backfilled as historical values.

## Scope of this PASS

The developer may now draft:
- a machine-readable exact request manifest with explicit date shards, response budgets, options grid, cache targets, retries disabled by default, source fallback rules and source/family-local failure outcomes;
- collector code that appends/merges chunks, persists immutable shard manifests/checkpoints and reuses cache hits;
- a normalized long-form CSV exporter plus a CSV manifest/coverage report;
- offline mocked tests for chunk boundaries, exclusive end-date, array-length mismatches, duplicate keys, resume/cache logic, spot/option joins, missing Greek inputs and secret redaction;
- a guarded GitHub Actions workflow with manual dispatch and push-trigger support, but with live source execution still denied until its exact-snapshot tester gate passes.

## Conditions for future manifest review

The exact acquisition snapshot must distinguish historical Dhan rolling-option fields from model-derived Greeks, preserve time-zone-aware timestamp and session keys, enumerate the exact contract-relative strike/expiry/side keys, stay within the pinned budget, fail closed on schema corruption, and still continue unrelated sources after local failures. It must include a durable persisted-cache location; Actions artifacts alone are not enough.

No live request, dataset publication, model fit, holdout access, or option P&L is authorized by this plan PASS. The prior single-use Dhan request remains spent and must not be reused.

**Developer → Tester:** Draft the exact manifest/collector/exporter and test/workflow artifacts under these reviewed constraints, and resubmit hashes before any live request.  
**Tester → Developer:** This PASS authorizes drafting only. Independently test the exact acquisition snapshot next; only a subsequent gate may approve its enumerated live requests.
