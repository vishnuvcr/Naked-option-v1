# Phase 5 Family D — Run 5 Tester Follow-up

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer commit: `6dc3f1fb7447fada84929c83bf068948378b4746`
Hosted run: #5 / `37595530652`

## Gate result

**REQUEST CHANGES — REGRESSION FIXTURE ONLY**

Run #5 again failed at D13 with finite-probability regression returning NaN.

## Diagnosis

The corrected test used a single synthetic group, but the training cutoff remained at 300. A causal 20-observation window creates only 281 trainable endpoints before that cutoff, below the registered minimum of 300. The production code correctly returned NaN instead of fitting an under-sized model.

## Required action

Use a training cutoff of at least 319; the proposed 360/420 fixture is adequate. Keep the independent session-boundary test unchanged.

No empirical Family D metric is accepted from run #5.

## Tester instruction to developer

Commit the deterministic fixture correction only, run the hosted Family D gate, and submit the resulting artifact for independent review.

## Developer instruction to tester

On the next completed run, independently inspect the actual hosted regression output, then audit D13-D15 intraday session-local window availability before accepting or restricting those methods.
