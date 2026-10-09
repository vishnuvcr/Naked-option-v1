# Review of Newly Uploaded Research PDFs — 2026-10-10

## Purpose and scope

This supplement reviews the 15 unique PDF papers attached to the research conversation on 2026-10-10. Re-uploaded copies of the same filenames were treated as duplicates rather than additional independent studies. The review records what each paper reports, then separates that report from the project's own evidence. A paper's headline accuracy, correlation, or simulated return is not accepted as a result for this repository until its data, timing, metrics, code and inference are independently reproduced.

This is an additive literature update only. It does not change the frozen method universe, current Phase 7 extension specification, test horizons, or gate sequence. The current empirical task remains prediction of NIFTY direction with available historical cross-market data; options-strategy research remains outside this continuation.

## Executive synthesis

1. **Price-level fit is not the same as directional skill.** Several papers use the word accuracy without making clear whether it means closeness of a normalized price forecast, correct direction, or a classification hit rate. Such numbers are not comparable across studies.
2. **Naive baselines and chronological evaluation matter.** The 2026 Cureus paper is especially relevant because it explicitly includes a naive persistence forecast and compares raw versus engineered features across 5-, 10- and 20-year windows. It reports stable linear-model performance over the longer windows, while tree ensembles that appear competitive on five years can underperform persistence over the longer windows.
3. **High scores may depend on very small test samples or in-sample evaluation.** For example, the 2022 multi-stock study uses a 99:1 split and reports only eight test days in the stated example. Mehtab and Sen distinguish an in-sample case from a later test period; the in-sample scores must not be described as out-of-sample evidence.
4. **External information is a hypothesis, not a guarantee.** Sentiment, FII/DII flows, USD/INR, India VIX, option PCR and cross-market features are worth testing because multiple papers use them. But publication timestamps, stale observations, survivorship, missing data, model-selection leakage and multiple testing need to be controlled.
5. **Price-level regression metrics cannot be compared across scales.** RMSE/MSE may be reported on normalized values, price levels, or returns. A very low normalized RMSE or high correlation does not, on its own, establish calibrated direction probabilities or an economically useful forecast.
6. **Published options returns are adjacent evidence only.** Three papers discuss option strategies, but this phase does not validate their trade rules or P&L. Any later use must go through a separate approved phase and exact contract-level costs, spreads, slippage, latency and option-premium effects.
7. **No PDF changes the current project result.** The existing accepted Phase 7 run's ten family-level predictive-improvement tests were all non-significant. The uploaded studies expand the future replication queue; they do not promote a model or strategy.

## Paper-by-paper review

### PDF-01 — “Stock Market Prediction with High Accuracy using Machine Learning Techniques”

- **Citation:** Malti Bansal, Apoorva Goyal and Apoorva Choudhary (2022), Procedia Computer Science 215, 247–265. DOI: https://doi.org/10.1016/j.procs.2022.12.028.
- **File:** 1-s2.0-S1877050922020993-main.pdf.
- **Question and methods reported:** Compares K-nearest neighbours, linear regression, support-vector regression, decision-tree regression and LSTM using daily history for 12 Indian companies from 2015 to April 2021.
- **Reported result:** The paper reports LSTM as strongest in its comparison, with average SMAPE 1.59, R² −0.11 and RMSE 22.55; SVR is next, with SMAPE 5.59, R² −1.69 and RMSE 46.36.
- **Critical qualification:** The stated 99:1 partition yields only eight test observations in the described example. The negative R² values are a caution that the reported low percentage error does not establish an adequate model relative to the sample mean. This is multi-stock evidence, not a direct NIFTY-index directional test.
- **Use in this project:** A replication lead for comparing simple regression and sequence models; require a larger untouched chronological test and a naive baseline. Do not transfer its headline ranking to NIFTY direction.

### PDF-02 — “A Robust Predictive Model for Stock Price Prediction Using Deep Learning and Natural Language Processing”

- **Citation:** Sidra Mehtab and Jaydip Sen, arXiv:1912.07700v1. Public record: https://arxiv.org/abs/1912.07700.
- **File:** 1912.07700v1.pdf.
- **Question and methods reported:** Uses NIFTY daily data, trains on 2015–2017 and tests from January 2018 to June 2019 at a one-week horizon. It compares eight classification methods and eight regression methods and adds Twitter sentiment classified into four mood classes, with a Self-Organizing Fuzzy Neural Network (SOFNN) sentiment-integrated model. Granger-causality tests are used for the sentiment hypothesis.
- **Reported result:** Several held-out regression models have materially different errors; the paper reports a test MAPE of 5.37 for its sentiment-integrated SOFNN in the relevant table, compared with much larger errors for some base regressors. The paper also reports “matched case” rates for its sentiment experiment.
- **Critical qualification:** Its Case I evaluates predictions on the training sample and must be kept separate from Case II's held-out test. Sentiment collection/classification, availability timing, and the exact mapping between sentiment dates and future weekly targets require independent verification. The reported metric is not evidence of post-cost option profitability.
- **Use in this project:** Supports retaining lagged public sentiment as a candidate feature family when there are genuinely timestamped historical texts; do not reproduce with today's headlines or undated sentiment.

