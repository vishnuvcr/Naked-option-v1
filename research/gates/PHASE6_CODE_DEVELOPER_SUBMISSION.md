# Phase 6 Implementation — Developer Submission for Tester Gate

Date: 2026-10-07
Developer branch: `phase-05-developer`
Precondition: `research/gates/PHASE6_METHOD_SPEC_APPROVAL_TESTER.md` approved the frozen method specification.

## Files submitted
- `research/phase6/PHASE6_METHOD_SPEC.md`
- `scripts/run_phase6_novel.py`
- `scripts/test_phase6_novel.py`
- `.github/workflows/phase-06-novel.yml`

## Implementation scope

The implementation covers the full registered E01-E10 and I01-I10 matrix. Methods that require unavailable PIT-safe option/global/liquidity histories are explicitly marked BLOCKED_DATA rather than silently substituted.

The workflow has two gates:
1. a regression/static job that runs automatically on developer pushes and manual dispatch;
2. an empirical job that is hard-gated on the presence of the independent tester approval file `research/gates/PHASE6_CODE_APPROVAL_TESTER.md` on the developer branch.

Therefore no Phase 6 empirical result can start before the tester code gate is archived on the developer branch.

## Required regression coverage

The submitted regression suite checks:
- future-row mutation invariance;
- deterministic training-reference rank binning;
- E03/E04/E05 causal windows and degenerate cases;
- I03 dimensionless bounded scoring;
- I07 CE/PE break-even directionality and invalid put guard;
- I08 entropy weighting;
- I09 fixed abstention band;
- fixed E08 model map;
- absence of centered windows and forward-filling/back-filling in the implementation.

## Developer request to tester

Independently inspect all four submitted files for mathematical correctness, causality, leakage, numerical robustness, status handling, workflow gating and reproducibility. Confirm that no empirical run should proceed until your gate is archived on the developer branch.

## Tester instruction

Return APPROVE or REQUEST CHANGES with concrete mathematical/code/workflow findings. The developer will not launch empirical execution until approval is independently recorded.
