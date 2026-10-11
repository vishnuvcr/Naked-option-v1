# Dataset Value Audit — Mistake Log (2026-10-11)

| Step | Mistake | Impact | Correction | Verification |
|---|---|---|---|---|
| Initial synthetic test run | Blank optional numeric cells were compared against zero in the negative-value check. | The auditor raised TypeError and returned no useful aggregate finding for five tests. | Guard the comparison with `value is not None`; retain blankness as an explicit missing-value count. | Corrected auditor commit `8c95d0dc19a3987e3fb1d3a14ea06964b7e42799`; later suite passed at run `38121256105`. |
| Initial review of option enum | The auditor initially expected `CE/PE`, but the repository's collector emits `CALL/PUT`. | Valid option rows would have been wrongly classified. | Align the validation enum with collector output and add the valid synthetic fixture using `CALL`. | Commit `cea8e3295ad49129a357d1848ac315e844cd1677`; subsequent suite passed. |
| Initial schema-fixture test | The wrong-header synthetic fixture attempted to write extra dictionary fields not present in its deliberate bad header. | The fixture itself failed before exercising the schema check. | Filter fixture rows to the header fields when deliberately producing a schema-mismatch file. | Commit `94b5611117351653ddfe87f97af2cf84979778ca`; subsequent suite passed. |

These were development/test-fixture defects; no market rows were decrypted and no market-data request was made during their discovery. The first failure was not treated as a pass. This log stores action summaries only, not private reasoning.

**Developer → Tester:** Confirm these three mistakes are accurately captured and that regression tests now exercise them.

**Tester → Developer:** Check the exact-snapshot automated test receipt and retain the fail-closed boundary for any runtime findings.
