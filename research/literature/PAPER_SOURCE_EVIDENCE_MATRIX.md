# Paper Source-Evidence Matrix — Uploaded Prediction Papers

**Date:** 2026-10-10  
**Branch:** `phase-07-developer`  
**Status:** source locators added; PPR-1 remains PROPOSED / tester re-review required. No model fitting or new data access is authorized by this document.

## Reading convention

“PDF p.N” means the Nth physical page in the uploaded PDF viewer, not necessarily the printed journal page. Each paper is split into claim categories so the sources of method, sample, target/horizon, split, metric/result, and limitations are independently traceable. Author-reported figures remain literature claims, not project results. A source claim can be tagged:
- `AUTHOR-IMPLEMENTED`: methods/results show that the authors evaluated the method.
- `BACKGROUND-ONLY`: only discussed or cited, not shown as an evaluated method.
- `AMBIGUOUS`: the source does not permit a defensible, reproducible specification.
- `PROJECT-ADAPTATION`: a new project task/configuration, not an exact replication.

## Paper 1 — Bansal, Goyal & Choudhary (2022), `1-s2.0-S1877050922020993-main.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods | PDF pp. 9–13 | Methods describe five price regressors: KNN, linear regression, SVR, decision-tree regression and LSTM. | `AUTHOR-IMPLEMENTED` as a source task; exact hyperparameters/architecture are not all frozen in the paper text. |
| Data | PDF pp. 10–11 | Describes daily stock data from Jan 2015 through Apr 2021 for 12 companies from Quandl/BSE. | This is not a NIFTY-index-only training set. Abstract/date wording conflicts and should be preserved as ambiguity rather than silently reconciled. |
| Target/horizon | PDF pp. 9–13 | Stock price prediction/regression is described; the common forecast endpoint/label for project adaptation is not a paper-native NIFTY-direction label. | Record exact source target column/shift before reproduction. NIFTY-only and derived-direction versions are `PROJECT-ADAPTATION`. |
| Split | PDF pp. 12–13 | 99:1 train/test ratio is specified; text also describes random sampling through the splitting library. | Paper-faithful random split is leakage-risk evidence only; causal chronological split is a distinct adaptation. |
| Metrics/results | PDF pp. 12–17 | SMAPE, RMSE and R² are used; results/tables compare the five methods and report LSTM as strong on the studied stock panel. | Figures are author-reported. They cannot be represented as project results or directional accuracy. |
| Limitations | PDF pp. 10–13 | Multi-company data, sample-date ambiguity and randomized split wording constrain exact causal reconstruction. | Exact reproduction and causal NIFTY adaptation require separate ledger entries. |

## Paper 2 — Mehtab & Sen, `1912.07700v1.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods | PDF pp. 3–5 | Classification methods include Logistic Regression, KNN, Decision Tree, Bagging, Boosting, Random Forest, ANN and SVM. Regression/SOFNN/LSTM and sentiment-augmentation results are presented in the methods/results pages. | Only methods with reported evaluation tables count as `AUTHOR-IMPLEMENTED`; related-work names remain `BACKGROUND-ONLY`. |
| Data | PDF pp. 2–3 | NIFTY 50 daily data; Jan 2, 2015–Dec 29, 2017 (737 observations) described as training and Jan 2, 2018–Jun 28, 2019 as test. | Paper-native dates must not be substituted with 2020+ project data and still called exact replication. |
| Target/horizon | PDF pp. 2–3, 5 | Text specifies a one-week forecast horizon; regression predicts normalized closing-price values and classification uses positive/negative normalized movement. | Weekly price forecast and next-day binary classification are different target rows; exact label shift and endpoint need separate config entries. |
| Split | PDF pp. 3–5 | Case I reports training-set performance and Case II reports test-set performance. | Do not pool training results with out-of-sample test results. |
| Metrics/results | PDF pp. 3–5 | Classification reports sensitivity, specificity, PPV, NPV and classification accuracy; regression reports MAPE/correlation and LSTM/SOFNN outputs; Granger tests appear in p.5. | Paper-reported figures only; “accuracy” and regression scores belong to separate target types. |
| Limitations | PDF pp. 2–5 | Multiple target constructions coexist and model tuning details vary by case. | Preserve native task distinctions; the common direction task is an adaptation. |

