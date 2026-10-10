# Extension 2 — Free Daily Flow Source Discovery 3

**Status: PROPOSED — NOT AUTHORIZED FOR LIVE SOURCE REQUESTS.**  
**Research branch roles:** developer on `phase-07-developer`; independent tester on `phase-07-tester`.  
**Preceding state:** Gate A Run 2 accepted the sample schemas but did not close full source feasibility. The prior one-run manifest is spent.  
**Scope:** a finite, strictly bounded investigation of additional free daily FII/FPI/DII sources. No full-history download, feature construction, labels, model fitting, predictive metrics, p-values or final-holdout access.

## 1. Research question

Can we identify at least one non-synthetic, point-in-time-auditable free daily source for both FII/FPI and DII cash-market flow, with a plausible path to at least 752 aligned sessions (minimum training prefix plus 500 test dates), without silently substituting an incompatible source definition?

## 2. Aims and objectives

### Aims
1. Resolve the G14/G15 data bottleneck before implementing features or running prediction experiments.
2. Identify which free source candidates contain observed daily records, which are generated/semi-synthetic, which expose only FPI, and which are too short.
3. Establish enough source provenance, row schema and potential historical coverage to decide whether a later full acquisition proposal is scientifically defensible.
4. Preserve the strict finite phase plan: this source-discovery phase ends after the registered bounded probes and their independent audit.

### Objectives
- Probe exact dated CDSL FPI report files and its archive index.
- Inspect the pinned Hugging Face daily FII/DII candidate using only bounded HTTP byte ranges.
- Inspect one dated static JSON record from the public chirag127 source.
- Probe public SEBI/FPI archive metadata and a small CalcSetu page sample without pulling historical datasets.
- Inspect only GitHub repository metadata/tree sizes for other mirror leads; do not request their raw data files in this step.
- Explicitly reject synthetic/history-seed values and any response that ignores date limits, byte ranges, or row caps.
- Create a machine-readable report with attempted URLs, response status, bytes read, hashes, dates/fields found, source labels, and an explicit status/reason per source.

## 3. Frozen source candidates and request budgets

Each URL below is fixed in code before the workflow runs. A source can be marked `NOT_VERIFIED`, `REJECTED_SCOPE`, `REJECTED_SYNTHETIC`, `REJECTED_SCHEMA`, `SCHEMA_SAMPLE_PASS`, or `COVERAGE_LEAD_ONLY`. None of those statuses authorizes model work.

| ID | Exact probe | Maximum requests | Response cap | Allowed use |
|---|---|---:|---:|---|
| CDSL-1 | `https://www.cdslindia.com/Publications/ForeignPortInvestor.html` | 1 | 128 KiB | Parse dated report links/visible archive span only |
| CDSL-2 | `https://www.cdslindia.com/downloads/Publications/Latest/Latest_30092024.xls` | 1 | 384 KiB | One single-day historical FPI report; validate date/schema only |
| CDSL-3 | `https://www.cdslindia.com/downloads/Publications/Latest/Latest_09102024.xls` | 1 | 384 KiB | One single-day historical FPI report; validate date/schema only |
| CDSL-4 | `https://www.cdslindia.com/Publications/FIITrends.aspx` | 1 | 64 KiB | Archive-form/page metadata; no form submission, session workaround or broad date query |
| HF-1 | `https://huggingface.co/api/datasets/johnwick3690/stocks/revision/f90f7acad633ba5a803f25cf431fb5f13ce3d162` | 1 | 128 KiB | File path, size, revision metadata only |
| HF-2 | HEAD + ranges `0-8191` and `L-8192` through `L-1` on `https://huggingface.co/datasets/johnwick3690/stocks/resolve/f90f7acad633ba5a803f25cf431fb5f13ce3d162/nifty%20historical%20data/fii%20dii%20data/fii_dii_2024_to_today.csv` | 3 | 8 KiB per range; HEAD has no body | Inspect CSV header and small head/tail samples only; maximum 16 KiB of CSV bytes total |
| CHIRAG-1 | `https://api.github.com/repos/chirag127/fii-dii-activity-api/commits/main`, then `https://raw.githubusercontent.com/chirag127/fii-dii-activity-api/{resolved_commit_sha}/data/2026-10-01.json` | 2 | 32 KiB total, 8 KiB file body | Single dated JSON row/schema/source probe |
| SEBI-1 | `https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html` | 1 | 128 KiB | Archive link/date metadata only; do not download monthly transaction files |
| NSE-1 | `https://www.nseindia.com/reports/fii-dii/` | 1 | 128 KiB | Visible fields/CSV link metadata only; do not submit date-range queries |
| CALCSETU-1 | `https://calcsetu.com/Utility/Diifii/` | 1 | 64 KiB | At most 20 visible recent table rows, page metadata only; no pagination/range requests |
| GH-META-1 | GitHub Contents API directory metadata-only calls to `https://api.github.com/repos/marketcalls/fii-dii-data/contents/data` and `https://api.github.com/repos/r7sh7/fii-dii-data/contents/data` | 2 | 64 KiB per response | Directory listing provides per-file sizes/SHAs; never call a file-specific `/contents/data/history.json` endpoint because it can return file content |

