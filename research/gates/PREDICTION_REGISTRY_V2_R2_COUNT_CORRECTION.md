# Registry V2 R2 count correction

The human-readable index initially said 16,000 configurations. This was inconsistent with the actual construction: 1,000 methods × 2 target strata × 2 lookbacks × 2 complexity presets = **8,000 configurations**, organized into four shards of 2,000. The index has been corrected in commit `c37180afdf9d0c3c8cf545e84b3670534c609b7d`.

This documentation correction does not mean the registry has passed independent review. Empirical execution remains blocked until the tester verifies the machine-readable files, fingerprints, method compatibility, labels, and configuration completeness.

**Developer → Tester:** include this count correction in the R2 audit; independently check all files and hashes.

**Tester → Developer:** report PASS/REQUEST CHANGES only after reading and reconciling the actual artifacts.