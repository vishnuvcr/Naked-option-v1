# Uploaded Paper Method Coverage Audit

**Audit date:** 2026-10-10  
**Branch:** `phase-07-developer`  
**Status:** FIRST-PASS INVENTORY — NOT A COMPLETE FULL-TEXT METHOD REVIEW  
**Research scope:** Prediction methods first. Option strategy papers are inventoried but strategy/P&L research remains outside the current prediction-only gate.

## Executive finding

The repository has a finite registry of 112 methods across Families A–J and a literature registry of 36 source records. These are useful research controls, but neither count establishes that every method from each uploaded PDF was implemented and independently replicated.

The current conversation contains 15 PDF files. A first-pass title/abstract/early-page extraction identified the topics below. Exact paper-specific settings, datasets, target/horizon, feature definitions, split protocol, baseline, metric definitions and reported results have **not** yet been reconciled for every paper. Unless a separate result artifact and independent tester report are linked, mark the paper-level method as **NOT VERIFIED AS REPLICATED**. Broad overlap with a method family is not an exact replication.

## Uploaded-PDF inventory

| # | Uploaded file | Identified paper / method focus | Potential registry overlap | Paper-specific reproduction status |
|---:|---|---|---|---|
| 1 | `1-s2.0-S1877050922020993-main.pdf` | *Stock Market Prediction with High Accuracy using Machine Learning Techniques*; comparative ML/DL forecasting | Families C/D; exact model mapping still to extract from the full methods/results sections | NOT VERIFIED AS REPLICATED |
| 2 | `1912.07700v1.pdf` | *A Robust Predictive Model for Stock Price Prediction Using Deep Learning and Natural Language Processing*; multiple classical/ensemble models, LSTM and a sentiment/SOFNN component | C/D/H; SOFNN-style sentiment method needs an explicit mapping | NOT VERIFIED AS REPLICATED |
| 3 | `50375.pdf` | *Developing A Machine Learning-Based Options Trading Strategy for the Indian Market*; options trading signal/policy with XGBoost/LSTM and option-chain/Greek context | D/F/J; strategy economics belong to the later, currently blocked options phase | NOT VERIFIED AS REPLICATED |
| 4 | `9472-Article Text-11108-2-10-20231228.pdf` | *An Efficient Approach to Forecasting the NIFTY-50 Indian Stock Market's Daily Closing Price with Artificial Neural Networks*; SVM, RBF, MLP and SLP comparison, with currency/institutional-flow inputs | C/D/G | NOT VERIFIED AS REPLICATED |
| 5 | `CureusJournals_1986620261002-185337-d4go5h.pdf` | *Open and Close Price Forecasting of the NIFTY 50 Stock Index Using Machine Learning: A Multi-Window Study of Feature Engineering and Model Tuning*; 12 supervised models versus persistence across 5-, 10- and 20-year windows, raw versus indicator-augmented inputs | A/B/C/D; recent 2026 paper not assumed to be covered by older family runs | NOT VERIFIED AS REPLICATED |
| 6 | `D0801051829.pdf` | *Options Trading Strategy: A quantitative study from an Investor's POV*; option-pricing/payoff and strategy comparison | F/J; not a directional-prediction replication by itself | NOT VERIFIED AS REPLICATED |
| 7 | `IJCSE-V11I10P106.pdf` | *Bridging Temporal Dependencies and Sentiment: A Comprehensive Approach to NIFTY 50 Index Prediction*; LSTM plus BERT-based news sentiment and features including FII/DII, India VIX and put-call information | D13, H01, G14/G15/G16, F03 | NOT VERIFIED AS REPLICATED |
| 8 | `IJNRD2205074.pdf` | *Options Trading Strategies for the Indian Market — An Effective Financial Derivative Tool*; options strategy/risk-return discussion | F/J; detailed method extraction is still required | NOT VERIFIED AS REPLICATED |
| 9 | `IJSDR2309053.pdf` | *NIFTY-50 Stock Prediction Master*; LSTM/deep-learning prediction | D13 | NOT VERIFIED AS REPLICATED |
| 10 | `ISMLA+7481.pdf` | *Deep Learning Approaches for Stock Price Prediction: A Comparative Study on Nifty 50 Dataset*; linear regression, LSTM, GRU, CNN, RNN, TCN and hybrid architectures | C/D13–D15; exact configurations and evaluation protocol need reconciliation | NOT VERIFIED AS REPLICATED |
| 11 | `JIER-+Vol.+5+No.+3+(2025)+-+Dr.+Deepesh.Formated.pdf` | *A Study of the Impact of Moving Averages on Predicting Stock Market Trends: A Study of NIFTY 50*; moving-average trend rules | B01/B04 family vicinity; exact average definitions and parameters not yet matched | NOT VERIFIED AS REPLICATED |
| 12 | `Stock Market Prediction of NIFTY 50 Index Applying Machine Learning Techniques.pdf` | NIFTY 50 forecasting paper; abstract emphasizes RNN, LSTM and CNN comparisons | D13–D15 | NOT VERIFIED AS REPLICATED |
| 13 | `Stock_Market_Index_Forecasting_of_Nifty.pdf` | *Stock Market Index Forecasting of Nifty 50 Using Machine Learning Techniques with ANN Approach*; feed-forward ANN/MLP and back-propagation | D12 and baseline/technical-feature families | NOT VERIFIED AS REPLICATED |
| 14 | `jrfm-16-00423.pdf` | *Forecasting of NIFTY 50 Index Price by Using Backward Elimination with an LSTM Model*; LSTM versus backward-elimination LSTM with OHLCV/RSI variables | D13 and B03 | NOT VERIFIED AS REPLICATED |
| 15 | `ssrn-3323746.pdf` | *An Empirical Study on Options Trading Strategy Using Commodity Channel Index for NSE's Nifty Options in India*; CCI-triggered option rules and return/risk/strike-rate analysis | Potential Family B indicator and later options-economics mapping | NOT VERIFIED AS REPLICATED; CCI is not an explicit standalone row in current B01–B13 registry |

