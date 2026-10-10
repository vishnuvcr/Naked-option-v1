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


### 2026-10-07 — Family D run #19 live verification checkpoint

Developer re-read the active Phase 5 status and logs before taking the next action. Hosted run #19 (37611880308), job 112760881845, remains `in_progress`.

- Steps through Family D regression tests are complete and successful.
- The full D01-D15 empirical suite remains the active step.
- Result-schema validation and immutable artifact upload have not started.
- No Family D metric is accepted.
- Phase 6 remains blocked pending the immutable artifact and independent tester audit.

This is a monitoring checkpoint only; no scientific conclusion or promotion was made.


### 2026-10-07 — Family D run #19 continuation after dual-branch gate check

Developer re-checked the developer-side frozen protocol/status and the independent tester-side Phase 5 protocol records before proceeding. The tester records continue to require an immutable artifact and independent audit before any Family D promotion.

Live hosted state remains unchanged:
- run #19 (37611880308) is `in_progress`;
- job 112760881845 is executing the D01-D15 empirical suite;
- regression tests passed;
- result-schema validation and artifact upload remain pending;
- no Family D metric is accepted.

No scientific or protocol change was made during this checkpoint.

## 2026-10-08 — User continuation: Phase 6 fresh run and tester pre-result audit
- User said "Ok proceed" and provided a screenshot confirming Research Protocol Check run #575 is active on `phase-06-developer`.
- Developer verified the live run by GitHub API: run `37678088131`, regression/protocol/detection jobs succeeded and the empirical job was active.
- Before accepting any result, the developer/tester review inspected the full Phase 6 code and found a second, residual `decision_times.iloc[rows[0]]` use in the later global-I03 block.
- Tester submitted REQUEST CHANGES. The current run is classified as non-evidence, and a detached correction is being prepared for independent tester approval before the developer branch advances.
- A GitHub live-log retrieval attempt returned BlobNotFound; no scientific inference was drawn from missing logs.

## 2026-10-08 — Tester approval of Phase 6 residual cutoff correction
- Independent tester reviewed corrected detached commit `e27b6358901dc60bc90bad295f46c9493ab63d1e`.
- Tester verified removal of the residual `decision_times.iloc` defect, valid indentation, complete cutoff regression coverage, and preservation of frozen scientific definitions.
- Tester gate `research/gates/PHASE6_RUN25_RESIDUAL_CUTOFF_APPROVAL_TESTER.md` = PASS for fresh empirical execution only.
- Developer may now archive the approval on `phase-06-developer` and advance the branch; run #575 remains non-evidence.

## 2026-10-08 — Phase 6 run 578 regression correction cycle
- User said "Ok proceed" and the developer/tester gate was advanced from the tester-approved cutoff fix.
- Fresh run #578 (`37680279189`) passed protocol and acquisition but failed the Phase 6 regression suite before empirical execution.
- Tester independently checked the failing assertion and identified a pure arithmetic error in the regression fixture: 13:15 minus 120 minutes is 11:15.
- Tester issued REQUEST CHANGES at `research/gates/PHASE6_RUN26_REGRESSION_TESTER.md`.
- Run #578 is non-evidence and no scientific metric is accepted. A detached correction is being prepared for independent approval before the next hosted run.

## 2026-10-08 — Tester approval of Phase 6 run 578 regression correction
- Independent tester reviewed the detached arithmetic correction `1a956f930b11850fb238ea3352565b36a7337395`.
- The incorrect 11:00 expectation was corrected to 11:15; production logic was unchanged.
- Tester gate `research/gates/PHASE6_RUN26_REGRESSION_APPROVAL_TESTER.md` = PASS for fresh execution only.
- Developer may archive this gate on `phase-06-developer` and trigger a fresh hosted run. Run #578 remains non-evidence.

## 2026-10-08 — User continuation: Phase 6 Run #581 completed
- User said "Ok proceed". Developer rechecked the live hosted run and confirmed Run #581 completed successfully through artifact upload.
- Artifact `phase6-novel-results` ID `11513410209`, SHA-256 `2065f7d8025b87f67de1a9f04908ec2fc015a6bda98c5a8162ddad3b01961c24` was retrieved for independent audit.
- Tester independently reconciled all 200 registered method/horizon cells: 140 executed and 60 blocked-data; no missing cells or unexpected statuses.
- Tester found no arithmetic/schema inconsistency in executed cells. Apparent performance elevations are treated as research leads only, not validated strategies.
- Tester gate `research/gates/PHASE6_RUN581_TESTER.md` = PASS WITH SCOPED RESTRICTIONS.
- Developer may archive the gate and proceed to Phase 7 ensemble/regime research; Phase 8 option economics and later robustness/fresh-forward gates remain mandatory.


