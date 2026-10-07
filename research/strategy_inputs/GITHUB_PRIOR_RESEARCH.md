# Prior GitHub Research Repository Intake

## Relevant public repositories discovered

The GitHub account exposes 19 public repositories. The following repositories contain trading research/data/strategy material relevant to this NIFTY direction project and have been registered for prior-art mining.

| Repository | Relevant material | How it will be used |
|---|---|---|
| [Iron_condor](https://github.com/vishnuvcr/Iron_condor) | NIFTY weekly iron-condor signal pipeline; Tuesday signal → next-session delayed paper entry; lot-size history; cost model; parameter grid | Mine timing, DTE selection, cost/slippage modeling and robust parameter selection; original multi-leg structure is excluded from final naked-long execution |
| [Paper-Trade-v1](https://github.com/vishnuvcr/Paper-Trade-v1) | NoDip 3W/1W far-expiry variants and MC-RQ6-v1; point-in-time paper execution; 2-point adverse slippage per leg; configurable brokerage/statutory costs | Mine near/far-expiry ideas, prospective validation controls, execution-cost model and paper protocol |
| [market-inefficiency](https://github.com/vishnuvcr/market-inefficiency) | NIFTY index-option data acquisition/reconciliation; PIT/CPCV/DSR/PBO policy; net-of-cost requirement | Reuse data-engineering patterns and robustness standards where technically compatible |
| [research-ML-trading](https://github.com/vishnuvcr/research-ML-trading) | Technical/ML pipeline plus Pine strategy_v6 | Mine feature families and non-option directional signals only |
| [ML-trading-v2](https://github.com/vishnuvcr/ML-trading-v2) | Next-session NIFTY-equity surge/anomaly prediction, including a 5% High/Open event | Use as event-definition and anomaly-detection prior art, not as an options execution strategy |
| [btst-strategy-lab](https://github.com/vishnuvcr/btst-strategy-lab) | Rule, factor, regime, ranking, ML and hybrid BTST research with embargoed walk-forward OOS and costs/slippage | Transfer validation architecture and candidate family ideas to NIFTY direction testing |
| [Surge-identifier](https://github.com/vishnuvcr/Surge-identifier) | NSE equity next-session +3% high/open event; F&O context, OI/PCR features, technical/volume/volatility model | Mine surge-event labels, derivatives context and regime features |
| [market-gainer-predictor-specificity-prioritised](https://github.com/vishnuvcr/market-gainer-predictor-specificity-prioritised) | 5% next-session surge target, high-specificity screening, technical/volume features | Mine high-specificity event formulation and threshold discipline |
| [market-gainer-predictor-specificity-precision-prioritised](https://github.com/vishnuvcr/market-gainer-predictor-specificity-precision-prioritised) | stricter precision/specificity configuration; daily P&L/trade artifacts | Mine precision-first decision thresholds and cost-sensitive ranking |
| [Institutional-Algorithmic-Trading-System](https://github.com/vishnuvcr/Institutional-Algorithmic-Trading-System) | 15-minute ML pipeline; fractional differentiation d=0.40; cross-sectional quintile filtering; monotonic GBDT + RF + logistic ensemble; NIFTY regime features | Re-test these as candidate directional feature transformations/models |
| [ML-trade](https://github.com/vishnuvcr/ML-trade) | Gradient-boosted next-day direction model with cost, turnover and drawdown penalties | Re-test cost-penalized model selection and compare against PIT-safe implementations |
| [CPR-](https://github.com/vishnuvcr/CPR-) | CPR/Camarilla/Virgin-CPR/multi-timeframe research workspace | Mine structured levels and regime/entry hypotheses after data validation |

## Evidence-status rule

Prior repositories are **prior-art and hypothesis sources**, not accepted performance evidence. Any copied model or rule must be re-run on this project's frozen dataset, cost model and tester gates.

## Most important transfer candidates

1. CPR / Virgin CPR / multi-timeframe levels.
2. Surge-event labels and high-specificity thresholding.
3. Fractional differentiation and monotonic ML ensemble.
4. NoDip far-expiry variants.
5. MC-RQ6-style distributional/Monte-Carlo directional evidence.
6. NIFTY F&O OI/PCR/derivatives context.
7. Iron-condor research's cost-aware parameter selection and delayed execution discipline.

## External research citations

The account/profile currently exposes 19 public repositories, including market-gainer-predictor-specificity-prioritised, Surge-identifier, Iron_condor, CPR-, market-inefficiency and qullamaggie-scanner. This repository intake is a research inventory, not a claim that every repository is relevant to naked option buying.
