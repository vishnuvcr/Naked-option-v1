# Logistic family synthetic gate — 2026-10-13

Status: PASS_SYNTHETIC_ONLY.

Hosted workflow: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38420549917

- Five synthetic logistic adapter tests passed.
- Four synthetic chronological OOF calibration tests passed.
- Python compilation and source checks for market-data/holdout references passed.
- Tests used generated synthetic samples only; no market data loaded and no holdout accessed.
- This gate validates the adapter contract only. It does not approve any registry method for empirical fitting and does not establish prediction performance.

Next gate: add a method-family-specific contract tying each allowed PM ID to exact adapter parameters, required tests, feature representation, calibration contract and preregistered label support; independent review must pass before any empirical run.


## Probit adapter extension
- Updated hosted workflow [38421293871](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38421293871) passed. The gate now runs 5 logistic tests, 4 chronological calibration tests, and 4 probit adapter tests, plus compilation and source checks.
- Probit tests cover valid probability output, training-only standardization, invalid/single-class training rejection, pre-fit prediction rejection, and non-finite inputs. Synthetic data only; no market data or holdout access.
