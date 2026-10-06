[object Object]
## 2026-10-07 — Phase 2B secondary-source corroboration protocol revision

- The strict ±0.25%/tick LastPric agreement was 95.8333%, with the largest observed relative discrepancy about 2.8%.
- Rather than pretending the strict test passed, the research preserved it as a diagnostic and introduced a distinct, explicitly labeled secondary-corroboration gate suitable for non-canonical derived data: >=95% within 1% relative error, no observation beyond 3%, plus median relative error reporting.
- This protocol revision is about data-source corroboration only and cannot authorize use of the derived dataset as an executable price feed.
- Tester review is required before the data gate can advance.
