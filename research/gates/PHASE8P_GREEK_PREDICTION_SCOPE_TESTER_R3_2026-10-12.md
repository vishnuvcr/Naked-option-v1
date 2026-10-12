# Independent Tester Review — Phase 8P Greek Prediction Scope R3
Date: 2026-10-12
Reviewed developer branch: phase-08-prediction-developer
Reviewed scope file SHA-1: 018500722f88f5fb100a2e24afc3d5d97394631e

## Decision
**PASS — SCOPE ONLY, WITH RESTRICTIONS.** This authorizes implementation and synthetic-only testing against the frozen scope. It does not authorize artifact decryption, model fitting, holdout access, new data requests, option P&L, execution testing or strategy promotion.

## Independent mathematical and protocol checks
- R3 now gives explicit signed feature math: Delta imbalance is the median signed CE Delta plus the median signed PE Delta. Since PE Delta is normally negative, the sign has a reproducible interpretation and is not a call-minus-absolute-put sign ambiguity.
- OI/volume ratios use sums of finite nonnegative inputs and a strictly positive CE denominator. No epsilon, smoothing, or result-dependent handling is introduced; invalid denominator cases remain missing and flagged.
- Cross-sectional Greek medians require at least five eligible observations per side. Invalid IV and source-flagged non-trading rows are excluded from the primary feature set. Source-provenance proportions remain separately reportable.
- The paired primary metric is correctly signed: d = Brier(spot-only) - Brier(spot-plus-Greek), so positive mean d favors the augmented model.
- The one-sided null is stated, block-resample indices are shared, null centering and p-value calculation are explicit, non-finite resamples fail closed, Holm controls the 20 registered primary comparisons, and the coarse 1/501 resolution is disclosed.
- Exact estimator settings are pinned, including the named logistic solver and fixed boosting arguments. The proposal disallows changing settings silently after convergence or environment failures.
- Artifact IDs/digests, the license, partial-grid status, timestamp convention, no-new-source rule, encrypted-only processing, target maturity purge and holdout boundary are protected by a machine-readable preflight decision. A failed/ambiguous schema is a BLOCKED outcome, not permission to guess or change labels.

## Remaining restrictions before any empirical use
1. Developer must implement the scope exactly and add independent synthetic fixtures for signed Delta, side coverage, ratio zero/missing denominators, exact timestamp equality, label maturity purging, split masking, blocked schemas, bootstrap indices/null centering/p-value direction and Holm adjustment.
2. The code/hash gate must independently pass before the run downloads or decrypts either artifact.
3. The separate hosted preflight must prove the panel schema, target-end/maturity rule, valid development-only mask and exact block units. This tester must inspect that exact preflight artifact and issue a separate PASS before fitting.
4. If the Run #994 artifact does not prove a usable label/timestamp/split contract or if the registered block unit does not match its actual panel, the correct result is BLOCKED_DATA and a new tester-reviewed amendment—not a substitute source, a changed label, or an opened holdout.
5. Any resulting inference is historical model comparison, not evidence of a live edge or profitable strategy. CC-BY-NC-4.0 non-commercial research terms remain binding.

## Next required action
Proceed to implementation and synthetic regression tests on the isolated developer branch. Preserve R1 and R2 as history. Submit exact source/blob hashes and test evidence for the independent code gate.

**Tester → Developer:** implement only the R3 scope; keep artifact loading/model fitting behind the separate preflight-and-tester gate.
**Developer → Tester:** submit the exact code/test snapshot for independent formula, leakage, determinism and gate review; do not run empirical models before your separate code and preflight decisions.
