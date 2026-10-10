# PPR-4 Independent Tester Review — NIFTY 1-Minute Composite Acquisition

**Review date:** 2026-10-11  
**Reviewer role:** Independent tester  
**Branch:** `phase-07-tester`  
**Decision:** **PASS WITH SCOPED RESTRICTIONS**  
**Approved scope:** **EXACT MANIFEST AND ACQUISITION WORKFLOW ONLY**  
**Reviewed developer commit:** `98ef6ca039b19f0284981c57fc17b39124284869`  
**No further Dhan-versus-NSE/third-party price-value cross-check is required.**  
**No model fitting or holdout access is authorized.**

## 1. Decision

The exact acquisition manifest and the guarded acquisition workflow pass the defined pre-acquisition gate. The reviewer independently reconstructed the 30-day date partition and inspected all sub-manifests, including both split 2023 parts. The request grid contains exactly **8,601 unique requests**: 61 NIFTY spot requests and 8,540 rolling-option requests, with one occurrence of every declared option selector in each of the 61 date windows.

This is an approval to execute only the enumerated Dhan historical-data acquisition and produce the encrypted offline composite bundle. It is not an approval for modeling, parameter tuning, prediction scoring, holdout access, option P&L, or strategy selection.

## 2. Exact-snapshot pins

Each blob below is the Git blob SHA returned for the reviewed developer-branch file. The acquisition workflow must re-check these pins from the current `HEAD`; any changed pinned file invalidates this approval and requires a new tester review.

| File | Reviewed Git blob SHA |
|---|---|
| `research/gates/NIFTY_1M_COMPOSITE_REQUEST_MANIFEST.json` | `0c1a125ca2c16e72b07177bdebc403f50edf4cb7` |
| `research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2021.json` | `213bb4e0a4c2e73d0d5596d83bc7c49ac3f74d0a` |
| `research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2022.json` | `88930d72c27db2c8e7249931a5065b5a6b9f0db8` |
| `research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2023_A.json` | `b8152967f4d08417f765c300d9f1aef0e9420178` |
| `research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2023_B.json` | `009a460e8e831c70c9efec04f9c524b1d24f1c17` |
| `research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2023.json` (index only; not consumed by collector) | `ae076d2f8af47a415769b64e2080b9c7d93271cb` |
| `research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2024.json` | `a8be3617c9b68095b1455635af66280a9dba1166` |
| `research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2025.json` | `cc9bf87868d829068322af88bdcbeb9bc514d0b4` |
| `research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2026.json` | `0437eb1ddfbf9065dfea6cc0fd8c9ce3fc7108df` |
| `research/phase7/PPR4_DHAN_OPEN_SOURCE_ACQUISITION_PLAN.md` | `9f82add4eddbc3af91faf94da4d5f143c7e2d0ce` |
| `research/phase7/PPR4_USER_DIRECTED_DATA_CONTINUATION_POLICY.json` | `6dfd44e5a663d08c1f2e2a50669e30043d5bea18` |
| `research/gates/DHAN_SAMPLE_USER_ACCEPTANCE_WAIVER.json` | `7979a8e3212e874489c5f3b2e59f96307e436ae6` |
| `scripts/run_nifty_1m_composite_dataset.py` | `d639cd66dd3f427cd46c849fccb08cc9cf3933ab` |
| `scripts/decrypt_nifty_1m_composite.py` | `6ba27b65548b9197e0db35deeafcedbade6ca445` |
| `scripts/validate_nifty_1m_composite_manifest.py` | `39e71ec194dc81ee00a75330f805c7eb02a06d79` |
| `scripts/validate_nifty_1m_composite_approval.py` | `1a020d16d57396b8333c8432c1d33558c2e14e52` |
| `scripts/validate_ppr4_continuation_policy.py` | `d7de4479acf3750d8d37ee61fd0058d066f999e5` |
| `scripts/test_nifty_1m_composite_manifest.py` | `ecfe9841c21dd4ee2bc52ab1a8e447401739dc9c` |
| `scripts/test_nifty_1m_composite_dataset.py` | `bfdf8b05c17b6b98805f83028fc927dfb077b993` |
| `scripts/test_ppr4_continuation_policy.py` | `d21313a49548f96925498cbd10b2963f48be880b` |
| `requirements-composite.txt` | `8c74241f2035a3e388087078be5e5aaf846addca` |
| `.github/workflows/phase-07-nifty-1m-composite-manifest-tests.yml` | `1af2d77af8ddf8c828eef19aea04bdb9d4c36016` |
| `.github/workflows/phase-07-nifty-1m-composite-tests.yml` | `b4126d5c782c2a2f6566ffd06514bea8d2a08d64` |
| `.github/workflows/phase-07-nifty-1m-composite-live.yml` | `cf4d072b2f6530ffc89c65f2e849bb042e6f9cd5` |
| `.github/workflows/phase-07-ppr4-data-continuation-policy-tests.yml` | `16852f45c22b3165bd1020c5869df81643a5f48c` |

## 3. Independent request-grid audit

An independent check reconstructed the dates from 2021-10-11 inclusive to 2026-10-11 exclusive, advancing 30 calendar days each time, and inspected every request object in the root manifest's referenced files.

| Check | Result |
|---|---:|
| Non-overlapping 30-day date windows | 61 |
| Unique request IDs | 8,601 |
| NIFTY spot requests | 61 |
| Rolling-option requests | 8,540 |
| Option requests per window | 140 |
| Missing/duplicate option grid cells | 0 |
| Unexpected request family/endpoint/interval or per-response caps | 0 |
| Manifest validation findings | 0 |