## 2026-10-09 — User continuation: Phase 7 Run #925 independent audit

- User asked to continue from the Phase 7 long-running artifact checkpoint.
- Developer/tester reconciled Run #852, #924 and #925; all completed and uploaded aggregate/reference artifacts. Run #925 was chosen for a frozen-source independent review rather than pooling results from multiple duplicate runs.
- The first tester audit workflow failed before audit because its pip-cache setting required a missing dependency manifest. That workflow configuration failure was corrected; a second workflow run failed at artifact audit, producing a preserved independent report.
- Corrected tester checks confirmed artifact hashes, source/code hashes, panel identities and source-derived labels/returns/timestamps, but issued REQUEST CHANGES for four protocol/implementation defects: P10 abstention omitted, missing regime features classified as low/low, P05/P06 block diagnostics not abstention-aligned, and unavailable rows treated as zero differences in family bootstrap.
- The gate is recorded at [PHASE7_RUN925_EMPIRICAL_TESTER.md](../gates/PHASE7_RUN925_EMPIRICAL_TESTER.md), with corresponding status, README and error-log updates on the isolated tester branch.
- No metrics or strategy are promoted from Run #925. Phase 8 stays blocked. Next step: developer corrects only the approved defects, adds focused tests, submits the exact commit for independent review, and runs a fresh artifact only after the code gate passes.


## 2026-10-09 — Tester review of Phase 7 correction submission

- Tester independently reviewed the developer correction to Run #925. The P10 abstention mask, finite volatility/trend eligibility, candidate-specific block diagnostics, and NaN-versus-zero family-bootstrap differential handling are implemented and have targeted regression coverage. Hosted run #964 passed the regression workflow.
- Tester then found a separate authorization flaw: a correction-specific PASS is not tied to an exact reviewed source snapshot, so later changes could reuse it.
- Report [PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md](../gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md) = REQUEST CHANGES for exact commit/file-hash binding and negative fail-closed tests.
- Empirical jobs `37935752265` and `37935794939` were started under the stale gate before it was contained. They are strictly non-evidence; results/artifacts must not be accepted.
- Developer may not run another empirical Phase 7 job until the tester approves the snapshot-binding correction. Phase 8 remains blocked.


## 2026-10-09 — Tester workflow isolation and generic artifact audit entry point

- Changed the legacy Run #925 audit trigger to manual-only so unrelated tester-branch pushes cannot repeatedly audit the rejected artifact.
- Added a generic tester-side audit entry point that uses the same frozen audit checks but derives run/commit identity from explicit required inputs.
- The main orchestrator will checkout this tester script by immutable commit SHA; artifact identity and run eligibility are independently checked before it runs. Reports are written to the tester branch, and the orchestration gate fails unless the audit decision passes.
- Developer → Tester: only run on a successful completed developer branch run with both uploaded artifacts; fail closed for missing/expired artifacts or source identity mismatch.
- Tester → Developer: report the exact run/commit, counts and failures; no promotion until all numerical, source, hash, panel and family-inference checks pass.


## 2026-10-09 — Legacy Run #925 audit now requires explicit manual opt-in

The tester workflow's manual button now exposes boolean input `run_legacy_run925_audit`, default false. The legacy pinned Run #925 audit runs only when the user deliberately selects that opt-in. All normal tester branch pushes and ordinary manual protocol-validation runs skip the historical audit. Approved fresh-run audits are handled separately by the main-branch workflow, which pins the generic tester script from commit 50334eb728a85ae8ca88f9ded5246b867c9cb56f and publishes each exact-run report to this isolated tester branch.

This workflow-only safety change does not alter the frozen metric calculations or any empirical data.


## Run #37957677656 independent empirical artifact audit

- Automatically audited the completed developer run and preserved the decision, checks and artifacts on the isolated tester branch.
- Tester to Developer: resolve discrepancies without changing the frozen method; resubmit through the same gate.
- Developer to Tester: Phase 8 remains blocked unless this empirical audit passes and the remaining source/economic gates are approved.

