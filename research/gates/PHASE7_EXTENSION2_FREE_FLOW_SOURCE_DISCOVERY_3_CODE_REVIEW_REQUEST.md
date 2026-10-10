# Developer → Tester Code-Gate Review Request — Extension 2 Free Flow Source Discovery 3

**Status: READY FOR INDEPENDENT CODE GATE; no live source requests have been made by this implementation.**  
**Reviewer scope:** review exact sampler, offline tests, requirements and both workflows. A PASS may authorize only preparation/validation of a one-run manifest; it does not authorize network requests by itself. A separate manifest is required for one bounded probe.

## Exact reviewed snapshot

**Developer commit:** `918821ba9e74342bb282fe3a86138e8aa8e29ea7`  
**Latest hosted offline test:** [Run 38029034365](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029034365) — **29/29 checks passed**, no live source-request step.

| Protected path | Git blob ID | SHA-256 of file bytes | Bytes |
|---|---|---|---:|
| `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md` | `4e30415632545c04a2875d627afa0191afe3f383` | `9862bbe2cf572efc9e7ebad41074439ecbf7b339d97ae41039c7b7feb3993fd5` | 15,839 |
| `scripts/extension2_free_flow_source_discovery_3.py` | `2df0dd511a1f6a15f1fd82ad4da0ab71891aa778` | `ec88a2d2902455d6d3fa3946c568a636d7908e7d9961d07f9345978231b80c66` | 48,010 |
| `scripts/test_extension2_free_flow_source_discovery_3.py` | `5cda644ed9a28b5855097ba021300dee7cbab0fa` | `ec45663dc7d7a11b882f3e836303f89f4d397d97ec2757597a422e27a2dab78c` | 23,137 |
| `requirements-source-discovery-3.txt` | `921812b1d6da657ee1de2a4b35e7ff8b43cc8ce6` | `809422d070124a35ad899d303051f245fbad1fa8a981481fab8fb56857046d4b` | 12 |
| `.github/workflows/phase-07-free-flow-source-discovery-3-tests.yml` | `634f87014f334d3c4a903269a073c4e5e2786d46` | `b9d191bc0c18386f4d77aadd9ff053291c772c0cf9563f53bc7646b016e7b8a4` | 1,519 |
| `.github/workflows/phase-07-free-flow-source-discovery-3.yml` | `c0a68275c4a6c60d81726fb6ec0bf563bd86dada` | `44ec73a536f5708f8855ecbf0c69390833aa4e998597c619dcc5135b4d114a35` | 10,065 |

The spec received a separate spec-only pass. This is a new review for the implementation and both workflows; the earlier spec-only pass must not be reused as a code gate.

## Scope implemented

The sampler is limited to the finite probes in the current frozen proposal:
- CDSL archive metadata and two exact-date XLS reports. The parser marks CDSL as **FPI-only**, checks the expected report date and equity/stock-exchange row, identifies candidate buy/sell/net labels and extracts bounded same-column numeric values when the row/header alignment permits. Candidate values remain explicitly **not accepted as model features** until grouped-header mapping is independently reconciled.
- Hugging Face metadata at a pinned revision, then one HEAD and two 8 KiB byte-range requests for one exact CSV path. Range requests require HTTP 206, exact Content-Range and exact body length; only registered 8 KiB ranges are allowed; total CSV sample size is capped at 16 KiB and no full-file fallback exists.
- One Chirag dated JSON record resolved against a commit SHA and a fixed date path. The record date and source label are checked; flow-like values must be numeric/finite; known synthetic/placeholder data are rejected. Nested credential-like JSON keys and sensitive query parameters in source URLs are redacted before reporting.
- SEBI, NSE, CalcSetu and two GitHub Contents directory metadata probes. The client allowlist refuses file-specific GitHub contents URLs, and directory responses containing inline file content are rejected.

## Network and data restrictions

- The client has a frozen URL/method allowlist, bounded per-source response body limits, 15 initial requests maximum, three aggregate redirects maximum, 18 HTTP exchanges maximum, and a 2 MiB total response-body budget.
- The HTTP wrapper applies body caps itself, reads at most cap+1 bytes, validates permitted headers before the network call, denies arbitrary Range values, follows at most one redirect per registered HF request, and rejects non-HTTPS or non-allowlisted redirect hosts.
- No cookies/authorization headers are forwarded to redirect targets. Signed-query values are redacted from logged URLs.
- Offline tests use mocked responses and fixtures. **No live source requests were issued while implementing or testing this snapshot.**

## Hosted regression evidence

[Run 38029034365](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029034365) passed **29 offline regressions**, including:
- exact Content-Range and 8 KiB Range values;
- request/byte/redirect budget limits and source-specific response caps;
- fixed URL/method/header allowlist and fail-before-network cases;
- no-auto-redirect for non-HF sources, redirect host/hop caps, and no credential forwarding;
- redaction of signed URLs and nested source JSON secrets;
- CDSL XLS date/source semantics and candidate numeric buy/sell/net values;
- date/provenance/numeric flow validation for one dated JSON record;
- Hugging Face head/tail schema sampling within 16 KiB;
- metadata-only GitHub directory parsing and inline-content refusal;
- static workflow checks that the one-run manifest is spent before the source probe and that the offline workflow never executes the live sampler.

## One-run replay protection

The live workflow runs tests first and validates the exact tester report SHA-256, current-decision/scope lines, six-path allowlist, byte hashes, Git blob IDs, and reviewed-commit ancestry. Before the first data-source request, it verifies the branch head is unchanged, changes the manifest to `SPENT — ONE BOUNDED SOURCE-DISCOVERY RUN CONSUMED`, and only then executes the sampler. A generated `[manifest-consumed]` commit cannot re-enter the live approval job. Manual live dispatch defaults to false; replaying a spent manifest does not authorize another request. The offline workflow has no live sampler step.

## Requested independent review

Independently re-fetch and verify all six paths against these exact blob IDs and byte hashes. Review the implementation and both workflows—not just the passing test output. Check that the source list cannot be expanded at runtime; all byte/request/redirect limits hold; HTTP 200 cannot masquerade as a range response; CDSL FPI-only semantics remain separate from DII; candidate numeric values remain marked unaccepted until mapping is verified; source JSON redaction is recursive; and a consumed manifest cannot authorize a second live run.

Return **PASS** or **REQUEST CHANGES**, citing concrete reasons.

A code-gate PASS may authorize only preparing a fresh exact-hash single-use manifest. **It does not authorize network requests without that manifest passing in the guarded workflow.** Any resulting source artifact then requires an independent artifact audit before any later source expansion, full-history acquisition or model fitting.

**Developer → Tester:** Review the exact six protected files at commit `918821ba9e74342bb282fe3a86138e8aa8e29ea7`; specifically validate CDSL candidate value mapping and one-run consumption-before-fetch.

**Tester → Developer:** Keep source requests disabled pending a current exact-snapshot code PASS and a separate single-use manifest. After the one bounded sample, perform another artifact gate. Full-history acquisition, feature/label building, model fitting, metrics/p-values and final-holdout access are not authorized by this code review.
