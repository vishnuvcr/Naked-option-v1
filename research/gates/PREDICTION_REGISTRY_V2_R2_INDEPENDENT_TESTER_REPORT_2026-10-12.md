# Independent Tester Report — Prediction Registry V2 R2 (2026-10-12)

**Decision: REQUEST CHANGES — registry gate remains BLOCKED.**  
**Scope:** artifact auditability and scientific design review only. No model fitting, no holdout access, no performance claims.

## Evidence inspected
- Human index on developer branch: `research/registry/METHOD_REGISTRY_V2_R2.md`, blob `dd6abf4283c79068eb6603100b50b153cf1485c9`.
- Label manifest: `research/registry/PREDICTION_LABEL_MANIFEST_V2_R2.json`, blob `eedd0852414a9ef6ec56d0e0af0152bddc9bf2be`.
- Configuration manifest: `research/registry/PREDICTION_CONFIG_MANIFEST_V2_R2.json`, blob `427e92cc5eb44a126e327da7b7eb305a3338096b`.
- Method registry JSON blob is not readable through the connected GitHub file fetch (returned empty content); raw fetch reports oversized/unsupported. The configuration manifest points to 2,000-record shards, which are also not independently available in a reliably inspectable form here.
- Issue #25 has no tester comments at inspection time.

## Findings

### T1 — Reproducible independent audit cannot be completed (BLOCKER)
The stated 1,000 method definitions and 8,000 configurations cannot be independently reconstructed and verified from small, accessible source artifacts in this review. The human index and summary counts do not prove method uniqueness, config uniqueness, parent linkage, or SHA-256 integrity. Do not infer PASS from counts in prose.

### T2 — Cartesian product does not establish 1,000 scientifically valid methods (BLOCKER)
The registry is defined as 20 model/architecture families × 10 feature representations × 5 inference operators. That arithmetic yields 1,000 IDs, but does not prove all combinations are compatible or materially distinct. For example, conformal-set decisions require a valid calibration procedure and exchangeability/temporal validity assumptions; survival first-passage outputs require a well-defined time-to-event estimand and compatible inference mapping; HMM/regime and Bayesian/dynamic models require family-specific fitting and uncertainty semantics. A generic adapter cannot make every pairing valid by declaration alone. Provide a compatibility matrix with explicit ALLOW/BLOCK reasons, family-specific output contracts, and a semantic distinctness rule. Count only valid combinations toward the 1,000 target; if fewer survive, add scientifically justified methods rather than invalid cross-products.

### T3 — Labels and sample eligibility are not frozen enough for execution (BLOCKER)
The labels refer to zero/flat treatment and label-manifest rules, but exact numerical flat-return tolerance, session-boundary handling, missing-data policy, minimum class support, minimum observations per fold, purging/embargo details, and block-bootstrap length need a hash-pinned, pre-run specification. The label manifest is explicitly draft. These must be approved before any empirical fitting.

### T4 — Statistical-control plan needs executable artifacts (BLOCKER)
The R2 amendment describes log loss versus a training-only baseline, Benjamini–Yekutieli FDR q=.05, and paired chronological block bootstrap with 10,000 replicates. This report cannot verify a frozen family/stratum multiplicity grouping, baseline implementation, bootstrap block-length rule, missingness/sample freeze, or deterministic seed policy in executable config. Add machine-readable preregistration and tests. No repeated tuning on an untouched holdout.

### T5 — Resource/restart evidence is missing from the accessible artifacts (BLOCKER)
Provide a deterministic dry-run using synthetic data, wall-time/memory estimates per family and full sweep, checkpoint/restart test, and failure logging. The registry gate and synthetic-runner gate both need tester approval before empirical execution.

## Required developer actions
1. Publish auditable method shards (recommended ≤25 methods/file) and config shards (recommended ≤100 configs/file), each with exact SHA-256 computed over documented canonical bytes.
2. Publish a compact top-level index containing path, byte count, record count, first/last ID, and SHA-256 for every shard; include a verifier that recomputes all hashes and counts from the checked-out repository.
3. Add a family × representation × operator compatibility matrix and count only allowed, meaningfully distinct combinations.
4. Freeze label, missingness, sample eligibility, fold/purge/embargo, multiplicity, bootstrap, and seed policies in machine-readable preregistration.
5. Run the verifier and synthetic restart/resource tests; submit exact commit SHA and artifacts for a fresh independent review.

## Gate decision
**REQUEST CHANGES.** Registry approval is not granted. Empirical model fitting, strategy selection, and untouched-holdout access remain prohibited. This is not a finding that prediction is impossible; it is a finding that the current registry has not yet passed scientific and reproducibility gates.