### PDF-03 — “Developing A Machine Learning-Based Options Trading Strategy for the Indian Market”

- **Citation:** Firoz A. Sherasiya (2025), International Journal for Multidisciplinary Research 7(4). Publisher page: https://www.ijfmr.com/research-paper.php?id=50375.
- **File:** 50375.pdf.
- **Question and methods reported:** NIFTY 50 spot and option-chain history from 2020–2024; compares Random Forest, XGBoost and LSTM with options/spot features including Greeks and implied volatility. It discusses one-day holding and a strategy backtest.
- **Reported result:** The paper reports LSTM accuracy 90.10%, F1 0.90, Sharpe 1.95 and simulated return ₹205,720; XGBoost accuracy 89.20%, F1 0.89, Sharpe 1.78 and simulated return ₹196,450; Random Forest accuracy 87.40%, Sharpe 1.53 and return ₹182,300.
- **Critical qualification:** These are the paper's stated results, not independently verified results. The uploaded material alone is not enough to establish executable bid/ask-side entry and exit prices, realistic latency/slippage, full statutory charges, expiry/contract-roll handling or a multiple-testing-adjusted out-of-sample edge.
- **Use in this project:** Adjacent future strategy literature only. It does not authorize Phase 8 or override the current prediction-only scope.

### PDF-04 — “An Efficient Approach to Forecasting the NIFTY-50 Indian Stock Market's Daily Closing Price with Artificial Neural Networks”

- **Citation:** Kuljinder Singh Bumrah and Sandeep Kumar Budhani (2023), International Journal on Recent and Innovation Trends in Computing and Communication 11(11). Publisher: https://ijritcc.org/index.php/ijritcc/article/view/9472.
- **File:** 9472-Article Text-11108-2-10-20231228.pdf.
- **Question and methods reported:** Uses 1 April 2018–31 March 2023 daily data (the paper reports 1,183 observations), including NIFTY close, foreign institutional investor gross purchases and sales, and the dollar/rupee exchange rate. It compares SVM, RBF, MLP and SLP approaches using MATLAB neural-network tools.
- **Reported result:** The authors report MLP as the strongest of the tested methods and a strong association among NIFTY close, FII purchases/sales and USD/INR.
- **Critical qualification:** Correlation is not forecasting skill, and forecasting a rounded price is not the same as forecasting next-session direction. The paper's emphasis on association and neural-network fit requires a stricter chronological baseline comparison before the result can be reused.
- **Use in this project:** Supports testing lagged institutional-flow and currency features under strict publication-time alignment. FII/DII figures must be joined only after they became available.

### PDF-05 — “Open and Close Price Forecasting of the NIFTY 50 Stock Index Using Machine Learning: A Multi-Window Study of Feature Engineering and Model Tuning”

- **Citation:** Rohit K. Sain and Amresh K. Singh (published 1 October 2026), Cureus Journal of Computer Science 3. DOI: https://doi.org/10.7759/s44389-026-00306-5.
- **File:** CureusJournals_1986620261002-185337-d4go5h.pdf.
- **Question and methods reported:** Compares 12 supervised regressors with Naive Persistence for next-day open/close prediction, using 5-, 10- and 20-year NIFTY windows and two inputs: raw OHLCV versus OHLCV plus SMA, RSI, daily return and rolling volatility. The article describes chronological splitting and TimeSeriesSplit tuning for Random Forest and XGBoost.
- **Reported result:** The paper reports Linear Regression, Ridge and Lasso as more stable over 10- and 20-year windows and consistently better than naive persistence in its setting. Random Forest and XGBoost can be competitive on the 5-year window but generalize less well over 10 and 20 years, sometimes worse than the naive forecast.
- **Critical qualification:** The target is a next-day price level, not a direction probability or a calibrated return. Its result is still bounded by its dataset, target definition, and train/test design; this is not evidence that linear regression has tradable direction or option-premium edge.
- **Use in this project:** Highest-priority methodological comparator from the newly supplied set. Keep persistence as a hard benchmark, test raw and engineered inputs fairly, and add walk-forward stability plus uncertainty. Relevant material appears in the abstract and methodology/results sections (early and middle pages of the PDF).

