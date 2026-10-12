# Independent Tester Report — R4 Manifest-Bound Duplicate Diagnostic Code Gate

Date: 2026-10-12  
Role branch: `phase-08-prediction-tester`  
Reviewed developer branch: `phase-08-prediction-developer`  
Exact reviewed developer commit: `8f8d513330d1cb064b4d3ffe9933f8e8014f2850`  
Developer request: [PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_REQUEST_R4_2026-10-12.json](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-developer/research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_REQUEST_R4_2026-10-12.json)

## Decision

**PASS_FOR_DUPLICATE_DIAGNOSTIC_CODE_ONLY.**

This decision approves the exact R4 implementation and synthetic/static checks only. It does **not** authorize downloading, opening or decrypting the pinned Greek artifact; running the diagnostic over real rows; modifying/deduplicating source records; building features from real data; fitting models; opening a holdout; calculating option P&L; or promoting a strategy.

## Exact developer snapshot and source pins

| File | SHA-1 blob |
|---|---|
| `scripts/phase8p_greek_prediction.py` | `3358381d64b3e675e49687fa5d34df44d8a9c984` |
| `scripts/test_phase8p_greek_prediction.py` | `198e731e9e5f5dd011370cd6f656fe27e97c6ca5` |
| `.github/workflows/phase8p-greek-prediction.yml` | `5d413bc4a0d6fb63c89775a153af33f270853b8f` |
| `scripts/phase8p_duplicate_key_diagnostic.py` | `6e4484cc5893bae27966c2b8d7561c2435e00023` |
| `scripts/test_phase8p_duplicate_key_diagnostic.py` | `232de27ff2c26a4ad228ae179d8ec5565ac97eeb` |
| `.github/workflows/phase8p-duplicate-diagnostic-synthetic.yml` | `08cbb1519666d25186b684c000a1df478ad3329d` |

R4 scope amendment and decision pins:
- Developer scope proposal blob: `1ea9bca882b53fd2853829137aba2d521023b3bd`.
- Independent scope-only tester decision blob: `ee9fb7e4cc2030a532b358e450ca1e4f0325d91b`.
- Independent scope-only tester report blob: `3305ed3a2a6617441c9ccaf73764d9edf0e53b5f`.
- Scope decision is `PASS_SCOPE_AMENDMENT_ONLY_WITH_RESTRICTIONS`; it explicitly authorizes scope/implementation only, not real-data execution.

## Verification evidence

- Core synthetic workflow [#38205169093](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205169093) succeeded on the pinned developer commit.
- Diagnostic synthetic workflow [#38205127423](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205127423) succeeded on the pinned diagnostic and test blobs.
- Independent tester workflow [#38205506563](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205506563) completed with **29/29 checks passing**, decision `PASS_FOR_DUPLICATE_DIAGNOSTIC_CODE_ONLY`, and no failures.
- Receipt artifact: [11726624314](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205506563/artifacts/11726624314); SHA-256 of the uploaded artifact ZIP: `464d9bffb484210a3aac1e821b78828b5016394afbf07740cd1fc0e566591bac`.

## Independent findings

1. **Schema is manifest-bound.** The code validates the manifest's ordered `columns` list and requires each encrypted part's ordered header to match it exactly. It fails closed on missing required semantic fields, duplicate/invalid column names, and reordered/extra/missing headers.
2. **Timestamp representation is conditional, not guessed.** At least one of `timestamp_utc` / `timestamp_ist` must exist; each present representation must normalize to the source epoch. Tests allow a one-representation schema and reject timestamps that disagree with the epoch.
3. **Signature is dynamic.** Every actual manifest column participates in the economic signature except the four approved collection-provenance variance fields when present: `source_request_id`, `requested_relative_strike`, `request_scope_sha256`, `response_sha256`. An otherwise unmodeled extra column is tested and conflicts fail closed.
4. **Economic key/time contract is explicit.** The key is underlying, Greek valuation instant, normalized expiry date, actual returned strike and normalized option side; the registered valuation offset must be 60 seconds. Seconds/milliseconds normalization and provenance-only repeat rows are covered.
5. **No data editing/output path in the reviewed diagnostic.** Static checks found no external market-data/network-source imports, no source-row/contract-key serialization, and no deduplication operation. Synthetic output reports aggregate counts, hashes and conflicting column names only.
6. **Repeatability and no-leak tests.** Synthetic tests exercise conflicts, provenance-only exact repeats, malformed/reordered headers, UTC/IST consistency, timestamp normalization, row/part-order permutation and aggregate-only output.
7. Both core and diagnostic synthetic test commands passed inside the isolated detached worktree for the exact developer commit. No real market artifact was downloaded or decrypted during this review.

## Failures preserved as tester-harness non-evidence

- [#38205280084](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205280084) audited the old R3 request because its push occurred before the workflow path was switched to R4; the pin mismatch did not constitute an R4 code review.
- [#38205378764](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205378764) and [#38205429386](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205429386) each passed 28/29 checks. The sole failing condition was a brittle tester-source assertion expecting literal wording that did not match the synthetic test source. The assertions were corrected and the final independent run #38205506563 passed 29/29.
- Earlier developer CI failures [#38204971703](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204971703) and [#38205048202](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205048202) were test-fixture/test-contract mismatches before the revised synthetic tests were in place; subsequent pinned synthetic runs passed. They remain historical non-evidence, not deleted.

## Mandatory next gate before real data

The code-only PASS is not a runtime authorization. The next developer phase must implement and submit a **separate one-use execution workflow/request**, pinned to this report and decision, the exact reviewed developer commit and blobs, artifact ID/digest, expected aggregate-only output schema, explicit no-replay rules, and disabled model/holdout/P&L permissions. That executor workflow must independently pass tester review **before** downloading/opening the artifact. The diagnostic report must itself be independently reviewed before any feature preflight or model fit is allowed.

The pinned Greek artifact remains ID `11723198817`, SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`. The artifact was not accessed as part of this review. Runtime and peak memory for the full scan are unmeasured.

## Authorization flags

- Real artifact access/decryption: **false**
- Real duplicate diagnostic execution: **false**
- Deduplication: **false**
- Feature preflight / model fit: **false**
- Holdout access: **false**
- External market-source requests: **false**
- Option P&L / strategy promotion: **false**

**Tester → Developer:** preserve this code-only PASS and all failed-run history. Submit the separate pinned one-use executor workflow/request; do not access the encrypted artifact before the tester approves that exact executor.

**Developer → Tester:** independently review the exact execution workflow and authorization bundle, including no-replay, hash pins, access ordering, aggregate-only output and closed model/holdout/P&L flags. If any bypass remains, request changes and keep the scan blocked.