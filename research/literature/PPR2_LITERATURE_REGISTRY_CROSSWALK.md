# PPR-2 Literature Registry Reconciliation — 36 Records

**Date:** 2026-10-10  
**Branch:** `phase-07-developer`  
**Status:** developer draft submitted for PPR-2 tester review; no source acquisition or model fitting authorized.

## Aim and scope

PPR-2 maps every row of `LITERATURE_REGISTRY.csv` (L001–L036) to its role in the research program and to the 15 PDFs uploaded in this project conversation. The purpose is to prevent a background citation, source page, or model family that merely resembles a paper from being treated as an exact replication target.

**Row-level mapping:** [PPR2_LITERATURE_REGISTRY_CROSSWALK.csv](PPR2_LITERATURE_REGISTRY_CROSSWALK.csv).

## Coverage summary

- Registry records: **36**
- Crosswalk rows: **36**
- Duplicate or missing source IDs in the draft mapping: **0**
- Exact PDF matches among the 15 uploaded papers: **0** (this explicitly means none of the 36 bibliography records has yet been established as the same source as one of the 15 uploaded PDFs; some have conceptual/model-family overlap).
- Registry IDs L001 through L036 are represented once each.
- One semantic CSV alignment defect in the existing registry was found and corrected during this pass: L003's URL had been placed in the `related_hypotheses` column and its subsequent fields were shifted. The correction is in the current source registry and is validated by the existing RFC-style registry check.

## Dispositions

| Record group | IDs | Research role | Current disposition |
|---|---|---|---|
| L001–L007 | 7 records | Adaptive Markets theory and statistical/multiple-testing methods | Methodology / theory only; not prediction models |
| L008–L011 | 4 records | Technical-rule and accounting/technical empirical evidence | Full-text method extraction needed before claiming a paper-native implementation |
| L012–L018 | 7 records | Option-return, order-flow, option-strategy, IV-surface and option-price prediction literature | Separate targets; conceptual overlap only with F-family hypotheses; not interchangeable with NIFTY spot direction |
| L019–L024 | 6 records | Official NSE India VIX, derivatives, participant-flow and index-history sources | Documentation/data-source leads only; no data fetch initiated |
| L025–L026 | 2 records | SEBI retail trading outcomes/behaviour reports | Regulatory context, not predictors |
| L027–L030 | 4 records | NIFTY/India VIX high-frequency relationships, VIX direction forecast, spillovers | Different target/frequency or contextual evidence; any adaptation needs a separate task declaration |
| L031–L034 | 4 records | Recent NIFTY options microstructure, XGBoost, news sentiment, wavelet/cross-market claims | Replication targets; source depth ranges from abstract-only to metadata-only; results unverified |
| L035 | 1 record | NIFTY options variance-risk-premium strategy | Strategy/performance literature; out of the current prediction-only gate |
| L036 | 1 record | Public NIFTY-direction code repository | Open-source replication target; README claims and metrics are not independently validated and the code was not executed |

These dispositions classify the **role of each source in this project**; they do not certify the truth of all source contents. The detailed CSV lists `review_depth`, exact PDF match, concept-only overlap, source-native task, next action and limitations for every row.

## Evidence-depth control

The current crosswalk explicitly varies the strength of inspection. In particular, L032 and L034 remain metadata-only, L031 abstract-verified, L033 abstract/metadata checked, and L036 README-verified only. These sources cannot be promoted to exact replication or performance evidence until source text/code, target labels, timestamps, splits and metric formulas are checked. Other rows marked `REGISTRY_AND_REVIEW` refer to the existing literature synthesis and registry entry, not a new full-text re-audit of every original paper.

## Relationship to the 15 uploaded PDFs

The uploaded-paper evidence matrix (PPR-1) has 15 paper-level sections and a named-method fidelity ledger. PPR-2 marks all 36 registry records as `NONE_EXACT` against those 15 PDF identities. It records concept/method overlap separately (for example, option-flow sources overlapping with F03–F05, or recent direction models overlapping with D-family methods). Conceptual overlap is not replication, and a citation alone does not mean the corresponding project method has been run.

## Registry schema correction: L003

The former L003 row had values shifted across columns: the URL appeared under `related_hypotheses`, the family IDs under `url_or_doi`, and the replication requirement/status were displaced. The row was repaired to the expected 11-column schema. Source ID, title, year, source class/evidence class and data-snooping note were retained; corrected URL: `https://doi.org/10.1111/0022-1082.00163`. The error and correction are part of the PPR-2 log.

## Next gate

The next permissible action is **PPR-2 tester review** of the exact registry and crosswalk blobs plus the offline validation result. If it passes, the next permitted scope is PPR-3 **documentation-only** configuration manifest and protocol freeze. PPR-2 does not authorize:
- public/web or exchange-source pulls;
- full-history market data, HF_TOKEN use or any new paid/broker-source request;
- training, tuning, scoring or holdout inspection;
- option P&L, brokerage/slippage modelling or strategy optimization.

**Developer → Tester:** Review the 36-row CSV against the source registry; verify the L003 correction, completeness, source-role classifications, exact-vs-conceptual overlap and evidence-depth tags.  
**Tester → Developer:** Return PASS/REQUEST CHANGES for the exact snapshot and, if passing, authorize PPR-3 documentation-only configuration freezing.
