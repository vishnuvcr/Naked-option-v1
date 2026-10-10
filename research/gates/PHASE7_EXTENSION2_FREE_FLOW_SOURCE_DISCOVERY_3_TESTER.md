# Independent Tester Report — Extension 2 Free Daily Flow Source Discovery 3 (Specification Gate)

**Current decision: PASS WITH SCOPED RESTRICTIONS — specification only.**  
**Reviewed developer commit:** `664b58a541f9dded0e39a0bb6ab23f1f0179ca35`  
**Reviewed frozen spec Git blob:** `52b030e09213cb30c4de6a1633da38e6b2558b1f`  
**Authorization scope:** implement the frozen sampler and offline tests only. **No live source requests are authorized by this decision.**

## 1. Exact files and repository state

- Spec: `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md`
- Developer handoff: `research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_DEVELOPER_SUBMISSION.md`
- Prior source inventory: `research/sources/EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md`
- Current overall Gate A source-coverage status remains open due to the prior independent finding that valid FII/DII history coverage is not yet established.
- The previous Gate A one-run manifest is spent and must never be reused.

The spec blob and developer handoff were re-fetched from the developer branch. The handoff names the exact spec blob and distinguishes the Git blob from the developer commit SHA.

## 2. Why the proposal passes the spec gate

### Bounded request budget is internally consistent

The proposal enumerates 15 initial requests, with at most three one-hop redirects for the Hugging Face HEAD and two Range requests. It therefore states an 18-exchange hard maximum and a shared 2 MiB total response-body budget. Per-source maximum body caps sum to 1,584 KiB, leaving 464 KiB under the global limit. CDSL and page response limits are bounded; HF CSV data is capped at 16 KiB total. The proposal requires the request/byte budget to be enforced globally, not independently per helper.

### Hugging Face range behavior is fail-closed

The dataset revision is pinned to immutable commit `f90f7acad633ba5a803f25cf431fb5f13ce3d162`. The exact CSV path is specified. A sample is accepted only with HTTP 206 and exact matching Content-Range. HTTP 200 is rejected even if it supplies Content-Range; missing, malformed or mismatched ranges fail closed. Tail-range calculation depends on a credible HEAD Content-Length greater than 8 KiB; otherwise the tail request is skipped and the source remains unverified/lead-only. Redirects are limited to the listed hosts and one hop per HF range/HEAD request. Credentials/cookies are not forwarded to redirect targets.

The public Hugging Face commit page identifies the file as `fii_dii_2024_to_today.csv` with a 503-line addition, but that count is only a lead, not proof of unique valid daily dates or provenance. The spec does not assume the source meets the research threshold.

### GitHub metadata inspection avoids re-fetching raw history

The corrected proposal uses GitHub Contents **directory** metadata endpoints for the two mirror repositories and explicitly forbids file-specific `/contents/data/history.json` requests, which can return the whole file in the response. This is an important control given the previously recorded inadvertent retrieval of a raw history file. Directory listing results must be parsed as metadata only; if any body includes an unexpected payload, the probe should be rejected and logged.

### Source semantics are kept separate

- CDSL date-specific reports are FPI-only and cannot fill the DII series by themselves.
- SEBI trade-wise FPI records are transaction-level and not interchangeable with daily aggregate FII/FPI/DII imbalance.
- The NSE dated FII/DII endpoint previously returned current-date rows for an old requested window. The new proposal does not re-test or widen that API query; it only reads the visible page/link metadata.
- `historical-seed` and placeholder/generated records are excluded as synthetic, not accepted as observed daily flows.
- The proposal preserves source/report date, provenance, vintage, request hash and limitations. It does not permit predictor features, labels, fits, metrics or holdout reads.

### Frozen next step is finite

