# Phase 3 Developer Submission

## Scope

Freeze label definitions, baseline models and option break-even rules before any large-scale predictive model search.

## What this gate does

- Defines intraday and positional direction labels.
- Separates direction prediction from option-economic profitability.
- Registers no-trade/abstention as a valid action.
- Establishes simple baseline families.
- Establishes cost-sensitivity scaffolding without hard-coding historical brokerage/statutory rates.
- Establishes sample-adequacy criteria.
- Adds deterministic protocol validation.

## Developer instruction to tester

Independently audit the mathematical definitions, horizon timing, leakage rules, option P&L formulas, cost scenario ordering, baseline completeness and the distinction between spot-direction accuracy and option-buying profitability. Reject any ambiguity that could create label leakage or hindsight selection.
