# Canonical Phase 2 Data Schema

## Observation timestamp rule

Every observation has:
- `timestamp_utc` or `timestamp_ist`;
- `available_at` (the earliest time the observation could have been known to the trader in this research simulation);
- `source_id`;
- `snapshot_id`.

## Underlying fields

`trading_date, timestamp, underlying_symbol, open, high, low, close, volume, turnover, available_at, source_id, snapshot_id`

## Option observation fields

`trading_date, timestamp, underlying, option_symbol, expiry, strike, option_type, open, high, low, close, ltp, settle_price, volume, oi, change_oi, underlying_value, bid, ask, available_at, source_id, snapshot_id`

Bid/ask are optional but absence must be explicit, never silently inferred as zero.

## Contract master

`underlying, option_symbol, expiry, strike, option_type, listing_from, listing_to, lot_size, tick_size, available_at, source_id, snapshot_id`

Contract master is interval/effective-dated. It must not be validated as if it were a normal timestamp observation.

## Cross-market fields

`instrument, exchange, timestamp, local_timezone, close, available_at, source_id, snapshot_id`

The schema retains original local timestamps and a normalized time representation.

## FII/DII fields

`report_date, segment, participant, buy_value, sell_value, net_value, published_at, available_at, source_id, snapshot_id`

If publication timing cannot be demonstrated, the conservative default is next-session availability rather than same-session predictive use.

## News/event fields

`event_id, event_time, headline_time, published_at, source_timestamp, sentiment, surprise_score, source_id, available_at, snapshot_id`

No NLP feature can use an article body/headline before its recorded/publication availability time.

## Quality flags

Every canonical table may carry:
`is_duplicate, is_missing_core, is_outlier, is_stale, is_composite, provenance_chain`

Quality flags are not overwritten; they explain transformations.
