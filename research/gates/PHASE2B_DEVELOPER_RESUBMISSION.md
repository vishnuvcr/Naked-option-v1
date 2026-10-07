# Phase 2B Developer Resubmission

The Phase 2B reconciliation gate has been corrected after tester review.

## Corrections since prior submission

- Enforce 95% two-way contract-key coverage after selecting the expiry represented by the weekly HF file.
- Enforce 99% close tolerance within one tick or 0.25%.
- Detect official duplicate keys.
- Detect tied latest HF timestamps.
- Preserve final HF observation even when close is missing; fail rather than backfill an earlier close.
- Compare HF latest underlying value with official EOD underlying.
- Probe global source manifest in CI.
- Keep derived HF data non-canonical and license-restricted.

Tester should independently review the new final-close logic and threshold enforcement.