The source inventory is limited to CDSL metadata plus two exact XLS dates and a constrained archive-form request; one HF metadata call and three HEAD/range calls; one single-date chirag JSON; metadata-only SEBI/NSE/CalcSetu pages; and two GitHub directory metadata calls. The plan ends after the artifact audit. If the source candidates remain too short or incompatible, a new separately reviewed scope is required; the developer cannot broaden requests during execution.

## 3. Public reference checks

- CDSL's [FPI archive page](https://www.cdslindia.com/Publications/ForeignPortInvestor.html) has dated daily links including 30 September 2024 and 9 October 2024. Direct XLS viewing in the web reader failed because it did not support the XLS content type; no table values were read from those attempts.
- SEBI's [Trade-wise Equity data of FPI](https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html) lists monthly FPI equity archives dating to 2003 and describes transaction-level fields. This supports treating SEBI as a separate FPI-only transaction source, not as a drop-in replacement for combined daily flow.
- Hugging Face's pinned [dataset commit](https://huggingface.co/datasets/johnwick3690/stocks/commit/f90f7acad633ba5a803f25cf431fb5f13ce3d162) includes the CSV candidate with a 503-line addition. Actual schema, unique date coverage and lineage remain unverified pending separate approval.

**Governance note:** During proposal-link verification, the web reader attempted to open the two fixed CDSL XLS links but could not parse their content type; no values or files were stored in repository research data. These are not accepted source-sample results and cannot be used to pass the subsequent artifact gate. The developer must retain this note in the step log.

## 4. Conditions before any implementation is considered ready

Implementation is permitted only on the developer branch and must create:
1. an import-safe, source-limited sampler whose URL/request/byte counters are shared across the whole process;
2. offline fixtures for all parsers and reject cases, including Range ignored/Content-Range mismatch, unregistered and multi-hop redirects, credentials not forwarded, low/missing Content-Length, file-specific Contents API forbidden, synthetic source labels, wrong CDSL report date and source semantics;
3. separate automatic/manual offline-only and guarded live workflow files. The offline workflow must run tests only and must never import/call source network code;
4. a review handoff with exact byte hashes and Git blob IDs for every source, test and workflow file.

The live source job must remain impossible to trigger until a new exact-snapshot code-gate PASS and a new one-run manifest pass. A code-gate decision will authorize at most implementation / offline testing until the later run gate explicitly authorizes the one bounded probe.

## 5. Explicit restrictions

- **Source requests authorized now: NONE.**
- **Full-history acquisition: NOT AUTHORIZED.**
- **Model fitting: NOT AUTHORIZED.**
- **Features/labels/predictions/metrics/p-values: NOT AUTHORIZED.**
- **Final holdout access: NOT AUTHORIZED.**
- The prior Gate A manifest is SPENT.
- A fresh, separate exact-snapshot code review and one-run approval are required after implementation.
- The sampled artifact needs its own separate independent audit, especially for whether the HF rows are observed daily values, whether CDSL's FPI rows are relevant to the frozen feature definition, and whether the available daily coverage can plausibly reach 752 aligned sessions.

**Tester → Developer:** Implement this fixed proposal and offline tests only. Keep all source-fetch paths disabled/fail-closed, and include the CDSL web-reader limitation in the step log. Submit exact hashes for a new code-gate review.

**Developer → Tester:** Independently inspect every source URL, parser, cap, redirect rule, and test. Do not sign a network-sampling approval until the exact code snapshot passes. The final decision after one approved sample must be based on the artifact, not on README/history claims.


## Spec erratum re-review — redirect rule clarified, decision retained

**Current decision: PASS WITH SCOPED RESTRICTIONS — latest spec blob `4e30415632545c04a2875d627afa0191afe3f383`.**  
This re-review replaces the earlier 52b030… spec hash for all downstream implementation-gate references.

The developer resolved the conflict between “no redirect is followed” and the later host-based redirect sentence. The frozen rule now states that every non-HF-data request rejects redirects without following them. Only the HF HEAD and two Range requests may follow at most one redirect to the exact allowlist. This is a restriction, not an expansion. It closes the last ambiguity in this proposal.

