# Margin/distance adapter synthetic gate — 2026-10-13

Status: PASS_SYNTHETIC_ONLY.

Latest combined workflow: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38423098453

The combined suite passed 32 synthetic tests. New checks cover kernel SVM raw decision scores, nearest-centroid distance contrast, KNN neighbor log-odds scores, and chronological Platt calibration for raw scores. The SVM deliberately disables internal probability calibration because it is not chronological; all raw scores must be calibrated on inner chronological OOF rows before log-loss evaluation.

Initial run [38423018566](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38423018566) exposed two nearest-centroid API issues; both were corrected and logged in research/ERROR_LOG.md. The hardened run passed.

No market data or holdout access. This validates synthetic mechanics only and does not authorize empirical fitting.
