# Research Conversation / Decision Log

## 2026-10-07

### User request

Test every plausible method for predicting NIFTY 50 direction, for both intraday and positional trading, while restricting the eventual strategy to naked long call/put buying. User requested invention of new metrics/models/rules and an exhaustive research effort.

### Developer decision summary

- Interpret “every possible way in the universe” as a finite pre-registered method universe that is broad, reproducible and exhaustively covered, not literal infinite/unbounded search.
- Keep intraday and positional research separate.
- Do not use option-selling strategies as the final strategy family.
- Include global/NSE/BSE inefficiencies, option data, FII/DII, volatility, sentiment, macro/cross-market information and execution frictions where relevant.
- Require developer/tester gates and immutable logs.
- Preserve failed methods as research results.
- Never claim a result exists before it has been run and independently verified.

### Prior-project continuity recovered from Project artifacts

Earlier project artifacts reported:
- next-day direction model on an untouched holdout: AUC about 0.458, accuracy about 48.2%;
- 5-session volatility expansion prediction: AUC about 0.688;
- an apparent directional trading rule failed stronger CPCV/robustness testing;
- option-surface/skew information remained an interesting signal.

Those are prior findings to be revalidated, not accepted as current conclusions.


## 2026-10-09 — Resume checkpoint

- User instructed: “Ok proceed”.
- Verified Phase 7 Run #994 (`37957677656`) remains in progress at the empirical ensemble step; regression and tester authorization gates passed, and artifact upload has not started. No metric is accepted.
- Investigated main-branch Research Protocol Check #997 (`37959386545`): job logs showed a deterministic infrastructure defect, `scripts/validate_protocol.py` missing from main. The workflow had skipped the literature check and all gated phase jobs as a result.
- Developer fix copied `scripts/validate_protocol.py`, `scripts/validate_literature_registry.py`, and `research/literature/LITERATURE_REGISTRY.csv` byte-for-byte from `phase-07-developer` to `main`. This is infrastructure synchronization only; no research code, results, or phase authorization changed.
- Next: confirm a fresh main protocol run passes, keep monitoring Run #994, and have the independent tester audit the exact new artifact after it uploads.
- Private hidden chain-of-thought is not archived; decisions and verifiable actions are recorded instead.
