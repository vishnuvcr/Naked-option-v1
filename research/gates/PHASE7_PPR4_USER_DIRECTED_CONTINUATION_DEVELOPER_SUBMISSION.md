# Developer Submission — User-Directed Dhan Acceptance and Open-Source Continuation Plan

**Date:** 2026-10-11  
**From branch:** `phase-07-developer`  
**Submission type:** Exact-snapshot plan/policy gate, before any new live requests  
**Requested decision:** Review the user waiver, no-source-stop policy, fallback plan, source supplement, and offline validation receipt. If passed, authorize the developer only to prepare the exact multi-source acquisition manifest and guarded acquisition workflow.

## 1. Explicit user decisions now binding for research

The user has directed that:
1. The existing Dhan sample and future Dhan provider output be accepted as supplied; no Dhan-versus-NSE/third-party **market value** cross-check is required.
2. The research must never stop globally because one source or feature family is unavailable.
3. When Dhan does not supply a feature, search official/free alternatives (NSE/BSE/regulators/underlying providers, public APIs, GitHub, Kaggle, Hugging Face and other open sources), then construct lineage-preserving composites where valid.
4. Paid sources are not pursued until free-source possibilities for the relevant feature family have been investigated.
5. Source failure affects the relevant source/shard/feature-family/candidate cell only. The family becomes `NOT_ESTIMABLE` only after listed free fallbacks are exhausted; unrelated families/phases continue.

The tester is **not** asked to restore any price-value cross-check. The prior tester report is retained as historical audit record but is waived by the user's new decision for data acceptance.

## 2. Exact developer snapshot pins

| Artifact | Branch | Git blob SHA |
|---|---|---|
| User acceptance waiver | `phase-07-developer` | `7979a8e3212e874489c5f3b2e59f96307e436ae6` |
| Continuation policy | `phase-07-developer` | `bf153f8072190ee2efeeb4f1518a4fb00ed60c02` |
| Dhan-first acquisition/fallback plan | `phase-07-developer` | `4091c54dd660d385583fb72b9eb354edf6aeaa87` |
| Source supplement CSV | `phase-07-developer` | `067a967d07faa6a39d703c2832e5c221ae08efc1` |
| Offline policy validator | `phase-07-developer` | `76dae37749a24ce1a510966f193d8747f5862669` |
| Offline regression tests | `phase-07-developer` | `8d93937d98e7afe79b6db694b2ab22dcd4c3bd41` |
| Offline workflow | `phase-07-developer` | `2219fe01d0e8aa9ba39901f2eb76383bd7c3e989` |
| Research plan amendment | `phase-07-developer` | `c38df3ed1a30f278ec7b2b49929e2faf7d995ab3` |
| Status ledger | `phase-07-developer` | `4edd771007fc7f20823def5f5b684c2c19f3735e` |
| Developer README | `phase-07-developer` | `230bcaed5900e4a729344855ff27f5b0674303af` |
| Main README | `main` | `0bf34cf9d931ee304769e55d5ff4c1b3eb7c7bbe` |

Developer branch head at submission assembly: `708249e5552d1bd57bc297772e8a299291e4d5a9`.

## 3. Exact offline receipt and preserved failures

- **PASS:** [run 38078187293](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38078187293), trigger commit `a2fe4e2462060bee20bee16ade66169cea70a12d`.
- Verified results: Python compilation passed; all 4 unit tests passed; policy validator passed; output says waiver and no-source-stop policy are internally consistent.
- The test was strictly local/offline: no source request, market-data read, model fitting/scoring or holdout access occurred.
- Prior failed iterations remain preserved in [run 38077986545](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38077986545), [run 38078034861](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38078034861), [run 38078037477](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38078037477), and [run 38078126806](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38078126806). The fixes corrected test/plan phrase expectations only. Error log preserves the iterations and the corrected snapshot subsequently passed.

## 4. Plan summary for review

The source plan specifies:
- Dhan daily NIFTY candles for long development history, saved as immutable/checksummed chunks.
- Dhan intraday bars over its documented window, split into requests no longer than 90 days.
- Dhan rolling expired option data over its documented window, split into requests no longer than 30 days; begin with registered 5-minute ATM ±5 coverage and expand only for preregistered needs.
- Official/free fallbacks for NSE/BSE indices, NSE derivatives/UDiFF, India VIX, FII/DII, CDSL/SEBI FPI, global market series, Cboe VIX, Treasury rates, FX, commodities, news/event/sentiment, calendars and corporate actions.
- Composite joins preserving `source_id`, `available_at`, `observed_at`, `source_version`, raw checksums, licenses and transformation hashes. No source is silently overwritten; no missing option values are made into zero quotes.
- Safe serial pacing, bounded response sizes, immutable caches, resumable date shards and automatic failure reports. A source failure skips the affected shard, attempts its free fallback, and continues unaffected source/family jobs.
- Secret is injected at runtime only. It is never echoed or written into logs/artifacts.
- Future Phase 8 costs must incorporate Paytm Money brokerage, exchange/statutory charges, bid/ask spread, slippage, latency, lot-size regimes, fills and premium decay.
- User accepted the previous one-row Dhan sample for development use by waiver. The sample alone is not a sufficient training panel. No external value reconciliation will be performed.

## 5. Holdout, model and strategy scope

The prospective final holdout design has already received a tester PASS **for design only**: 252 future official NSE decision-origin sessions plus 10-session label-maturity tail. It must be instantiated after real config/source/code freeze and sealed before first forecast. Do not retroactively relabel used history as untouched.

This request does **not** ask the tester to authorize fitting/scoring, open holdout labels, or run option P&L. It asks for permission to create the next **exact source-by-source acquisition manifest and guarded workflow**. That exact acquisition snapshot will be submitted again to the tester before any new live request.

## 6. Explicit review checklist

Please verify:
- The user's no-cross-source-value-check waiver is unambiguous and does not falsify the retained historical tester record.
- No-source-stop behavior applies to individual sources/feature families, with a finite source fallback order and no fabricated values.
- Dhan request windows/rate pacing, cache integrity, resume logic, and secret handling are conservative and testable.
- Free sources are prioritized; FPI-only series are not relabelled DII or total institutional flow; proxies are distinct features.
- The current no-download/no-fit boundary remains explicit for this plan gate only.
- The exact offline receipt matches the pinned validator/tests/workflow.
- If deficiencies exist, return REQUEST CHANGES with precise findings; otherwise pass this plan and authorize only drafting the exact next request manifest/workflow.

**Developer → Tester:** Independently review the pinned plan/policy and hosted offline receipt. Do not require the waived Dhan-versus-other-source price-value check.  
**Tester → Developer:** Return a concrete disposition. If approved, specify the exact next permitted operation; do not silently authorize live acquisition through a plan-only PASS.
