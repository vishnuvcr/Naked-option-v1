# Uploaded-Paper Claim Verification Notes — 2026-10-11

- **Branch:** `phase-07-developer`
- **Purpose:** preserve targeted, render-verified source results and internal consistency checks from the uploaded PDFs.
- **Scope:** literature evidence only. These observations do not authorize new data requests, model fitting/scoring, holdout access, or options P&L testing.
- **Method:** target pages were rendered to PNG and inspected for table/page layout; text extraction was used only as a supporting aid.
- **Source provenance:** exact local PDF SHA-256 values are included below so a later reviewer can confirm the inspected upload version.

## 1. Naik & Inamdar (2024), `IJCSE-V11I10P106.pdf`

**Inspected pages:** PDF p. 5–7 (journal pp. 50–52); visually checked PDF p. 6 and p. 7.  
**PDF SHA-256:** `896b4e9a4792d5fef39f78dc12c4b1c94fa47cd1eb55cee1a6b001db7871e5ae`

### PCR decision-rule coverage gap

PDF p. 7 defines bearish as (PCR < 0.8), neutral as (0.8 \le PCR \le 0.9), and bullish as (PCR > 1). This leaves the interval (0.9 < PCR \le 1) without a stated class. The example table on PDF p. 6 labels a PCR of **0.91** as **Neutral**, even though 0.91 is outside the stated neutral interval and below the stated bullish threshold. This is a source-internal rule/example mismatch, not a project experiment. Do not silently extend the neutral threshold in a replication; keep the source-native rule AMBIGUOUS until a faithful source clarification or explicit project adaptation is approved.

### Headline metrics do not share a fully specified evaluation contract

The results prose reports LSTM accuracy of 98% and precision of 99%, and BERT sentiment accuracy/precision of 99%/99% (PDF p. 5). The conclusion reports 99% accuracy and 100% precision for the combined framework (PDF p. 6). These may refer to different components, but the inspected text does not provide a common denominator, fully specified scored target, or clearly aligned temporal test sample sufficient to reconcile them. Store as author-reported claims with unresolved metric/target linkage; do not compare them to directional hit rate or accept them as project performance.

### Formula reproducibility limitation

The score formula on PDF p. 7 combines inverse India VIX, FII, sentiment score and the PCR-derived value using a described “Market Entropy Constant,” but a reproducible estimation/calibration recipe and compatible scale/units for the components are not specified in the displayed derivation. It is not sufficiently defined to implement faithfully without an explicit adaptation. The paper's text alternates among price, direction and PCR-derived sentiment examples; keep the precise forecast label and endpoint unresolved unless a separate locator establishes them.

## 2. Khan et al. (2023), `jrfm-16-00423.pdf`

**Inspected pages:** PDF p. 16–17 and p. 20; visually checked model summary and backward-elimination tables.  
**PDF SHA-256:** `c890cdd7bee281352531a69470f8b80469e248c94978b7b7840addc052810634`

### LSTM parameter-count arithmetic mismatch

On PDF p. 17, prose says the selected LSTM has **330,369** trainable parameters. The displayed model summary lists layer parameters of 17,920 (first LSTM), 12,416 (second LSTM), 0 (dropout), and 33 (dense). The displayed layer sum is:

`17,920 + 12,416 + 0 + 33 = 30,369`

The summary itself also prints **Total params: 30,369**. Therefore the prose differs from both the layer arithmetic and the printed total by a factor of roughly 10. The evidence supports an internal reporting discrepancy; the intended model parameter count should not be guessed beyond the arithmetic shown.

### In-sample variable selection and result interpretation

The backward-elimination tables on PDF pp. 15–17 describe using the full 3,986-row set for OLS feature selection before feeding selected fields to the LSTM. Table 7 reports (R^2=1.000) on the 3,986 observations (PDF p. 16). These are source-reported in-sample/selection figures, not valid proof of future predictive performance. The project's leakage-safe adaptation must redo any selection within each training window and report chronological out-of-sample results; it must not reuse the paper's full-sample selected feature list for a confirmatory evaluation.

PDF p. 20 visually compares a plotted 5–31 March 2021 window for LSTM/backward-elimination LSTM/original prices. A plotted closeness claim is not a replacement for a numeric, untouched out-of-sample result table with a defined forecast origin and baseline.

## 3. Bansal, Goyal & Choudhary (2022), `1-s2.0-S1877050922020993-main.pdf`

**Inspected pages:** PDF p. 14–15 (journal pp. 260–261), especially Table II and its interpretation.  
**PDF SHA-256:** `b8a45dd5bde5d268365beb7be16856c35e139a3382ca26aeae9c705aa7d87978`