## Paper 3 — Sherasiya (2025), `50375.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods/features | PDF pp. 2, 5–6 | The paper identifies Random Forest, XGBoost and LSTM as its evaluated models and uses option-chain features, changes in OI/volume, implied volatility, option Greeks and price-action inputs. | `AUTHOR-IMPLEMENTED` for the source option-signal task. Models cited only in background pages are not added to the implemented list. |
| Data | PDF pp. 2, 5 | High-resolution option-chain data for Nifty/Bank Nifty instruments are described. | Exact vendor archive, point-in-time coverage and raw sample rows are not specified enough for literal reconstruction. |
| Target/horizon | PDF p. 5 | Buy/Sell labels are defined; Buy corresponds to a next-day price increase above 1%. Predicted signal is used to select an ATM call or put with a one-trading-day holding period. | This is an option trading-signal/strategy task, not a pure spot-index directional forecast. |
| Split | PDF p. 5 | 80:20 train/test ratio, cross-validation and XGBoost grid search are described. | Random/chronological ordering and fold details need source confirmation before exact replication. |
| Metrics/results | PDF pp. 5–6 | Accuracy, precision, recall, F1, confusion matrix/ROC-AUC and strategy measures are discussed; p.6 gives model comparison and source-reported trading outcomes. | Keep strategy metrics out of prediction-only project results. |
| Limitations | PDF pp. 5–6 | Reported metrics rely on option strategy assumptions and are not evidence of NIFTY spot-direction edge. | `STRATEGY_ONLY / OPTION_SIGNAL` for this phase; revisit only under a separate approved option gate. |

## Paper 4 — ANN/SVM with FII and FX, `9472-Article Text-11108-2-10-20231228.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods/features | PDF pp. 4–6 | Daily NIFTY close is described as the dependent variable; ANN variants include SLP/MLP/RBF and an SVM comparison. FII gross purchases/sales and USD/INR are included as explanatory variables. | Each architecture's evaluated/mentioned status and its exact input list must remain separate. |
| Data | PDF pp. 4–5 | Data source/sample details and the stated observation span appear in the methodology pages. | The claimed 2018–2023 window and 1,183 observation count must remain linked to the exact passage; if the source's own date/count descriptions conflict, mark `AMBIGUOUS`. |
| Target/horizon | PDF pp. 4–6 | NIFTY daily closing price forecasting. | Exact next-session target shift must be located in the method/results text; do not infer a direction label. |
| Split | PDF pp. 5–6 | Method pages discuss percentage train/test allocation, including competing 65:35 / 70:30 wording in the crosswalk extraction. | Record which split belongs to which model/config; do not reduce conflicting descriptions to one setting. |
| Metrics/results | PDF pp. 6–7 | Results and comparisons are shown. | Attach metric names and model-specific result table references; source claims remain unvalidated in this project. |
| Limitations | PDF pp. 4–7 | Split and setup descriptions are not yet fully normalized into per-model entries. | PPR-1 must preserve unresolved settings instead of guessing. |

## Paper 5 — Sain & Singh (2026), `CureusJournals_1986620261002-185337-d4go5h.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods | PDF pp. 6, 9–10 | Twelve regressors: Linear Regression, Lasso, Ridge, Elastic Net, SGD Regressor, SVR, KNN, Decision Tree, Random Forest, Gradient Boosting, AdaBoost and XGBoost; Naïve Persistence baseline. | `AUTHOR-IMPLEMENTED` as described in the experiment. |
| Data/features | PDF pp. 7–10 | Daily OHLCV data; engineered pipeline adds SMA(10/20), daily return, rolling volatility(20) and RSI(14). The 20-year window is described as Jun 1, 2006–Jun 1, 2026. | Keep 5-, 10- and 20-year data-window statuses distinct from the project’s currently audited 2020+ sample. |
| Target/horizon | PDF pp. 6–8 | Next-day open and close price regression. | Open and close are different targets; an open forecast is not automatically a close-direction prediction. |
| Split/tuning | PDF pp. 8–10 | Chronological 80:20 split; Random Forest/XGBoost tuning uses TimeSeriesSplit. | Reproduction needs exact split boundary and final training/test windows recorded. |
| Metrics/results | PDF pp. 10–18 | MAE, RMSE and R² reported; tables compare raw and engineered features across the historical windows. | Price-level R²/very high in-sample fit is not proof of direction prediction. Copy values only as author-reported and cite the exact table. |
| Limitations | PDF pp. 11–18 | Performance differs by target/window; some engineered-feature and long-window test results are poor. | Preserve negative test results rather than selecting only high scores. |

