# Phase 8 H=1 ULP Gate — Independent Tester Review R2 (2026-10-12)

## Decision
**REQUEST CHANGES — narrow, evidence-based hold.**

## Scope checked
- Developer branch: `phase-08-developer`
- Exact HEAD under review: `da33a40f4f52e51807ca0fb7882e7920021c47a1`
- Validator blob SHA: `9650ebc39d495dd414cfcbc2710452295743c0e9`
- Regression test blob SHA: `569b6e511a768ca875d23225eeb65c039fc8b87e`
- Workflow blob SHA: `2ee83ff45f4b5aa1d237da3e64bfb6e6a9aa4329`

## Evidence
- Hosted validator regression [run 38164567189](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38164567189): success at the exact HEAD above.
- Hosted protocol check [run 38164567374](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38164567374): success at the same HEAD.
- The reviewed comparator confines the two-ULP exception to float64 source-derived `future_return`; paired NaNs and equal infinities are handled explicitly, non-finite mismatches and shape mismatches fail closed. The test suite covers 1/2/3 ULP and sign/non-finite edge cases.
- Earlier full reconstruction [run 38164524835](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38164524835) succeeded on older HEAD `21dd39b6819dcc1ecae67307633fe4621e168c58`, not the exact HEAD under this review. Its observed daily H=1 differences were 64 values, max absolute difference `3.469446951953614e-18`, maximum distance 1 ULP; all were within policy. However, this is not proof that the final diagnostics-persistence changes were exercised in a full artifact reconstruction.

## Required next action
Run the saved Run #994 reconstruction on exact HEAD `da33a40f4f52e51807ca0fb7882e7920021c47a1`, using the immutable cached reference artifact and without fetching new market data. Confirm the generated validation manifest includes per-panel ULP diagnostics, all observed mismatches are <=2 ULP, and labels/timestamps remain exact. Keep the Run #994 artifact and `1e-9` aggregate tolerance unchanged.

## Restrictions
No option P&L, holdout access, fresh market-data acquisition, empirical authorization, or strategy promotion is approved by this review. The one-use R1 preflight authorization remains consumed/disabled.

## Developer instructions
Developer → Tester: resubmit only after exact-HEAD reconstruction evidence and manifest are available.

## Tester instructions
Tester → Developer: keep the gate open until the exact-HEAD reconstruction is reviewed; no unrelated requirements are added.
