# Availability and Alignment Policy

## Default conservative availability

| Data class | Usable at decision time when |
|---|---|
| NSE/BSE intraday | timestamped observation is <= decision timestamp |
| NSE/BSE EOD | exchange publication is known to have completed; for same-day intraday decisions, EOD is not usable |
| India VIX | published observation timestamp <= decision timestamp |
| FII/DII | publication/availability timestamp <= decision timestamp; otherwise next-session default |
| Global equity close | local exchange close + conservative publication delay < NIFTY decision time |
| FX | quote/reference observation <= decision time |
| US rates | release timestamp <= decision time; daily Treasury rates default to next Indian session unless release timing is proven |
| Gold/crude | timestamped observation <= decision time; daily closes default to next-session use unless release timing is proven |
| News | article/event publication timestamp <= decision timestamp |
| Corporate actions | announcement time for information; effective date for adjustment |

## Overnight feature rule

A global-market feature used at the NIFTY open may use only the information that was already observable before that NIFTY open. A global close that occurs after the decision time is excluded.

## Cross-source precedence

1. Official exchange/regulator source.
2. Official underlying/index provider source.
3. Free independently documented fallback.
4. Derived community dataset only for gap fill after reconciliation.

Derived sources never overwrite an official source without a documented data-quality reason and row-level provenance.

## Revision handling

Later revisions create a new snapshot/version. They do not overwrite the original historical availability record.
