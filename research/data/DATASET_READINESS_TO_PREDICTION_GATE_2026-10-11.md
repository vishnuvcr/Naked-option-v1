# Dataset Readiness → Prediction Gate — 2026-10-11

## Purpose and current status

This is a bridge/checklist for moving from the fixed-artifact value audit to a gated prediction-only experiment. It does not amend or unlock the frozen research protocol.

- Acquisition is closed by user instruction; do not make new market-data requests.
- The encrypted fixed artifact is identified by SHA-256 `aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216`, source run `38116772719`, artifact ID `11693866249`.
- Its manifest reports 8,490,723 option rows, 403,664 spot rows, 7,591,172 matched spot joins, 899,551 unmatched option rows and six failed spot gap-fill windows.
- Authenticated decryption has succeeded in the fixed-artifact audit workflow. The row-level semantic scan has not yet produced a verdict at the time this plan was written.
- The current PPR-3 configuration manifest remains `PROPOSED_NOT_AUTHORIZED`. A structurally clean data audit does not grant model-fitting, scoring, holdout, or strategy permission.

## Data readiness checks

1. **Archive/decryption:** verify immutable artifact identity, encrypted byte sizes/hashes, authenticated plaintext gzip hashes, and total rows. This stage has passed for the current workflow run.
2. **Schema/count contract:** verify every monthly CSV header against the manifest, per-month row count and dataset summary totals, only known `OPTION`/`SPOT` rows, and no extra/missing part.
3. **Timestamp contract:** verify epoch against UTC and IST timestamp fields, local session date, month-part placement, and observed session count. Reject silent rounding of malformed epochs.
4. **Market-price semantics:** check option and spot OHLC inequalities, positive prices, finite/malformed numeric values and impossible negative volume/open-interest/time-to-expiry values. Keep missing data as missing.
5. **Duplicates:** count duplicate collector composite row keys and repeated standalone spot timestamps. Do not silently collapse duplicates before their source lineage and agreement are understood.
6. **Spot joins/coverage:** independently reconcile exact-match and unmatched counts to the manifest; report monthly option/spot counts and sessions with no spot observation. The 899,551 unmatched option rows and six failed windows remain explicit limitations even if other checks pass.
7. **Missingness:** report per-feature blank/malformed values and data-quality flags by row type. A passing schema is not a complete-feature-panel claim.

## Candidate prediction panels after a tester pass

- **Primary intraday reference candidate:** canonical rows from the standalone `SPOT` series, keyed by exact epoch and sorted chronologically in Asia/Kolkata. If the actual spot coverage lacks a given timestamp, that timestamp is not fabricated.
- **Rolling-option fallback:** `rolling_spot` is a scalar supplied on option rows. It is *not* interchangeable with a spot OHLCV bar. It may be evaluated as a separate reference-price series only after a dedicated cross-contract/time check proves that contemporaneous rows agree sufficiently and the rule is reviewed. Until then, do not use it to silently fill missing spot OHLC.
- **Option predictor layer:** option OHLCV, OI, IV, relative strike/returned strike and expiry-related fields may be considered only where their time/contract availability is defensible. Proxy Greeks and inferred expiry metadata must be separately labelled and must not be passed off as sourced historical values.
- **External/alternative features:** this artifact alone does not establish PIT historical FII/FPI, DII, India VIX, market breadth, global-index availability, news or sentiment. With acquisition closed, these are `BLOCKED_DATA`/not included unless validated data already exist in the repository cache. No synthetic values or unregistered proxies.

## Pre-registered prediction contract to preserve

Use the existing frozen label and inference specifications; do not choose targets or metrics after seeing the audit or model results.

- Intraday candidate decisions: 09:30, 10:00, 11:00, 12:00, 13:00, 14:00 and 15:00 IST.
- Intraday horizons: 5, 15, 30, 60 and 120 minutes. Positional horizons: 1, 2, 3, 5 and 10 trading sessions.
- The Phase 3 sign, threshold, triple-barrier and economic labels are separate label families; do not merge them. A direction forecast is not an option profitability result.
- In the PPR-3 common daily family, the frozen target/inference contract uses DOWN/FLAT/UP close-to-close probabilities, exact shared decision/label endpoints, and multiclass Brier-loss improvement over the causal training-only rate baseline. PPR-3 remains proposed/not authorized for fitting, despite its documented configuration matrix.
- Use strict chronological folds, training-only scaling/feature selection, purge at least the label horizon as the frozen protocol requires, and never inspect final holdout values/labels before a separately authorized final evaluation.
- Preserve candidate IDs, fixed settings, input hashes, random seeds, row eligibility/exclusion manifests, and all failed/blocked cells. Do not exceed the registered fit budget or add model configurations based on an attractive result.
- If empirical execution is later authorized, report class balance, calibration, proper scoring, directional metrics and confidence intervals under the applicable frozen statistical contract. Family inference and multiple-testing controls must be the exact contract for that approved experiment; do not mix Phase 3 and PPR-3 bootstrap settings.

## Gates and decisions

1. The current fixed-artifact workflow must finish and publish `research/data/DATASET_VALUE_AUDIT_RESULT.json`.
2. Tester branch reviews that sanitized report and its hashes/run/cleanup evidence; verdict scope is value-level integrity and sample suitability only.
3. If row-level checks fail, resolve documented findings without recollecting data or silently altering prices; rerun only the fixed-artifact offline audit.
4. If structural checks pass with coverage restrictions, submit a separate exact-snapshot prediction-pipeline proposal using only demonstrably available fields. Keep the matrix frozen and ask the tester to approve the exact dataset/labels/code snapshot.
5. Do not fit/score models until the currently applicable empirical permission gate explicitly passes. The current PPR-3 manifest says empirical execution is blocked; older approvals from different experiment scopes must not be treated as a substitute.
6. Do not open the final holdout, do strategy/P&L tests, or declare a profitable strategy as part of this data-readiness stage.

## Handoffs

**Developer → Tester:** Check the actual fixed-artifact JSON report, audit-run outcome, encrypted/decrypted hashes, coverage and cleanup; state clearly whether a candidate prediction panel is structurally suitable and which limitations remain.

**Tester → Developer:** Return a scoped readiness decision on `phase-07-tester`. A structural pass is not a modeling approval; preserve the PPR-3 and holdout gates.
