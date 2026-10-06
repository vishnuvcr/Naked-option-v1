# Phase 2C Source Gaps and Quarantine Register

## Combined historical FII/DII

The live NSE `fiidiiTradeReact` endpoint is suitable for current snapshots but does not expose a reliable historical date-query contract in the current implementation. Public open-source implementations document the legacy FII/DII archive path as historical but obsolete/dead or require manual archive seeding.

Decision:
- keep the live NSE snapshot source;
- use official/independently documented historical FPI/FII sources only when scope and publication timing match;
- do not synthesize a fake DII history;
- historical DII-based predictors are quarantined until a free, verifiable point-in-time history is obtained.

## India VIX

NSE exposes an historical VIX API path of the form:

`https://www.nseindia.com/api/historicalOR/vixhistory?from=DD-MM-YYYY&to=DD-MM-YYYY&csv=true`

Phase 2C acquires this in chunks and stores the original response hash. The route is treated as a source-access implementation detail, not as a permanent guarantee.

## Intraday option source

S08 is useful for cross-validation but is not canonical. Its observed practical corroboration passed in a pre-declared near-ATM universe; its spot series was unavailable for the selected rows. S08 may therefore be used only with a separately validated underlying series.

S31 dynamic ATM files are not contract-identifiable enough for executable contract-level backtesting and remain quarantined.

## US 10Y

The previous Treasury landing URL returned 404. Phase 2C uses the Federal Reserve/FRED DGS10 daily series as the free official-rate source. The FRED series is daily, sourced from the Board of Governors, and has a downloadable CSV endpoint. citeturn933765search2turn933765search3

## Current decision

No paid source is required at this stage.
