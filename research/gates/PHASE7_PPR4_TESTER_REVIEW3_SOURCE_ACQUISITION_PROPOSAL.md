# PPR-4 Tester Review 3 — Source/Cache Proposal

Decision: **PASS WITH SCOPED RESTRICTIONS — proposal design only** (review date 2026-10-11).

Exact source/cache proposal reviewed: `e94b97164a8223fec4be7dd7583f00c359b11a5c`. Source register: `07e668569d1ab32574bbef05dad1974ec2a2be7f`. Prospective holdout design: `23f19a3e8068f6687545df15917fce23498ba462`. Governance manifest: `fa54b4c984e3e2c4aaa40f8debc7980a6a8af9d2`.

The 34-source proposal is fail-closed: 0 requests, 0 bytes downloaded, 0 exact URLs pinned, 0 licenses cleared, 0 accepted modeling datasets, and 0 fitting permissions. Wave limits are ceilings for future individually reviewed requests, not blanket permission to contact any source. Licensing, historical coverage, publication timing and PIT validity remain unverified for listed leads. The prospective holdout remains design-only; no real boundary manifest exists.

This decision authorizes **only drafting** a Wave 1 exact-request manifest. It does not authorize network requests, data downloads, cache population, model-panel acceptance, feature/label generation, fitting/tuning/scoring, forecast capture, label release or options P&L.

The developer has drafted `research/phase7/PPR4_WAVE1_METADATA_REQUEST_DRAFT.json` (blob SHA `cf49868c077b006315b0576519933312333a6efb`) with three exact official documentation-page GETs (NSE index archive, NSE India VIX methodology, US Treasury feed documentation), each capped at 2 MiB, one request, no retries, no redirects, and no data-value retrieval. It remains unexecuted. This new draft needs a **second exact-snapshot review** before any request.

**Developer → Tester:** Review the exact Wave 1 draft blob `cf49868c077b006315b0576519933312333a6efb`; approve only these three documentation GETs or request changes.  
**Tester → Developer:** Keep all network/data/model/holdout permissions false until a second exact-snapshot decision is recorded.
