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


### Follow-up verification — 2026-10-09

- Research Protocol Check #1008 passed both validator steps after the missing validator/registry files and terminology mismatch were fixed.
- Run #994 still has no artifacts published at the latest query. The developer must continue monitoring and submit its exact immutable artifacts for tester review once uploaded.
 
## 2026-10-09 — Approved tester-audit workflow smoke test

- The automatic audit workflow's first run examined developer run #1033, a successful documentation-only protocol run with no Phase 7 artifacts.
- It correctly skipped the independent calculation; the skipped audit is not a strategy result or independent approval.
- Run #994 remains in progress without artifacts. The tester workflow will start only after the exact run is completed successfully and both required artifacts pass preflight.


 
## 2026-10-09 — Main log: audit preflight safety verified twice

- Main workflow audit runs #1 and #2 inspected completed developer protocol runs with no Phase 7 artifacts. Run #2 also verified the exact workflow-name guard, then skipped because the aggregate artifact was absent.
- Neither workflow ran the tester calculation. These are safety-gate checks only.
- Phase 7 Run #994 still has no artifacts; continue tracking this same run until completion and then audit its exact outputs.

## 2026-10-09 — Research resume: validated code-delta reason for fresh Run #994

- Compared Run #925 and Run #994 exact source code. The frozen protocol specification did not change; the new implementation fixes four prior independent-audit mismatches: P10 inclusive abstention, finite regime feature eligibility, NaN-preserving family-bootstrap missingness, and candidate-specific chronological block masks.
- The test suite includes explicit boundary/sign/missingness tests for those changes; the latest empirical workflow's regression step passed before the model calculation began.
- This establishes why the fresh run is justified but does not show improved performance. Run #994 is still in progress without artifacts, and the independent audit has not run.
- Tester → Developer: reconcile the exact artifact against all four fixes and the frozen protocol; preserve REQUEST CHANGES if any discrepancy remains.
- Developer → Tester: wait for the exact Run #994 artifacts and source commit; do not accept results from the preflight-only workflow runs.


## 2026-10-09 — Resume: P10 diagnostic invariant referred to tester

- The developer identified a possible inconsistency: the frozen spec requires P08/P09/P10 regime diagnostic block count to equal candidate chronological block count, but the current validator only enforces this for P08/P09 because P10 abstention can empty a metric block.
- Logged on both branches. Run #994's source commit remains immutable and active; no code/spec change was made to its running execution.
- Tester → Developer: adjudicate the frozen wording against the current output once available; require a tester-approved, pre-registered amendment if the spec must change. Keep Phase 8 blocked while unresolved.
- Developer → Tester: audit the exact Run #994 artifact and this count invariant explicitly; do not waive a failed check to preserve a run.


 
## Independent tester finding — P10 diagnostic block invariant (2026-10-09)

The isolated tester branch has issued [PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md) = **REQUEST CHANGES FOR SCIENTIFIC PROMOTION** for a static consistency issue: the frozen spec includes P10 in the regime-diagnostic/chronological-block count equality, while the current validator enforces this invariant only for P08/P09 because P10 abstentions can empty a block. Run #994 may complete and be audited as the already-running immutable execution, but no metric, method or strategy may be promoted until this issue is resolved through an implementation correction or a separate pre-registered tester-approved spec amendment. Phase 8 remains blocked.