## Paper 6 — Atheetha et al. (2019), `D0801051829.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods | PDF pp. 3–4, 10 | Descriptive averages/monthly seasonality are discussed; the conclusion centres on a simple-average options strategy. | No sufficiently specified fitted NIFTY-direction estimator was established from the inspected methods/conclusion pages. |
| Data/target/split/metrics | PDF pp. 3–10 | Source discusses investor/options profitability, average return and period/seasonality calculations. | These are not enough to assert a standalone forecast model with fixed target, split and OOS metrics. |
| Disposition | PDF pp. 3–10 | Strategy/descriptive study. | `STRATEGY_ONLY / DESCRIPTIVE` unless an exact implemented prediction task is traced to a specific methods/results passage. |

## Paper 7 — Naik & Inamdar (2024), `IJCSE-V11I10P106.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods/features | PDF pp. 3–4 | LSTM plus BERT-derived sentiment from news; FII/DII, India VIX and PCR from the two nearest expiries are used as combined/corrective inputs. | The combined model and ablations should be distinct configurations; generic LSTM runs do not reproduce the fusion. |
| Data | PDF pp. 3, 5 | The text describes 2000–2024 price/PCR coverage, while news collection is described from the COVID period to the paper's present. | These date ranges and source-vintage alignment are not a single automatically coherent panel; record each source separately. |
| Target/horizon | PDF pp. 3–6 | NIFTY price/trend prediction and sentiment labels are described; PCR examples show bullish/bearish/neutral labels. | Precise NIFTY forecast label, endpoint and metric mapping need exact config locators. |
| Split | PDF pp. 4–5 | An 80:20 split is stated for the LSTM/data workflow. BERT evaluation is described separately. | Do not assume the BERT text split and price sequence split are aligned by date. |
| Metrics/results | PDF p. 5 | The source claims 98% LSTM accuracy/99% precision and 99% BERT accuracy/precision. | Mark as author-reported and not comparable until metric formula, test labels, sample size and temporal split are substantiated. |
| Limitations | PDF pp. 3–7 | Publication/ingestion timestamps, revised news and PIT availability are not fully specified in the source. | No same-day news/flow/option feature is admitted to a causal project dataset without a separate data-vintage gate. |

## Paper 8 — Chatterjee (2022), `IJNRD2205074.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Method/scope | PDF pp. 2–3, 14–15 | Methods explicitly say the study is based on secondary sources; body explains option terms and strategy classes. | `BACKGROUND-ONLY / NOT A FORECAST METHOD`; no estimator is described as fitted/evaluated. |
| Target/split/metrics | PDF pp. 2–15 | No standalone forecast target, train/test split or model evaluation is identified. | Do not manufacture a model from its strategy descriptions. |

## Paper 9 — `IJSDR2309053.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Method | PDF pp. 1–4 | LSTM is named in the stock prediction/app discussion; pages include an application UI and next-30-days prediction display. | LSTM implementation details sufficient for a faithful recreation are not all provided; tag `AMBIGUOUS` where architecture/training inputs are absent. |
| Data | PDF p. 1 | Claims data span Dec 10, 2011–Dec 10, 2021. | This is a paper claim; raw source, number of eligible rows and availability convention are not established here. |
| Target/horizon | PDF pp. 1, 4 | Abstract reports an 83.88% accuracy claim; UI shows a next-30-days price forecast. | 30 days vs 30 trading sessions and the actual scored endpoint require clarification. |
| Split | PDF pp. 1–5 | Training/testing is mentioned but a fully reproducible chronological split is not established in the inspected text. | Do not guess the split. |
| Metrics/results | PDF p. 1 | “83.88% accuracy” appears in the abstract without a sufficiently explicit formula/label definition in the examined pages. | `AMBIGUOUS`; never compare as a directional hit rate without definition. |
| Limitations | PDF pp. 1–5 | The paper mixes app/UI material with a brief method description. AR/ARMA/ARIMA appear as general time-series context rather than clear fitted comparators. | Keep these as background and do not claim replication. |

## Paper 10 — Kallimath et al. (2025), `ISMLA+7481.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods | PDF pp. 6–12 | Text describes Linear Regression, LSTM, GRU, CNN, RNN and TCN, plus LSTM+GRU, CNN+RNN, CNN+TCN and LSTM+TCN comparisons. Results include optimizer comparisons. | Use exact architecture/config rows only when evaluated by authors; generic architecture description alone is not implementation evidence. |
| Data/schema | PDF p. 10 | Dataset is said to come from Kaggle and to contain fields such as strike price and callOpen/callHigh/callLow/callClose. | **Target/schema ambiguity:** these are option-contract-like fields. The crosswalk must not label this an ordinary spot NIFTY OHLCV experiment unless it identifies the target column and dataset schema. |
| Target/horizon | PDF pp. 10–11 | Stock-price prediction is discussed but the exact dependent variable and its relationship to the call-option fields is not unambiguously defined in the inspected passage. | `AMBIGUOUS` until target column and forecast shift are found. |
| Split | PDF p. 11 | Text gives 2,350 training and 235 test observations and 50 iterations. | Split order and meaning of “50 iterations” need to be documented; do not infer random or chronological order. |
| Metrics/results | PDF pp. 10–12 | R², RMSE, MAE and other regression metrics/optimizer comparisons are described. | Keep author-reported results distinct from NIFTY spot-direction results. |
| Limitations | PDF pp. 10–12 | Input schema, target definition and chronology are insufficiently specified for exact replication from the available text. | Block exact reproduction until resolved; a recreated spot-index task is an adaptation only. |

