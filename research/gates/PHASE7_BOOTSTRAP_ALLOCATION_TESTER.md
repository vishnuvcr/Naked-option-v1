# Independent Tester Report — Phase 7 bootstrap sampler allocation optimization

**Decision: PASS WITH SCOPED RESTRICTIONS — sampler equivalence and hosted regression only**

Date: 2026-10-09  
Developer commits reviewed:
- `4f959a0ba46929fe427bc3db27d02e57f88687fa1` — optimized sampler
- `682eadf2a9eb4de250bc3db27d02e57f88687fa1` — regression tests

Hosted evidence:
- [Run #924](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37914896724): Phase 7 regression job completed successfully; empirical job was queued at the latest check.
- Run #925 (`37914905848`) regression job completed successfully; downstream gate/job remained queued at the latest check.

## Independent review

1. Legacy implementation materialized all overlapping blocks as a Python list on each bootstrap replication. The replacement samples a start index uniformly from `0..n-L` and materializes only selected blocks.
2. Both versions call `rng.integers` with the same lower bound, upper bound, and output size; selected start indices therefore remain bit-for-bit identical for the same generator state. Each selected block is still `arange(start, start+L)`; concatenation and truncation are unchanged.
3. Regression coverage compares optimized output to an embedded legacy reference using fixed seed 42 at daily/intraday-like sizes and edge cases `(3,20)`, `(1,1)`, and `(0,20)`.
4. The hosted regression job passed. No scientific definition, seed, block length, replication count, candidate forecast, or inference formula was changed.

## Restrictions / next gate

- This approval applies only to sampler equivalence and regression tests.
- It does not accept any empirical run or result. Run #852 was still reported active, while the optimization commits caused two further workflow attempts; run ordering/duplication must be reconciled.
- Before interpreting any result, the developer must identify the single completed empirical run and independently audit its immutable artifact, all ten panels, provenance hashes, source-derived labels/returns/timestamps, aggregate metrics and family-level inference.
- The Phase 8 manifest and 4,800-cell option grid remain blocked until the real artifact audit passes.
