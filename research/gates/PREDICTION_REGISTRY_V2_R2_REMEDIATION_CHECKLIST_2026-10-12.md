# Registry V2 R2 — Independent review blocker and remediation checklist

Date: 2026-10-12  
Status: **BLOCKED — tester requested changes; no empirical fitting authorized.**

The independent audit could read the human index and small label/config manifests but could not inspect the oversized method registry and configuration shards reliably. The arithmetic 20 × 10 × 5 = 1,000 is not evidence that every Cartesian-product combination is a valid or distinct scientific method.

## Required before resubmission
- [ ] Split methods into small, inspectable shards (target <=25 records/file).
- [ ] Split configurations into small, inspectable shards (target <=100 records/file).
- [ ] Add top-level index with exact file paths, counts, byte lengths, first/last IDs, and SHA-256 values.
- [ ] Add deterministic verifier using standard SHA-256; include known-vector test `SHA256("abc") = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`.
- [ ] Add explicit compatibility matrix across algorithm family, feature representation, and inference operator; block incompatible combinations and count only valid, semantically distinct methods.
- [ ] Freeze exact label/flat-return/session-boundary rules, eligibility and minimum class support, missingness policy, chronological folds, purging/embargo, multiplicity groups, bootstrap block-length rule and random seeds.
- [ ] Add synthetic dry-run, restart/checkpoint test, resource estimate and failure-log test.
- [ ] Ask independent tester to review the exact commit and hashes. Do not run empirical fits or access untouched holdout until both registry and synthetic-runner gates pass.

## Audit trail
The connected GitHub file-fetch adapter returned empty content for the large method registry and could not fetch its raw contents due to response size. This is an auditability failure, not evidence of invalid underlying bytes. Earlier 8,000-count correction remains in force. Do not mark the gate passed based on the summary alone.
