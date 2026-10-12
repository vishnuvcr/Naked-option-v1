# Tester decision — registry V2 R1

Decision: **REQUEST CHANGES**

Verified: 1,000 unique method IDs/fingerprints; 2,000 unique config IDs/hashes; all configs have valid parent methods; independently recomputed hashes match.

Blockers: (R1) two lookback-only configurations per method are insufficient for the declared exhaustive grid; (R2) probability/calibration and decision-operator compatibility is underspecified; (R3) exact label/horizon IDs, sample/missingness/class-support and data eligibility are missing from the configuration manifest.

Empirical execution authorized: **No**. Holdout accessed: **No**.

See the full report: [registry V2 R1 tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-tester/research/gates/PREDICTION_REGISTRY_V2_R1_TESTER_REPORT.md).

**Tester → Developer:** address R1–R3 and resubmit exact hashes.
**Developer → Tester:** submit revised registry and synthetic-only validator; no empirical run yet.