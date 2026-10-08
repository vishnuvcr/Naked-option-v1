# Phase 7 Run 628 Empirical Failure — Tester Review

Status: REQUEST CHANGES.

Hosted Run 628 (`37717789013`) passed the Phase 7 regression suite, but empirical execution failed after ~19 minutes at the daily second horizon:

`KeyError: ('2', 'E01')`

Root cause: `capture_scope()` iterates over horizons but assigns `H=horizons[0]` inside the metrics hook, so all captured method arrays are stored under the first horizon key. The outer Phase 7 run later requests the second horizon and correctly fails.

Impact:
- Run 628 is NON-EVIDENCE.
- No artifact or scientific metric was accepted.
- This is a production mapping defect, not a data failure.

Required correction:
- bind each metrics call to the actual current `H` being evaluated, not `horizons[0]`;
- add a regression assertion that all registered horizon keys are captured for E01 and at least one non-E01 method;
- preserve all frozen Phase 7 scientific rules unchanged.

Tester -> Developer: correct only the horizon-capture mapping, log Run 628, add regression coverage, and resubmit for tester approval before rerunning empirical execution.