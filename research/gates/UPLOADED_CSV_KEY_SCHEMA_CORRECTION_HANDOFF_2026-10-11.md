# Developer handoff: CSV key-schema correction

Date: 2026-10-11

The prior tester review requested schema-specific keys. Developer changes on `phase-07-developer`:

- Added OPTION key: `timestamp_epoch,row_type,underlying,expiry_code,returned_strike,option_type`.
- Added SPOT key: `timestamp_epoch,row_type,underlying`.
- Kept legacy key groups for older fixtures.
- Batched SQLite inserts in chunks of 10,000 to reduce scan time and compute duplicate counts using successful insert deltas.
- Added `scripts/test_offline_dataset_actual_schema.py` for duplicate OPTION/SPOT and incomplete-key fixtures.
- Updated the offline synthetic workflow to execute the new test.

Exact current blobs:
- Scanner: `e27ec2688d2d0782408bb2d2e0ab4f4122fce9af`
- New tests: `12fec21c9374792b273f9b8167aa42545674497a`
- Test workflow: `2e3feaf8cd0edd39283d9ee675c9c52e4b75aaa8`

Hosted synthetic CI completion is not yet verified. The real-file audit has not been rerun. Prior exact-hash authorization is invalid for these changes and must not be reused. No duplicate count or data-readiness PASS is claimed. All modelling, holdout, source-request and strategy/P&L gates remain closed.

**Developer → Tester:** Independently review the code, exact hashes, batching duplicate logic and hosted test result.
**Tester → Developer:** Issue a fresh exact-hash decision only after synthetic CI passes; do not reuse the previous authorization.
