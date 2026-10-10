# PPR-3 Tester Review 1 — Configuration Matrix and Protocol Freeze

**Review date:** 2026-10-10  
**Branch:** `phase-07-tester`  
**Decision:** **REQUEST CHANGES — PPR-3 is not passed**  
**Allowed next work:** documentation/configuration correction and offline validation only. No PPR-4 source requests, data downloads, model fitting/tuning/scoring, final holdout access or option P&L.

## Exact snapshots reviewed

| Artifact | Developer blob SHA |
|---|---|
| Configuration matrix | `f55b46917404237cb32ab0c58795689905c04396` |
| Expanded candidate cells | `a208c3331f7cfde20922fc3d9f0847fac53a90cc` |
| Model settings | `d8373d6e9e997582695db7997636eece762c95c2` |
| Target/inference contract | `4822344b05923dba933a42f13b7b3d86754505b1` |
| PPR-3 protocol | `abd66d76d5a56be0227e91fc359bf4b672df0db8` |
| PPR-3 manifest | `cd51483a140fab8ca197b2dca1ab9982aca29a0e` |
| PPR-3 validator | `e03b6322ab07876dd2aa9766168e59fd3a2b9efb` |
| Offline workflow | `db379d1890a473ea09ca4fccf41ce30ee6d02a3b` |
| PPR-1 evidence matrix | `fe61751cac09089d0052bb92212dddd4a7b670dc` |
| PPR-2 registry crosswalk | `ac8491628913c5019d7a4b986339489b1dff1f14` |
| Literature registry | `2ee49ae119e61c8c523ed212c7f21bf15c5e8d7a` |

**Hosted exact-commit check:** [run 38071163481](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38071163481), success on trigger commit `0d287f3c25e1bf9c9bbaa7424e785d2ecb879cd4`. The log confirms the run checked out that exact commit, the PPR-1 structural validator passed, PPR-3 row/cell/target/grid/budget validation passed, and the manifest blob pins matched. Scope was offline documentation validation only; no market-data read, network/source request, model fit, tuning, scoring or holdout access occurred.

## Checks that passed

1. **Inventory arithmetic:** 80 configuration ledger rows, 72 rows counted against the 93-row cap, 71 active candidate configurations, one blocked SOFNN configuration, eight blocked/out-of-scope source/task records.
2. **Candidate expansion:** 1,183 unique configuration × feature-pipeline × horizon cells reconcile to the active configuration scopes. Family counts are 375 directional, 760 close-regression and 48 next-open regression cells. Pipeline and horizon totals reconcile to the expanded file.
3. **Settings/blocked tasks:** all matrix settings IDs resolve to an estimator template, alias or explicit blocked setting; the previously missing TCN/hybrid-regression templates are now present, and SOFNN is explicitly blocked.
4. **Tuning-grid cardinality and budget arithmetic:** the frozen tuning cells are R010 h1/2/3/5/10, R029 h1/2/3/5/10, R038 h1 and R041 h1. The RF grid lists 18 settings and the XGBoost grid eight. The declared candidate-cell fit budget is below 8,000.
5. **Exact-snapshot integrity:** the manifest pins the current source evidence, configuration, candidate cells, model settings, target contract, protocol, validator and workflow Git blob IDs; run 38071163481 verifies those pins against its exact checkout.
6. **Fail-closed governance:** all candidate cells remain `PROPOSED_NOT_AUTHORIZED`; the execution chain explicitly requires the PPR-4 data gate, PPR-5 code gate and PPR-6 exact-snapshot authorization.

## P1 — Separate native paper configurations from common-task adaptations

The earlier PPR-1 tester finding required separate rows for the paper-native configuration/task and the leakage-safe/common-task adaptation. PPR-3 still merges common tasks from different papers into a single candidate row and records multiple source IDs/aliases, for example:
- KNN regression across P01/P05;
- linear regression across P01/P05/P10;
- SVR across P01/P02/P04/P05;
- decision-tree regression across P01/P02/P05;
- LSTM regression across P01/P02/P10.

