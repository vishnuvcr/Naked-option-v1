# Independent Tester Review — Phase 8P Greek Prediction Scope R1
Date: 2026-10-12
Reviewed developer branch: phase-08-prediction-developer
Reviewed scope file SHA-1: d41a0fd5300df85ab5d637b356cd640c6059c594

## Decision
**REQUEST CHANGES — SCOPE NOT YET APPROVED.** This decision concerns only the proposed research scope. No data artifact was downloaded or decrypted, no model was fitted, and no empirical result is accepted.

## Independent checks performed
- Compared the proposal to the accepted Greek artifact report: artifact ID 11723198817, ZIP SHA-256 e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736, 61 encrypted parts, CC-BY-NC-4.0 restriction, PARTIAL_GRID coverage and proxy/modelled Greeks.
- Checked the existing Phase 3 label protocol and Phase 7 frozen method/addendum: the saved forecast panels must remain immutable; timestamp key semantics cannot be guessed; only chronological development rows may be used; the final holdout must stay unopened.
- Verified the proposal correctly prevents P&L, option-entry/exit testing, new source requests, holdout access and strategy promotion.
- Verified the proposed primary paired metric direction: Brier change = Brier(spot-only) minus Brier(spot-plus-Greek), so positive values indicate lower loss for the augmented model.
- Checked the proposed 20-test family count: two fixed model classes times ten registered horizons.

## Required corrections before scope approval
1. **Exact feature formulas are missing.** Define the signed Delta imbalance algebraically (including CE/PE signs), the denominator and zero/missing behavior for put/call OI and volume ratios, median aggregation/eligibility rules, and what is meant by a “prior-observed-panel” measure. A phrase such as “Delta imbalance using signed Delta” is not a reproducible formula and can conceal a sign error.
2. **Fix the timestamp/schema contract as an explicit preflight deliverable.** The proposal appropriately says to fail closed if the saved forecast panel's decision timestamp, target label, target-end timestamp or protected-holdout boundary is ambiguous. The scope should require a schema/coverage-only job to produce a machine-readable PASS/BLOCKED decision before any fit; model code must be unreachable unless that decision confirms exact timestamp alignment, a matured-label purge rule and a development-only row mask.
3. **Feature/target row identity must be frozen.** Both arms must use the identical complete-case decision-row intersection for each model/horizon. No model-specific deletion, imputation fitted on test rows, or different test timestamps between baseline and augmented arm.
4. **Define how the daily and intraday horizon target-end times are obtained.** Do not infer them solely from horizon names. Use only a field/protocol definition proven from the immutable Run #994 manifest/panel schema; if not present, stop with BLOCKED_DATA and request a new tester-reviewed protocol amendment.
5. **Coverage metrics need a distinction between observed data provenance and usable Greek rows.** Report overlap and valid-feature coverage separately by IV source, expiry-mapping source, Greek status, and layer/horizon. Do not present a cross-sectional aggregate as an exchange-wide Greek surface.

## Required next submission
Developer should submit a versioned R2 scope that implements the above clarifications and includes synthetic formula/edge-case fixtures before any empirical implementation. The proposal must not silently relax the dataset restrictions or thresholds.

## Restrictions
No artifact decryption/download, model training, result publication, P&L, holdout access, source calls or strategy promotion is authorized by this REQUEST CHANGES decision.

**Tester → Developer:** correct the five scoped issues above and resubmit the complete R2 scope for an independent check; preserve R1 unchanged as history.
**Developer → Tester:** await the R2 exact file SHA and review only the corrected scope; do not grant empirical authorization from a scope approval.
