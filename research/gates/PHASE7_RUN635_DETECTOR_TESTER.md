# Phase 7 Run #635 Detector-Scope Failure — Tester Review

Status: REQUEST CHANGES.

Run #635 (`37719802712`) completed protocol/detector jobs successfully but skipped `phase7-ensemble-gated`.

Cause: the detector derives `run_phase7` from files changed in the current push. The newly added Run 628 approval gate had already been archived in an earlier commit, so the detector correctly saw no Phase 7-triggering file in the immediate diff. The later detector-path correction itself did not produce the intended trigger because its parent diff did not contain an allowed scientific-path change.

Impact: no regression or empirical execution occurred; no scientific metric exists. Run #635 is non-evidence.

Correction: make a harmless, non-scientific trigger commit after the approved detector correction. Do not alter production science.

Tester -> Developer: log Run #635 and trigger the approved Phase 7 workflow with a harmless test-file comment.