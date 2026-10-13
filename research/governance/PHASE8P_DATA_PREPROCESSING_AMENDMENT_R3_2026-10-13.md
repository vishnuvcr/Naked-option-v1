# Phase 8P data-preprocessing amendment — R3 (2026-10-13)

**Status:** FROZEN BEFORE PREDICTION PERFORMANCE INSPECTION  
**Machine-readable rules:** [PREDICTION_DATA_PREPROCESSING_RULES_R3_2026-10-13.json](../data/PREDICTION_DATA_PREPROCESSING_RULES_R3_2026-10-13.json)

## Scope
This amendment freezes deterministic handling of observations outside the official regular-session label grid. It does not change the ten horizons, label formula, model registry, chronological folds, sample minima, metric family or untouched-holdout restrictions. No R3 prediction metric had been computed when frozen.

## Official session-calendar corrections
- NSE/CMTR/57285 moved the 2023 Bakri Id holiday from June 28 to June 29; the official NSE Indices notice confirms June 28 was a trading session: [NSE Indices release](https://niftyindices.com/Press_Release/ind_prs27062023.pdf), [NSE circular](https://archives.nseindia.com/content/circulars/CMTR57285.pdf).
- NSE/CMTR/60338 makes 22 January 2024 a trading holiday: [NSE circular](https://archives.nseindia.com/content/circulars/CMTR60338.pdf).
- NSE/CMTR/61518 makes 20 May 2024 a trading holiday: [NSE circular](https://nsearchives.nseindia.com/content/circulars/CMTR61518.pdf).
- NSE/CMTR/64960 makes 20 November 2024 a trading holiday: [NSE circular](https://archives.nseindia.com/content/circulars/CMTR64960.pdf).
- NSE/CMTR/72349 declared live regular-hours trading on Sunday, 1 February 2026 for the Union Budget: [NSE circular](https://nsearchives.nseindia.com/content/circulars/CMTR72349.pdf).

Corrections are stored as source-bearing calendar entries. A date is never made a trading session merely because data rows exist.

## Observation eligibility
A row can be used for the frozen spot-direction labels only if it is a SPOT observation on a pinned date marked open, eligible for both label grids, compatible with regular hours, minute-aligned, within 09:15–15:30 Asia/Kolkata time and has a finite positive close. Closed/unmapped, nonstandard, out-of-session, non-minute and invalid-price rows are quarantined from predictor and target endpoint use. Raw source bytes remain immutable; no interpolation, forward-fill or synthetic prices.

Quarantine does not waive coverage tests. Targets require exact observed endpoints. The preregistered 1.0% missing-target-pair threshold and fold-specific sample/directional class minimums remain hard gates. Positional horizons count only `prediction_session_index`, excluding Muhurat/BCP-DR sessions from the label clock.

Option-based configurations with unavailable expiry/strike/IV/Greek/contract data remain blocked; those fields cannot be imputed from future metadata.

## Reproducibility and security
R3 preregistration pins the policy by Git blob SHA-1 and SHA-256. Plaintext remains only in temporary runner storage; raw rows and plaintext are not uploaded. Tester review remains deferred until all planned results are acquired, frozen and hash-pinned.
