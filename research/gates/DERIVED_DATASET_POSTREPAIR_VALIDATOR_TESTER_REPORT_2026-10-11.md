# Tester Report — Derived Dataset Post-Repair Validator

- Review date: 2026-10-11 UTC
- Exact developer commit reviewed: `c4654b551a061652c98c6b0be81ae46a90083f6b`
- Offline test run: [38131302858](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131302858) — PASS
- Protocol check: [38131303137](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131303137) — PASS
- Scope: offline repair and post-repair structural validation of the existing R2 artifact only.
- Independence caveat: this is a tester-role repository review in the connected assistant session, not a separate human or external independent reviewer.

## Exact files reviewed

| File | Blob SHA |
|---|---|
| `scripts/repair_nifty_1m_composite_values.py` | `5fe7b5fb35e7cae1c1a39258ce7e3c78adf8fb8b` |
| `scripts/validate_repaired_nifty_1m_composite.py` | `e2feada6125666b1277af288e9ad1ca5fa444b50` |
| `scripts/test_repair_nifty_1m_composite_values.py` | `79a1625f768790395e5f121423e340627c83ee98` |
| `scripts/test_validate_repaired_nifty_1m_composite.py` | `d04046bc86110853c423955f8b2b4a5e93454740` |

## Review results

1. **Source immutability — PASS.** Repair writes a separate encrypted derived dataset; it does not overwrite the source artifact.
2. **Exact joins only — PASS BY CODE REVIEW.** Joined NIFTY OHLCV is reconciled only from a standalone SPOT row at the same epoch. Unmatched option rows are kept unmatched and their underlying fields remain blank; no nearest-time join, timestamp shift or interpolation is introduced.
3. **Invalid values — PASS BY CODE REVIEW.** Invalid standalone OHLC and negative/unparseable volume are masked to missing rather than clamped or fabricated. Option volume anomalies are masked. Weekend session labels are flagged for review, not silently deleted.
4. **Independent output validation — PASS IN SYNTHETIC TESTS.** The repair routine decrypts its own output parts only inside a temporary directory, verifies each compressed-payload SHA-256, runs a separate validator against the derived manifest, and refuses to report repair success unless the validator returns `PASS_WITH_COVERAGE_RESTRICTIONS`. The smoke test exercises a valid exact-epoch join. Existing repair tests also exercise invalid spot bars and unmatched rows.
5. **Privacy and cleanup — PASS BY CODE/TEST REVIEW.** The post-repair audit report includes aggregate counts only; temporary plaintext and the SQLite duplicate-check database are removed. Actual hosted cleanup still must be confirmed on the rerun.
6. **Test failure handled correctly.** Run [38131249432](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131249432) failed because a synthetic unmatched-row fixture incorrectly claimed one matched row in its manifest. The fixture counts were corrected in commit `c4654b551a061652c98c6b0be81ae46a90083f6b`; the full offline suite then passed at run `38131302858`. This was a fixture error, not evidence that the real data had changed.

## Decision

**PASS WITH SCOPED RESTRICTIONS — code and synthetic tests only.**

Authorize the exact reviewed implementation to rerun the derived repair against the already-approved encrypted R2 artifact `11696937921`, and require the independent post-repair validation to pass before publishing `DERIVED_REPAIR_COMPLETE`. This does not approve any new source request or establish model readiness.

The parent artifact has 19,021 unmatched option rows at 421 distinct timestamps, 382 joined-NIFTY OHLC violation occurrences, 12 standalone spot OHLC violation timestamps, 309 negative spot-volume occurrences and 11 negative option-volume occurrences. The repair policy masks invalid values and preserves unmatched targets rather than inventing values. The remaining missingness is a known coverage restriction.

## Permissions

- Further market-data requests: **NOT AUTHORIZED**
- Option endpoint requests: **NOT AUTHORIZED**
- Model fitting/scoring: **NOT AUTHORIZED**
- Holdout access: **NOT AUTHORIZED**
- Strategy/P&L testing: **NOT AUTHORIZED**

**Tester → Developer:** Promote only the exact reviewed code and rerun the fixed R2 artifact. Inspect the post-repair audit summary and hosted cleanup logs before calling repair complete.

**Developer → Tester:** Review the new run's artifact/manifest linkage, row-count reconciliation, quality counts and cleanup proof. Return REQUEST CHANGES if any invariant fails.


## Follow-up — scoped test repair (2026-10-11)

- Follow-up exact developer snapshot: `350776e764ec238e23dd325b2a4d64f3d9fa468c`.
- Offline suite [38131565150](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131565150) and protocol check [38131565322](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131565322) both passed.
- The prior suite correctly surfaced that main's separate unmatched-timestamp diagnostic workflow lacks the pinned cryptography installation. That issue is tracked in [PR #8](https://github.com/vishnuvcr/Naked-option-v1/pull/8), which remains open because the connected account cannot approve its own PR. The repair regression now checks the repair workflow's own dependency and artifact preparation, so an unrelated diagnostic workflow defect does not block this repair gate. This does not declare PR #8 resolved.
- This follow-up changes test scope only; the repair implementation and exact-epoch/missingness policy are unchanged. The repair may now be rerun against the fixed R2 artifact with independent post-repair validation mandatory.

**Tester → Developer:** Rerun only the fixed R2 artifact, and verify the embedded post-repair validation plus cleanup evidence.

**Developer → Tester:** Return the new report and derived artifact hashes for final scoped review; do not authorize modeling or source requests.