The grid is explicitly limited to provider-supported **rolling ATM-relative historical data**, not every distinct listed historical option contract and strike:
- Historical window: `2021-10-11` through `2026-10-10`; end boundary `2026-10-11` is exclusive.
- Option endpoint: `POST https://api.dhan.co/v2/charts/rollingoption`, interval 1 minute, non-overlapping 30-day shards.
- Spot endpoint: `POST https://api.dhan.co/v2/charts/intraday`, interval 1 minute, non-overlapping 30-day shards (below the provider's 90-day maximum).
- For both `WEEK` and `MONTH`: expiryCode 0 covers ATM−10 through ATM+10; expiryCode 1 and 2 each cover ATM−3 through ATM+3; each selector is requested for CALL and PUT.
- Request/response budgets: 8,601 planned unique requests, no more than 100 retries total, no more than 8,701 wire requests overall, one retry per request, no faster than 2 requests/second, per-response byte/row caps and family aggregate byte caps.

The oversized 2023 file was turned into a small index and split into part A and part B to keep each active request list inspectable. The root manifest references only the two bounded parts; the index is not consumed by the collector.

## 4. Independent pipeline and workflow review

The reviewer checked the following properties in the collector, validator, tests and workflows:

1. The live acquisition workflow re-runs offline tests and validates the exact request grid, then fetches the tester branch and checks the tester report plus protected Git blob pins before spending the single-use acquisition approval. No source request occurs before the approval has been marked spent and pushed.
2. Manual workflow execution requires `confirm_live_acquisition=true`; automatic push execution also requires the exact approval-commit message and the developer branch.
3. Access credentials are provided only to the live collector step. The workflow checks secret configuration without printing secret contents. The data runner does not pass the Dhan token to other sources or serialize it into manifests/logs.
4. Raw responses and output CSV parts are encrypted at rest with AES-256-GCM; plaintext subscribed rows are not uploaded or committed to the public repository. The artifact upload pattern includes encrypted monthly CSV parts, not plaintext CSV scratch paths.
5. Cache objects are keyed to the exact request scope and checked against ciphertext/response hashes and schema. Invalid cache objects are removed and refetched within the cumulative request budget. A persistent append-only attempt ledger records request/retry spending and fails closed if corrupted.
6. Array-length mismatches, malformed data, duplicate timestamps, request-window violations, missing spot joins and source failures are surfaced to the coverage/error output. A family or request failure is reported locally; unrelated request keys continue where credentials and budgets permit.
7. The offline suite covers request-grid arithmetic, timezone handling, schema errors, exact timestamp joins, encryption/decryption round trips, Black–Scholes Greek signs, explicitly labelled proxy inputs, expiry-rule transition fixtures, request-ledger persistence/corruption handling and live-workflow gate ordering.
8. The Greek columns are not represented as Dhan-supplied historical Greeks. They use source inputs where available, otherwise visible proxy assumptions; Dhan's undocumented IV numeric unit is carried as a heuristic disclosure on calculated Greek rows. If an expiry cannot be mapped, the Greek result remains null with a reason code.

## 5. CI evidence

The following GitHub Actions runs completed successfully:
- [38082010348](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38082010348) — latest full parser/encryption/Greek/ledger regression before the manifest split.
- [38082127392](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38082127392) — after creating 2023 request part A.
- [38082132059](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38082132059) — after creating 2023 request part B.
- [38082152423](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38082152423) — after updating the root manifest to reference the split parts.
- [38082160780](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38082160780) — after turning the old 2023 oversized request list into a small index.
- [38081831327](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38081831327) — PPR-4 Greek-provenance policy validator/tests.

The final developer commit after these CI checks changes the README links only; all reviewed request-list, code, policy, validator, tests, requirements and workflow blobs remain pinned above. The README-only update did not change executable code or request scope.

## 6. Scoped restrictions and required data-disposition rules

This is a PASS for **the exact manifest and acquisition workflow only**. The developer may create the single-use approval file pinned to these reviewed Git blobs and initiate the enumerated Dhan requests.

- No Dhan-vs-NSE or third-party price-value cross-check is required; the user's explicit waiver stands.
- The workflow must not expand the request grid, widen any date window, add a new source/endpoint, increase budgets or change the option grid without a fresh exact-snapshot tester review.
- A successful API call grid does not mean every selector has observations. Valid empty responses, failed request IDs, missing timestamps and unjoined features must be reflected in the coverage report.
- If the final Dhan coverage is partial, do not relabel it complete. Mark the affected family/rows locally and prepare the free-source fallback requests for any recoverable missing feature family under a separate manifest/gate. Do not stop unrelated research merely because a source is unavailable.
- Derived Greek fields must include source/proxy status and per-row assumptions. No current Option Chain Greek snapshot may be copied backwards into historical rows.
- Persisted/cache and exported subscribed market rows stay encrypted. The user needs the same `HF_TOKEN` value used by the collector to decrypt locally; do not lose or rotate that value before downloading, decrypting and safely saving the artifact.
- This acquisition does not grant modeling, scoring, holdout, trading-strategy or profitability-claim permission.

**Developer → Tester:** This is the tester's signed decision for the pinned scope. After publishing this report, keep the tester branch read-only except for its own review/status/error/chat-log updates.  
**Tester → Developer:** Create the one-use approval with these exact blob pins, rerun the approval check on the developer branch, and only then start the guarded workflow. When the encrypted artifact and coverage report exist, submit the actual coverage/result snapshot for a new independent review before using the data in prediction experiments.
