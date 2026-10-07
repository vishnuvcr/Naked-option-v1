# Phase 4 Family C — Independent Tester Final Gate

Date: 2026-10-07

## Reviewed artifact

- Workflow run: #38
- Commit: `d33b42f11c5373c0b0b2550a698df36e35f0f761`
- Artifact: `phase4-family-c-results`
- Artifact ID: `11469469440`
- Artifact digest: `sha256:963c263c144e7ed9fb44baa81ae7868b5b133aacc44f66b8a2037196fcae7ede`

## Independent checks

The tester independently inspected the current developer implementation and the newly generated artifact.

### Data and chronology
- Daily layer covers 2020-01-01 through 2026-09-30 with 1,670 rows.
- Intraday research reference remains the pinned derived 1-minute NIFTY dataset with official NSE overlap validation.
- C01-C04 model fitting follows the frozen 20-session refit cadence.
- Intraday C01-C03 use the frozen decision grid.
- The artifact contains the complete registered C01-C09 set for every required horizon; C10/C11 are explicitly BLOCKED_DATA.
- Result denominators are internally consistent with the reported metric sample sizes.

### Mathematical corrections verified
- C04 uses continuous returns and exact cumulative AR innovation-weight variance.
- C06/C07 use transition-predicted priors before current-observation updating and calculate H-step cumulative state-return moments.
- C08 explicitly propagates the state H steps.
- C09 uses persistent directional state until opposite-threshold reset.
- C05 is explicitly treated as a horizon-invariant conditioning signal.

### Artifact sanity
- Regression tests passed in the hosted workflow before empirical execution.
- No future positive/negative labels are used as model inputs in the reviewed chronology.
- No result from the pre-correction Family C artifact is used for this gate.

## Scientific result interpretation

Family C does **not** demonstrate a robust directional edge.

The strongest apparent directional metrics are small and inconsistent across horizons. For example, daily C06 reaches AUC about 0.536 at H1 and daily C05/C07 are around 0.53 AUC in some horizons, while intraday performance is generally near 0.50 and several state-space methods are below 0.50. These are descriptive screening results only and have not passed multiple-testing, block-robustness, or option-economic gates.

Therefore no Family C method is promoted as a trading strategy.

## Gate decision

**PASS WITH SCOPED RESTRICTIONS**

The family implementation and empirical execution are accepted as a valid Phase 4 research input.

Restrictions:
1. C10 and C11 remain BLOCKED_DATA.
2. No Family C method is considered economically viable.
3. No method may be selected on the basis of a single AUC/horizon observation.
4. Family C results must undergo the later multiple-testing, chronological robustness, and long-option execution-cost gates.
5. Phase 5 may proceed, but only under the same preregistered controls and without treating Family C as evidence of a deployable edge.

## Tester instruction to developer

Advance to the next registered family/phase only after preserving this gate and its artifact lineage. Do not promote any Family C method to a trading strategy; carry the complete Family C result set forward as an auditable input to the ML/novel/robustness stages.