### PDF-06 — “Options Trading Strategy: A Quantitative Study from an Investor’s POV”

- **Citation:** Atheetha S., Simran Mondal, Dhanusha N. and Raghunandan H. J. (2019), International Journal of Business and Management Invention 8(1), Version V, pp. 18–29. PDF: https://www.ijbmi.org/papers/Vol(8)1/Version-5/D0801051829.pdf.
- **File:** D0801051829.pdf.
- **Question and methods reported:** Discusses several instruments, including NIFTY, with an emphasis on simple averages, trend/seasonality and timing risk.
- **Reported result:** The paper provides a quantitative options-investor discussion and descriptive comparisons; it is not a direct, modern point-in-time ML direction benchmark.
- **Critical qualification:** Seasonality or average returns do not prove a reusable conditional signal. The source should not be treated as a replication-ready strategy without exact rules, date/contract mappings, costs and out-of-sample design.
- **Use in this project:** Contextual literature only; no method promoted.

### PDF-07 — “Options Trading Strategies for the Indian Market—An Effective Financial Derivative Tool”

- **Citation:** Partha Chatterjee et al. (2022), International Journal of Novel Research and Development 7(5), pp. 673–687. Publisher: https://www.ijnrd.org/viewpaperforall.php?paper=IJNRD2205074.
- **File:** IJNRD2205074.pdf.
- **Question and methods reported:** Overview of Indian options and common option-strategy categories.
- **Reported result:** Primarily descriptive and educational; it is not a controlled directional-prediction experiment.
- **Critical qualification:** It should not be counted as evidence of profitable prediction or as validation of any strategy.
- **Use in this project:** Background taxonomy only, explicitly outside the current empirical prediction task.

### PDF-08 — “Bridging Temporal Dependencies and Sentiment: A Comprehensive Approach to NIFTY 50 Index Prediction”

- **Citation:** Pranav P. Naik and Vadiraj G. Inamdar (2024), SSRG International Journal of Computer Science and Engineering 11(10), DOI: https://doi.org/10.14445/23488387/IJCSE-V11I10P106.
- **File:** IJCSE-V11I10P106.pdf.
- **Question and methods reported:** Integrates LSTM price history with BERT sentiment from NIFTY-related news, plus FII/DII, India VIX and PCR from the two nearest option expiries. It describes 80/20 validation and a broad 2000–2024 data range.
- **Reported result:** The authors claim that the combined model improves bullish/neutral/bearish trend prediction compared with historical-price-only models.
- **Critical qualification:** The available result presentation does not provide enough detailed, consistently comparable test metrics and robustness evidence to accept the claimed improvement here. The broad dataset date range and synchronization of all feature sources need verification. The printed LSTM state equations also warrant a formula-level implementation check before any reproduction.
- **Use in this project:** Candidate feature architecture—price sequence, sentiment, institutional flow, implied-volatility regime and option PCR—only after every input has point-in-time availability and source-specific coverage evidence.

### PDF-09 — “NIFTY-50 Stock Prediction Master”

- **Citation:** Dr. Harish B. G., ChetanKumar G. S., Raghavendrareddy Radder and Manoj K. (2023), International Journal of Scientific Development and Research 8(9), pp. 319–323. Publisher: https://ijsdr.org/viewpaperforall.php?paper=IJSDR2309053.
- **File:** IJSDR2309053.pdf.
- **Question and methods reported:** Describes an LSTM-based NIFTY prediction application, using approximately ten years of history (10 December 2011–10 December 2021) and showing an interface for 30-day forecasts and news.
- **Reported result:** The abstract claims 83.88% prediction accuracy.
- **Critical qualification:** The paper does not clearly establish the accuracy definition, a stringent chronological untouched test, or detailed metric reconciliation. The included screenshots demonstrate an application interface, not by themselves scientific predictive validity.
- **Use in this project:** Weak replication lead only; do not use 83.88% as directly comparable directional accuracy.

### PDF-10 — “Deep Learning Approaches for Stock Price Prediction: A Comparative Study on Nifty 50 Dataset”

