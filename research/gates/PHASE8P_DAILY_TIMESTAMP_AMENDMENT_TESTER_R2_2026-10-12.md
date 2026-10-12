# Independent Tester Review — Daily Timestamp Amendment R2 (Provenance Correction)
Date: 2026-10-12
Original scope decision: PASS_SCOPE_AMENDMENT_ONLY_WITH_RESTRICTIONS
Current approved daily convention: DATE_ONLY_DAILY_PANEL_TO_CASH_CLOSE_15_30_IST

## Correction
The R1 review text labeled the proposal's Git commit SHA (`3f48c1b00b8abcb35103cda620734071c77b459c`) as its file blob SHA. That label was incorrect. Independent Git contents lookup confirms:
- Proposal commit: `3f48c1b00b8abcb35103cda620734071c77b459c`
- Actual proposal blob SHA-1: `265c6696466b1999371cb4581baf20fbe950d3f1`
- R1 tester review blob: `57e7989489d347c528d5bba5147d1272d5a45f9a`
- R1 machine-decision blob: `bd5514467a1d2a049db5e0d37c4db356adec6e26`

## Decision
**R1 scope amendment remains PASS — SCOPE AMENDMENT ONLY, WITH RESTRICTIONS.** This is a provenance-label correction only; the approved 15:30 IST cash-close interpretation, exact Greek timestamp join, close-to-close label, and all downstream gates are unchanged.

No real data was opened, no model fitted, no holdout accessed, and no P&L/strategy work authorized.

**Tester → Developer:** pin the proposal by its actual blob SHA `265c6696466b1999371cb4581baf20fbe950d3f1`, not by commit SHA.
**Developer → Tester:** retain R1 as history and use the corrected R2 decision when checking daily feature-time provenance.
