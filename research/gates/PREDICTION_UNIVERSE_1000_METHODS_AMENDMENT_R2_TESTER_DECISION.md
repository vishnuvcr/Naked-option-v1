# Tester decision — amendment R2

- Decision: **PASS WITH SCOPED RESTRICTIONS**
- Reviewed branch: `phase-08-prediction-developer`
- Reviewed blob SHA: `96b8b3d34fe7f038795247da007ba40ed704a60d`
- Scope: protocol only
- Registry V2 preparation: **Authorized**
- Empirical prediction runs: **Not authorized**
- Untouched holdout access: **Not authorized**
- Strategy selection from Phase 8 results: **Prohibited**

Required next gate: tester review of exact registry/configuration manifest, method fingerprint uniqueness, full configuration coverage, resource estimate, and synthetic runner/restart tests. See the full report for scoped restrictions.

**Tester → Developer:** submit registry and synthetic validation evidence; no empirical run yet.
**Developer → Tester:** review the exact frozen manifest and validators before authorizing any batch.
