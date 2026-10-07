# Phase 3 Independent Tester Review — REQUEST CHANGES

## Review target

Developer empirical artifact from GitHub Actions Phase 3 run #97, commit `9260918b285167ecefc06f6858c8712563654ab4`.

The review was performed independently from the immutable workflow artifact, the frozen Phase 3 baseline protocol, the Phase 3 data requirements, the result-schema validator and the current developer implementation. No developer conclusion is treated as evidence without reconstruction.

## Gate decision

**REQUEST CHANGES — Phase 3 empirical gate does not pass yet.**

The data acquisition and core B0-B11 execution now run end-to-end, but one clear point-in-time leakage defect and one reporting-consistency defect remain.

## Findings

| Area | Result | Finding |
|---|---|---|
| Workflow/data acquisition | PASS | Protocol validation, daily acquisition, intraday discovery/acquisition, both baseline suites, result-schema validation, persistence and artifact upload all completed successfully in run #97. |
| Daily data provenance | PASS WITH RESTRICTION | 1,670 daily observations, 2020-01-01 to 2026-09-30; official NSE overlap checks passed on 2024-07-05 and 2024-07-08. Yahoo remains a derived bulk backfill rather than canonical exchange data. |
| Intraday reference | PASS WITH RESTRICTION | Pinned HF revision `0f4800e43e6f96cec0794369d78eb4d3c4211ef5`, 486,050 rows and ~1,865 days; two official-NSE EOD overlap checks matched exactly. Derived source remains non-canonical. |
| Horizon coverage | PASS | Daily {1,2,3,5,10}; intraday {5,15,30,60,120}. Every horizon contains explicit B0-B11 dispositions. |
| Confusion-matrix arithmetic | PASS | For executed baselines, TN+FP+FN+TP equals reported n and accuracy matches the confusion matrix. |
| B3/B4 semantics | PASS | Intraday B3 uses previous session close; B4 uses the registered `min(H,30)` lookback sequence. |
| B6 look-ahead control | PASS | Current implementation uses the shifted prior-20 range rather than allowing the current bar into the range. |
| B11 walk-forward purge | PASS | The current developer implementation uses only labels/features before the purged training endpoint and scales from the training frame. |
| **Intraday B8 PIT control** | **FAIL — HIGH** | The intraday calendar baseline builds B8 from `y_full` and uses `groupby("dow")["y"].transform(lambda s: s.shift(1).expanding(...).mean())`. For a horizon H, the label at time t-1 is based on a future return ending at t-1+H, which can extend well past the current decision timestamp t. This is future-label leakage, especially severe at H=60/120. The latest run therefore cannot be accepted as point-in-time clean. |
| **Probability-bin diagnostic consistency** | **FAIL — MEDIUM** | `future_return_by_probability_bin` is computed from p/future without applying the same label-validity mask used by `metrics()`. For example, intraday H=5 reports 7,530 observations across bins while the corresponding baseline metrics use n=7,517. Similar differences occur at H=15/30/60/120. This makes the diagnostic internally inconsistent and can mix rows excluded from classification metrics. |
| Result-schema gate | PARTIAL | It verifies baseline IDs/statuses/horizons, but does not verify that probability-bin counts equal the metric evaluation sample or that B8 is PIT-safe. |
| B9/B10 | BLOCKED_DATA | Explicitly documented global-overnight and breadth gaps are acceptable as quarantined components, but they prevent those components from being claimed as tested. |
| Scientific promotion | BLOCKED | No option strategy or Phase 4 method may be promoted from this run. |

## Required developer corrections

1. Rewrite intraday B8 using only calendar-history labels that were fully observable before each decision. A safe construction for horizon H must only use labels whose label-end timestamp is strictly before the decision timestamp, e.g. restrict historical labelled observations to `label_time + H < decision_time` before calculating the expanding weekday rate.
2. Pass the same valid-row mask used for classification metrics into `future_return_by_probability_bin`. The sum of probability-bin counts must equal the baseline metric n for every EXECUTED baseline, or the diagnostic must explicitly report a separate denominator with a documented reason.
3. Extend `validate_phase3_result_schema.py` to reject PIT-unsafe B8 construction markers and to enforce probability-bin denominator consistency.
4. Add a regression test with a synthetic horizon where an otherwise tempting B8 implementation would use an unfinished future label; the test must fail for the leaked implementation and pass for the corrected implementation.
5. Rerun the full Phase 3 workflow from a fresh immutable commit. Earlier results remain rejected evidence.

## Independent tester conclusion

The project has made substantial progress: the workflow is now actually producing immutable empirical artifacts, and most structural/math checks pass. The current gate is **not** a scientific null result and is not a reason to stop the research. It is a reproducibility/leakage correction gate.

No Phase 4 search should start until the corrected Phase 3 artifact passes independent re-review.

## Tester instruction to developer

Correct B8 and the probability-bin denominator handling, add regression coverage, rerun Phase 3, then resubmit the new immutable artifact for independent reproduction.
