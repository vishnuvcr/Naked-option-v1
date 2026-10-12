# Independent Tester Review — Phase 8P Daily Decision-Time Amendment R1
Date: 2026-10-12
Reviewed proposal: `research/gates/PHASE8P_DAILY_TIMESTAMP_AMENDMENT_R1_2026-10-12.md`
Developer branch: `phase-08-prediction-developer`
Proposal blob SHA-1: `3f48c1b00b8abcb35103cda620734071c77b459c`

## Decision
**PASS — SCOPE AMENDMENT ONLY, WITH RESTRICTIONS.** This approves the proposed interpretation of date-only daily panel rows for the future implementation. It is not a code gate, data access approval, preflight approval or empirical-model authorization.

## Independent checks
1. **NSE session time:** NSE's published market-timings page states the regular equity session is 09:15–15:30 IST and the equity-derivatives regular session is 09:15–15:40 IST. Sources: [NSE Market Timings](https://www.nseindia.com/static/market-data/market-timings) and [NSE Market Timings & Holidays](https://www.nseindia.com/resources/exchange-communication-holidays). This distinction supports using the cash-index close instant for a daily NIFTY spot-close target; it does not mean later derivatives observations can enter the daily feature set.
2. **Target consistency:** the frozen daily label implementation uses `future = log(close.shift(-H) / close)`; mapping date D to D's cash-session close preserves this target and does not change H or any label value.
3. **Target-end arithmetic:** the H-th later observed daily source row—not H calendar days—is the label end. This agrees with the frozen row-shift rule and keeps holidays/weekends out of target indexing.
4. **Exact option-time alignment:** R3 assigns Greek valuation time as the source timestamp plus its recorded 60-second offset. Only a Greek valuation instant equal to D 15:30 IST may be included. A bar starting at 15:29 IST is eligible only if its timestamp/offset proves that exact end time; later option rows are excluded despite the longer derivatives session.
5. **Leakage boundaries:** no feature is allowed after the daily decision instant, no nearest/as-of/forward-filled option snapshot is permitted, and the existing target-maturity purge and protected holdout remain unchanged.

## Required implementation controls
- Store the daily timestamp convention in the preflight decision and experiment manifest as `DATE_ONLY_DAILY_PANEL_TO_CASH_CLOSE_15_30_IST`.
- Validate that the row date exists in the immutable daily trading-date sequence, and derive target end from its H-row-ahead source date.
- Verify exact UTC timestamp equality and report per-day exact-snapshot coverage. If missing, retain the missing join; do not move the timestamp.
- Preserve all R3 and Run #994 artifact IDs/digests and non-commercial/partial-grid restrictions.
- Keep the model job blocked until the separate exact-code gate and an actual artifact-bound schema/coverage preflight receive independent PASS decisions.

## Restrictions
No real artifact has been downloaded/decrypted for this sub-study; no empirical model fitted, holdout opened, source requested or option P&L run. Daily feature construction remains unavailable until the developer implements the exact convention and the complete code gate passes.

**Tester → Developer:** implement only the approved cash-close mapping described here; test 15:29+60s exact inclusion and 15:28/15:30 start exclusion, dates missing from the session index, holidays, and target H-row arithmetic.
**Developer → Tester:** keep this amendment separate from the code R1 REQUEST_CHANGES; resubmit a new exact code snapshot and require code gate PASS before artifact preflight.
