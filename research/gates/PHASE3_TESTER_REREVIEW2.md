# Phase 3 Tester Re-Review 2 — REQUEST CHANGES

## Independent audit after prior corrections

| Area | Result | Finding |
|---|---|---|
| Volatility units | PASS | No annualization; 20-observation same-frequency window is explicit. |
| Triple-barrier construction | PASS | Fixed, non-updating barriers are explicit. |
| Baseline feature specifications | PASS | Main periods/formulas/Logit hyperparameters are now deterministic. |
| Option cost round trip | PASS | Entry + exit costs are explicitly required. |
| **Horizon consistency** | **FAIL** | "Same-frequency" is currently defined relative to the decision grid, but the label horizons are 5/15/30/60/120 minutes. A 5-minute label needs a volatility reference built from 5-minute returns, not 20 one-hour decision-to-decision returns. This is a material unit/horizon mismatch. |
| Triple-barrier path frequency | REQUEST | The protocol should state that barrier crossing is evaluated at the finest available observation frequency after decision time, while the volatility reference is horizon-matched. |
| Option break-even delta units | PASS WITH CLARIFICATION | State explicitly that per-unit costs are per option unit; brokerage/fees are divided by traded quantity only after the exact transaction bill is computed. |
| Protocol determinism | PASS AFTER CORRECTION | No hyperparameter search remains in baselines. |

## Required correction

Define for every horizon H:

`sigma_H(t) = std of the preceding 20 non-overlapping H-length log returns ending no later than t`.

For 5/15/30/60/120-minute labels, this creates a horizon-matched volatility reference. For 1/2/3/5/10-session labels, use the preceding 20 H-session returns. The reference is frozen at decision time.

For triple-barrier labels:
- use `sigma_H(t)` for the barrier width;
- inspect the full finest-available post-decision path to detect first barrier crossing;
- do not recompute barriers after entry.

## Gate decision

**REQUEST CHANGES**

This is the last label-protocol correction required before Phase 3 data execution.

## Tester instruction to developer

Apply the horizon-matched volatility definition and explicit finest-frequency barrier scanning rule, append the correction to the research/error logs, and resubmit for final Phase 3 tester gate. No baseline results yet.
