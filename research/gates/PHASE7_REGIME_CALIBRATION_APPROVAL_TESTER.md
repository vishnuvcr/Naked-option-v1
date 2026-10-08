# Phase 7 Regime Calibration Amendment — Tester Approval

**Status: PASS — FROZEN AMENDMENT**

Tester independently reviewed developer commit `b410c7f6e5df2888190b0b03bfd6300d25bf0a82`.

P08 and P09 are now genuinely regime-conditioned rather than merely labeling the same forecast by regime:

- causal four-state regime;
- training-only regime positive-class rate q_s;
- fixed probability calibration P = 0.5*base_probability + 0.5*q_s;
- pooled training rate fallback when a regime has <50 observations;
- no result-driven regime selection or weight tuning.

The 0.5 blend is frozen before empirical execution. The added probability-forecast-combination literature anchor is consistent with the methodological motivation for calibration of combined probabilities.

No other Phase 7 definitions are changed.

**Tester disposition: PASS.**

**Tester → Developer:** Archive this amendment and ensure the implementation matches the exact P08/P09 formula. Then submit the complete implementation for the independent code gate.