## Paper 11 — Mahajan et al. (2025), `JIER-+Vol.+5+No.+3+(2025)+-+Dr.+Deepesh.Formated.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods | PDF pp. 5–8, 12–13 | Moving-average analysis includes EMA-based Golden/Death Cross descriptions; the text compares 50/200 EMA and reports simple regression/correlation claims. | Exact crossover configuration must be named; passages also refer to EMA 50/100. |
| Data | PDF pp. 5–8 | Coverage is variously described as 2010–2023, 2010–2024 and trend descriptions through 2025. | Date-span inconsistency is source ambiguity, not an invitation to choose silently. |
| Target/horizon | PDF pp. 5–8 | Market trend/crossover signals and regression of price on moving averages are described. | A contemporaneous price-level regression is not a forecast target; crossover-at-time-t / forecast-at-t+1 timing must be explicit for an adaptation. |
| Split | PDF pp. 5–13 | No clear isolated untouched chronological OOS split is established in the inspected analysis. | Treat the historical analysis as descriptive/in-sample unless a split is directly located. |
| Metrics/results | PDF pp. 6–7, 12–13 | p.6 reports crossover comparison t=-1.271, p=.1079, which is not significant at .05; elsewhere very high price/EMA correlations and R² are described as predictive evidence. | Preserve the non-significant crossover result and distinguish it from highly autocorrelated level regressions; do not call the crossover OOS-validated. |
| Limitations | PDF pp. 5–13 | Period/window inconsistencies and mixed inference language constrain faithful reproduction. | Freeze a declared 50/200 EMA adaptation only after tester approval. |

## Paper 12 — Fathali, Kodia & Ben Said (2022), `Stock Market Prediction of NIFTY 50 Index Applying Machine Learning Techniques.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods/architecture | PDF pp. 11–14 | The proposed evaluated families are RNN, LSTM and CNN; the paper varies input-feature sets/epochs and describes layer/feature-selection steps. | Architecture specifics must be captured from the method text and separate base methods from mentioned related work. |
| Data/features | PDF pp. 12–14 | Text describes daily NIFTY OHLCV features and scaling/missing-value/preprocessing steps. | Need exact source date span and order of any feature-selection/normalization relative to train split. |
| Target/horizon | PDF pp. 11–18 | The paper forecasts index prices and reports train/test regression tables. | Derived direction is a separate project adaptation; do not treat undefined “accuracy” as a common metric. |
| Split | PDF pp. 11–14 | A train/test split and K-fold training procedure are discussed. | Fold construction must be verified for chronology; ordinary K-fold over time is not assumed causal. |
| Metrics/results | PDF pp. 15–18, 22–25 | MSE, RMSE, MAE, R² and an “accuracy” term are reported, with feature-set/epoch tables. | The formula/meaning of “accuracy” must be traced before comparison; only price metrics can be compared directly to a price baseline. |
| Limitations | PDF pp. 11–18 | Activation/feature/epoch selection may leak if selected using test data; CV timing matters. | Leakage-safe project adaptation must refit preprocessing and selection inside chronological training folds. |

## Paper 13 — Kumar & Sharma (2016), `Stock_Market_Index_Forecasting_of_Nifty.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods/features | PDF p. 3 | Feed-forward multilayer perceptron with one input layer, one hidden layer and one output layer; inputs include open/high/low/close/volume/turnover; Min-Max normalization. | Optimizer/training software is described; don't expand the model into unmentioned architecture variants. |
| Data | PDF p. 3 | Daily NSE NIFTY data from 3-Apr-2006 to 16-May-2016, 3,335 instances. | Paper-native data window is longer than the current project sample. |
| Target/horizon | PDF pp. 3–5 | Forecasts OHLC price fields. | Exact forecast shift must be verified before scoring a next-session task. |
| Split | PDF p. 3 | 70% training and 30% testing. | The page does not clearly establish the chronological order; record `split_order=AMBIGUOUS` unless another exact locator does. |
| Metrics/results | PDF pp. 4–5 | Reports normalized train/test RMSE, including main-network values 0.0078485851 and 0.0106902067. | The inspected results support those RMSE values. The crosswalk's 99.2152% “accuracy” is **unverified** in these source sections; locate the exact page and formula or remove it from source-verified claims. |
| Limitations | PDF pp. 3–5 | Results use normalized-space RMSE and graphical comparison; chronology/horizon/accuracy formula remain insufficiently located. | Do not compare reported normalized errors to raw-price RMSE without inverse-scaling. |

