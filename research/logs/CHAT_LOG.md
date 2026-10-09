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


## 2026-10-10 — Resume prediction research and incorporate uploaded papers

User requested a research resume and inclusion of the newly attached research PDFs. Developer re-read the latest main README, Phase 7 status, method/protocol constraints, recent Run #994 independent audit, the available-data extension spec/handoff, recent error/research logs and both Phase 7 branch status ledgers before acting.

- Latest accepted project evidence remains Phase 7 Run #994: 100 candidate cells technically audited (3,098 independent checks passed, 0 failed), but all ten method-family predictive-improvement tests are non-significant. No model is promoted.
- The available-data global-feature prediction extension is in regression-passed / tester-review-pending state; hosted empirical prediction remains blocked until the exact protected snapshot is independently approved.
- Reviewed 15 unique user-supplied PDFs. Re-upload duplicates were counted once. New supplement: research/literature/UPLOADED_PDF_REVIEW_2026-10-10.md; registry IDs L037–L051.
- Paper claims are labeled as reported literature, not project experiments. The literature supplement does not change registered methods, split/horizon definitions or authorize option strategy work.
- Developer → Tester: review the supplement, the 15 new CSV records and this disposition independently; flag inaccurate claim/metric attribution, bibliography/column issues or scope violations. Do not authorize empirical execution from a literature-only change.
- Tester → Developer: return concrete corrections and a gate report; preserve the existing hold on the available-data empirical workflow until its own exact-snapshot gate passes.
