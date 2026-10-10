# PPR-3 Tester Re-review 2 — Exact Configuration and Native-Task Freeze

**Review date:** 2026-10-10  
**Branch:** `phase-07-tester`  
**Decision:** **PASS WITH SCOPED RESTRICTIONS**  
**Next permitted phase:** **PPR-4 source availability/cache/point-in-time feasibility audit only**. No data bulk-download for modeling, no fit/tune/score, no final-holdout access, no options P&L.

## Exact snapshot reviewed

| Artifact | Developer blob SHA |
|---|---|
| PPR-3 manifest | `7c2ce64117559931cfd18444ed3de92012a36168` |
| Common-task configuration matrix | `9b47b2de7ad04fee26c6d5075772b56b9486df74` |
| Expanded model/pipeline/horizon cells | `b11b88d30ab0599ec18617738a9065589364ab49` |
| Frozen model settings/tuning grid | `23f99d44f899928ce29842c0be171724afaf9c91` |
| Target/inference contract | `049f5d3529ff5e82b3798fdb8e27bad10c413d80` |
| PPR-3 protocol | `998d9136ab624ec9764d9f205ba5ff9413fe9030` |
| Per-method native-task ledger | `7c5c48e015b6b3642e0bdfdcaa17f00ed7fa035e` |
| Offline validator | `bd105bc12a4da11c4146bb3e6fe90b29f6c42859` |
| GitHub Actions workflow | `db379d1890a473ea09ca4fccf41ce30ee6d02a3b` |
| Uploaded-PDF evidence matrix | `fe61751cac09089d0052bb92212dddd4a7b670dc` |
| Uploaded-PDF method crosswalk | `58f1f054fee33956c98d93a396fbca73e1397b0b` |
| 36-record registry crosswalk | `ac8491628913c5019d7a4b986339489b1dff1f14` |
| Literature registry | `2ee49ae119e61c8c523ed212c7f21bf15c5e8d7a` |

**Hosted exact-commit receipt:** [run 38074087881](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38074087881), success. It checked out trigger commit `9513e737313a56156e409331f47ee1cb8ae8e0d5` and printed: `PASS: PPR-3 configuration rows, candidate-cell expansion, target families, tuning grids and fit budget reconcile.` Scope was offline configuration/contract validation only. No market data was read, no external source was requested, and no model was fitted, tuned or scored.

## Tester re-review findings

### Previously requested changes now resolved

1. **Paper-native versus adapted tasks are separate.** The matrix contains 81 individual native-method/component records across all 15 uploaded PDFs. Each is explicitly outside the active common-model fit cap, has zero executable cells and states `model_fit_authorized=false`. The ledger now includes structured per-row fields for native task family, target/output, horizon, data window, split, feature recipe, source-reported metric/result, evidence status and source-specific ambiguity. Where the paper does not define a setting, the row states the unresolved issue instead of inventing a value. The common candidate universe remains separate.
2. **Native link errors corrected.** `NT022` (four-class Twitter mood) links only to a sentiment pipeline class and is not credited as the BERT-LSTM candidate. `NT023` (SOFNN) points to blocked `C011`, with no substitute model implied. `NT045` and `NT046` (simple-average/seasonality and simple-average options strategy) have no SMA/EMA crossover link. The offline validator asserts all four distinctions.
3. **Tuning fit count resolved.** Each of 18 RF and eight XGBoost settings receives five chronological inner-fold fits. One selected-setting outer fit per seed is already included in the outer fit budget; a full-prefix refit is not repeated per hyperparameter setting. Inner-search calls are `6×18×5 + 6×8×5 = 780`; the conservative outer allowance is `1,188×3 = 3,564`; total current upper bound is **4,344**, below 8,000.
4. **FLAT semantics explicit.** The fixed (10^{-8}) threshold defines only a numerical zero-return tie. It is not an economic no-trade class or a cost-neutral band. The threshold is fixed before results are seen.
5. **RF numeric type protected.** The serialized JSON file contains `1.0` for all-features mode in the RF summary and candidate settings; the Python validator confirms it parses as a float, distinct from integer `1`. This avoids a change in scikit-learn meaning.
6. **Coverage and exact hashes reconcile.** There are 81 configuration-ledger rows, 73 counted against the 93-row cap, 72 active candidates, one blocked SOFNN row, eight additional blocked/out-of-scope source-task rows, and exactly 1,188 expanded cells. These are 380 directional, 760 close-regression and 48 next-open cells. Native links resolve; the source-native fields are populated; no matrix/cell key is missing or extra; all manifest pins match the current files.
7. **Research boundary remains closed.** All model cells still say `PROPOSED_NOT_AUTHORIZED`; final holdout and option economics remain expressly blocked. No source-reported accuracy or strategy result is promoted as a project result.

## PPR-3 decision

**PASS WITH SCOPED RESTRICTIONS.** The configuration/protocol freeze meets the PPR-3 documentation gate. This is **not** approval to execute models or to claim a trading edge.

### Exact next allowed scope: PPR-4 source feasibility and point-in-time audit

PPR-4 may:
- inventory existing repository caches and files, inspect metadata/schema/coverage, and search free/official public-source documentation and data availability;
- document candidate sources for NIFTY/index OHLCV, global markets/macro/FX/gold/crude, India VIX, FII/FPI/DII, option-chain/contract/OI/IV/Greeks, timestamped news/social sentiment and corporate actions where applicable;
- assess point-in-time timestamps, revisions/vintages, exchange-session alignment, missingness and whether a sealed-holdout boundary can be proved from metadata **without reading holdout values or labels**;
- emit source-level row counts/date ranges/schema findings only for data already cached or explicitly permitted for metadata inspection, with hashes and source-specific limitations.

PPR-4 may **not** bulk-download candidate training datasets or pretrained models, accept new data into the model panel, fit any estimator, inspect predictions/scores, use holdout observations/labels, or calculate option P&L. Before a download or model use, a separate PPR-4 source manifest and exact-snapshot tester decision must specify the permitted URL/source, fields, time range, cache destination, license/terms, data-vintage rules, row-ID boundaries and allowed operation. Search the free-source landscape before claiming a source unavailable. A missing or unprovable sealed-holdout boundary blocks model execution.

## Reviewer transparency

This reviewer-role audit was performed in the same connected assistant session using the isolated `phase-07-tester` branch; it is not misrepresented as a separate human reviewer or independently hosted LLM identity.

**Developer → Tester:** Continue with PPR-4 read-only source/cache/PIT feasibility; present exact source manifest and holdout-exclusion proof for review before bulk data acquisition or model use.

**Tester → Developer:** Keep model/data acceptance, fitting/tuning/scoring, final-holdout access and option P&L blocked until a PPR-4-specific exact-snapshot PASS grants that precise operation.
