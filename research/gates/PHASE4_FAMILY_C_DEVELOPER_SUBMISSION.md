# Phase 4 Family C Developer Submission

Family C statistical/time-series methods are frozen in `research/phase4/FAMILY_C_PROTOCOL.md`.

C01-C09 are implemented as registered models/filters; C10-C11 remain explicit BLOCKED_DATA until the event and cross-market PIT layers are materialized.

Developer instruction to tester: independently inspect the online filtering logic, training/test boundaries, state initialization, probability calibration and result denominator reconciliation from the Family C artifact before allowing Family D to start.