- **Citation:** Sushma P. Kallimath, Narayana Darapaneni and Anwesh Reddy Paduri (published 28 February 2025), EAI Endorsed Transactions on Intelligent Systems and Machine Learning Applications. DOI: https://doi.org/10.4108/eetismla.7481.
- **File:** ISMLA+7481.pdf.
- **Question and methods reported:** Compares linear regression, LSTM, GRU, CNN, RNN, TCN and hybrids LSTM+GRU, CNN+RNN, CNN+TCN and LSTM+TCN. It reports MSE, R², RMSE, MAE and MAPE; its diagram describes about a 90/10 split (2,350 training and 235 test points).
- **Reported result:** The authors state that nonlinear deep-learning and hybrid architectures can outperform the linear baseline in their experiments.
- **Critical qualification:** The supplied paper's reported comparisons do not by themselves demonstrate incremental directional skill, statistical significance, calibration, or economic value; the split chronology and exact numerical results require code/data audit. Multi-model comparisons increase selection risk.
- **Use in this project:** Broad candidate family inventory, but prioritize simpler benchmarks and pre-registered, chronological family tests over an uncorrected architecture bake-off.

### PDF-11 — “A Study of the Impact of Moving Averages on Predicting Stock Market Trends: A Study of NIFTY 50”

- **Citation:** Dr. Deepesh Y. Mahajan, Dr. Nitin Tanted, Dr. Siddharth Rewadikar and Jasdeep Singh Chhabra (published 17 July 2025), Journal of Informatics Education and Research 5(3). Publisher: https://jier.org/index.php/journal/article/view/3254.
- **File:** JIER-+Vol.+5+No.+3+(2025)+-+Dr.+Deepesh.Formated.pdf.
- **Question and methods reported:** Examines SMA/EMA indicators and crossover rules on NIFTY daily data from 2010–2023, comparing with passive buy-and-hold and using a paired t-test.
- **Reported result:** The paper reports crossover t = −1.271 and p = 0.1079, which does not meet the conventional 0.05 significance threshold.
- **Critical qualification:** A high correlation between a moving average and the index level is expected because the moving average is computed from that price series; it is not evidence of incremental forecast power. The reported non-significant test should not be rephrased as proof that the rules work.
- **Use in this project:** Supports explicitly testing moving-average rules against baseline and using statistical tests; the paper's own reported crossover test is not statistically significant at 5%.

### PDF-12 — “Stock Market Prediction of NIFTY 50 Index Applying Machine Learning Techniques”

- **Citation:** Zahra Fathali, Zahra Kodia and Lamjed Ben Said (2022), Applied Artificial Intelligence 36(1), article e2111134. DOI: https://doi.org/10.1080/08839514.2022.2111134.
- **File:** Stock Market Prediction of NIFTY 50 Index Applying Machine Learning Techniques.pdf.
- **Question and methods reported:** Compares RNN, LSTM and CNN for NIFTY time-series prediction and studies feature selection and hyperparameter/epoch choices, with model performance primarily quantified by MSE/RMSE-type regression errors.
- **Reported result:** The abstract reports lower errors for LSTM than RNN and CNN in the authors’ setting; reported errors vary with features and epochs.
- **Critical qualification:** Lower price-level error is not a directional-skill metric. Performance comparisons depend on the precise input features, scaling, horizon and test dates. Any time-series split and preprocessing parameters must be independently recreated without future information.
- **Use in this project:** Candidate for an architecture-baseline comparison, not a result that LSTM is universally superior.

### PDF-13 — “Stock Market Index Forecasting of Nifty 50 Using Machine Learning Techniques with ANN Approach”

- **Citation:** Gourav Kumar and Vinod Sharma (2016), International Journal of Modern Computer Science 4(3), pp. 22–27.
- **File:** Stock_Market_Index_Forecasting_of_Nifty.pdf.
- **Question and methods reported:** Uses 3 April 2006–16 May 2016 data (3,335 observations) on open, high, low, close, volume and turnover; a feed-forward MLP with a 6-10-4 topology and multiple back-propagation algorithms. The paper describes min-max scaling to −1 to 1 and a 70/30 train/test split.
- **Reported result:** The abstract calls its average result “99.2152% accuracy” and reports normalized RMSE 0.0079; the results section lists test RMSE values of about 0.01069 for the main network and 0.00552 for a second network.
- **Critical qualification:** Here “accuracy” appears to describe closeness of normalized OHLC output, not a classifier hit rate for up/down moves. The exact chronological ordering of the 70/30 split and comparison with persistence are not sufficiently clear in the extracted text.
- **Use in this project:** Historical ANN replication target only. Do not map the 99.2152% number to directional accuracy.

### PDF-14 — “Forecasting of NIFTY 50 Index Price by Using Backward Elimination with an LSTM Model”

