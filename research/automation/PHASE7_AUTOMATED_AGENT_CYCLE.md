# Phase 7 automated tester–developer cycle

**Purpose:** remove manual back-and-forth from the Phase 7 NIFTY one-minute composite code gate while preserving the developer/tester split and the existing acquisition approval boundary.

## Components

- [Controller workflow](../../.github/workflows/phase-07-nifty-1m-composite-agent-cycle.yml) runs for relevant controller/developer updates and has a manual `workflow_dispatch` button.
- [Controller agent helper](../../automation/nifty_composite_agent.py) asks an independent review model for structured findings, compiles a durable report, and can propose a constrained source/test patch.
- [Tester-owned offline harness](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/scripts/review_nifty_1m_composite_gate.py) checks exact source hashes, required schema validation, explicit regression cases, sanitized diagnostics, offline tests and key workflow safeguards.
- [Current recovery review issue](https://github.com/vishnuvcr/Naked-option-v1/issues/7) mirrors status for visibility only; it is not a human hand-off or approval queue. The machine-readable tester report/decision on `phase-07-tester` is authoritative.

## Automated cycle

**No human tester turn is expected.** The developer workflow consumes tester JSON, repairs/resubmits on a bounded loop, and automatically invokes the next eligible scoped gate after a pass. A workflow must not stop at “waiting for tester”; it waits only for the automated Actions job to finish and then follows its decision. If a run fails or a scope cannot be granted, the failure and exact machine-readable next step must be logged. Issue comments are notifications, not a required response.

1. Resolve and pin the exact `phase-07-developer` commit.
2. Check out developer and tester code into separate directories in a credential-free offline test job. Compile the pipeline and run the existing offline regression suites.
3. Send a read-only source snapshot plus deterministic test findings to the reviewer job using Hugging Face Inference Providers. It cannot edit the code.
4. Commit the tester report, decision JSON, and bounded-cycle state to **`phase-07-tester` only**; post the report link and exact reviewed commit to Issue #7.
5. On `REQUEST_CHANGES`, and only when the AI review completed successfully and the repair budget remains, ask the developer model to propose a patch. The patch is limited to `scripts/run_nifty_1m_composite_dataset.py` and `scripts/test_nifty_1m_composite_dataset.py`.
6. Apply the patch in an isolated, secret-free checkout. Run compilation, the full offline test suites, request-manifest validator, acquisition-approval self-test, and the tester harness again.
7. Only a patch that clears both test layers and whose original developer head is still unchanged can be committed to **`phase-07-developer`**. The workflow then dispatches a fresh review of the new exact commit.
8. The loop is bounded to five review cycles. Failed patches are not pushed. At the limit, Issue #7 receives an intervention notice and the gate remains closed.

## Non-negotiable scope boundaries

- No model fitting, prediction scoring, strategy/P&L execution, holdout access, or live market-data call is performed by this coordination workflow.
- A tester report is **not** an acquisition approval. The existing one-use acquisition approval remains independent, exact-hash validated and spent; any future acquisition requires a separately prepared and independently reviewed approval.
- The Dhan response schema documents timestamps, OHLC and volume. The developer loop must not remove volume validation merely to make a failing test pass. Diagnose the actual response/schema defect using safe evidence; never infer the historical ValueError root cause from incomplete logs.
- Tester findings and decision summaries are persisted; private reasoning is not copied into the repository.
- If `HF_TOKEN` lacks Hugging Face Inference Providers permission, the chosen model/provider is unavailable, or credits are exhausted, the AI reviewer fails closed and records no AI verdict. The deterministic tester still decides any narrow scope it can independently validate; if it cannot, it writes `REQUEST_CHANGES` with exact findings and the developer loop continues bounded repairs/other eligible tasks without human polling. It must never invent a PASS or silently bypass the tester gate.
- Any PASS is bound to the report's exact developer commit and file hashes. Changes after review require a fresh cycle.

## Manual use

In GitHub Actions, select **Phase 7 NIFTY Composite — Automated Tester Developer Loop**. An optional `developer_sha` is honoured only when it equals the current developer branch tip; otherwise the latest tip is used. Set `reset_cycle` only when deliberately starting a new, separately logged repair cycle.

## Autonomous continuation contract

A passing offline code gate is not a live-data permission. It must, however, automatically submit the next predefined gate (for example, a one-request, non-exporting Dhan schema diagnostic) to the tester branch. The diagnostic workflow may run only when the tester decision is pinned to the exact developer SHA and explicitly sets its narrowly scoped authorization field. Its sanitized output is committed as a developer result, which automatically triggers another tester review. A passing diagnostic may then authorize only the separately specified gap-fill run, with cache-integrity checks and no-option-refetch enforcement. Do not wait for a user to relay any of these branch decisions.
