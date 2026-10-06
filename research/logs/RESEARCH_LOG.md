[object Object]
## 2026-10-07 — Phase 3 tester REQUEST_CHANGES and correction

- Tester rejected the first protocol draft because sigma units, triple-barrier volatility construction and several baseline parameter choices were not fully deterministic.
- Corrected and froze: 20-observation same-frequency sigma, non-updating triple barriers, 5/20 moving averages, training-only 33/67 volatility-regime cut points, equal-weight global composite, exact breadth formula, and logistic L2/C=1/liblinear/max_iter=1000 specification.
- No baseline results have been inspected during this correction.
- Phase 3 remains gated pending independent tester re-review.
