# Phase 6 Fresh Run — Tester Review of Residual Intraday Cutoff Defect

**Status: REQUEST CHANGES**

## Independent finding

During pre-result review of developer commit `9b9b7914f82993505ec4f2f0c3aac0b3d6732521`, the tester inspected the full Phase 6 empirical implementation rather than assuming the previously corrected cutoff path was exhaustive.

A residual invalid positional access remains in `scripts/run_phase6_novel.py`:

`cutoff = decision_times.iloc[rows[0]] - pd.Timedelta(minutes=int(H))`

Here `decision_times` is explicitly constructed as a pandas `DatetimeIndex`. `DatetimeIndex` does not expose the Series/DataFrame `.iloc` accessor. The remaining occurrence is in the later global I03 block, after the per-session loop.

## Consequence

The fresh hosted run `37678088131` is **not scientifically accepted**. It is expected to terminate with the same AttributeError when execution reaches this path unless corrected first. No metric from this run may be promoted or used for selection.

## Required developer correction

1. Replace the residual `decision_times.iloc[rows[0]]` with valid positional indexing `decision_times[rows[0]]`.
2. Search the complete Phase 6 implementation for all `.iloc` accesses and verify that every remaining use is applied to Series/DataFrame objects, not Index objects.
3. Add a regression covering the later global-I03 cutoff path, not only the earlier block cutoff path.
4. Preserve all frozen Phase 6 method definitions, labels, horizons, training rules, and cost rules.
5. Submit the corrected code back for an independent tester approval before the next empirical execution.

**Tester disposition:** REQUEST CHANGES — fresh empirical execution must not be treated as valid evidence until the correction is reviewed and approved.
