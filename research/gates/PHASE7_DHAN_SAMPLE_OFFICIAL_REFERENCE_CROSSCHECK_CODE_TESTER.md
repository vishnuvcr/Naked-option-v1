# Independent Tester Report — Official NIFTY Cross-Check

Decision: REQUEST CHANGES. No live request is authorized.

The current adapter, runner, and test blob IDs differ from the IDs recorded for hosted run 38056916677. That historical 32-test PASS therefore does not verify the exact current snapshot. Re-run the offline workflow against the current developer branch, record the run ID and exact file blob/SHA-256 pins, and resubmit for independent review. The current review performed no network requests. Do not create/consume a live manifest, fetch NSE/Dhan sources, accept data for modeling, or rerun prediction models until a fresh exact-snapshot tester PASS.

Positive checks: one-date OHLC scope plus one public instrument-master lookup; no credential forwarding; normal CLI offline-only; explicit live flag plus environment gate; redirect/retry prohibition; exact OHLC comparison; volume explicitly not cross-checked; cache only after both sources and comparison pass.

Tester → Developer: fix the stale-snapshot evidence gap and resubmit the exact hosted test receipt and hashes.
Developer → Tester: re-review the exact post-test snapshot; no live request until explicit PASS.
