# Independent Tester Report — Extension 3 Offline Code Gate

**Decision: PASS WITH SCOPED RESTRICTIONS — offline validation/cache helpers only. No live request authorized.**

Reviewed snapshot: `phase-07-developer`, commit `939704a46246e90ae2850a16e2b4d2bf22f76ec4`. Hosted test: [38048191811](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38048191811), success.

## Reviewed blobs

- Adapter `scripts/dhan_instrument_master.py`: `b292c10735ec43520a664ed9b8e892072eb169a2`
- Tests `scripts/test_dhan_instrument_master.py`: `fa485bc5be727153c52e7e6ef96a4251b5c553c3`
- Workflow `.github/workflows/phase-07-dhan-instrument-master-tests.yml`: `243b9b22a3f1c5cbc5c3aaa3242360d4ff171859`
- Plan `research/phase7/EXTENSION3_DHAN_OFFICIAL_INSTRUMENT_SOURCE_PLAN.md`: `dd53a6bb2ec581d8a726397cd3767bbee8b0da0e`

## Checks

1. Hosted run passed and reported **9 offline tests passed**; CLI reported `network_enabled=false`.
2. Input checks reject empty, oversized, invalid UTF-8 and NUL-containing payloads; UTF-8 BOM is supported.
3. CSV schema checks reject missing/duplicate headers, missing required values, malformed rows and duplicate (segment, security ID) pairs.
4. Validation returns SHA-256 and row/security-ID counts.
5. Cache writes validate first, write to a temporary file, fsync and atomically replace; a regression test confirms invalid content does not overwrite an existing valid cache.
6. The new workflow only runs the offline test/CLI with read-only repository permissions and no secrets.
7. [Protocol run 38048191923](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38048191923) passed repository contract and literature-registry checks.

## Restrictions and limitations

- No real CSV was fetched or inspected and no cache was populated.
- The 8 MiB limit is only a proposed cap; actual file size has not been measured. An over-cap response must fail closed.
- The helper validates bytes supplied by a caller; it does not prove source URL, HTTPS, content type or redirect behavior. Those must be implemented and reviewed separately.
- No credentials may be sent to the CSV host; redirects must be disabled and any 3xx must fail closed.

## Decision

Accept only the offline parser/validation/cache foundation. This does **not** authorize a live request, source acquisition, history/options downloads, modeling, strategy testing or holdout access.

**Tester → Developer:** Prepare a separate fetch implementation with exact URL/host checks, no credentials, redirects disabled, timeout and byte caps, then submit the exact snapshot for another independent review. Do not make a live request yet.

**Developer → Tester:** Review any fetch/workflow change before a new one-use manifest is created.
