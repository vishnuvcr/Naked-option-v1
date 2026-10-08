# Phase 7 Run 628 Horizon-Capture Correction — Tester Approval

Status: PASS.

Tester independently reviewed developer commit `31a39d2b4448e33e24730f1df61ca41df129a7c4`.

Verified:
- production `capture_scope` now binds each captured metric call to the current horizon `H` instead of `horizons[0]`;
- the malformed first regression assertion was removed before hosted rerun;
- the new regression monkeypatch directly exercises `capture_scope` across multiple horizons and asserts E01 keys for 1, 2 and 3;
- no scientific Phase 7 definition, baseline, regime rule, or family-bootstrap rule changed;
- Run 628 remains non-evidence.

Tester disposition: PASS.

Tester -> Developer: archive this gate and trigger the next hosted Phase 7 regression. Empirical execution remains conditional on regression passing.