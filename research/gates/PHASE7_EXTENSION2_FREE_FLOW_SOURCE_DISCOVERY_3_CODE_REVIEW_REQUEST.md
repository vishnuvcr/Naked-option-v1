# Developer → Tester Code-Gate Review Request — Extension 2 Free Flow Source Discovery 3

**Current status: REQUESTED — no source-probe approval manifest exists, and no live source requests have been made.**  
**Review scope:** current implementation/code gate only. A PASS can authorize a fresh one-run manifest; it does not by itself permit network access.

## Exact current snapshot

**Reviewed developer commit:** `1706a17d268e2b139fc9dba4504f498acc4f5de0`  
**Latest hosted offline test:** [Run 38029615734](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029615734) — **32/32 offline tests passed**. This workflow has no source-fetch step.

| Protected path | Git blob ID | SHA-256 of file bytes | Bytes |
|---|---|---|---:|
| `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md` | `4e30415632545c04a2875d627afa0191afe3f383` | `9862bbe2cf572efc9e7ebad41074439ecbf7b339d97ae41039c7b7feb3993fd5` | 15,839 |
| `scripts/extension2_free_flow_source_discovery_3.py` | `34b9dcb47288d103c236a8fd34603daf66135bc4` | `590b50cae5334eb98938f2731b3c5d2d527895a9d90447ff71b868a86c3e50d1` | 49,235 |
| `scripts/test_extension2_free_flow_source_discovery_3.py` | `ba901c0d056fa96dd84f201de6382a027c69bac8` | `79145cbdda7ae793f783f68e939084fc5cd40d32ec5b9e8ea35e0925903d2552` | 25,440 |
| `requirements-source-discovery-3.txt` | `921812b1d6da657ee1de2a4b35e7ff8b43cc8ce6` | `809422d070124a35ad899d303051f245fbad1fa8a981481fab8fb56857046d4b` | 12 |
| `.github/workflows/phase-07-free-flow-source-discovery-3-tests.yml` | `634f87014f334d3c4a903269a073c4e5e2786d46` | `b9d191bc0c18386f4d77aadd9ff053291c772c0cf9563f53bc7646b016e7b8a4` | 1,519 |
| `.github/workflows/phase-07-free-flow-source-discovery-3.yml` | `e29f66b67bd47f488b00a708988fca708b391732` | `2e7756618c3c1b89bae80710caad9504c4833008575db8d7ea7ddbc9758aaa05` | 10,624 |

All six Git blob IDs and byte hashes were freshly computed from the current developer branch. The current spec remains the separately approved spec blob `4e30415632545c04a2875d627afa0191afe3f383`.

## Corrections since REQUEST CHANGES

The prior tester report had six blocking findings. Current changes and regression coverage:

1. **Spec provenance:** sampler output now uses `CURRENT_SPEC_GIT_BLOB` and pins the current reviewed spec ID. Test asserts the report uses that constant and the stale ID is absent.
2. **Conflicting JSON dates:** all recognized non-empty date fields are now parsed and must agree with the fixed expected file date; malformed or conflicting dates reject the record. Tests cover conflict and malformed field.
3. **Non-finite CSV values:** numeric flow samples use explicit finite checks; NaN/Infinity are counted separately in `nonfinite_flow_cells` and set edge status to `REJECTED_NONFINITE_FLOW`. Test includes `nan`, `inf` and a valid numeric value.
4. **Signature-like JSON keys:** recursive redaction covers exact `signature`/`sig` and suffix forms including camelCase fields such as `requestSignature`, while preserving ordinary fields. Test covers nested keys and values.
5. **Dated HTML links:** every reported dated link has its `href` sanitized through `safe_url_for_report`; test checks signed query values are redacted while date/path and harmless query fields remain.
6. **Manifest-to-reviewed-tree binding:** before source access the guarded workflow now requires the exact line `**Reviewed developer commit:** <commit>` in the tester report; verifies the commit exists and is an ancestor; and checks for each protected path that `git rev-parse <reviewed_commit>:<path>` matches the exact approved Git blob ID as well as the current HEAD blob. Static offline test asserts these guard checks are present.

## Hosted test evidence

[Run 38029615734](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029615734) passed **32 offline tests** and has no source-fetch step. It includes the previous 29 checks plus three added regression cases for current spec identity, non-finite CSV handling and dated-link redaction, as well as the earlier additions for conflicting dates, signature-like fields and reviewed-commit tree binding.

## Source scope remains finite

The approved request inventory is unchanged: two single-day CDSL FPI XLS files and bounded page metadata; pinned Hugging Face metadata plus exact 8 KiB head/tail ranges; one date- and commit-pinned public JSON record; SEBI/NSE/CalcSetu pages; and GitHub directory metadata only. The client enforces its frozen URL/method/header inventory, source-specific caps, 15 initial request maximum, at most three aggregate redirects, 18 exchanges, 2 MiB total read budget, and one allowlisted HF redirect per eligible request. No full-file fallback or source list expansion is permitted.

## One-run workflow and authorization status

The live workflow runs offline tests, verifies the hash-bound tester report/manifest, checks exact approved blobs at both HEAD and the reviewed commit, confirms the reviewed commit line in the report, and marks the manifest SPENT before the first request. Manual live dispatch defaults to false. The offline workflow runs fixtures only.

**No live source requests have occurred with this implementation, and no one-run manifest exists.** A fresh code PASS is required before a new single-use manifest can be prepared. That manifest must then independently pass the guarded workflow. The eventual output needs a separate artifact audit. This code gate cannot authorize full-history acquisition, feature/label building, model fitting, metrics/p-values, or final-holdout access.

## Requested independent review

Independently re-fetch the six protected files, verify blob IDs/byte hashes and the hosted test run, inspect the updated date/number/redaction logic, and trace the live workflow from report/manifest validation to manifest consumption and first source call. Return **PASS** or **REQUEST CHANGES** with concrete reasons.

**Developer → Tester:** Re-review this exact six-file snapshot and verify the reviewed-commit tree binding. A PASS may permit only a fresh one-run manifest, not network access by itself.

**Tester → Developer:** Keep source requests disabled until this exact snapshot is passed and a separate single-use manifest validates. Independently audit any later source artifact before allowing further research.