- **Citation:** Syed Hasan Jafar, Shakeb Akhtar, Hani El-Chaarani, Parvez Alam Khan and Ruaa Binsaddig (2023), Journal of Risk and Financial Management 16(10), article 423. DOI: https://doi.org/10.3390/jrfm16100423.
- **File:** jrfm-16-00423.pdf.
- **Question and methods reported:** Uses 15 years of daily Bloomberg data with date, OHLC, volume and 14-period RSI to forecast NIFTY close; compares LSTM with backward-elimination LSTM over a stated 30-day forecast.
- **Reported result:** The abstract reports that backward-elimination LSTM is better than the base LSTM and gives “95% accuracy.”
- **Critical qualification:** The abstract does not define “accuracy” sufficiently to compare with a directional hit rate. Feature-selection and model fitting must be isolated inside training folds; price-level persistence needs to be benchmarked, and multistep forecast uncertainty should be reported.
- **Use in this project:** Candidate feature-selection method only with nested chronological selection and direct baseline comparisons.

### PDF-15 — “An Empirical Study on Options Trading Strategy Using ‘Commodity Channel Index’ for NSE’s Nifty Options in India”

- **Citation:** Pinkal Kishorbhai Shah (2019), SSRN working paper, DOI: https://doi.org/10.2139/ssrn.3323746. Record: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3323746.
- **File:** ssrn-3323746.pdf.
- **Question and methods reported:** Describes a Commodity Channel Index rule on NIFTY spot to trigger long in-the-money options, with an approximately two-week horizon and performance measures such as return, gain/loss ratio and strike rate.
- **Reported result:** The work reports strategy metrics from its own historical test.
- **Critical qualification:** This is an options-rule paper, not a validated direction-model benchmark. Its results require independent reconstruction of signal timestamps, option contract choice, entry/exit sides, data coverage, premium decay and all transaction costs.
- **Use in this project:** Adjacent strategy literature only. It does not authorize any option test during the current prediction extension.

## Cross-paper implications for the registered research

### Features worth testing only when point-in-time availability is proven

- Lagged NIFTY OHLCV and causal technical indicators (SMA/EMA, RSI, returns and rolling volatility).
- Global markets and currency/commodity references (S&P 500/Nasdaq/Nikkei/Hang Seng proxies, USD/INR, gold and crude oil).
- Institutional activity (FII/DII), India VIX and option-PCR features if historical coverage and release timestamps permit.
- Dated news/social-media sentiment and BERT-style embeddings only where original text timestamps and vintage are available; current sentiment cannot be backfilled into past decisions.
- Alternative model families (linear/ridge/lasso, SVR, random forest/boosting, RNN/LSTM/GRU/CNN/TCN/hybrids) as pre-registered challengers, not an unlimited search for a best score.

### Mandatory controls reinforced by the uploaded set

1. Publish the exact target: price level, return, binary up/down, multi-class state, or volatility. Never mix their metrics.
2. Include persistence and training-rate baselines; compare candidates on the same eligible holdout rows where possible.
3. Use chronological evaluation and walk-forward refitting; fit scaling and feature selection on training data only.
4. Provide test sample counts, dates, formula definitions and confusion counts alongside all metrics.
5. Control multiple comparisons across methods and horizons; report uncertainty rather than only the winning cell.
6. Treat missing source coverage as a method-specific BLOCKED_DATA result, not a reason to fabricate values or to discard difficult periods silently.
7. Keep paper-reported outputs distinct from project-reproduced outputs. No source in this supplement is an accepted empirical result for this repository.
8. For any later strategy phase, audit exact option contracts and availability, and calculate gross and net results with spread, slippage, latency, brokerage, exchange/statutory charges and premium decay. This requirement is recorded here as future governance, not a trigger to begin that phase.

## Review limitations

This is a structured review of the 15 attached unique PDFs with targeted publisher/record checks where a source URL is available. It is not claimed to be a systematic review of every paper ever published, and subscription indexes such as Scopus/Web of Science were not available through the current toolset. Some PDFs provide incomplete source data, code, exact split details or fully reproducible tables; those gaps are recorded as limitations rather than filled by inference. The available-data empirical run is still blocked pending independent tester review.

## Repository disposition

- New literature records: L037–L051 in the machine-readable registry.
- This supplement is linked from the canonical literature review and main README.
- The finite method universe and pre-registered available-data specification are unchanged.
- Developer → Tester: independently validate the bibliography, the match between each paper's reported claim and its critique, the registry's 11-column CSV schema, the page/table-derived values noted above, and confirm no empirical/strategy phase has been opened by this supplement.
- Tester → Developer: report factual, citation, CSV, or governance errors for correction; do not treat these papers as project results or authorize the available-data run from the literature-only update.