## 2026-10-10 — Proceed: empirical audit complete

- Tester downloaded and reconciled the exact Run #994 artifacts; 3,098 checks passed, none failed.
- Decision: PASS WITH SCOPED RESTRICTIONS; this is technical/data integrity approval, not a strategy recommendation.
- All ten family-level bootstrap p-values are >.05; no statistically significant family edge.
- Static review of developer P10 correction commit 39e964d: PASS for future runs only, with the current Run #994 remaining immutable and unchanged.
- Tester → Developer: schedule the next empirical run only through the pre-authorized branch gate, use the reviewed correction commit, and retain all cost/data gates.
- Developer → Tester: audit the next exact-run artifacts and do not promote a candidate without significant pre-registered evidence and realistic after-cost option P&L.


## 2026-10-10 — Phase 7 tester review after hosted Run #37

The hosted Actions API was queried directly. Run #37 (37990522933; developer commit 18773e828f19c0ff2e9fc1af437db6b8ef181739) completed successfully in the regression job: 11 available-global predictor checks and 11 result/panel validator checks passed. The authorization job executed in the intended fail-closed state because no approval JSON/report mirror exists, and the empirical job was skipped. A compare of this run commit to current developer head 14656183f9977c94a178996943e027d09d4a483d shows only status/handoff/log document changes, so no protected code path changed after the run.

Independent tester review then found a reproducibility defect in the NIFTY acquisition script: despite workflow cache restoration, the script unconditionally downloads and overwrites history before checking for a valid cache. It also performs network I/O on import and has no acquisition/cache regression tests. Tester report `research/gates/PHASE7_AVAILABLE_GLOBAL_ACQUISITION_GATE_TESTER.md` records REQUEST CHANGES. No predictions or new metrics were generated; empirical execution and Phase 8 remain blocked.

**Tester → Developer:** Implement import-safe, validated cache reuse and no-network/invalid-cache regression coverage; protect the new test in the workflow and resubmit for an exact-snapshot review.

**Developer → Tester:** After correction, independently verify the cache behavior, hashes, and hosted regression run. Do not approve empirical execution if the cached-source rule or any other gate remains unmet.


## 2026-10-10 — Independent Phase 7 follow-up after Run #40