The other reviewed constraints remain unchanged: 15 initial probes; at most three one-hop HF redirects; maximum 18 HTTP exchanges; 2 MiB total response-body cap and 1,584 KiB sum of declared source body budgets; strict HTTP 206 + exact Content-Range; no tail request if HEAD length is missing/invalid or `L <= 8192`; directory-only GitHub Contents metadata; no HF credentials/cookies forwarded; explicit rejection of synthetic/seeded data; no full-file fallback.

**Decision retained:** spec PASS authorizes implementation and offline tests only. There are still no live source requests authorized, and no full history, feature/label generation, model fitting, metrics/p-values or final-holdout access is authorized. A new exact-snapshot code gate and one-run approval are required after implementation.

**Tester → Developer:** Use only spec blob `4e30415632545c04a2875d627afa0191afe3f383`. Implement the fixed request inventory and tests offline; submit the new exact script/test/workflow blobs for review. Do not request any data yet.

**Developer → Tester:** Reject a code implementation that follows any non-HF redirect, exceeds global limits, calls a file-specific GitHub history endpoint, downloads the HF full file, or treats a source claim as coverage evidence.


## Implementation code-gate review — 2026-10-10

**Current decision: REQUEST CHANGES — do not create the one-run approval manifest.**  
**Reviewed developer commit:** `918821ba9e74342bb282fe3a86138e8aa8e29ea7`.  
**Live source requests: NOT AUTHORIZED.** The only evidence reviewed here is the hosted offline suite [Run 38029034365](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029034365), which passed 29 fixture checks and contains no live source step. These code findings were discovered by independent static review; no source probe was run.

### Protected blobs reviewed

| Protected path | Git blob ID |
|---|---|
| `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md` | `4e30415632545c04a2875d627afa0191afe3f383` |
| `scripts/extension2_free_flow_source_discovery_3.py` | `2df0dd511a1f6a15f1fd82ad4da0ab71891aa778` |
| `scripts/test_extension2_free_flow_source_discovery_3.py` | `5cda644ed9a28b5855097ba021300dee7cbab0fa` |
| `requirements-source-discovery-3.txt` | `921812b1d6da657ee1de2a4b35e7ff8b43cc8ce6` |
| `.github/workflows/phase-07-free-flow-source-discovery-3-tests.yml` | `634f87014f334d3c4a903269a073c4e5e2786d46` |
| `.github/workflows/phase-07-free-flow-source-discovery-3.yml` | `c0a68275c4a6c60d81726fb6ec0bf563bd86dada` |

The submitted developer review request includes the byte SHA-256 values; the six Git blob IDs match the reviewed developer tree at the pinned commit. This review does **not** reuse the earlier spec-only PASS as a code-gate PASS.

### Blocking finding 1 — stale specification identity in output artifact

The current sampler sets `report["spec_git_blob"] = "52b030e09213cb30c4de6a1633da38e6b2558b1f"`, but the current approved spec blob is `4e30415632545c04a2875d627afa0191afe3f383`. A future artifact would misstate the exact spec version used, defeating the explicit provenance field.

**Required:** update the reported spec blob to the current exact value and add an offline assertion for it. If the spec changes, the value must be updated only with an approved spec snapshot and a fresh code gate.

### Blocking finding 2 — conflicting dates can be accepted in the single-day JSON probe

`validate_chirag_record` collects all fields among `date`, `trade_date`, `tradeDate`, and `report_date`, but accepts the record if the expected path date appears anywhere in the list. A record with `date=2026-10-01` and `trade_date=2026-10-02` therefore passes despite an internal date conflict.

**Required:** require every recognized, non-empty date field to be parseable and equal the fixed expected date. A malformed or conflicting date must yield `REJECTED_SCHEMA`. Add a fixture with one correct and one conflicting date.