Merging an identical *common-task fit* is reasonable for multiple-testing control, but the current ledger does not separately enumerate the paper-native task/configuration and its fidelity status for each source. A source's own target, sample dates, split, features, reported metric and deviations are noted in aggregate fields; that is not a distinct native-task configuration row.

**Required correction:** add a row-level `PPR3_PAPER_NATIVE_TASK_LEDGER.csv` with one row for every individually named method in the uploaded-PDF fidelity ledger. Each row must carry a unique native-task ID, source paper/method, exact page locator, source-native target/output type, horizon, window, split, feature recipe and metric where stated, fidelity status, explicit missing/ambiguous details, disposition (`PAPER_NATIVE_DESCRIPTIVE_ONLY`, `BLOCKED_DATA`, `BLOCKED_METHOD`, `OUT_OF_SCOPE_DIFFERENT_TARGET`, or another explicit justified status), and links to the common-adaptation config ID(s). Do not fit these native configurations under this correction; the native ledger is documentation only. Do not call a common adaptation an exact replication.

## P1 — Tuning fit-call formula is inconsistent with the described refit step

The model settings say each hyperparameter configuration uses up to five chronological inner folds and describes “after selecting parameters, refit once on the complete outer training prefix”. However, the stated tuning count `6 × (five folds + one refit)` for every candidate setting counts a full-training refit for **every** hyperparameter setting, while the written algorithm says the refit occurs only after selection. The outer-fit budget already includes the final selected estimator fit for each cell/seed. These are different execution plans and must not be left to implementation interpretation.

**Required correction:** freeze one explicit algorithm and recompute all arithmetic:
- preferred bounded design: for each hyperparameter setting, fit only the five inner chronological folds; select the setting by mean validation MAE; then let the already-counted outer fit(s) train the selected setting on the full outer training prefix and predict the hold-forward validation segment. Under that design, tuning inner-fold calls are `6 RF cells × 18 settings × 5 folds + 6 XGBoost cells × 8 settings × 5 folds = 780` additional fit calls; the selected outer fits are already inside the outer-fit budget.
- If a different refit design is desired, define it explicitly and include every distinct estimator fit in both the algorithm and the numeric budget.

Update `PPR3_MODEL_SETTINGS.json`, `PPR3_CONFIGURATION_MANIFEST.json`, `PPR3_PROTOCOL_FREEZE.md` and the offline validator together. Add a unit/contract assertion that the formula, counts and tuning cells reconcile.

## P2 — Freeze the meaning of the FLAT label

The common target uses tolerance (10^{-8}), which is effectively an exact-zero/numerical tie label, not an economically meaningful “small move/no-trade” state. That label can be very rare. It is acceptable to keep this fixed zero-return tie definition, but the manuscript and report must not describe it as a no-trade or cost-neutral class.

**Required correction:** state explicitly in the target contract and protocol that FLAT means only a numerical zero-return tie under the fixed tolerance; it is not a trading-cost or no-trade classification. Do not tune the tolerance after inspecting outcomes. If a future economically neutral band is studied, it needs a separate predeclared exploratory protocol, not a post-result change to this label.

## P2 — Regression-test the RF `max_features` numeric type

Manual review caught a JSON serialization bug: intended float `1.0` had become integer `1`, which means a single feature in scikit-learn rather than all features. The current settings/grid have been corrected to `1.0`, and the exact-snapshot CI passed after that correction. The validator still only checks grid lengths, not this semantic difference.

**Required correction:** add offline validator assertions that the RF default and grid values intended to mean “all features” parse as a floating-point `1.0`, not integer `1`; include the explicit candidate-settings list in that check.

## Scope decision

**REQUEST CHANGES.** The offline arithmetic and hash checks pass, but PPR-3 is not yet a sufficiently precise source-to-config freeze because native tasks are not separately enumerated, and the tuning fit plan is ambiguous. Correct those items and resubmit exact new blobs. Do not start PPR-4 source requests or model work before a later tester PASS.

**Developer → Tester:** Re-review the corrected native-task ledger, tuning algorithm/budget, FLAT-label wording and RF semantic validator against exact latest hashes.

**Tester → Developer:** Keep all data acquisition, model fitting/tuning/scoring, final-holdout access and option P&L blocked until a new exact-snapshot PASS specifies the next allowed gate.
