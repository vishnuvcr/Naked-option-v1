# Phase 5 Family D Run #23 — Independent Tester Gate

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer run: #23 (`37642007846`)
Developer head used by workflow: `75ed6ddd90ac261364bf52570999d3c308fb37b5`
Artifact: `phase5-family-d-results`
Artifact ID: `11499450561`
Artifact SHA-256: `27ca6cbc6e1653d40e2d896a81211c97a8d5e70543cf37ad9f402597eee306d8`

## Review scope

This is an independent artifact/code/protocol audit of the fresh Family D execution required by the prior tester approval for the intraday D13-D15 correction. The review was performed without changing the developer implementation.

## Independent checks

### 1. Hosted execution integrity
- Workflow run #23 completed successfully.
- The single `family-d` job completed all registered steps: dependency installation, cached-data restoration, daily/intraday acquisition, regression tests, empirical suite, schema validation, and artifact upload.
- The regression test step completed successfully before the empirical suite.
- The immutable artifact was downloaded and its SHA-256 independently recomputed to the GitHub Actions artifact digest.

### 2. Coverage and schema
- Daily layer: 1,670 source rows; registered horizons {1,2,3,5,10}; D01-D15 present for every horizon.
- Intraday layer: 471,346 source rows; 8,441 frozen hourly decision-grid rows; registered horizons {5,15,30,60,120}; D01-D15 present for every horizon.
- Every one of the 150 D-method/horizon cells is marked EXECUTED.
- No registered D13-D15 intraday cell has zero observations. Intraday D13-D15 sample sizes are non-zero at every horizon (5m: 5,862; 15m: 5,870; 30m: 5,868; 60m: 5,570; 120m: 4,326).

### 3. Numerical consistency
For every one of the 150 cells, the independent checks confirmed:
- n = TN + FP + FN + TP;
- accuracy exactly reconciles to (TP+TN)/n;
- balanced accuracy exactly reconciles to the two class recalls;
- positive_rate exactly reconciles to (TP+FN)/n;
- probability-bin counts sum to n;
- bounded metrics are finite and lie in valid ranges;
- bootstrap lower/upper bounds are ordered and lie in [0,1].

No numerical contradiction was found.

### 4. D07 calibration isolation
Independent code review of the submitted implementation and the passing regression test confirmed:
- chronological eligible-training block;
- fixed 80% base-training / 20% calibration split;
- minimum base-training guard of 200;
- D01-D06 fit on base training for calibration probabilities;
- logistic meta-model fit only on calibration outputs/labels;
- D01-D06 refit on the complete eligible training block for test probabilities;
- post-cutoff label mutation test is present and passed.

No future-label use was found in the D07 construction.

### 5. D13-D15 sequence correction
Independent review confirmed:
- representations are generated on the full 1-minute intraday feature path;
- the 20-observation causal window is formed within session groups;
- representations are then row-aligned to the frozen hourly decision grid;
- session boundaries are explicitly segmented;
- the regression test checks finite warm-up after 20 observations, non-crossing of session boundaries, and invariance of an earlier representation to future-row mutation.

The fresh artifact confirms non-zero D13-D15 intraday coverage at every registered horizon. The specific run-20 defect (n=0 caused by constructing the sequence cache on the hourly matrix) is therefore not reproduced.

### 6. Walk-forward / cost scope
The submitted implementation retains the tester-approved 20-trading-session intraday refit cadence, hourly evaluation grid, exact H-minute labels, training-only transforms, and chronological purge. The Family D artifact is directional-model evidence only; option execution costs, Paytm Money brokerage, spread/slippage, and long-option economics have not been evaluated in this phase and remain mandatory later gates.

### 7. Non-blocking observation
D05 and D06 produce identical outputs in the submitted implementation because both are explicitly defined as the same provider-independent HistGradientBoosting surrogate with identical hyperparameters. This is consistent with the frozen protocol as currently written, but it means D05 and D06 should not be interpreted as independent empirical successes in any later multiplicity calculation beyond the pre-registered method count.

## Directional screening summary

The independent audit does not promote a strategy. The artifact is internally coherent and suitable for the next pre-registered research phase.

The strongest single directional ROC-AUC observed in this Family D run is daily D02 at H=1 with AUC 0.548831; the strongest intraday value is D02 at 5 minutes with AUC 0.535101. These are descriptive screening values only and have not passed multiple-testing, economic, robustness, or fresh-forward gates.

## Disposition

**PASS WITH SCOPED RESTRICTIONS — FAMILY D EMPIRICAL ARTIFACT**

The artifact passes the technical empirical gate. This does **not** authorize:
- declaring any D method a winning strategy;
- skipping multiple-testing/robustness controls;
- skipping option selection and realistic execution-cost analysis;
- opening the final holdout;
- advancing to final strategy promotion without the downstream tester gates.

The developer may proceed to the next registered Phase 5/Phase 6 work only after recording this gate and preserving the immutable artifact lineage.

## Tester → Developer

Record this gate on the developer branch, preserve run #23 as the accepted Family D technical artifact, and do not select D02/D09/etc. from these descriptive maxima as a promoted strategy. Update the developer status/logs before any phase transition. The next work must remain within the pre-registered finite method plan and continue to enforce independent tester review.

## Developer → Tester

On the next submission, independently review the updated developer status/logs, the exact artifact lineage, and the proposed Phase 6/next-family scope before any subsequent progression. 
