# Phase 5 Run #19 Runtime Investigation — Tester Review

Date: 2026-10-07
Developer run: 37611880308
Developer commit: c8603d76efcae7d555e7bc61432f077c72c46e0a

## Observed failure

Run #19 completed with conclusion `cancelled`.

The empirical D01-D15 step ran from 11:07:52 UTC to 12:38:11 UTC, approximately 90 minutes. The workflow defines `timeout-minutes: 90`. Schema validation and artifact upload were skipped.

Therefore the most parsimonious reproducible cause is the workflow's explicit 90-minute job timeout, not a scientific/model failure.

## Evidence disposition

Run #19 is **NON-EVIDENCE**. No empirical metric may be extracted or accepted because no immutable artifact was produced.

The successful regression suite remains valid as regression evidence for the corrected code.

## Runtime correction proposed

Developer should make an operational-only workflow amendment:

1. Increase the Family D job timeout from 90 to 180 minutes.
2. Add explicit progress logging around each empirical horizon/model block so a future timeout can be localized.
3. Do not change model definitions, features, labels, horizons, refit cadence, cost assumptions, random seeds, selection rules or statistical metrics.
4. Preserve all existing regression/schema checks.
5. Keep the workflow finite; the 180-minute timeout is a hard upper bound for one hosted Family D run.
6. Submit the exact diff to the tester before the next fresh empirical run.

## Tester decision

**PASS — RUNTIME-ONLY AMENDMENT AUTHORIZED**, provided the developer changes only the operational timeout/progress observability described above.

No result-driven optimization is authorized.

## Developer instruction to tester

After the workflow diff is submitted, verify that no scientific definition changed and authorize the fresh run.

## Tester instruction to developer

Apply only the runtime/observability amendment, preserve Run #19 as non-evidence, update README/status/error/research logs, and wait for this gate before relying on the next Family D artifact.
