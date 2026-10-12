# Phase 8P — Daily Decision-Time Contract Amendment Proposal R1
Date: 2026-10-12
Applies to: PHASE8P_GREEK_PREDICTION_SCOPE_R3_2026-10-12.md
Status: **PROPOSED FOR TESTER REVIEW ONLY — NOT ACTIVE UNTIL APPROVED**

## Why an amendment is needed
The frozen Run #994 daily panel carries a date-only `decision_timestamp` derived from the daily source `date` field. Phase 3's daily label is close-to-close: `future = log(close.shift(-H) / close)`; its target is the H-th subsequent trading-session close. The label does not independently encode a wall-clock time. The R3 feature scope correctly disallows guessing a minute offset, so the daily feature join requires a pre-approved decision-time convention.

## Proposed fixed convention
1. For daily panel row with trading date D, represent the **prediction decision instant** as D 15:30:00 Asia/Kolkata, the published regular-session close for the NSE cash/equities segment, converted to UTC for joining. Official NSE source: https://www.nseindia.com/static/market-data/market-timings (regular equities session 09:15–15:30); corroborating NSE Market Timings & Holidays page: https://www.nseindia.com/resources/exchange-communication-holidays.
2. This is a timestamp interpretation for the existing daily-close label, not a label amendment. The label remains `sign(log(close[D+H trading sessions] / close[D]))`, with target end at that later trading session's 15:30 IST close.
3. Only option features whose stored Greek valuation instant equals the decision instant exactly are eligible. Under the accepted R3 convention, the Greek bar start timestamp plus the recorded 60-second valuation offset is the instant. A row starting at 15:29 IST may represent the completed 15:30 instant. No option data valued after 15:30 IST may enter this daily forecast, even though the derivatives segment may continue trading later.
4. Spot features use only the completed session D and older bars, ending at 15:30 IST. Previous-session features use completed daily sessions. No use of future-date option OI, volume, spot, Greek or target values.
5. Trading dates are taken from the immutable Phase 3 daily source date sequence; do not create holiday/weekend dates. Horizon H target end is the source trading date at row position i+H, exactly matching the frozen daily `make_label` logic. Training labels must mature strictly before each test decision instant.
6. If no exact option snapshot exists at the decision instant, record no exact feature join and apply the pre-registered overlap gate. No as-of, nearest-bar, forward-fill or interpolation fallback is permitted.

## What does not change
No Phase 3 labels, horizons, model methods, test-family size, primary metric, bootstrap procedure, Holm correction, coverage gates, holdout rules or artifact hashes change. The Run #994 forecast probabilities remain immutable. This proposal does not authorize artifact download/decryption, model fitting, holdout access, option P&L, strategy testing or promotion. The accepted Greek artifact remains PARTIAL_GRID and CC-BY-NC-4.0 non-commercial research only.

## Required tester decision
The tester should check (a) that the official NSE time source supports the cash-session close convention, (b) that this matches the stored daily close label rather than the longer derivatives session, (c) the t+60 exact-valuation arithmetic, and (d) that no look-ahead or target-label change is introduced.

**Developer → Tester:** approve or reject this exact timestamp amendment; this is not a code/data authorization.

**Tester → Developer:** keep daily Greek features blocked unless this amendment is explicitly approved; even after approval, the exact code and schema preflight gates remain mandatory.
