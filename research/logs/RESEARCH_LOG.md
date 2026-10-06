[object Object]
## 2026-10-07 — Phase 2B price-field semantics correction

- The derived final-bar close reconciled to official UDiFF `ClsPric` in only 31.25% of matched near-ATM contracts.
- Rather than lowering the quality threshold, the research checked field semantics and recognized that an intraday final-bar close is a last-traded-price concept, while UDiFF exposes `LastPric` separately from `ClsPric`.
- The reconciliation gate was corrected to use `LastPric` as the primary executable-price reference and `ClsPric` as a secondary diagnostic, with both metrics preserved in the failure artifact.