**Global limits:** maximum 15 initial probe requests, plus at most 3 one-hop redirects for the three HF HEAD/range requests (18 HTTP request/response exchanges maximum in total), and maximum 2 MiB (2,097,152 bytes) read across all response bodies, including redirect/error/partial bodies. The sum of the declared maximum source body budgets is 1,584 KiB, leaving 464 KiB headroom under the global byte cap. A shared byte/request budget must be enforced across the whole run; any unregistered URL/host, excess redirect, exceeded request count or exhausted global byte budget stops all subsequent requests. The HF dataset-metadata request must return 200 directly; no redirect is followed for metadata, CDSL, NSE, SEBI, CalcSetu or GitHub metadata requests. Only the HEAD plus two HF range requests may use one allowlisted redirect each.

For Hugging Face, the immutable metadata URL is `https://huggingface.co/api/datasets/johnwick3690/stocks/revision/f90f7acad633ba5a803f25cf431fb5f13ce3d162`; file requests use the exact pinned-commit `resolve` URL for the encoded CSV path. HEAD plus two byte-range requests are allowed. Follow at most one redirect per request, and only through the frozen redirect-host allowlist: `huggingface.co`, `www.huggingface.co`, `hf.co`, `cdn-lfs.huggingface.co`, `cas-bridge.xethub.hf.co`, `cas-server.xethub.hf.co`, and `us.aws.cdn.hf.co`. If an additional host is returned, record it and mark the source NOT_VERIFIED; do not follow or broaden the allowlist. No HF token, cookies, or authorization headers are forwarded to a redirected host. For other sources, redirects must remain on the corresponding source host (CDSL, NSE, SEBI, CalcSetu, GitHub API/raw) and any cross-host redirect is rejected.

**Range rule (strict):** the HF byte-range requests must return HTTP 206 with an exact `Content-Range` matching the requested inclusive start/end and a consistent total length. HTTP 200 is always rejected for a range request, even if it includes `Content-Range`; read at most 8 KiB plus one byte for overflow detection. Any missing/malformed/mismatched Content-Range is rejected. The sampler must never read more than the defined per-request cap plus one byte for overflow detection.

No other source, URL, date, time range, path, or endpoint may be added after results are seen. New sources must enter a separately versioned proposal and tester gate.

## 4. What the probes must establish

### CDSL daily FPI files
- Report date is exactly the date implied by the filename and report content.
- Parse the report's equity stock-exchange row and relevant buy, sell and net investment fields where available; do not mix equity with debt, primary/others, derivatives or total market flows.
- Mark this as FPI-only. It cannot supply DII.
- Preserve the disclosure that CDSL describes confirmed data as custodian-reported trades on and up to prior trading days. Record report date, source URL and vintage limitation.
- The archive index may show a historical range, but two daily samples do not demonstrate 500 sessions. Coverage remains `COVERAGE_LEAD_ONLY` until a separately authorized archive-coverage stage.

### Hugging Face CSV
- Pinned repository commit and exact filepath are mandatory.
- HEAD must provide a credible content length. The sampler may read only the first 8 KiB and last 8 KiB via Range; it must require status 206 and validate Content-Range against the requested interval. If HEAD omits/invalidates Content-Length or reports `L <= 8192`, make no tail-range request and mark the CSV source NOT_VERIFIED/COVERAGE_LEAD_ONLY.
- Report header, a maximum of 10 parsed rows from the head and 10 rows from the tail, date field candidates, FII/DII buy/sell field candidates, numeric validity and duplicate dates within the sampled rows.
- If the file is too small to satisfy the restricted two-range plan, Range is unsupported, content-length is missing, or the response would exceed caps, mark the probe unverified/rejected; do not fall back to downloading the file.
- The 503-line public diff is only a discovery clue, not proof of 500 unique dated observations. No full-file row count or model-usable coverage conclusion may be asserted from a partial sample.

### chirag127 dated JSON
- Use one pinned commit and one fixed date path only.
- Validate the record's date and field types. Inspect `source`/provenance fields; any `placeholder`, generated, fallback-without-source, or otherwise untraceable values are `REJECTED_SYNTHETIC` or `REJECTED_PROVENANCE`.
- One day's record is schema evidence only, not evidence of enough historical coverage.

### Other pages and repositories
- SEBI is FPI transaction-level, not the same aggregate series as G14/G15; only inspect month/date link availability, no monthly file download.
- NSE page: inspect current field names and CSV links only. Do not assume its date-filter API works; Run 2 demonstrated that a dated query may return out-of-window current rows.
- CalcSetu: limit to 20 visible rows. The visible history must not be assumed to cover 752 testable sessions.
- Other GitHub mirrors: tree/README metadata only. Do not fetch `data/history.json` or similar raw history paths during this phase.