The hosted run [#40](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37992378927) passed 4 NIFTY cache regression checks, all 11 predictor regression checks, and all 11 output-validator checks. Its authorization gate remained fail-closed and the empirical step was skipped. Independent tester review did not authorize predictions because the acquisition code still drops exchange timezone when assigning source dates, the UTC download cutoff may include the current India session before close, same-day cache data are not rejected before the completion cutoff, and cached official-source overlap records are not reconciled against CSV close values. The tester report was extended with those actionable findings.

**Tester → Developer:** Fix timezone, cutoff, cache allowed-session date and overlap consistency; include negative fixtures and trigger the automatic workflow.

**Developer → Tester:** Return a fresh exact-snapshot review only after hosted regression and hash verification; no empirical authorization while any point-in-time issue remains.


## 2026-10-10 — Post-approval operational status

Tester independently reviewed the final exact snapshot and authorized one Phase 7 available-data prediction batch only. Run #43 passed all three test suites (8, 11, and 11 checks respectively). The developer mirrored the report; the attempt to write the accompanying hash-bound approval manifest was blocked by platform safety checks. The empirical job remains skipped and no model metrics have been produced. Do not replace this gate with a manual alternate trigger; request intervention for a permitted authorization path.

**Tester → Developer:** Preserve the exact-snapshot PASS and hashes; do not alter protected code after approval. Use only a permitted authorization mechanism, then submit immutable run artifacts for independent audit.

**Developer → Tester:** Keep Phase 8 blocked until the single approved batch actually runs and its source/data/prediction artifacts pass an independent audit.


## 2026-10-10 — Tester review after user proceeded to Run #44

Run #44 completed successfully and its immutable artifact was downloaded. Tester independently verified provenance hashes, panel structure, label signs, probability bounds, metric recomputation, and all five family bootstrap tests. No integrity or arithmetic discrepancy was found. However, the strongest descriptive Brier improvement (G06 Asia composite, 5-session horizon, +0.001623) had family p=0.7745; all horizon family tests were non-significant and all adjusted p-values were 1.0. No candidate is promoted. The first run reports global cache misses (legacy cache schema/freshness rejected), which is documented. Phase 8 remains blocked; this batch did not test options execution or trading costs.

**Tester → Developer:** Preserve the negative family-level conclusion and artifact hash; keep Phase 8 blocked and do not convert descriptive accuracy into a strategy.

**Developer → Tester:** Any new prediction family requires preregistration and independent review before execution. If strategy research is later authorized, require options data, Paytm Money fees/taxes, spreads, slippage, liquidity and realistic fills.


## 2026-10-10 — Independent tester review of Extension 2 proposal

Tester returned REQUEST CHANGES before data acquisition. The proposal had five blocking ambiguities: option archive format transition (legacy F&O bhavcopy to UDiFF), undefined flow normalization denominator, ambiguous F04/F05 formulas, non-canonical sector index names, and missing deterministic common-grid bootstrap behavior for abstentions. No downloads or fitting occurred. Developer must correct the spec and resubmit.

**Tester → Developer:** Correct formulas and source-format boundaries; no source feasibility or empirical work until the new exact spec passes.

**Developer → Tester:** Re-review the corrected spec and synthetic family-bootstrap fixture; only a PASS can authorize small-sample source feasibility.


## 2026-10-10 — Tester rejected Gate A sampler before live fetch

The independent tester found that the source sampler checked the requested trade date only on the first archive row, which could hide mixed-date records. The developer must validate all rows, record distinct date count, and add negative fixtures for both legacy and UDiFF. No workflow or live download has run.

**Tester → Developer:** Fix row-wise date validation and tests, then resubmit exact blobs.

**Developer → Tester:** Keep Gate A workflow disabled until the corrected sampler is independently approved.


## 2026-10-10 — Tester blocked Gate A sampler due to full-history URL

Fresh exact-snapshot independent review returned REQUEST CHANGES: the Gate A v2 sampler contained a 2020–2025 NSE FII/DII URL, contradicting the limited sample-only authorization. The review also caught a wrong workflow Git-blob pin in the developer handoff. No source requests were made. The developer must bound the API to a short window, add strict body/row caps and tests, correct the blob/commit distinction, then request a new review.

**Tester → Developer:** Fix the request bounds and sample caps; keep the approval manifest absent.

**Developer → Tester:** Re-review the corrected exact source/workflow snapshot; source calls remain disabled until the new PASS.


## 2026-10-10 — Tester exact-snapshot decision after bounded-request corrections

The independent tester passed the corrected sampler/workflow snapshot for **one bounded Gate A source-sampling batch only**. Hosted tests passed: 7 v1 and 15 v2 checks in Run `38026024826`; the legacy workflow's offline-only safety run `38026080844` also passed. The tester report explicitly denies full-history acquisition and model fitting.

A previous legacy workflow did run the v1 source sampler without tester authorization (Run `38025793938`). The artifact is classified NON-ACCEPTED EVIDENCE, and the workflow has been modified to run tests only. The guarded v2 workflow is the only source-fetch path now.

**Tester → Developer:** Mirror the exact current PASS report and create one hash-bound Gate A approval manifest. Let the guarded workflow re-run offline tests before any live fetch; then submit both source reports for a separate tester artifact audit.

**Developer → Tester:** Preserve the prior unauthorized artifact as non-evidence and audit the new bounded run's URLs, hashes, all-row schemas and provenance. No full history or model fit is authorized by this gate.


## 2026-10-10 — Gate A artifact failed independent source validation

The one bounded source workflow completed successfully in all jobs but did not pass the separate artifact audit. The tester found (1) official index CSV dates were `DD-MM-YYYY`, so two index samples were marked FAIL by the code, and (2) the NSE API ignored the July 2024 date range and returned 2026-10-09 records; those records were incorrectly marked JSON_PARSED. FII/DII historical coverage is still only represented by a recent 164-row mirror and a 16-row recent page sample, so 500+ sessions have not been demonstrated.

The artifact is not accepted, and the current approval has been revoked. No full history, feature table, labels or model fit occurred. The next exact snapshot must add numeric date parsing and response-window rejection tests, then receive independent review and a new bounded sample gate.

**Tester → Developer:** Fix both source-validation defects and document broader free FII/DII source discovery. Keep full-history downloads/model fitting blocked.

**Developer → Tester:** Independently review the updated code and new test results. A code PASS authorizes only one new bounded source-feasibility sample, not full acquisition or fitting.


## 2026-10-10 — Tester artifact audit after corrected Gate A run

Tester reviewed Run `38026993369` and accepted the schema evidence but did not close Gate A. Both official sector-index samples now pass the date check; the two cash-equity archives and both F&O archive formats pass their sample schemas. The official NSE date-range API still returns current data for a July 2024 request, and the code correctly marks those rows out-of-window. The available rolling FII/DII mirror has 164 unique sessions, short of the 500-session requirement. The report requests changes for full source feasibility rather than calling the history unavailable.

The one-run authorization is spent. The next action is to propose a separate bounded free-source discovery step including the additional GitHub APIs and historical dashboards. That step requires a fresh tester review before live requests.

**Tester → Developer:** Propose deterministic sample requests and hard source limits for more free FII/DII sources. Do not use the spent manifest or request full history.

**Developer → Tester:** Review that the new scope is sample-only and can prove whether the candidate sources expose real dated daily records; keep model fitting blocked.


## 2026-10-10 — Source Discovery 3 spec gate PASS

Independent tester passed the finite spec for implementation + offline tests only. No live-source requests are authorized yet. The proposal now protects against ignored Range responses, unregistered redirects, over-budget probes, and accidentally retrieving small history files through GitHub's file-specific Contents API. CDSL web-reader attempts returned unsupported XLS content type and are logged as non-accepted activity.

**Tester → Developer:** Implement only the frozen sampler and offline regression suite; keep live workflow fail-closed.

**Developer → Tester:** Submit exact script/test/workflow hashes after hosted offline tests pass; do not create a live approval manifest until the separate code gate passes.


## 2026-10-10 — Discovery 3 code gate REQUEST CHANGES

The code gate was rejected after independent static review found six data-integrity/privacy/governance issues, notwithstanding 29 passing offline fixtures. The full tester findings are in `research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_TESTER.md`. The report has been mirrored to the developer branch. No live source requests have occurred.

**Tester → Developer:** Fix all findings, add offline tests, and submit a fresh exact-snapshot review. Do not create a live-source approval manifest.

**Developer → Tester:** Re-review the corrected code/workflow hashes; source access remains disabled until a fresh code PASS and separate one-run authorization.

## 2026-10-11 — Independent tester pass for NIFTY one-minute composite acquisition

### Reviewed decision
The tester branch reviewed the exact developer commit `98ef6ca039b19f0284981c57fc17b39124284869` and issued **PASS WITH SCOPED RESTRICTIONS — EXACT MANIFEST AND ACQUISITION WORKFLOW ONLY** in [the tester report](research/gates/PHASE7_PPR4_USER_DIRECTED_COMPOSITE_ACQUISITION_TESTER_REVIEW.md). Reviewer rebuilt the request grid from all active root-referenced manifests, not merely relying on the developer validator.

### Results
- 61 non-overlapping 30-day windows; 8,601 unique requests; 61 spot and 8,540 option requests; every declared option selector occurs once per window; no request-grid findings.
- Request list for 2023 was split into reviewable A/B files (987 and 846 entries) after the connector failed to expose the oversized single file. Root manifest links both; a small index remains at the old path.
- CI is green for both split parts, the root manifest, old index and current code/parser/encryption/Greek/attempt-ledger tests. These were offline runs and made no Dhan requests.
- Historical Greeks are either computed from source-based effective inputs or visibly marked as proxies (rule-based expiry, zero-rate/zero-dividend as needed, and IV-unit heuristic). No live option-chain Greeks are backfilled into history.
- Subscribed data will be cached and packaged only as AES-256-GCM ciphertext in the public repository's workflow artifact; local use requires the same `HF_TOKEN` value used to encrypt.

### Current gate state
The tester has approved the exact manifest and guarded workflow only. A one-use approval is the next developer action; it must bind the reviewed Git blob SHA of every protected code, request, policy and workflow file as well as the tester report. The guarded workflow marks approval spent before the first network request, then exports encrypted monthly CSV parts plus a redacted coverage/errors report. If any request or feature family is missing, the report must say PARTIAL and a separate open-source fallback manifest is prepared; unrelated research should continue.

**Developer → Tester:** proceed with the pinned one-use acquisition and return the actual coverage/artifact disposition for independent review.  
**Tester → Developer:** approval is scoped to enumerated acquisition only; do not start modeling until the realized dataset coverage has been reviewed.
