# PPR-4 Tester Review 2 — Prospective Holdout Design (Design-Only Gate)

**Review date:** 2026-10-10  
**Branch:** `phase-07-tester`  
**Decision:** **PASS WITH SCOPED RESTRICTIONS — DESIGN ONLY**  
**Current overall PPR-4/data gate:** remains closed pending source-acquisition/cache manifest review. This approval does not authorize data requests, downloads, modeling-panel acceptance, fitting/tuning/scoring, prospective forecast capture, final label release or options P&L.

## Exact reviewed snapshot

| Artifact | Branch | Blob SHA |
|---|---|---|
| Prospective holdout proposal | `phase-07-developer` | `23f19a3e8068f6687545df15917fce23498ba462` |
| PPR-4 source availability manifest | `phase-07-developer` | `7f98d51e56c3f5ff33d8d070e1f777b10095ed54` |
| PPR-4 source register | `phase-07-developer` | `143ffe396308719142b3c89d36444ec136c1ee0b` |
| Holdout metadata audit | `phase-07-developer` | `6b236e60337b8ae6d1c108cfe7fbdcbe39cb1eda` |
| PPR-4 source/cache validator | `phase-07-developer` | `b93b80cf1c82474320e976f2d4b834c65011817c` |
| Prior PPR-4 tester review | `phase-07-tester` | `1cf137d83c6b285cff093163b886484d1d9c55cb` |

**Exact-snapshot offline receipt:** [run 38076047468](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38076047468), success on trigger commit `adadfbf9932a7d5f422b24d781313e8e70c87bed`. It validated the source/cache/holdout metadata files and their pins only. It does not validate a future holdout boundary, because the proposal's boundary does not exist until a later approved final configuration freeze.

## Review findings

### Approved design elements

1. **No retroactive relabeling.** All current historical data and prior Run44/Phase 7 observations are classified as development-only. The design explicitly rejects choosing an already-used historical portion and rebranding it as “untouched”.
2. **Deterministic prospective boundary.** The proposed final freeze is to occur after development-period candidate results are independently audited and before future holdout outcomes are observed. The first holdout origin is the first official NSE session whose IST trading date is strictly later than the IST local date of that freeze commit. The official exchange calendar and exact session IDs must be frozen/hashed before the first forecast. If the calendar or timestamp cannot be verified, the run stays blocked.
3. **Finite window with horizon maturity.** The protocol uses 252 future NSE forecast-origin sessions and a 10-session maturity tail, sufficient to realize the registered maximum 10-session target. The data capture stops according to official session count; the window cannot be shortened based on interim performance.
4. **No in-period selection.** Model parameters, feature recipes, probability conversion, hyperparameters, seeds, candidate membership, baseline, code and dependency hashes freeze before the first origin. During holdout, model weights/parameters are fixed and point-in-time features may update only from data available at each decision. No tuning, refitting or candidate selection is permitted during the final period.
5. **Prediction-before-label protocol.** Each decision creates an immutable prediction-only record with split ID, origin, target/horizon, model ID, source snapshot hashes, time and output hash before the target matures. The forecasting job cannot emit realized return labels, aggregate metrics or rankings.
6. **One-time independent release.** After all origins and the 10-session tail mature, the tester verifies prediction-ledger completeness and hashes before a separate scoring job releases labels. The tester then independently recomputes all loss metrics, familywise max-statistic results and confidence intervals. The final holdout is spent after one release.
7. **Missing-cell/statistical consistency.** Source-ineligible configs are blocked before final family freeze. No candidate-specific row removal is allowed. Any missing frozen candidate forecast makes the family `INCOMPLETE_NOT_PROMOTABLE`; no confirmatory family (p)-value or promotion may be issued from a smaller set. The 250-row minimum does not override the completeness rule.
8. **Budget consistency.** Existing PPR-3 development screening is bounded at 4,344 fits (3,564 conservative outer fit allowance + 780 inner tuning folds). The final holdout fit is separately bounded at another 3,564 fits, with no repeated tuning. Cumulative PPR-3 development plus final confirmation is at most 7,908, below the declared 8,000 cap, provided no extra uncounted calibration/feature-selection fits are added. If implementation needs more fits, stop and request amendment first.
9. **Strict scope separation.** A design-only PASS is not approval to fetch data or pretrained models. It does not authorize model-panel acceptance, model fitting, predictions on future holdout origins, final label release or option P&L.

### Remaining governance requirements before source or model operations

- The current PPR-4 boundary finding stays truthful: no existing machine-readable final-holdout boundary was found after scanning 23 branch trees and relevant metadata. The approved path is a *new prospective* boundary, not a claim that a boundary already exists.
- Before any source-specific bytes are requested, the developer must submit a separate source-acquisition/cache manifest including exact URLs/identifiers/revisions, required fields, history range, license/terms, source schema, timestamp/PIT handling, missingness, cache destination, size/rate limits and allowed operation. Public metadata and licensing must be considered first; do not assume HF visibility grants bulk-download or redistribution rights.
- After data/code validation and development results have been audited, the developer must create the real machine-readable future holdout manifest using the approved deterministic selector and actual freeze commit/date/session keys. That real manifest must be committed/hash-pinned before the first holdout forecast; the forecast-capture and score-release workflows need their own tester gate.
- If the final freeze time, official calendar, prediction capture, or future data availability cannot be evidenced, do not start/continue the final holdout.
- Existing one-use Dhan sample approval remains spent. No market data was downloaded during this review.

## Decision

**PASS WITH SCOPED RESTRICTIONS — prospective holdout design only.** The design resolves the *protocol choice* for replacing a missing historical holdout. It does **not** prove the missing boundary exists, close PPR-4, or authorize data access. The next permitted developer task is to prepare a source-acquisition/cache manifest using only documented source metadata; that new manifest requires a separate exact-snapshot tester decision before any source-specific download.

**Developer → Tester:** Submit an exact source-acquisition/cache manifest for metadata review, with free-source candidates, schemas, licenses, PIT rules, cache/size limits and operations explicitly denied by default. Do not issue source requests or run models.

**Tester → Developer:** Limit this approval to the design and manifest drafting. Keep data acquisition, modeling, final forecast capture and label release blocked until a new exact-snapshot gate approves exact sources and operations.
