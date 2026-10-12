# Independent Tester Scope Review — Manifest-Bound Contract Signature and Schema Amendment R4
Date: 2026-10-12
Role branch: phase-08-prediction-tester

## Decision
**PASS_SCOPE_AMENDMENT_ONLY_WITH_RESTRICTIONS.** The R4 amendment is accepted as a scoped correction to R3's schema assumptions. It does not authorize code execution against any real artifact, model fitting, holdout access, external source calls, P&L or strategy promotion.

## Exact proposal reviewed
- Developer branch: `phase-08-prediction-developer`
- Proposal: `research/gates/PHASE8P_DUPLICATE_CONTRACT_SCOPE_AMENDMENT_R4_2026-10-12.md`
- Proposal blob SHA-1: `1ea9bca882b53fd2853829137aba2d521023b3bd`
- Proposal commit: `f9436fcd146316e3a3fbf4f166270d12c7c85471`
- Parent approved duplicate handling scope R3 blob: `6ea73c246a2cecd158e4bf8dbbd087befafcb89a`
- Frozen Greek artifact pin: ID 11723198817, SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`.

## Independent checks
- R4 appropriately acknowledges that a developer-authored full-column constant had not been proven against the accepted immutable source manifest. Fail-closed gates must not treat guessed source fields as authoritative.
- The exact schema source is now the `columns` list inside the already-pinned encrypted artifact's `dataset_manifest.json`. A whole-artifact ZIP hash and exact artifact ID remain mandatory, and each part's *ordered* header must match the manifest exactly.
- Required identity/economic fields remain explicit; timestamp UTC/IST representation is conditional on the immutable schema, but any present timestamp must agree with the source epoch. This avoids requiring a representation that the source did not record while preserving exact timing.
- All actual manifest columns are included in the row signature except the four explicitly permitted collection-provenance fields when present. Unknown fields are not omitted; a conflict in any such field is treated conservatively as a conflict. If serialization/type comparisons cannot be shown deterministic, implementation must block rather than relax comparison.
- The economic key keeps underlying, canonical Greek valuation instant, normalized actual expiry date, returned strike and normalized side. Expiry flags/codes remain part of the signature, preventing incompatible expiry descriptions from being split into separate keys.
- Exact duplicates may only be collapsed in the in-memory feature view after equality of all non-provenance fields; conflicting groups yield field-name/count-only diagnostics. The encrypted artifact and its row counts remain immutable.
- The amendment does not alter labels, horizons, model specifications, primary metric, bootstrap/multiplicity controls, or protected holdout rules.
- The prior CI failure [#38204234797](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204234797) is a synthetic fixture/schema mismatch under unapproved code. It is not a data integrity conclusion or prediction result.

## Required next gates
1. Implement R4 with exact manifest-column/header reconciliation before aggregation and a deterministic field canonicalizer. Schema mismatch or ambiguous typing must block.
2. Add synthetic tests for manifest-defined full schema, ordered header equality, missing/extra/reordered columns, known timestamps with conditional UTC/IST, identical duplicates across provenance differences, conflicts in all economic categories including unknown extra columns, row-order invariance, and aggregate-only output.
3. Preserve R1–R3 and previous failed runs as history. Submit new exact module/test/workflow hashes for a distinct independent code-only review.
4. Update the preflight executor to pin the new exact code commit and code decision, then obtain a separate tester PASS on that revised executor before any artifact rerun.
5. The subsequent run may generate only an aggregate schema/coverage report. Its exact report must receive a separate tester decision before any empirical fitting. If it cannot prove target maturity, development-only row masks/holdout exclusion, chronology/purge or coverage thresholds, remain BLOCKED.

**Tester → Developer:** implement R4 and synthetic tests only, then request a fresh exact-snapshot code review. Do not run the real artifacts yet.

**Developer → Tester:** retain prior code/preflight receipts unchanged. Independently audit dynamic schema enforcement, every-column signature completeness, deterministic equality, conflict handling, and no raw-data egress.
