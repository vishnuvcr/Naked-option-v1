# Phase 1 Literature Search Protocol

## Search date

2026-10-07 (IST).

## Accessible research surfaces used

1. Project Library / Project-attached prior research artifacts, searched with the Files tool.
2. Public web search, including official NSE, SEBI, RBI/official documentation and scholarly/preprint sources.
3. Public GitHub repositories and source-code search through the GitHub connector.
4. Literature URLs discovered through search results and then recorded as stable source links.

Direct subscription databases such as Scopus/Web of Science were not available through the current toolset, so they are not claimed as searched. Their absence is recorded as a limitation.

## Search themes and representative exact queries

### Market direction / NIFTY
- `predict NIFTY direction methods option buying backtest results`
- `direction signal NIFTY option buying research methods`
- `NIFTY 50 direction XGBoost 2026 prediction`
- `NIFTY 50 news sentiment direction prediction`
- `NIFTY 50 market direction machine learning`

### Options / order flow / volatility
- `NIFTY 50 option open interest intraday structure breaks 2026`
- `index option order imbalance predicts index returns`
- `option return predictability machine learning moneyness maturity`
- `retail option traders implied volatility surface 2026`
- `India VIX NIFTY high frequency return implied volatility`

### Methodology / data snooping
- `White reality check data snooping trading strategy`
- `probability of backtest overfitting`
- `deflated Sharpe ratio multiple testing`
- `technical trading rules transaction costs data snooping`
- `Diebold Mariano predictive accuracy`
- `stepwise SPA trading strategies`

### Indian primary sources
- `NSE historical contract wise F&O price volume open interest option fields official`
- `NSE FII FPI DII trading activity official`
- `NSE India VIX methodology official`
- `SEBI FY25 FY26 study profitability individual traders equity derivatives August 2026`
- `Paytm Money F&O brokerage ₹10 per order official`

## Inclusion criteria

A source was included when at least one of the following applied:

- primary source for NIFTY/NSE/SEBI/RBI/broker rules;
- peer-reviewed methodological or empirical study relevant to prediction, options, market efficiency, volatility, microstructure, sentiment or execution;
- transparent preprint/working paper with methods and data sufficient for replication;
- public open-source implementation directly relevant to a registered method.

## Exclusion criteria

- anonymous claims with no method/data;
- marketing material presented as empirical proof;
- sources whose principal claim could not be reproduced or independently checked;
- duplicated versions of the same study unless the version itself adds important methodological evidence.

## Screening

Each candidate receives:
- source ID;
- title/year;
- source class;
- URL/DOI;
- evidence class;
- related registry family/hypothesis;
- verification status;
- replication requirement.

## Evidence classes

- PRIMARY: official first-party source.
- METHODOLOGY: established statistical/econometric method.
- EMPIRICAL: empirical research with transparent methods.
- REPLICATION_TARGET: recent or weaker empirical claim that this project will independently test.
- OPEN_SOURCE: code/repository useful as a replication target, not evidence by itself.

## Search limitations

This phase does not claim that every paper ever published has been retrieved. The finite objective is to cover the registered method families, key methodology literature, India/NIFTY-specific evidence, current regulatory/data sources and credible replication targets. Missing sources discovered later may be appended only as a documented protocol revision before their associated final tests.


## Addendum — supplied PDF corpus reviewed (2026-10-10)

Fifteen unique user-supplied PDFs were screened and reviewed across abstracts, methods and available results/tables, with publisher/DOI records checked where identified. Re-uploaded duplicates were counted once. The paper-by-paper appraisal is in [UPLOADED_PDF_REVIEW_2026-10-10.md](UPLOADED_PDF_REVIEW_2026-10-10.md), with records L037–L051 in the literature registry.

This is a supplementary corpus, not proof that all literature has been covered and not a change to the pre-registered method universe. Some papers do not provide enough data/code, precise split details or comparable metric definitions for exact reproduction; these are explicitly treated as limitations. Copyrighted PDF binaries are not being copied into the public repository; the repository retains bibliographic metadata, stable public source links, critical appraisal and reproducibility requirements instead.
