# Frozen Research Windows — Phase 2C

## Decision date

2026-10-07.

## Primary research windows

### Positional NIFTY option research
- Start: 2019-02-11
- End: 2026-09-30
- Frequency: official NSE end-of-day NIFTY index-option contract observations
- Purpose: 1/2/3/5/10-session direction labels and option-selection experiments.

### Intraday NIFTY option research
- Start: 2021-01-01
- End: 2026-09-30
- Frequency: 1-minute or the highest validated sub-daily resolution available from the free source universe.
- Purpose: 5/15/30/60/120-minute direction and executable long-option research.
- Important: derived intraday sources are never treated as canonical until date/contract/price reconciliation passes.

### Contextual daily macro/regime window
- Start: 2019-02-11
- End: 2026-09-30
- Inputs: India VIX, global equity indices, US 10Y/DGS10, USD/INR, breadth, sector indices, FII/FPI/DII where available, gold/crude where source integrity permits.

## Holdout discipline

The final untouched forward period is not used during Phase 2 acquisition/feature engineering. Phase 3-9 may use the training/development period only. The final forward period will be frozen before strategy selection and disclosed in the final manuscript.

## Data-window rules

- A source with a shorter verified history is not padded backward.
- Missing dates remain missing until reconciled to an official market calendar.
- A source can be useful for a sub-window without becoming a universal source.
- All window dates are stored in experiment manifests.

## Rationale

2019-02-11 maximizes the positional option sample while remaining within the modern weekly-option regime. 2021-01-01 is the conservative start for the intraday executable research layer because free intraday sources are not yet validated for earlier history. 2026-09-30 is the frozen end date so the 2026-10-07 research work does not contaminate the test window.
