# Phase 2B Tester Re-Review — REQUEST CHANGES

## Independent code/data review

### Findings

| Check | Result | Finding |
|---|---|---|
| Static Python syntax is guarded in CI | PASS | AST validator is present. |
| Official archive acquisition/caching | PASS | Fixed legacy and UDiFF sample acquisition and raw cache exist. |
| HF_TOKEN use | PASS | Token is used for HF metadata/reference acquisition. |
| Global source manifest | PASS | Global macro/cross-market sources are enumerated. |
| Availability policy | PASS | Conservative PIT rules are explicit. |
| Reconciliation protocol stated | PASS | Official source is canonical; derived data only for validation/gap fill. |
| **Reconciliation enforcement** | **FAIL** | The reconciliation script reports tolerance/coverage but does not fail the workflow when acceptance thresholds are breached. |
| **Duplicate handling** | **FAIL** | Duplicate contract keys are silently overwritten in both official and HF maps, despite the protocol requiring duplicate rate = 0. |
| **Expiry-scope correctness** | **FAIL** | The selected HF weekly file is compared against all official NIFTY expiries for that date. A weekly-expiry reference file is expected to cover only a subset; the comparison must scope the official side to the matched HF expiry before applying coverage thresholds. |
| **Underlying reconciliation** | **FAIL** | Official underlying is extracted but HF spot is not compared even when a spot field is mapped. |
| Global-source probing | **FAIL** | `probe_sources.py` reads only `SOURCE_MANIFEST.csv`; the new `GLOBAL_SOURCE_MANIFEST.csv` is never probed in CI. |
| Missing/invalid price handling | **REQUEST** | The comparison skips non-finite values instead of reporting/thresholding missing core prices on the compared set. |
| Snapshot provenance | PASS | Official snapshot manifest includes hash, size, row count and parser version. |
| License constraints | PASS | S08 is explicitly restricted to research validation. |

## Important methodological correction

The derived HF dataset is not allowed to pass merely because a small intersection matches. The code must:
1. identify the expiry represented by the selected weekly file;
2. restrict official comparisons to that expiry;
3. detect duplicates before constructing maps;
4. compute coverage on the same key universe;
5. fail below declared coverage/price-quality thresholds;
6. compare the underlying spot series when both sources provide it.

## Gate decision

**REQUEST CHANGES**

Phase 2B is not passed. This is a code-enforcement gate, not a data-quality conclusion.

## Developer instruction

Fix the reconciliation logic and add global endpoint probing. Then resubmit the same Phase 2B branch to tester. Do not start label/model work.
