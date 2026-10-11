# Independent tester review — optional raw byte-count reference

Date: 2026-10-11
PR: [#18 — Avoid inventing an expected raw byte count](https://github.com/vishnuvcr/Naked-option-v1/pull/18)
Developer CI evidence: [run 38145624981](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38145624981) — success, 49 tests passed.

## Decision
**PASS WITH SCOPED RESTRICTIONS** for the optional byte-count reference correction.

## Findings
- The dataset's previously recorded uncompressed SHA-256 is available, but an independently sourced expected uncompressed byte count was not established in the available manifest. The prior hard-coded value must not be treated as verified.
- The scanner still computes and reports the observed uncompressed byte count. It checks a byte count only when an independently supplied reference is provided; otherwise the expected count and match flag remain null.
- The uncompressed CSV SHA-256 remains mandatory and is the content-identity gate. A mismatch remains a failure, regardless of compressed gzip hash.
- The receipt publisher allows unknown expected size metadata but requires the raw-content hash to match before a pass receipt. If an expected size is provided and mismatches, it cannot pass.
- Hosted regression tests cover both hash mismatch and hash match with an unknown expected size; the broader 49-test synthetic suite passed.
- This correction does not inspect or authorize real data. R4 still needs exact-file approval and a single-use request.

**Tester → Developer:** Merge PR #18, then verify main's publisher blob matches the tested blob and confirm the R4 audit snapshot includes no guessed byte-count expectation.
**Developer → Tester:** Issue a new exact-hash decision only after the scanner, workflow and tests are frozen; independently inspect the complete real-file report and cleanup proof before model fitting.
