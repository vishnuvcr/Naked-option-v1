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


### 2026-10-07 — Resume research command

User requested that the research resume from the current checkpoint. Developer re-read the Phase 2 status, research plan/protocol, method registry, error/research logs and both developer/tester branch status ledgers before continuing. Phase 2 remains the active gate; no prediction/strategy phase is allowed to start until data/PIT validation is passed.

Current automated run: Phase 2 Data Audit run #60 is executing on `phase-02-developer`. Official NSE legacy/UDiFF acquisition, schema validation, snapshot generation and HF acquisition have already completed in this run; the reconciliation stage is still executing. Prior real-run failures were preserved and corrected rather than bypassed.

### 2026-10-07 — Continuation from user-provided checkpoint

User supplied a screenshot of the prior Phase 2C checkpoint after a conversation-length boundary and asked to continue.

Developer re-read the current repository rather than trusting the screenshot as the latest state. The repository had already progressed beyond Phase 2C: Phase 2 had passed with scoped restrictions and Phase 3 protocol work existed on the phase-03 branches.

The independent tester then audited the actual Phase 3 empirical package and issued REQUEST CHANGES. The developer is correcting the package on phase-03-developer only. Phase 3 remains the active gate; Phase 4 is blocked.

Current correction set includes restoring the research log, wiring the full empirical workflow, requiring explicit B0-B11 dispositions, correcting intraday B3/B4/B11 semantics, adding official NSE overlap checks for the intraday research reference, and strengthening the result-schema validator.


### 2026-10-07 — Family D run #19 monitoring continuation

User requested continuation from the live Family D run #19 checkpoint and ongoing monitoring in chat. Developer independently checked the repository governance, phase-05 developer/tester status ledgers, prior Family D tester approvals and the live GitHub Actions state.

Run #19 remains in progress with the regression suite passed and D01-D15 empirical execution active. A direct live-log fetch returned BlobNotFound; this is treated as an infrastructure inspection limitation only. No scientific metric is accepted before immutable artifact creation and independent tester review.


### 2026-10-07 — User said Ok proceed: Family D gate continuation

Developer rechecked the live run rather than treating the prior checkpoint as final. Run #19 remains in progress with D01-D15 empirical execution active, so no tester promotion action is yet authorized.


### 2026-10-07 — Another user continuation of Family D

User again authorized continuation. Developer rechecked hosted run #19 and confirmed the empirical D01-D15 suite is still active. No result promotion or tester gate is possible before immutable artifact creation.
