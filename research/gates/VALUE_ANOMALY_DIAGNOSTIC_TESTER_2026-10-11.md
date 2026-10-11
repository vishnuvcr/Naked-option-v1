# Tester Report — Offline Value Anomaly Provenance Diagnostic

- Review date: 2026-10-11 UTC
- Exact developer commit reviewed: `0c502aa44274e841af263bd70791204144a36a78`
- Offline regression suite: [38129068261](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38129068261) — success
- Research protocol check: [38129068622](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38129068622) — success
- Reviewer independence caveat: tester-role review was performed in the same connected assistant session, not by a separate human or independent AI reviewer.

## Exact files reviewed

| File | Blob SHA |
|---|---|
| `scripts/diagnose_nifty_1m_value_anomalies.py` | `97df4b921ddd59b555514daac289d59d8601d62d` |
| `scripts/test_diagnose_nifty_1m_value_anomalies.py` | `ad2413202b0e9c4bd0d49c54f7580cc4bf46b558` |
| `scripts/diagnose_nifty_1m_unmatched_spot_targets.py` | `05d0a3a1f921d1405e52a7da7c2f781de5243865` |
| `.github/workflows/phase-07-unmatched-option-timestamp-diagnostic.yml` | `1948d2e09d2778a9687702c4ec384746c2ef2214` |
| `.github/workflows/phase-07-nifty-1m-composite-tests.yml` | `17b79400817614e59a714c89f9f2450b58feb228` |
| `.github/workflows/dataset-value-audit.yml` | `42c105bade1f001be422fc76fa8b38dfd65626e9` |

## Checks

1. **Regression suite — PASS.** The offline pipeline run completed successfully. The new synthetic tests cover OHLC and negative-volume detection, distinct bad epochs, redaction of raw values/request IDs, and the treatment of expected missing underlying values on unmatched rows.
2. **Provenance diagnostics — PASS BY CODE REVIEW.** The diagnostic groups issues by date and hashed source request identifier, emits stable row fingerprints excluding prices/volumes, and reports both occurrence counts and distinct-epoch counts. It compares joined NIFTY values with the standalone SPOT row at the exact same epoch only; it does not shift timestamps or mutate source data.
3. **JSON report repair — CODE FIXED; HOSTED RERUN PENDING.** The previous unmatched-timestamp workflow failed when it parsed the diagnostic JSON because the generated file had trailing extra data. The writer now emits a valid JSON newline, and the report parser validates JSON before cleanup/publication. The workflow must be rerun on the fixed exact snapshot to verify this operationally.
4. **Plaintext cleanup — NOT YET VERIFIED FOR THE NEW RUN.** Existing run [38128115186](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38128115186) confirms plaintext removal succeeded, but the later report-publication step failed. The new workflow now requires the anomaly diagnostic and cleanup steps to pass before publishing; confirm cleanup in the next hosted run.
5. **Data findings — NOT REPAIRED YET.** The latest audited artifact reports 382 matched-NIFTY OHLC violation occurrences, 12 standalone spot OHLC violation occurrences, 309 negative NIFTY-volume occurrences, 11 negative option-volume occurrences, and 19,021 unmatched option rows. These are counts, not a causal diagnosis. The new provenance report is required before deciding whether each is a collector/mapping defect, source anomaly, duplicated occurrence of one bad spot bar, or an explicit exclusion.
6. **Permissions — UNCHANGED.** No new data request, source-row correction, model fitting/scoring, holdout access or strategy/P&L testing is authorized.

## Verdict

**PASS WITH SCOPED RESTRICTIONS — offline diagnostic code and tests only.**

This does not approve changing the original data values. The immutable source artifact must be preserved. Any correction should be made only in a separate derived dataset, with source provenance, a deterministic documented rule, before/after row counts, and regression evidence. Never clamp negative volume to zero or repair OHLC by swapping/extending values without authoritative source evidence.

**Tester → Developer:** Promote only the exact reviewed files, rerun the offline workflow, and inspect the sanitized anomaly report before proposing any derived-data corrections.

**Developer → Tester:** Review the hosted report and cleanup evidence; then independently classify each anomaly family and test any correction/exclusion rule before model fitting is considered.
