# Phase 8 — Options Data, Point-in-Time and Source Plan

## Status

**DRAFT FOR INDEPENDENT TESTER GATE — DATA ACQUISITION NOT YET ACCEPTED**

## Data requirements

The canonical Phase 8 composite must support:

- NIFTY 50 option contract identifier;
- option type CE/PE;
- strike;
- expiry;
- lot size;
- timestamp;
- OHLC and, when available, bid/ask;
- volume;
- open interest;
- implied volatility and/or delta where available;
- underlying NIFTY value;
- source and snapshot provenance.

The final composite is row-level de-duplicated and hashed. Source precedence is explicit and cannot vary by observed strategy performance.

## Free-source-first acquisition sequence

### Source 1 — Official NSE

Use official NSE archives/contract information for:

- instrument and contract master;
- permitted lot sizes;
- expiry calendars;
- strike schemes/tick sizes;
- daily derivative bhavcopy/OHLCV/OI;
- official statutory/transaction-charge circulars.

NSE's current contract-information page exposes permitted-lot-size and contract-information resources. The current NIFTY 50 product page states Tuesday weekly/monthly expiry rules. These official metadata are the controlling reference.

### Source 2 — Hugging Face public historical dataset

Audit `artist-23/nifty-options-data`, currently indexed as approximately 34 million option rows spanning late 2020 through late 2025, with OHLC, IV, volume, OI, strike, spot, date/time and option-type fields.

This source is a candidate research source only until:

1. sample values are checked against official NSE records;
2. timestamps and timezone are reconciled;
3. duplicate/missing-value rates are measured;
4. lot-size/expiry joins are validated;
5. provenance/licence and reproducibility are recorded.

Use `HF_TOKEN` only through repository secrets/workflows; never commit credentials.

### Source 3 — Open-source NSE historical clients

Audit reproducible clients such as `jugaad-py/jugaad-data` for retrieval of official NSE historical index-option data.

The client is an acquisition mechanism, not an independent truth source. Retrieved records remain subject to direct NSE reconciliation.

### Source 4 — Open GitHub composite datasets

Audit open repositories such as the NIFTY options-data-engine and other public option archives as secondary completeness sources.

They may fill gaps only after overlap tests and row-level provenance rules pass.

### Source 5 — Other free datasets

Kaggle/Hugging Face/public Parquet archives may be used when they add history or fields not present elsewhere, subject to the same overlap and timestamp validation.

### Paid sources

Paid/vendor feeds are **blocked** until all materially relevant free routes above are exhausted and a written data-quality gate shows that the missing field materially prevents quote-executable research.

No paid purchase is a default Phase 8 action.

## Composite-data reconciliation

For overlapping observations:

1. exact contract key = underlying + expiry + strike + option type + timestamp;
2. compare prices and OI/volume across sources;
3. define tolerance before inspection of strategy results;
4. prefer official NSE values for exchange metadata;
5. retain the secondary value and provenance for disagreement analysis;
6. do not choose the source that gives better trading results;
7. log every material conflict.

## Point-in-time controls

At decision timestamp t, only these are allowed:

- contracts listed by t;
- latest known contract metadata as of t;
- underlying price at or before t;
- option quote/trade/OHLC at or before t for selection;
- prior observed volume/OI for liquidity rules;
- dated fee/rate schedule effective at t.

Never use:

- future expiry availability;
- future strike listings;
- future lot size;
- later-restated IV;
- later volume/OI;
- future corporate/calendar data;
- an exit quote to decide whether the entry contract was chosen.

## Timestamp normalization

All raw timestamps are preserved.

Canonical timestamps are UTC internally with a derived India-time field for session rules.

Regular NSE cash/F&O session mapping is validated against the Phase 3 intraday reference and official exchange session rules.

## Quote quality tiers

Each row is tagged:

- Q2 = validated bid/ask;
- Q1 = trade/OHLC only;
- Q0 = unusable or ambiguous.

Only Q2 supports quote-executable claims.

Q1 supports conservative proxy backtests.

Q0 is excluded from executable P&L.

## Historical lot size

The contract engine must join each contract to its effective lot-size snapshot.

The NSE October 18, 2024 circular revised the NIFTY 50 lot size to 75 for new index derivative contracts introduced from November 20, 2024. Earlier contracts retain their historical lot size. No global lot-size constant is permitted.

## Expiry rules

Current NSE NIFTY 50 index options use Tuesday expiry rules, subject to a previous-trading-day adjustment when Tuesday is a holiday. The date-appropriate contract master is authoritative for the historical backtest.

The primary strategy forcibly exits before expiry and does not depend on expiry exercise.

## Data-quality gate before empirical execution

The dataset cannot advance to the empirical job until:

- contract keys are unique;
- timestamps are monotone within contract;
- lot-size joins are complete for executable rows;
- no future contract metadata enters earlier rows;
- official NSE overlap error is below the pre-registered tolerance;
- option-price positivity and tick-size checks pass;
- missing-field statistics are recorded;
- source hashes are stored.

No strategy result is generated from an unapproved composite.

## Phase 7 row-level forecast dependency

Run #654's accepted artifact stores aggregate candidate metrics but not a complete row-level probability table. Before empirical option execution, regenerate the P01–P10 prediction panel deterministically from the frozen Run #654 developer commit and source inputs. The reconstruction is accepted only when all 100 aggregate metrics reproduce within a frozen numerical tolerance. The prediction panel is then hashed and treated as an immutable Phase 8 input.


## Tester-required data controls now frozen

- Intraday liquidity tie-break = prior 15 complete one-minute bars' volume; daily liquidity tie-break = prior-session volume.
- Critical metadata missing <=0.5%; stale observations <=1%; entry no-fill <=10%; exit-liquidity-failure <=1%; duplicate rows and invalid premiums are not permitted.
- A historical Paytm brokerage fallback is exactly ₹20/order when the historical tariff cannot be independently verified and is explicitly tagged `BROKERAGE_FALLBACK`.
- The complete registered grid is 4,800 configuration cells; unavailable configurations are retained as explicit `INELIGIBLE` statuses with deterministic reasons.
- The Run #654 row-level forecast reconstruction must reproduce integer counts exactly and continuous aggregate metrics within 1e-9 absolute tolerance before any option result is generated.
