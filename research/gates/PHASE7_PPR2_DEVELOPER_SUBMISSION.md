# PPR-2 Developer Submission — 36-Record Literature Registry Reconciliation

**Date:** 2026-10-10  
**Branch:** `phase-07-developer`  
**Scope requested from tester:** PPR-2 literature registry mapping only  
**Empirical authorization:** none

## Exact artifacts under review

| Artifact | Blob SHA |
|---|---|
| Existing literature registry (L001–L036) | `2ee49ae119e61c8c523ed212c7f21bf15c5e8d7a` |
| New row-level PPR-2 crosswalk CSV | `ac8491628913c5019d7a4b986339489b1dff1f14` |
| Crosswalk summary | `63ae0486b016f541bb70628525bd45f33585ace8` |
| Offline crosswalk validator | `3dc96155e460f92a192d45502973c89bc9bd68c3` |
| Exact-commit CI workflow | `dffa5262b991db9843df35c34157e1273365d8f5` |

## What changed

1. Mapped every registry source ID L001–L036 exactly once. The crosswalk preserves all 11 existing registry fields and adds seven explicit columns for review depth, PPR-2 disposition, exact uploaded-PDF match, conceptual-only overlap, source-native task, next action, and remaining limitations.
2. Explicitly recorded zero exact identity matches to the 15 uploaded PDFs. Conceptual overlap (for example, an LSTM paper with an LSTM row) is deliberately not called the same paper or an exact replication.
3. Classified methodology/theory and multiple-testing papers separately from predictor papers, options-return tasks separately from spot direction, VIX-direction prediction separately from NIFTY direction, official NSE/SEBI pages as primary-source or regulatory context, and open-source code as a replication target rather than empirical proof.
4. Preserved review-depth variation. L032 and L034 are still registry-metadata-only; L031 is abstract-verified; L033 has abstract/metadata review; L036 has README-only inspection. This crosswalk is not a claim that every primary text or source-code repository has been fully reproduced.
5. Corrected a pre-existing L003 CSV schema defect. Its DOI URL had been shifted to `related_hypotheses`; the repaired source row places the DOI in `url_or_doi` and restores the method family, hypothesis and replication requirement to the correct columns. The existing registry validator checks CSV shape, and the PPR-2 validator checks semantic field placement too.

## Automated checks

- [PPR-2 offline crosswalk workflow](../.github/workflows/phase-07-ppr2-literature.yml) checks out `${{ github.sha }}` and runs [`validate_ppr2_literature_crosswalk.py`](../../scripts/validate_ppr2_literature_crosswalk.py).
- Checks include RFC-style CSV parsing, expected 11-/18-column schemas, exact L001–L036 coverage, unique IDs, all source fields preserved exactly between registry and crosswalk, non-empty PPR-2 annotations, explicit exact-match status, URL/DOI plausibility, and specific L003 semantic checks.
- One initial CI attempt failed because the depth-label validator did not accept `REPOSITORY_README_VERIFIED`; this was a validator bug, not a source mapping failure. The allowed-label list was broadened, and exact-commit rerun [38069596564](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38069596564) passed on commit `974bed3013fa1a0a608f83a56220ed449514580a`. The failed run is preserved in the error log.
- Automated checks validate mapping integrity only. They cannot decide whether a scientific interpretation is correct, and do not search the web or retrieve data.

## Known limitations and exclusions

- This is a **registry reconciliation pass**, not a full-text systematic review of all 36 records. Source text depth is recorded row by row.
- The 15 uploaded papers are already represented in a separate PPR-1 matrix. None of L001–L036 has been proven to be the exact same item as an uploaded PDF. Some are close in topic or estimator family, but crosswalk references are labeled conceptual-only.
- L008–L018 need method/result extraction to support paper-native replication settings; L032–L035 require additional source-level verification; L036 source-code review is still pending. For any of these, titles/abstracts are not substitutes for model target, data dates, chronological split, features, metric formula and results.
- Official-source rows L019–L024 are data/documentation references only. This PPR-2 scope performs no new source pulls. Existing one-use Dhan data approval remains spent and untouched.
- No market-data acquisition, model fitting, hyperparameter search, empirical scoring, final holdout access, option P&L, brokerage/slippage scenarios or strategy work has occurred under this PPR-2 submission.

## Requested gate

**Developer requests PPR-2 PASS with scope limited to PPR-3 documentation-only configuration matrix/protocol freeze.** On approval, developer will map each paper-native configuration to the common-task families or mark it descriptive/blocked, freeze targets, horizons and compute budget; still no data pulls or model fitting until later gates.

**Developer → Tester:** Independently validate all 36 rows against the source registry, audit conceptual-vs-exact mapping and review-depth labels, verify the L003 fix, and inspect the exact-commit workflow receipt.  
**Tester → Developer:** Issue PASS/REQUEST CHANGES against the exact hashes above. If passing, authorize PPR-3 documentation-only configuration freeze and keep empirical/data/holdout/option work blocked.
