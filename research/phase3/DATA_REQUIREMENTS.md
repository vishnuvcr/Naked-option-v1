# Phase 3 Data Requirements

## Canonical daily layer

- NIFTY 50 daily OHLCV/close. Official NSE data are preferred; when bulk official archive acquisition is technically unavailable, a free Yahoo bulk backfill may be used only after explicit overlap validation against official NSE archive dates, with provider provenance retained.
- trading calendar.
- official availability timestamp/observation date.
- India VIX where PIT-safe.
- FII/DII where PIT-safe.
- global overnight closes with exchange timezone.

## Intraday layer

Target:
- 1-minute NIFTY underlying or a validated option dataset containing an underlying NIFTY series.

Derived datasets are accepted only as labelled research references after:
- source revision pinned;
- schema verified;
- overlap against official data demonstrated;
- PIT timestamps checked;
- missingness documented.

## Option layer for economic labels

Minimum fields:
- decision timestamp;
- option symbol;
- expiry;
- strike;
- CE/PE;
- entry premium;
- later exit premium;
- OI/volume where available;
- underlying;
- lot size;
- source/provenance.

## Minimum sample requirements

Do not publish a baseline result until:
- >= 1,000 daily observations for positional baselines, or all available observations with explicit low-power warning;
- >= 50,000 intraday decision observations across multiple market regimes for intraday baselines, or explicit low-power warning;
- at least 3 distinct volatility regimes;
- at least 2 calendar years for any claim of stability where the data allow it.

These are adequacy criteria, not guarantees of statistical power.
