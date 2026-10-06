# Phase 2C Gate

Phase 2C is the bulk-data/PIT completion gate.

## Must pass

- [ ] Frozen research windows committed.
- [ ] All official NSE year batches 2019-2026 acquired or every missing date explicitly classified.
- [ ] Legacy-to-UDiFF boundary reconciled.
- [ ] NIFTY-only Parquet manifests built for every acquired year.
- [ ] Zero duplicate canonical option keys.
- [ ] Core field missingness quantified and accepted.
- [ ] Effective-dated lot-size regimes documented; unresolved regimes quarantined.
- [ ] India VIX historical series acquired/validated.
- [ ] Global daily series acquired/hashed; availability rule validated.
- [ ] US 10Y source working and hashed.
- [ ] FII/DII historical availability either validated or explicitly quarantined with a free-source gap statement.
- [ ] Intraday option source is contract-identifiable over a representative date panel.
- [ ] PIT leakage suite passes on actual data.
- [ ] Raw cache hit behavior demonstrated on a repeat run.
- [ ] Tester independently reproduces the data-quality reports.

## Blockers

A failing derived source does not block the canonical EOD dataset if the source is explicitly quarantined. A failure in official NSE parsing, PIT integrity, duplicate detection, or unresolved date coverage is a blocker.

## Only after this gate

Phase 3 labels and baseline direction tests may begin.