Table II's reported average (R^2) values are KNN **−2.42**, Linear Regression **−2.27**, SVR **−1.69**, Decision Tree **−2.33**, and LSTM **−0.11**. The prose on PDF p. 15 describes the LSTM value “−0.11” as “quite close” to 1. This is an interpretation/sign inconsistency: −0.11 is negative, not close to +1. LSTM is the least-negative/strongest reported average among these five methods in the table, but a negative (R^2) conventionally indicates performance worse than a test-set mean predictor under that score definition. The source's “high accuracy” framing must therefore remain author-reported and qualified by its own (R^2) table. This paper evaluates 12 individual-company series; it is not an exact NIFTY 50 index replication.

## 4. Sain & Singh (2026), `CureusJournals_1986620261002-185337-d4go5h.pdf`

**Inspected pages:** PDF p. 10, p. 17–18 and p. 34; visually checked the results table and conclusion.  
**PDF SHA-256:** `8214d3ef97bc4752fc381a73f2eb7de1d01d483d64a6991cd3a4aef993092d95`

The displayed historical-window/model table (PDF pp. 17–18) contains substantial variation and very poor SVR generalization in the visible rows:
- 5-year row: SVR test (R^2=-47.8984), test RMSE 6,079.98 and test MAE 6,019.04.
- 10-year row: SVR test (R^2=-154.8147), test RMSE 12,296.97 and test MAE 12,255.35.

The paper's conclusion (PDF p. 34) itself reports deep negative (R^2)/very large errors for some models and says simple linear models were the only methods consistently beating the naive persistence baseline over all windows; it also notes tree-model extrapolation limitations. These values are **negative source results to preserve**, not a project metric or proof of an independent error. The exact relationship between every displayed table and the different open/close target phases should be retained from the paper's table context; do not collapse all rows into a single undifferentiated “model accuracy” ranking.

## Reproducibility checks and status

1. PCR rule test: the set of stated class conditions does not cover all PCR values; (PCR=0.91) has an example label but falls outside its stated neutral interval.
2. LSTM parameter arithmetic: displayed layer parameters sum to 30,369, matching the model summary but not the 330,369 stated in prose.
3. (R^2) interpretation: the Bansal paper's “close to 1” wording conflicts with a reported −0.11 average.
4. Result preservation: severe negative SVR results in the Cureus table are retained alongside the author's written caveats; no best-only selection was made.
5. No model was fitted, no market source was queried, no holdout data were opened, and no reported paper metric has been relabelled as project evidence.

These findings should feed paper-level fidelity and method mapping. They do **not** change frozen PPR-3 files, active configuration counts, methods, targets, multiplicity rules or authorization flags. Any proposed new or adapted model remains subject to its pre-registered method and exact-snapshot tester gate.

**Developer → Tester:** Independently recompute the PCR condition coverage and the LSTM parameter sum from the rendered pages; verify each (R^2) claim/result locator and identify any overstatement in these notes.

**Tester → Developer:** Return only source-specific corrections on `phase-07-tester`. Do not authorize data acquisition, fitting, holdout access or strategy tests from this literature audit.


## 5. Shaha (SSRN), `ssrn-3323746.pdf` — CCI option strategy (strategy-only source)

**Inspected pages:** PDF p. 9–10 (printed pp. 1444–1445); visually checked Tables II–V and the surrounding count/statistic discussion.  
**PDF SHA-256:** `06791b5d34c59611249778cf67099f0741db27a5ec062c3ca548cf5006f76798`

This paper is a historical option-trading strategy study, not a paper-native fitted NIFTY spot-direction forecaster. Its reported numbers are therefore not part of this project's prediction-model result set, and no CCI options P&L was run.

The sample counts are internally inconsistent:
- Table II (PDF p. 9) states 68 total trades, including 43 profitable and 25 loss-making trades. Those category counts sum to 68.
- The prose immediately below Table II describes profitable trades as **42/68**, while retaining 25/68 losses; 42 + 25 = 67, conflicting with the table's 43 winners.
- Table III (PDF p. 10) lists observed profitable/loss-making counts as 43 and 25, but its observed total row says **80**. The two category counts sum to 68, not 80. Its percentages 63.25% and 36.75% also correspond approximately to 43/68 and 25/68, not a denominator of 80.
- Table III's (chi^2) statistic of 4.765 is consistent with counts 43 and 25 compared against expected counts 34 and 34: ((43-34)^2/34+(25-34)^2/34=4.7647\ldots). This arithmetic supports 68 as the intended tested total for that specific calculation, but it does not authorize silently correcting the published row from 80 to 68.
- Table V then uses degrees of freedom 68 for a one-sample test, another sample-size choice that should be checked against the number of observations/test setup before any inferential result is repeated.

Disposition: record the count/statistic inconsistencies as source limitations and do not reuse its reported strike rate, annual return or p-values as verified strategy evidence. Any future CCI strategy reproduction belongs to the separately gated options phase and requires its own data, exact rules, costs/slippage, trade-count reconciliation and independent strategy tester.
