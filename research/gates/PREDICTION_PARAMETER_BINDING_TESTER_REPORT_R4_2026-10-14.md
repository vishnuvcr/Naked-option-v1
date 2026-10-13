# Independent tester report — Phase 8P R4 parameter binding

Date: 2026-10-14  
Tester branch: `phase-08-prediction-param-audit-tester`  
Reviewed developer commit: `0e016b657a4f7f906b4fde3a20a515d7ce53f0e4`  
R4 workflow: [run 38462243181](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38462243181)  
Artifact: [parameter-binding audit report](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38462243181/artifacts/11845873140)  
Artifact ZIP SHA-256: `035489e989057cfbbf0faa2b6866a8eb9cb4e7f89a70c8fdb21111351094f8a7`

## Decision

**BLOCKED — do not authorize empirical market-data fitting or advance to model-result selection.**

The automated implementation gate passed at the developer snapshot. The independent mathematical/semantic check found material gaps not exercised by the synthetic suite, described below.

## Evidence verified

The exact developer commit's hosted workflow completed successfully:
- 109 prediction synthetic tests passed;
- 20 prediction modules compiled;
- 1,000 methods and 40,000 configurations reconciled;
- 38,000 parameter configurations bound to supported family schemas;
- 2,000 survival/event-time configurations blocked;
- registry compatibility decisions remained 426 `ALLOW_IN_PRINCIPLE` and 574 `BLOCK`;
- empirically eligible methods remained 0;
- `empirical_fitting_authorized=false`, `market_data_loaded=false`, and `holdout_accessed=false`.

These results establish the declared synthetic/code-contract checks only. They do not establish market predictability or trading profitability.

## Blocking finding T1 — Markov terminal state and likelihood belong to a prior parameter iterate

Reviewed source: `scripts/prediction_markov_switching_logit_r3.py`  
Reviewed blob: `67932d8f0cc1836c645c79059492175ca0122895`

The forward likelihood and `gamma` state posterior are computed at the beginning of each iteration. The code then updates `initial`, `transition`, and all regime-specific logistic coefficients/intercepts (the M-step). But after that update, it can break on the convergence comparison and, in all cases, it stores `gamma[-1]` and `old_log_likelihood` as if they described the final updated model.

More specifically:
1. `log_likelihood` is based on emissions and transition probabilities before the current iteration's M-step.
2. If the convergence condition is satisfied, execution breaks before updating `old_log_likelihood = log_likelihood`, so the stored value remains an even older iterate.
3. `last_state_posterior_ = gamma[-1]` reuses the pre-M-step state posterior, while `predict_proba` subsequently propagates it with the post-M-step `transition_` and regime coefficients.

This mixes estimates from different parameter iterates. The probabilities may remain finite and normalized, so the existing tests do not detect the inconsistency. The published log-likelihood/convergence diagnostic can also refer to an older iterate.

### Required developer correction

- After the last M-step, rerun the forward recursion using the final `initial_`, `transition_`, `intercepts_`, and `coefficients_`.
- Set `last_state_posterior_` to the normalized final forward-state distribution and `log_likelihood_` to that same recursion's terminal log-normalizer.
- Add an independent synthetic test that recomputes the final forward recursion from stored model parameters and asserts equality of both the terminal posterior and final log-likelihood.
- Keep 2- and 3-regime tests, transition-prior sensitivity tests, normalization tests, and invalid-input tests passing.

Do not treat this as a cosmetic issue; the state distribution used for subsequent predictions is one of the model's central numerical outputs.

## Blocking finding T2 — transition-prior semantics must be frozen, not merely made active

The frozen registry records `transition_prior=2` or `5`, but the adapter contract does not itself define the statistical interpretation. R4 defines it operationally as a symmetric Dirichlet pseudocount added to every expected transition count.

That is a coherent *possible* interpretation, and the sensitivity test proves the value is consumed; however, a parameter that now changes estimates still needs a clear frozen statistical definition. A passing binder test alone does not establish that the adopted interpretation matches the research protocol.

### Required developer correction

- Record the exact definition, update rule, and meaning of values 2/5 in the preregistration/model-configuration contract before any empirical results are inspected.
- State whether these values mean per-cell Dirichlet pseudocount mass or another quantity; explain the corresponding transition estimator formula.
- Version the contract and ensure the run manifest captures that version/hash. Do not silently rewrite the meaning of an already frozen field.
- Re-run synthetic checks showing the documented formula is implemented.

## Non-blocking observations

- The strict binding layer is materially stronger than R3 because it validates exact keys and domains and checks actual constructor fields.
- `survival_first_passage` remains correctly blocked given the current directional fixed-horizon target contract; do not enable it without an event-time/censoring protocol.
- The calibration helper correction supporting both one-dimensional positive-class vectors and two-column binary matrices is tested in R4.
- The first R4 setup failure and intermediate failing suite are appropriately recorded; they are not counted as scientific evidence.

## Final disposition

The R4 **synthetic and full-registry automation gate passed**, but this **independent code review does not pass**. The developer must implement T1, freeze the T2 statistical semantics in the versioned preregistration, rerun all tests and the full registry audit, and resubmit the exact commit for a new independent review.

No empirical fitting, holdout access, option P&L computation, strategy ranking, or strategy promotion is authorized by this report.

**Tester → Developer:** correct T1, make T2's definition an explicit versioned research-contract decision, then resubmit the exact new commit/report hashes.

**Developer → Tester:** preserve this BLOCKED decision unchanged and independently re-check final posterior/log-likelihood arithmetic and the versioned transition-prior contract on the resubmission.
