# Parameter binding and Markov-switching semantics audit — R4

Date: 2026-10-14  
Branch: `phase-08-prediction-param-audit-developer`  
Developer snapshot status: **R4 HOSTED SYNTHETIC/REGISTRY GATE PASSED; FRESH INDEPENDENT REVIEW PENDING**

## Purpose and restrictions

This is a code-contract and registry-parameter audit only. It does not authorize market-data access, fitting on market observations, holdout access, method ranking, option P&L, or strategy promotion. The untouched holdout remains sealed. Existing compatibility labels are not changed and empirical eligibility remains zero.

## Findings inherited from R3

- The existing file-mapping audit verified registry counts and adapter/test file existence, but did not prove that each registered parameter reached the intended constructor or model component.
- Bayesian `coefficient_drift` is a registry name while the adapter constructor calls the corresponding state-evolution setting `process_variance`. Binding must be explicit and preserve the exact value.
- Markov switching's adapter had only two regimes and ignored the registered `transition_prior` setting. The registry values are 2 or 3 regimes and transition prior 2 or 5.
- Temporal-convolution dropout was previously ignored by the adapter; it was subsequently implemented as training-time inverted dropout, with inference dropout-free. Its remaining issue was parameter-binding support.
- HMM's adapter is diagonal-Gaussian and therefore supports only the registered `covariance="diag"`; the value must be validated and never silently broadened.
- `survival_first_passage` remains incompatible with the currently frozen fixed-horizon directional label contract and stays blocked.

## R4 changes proposed for validation

1. Add an explicit, fail-closed binding schema for each supported prediction family. Each binder entry checks the exact model-parameter keys, allowed value domain, and adapter constructor names.
2. Map `coefficient_drift` to `process_variance` without changing the value.
3. Support Markov-switching models with 2 or 3 regimes.
4. Define the previously ambiguous `transition_prior` in this implementation as a symmetric Dirichlet pseudocount added to every expected transition-matrix cell count. Only the frozen values 2 and 5 are accepted. This is a proposed operational definition and requires independent methodological review; it is not represented as a definition supplied by the original registry.
5. Correct Markov log-likelihood accounting to use the forward-algorithm terminal normalization, and test normalized transition rows, initial probabilities and final state posterior.
6. Pass registered temporal-convolution channels/kernel/dropout to the adapter.
7. Keep survival/event-time methods blocked until their target, censoring, no-event and competing-risk semantics are separately preregistered and compatible.
8. Extend the mapping audit to walk the committed parameter shards and all 40,000 frozen configurations—not just confirm that source files exist.

## Expected registry accounting

- 1,000 method records / 40,000 configuration records across 20 registered families.
- 19 non-survival families have constructor-binding schemas; expected binding count is 38,000 configuration records if every non-survival record is valid.
- 2,000 survival-family configurations should be explicitly blocked with `SURVIVAL_EVENT_TIME_CONTRACT_NOT_IMPLEMENTED`.
- 426 methods are listed `ALLOW_IN_PRINCIPLE` and 574 are `BLOCK` by the separate compatibility screen. These labels do not confer empirical eligibility.
- Empirically eligible methods: **0**. Empirical fitting authorization: **false**. Market data loaded: **false**. Holdout accessed: **false**.

## Required verification sequence

1. Run the dedicated binder tests, including all 19 supported constructor maps and the unsupported survival family.
2. Run the Markov 2/3-regime tests and demonstrate that changing the registered prior changes the fitted transition matrix under fixed synthetic inputs.
3. Run the full adapter family synthetic test suite and Python compilation checks.
4. Recompute and verify every compatibility/configuration shard hash and record count; bind every one of the 40,000 configs.
5. Fail the gate on any unmapped key, unknown value, silent extra key, unexpected blocked family, arithmetic/shape mismatch, or broken digest.
6. Keep all market-data fitting and holdout flags false. Only after code and registry audit pass may the exact snapshot be submitted for independent review. No empirical fit may occur before that review and a separate data/label preflight gate.

## Snapshot status

This file records the R4 intent and implementation in the developer branch. At the time of writing, no R4 hosted run or independent reviewer decision has been verified. Do not interpret a successful synthetic run, if later obtained, as prediction skill or trading profitability.

**Developer → Tester:** independently audit the frozen prior definition, forward/backward arithmetic, 2/3-regime posterior normalization, all 38,000 supported parameter bindings, and the exact 40,000-row registry result. Do not authorize empirical fitting on code-only evidence.

**Tester → Developer:** return exact reproducible findings against the pinned commit and artifact hashes. Reject any mismatch; keep market data, holdout, option P&L and promotion blocked until all separate gates pass.


## Developer remediation/resubmission checkpoint — 2026-10-14

**Exact tested commit:** `28e192269a63030c03963e83767f1dc6d7c6a81e`  
**Hosted run:** [38463113199 — SUCCESS](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38463113199)  
**Artifact:** [11847406156](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38463113199/artifacts/11847406156)  
**Artifact ZIP SHA-256:** `c3e96cb549ba55781a729104f0319b71338d9965f9596aa7a4bcf629d9b07c5c`

The updated run passed 111 synthetic tests, compiled 20 prediction modules, and reconciled 1,000 method records / 40,000 configurations (38,000 supported parameter bindings and 2,000 explicitly blocked survival/event-time configurations). Compatibility remains 426 `ALLOW_IN_PRINCIPLE`, 574 `BLOCK`; empirically eligible methods remain zero.

T1 is corrected: convergence compares the post-M-step likelihood and a final forward pass recomputes the terminal posterior/log-likelihood from final stored parameters. A synthetic test independently reconstructs the recursion. T2 now has a versioned contract and preregistration amendment; this amendment remains proposed pending independent approval.

**Current gate:** developer automation **PASS**; independent review of the new SHA **PENDING**. No market-data fitting, holdout access, options P&L, ranking, or strategy promotion is authorized. Other preregistration `NOT_FROZEN_BLOCKED` fields remain unresolved.

**Developer → Tester:** review the exact SHA, numerical test, semantic contract pins and hosted artifact.  
**Tester → Developer:** return a fresh decision without rewriting the historical BLOCKED report.


## Final independent gate result — R6 PASS (2026-10-14)

The R4 parameter-binding/code-contract gate is closed on developer SHA `1bfba987629e793accbd218d87745a8f80cf8dbd`. Hosted run [38464388094](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38464388094) passed 111 synthetic tests, compiled 20 modules, and audited 1,000 methods / 40,000 configurations. Result: 38,000 bindings, 2,000 explicit survival/event-time blocks, 0 empirically eligible methods. Artifact [11847692839](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38464388094/artifacts/11847692839), ZIP SHA-256 `f8c7b8c30545772e28bf63ba5678f2809553bba224d17d479fba5bd1fdec6f0b`.

Independent decision: [R6 tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-param-audit-tester-r6/research/gates/PREDICTION_PARAMETER_BINDING_TESTER_REPORT_R6_2026-10-14.md) — **PASS** for this code subgate only. Empirical fitting remains blocked pending the full ten-horizon preregistration, frozen statistical/fold parameters, data/label provenance and authorization-enforcement gate. No market data, holdout or option P&L was accessed.

**Developer → Tester:** review the complete next preregistration/data-preflight bundle when committed.  
**Tester → Developer:** reject any unresolved `NOT_FROZEN_BLOCKED` field or unproven exact input/authorization binding.
