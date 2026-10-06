[object Object]

## Option-price field alignment

For an intraday-derived dataset aggregated to its final observed bar, the primary official reference is UDiFF `LastPric`, because it represents the last traded price available at the end of the session. Official `ClsPric` is retained as a secondary diagnostic because the exchange closing-price field can differ from the last trade. The primary data-quality gate therefore compares the derived final-bar close with `LastPric`; the `ClsPric` comparison is reported but is not used to silently rescue a failed primary check.
