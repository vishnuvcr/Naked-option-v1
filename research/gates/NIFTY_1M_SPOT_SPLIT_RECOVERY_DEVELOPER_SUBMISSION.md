# Developer Submission — Exact-Snapshot Review for Dhan Spot Split Recovery

**Date:** 2026-10-11  
**Role/branch:** Developer, phase-07-developer  
**Decision requested:** review this exact commit and, only if every check passes, permit the bounded live spot-only recovery below.

## User request and reason
The user explicitly requested that Dhan be used to recover missing NIFTY spot bars rather than fabricate or interpolate market prices. The latest accepted artifact had six failed Dhan spot shards due to a 12,000-row response cap; the prior retry proposal splits their contiguous 234-calendar-day interval into 34 shards.

## Exact bounded request scope

- Endpoint: POST https://api.dhan.co/v2/charts/intraday.
- Instrument: securityId=13, exchangeSegment=IDX_I, instrument=INDEX, one-minute interval, no OI.
- Dates: 2021-10-11 inclusive through 2022-06-02 exclusive, exactly 234 calendar days.
- Request grid: exactly 34 contiguous, nonoverlapping shards; each at most 7 calendar days.
- Per-response caps: 4,000 rows and 8,388,608 bytes.
- Attempts: one per shard; zero retries; maximum 34 wire requests. Serial pacing remains 2 requests/second.
- No option endpoint, order/trading endpoint, model fitting, prediction scoring, holdout access, or strategy/P&L testing.

## Immutable base and acceptance criteria

- Base Actions artifact: [11693866249](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38116772719/artifacts/11693866249).
- Base ZIP SHA-256: aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216.
- Preserve exactly 8,490,723 option rows and all 403,664 already recovered spot rows; never start from the original zero-spot artifact.
- Add only validated Dhan observations; join only on exact timestamp_epoch. Missing values stay missing. Keep request IDs, response hashes, source lineage and quality flags. Do not silently correct source values or impute target prices.
- Preserve input response/artifact immutability. Encrypt caches and output parts; remove all plaintext scratch before artifact upload. Publish safe metadata and failure counts only.
- The user waived external price-value reconciliation for returned Dhan values. This does not waive parse, schema, timestamp alignment, duplicate, timezone or internal OHLC checks.

## Relevant reviewed implementation snapshot

The following files are unchanged from the offline pipeline-test snapshot a08ba25d308f64896d39b0aae89f64317453b824, run [38122563406](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38122563406), which completed successfully:

| Path | Blob SHA |
|---|---|
| scripts/run_nifty_1m_spot_gapfill.py | ef5b5486c98d9a8dbd297f6d4a221f3ab28fc45e |
| scripts/test_nifty_1m_spot_gapfill.py | 236775f1bb54286a12223e9d44744b80500d55a1 |
| scripts/validate_nifty_1m_spot_gapfill_split_proposal.py | 52feb8627db20077aa1a5ff08e406df7c82e9481 |
| .github/workflows/phase-07-nifty-1m-spot-split-recovery.yml | 9b16c19bcd886ff7e6d12d24c98b89d965a8fdd0 |
| research/gates/NIFTY_1M_SPOT_GAPFILL_SPLIT_PROPOSAL.json | 77f40a95604777721fd701f4d7245bf43a8871f5 |

The tests cover proposal geometry, stale/missing tester-decision rejection, exact-SHA checks, zero-retry behavior when max_attempts=1, exact timestamp joins, and preservation of existing rows. The workflow verifies the immutable base artifact hash, spends a one-use execution marker before any source access, checks that DHAN_ACCESS_TOKEN and HF_TOKEN exist without printing values, and removes plaintext scratch on completion.

## Prior gate state — must not be reused

The current tester decision is OFFLINE_SPLIT_MANIFEST_DESIGN_ONLY and sets live_requests_authorized=false. A previous one-use approval is SPENT. Neither authorizes this new request. The workflow must not run a request unless the tester branch writes a fresh exact-snapshot decision that explicitly sets decision_scope=SPLIT_RECOVERY_EXECUTION, split_recovery_authorized=true, live_requests_authorized=true, split_recovery_request_limit=34, split_recovery_retry_limit=0, with live option/model/holdout/strategy permissions false.

## Required independent tester checklist

1. Review the developer commit SHA that contains this submission and verify the current split-proposal blob is still exactly 77f40a95604777721fd701f4d7245bf43a8871f5.
2. Verify the implementation/test/workflow hashes above and inspect the one-attempt path, global request cap, exact timestamps, row-preservation checks and cleanup steps.
3. Verify the workflow has no option requests and keeps model fitting, holdout access and strategy testing false.
4. Verify no data are yet claimed recovered at submission time. Run metadata must distinguish workflow status from scientific completeness status.
5. Publish a tester report and machine-readable decision on phase-07-tester only. Do not edit developer code from the tester role.
6. If passing, authorize only the exact 34 spot requests and zero retries. If any concern remains, issue REQUEST CHANGES and leave live authorization false.

**Role caveat:** this review path is separated by repository branch and exact commit, but the connected session does not provide a separately identified human reviewer. Do not claim external independent-person review or AI inference when it was unavailable.

**Developer → Tester:** Review the exact snapshot and either grant the narrowly scoped authorization or record concrete blocking findings.  
**Tester → Developer:** Return the report and machine-readable decision; do not grant model, holdout, option-history, or strategy permissions through this data-recovery gate.
