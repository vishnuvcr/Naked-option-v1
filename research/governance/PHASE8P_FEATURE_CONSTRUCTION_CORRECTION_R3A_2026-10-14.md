# Phase 8P R3A — Positional close timestamp correction

**Status:** Frozen pre-results implementation correction  
**Amendment ID:** `PHASE8P_FEATURE_CONSTRUCTION_CORRECTION_R3A_2026-10-14`

## Why this correction is needed

The canonical-data preflight completed successfully for run [#38519242615](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38519242615). Its aggregate time-frequency diagnostic found that the last eligible SPOT row is timestamped 15:29 on 1,150 sessions, 15:30 on 72 sessions, and 15:28 on 9 sessions. The preflight already defines 15:29 as the start-of-final-minute bar or 15:30 as an explicit close. The feature builder, however, had required exactly 15:30 and therefore emitted no positional samples for most sessions.

This is an implementation-contract inconsistency discovered before any empirical PM0001 fit or predictive result. It is not a model result and does not justify changing a target, sample threshold, or fold.

## Corrected positional-close mapping

For every eligible official session, use the latest observed source bar timestamped either 15:29 or 15:30. If both exist, the explicit 15:30 record wins. A 15:29 source row is the final one-minute interval and its close becomes available at 15:30; normalize its effective decision/endpoint instant to 15:30. An explicit 15:30 close remains unchanged.

No other timestamp qualifies. The 9 sessions whose last eligible source bar is 15:28 remain missing under this rule. Do not forward-fill, interpolate, select a nearest bar, fabricate a price, or relax the frozen 1% data-quality threshold. If either decision-session or target-session close is missing, exclude that row and count it.

## Unchanged protocol

This correction does not change the canonical CSV or its hash, calendar, label sign or flat tolerance, horizons, feature order, lookback set, fold boundaries, purging/embargo, minimum row/class support, baselines, log-loss metric, bootstrap settings, multiplicity correction, model configuration or strategy-selection scope. It amends only how an already-registered positional session-close value is mapped from the dataset's known final-minute timestamp convention to its effective 15:30 interval-end time.

## Required revalidation before fitting

1. Pass synthetic tests for 15:29 normalization, explicit-15:30 precedence, rejection of 15:28-only sessions, and unchanged exchange-session horizon indexing.
2. Regenerate the source-pinned feature-construction test report.
3. Re-run the canonical data precheck, requiring nonzero positional sample counts and zero technical failures.
4. Rebuild the run-scoped execution gate from the new full 320-cell precheck report and exact source pins.
5. Only then perform the registered PM0001 fit on passing cells; retain blocked rows.

No holdout was accessed and no model was fitted to generate this correction.
