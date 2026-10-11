# Uploaded-Paper Finding → PPR-3 Configuration Crosswalk Supplement

- Date: 2026-10-11
- Branch: `phase-07-developer`
- Type: literature/configuration traceability only; no frozen configuration is changed.
- Related claim audit: [PAPER_CLAIM_VERIFICATION_NOTES_2026-10-11.md](PAPER_CLAIM_VERIFICATION_NOTES_2026-10-11.md).
- Pinned source artefacts consulted:
  - `PAPER_SOURCE_EVIDENCE_MATRIX.md`: `fe61751cac09089d0052bb92212dddd4a7b670dc`
  - `PAPER_PREDICTION_METHOD_CROSSWALK.md`: `58f1f054fee33956c98d93a396fbca73e1397b0b`
  - `PPR3_PAPER_NATIVE_TASK_LEDGER.csv`: `7c5c48e015b6b3642e0bdfdcaa17f00ed7fa035e`
  - `PPR3_CONFIGURATION_MATRIX.csv`: `9b47b2de7ad04fee26c6d5075772b56b9486df74`
  - `PPR3_CONFIGURATION_MANIFEST.json`: `72ed1935917bf722a2cf47a184e73ed24b71a690`

## Why this supplement exists

The source documents already identify the 15 PDFs and the frozen PPR-3 configuration ledger. This supplement connects the recent rendered-page audit issues to the corresponding native-task/configuration rows so they cannot be lost when later researchers select shared model families. The configuration matrix, 1,188 candidate cells, 112-method registry, task contract, target labels, and scope gates are not modified here.

| PDF / paper ID | Existing native-task rows | Current common config overlap | Verified source issue / required handling | Current scientific disposition |
|---|---|---|---|---|
| `1-s2.0-S1877050922020993-main.pdf` / P01 (Bansal et al.) | NT001–NT005 | Shared regression models, including common KNN/linear/SVR/tree/LSTM adaptations | Table II average LSTM (R^2=-0.11), while prose describes this as “close to” +1. Keep the numeric value and source/target caveat; do not carry the paper's high-accuracy phrase into a NIFTY-direction claim. Dataset is 12 single-stock series and paper date/split details remain ambiguous. | Source-native replication not completed; a NIFTY configuration is a common-task adaptation only. |
| `CureusJournals_1986620261002-185337-d4go5h.pdf` / P05 (Sain & Singh) | NT032–NT044, including 12 regressors and naive persistence | Shared regression settings; paper-native open/close targets/windows are recorded separately in ledger | Preserve high and low performance rows across 5/10/20-year windows, including severe negative SVR test (R^2) values and the source's own tree-extrapolation caveat. Do not average across incompatible windows/targets or convert price regression into directional accuracy without an explicit derived label. | Source-native next-open/next-close tasks are distinct from common NIFTY close/direction adaptations; data-window/PIT gate still applies. |
| `IJCSE-V11I10P106.pdf` / P07 (Naik & Inamdar) | NT047–NT052 | C009 LSTM direction; C010 BERT+LSTM fusion; feature pipelines include flow/options and timestamped sentiment | PCR rule leaves (0.9<PCR\le1) unclassified but labels PCR=0.91 neutral in an example. Accuracy/precision summaries vary between model-result prose and conclusion without a common target/denominator contract. Keep P07 metric claims unresolved and require exact target plus point-in-time news/FII/DII/VIX/PCR vintages before any later experiment. | Combined model is not equivalent to a generic LSTM; it is not established as reproduced. Current data/model gates block fitting. |
| `jrfm-16-00423.pdf` / P14 (JRFM BE-LSTM) | NT076–NT079 | R062 LSTM adaptation; R063 leakage-safe BE-LSTM adaptation | Text states 330,369 trainable parameters; layer summary sums to 30,369. Source feature-selection tables use all 3,986 observations. Retain the parameter-count ambiguity and redo feature selection inside chronological training windows for the leakage-safe adaptation. | Paper-native selection result is not causal OOS evidence; exact source replication and project adaptation must remain separate. |
| `ssrn-3323746.pdf` / P15 (Shaha CCI) | NT080 strategy-only CCI option rule; NT081 project CCI spot-direction proxy | C023 is recorded as a project-defined adaptation; not an exact source reproduction | Table II lists 43+25=68, prose says 42+25=67, Table III prints total 80, while its chi-square value 4.765 matches 43/25 versus 34/34, total 68. Do not repeat published strike rate/annual return/p-values as verified evidence, and do not use the CCI option rule to bypass the separately gated strategy phase. | Native paper is strategy-only. NT081 is an explicit project adaptation, not the paper's option strategy and not a tested result. |

## Gate and evidence rules carried forward

1. `AUTHOR-IMPLEMENTED` in a paper-native ledger means that the source says the method was used; it does not mean this repository has run it.
2. Shared estimator overlap does not establish exact source replication if data, features, target, horizon, split, or metric differ.
3. The PPR-3 configuration files and manifest remain unchanged; this supplement neither adds candidate cells nor changes model-fit flags.
4. The split-recovery request gate remains separately denied. No live source access, prediction fitting/scoring, holdout access or strategy/P&L evaluation is authorized by this literature review.
5. Every unresolved source issue remains explicitly unresolved until a source-specific check settles it. A correction in project code must be a registered adaptation and pass its own gate.

**Developer → Tester:** Verify each listed native-task/config identifier against the pinned CSV files and confirm that source issues are not mapped into changed/frozen configurations.

**Tester → Developer:** Return a scoped traceability review on `phase-07-tester`; preserve all empirical/live denials and keep paper-native versus project-adaptation status distinct.
