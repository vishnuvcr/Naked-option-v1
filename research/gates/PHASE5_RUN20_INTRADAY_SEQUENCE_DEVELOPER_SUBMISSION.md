# Phase 5 Run #20 Intraday Sequence Correction — Developer Submission

Run #20 (37626101730) completed successfully but tester identified that intraday D13-D15 were evaluated with n=0 because sequence windows were built on the hourly decision matrix.

Implemented correction:
- D13-D15 intraday representations are now precomputed from the full 1-minute feature path.
- Session groups are taken from the full intraday source rows.
- The causal representations are mapped exactly to the frozen hourly decision indices before model fitting/prediction.
- The 20-observation warm-up, causal direction, session-locality, hourly decision grid, 20-session refit cadence, labels, seed, and architectures remain unchanged.
- Protocol wording was amended to make this data-path definition explicit.
- Regression tests now verify finite 20-observation warm-up, session boundaries, and invariance to future-row mutation.

Run #20 remains non-evidence. A fresh hosted Family D run will only be launched after tester approval of this submission.

Developer → Tester: independently review the code/protocol/test diff for causality, session-locality, row alignment and preservation of the frozen scientific definitions.

Tester → Developer: approve only if the 1-minute representation mapping is mathematically causal and no future information or cross-session rows can enter a prediction.