# Tester Report — NIFTY Spot Split Recovery Execution Gate

**Decision: PASS WITH SCOPED RESTRICTIONS for the exact bounded spot-only request manifest.**  
**Reviewed developer commit:** daad5f22d08c912bbcfc0a7a616239f89574a48e  
**Proposal blob:** 77f40a95604777721fd701f4d7245bf43a8871f5  
**Review time (UTC):** 2026-10-11T08:21:43.207Z  
**Tester branch:** phase-07-tester

## Scope of this decision

This review authorizes only the 34 one-minute NIFTY spot-history requests described in research/gates/NIFTY_1M_SPOT_GAPFILL_SPLIT_PROPOSAL.json. It does not authorize live option-data calls, model fitting/scoring, holdout access, strategy/P&L evaluation, or trading endpoints.

## Exact-snapshot checks

The developer commit daad5f22d08c912bbcfc0a7a616239f89574a48e contains a documentation/status/log handoff. The acquisition implementation was not changed by that commit. The following current blob hashes were fetched from the reviewed branch and match the already passing offline pipeline snapshot (a08ba25d308f64896d39b0aae89f64317453b824):

| Path | Verified blob SHA | Finding |
|---|---|---|
| scripts/run_nifty_1m_spot_gapfill.py | ef5b5486c98d9a8dbd297f6d4a221f3ab28fc45e | unchanged |
| scripts/test_nifty_1m_spot_gapfill.py | 236775f1bb54286a12223e9d44744b80500d55a1 | unchanged |
| scripts/validate_nifty_1m_spot_gapfill_split_proposal.py | 52feb8627db20077aa1a5ff08e406df7c82e9481 | unchanged |
| .github/workflows/phase-07-nifty-1m-spot-split-recovery.yml | 9b16c19bcd886ff7e6d12d24c98b89d965a8fdd0 | unchanged |
| research/gates/NIFTY_1M_SPOT_GAPFILL_SPLIT_PROPOSAL.json | 77f40a95604777721fd701f4d7245bf43a8871f5 | exact proposal preserved |

The corresponding [offline pipeline test run 38122563406](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38122563406) succeeded. Its steps report that the collector/decryptor/validators compile, offline manifest and dataset tests pass, the request grid is validated, and the existing approval helper’s offline self-test passes. This is an offline-code gate result, not evidence that any Dhan retrieval has completed.

## Mathematical and request-grid review

- The 34 windows are contiguous and nonoverlapping from 2021-10-11 inclusive to 2022-06-02 exclusive: 234 calendar days total.
- Each window spans at most 7 calendar days; all requests use max_rows=4000, max_response_bytes=8,388,608, and max_attempts=1.
- The total maximum is 34 new wire requests, zero retries. The collector checks the global cumulative request budget and records attempts in the request ledger before network access.
- The endpoint is POST https://api.dhan.co/v2/charts/intraday with securityId=13, exchangeSegment=IDX_I, instrument=INDEX, interval=1, oi=false. The proposal contains no rolling-option endpoint or orders/trading API.

## Data integrity and safety review

- The guarded workflow checks the exact current developer SHA and proposal blob, refuses an absent/stale/wrong-scope tester decision, and checks that its single-use split marker has not already been spent.
- Before the first data request, it downloads the existing encrypted base artifact 11693866249 and verifies ZIP SHA-256 aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216.
- The runner verifies the base data’s encrypted manifest and row counts: 8,490,723 option rows and 403,664 spot rows. It merges only into that partial artifact and asserts the original option count and previously recovered spot rows are preserved.
- New spot observations are joined to option rows only by exact timestamp_epoch. A nearby timestamp, rolling-option spot field, interpolated value or fabricated replacement is not accepted as the missing spot bar.
- Parser/schema/timestamp and internal OHLC checks remain enabled. Missing or misaligned volume stays blank and receives a quality flag; it is not zero-filled.
- The workflow removes plaintext scratch directories on completion and uploads only encrypted CSV parts plus safe metadata. Request and response lineage is carried in the dataset.
- The workflow can report SPOT_GAPFILL_PARTIAL if Dhan rejects or omits any shard. A successful workflow status is not itself proof of data completeness; completion requires all requested shards to validate and zero missing exact spot joins under the runner’s criterion.

## Restrictions and residual caveats

1. The last value-level data audit is FAIL. This execution decision does not clear it, authorize fitting, or promote a clean prediction dataset.
2. The earlier acquisition approval was spent and is not reused. This is a fresh, exact-snapshot scope with a separate split execution marker.
3. All previous raw/provider observations are immutable. The user waived external provider-value reconciliation, but structural validation is not waived.
4. Do not log access-token values or plaintext price rows. If request failure or partial coverage occurs, preserve safe error counts and encrypted artifacts; do not silently restart with an expanded request grid.

## Decision

**PASS WITH SCOPED RESTRICTIONS:** permit only the 34 manifest-pinned NIFTY one-minute spot requests, at most 34 wire attempts and zero retries. Live option requests, model fitting/scoring, holdout access, and strategy testing remain false.

**Role caveat:** the tester branch is used as a separate review surface and this report does not modify developer code. The connected environment does not provide a separately identified human reviewer or independent AI inference result; do not represent this as a human third-party audit.

**Developer → Tester:** After the guarded run, compare only safe metadata, exact timestamp-join counts, artifact integrity, row preservation, and cleanup evidence; reject completeness if any required check fails.  
**Tester → Developer:** Preserve this exact scope. Do not start modelling or strategy testing based solely on an Actions workflow success; require the post-run data-completeness review as a separate gate.