## 5. Synthetic and provenance exclusion rules

- The code review of `MrChartist/fii-dii-data/scripts/seed_history.js` says it generates “realistic per-day” values from monthly/yearly aggregate totals. Records created by `historical-seed` are synthetic estimates, not observed daily flows, and must never enter model inputs.
- A data file that mixes `historical-seed`, `fetch-pipeline`, `live-fetch`, `placeholder`, or similar tags cannot be accepted wholesale. Each source label needs a defensible, explicit rule and separate source coverage. Missing provenance is a rejection, not an invitation to infer that data are real.
- Do not blend NSE-exclusive FII/FPI/DII values, combined NSE/BSE/MSEI aggregates, CDSL FPI-only values, or SEBI transaction-level values without a versioned formula/source amendment and independent review.
- Preserve source-local publication date, retrieval timestamp, report date, and whether records are provisional/revised. The target session must only use features that satisfy the registered strict prior-session rule.

## 6. Offline regression requirements

Tests must include:
1. An HF Range response with status 206 and exact Content-Range passes; status 200 or mismatched Content-Range is rejected.
2. A range response exceeding 8 KiB fails after bounded read; no unbounded `.read()` call is possible.
3. HF head/tail probe never downloads the complete file; total sampled bytes are at most 16 KiB.
4. CDSL XLS parsing recognizes the report date and separates equity stock-exchange rows from debt/primary rows; a wrong report date fails.
5. A CDSL or other FPI-only record cannot be marked as a complete G14+G15 source.
6. A source labelled `historical-seed`, `placeholder`, or generated fails provenance acceptance.
7. The chirag JSON date must match `2026-10-01`; a mismatched date/unknown source fails.
8. Any HTTP redirect outside the pinned host allowlist fails.
9. Aggregate requests stay at or below 15; total bytes stay below 2 MiB; source rows are capped (maximum 20 visible records/table and 10 parsed records per HF edge).
10. The CDSL archive-form response may return 403; the report records `NOT_VERIFIED` without trying a bypass.
11. A failed/ignored NSE date-range response remains rejected; no broader retry is issued.
12. No sampler function calls the model runner, makes target labels, or writes predictor tables.
13. A valid HF HEAD length `L > 8192` defines tail Range `L-8192` through `L-1`; missing/invalid length or `L <= 8192` must skip tail fetch and fail closed.
14. GitHub metadata tests use only the `contents/data` directory endpoints and validate that the parser reads file `size`/`sha` metadata, not any `content` payload. No request may use a file-specific Contents API endpoint.
15. Redirect tests verify exactly one allowlisted HF hop at most, reject an unregistered host or two-hop chain, and verify no authorization/cookie headers are sent to redirected hosts.

The source-specific runner must be import-safe. The offline workflow must run tests only and must not call any source retrieval module. The live workflow must remain a separate, fail-closed job.

## 7. Statistical/data decisions after sampling

The result should answer only these questions:
- Does the HF CSV have a credible schema and date-range lead to inspect further?
- Does CDSL expose parseable historical FPI reports and an archive path that could plausibly extend far enough?
- Is the static JSON source verifiably observed or contaminated with placeholders/synthetic fallback?
- Which sources are official, third-party, FPI-only, combined FII/FPI/DII, or transaction-level?
- What follow-up source acquisition, if any, is scientifically justified?

No prediction metrics, p-values, model fits, features/labels or trading results may be generated. If no source is sufficient, prepare one finite further free-source proposal rather than jumping to paid feeds. If a source shows no credible path to enough dates, record the reason and move on after the bounded inventory is complete.

## 8. Gate sequence and stop rules

1. **Spec gate:** independent tester reviews this exact proposal before coding.
2. **Code gate:** developer implements the sampler/tests and two workflows; offline regression passes; independent tester reviews exact blob IDs and bounds.
3. **One-run authorization gate:** hash-bound manifest permits exactly one bounded source-discovery run.
4. **Artifact gate:** tester audits hashes, source URLs, byte counts, Range behavior, sample fields, date/source labels and synthetic-provenance rules.
5. **Stop:** this source-discovery phase ends after the registered probes and artifact audit. No model-fitting or full-history acquisition is authorized by this phase; a subsequent full-acquisition proposal must specify coverage targets and obtain a new independent gate.

**Current status:** proposal only. No request in this spec has been issued. The previous Gate A sample manifest is spent and must not be reused.

**Developer → Tester:** Review the finite request inventory, CDSL/HF source semantics, range safeguards, synthetic provenance exclusion, byte caps and test plan. Return PASS or REQUEST CHANGES before implementation.

**Tester → Developer:** Reject any scope that can download the full HF CSV or other history file, follow unregistered redirects, use seed-generated values, or proceed to full history/model fitting. A spec PASS must authorize only implementation and offline tests, not network retrieval.
