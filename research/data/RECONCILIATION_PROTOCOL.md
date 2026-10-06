[object Object]

## Secondary derived-source price corroboration gate

Because an independently derived 1-minute dataset and an exchange EOD reference are not guaranteed to share an identical terminal trade timestamp, two price-quality metrics are retained. The strict diagnostic remains a pre-declared 0.25%/tick agreement fraction and is never erased. A derived source may be used only as **secondary corroboration**, not as a canonical price source, when at least 95% of matched near-ATM contracts are within 1% relative error and no matched contract exceeds 3% relative error, with the median relative error also reported. Any failed source remains non-canonical. These tolerances govern corroboration only; executable strategy backtests must use canonical/persisted exchange-quality prices and their own bid/ask/slippage model.
