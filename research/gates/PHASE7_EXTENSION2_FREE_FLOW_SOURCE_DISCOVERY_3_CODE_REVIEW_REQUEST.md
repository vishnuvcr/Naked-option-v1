# Developer → Tester Code-Gate Review Request — Extension 2 Free Flow Source Discovery 3

**Status: RESUBMITTED FOR INDEPENDENT REVIEW. No source-probe approval manifest exists; no live source requests are authorized.**  
**Review scope:** code/workflow gate only. A PASS can permit creation of a fresh single-use manifest, but does not itself permit network access.

## Exact current snapshot

**Reviewed developer commit candidate:** `37ed60f260d8833d37d1964dc01c8317f1dcf6b3`  
**Hosted offline test evidence:** [Run 38029797600](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029797600) — all **32 Extension 2 source-discovery 3 offline regressions passed**. This workflow contains no live source-fetch step.

| Protected path | Current Git blob ID | Bytes |
|---|---|---:|
| `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md` | `4e30415632545c04a2875d627afa0191afe3f383` | 15,827 |
| `scripts/extension2_free_flow_source_discovery_3.py` | `34b9dcb47288d103c236a8fd34603daf66135bc4` | 49,231 |
| `scripts/test_extension2_free_flow_source_discovery_3.py` | `9c2e89ff810d2820d6dacdec36fbaf0a18cf4eec` | 25,754 |
| `requirements-source-discovery-3.txt` | `921812b1d6da657ee1de2a4b35e7ff8b43cc8ce6` | 12 |
| `.github/workflows/phase-07-free-flow-source-discovery-3-tests.yml` | `634f87014f334d3c4a903269a073c4e5e2786d46` | 1,517 |
| `.github/workflows/phase-07-free-flow-source-discovery-3.yml` | `e29f66b67bd47f488b00a708988fca708b391732` | 10,618 |

These are current branch file blob IDs; they are distinct from the reviewed commit ID. Please independently re-fetch the six files and compute/verify byte-level SHA-256 values before any manifest is created.

## Changes covered by the current code and tests

The prior independent tester returned REQUEST CHANGES on six findings. The current implementation adds the following corrections and offline regressions:

1. **Spec identity:** report metadata pins the current approved spec blob `4e30415632545c04a2875d627afa0191afe3f383`, not the stale ID.
2. **Conflicting JSON dates:** every recognized non-empty date field is parsed and must agree with the fixed expected date; malformed or conflicting fields reject the record.
3. **Non-finite CSV flows:** NaN/Infinity are identified separately and fail the sampled edge closed.
4. **Recursive signature redaction:** nested `signature`/`sig` and suffix-style names are redacted without deleting harmless data.
5. **Dated link URL redaction:** every reported dated link sanitizes sensitive query parameters while preserving non-sensitive date/path information.
6. **Reviewed commit/tree binding:** the live workflow requires an exact reviewed-commit line in the tester report, checks commit ancestry, and verifies each approved path's blob at the reviewed commit and current HEAD.
7. **Live-workflow manifest ordering:** an offline regression checks that the single-use manifest is consumed before the first source request.

The current hosted test log explicitly reports all 32 tests passing, including the regressions for current spec identity, non-finite flow values, dated-link redaction, recursive JSON redaction, and manifest-before-source ordering.

## Bounded discovery scope

The inventory remains fixed and finite: two single-day CDSL FPI XLS probes and bounded page metadata; pinned Hugging Face metadata with exact 8 KiB head/tail ranges; one date- and commit-pinned public JSON record; SEBI/NSE/CalcSetu pages; and GitHub directory metadata only. The client enforces its frozen URL/method/header inventory, source-specific caps, 15 initial request maximum, at most three aggregate redirects, 18 exchanges, 2 MiB total read budget, and one allowlisted HF redirect per eligible request. No full-file fallback or source-list expansion is permitted.

## Requested independent review

Please independently:
- re-fetch the exact six protected blobs above and calculate byte hashes;
- review each of the six prior findings against implementation and regression tests;
- trace the live workflow from offline tests through exact report/manifest checks to manifest consumption and first source request;
- confirm there is no alternative trigger or path that permits network requests without a fresh exact-snapshot tester approval;
- return PASS or REQUEST CHANGES with specific findings.

**A PASS must be limited to the current code/workflow gate.** It does not authorize live requests by itself. After PASS, a separate single-use manifest must pin the tester report and every protected file's byte SHA-256 and Git blob ID. A successful bounded run still requires a separate artifact audit.

**Developer → Tester:** Review the exact current six-blob snapshot at candidate commit `37ed60f260d8833d37d1964dc01c8317f1dcf6b3`; do not rely on the earlier decision for commit `1706a17...`.

**Tester → Developer:** No live requests until the current exact-snapshot code gate passes and a fresh single-use manifest validates. Full-history acquisition, feature/label construction, model fitting, metrics/p-values and final-holdout access remain prohibited.