### Blocking finding 3 — sampled CSV numeric validation accepts NaN/Infinity

`parse_csv_edge` currently uses `float(value)` as its numeric test. Python accepts `NaN`, `Inf`, and `Infinity` as float values, so non-finite FII/DII rows can be reported as having no numeric error even though the spec requires numeric validity.

**Required:** add explicit finite-value checking after conversion (e.g. `math.isfinite`) and a regression that includes `nan`, `inf`, and a valid numeric value. Report non-finite cells separately or fail the sampled edge closed.

### Blocking finding 4 — JSON field redaction omits signature-like field names

`redact_sensitive_json` removes keys containing authorization/cookie/token/secret/password/credential/API-key terms, but it does not remove fields named `signature` or `sig`. Those can carry sensitive values even when nested.

**Required:** add `signature`/appropriate `sig` handling to the sensitive-key inventory and test nested signature/signed-token fields. Preserve harmless business fields.

### Blocking finding 5 — dated page links may persist sensitive query values

`inspect_html_page` directly reports `date_links(parser)`, whose returned `href` is the raw URL from page HTML. `safe_url_for_report` is applied to HTTP request/redirect URLs and JSON-record URLs, but not to the dated links array. A link containing signed or credential query parameters could therefore leak those values in the JSON artifact.

**Required:** sanitize every URL before adding it to `dated_links_sample`, and add a fixture proving that dated links retain date/path identity while signature/token/API-key query values are redacted.

### Blocking finding 6 — manifest reviewer commit is not bound to the tree in the tester report

The guarded workflow validates that `reviewed_developer_commit` exists and is an ancestor of the current `HEAD`, but it does not require that commit ID to appear as the reviewed commit in the tester report, nor does it verify each protected path's Git blob at that commit. It does check that the current `HEAD` protected blobs appear in the report, but the manifest could still nominate a different ancestor as the reviewed commit.

**Required:** require the manifest's `reviewed_developer_commit` to match an exact reviewed-commit line in the tester report, and for every protected path validate `git rev-parse reviewed_commit:path` equals the expected protected Git blob. Add offline workflow/guard regression coverage.

### Required resubmission

1. Correct the six findings above on `phase-07-developer`.
2. Add focused offline fixtures for all six cases.
3. Run the offline-only workflow and submit the newest exact commit, all six Git blob IDs and byte SHA-256 values.
4. Request a fresh independent code/workflow gate.

**Current disposition:** REQUEST CHANGES. **No one-run manifest or live source requests are authorized.** Full-history acquisition, features/labels, fitting, metrics/p-values and final-holdout access remain prohibited.

**Tester → Developer:** Correct the stale spec ID, conflicting-date acceptance, non-finite CSV handling, recursive signature redaction, dated-link URL redaction, and reviewed-commit/tree binding. Do not create a source-probe approval manifest.

**Developer → Tester:** Resubmit the exact corrected snapshot with offline tests green. The tester must re-review the code/workflow gate before any new single-use manifest can be created.


## Fresh exact-snapshot independent code gate — 2026-10-10

**Decision: PASS WITH SCOPED RESTRICTIONS — code/workflow gate only.**  
**Reviewed developer commit:** `37ed60f260d8833d37d1964dc01c8317f1dcf6b3`.  
**Live source requests: NOT YET AUTHORIZED.** No single-use approval manifest is authorized by this code-gate decision alone.

### Current protected Git blobs independently re-fetched

| Protected path | Git blob ID |
|---|---|
| `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md` | `4e30415632545c04a2875d627afa0191afe3f383` |
| `scripts/extension2_free_flow_source_discovery_3.py` | `34b9dcb47288d103c236a8fd34603daf66135bc4` |
| `scripts/test_extension2_free_flow_source_discovery_3.py` | `9c2e89ff810d2820d6dacdec36fbaf0a18cf4eec` |
| `requirements-source-discovery-3.txt` | `921812b1d6da657ee1de2a4b35e7ff8b43cc8ce6` |
| `.github/workflows/phase-07-free-flow-source-discovery-3-tests.yml` | `634f87014f334d3c4a903269a073c4e5e2786d46` |
| `.github/workflows/phase-07-free-flow-source-discovery-3.yml` | `e29f66b67bd47f488b00a708988fca708b391732` |