## Interpretation

1. **No claim of exhaustive paper-method testing is permitted at this checkpoint.** Phase 1's literature/method-registry gate passing means a registry and governance process exist; it does not certify every paper-specific experiment as replicated.
2. Some paper methods overlap with families already tested in the broader program, but overlap is not proof that the paper's exact feature construction, estimator, horizon, split, hyperparameters or baseline were run.
3. Methods that require option-contract observations, news/sentiment history, FII/DII series or other unavailable inputs must be marked as data-blocked only after a documented free-source search and data-quality gate. A missing source must not silently become a test pass.
4. The current Phase 7 checkpoint remains prediction-only. The latest daily cross-market extension is a documented negative result; the Dhan single-row sample has not been accepted into training/validation, and official source/mapping checks still gate any model rerun.
5. Do not add CCI or any other newly identified method to the frozen registry and run a final-test experiment in the same step. First write an exact protocol amendment, record its hypothesis/configuration and multiplicity treatment, and obtain independent tester approval.

## Required next substeps

- **P1 — Full-text method extraction:** inspect each paper's Methods/Experimental Setup/Results tables and extract the exact models, indicators/features, input fields, labels, sampling frequency, forecast horizon, dates, train/validation/test split, tuning approach, metrics and costs.
- **P2 — Registry crosswalk:** map each extracted paper method to existing method IDs or document a proposed registry amendment before seeing new test results.
- **P3 — Data feasibility:** check current cached data and all viable free sources for required fields; log coverage and missingness without imputing away economically important gaps.
- **P4 — Reproduction design:** define a causal, leakage-safe replication protocol with strong baselines, walk-forward splits, uncertainty and multiplicity control.
- **P5 — Developer implementation:** implement only after the frozen protocol and data requirements pass their gate.
- **P6 — Independent tester:** verify formulas, signs, splits, look-ahead controls, arithmetic, schemas and exact source/test/workflow hashes before execution and again audit immutable results.
- **P7 — Status/result reporting:** classify each method as REPLICATED, TESTED-NEGATIVE, DATA-BLOCKED, REJECTED-AT-GATE or NOT-YET-REVIEWED; update the status, research log, README and final manuscript only with evidence-backed claims.

## Developer / tester handoff

**Developer → Tester:** Independently review this inventory for title/method omissions and verify the next full-text extraction and registry crosswalk. Treat every row as unreplicated until an exact method-to-result artifact and accepted tester report are provided.

**Tester → Developer:** Return corrections and missing-method findings on the isolated tester branch. Do not approve empirical execution solely from a title/abstract inventory or a broad family-name match.
