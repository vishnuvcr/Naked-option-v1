# Phase 2C Historical FII/DII Source Decision

## Status: QUARANTINED

The live NSE `/api/fiidiiTradeReact` endpoint is suitable for current snapshots. The exact combined historical FII+DII cash-market series is not yet a stable, demonstrated public API contract in the current source universe.

Free-source attempts documented in public open-source implementations show:
- the legacy NSE archive endpoint was historically used for backfill;
- the legacy endpoint is no longer a reliable live historical endpoint;
- current NSE live API remains useful for ongoing snapshots.

The research will not invent or forward-fill a historical DII series.

### Allowed uses before the gap is closed

- current/live FII/DII snapshot for monitoring;
- official/point-in-time FPI/FII history where the scope is explicitly labeled;
- historical DII-dependent predictors are disabled until a free reproducible series is validated.

### Paid-data trigger

A paid source is still prohibited. This quarantine remains the preferred treatment until a free source with reproducible publication timing is validated.