The exact Git blob IDs above match the current developer branch. The live workflow's reviewed-commit guard checks the exact commit line in the tester report, commit ancestry, current HEAD blob IDs and the reviewed-commit tree blob IDs. The live source job is downstream of the offline regression and authorization jobs, and the manifest is marked SPENT before the source script is called.

### Review of the six previous blocking findings

1. **Stale specification identity — PASS.** Report output uses `CURRENT_SPEC_GIT_BLOB` pinned to the current approved spec blob. Regression `test_report_metadata_pins_current_spec_blob` covers this.
2. **Conflicting/malformed dates — PASS.** The JSON probe validates recognized non-empty date fields and rejects invalid/conflicting dates. The offline suite includes conflicting-date and malformed-date cases.
3. **NaN/Infinity flows — PASS.** CSV numeric validation uses finite-value checks, reports `nonfinite_flow_cells`, and returns `REJECTED_NONFINITE_FLOW`; a dedicated fixture tests `nan` and `inf`.
4. **Recursive signature redaction — PASS.** Recursive JSON redaction covers exact and suffix-style signature keys, including nested objects; regression `test_source_json_redaction_is_recursive_and_preserves_nonsecret_data` is present.
5. **Dated-link URL redaction — PASS.** Dated links pass through `safe_url_for_report`; the regression checks signed query values are removed while harmless path/date/query information remains.
6. **Reviewed commit/tree binding — PASS.** The workflow requires the exact reviewed-commit line in the report, validates ancestry, compares each protected file's current and reviewed-commit blob IDs to the manifest, and consumes the manifest before source access. Static regression `test_live_workflow_consumes_manifest_before_any_source_request` is present.

### Hosted offline evidence

[Run 38029797600](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029797600) succeeded on commit `5a8793d7cfe66ad8d68094ff85a0750758f0c5c9` and logged **32/32 offline regressions passed**. The offline workflow installs the pinned parser dependency and invokes the fixture test script only; it has no live source-fetch step. The six protected blobs above are the current reviewed snapshot, so the developer must rerun the offline suite on that exact candidate before any approval manifest is created.

### Strict scope and remaining prerequisites

This code-gate PASS is **not** a data-source feasibility PASS and does not establish 500+ historical FII/DII sessions. The prior bounded artifact's NSE date-filtered API result was rejected as out-of-window; that finding remains valid. Free-source coverage research must continue within separately approved bounded stages.

- **Live source requests: NOT AUTHORIZED by this report alone.**
- **Full-history acquisition: NOT AUTHORIZED.**
- **Feature/label construction and model fitting: NOT AUTHORIZED.**
- **Metrics/p-values and final-holdout access: NOT AUTHORIZED.**

Before any source call, the developer must run the offline tests against the exact reviewed snapshot, calculate and verify byte-level SHA-256 hashes for all six protected files, mirror this report byte-for-byte to the developer branch, and create a separate single-use manifest binding the exact report digest, reviewed commit, Git blob IDs and file hashes. The guarded workflow must validate it and spend it before the first request. The resulting artifact needs another independent tester audit.

**Tester → Developer:** Code/workflow gate PASS for this exact snapshot only. Re-run the offline workflow on the exact candidate, compute all six byte SHA-256 hashes, mirror this report, and submit a separate one-run manifest for review. Do not expand the probe inventory.

**Developer → Tester:** Independently verify the manifest's hashes/scope before source access. After the bounded artifact is uploaded, audit provenance, requested dates, source hashes, parsing/redaction and coverage; do not authorize full-history acquisition or model fitting.
