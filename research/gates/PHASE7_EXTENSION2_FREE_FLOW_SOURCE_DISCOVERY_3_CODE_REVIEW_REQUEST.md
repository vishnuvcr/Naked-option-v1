# Developer → Tester Code-Gate Review Request — Extension 2 Free Flow Source Discovery 3

**Current status: READY FOR INDEPENDENT CODE GATE; no live source requests have been made by this implementation.**  
**Reviewer scope:** review exact sampler, offline tests, requirements, and both workflows. A PASS may authorize only preparation/validation of a one-run manifest; it does not authorize network requests by itself. A separate manifest is required for one bounded probe.

## Exact reviewed snapshot

**Developer commit:** `b3a6c3dcde845923a0dba55a0f350d5e67361a76`  
**Latest hosted offline test:** [Run 38028738968](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38028738968) — **27/27 checks passed**, no live source request step.

| Protected path | Git blob ID | SHA-256 of file bytes | Bytes |
|---|---|---|---:|
| `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md` | `4e30415632545c04a2875d627afa0191afe3f383` | `9862bbe2cf572efc9e7ebad41074439ecbf7b339d97ae41039c7b7feb3993fd5` | 15,839 |
| `scripts/extension2_free_flow_source_discovery_3.py` | `9c095efe425366f445aa63e04cc80bd52255acf2` | `6e18dbe4811f3c547c518125c93ebb584a049d50f64dac9ee727e10315b5aca7` | 44,916 |
| `scripts/test_extension2_free_flow_source_discovery_3.py` | `3b83459661ed08f0108e7e72808fc7a4ef78abc3` | `3f38143fa891a632fae6d07fcadc3fcdcdcedb2dda458abb1b299b0ef0e92d68` | 20,947 |
| `requirements-source-discovery-3.txt` | `921812b1d6da657ee1de2a4b35e7ff8b43cc8ce6` | `809422d070124a35ad899d303051f245fbad1fa8a981481fab8fb56857046d4b` | 12 |
| `.github/workflows/phase-07-free-flow-source-discovery-3-tests.yml` | `634f87014f334d3c4a903269a073c4e5e2786d46` | `b9d191bc0c18386f4d77aadd9ff053291c772c0cf9563f53bc7646b016e7b8a4` | 1,519 |
| `.github/workflows/phase-07-free-flow-source-discovery-3.yml` | `c0a68275c4a6c60d81726fb6ec0bf563bd86dada` | `44ec73a536f5708f8855ecbf0c69390833aa4e998597c619dcc5135b4d114a35` | 10,065 |

The spec was separately passed at the spec gate; current spec Git blob above is the latest reviewed spec. This request is for the code/workflow gate, which has not yet passed.

## Scope implemented

The sampler is designed to make only the finite probes in the current frozen spec:
- CDSL archive metadata plus two exact dated XLS reports; labels CDSL as FPI-only and records date/schema/provenance candidates.
- Hugging Face metadata at a pinned revision, then one HEAD and two 8 KiB byte-range requests for the exact CSV path. Range requests require HTTP 206, exact Content-Range and exact body length; response rows/bytes are bounded and no full-file fallback exists.
- One Chirag dated JSON record resolved against a commit SHA and an exact date path; record must have a known source label, a date matching the path, no synthetic/placeholder signals, and any flow-like fields must be numeric and finite.
- Metadata/page-only SEBI, NSE, CalcSetu and two GitHub Contents directory-listing probes; file-specific `/contents/data/history.json` is rejected by the URL allowlist, and any inline content property in a directory-listing payload fails closed.
- One shared request/redirect/byte budget and per-source body limits. The HTTP wrapper enforces the fixed URL/method inventory, permitted headers, exact 8 KiB range shapes, allowed redirect hosts, one HF redirect per request, HTTPS-only redirect targets, no forwarded credentials/cookies, and redaction of signed HF redirect query strings from the report.

The output report is written only when the sampler is executed directly; the offline suite imports the sampler and uses mock responses/fixtures. **No live source requests were issued while implementing or testing this snapshot.**

## Hosted test evidence

[Run 38028738968](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38028738968) passed **27 offline regressions**:
- strict Content-Range and exact 8 KiB range bounds;
- unregistered URL/method/header refusals before network;
- per-source byte caps and global request/byte budgets;
- redirect allowlist, hop cap, preserved Range header, and no credential/cookie forwarding;
- signed redirect URL redaction;
- CDSL XLS schema/date/equity-row fixture and compact archive date link parsing;
- Chirag pinned path/date/provenance and numeric/finite flow-field checks;
- HF head/tail range sampling capped at 16 KiB;
- GitHub directory metadata-only parsing with inline content rejection;
- static workflow check that the one-run manifest is spent before the source-probe step and the offline workflow does not call the live sampler.

The offline workflow has only test and pinned-dependency-install steps. The live workflow is separate and guarded. The live workflow path was added to the offline workflow's change triggers so changes to the gate itself cause offline regression to run.

## One-run replay protection

The live workflow:
1. Runs the offline tests first.
2. Validates the exact tester report SHA-256, required current-decision and scope lines, protected-path allowlist, file-byte SHA-256 values, Git blob IDs quoted in the tester report, and reviewed-commit ancestry.
3. Before the first source request, checks the branch is still at the run's commit and changes the manifest to `SPENT — ONE BOUNDED SOURCE-DISCOVERY RUN CONSUMED`.
4. Only then runs the frozen sampler and uploads the JSON report.
5. Excludes the generated `[manifest-consumed]` commit from re-entering the live authorization job. Replays of the same manifest fail because its decision is spent.

The offline workflow is read-only and has no network-fetch step. Manual live dispatch defaults to false and still requires exact manifest validation.

## Required tester checks

Independently re-fetch the six paths and verify the blob IDs and byte hashes above; inspect all code and workflows rather than relying on this summary. In particular, verify that:
- the source list is identical to the frozen spec and cannot be expanded at runtime;
- byte/request budgets are enforced by the shared client, including redirects and errors;
- no Range request can download the full Hugging Face file or silently accept HTTP 200;
- the FPI-only versus FII/FPI/DII semantics remain separate, and generated/synthetic records cannot be accepted as observed daily records;
- a previously consumed manifest cannot authorize a second run;
- all current test results correspond to this exact snapshot.

Return **PASS** or **REQUEST CHANGES** with concrete reasons.

A code-gate PASS may authorize only creation of a new exact-hash, single-use approval manifest. It does **not** authorize source requests without that manifest passing in the guarded workflow. The artifact produced by any subsequent one-run sample requires a separate independent artifact gate.

**Developer → Tester:** Review these exact six protected Git blobs and file hashes. Do not authorize live source requests on a code-gate PASS alone; confirm that only a new single-use manifest can enable the one bounded probe.

**Tester → Developer:** Keep source requests, full-history acquisition, features/labels, model fitting, metrics/p-values and final-holdout access disabled until the separate one-run manifest is valid. After the sample, independently audit the immutable artifact before deciding the next gate.
