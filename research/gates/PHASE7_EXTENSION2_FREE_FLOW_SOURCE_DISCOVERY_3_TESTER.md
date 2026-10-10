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
