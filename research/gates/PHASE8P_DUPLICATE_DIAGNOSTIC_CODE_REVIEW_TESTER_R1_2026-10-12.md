# Independent Tester Report — Phase 8P Duplicate-Diagnostic Code Gate R1

Date: 2026-10-12  
Role branch: `phase-08-prediction-tester`  
Reviewed developer branch: `phase-08-prediction-developer`  
Exact developer commit: `aae250d8a34989ebe0bd901e1d6b7d9aa0ec5a5f`  
Pinned R3 request blob: `d2c4993315987523b569e122a3949967b87263e5`

## Decision

**PASS_FOR_DUPLICATE_DIAGNOSTIC_CODE_ONLY.** This is a code-and-synthetic-test approval for the hash/count-only duplicate diagnostic. It is not authorization to read/decrypt the real artifact, delete/deduplicate any records, run feature construction, fit a model, inspect the holdout, calculate option P&L, or promote a strategy.

## Exact snapshot reviewed

| Component | Path | Blob SHA-1 |
|---|---|---|
| Diagnostic | `scripts/phase8p_duplicate_key_diagnostic.py` | `3427c48dcd86207dbe0a22d41da15ffa1a59fa43` |
| Synthetic regression tests | `scripts/test_phase8p_duplicate_key_diagnostic.py` | `c1f3d1f86e728fc0a3ee3b28dcd58264767fb3b1` |
| Synthetic-only workflow | `.github/workflows/phase8p-duplicate-diagnostic-synthetic.yml` | `08cbb1519666d25186b684c000a1df478ad3329d` |
| Existing pinned prediction/encrypted-reader module | `scripts/phase8p_greek_prediction.py` | `410e1995d6093b959d4334ed678a588c146af5c2` |

The R3 request pins the existing source artifact as ID `11723198817`, SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`. This identity was reviewed as metadata only; the artifact was not accessed in this code gate.

## Verification evidence

- Developer synthetic workflow [#38204164532](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204164532) passed; its receipt identifies the synthetic-only result (artifact `11726546815`, receipt SHA-256 `79efe7183c8f7e95dbc4d0930e534e94522af3b7c16bf12b876f5b3a453847ff`).
- Tester audit [#38204532045](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204532045) completed successfully with **19/19 independent checks passing**. The tester receipt is artifact [11726911040](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204532045/artifacts/11726911040), ZIP digest `sha256:2c30e354268a4f9dacfb62edf13c2423f3c0c9f7c0ca0cbcbffa480ddf9b1c99`.
- The isolated tester job checked out the exact developer commit in a detached worktree and checked the diagnostic, tests, synthetic workflow and imported source module against the pinned blob hashes.
- Static checks and source review found no external market-source/network access in the diagnostic path, no raw-row/key output, and no deduplication operation. Artifact identity/hash verification is called before the authenticated encrypted-part reader.
- Synthetic tests exercised exact duplicate groups, conflicting duplicate groups, seconds/milliseconds timestamp normalization, invalid schema fail-closed behavior, and the absence of deduplication. Both the module self-test and regression suite passed.
- The key fields were compared with the existing feature-builder duplicate-key tuple: `timestamp_epoch`, `expiry_date`, `expiry_flag`, `expiry_code`, `returned_strike`, and `option_type`. The diagnostic preserves separate raw-key and normalized-key summaries and hashes full rows for classification.

## Failures preserved as non-evidence

1. Tester run [#38204120560](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204120560) stopped before review because the tester workflow still loaded the R2 request path instead of the submitted R3 request. No code review was performed in that run.
2. After correcting the request path, tester run [#38204512622](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204512622) stopped before review because a redundant `cp` attempted to copy the request file onto itself. No code review was performed in that run.
3. The tester-owned workflow was corrected on the tester branch. Fresh run #38204532045 then passed all 19 checks. These earlier failed workflow runs remain in the historical record and are not treated as developer-code failures or scientific evidence.

## Scope and required next gate

The diagnostic is approved only to support a separately authorized, one-use duplicate classification run against the exact pinned encrypted artifact. Before that run, the developer must submit a new authorization request that pins this tester decision, the exact developer commit/blob hashes, artifact ID and digest, expected output schema, and the one-use/no-replay rule. The independent tester must validate that exact request before the diagnostic can run.

The diagnostic output must remain aggregate-only: row/group counts, hash comparisons, artifact identity and provenance metadata. No raw keys, contract identifiers, row values or decrypted tables may be emitted or uploaded. No records may be silently removed. After the run, an independent tester must review the exact report hash and duplicate classifications before the schema/coverage preflight can be reconsidered.

Unmeasured operational limitation: the full 8.5-million-option-row scan has not been executed, so runtime and peak-memory behavior are not established by this synthetic code gate.

## Authorization flags

- Real artifact access/decryption: **false**
- Duplicate diagnostic execution: **not yet authorized**
- Deduplication: **false**
- Feature building / model fit: **false**
- Holdout access: **false**
- External market-source calls: **false**
- Option P&L / strategy promotion: **false**

**Tester → Developer:** preserve this exact R1 code-only PASS and the two failed workflow attempts; submit a separately reviewed, one-use diagnostic authorization request. Do not open the artifact before that authorization passes.

**Developer → Tester:** after submitting the exact authorization request, wait for independent authorization review; then review only the aggregate diagnostic receipt and its pinned report hash.