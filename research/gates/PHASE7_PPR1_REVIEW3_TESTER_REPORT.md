# PPR-1 Tester Re-review 3 — Claim-Level Source Matrix and Inference Contract

**Review date:** 2026-10-10  
**Branch:** `phase-07-tester`  
**Decision:** **PASS WITH SCOPED RESTRICTIONS**  
**Authorized next scope:** PPR-2 literature-registry crosswalk only. This decision does not authorize new source requests, model fitting/tuning/scoring, holdout access, option P&L or strategy research.

## Exact reviewed artifacts

| Artifact | Branch | Blob SHA |
|---|---|---|
| Claim-level evidence matrix and individual method fidelity ledger | `phase-07-developer` | `fe61751cac09089d0052bb92212dddd4a7b670dc` |
| Machine-readable target/inference contract | `phase-07-developer` | `c85df8b0c2f7e6d5048de7e014f4187170cebb41` |
| Protocol amendment | `phase-07-developer` | `7ecff1be9aa2d6c2c8d5abbf89457113e382b1e3` |
| Uploaded-paper crosswalk | `phase-07-developer` | `58f1f054fee33956c98d93a396fbca73e1397b0b` |
| Offline contract validator | `phase-07-developer` | `6c723693e058470c78a1c4f93908b979eedfffe9` |
| Exact-commit offline workflow | `phase-07-developer` | `783fa9e57ca368bf1e7b0db9a3c91a7fced3380c` |

**Hosted exact-snapshot receipt:** [run 38069062885](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38069062885), success. The job log confirms checkout commit `676bffb9b36b4f499d74d0072c42a15c360fc6c5`, exactly the workflow-triggering commit. Validator output: “PASS: source matrix, target/inference contract, search bounds and fail-closed flags.” It explicitly performed offline document checks only; no data acquisition or model fitting.

## Review work and findings

1. **Source traceability:** The matrix covers all 15 uploaded PDFs and has separate claim categories for methods, sample/date span, target/horizon, split, metrics/results and limitations. The additional individual fidelity ledger separates named estimators, architecture hybrids, input components, diagnostics, strategy-only methods and adaptations. Method-level locators point to physical PDF viewer pages. Where the source is ambiguous, the artifact explicitly retains `AMBIGUOUS` instead of inferring an implementation.
2. **Fidelity classifications:** The ledger distinguishes `AUTHOR-IMPLEMENTED`, `BACKGROUND-ONLY`, `AMBIGUOUS`, and `PROJECT-ADAPTATION`. This prevents treating every model cited in related work as a model the paper evaluated. The 15-paper matrix remains distinct from the repository's separate 36-record literature registry.
3. **Source discrepancies are preserved:** ISMLA's option-like `callOpen/callHigh/callLow/callClose` columns leave its claimed NIFTY spot target unresolved; JIER uses inconsistent MA periods/date spans and reports crossover t=-1.271, p=.1079; IJSDR's 83.88% and Naik/Inamdar's reported accuracy/precision remain non-comparable without full target/formula details; Kumar & Sharma's 99.2152% claim is correctly located in the abstract but remains undefined; JRFM's published full-sample backward-selection path is flagged as leakage-prone for causal validation; CCI's table has a 68-trade versus 80-total inconsistency. These items are not promoted to validated project results.
4. **Target/output schema:** The common direction task is explicitly three-class `DOWN/FLAT/UP` and uses multiclass Brier loss. Common close regression and next-open regression are separate families with explicit persistence baselines. Each base configuration is assigned one target/output schema; distinct tasks cannot be pooled in the same max-statistic family.
5. **Inference:** The JSON freezes a one-sided familywise max-studentized mean loss-improvement test; candidate paired loss differentials are null-centered before moving-block resampling; one common decision-origin index is used per family; within-family block length is consistent and set to max(5, the longest family horizon); 10,000 replicates and seed 20261010 are fixed; adjusted p-value and simultaneous max-statistic 95% confidence interval formulas are given; an incomplete planned cell blocks family-level promotion rather than being silently dropped.
6. **Search budget and guardrails:** Base configurations include task/target schema, total cap 80; up to four feature pipelines and five common horizons yield at most 1,600 outer cells; three seeds give at most 4,800 outer fits; bounded tuning and total fit-call limits are expressed in the contract. The offline validator checks matrix coverage, target families, key inferential fields, budget arithmetic and fail-closed flags.
7. **Workflow integrity:** The workflow now checks out `${{ github.sha }}`, not the moving branch name, and run 38069062885 confirms the exact-trigger commit. Previous validator failures (runs 38068895685 and 38068938072) are preserved and the string-check defect was corrected before this exact-snapshot success.

## Remaining restrictions

- The PPR-3 configuration manifest, source-availability manifest and execution implementation do not yet exist as reviewed executable artifacts. This PASS approves the uploaded-PDF evidence/crosswalk gate and permits PPR-2 documentation-only reconciliation, not execution readiness.
- PPR-2 must map every row in the 36-record literature registry to a paper/method row, background-only item, explicit exclusion, or unresolved/blocked status. It must not fetch data or add models to the confirmatory universe.
- All unresolved target, sample-window, metric and source-vintage matters must survive into the registry/configuration manifest as explicit ambiguity or deviation.
- The role-separated tester report is generated in the same connected assistant session; it is not represented as a separate human reviewer or independently hosted LLM agent.

## Gate decision

**PASS WITH SCOPED RESTRICTIONS — PPR-2 literature-registry reconciliation only.** PPR-1 is complete for the 15 uploaded PDFs as a sourced inventory with explicit ambiguity tags. This is not an empirical-model approval and does not certify any paper-reported accuracy or profitability claim.

**Developer → Tester:** Begin PPR-2 by reading all 36 literature-registry records, map each record to the uploaded-paper ledger/background/exclusion/status, and submit the exact mapping for re-review. Do not fit models or pull data.

**Tester → Developer:** Audit mapping completeness, duplication, unjustified exclusions, source-to-method match and preservation of ambiguity; authorize only PPR-2 if the exact mapping passes.