## Paper 14 — JRFM (2023), `jrfm-16-00423.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Methods | PDF pp. 9–13, 15–18 | Proposed method is backward-elimination LSTM (BE-LSTM) compared with LSTM; BE steps use regression significance/p-values. | Preserve the BE selection procedure as its own method, not just a generic LSTM. |
| Data/features | PDF p. 15 | Yahoo Finance data from 20-Jan-2005 to 5-Mar-2021, 3,986 rows and eight listed attributes (date, OHLC, volume, value, trades, RSI average). | Paper-native window and attributes differ from other source panels. |
| Target/horizon | PDF pp. 15, 20 | Closing-price prediction, including a next-30-days display/result. | Clarify 30 trading sessions versus calendar days in the target manifest; don't merge with next-session predictions. |
| Split/selection | PDF pp. 15–17 | Backward elimination regression tables are fitted/reported using the full 3,986-row dataset before selected features are fed into LSTM. | **Leakage risk:** source-faithful full-sample feature selection is not a causal forecast evaluation. The safe adaptation must refit selection inside training data only. |
| Metrics/results | PDF pp. 14, 18–20 | MSE, RMSE, MAPE and reported accuracy/precision/recall are given; Table 10 compares LSTM and BE-LSTM; p.20 shows next-30-days comparison. | The accuracy/precision/recall target definition is not the same as price RMSE; retain each metric's source claim and formula separately. |
| Limitations | PDF pp. 15–20 | Full-sample selection and very high in-sample regression fit can inflate apparent skill. | Exact reproduction and leakage-safe adaptation must be separate manifest rows. |

## Paper 15 — CCI option strategy, `ssrn-3323746.pdf`

| Claim category | Source locator | Source-grounded finding | Fidelity / unresolved issue |
|---|---|---|---|
| Method/scope | PDF pp. 6–8 | A descriptive CCI-based system for long NIFTY call/put options; data from 1-Oct-2008 to 30-Sep-2018. | `STRATEGY_ONLY`; it is not a fitted spot-direction prediction paper. |
| Costs | PDF p. 8 | Assumptions include lot size 50, brokerage/taxes Rs 100, and slippage cost of 10%. | These are the paper's historical assumptions, not the current Paytm Money schedule. Any future strategy work needs current cost verification and its own gate. |
| Sample/metrics | PDF pp. 8–11 | Reports 68 trades, 63.25% strike rate and several significance tests. | Author-reported results are not validated here. |
| Arithmetic issue | PDF pp. 9–10 | The source gives 43 profitable and 25 losing trades (68 total) in its chi-square discussion, but another table cell prints a total of 80. | Record the internal count mismatch in the error log; don't treat the inconsistent table as a trusted inferential result. |
| Disposition | PDF pp. 6–11 | Long-option trade rules, returns, strike rate and slippage/brokerage assumptions are central. | No CCI option P&L or CCI signal test is authorized in this prediction-only proposal. A spot-direction CCI proxy would be a separately reviewed `PROJECT-ADAPTATION`. |

## Source-audit stop rules

- If any model, target, split, horizon or metric has no source locator, mark the field `AMBIGUOUS`/unverified; do not fill it from memory or a secondary article.
- If a source describes a model but does not show its evaluation, tag it `BACKGROUND-ONLY`.
- A paper-native random split or full-sample feature selection must be recorded as its own fidelity line and must not enter the leakage-safe confirmatory metric.
- Author-reported performance is not a project result. No row becomes `TESTED` without an immutable project artifact and an allowed independent gate.
- This matrix does not provide full-text coverage for the repository's separate 36-record literature inventory; that work is PPR-2 and remains unauthorized until PPR-1 passes.

**Developer → Tester:** Review this matrix against the exact PDFs and the updated protocol before authorizing PPR-2.  
**Tester → Developer:** Keep empirical work blocked until all flagged target/window/metric ambiguities are recorded in a frozen manifest or explicitly excluded.
