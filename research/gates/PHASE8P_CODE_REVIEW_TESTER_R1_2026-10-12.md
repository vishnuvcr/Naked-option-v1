# Independent Tester Report — Phase 8P Greek Prediction Code Gate R1
Date: 2026-10-12
Role branch: `phase-08-prediction-tester`
Developer snapshot reviewed: `16cb5d266c6312aeeea07ebd61fbbcd589a8281d`
Developer module blob: `2e69fff59e694e7fb06111c3af5a8ad5e03ac746`
Developer test blob: `a7bc842d63e07c1041c98f7de83d9a6f78c4be43`
Developer synthetic workflow blob: `9ba46f5563de564b22de088fea5e59cf48792655`
Approved scope blob: `018500722f88f5fb100a2e24afc3d5d97394631e`

## Decision
**REQUEST CHANGES — CODE GATE NOT PASSED.** Real artifact download/decryption and empirical model fitting remain prohibited.

## Test evidence
- Developer synthetic workflow [#38199456531](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38199456531) passed on code/test blobs matching this reviewed snapshot. Receipt artifact [11724718426](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38199456531/artifacts/11724718426), SHA-256 `b108b9f412f4532b6de50e7b4763651caf409d6d0faf8cb95c78feff4ddf4cf4`. This is synthetic-only evidence, not empirical prediction validation.
- Independent tester review workflow [#38199864955](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38199864955) returned `REQUEST_CHANGES`: 9 of 13 recorded checks passed; the decision artifact is [11724953413](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38199864955/artifacts/11724953413), SHA-256 `b55fa2a3ff3d0dcaae38a4178410587d8fc48b721b7c37e19355ccadcada5b6b`.
- Independent arithmetic checks passed for the signed Delta imbalance, put/call ratio, put-minus-call IV difference, paired Brier sign, and Holm adjustment.
- No real market artifact was downloaded or decrypted; no empirical model was fitted; no external source was called; no holdout or option P&L was accessed.

## Findings requiring correction

### F1 — No complete end-to-end prediction run
The submitted module has utility functions but no implementation of the required full study path:
- pinned artifact identity/hash verification;
- option-feature frame construction over the encrypted monthly parts;
- feature-to-panel exact alignment for daily and intraday decisions;
- a reproducible 2-model × 10-horizon runner with primary metrics, all raw p-values and Holm-adjusted p-values;
- aggregate-only report writing and post-run plaintext cleanup.

The CLI currently only supports `--self-test` and `--validate-decision`; it has no real schema-preflight/run entry point. A synthetic green test therefore cannot yield the promised research result.

### F2 — Empirical authorization is caller-controlled
`walk_forward_predict` accepts caller-provided `scope_approved` and `code_approved` booleans plus an arbitrary dictionary for `preflight`. A caller can supply `True, True` and a fabricated `model_fit_authorized=True` mapping; the function does not verify a signed/pinned tester decision, its developer commit, the frozen artifact IDs/digests, or the exact preflight artifact hash. A separate workflow gate alone is insufficient unless the actual empirical entry point enforces the same exact bindings.

### F3 — Chronological split order is not validated
`walk_forward_predict` checks that unique block IDs are contiguous but does not verify that `block_index` is non-decreasing with ordered decision timestamps or that each block maps to a contiguous chronological interval. Its `blocks < b` training filter can therefore include later observations if block IDs are misassigned. Add regression fixtures for decreasing/reordered IDs and fail closed before any model fit.

### F4 — Exact snapshot helper rejects normal mixed composite rows
Independent mixed-row fixture failed. `exact_snapshot_rows` loops over every input row and raises when a Greek valuation offset is missing. The accepted R3 artifact includes SPOT rows for which `greek_valuation_offset_seconds` is not an option valuation and is NaN. The helper must exclude SPOT rows before applying option Greek timestamp checks, while continuing to reject missing timestamp/offset fields on OPTION rows. Preserve strict exact-time joins.

### F5 — Daily feature path is missing
The panel validator represents daily decision timestamps from the daily source `date` field, which is date-only/naive; `build_spot_features` requires a timezone-aware timestamp and is based on minute-bar semantics. There is no `build_daily_spot_features` or approved, exact rule for mapping a daily decision date to a Greek valuation instant. Daily horizons cannot currently execute without either a tester-approved timestamp contract or a deliberately recorded `BLOCKED_DATA` outcome. Do not guess a time offset.

### F6 — Preflight does not pin the real input contract
The current `preflight_contract` checks generic manifest status/run/commit fields and trust-provided `holdout_exclusion_contract` / `target_maturity_contract` dictionaries, but it does not itself bind these to the R3 and Run #994 artifact IDs and SHA-256 values, verify embedded manifest/panel hashes, prove that the supplied holdout mask was extracted from an approved source, or verify the target-end rule against the exact frozen label code. The next preflight must be schema/coverage-only and fail closed unless those proofs are actually produced and independently accepted.

## Required developer resubmission
1. Preserve this R1 decision and current code snapshot as history.
2. Fix F2–F6 and complete F1 without loosening the approved scope or introducing any live/paid data source.
3. Add synthetic fixtures for mixed OPTION/SPOT snapshots, exact timestamp inclusion/exclusion, daily-date handling, block-order/purge invariants, authorization mismatch, and 20-cell/Holm report completeness.
4. Submit new exact commit/blob hashes. The tester must rerun the independent audit and issue a new code-only decision.
5. Only after code-gate PASS may a schema-only workflow download the exact pinned artifacts. The schema/coverage result then requires its own independent tester PASS before any model fitting. If target maturity or the protected holdout cannot be proven, report `BLOCKED_DATA` and seek a scope amendment; do not fabricate missing metadata.

**Tester → Developer:** fix F1–F6 and resubmit the exact new snapshot; no empirical artifacts, fitting, holdout, P&L or strategy work is authorized by this review.

**Developer → Tester:** retain R1 unchanged and independently rerun formulas, snapshot edge cases, block chronology, artifact/preflight bindings and end-to-end synthetic coverage for the resubmitted code.
