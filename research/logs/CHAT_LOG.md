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

### 2026-10-07 — “Ok proceed” continuation checkpoint

User instructed the research to continue. Developer resumed Phase 2C from the declared gate rather than starting Phase 3.

Developer actions recorded:
- inspected the developer/tester branch heads and canonical governance/status documents;
- inspected the real hosted Phase 2C run #14 and its job logs;
- diagnosed the observed failures as legacy NSE expiry-date parsing, non-option NIFTY rows being counted as invalid options, and narrow India VIX date parsing;
- applied parser/validation corrections without lowering scientific acceptance thresholds;
- recorded the failures in the developer error/research logs;
- queued corrected-tree Phase 2C run #16 on commit `be5302615522592275db10741d5de377c1ecace3`;
- updated the isolated Phase 2C tester branch with an independent correction review marked **PASS WITH DATA EXECUTION PENDING**.

Current decision: Phase 2 data gate remains OPEN. No Phase 3 prediction testing is permitted yet.

### 2026-10-07 — “Ok proceed” continuation and Phase 2C run #25 checkpoint

User again instructed the research to proceed. The developer continued Phase 2C rather than advancing phases. The corrected data run #25 successfully acquired and validated all eight official NSE NIFTY yearly datasets plus India VIX, global/rates context and the live FII/DII snapshot. The gate stopped on a stale static-workflow validator that checked the legacy Phase 2 workflow instead of the active Phase 2C workflow. This is logged as a CI/governance defect and is being corrected without changing data-quality thresholds. Phase 3 remains blocked.
