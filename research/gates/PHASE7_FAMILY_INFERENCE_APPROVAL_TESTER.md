# Phase 7 Family-Inference Amendment — Tester Approval

**Status: PASS — FROZEN**

Tester reviewed developer commit `5f4f8b0c64c59bc2fcad1aba454647a3c89aacbf`.

The family-level data-snooping procedure is now fully frozen before implementation correction:

- Brier-loss improvement versus causal training-only positive-rate baseline;
- positive differential = lower candidate Brier loss;
- moving-block bootstrap;
- block length 20 daily / 60 intraday;
- 500 replications;
- shared resampled indices across candidates;
- seed 42;
- per-candidate mean recentering under the null;
- maximum positive candidate mean improvement as the family statistic;
- abstention candidates receive zero differential on abstained observations, equivalent to benchmark loss when no forecast is taken.

This is consistent with the project's requirement to account for data snooping across the registered candidate family.

**Tester disposition: PASS.**

**Tester → Developer:** Archive this amendment and implement the exact frozen family test. Then resubmit the code gate.