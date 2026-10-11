# Project Research Instructions

These are the repository-level operating instructions for the Naked-option-v1 research. The main README is the public status index.

## Autonomous developer–tester conversation — mandatory

**The tester is not a person. It is the independent automated reviewer maintained on `phase-07-tester`. Never ask the user to contact, wait for, or manually reply on behalf of the tester.** The developer and tester must communicate through versioned files and GitHub Actions, not through human messages.

1. The developer submits a precise, immutable snapshot: exact commit SHA, changed-file hashes, purpose, requested gate scope, test results, risks, and proposed next action.
2. The workflow automatically checks out the developer snapshot and the tester branch into separate, credential-isolated locations. The tester independently reruns the tests and audits logic, formulas/signs, schemas, row joins, privacy, authorization boundaries, and the exact workflow.
3. The tester writes its machine-readable decision and findings **only to `phase-07-tester`**. The exact reviewed SHA, verdict, blockers, approved scope, and next action must be explicit. A report for a different SHA is stale and cannot authorize anything.
4. The developer workflow automatically reads the tester output. For `REQUEST_CHANGES`, it repairs the reported defects, reruns offline tests, submits a new snapshot, and invokes the tester again. For a pass, it automatically starts the next predefined gate when that gate's independent scope conditions are met; it must not stop after merely reporting a pass.
5. Continue the branch-to-branch exchange autonomously through the predefined phases, with the documented repair/retry bound. The current Issue #7 comments are a status mirror, **not a human approval queue**. Do not ask the user to run a workflow when a permitted Actions trigger/dispatch can do it.
6. If the optional AI reviewer is unavailable, record that accurately and use deterministic checks only for the narrow scopes those checks can fully validate. Never infer an AI pass. Do not let an AI outage alone require the user to act; proceed with a safe deterministic gate if it is sufficient, otherwise issue a machine-readable `REQUEST_CHANGES`/blocked decision and continue any independent work.
7. A gate may fail closed for an actual serious blocker: absent required credentials/permissions, a corrupted or unverifiable cache, ambiguous authorization, exhausted predeclared budgets, a security/privacy issue, or repeated failures after the documented bounded retries. Record the blocker and machine-to-machine next action. Never fabricate an output or quietly weaken a gate.
8. Branch roles are immutable: developer changes implementation on `phase-07-developer`; tester changes review harness/reports/decisions on `phase-07-tester`. The roles may coordinate through Actions, exact hashes and JSON reports but must not edit one another's owned artifacts. No source-data response bodies, secrets, or private reasoning are written into research logs; record only action summaries, sanitized findings and reproducible results.
9. Every pass, failure, retry, stale snapshot, skipped stage, provider outage and terminal decision is recorded in `research/STATUS.md`, `research/ERROR_LOG.md`, `research/logs/CHAT_LOG.md`, the relevant gate report and the main README. Keep these entries short, factual, and linked.
10. Live data, prediction fitting, holdout scoring and strategy/P&L testing are distinct scopes. A tester pass authorizes only the explicitly named scope in its machine-readable decision. A one-request schema diagnostic never authorizes a bulk download; a data-recovery gate never authorizes modelling.

## General research rules

- Keep research finite and phase-based; stop only at a supported conclusion or the predeclared end of the phase plan.
- Main README is the public status index and must stay synchronized with the gate reports.
- Every phase gets its own branch. Developer and tester environments remain isolated by role.
- No phase advances before the exact-snapshot tester report for that gate is available and its scope conditions pass.
- Every error is logged with observed symptom, root cause when established, fix, and verification. Do not guess an unverified root cause.
- Every result, including null, partial and failed outcomes, is recorded.
- Prefer official/free sources before paid sources. Search alternatives before declaring data unavailable.
- Cache data and reuse immutable snapshots rather than re-downloading blindly. If recovering a partial dataset, preserve valid acquired data and request only the gaps; if source cache is required, prove it is present and valid before making live requests.
- Use Python/Rust and GitHub Actions. Every phase workflow should support automatic execution and retain a manual run button as a fallback.
- In market research include relevant global/NSE/BSE inefficiencies, option data, DII/FII flows, regime/sentiment, volatility, benchmark indices, corporate actions and news as applicable.
- Include realistic Paytm Money transaction-cost, slippage and brokerage assumptions after verifying historical applicability before any strategy/P&L research.
- End with a structured manuscript containing tables, figures, appendices and supplements.
- Do not store or disclose private chain-of-thought. Store only concise decision summaries and test evidence.
