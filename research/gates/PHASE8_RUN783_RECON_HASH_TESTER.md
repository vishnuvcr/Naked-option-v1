# Phase 8 Run #783 — Reconstruction Hash-Integrity Tester Request Changes

**Developer head reviewed:** `59cbac120b08c0961c5919f364994d392366e61a`  
**Hosted run:** Research Protocol Check #783 (`37815994871`)  
**Status: REQUEST CHANGES**  
**Empirical option P&L:** BLOCKED

## Finding

All upstream Phase 8 gates passed:
- protocol;
- free-source NSE/BSE/Hugging Face audit and reconciliation;
- immutable Run #654 artifact verification;
- workflow-contract regression;
- reconstruction harness regression;
- execution-engine regression.

The forecast reconstruction then failed at the source-integrity check:

```
RECONSTRUCTION_ERROR: Phase 7 source blob mismatch; the accepted Run #654 implementation is not present
```

Independent source comparison shows the current `scripts/run_phase7_ensemble.py` blob SHA is exactly the frozen manifest value:

`399ad338a409b6faf56c3ee243f2643cc89f162a`.

The defect is in `scripts/reconstruct_phase7_predictions.py::git_blob_sha()`:

```python
header = b"blob " + str(len(data)).encode("ascii") + b"\\x00"
```

The final term is the two literal characters backslash-x followed by two zeros, not the Git blob header's required NUL byte. Therefore the checker computes a non-Git blob hash and falsely rejects the accepted source.

## Scientific assessment

- This is a production reconstruction-integrity defect.
- It creates a false negative at the exact immutable-source gate; it must not be bypassed.
- Run #783 is non-evidence for forecast reconstruction.
- No forecast panel was generated and no option P&L was generated or accepted.
- The underlying frozen source blob itself is correct and matches the manifest.

## Required correction

Change only the hash-header construction to use a real NUL byte:

```python
header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
```

Add deterministic regression coverage that computes the Git blob SHA for a known byte string and matches a precomputed expected hash, preventing recurrence.

Do not change the frozen Run #654 source, forecast methodology, artifact digest, or empirical authorization.

**Tester → Developer:** correct the Git blob hash calculation and its regression test, log this defect, obtain fresh tester approval, and rerun the complete Phase 8 hosted workflow/data/reconstruction gate. Empirical execution remains blocked.
