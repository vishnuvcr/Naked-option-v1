# Tester Review — Phase 8 cached composite preflight R1

**Decision: PASS WITH SCOPED RESTRICTIONS — proposal only**  
Date: 2026-10-11  
Proposal commit: `1abaa7cd92bbbc7c89294e7b63c0067e2b615b13`  
Proposal blob: `7a6a2d557a04861fa8203d5083c981ebbff20b0f`  
Scope blob: `3b4c06faf439c436c2e555a41e6c8676ca6e1f68`

## Independent input checks

1. **Forecast lineage checks out.** Run #994 `37957677656`, source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`, artifact `11638738288`; archive SHA-256 `3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9`; embedded manifest `f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091`; aggregate `96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39`. Accepted validator run 38157819076 reproduced all 10 forecast cells/50,555 rows at 1e-9.
2. **Composite lineage checks out against the repository's existing offline export path.** Run `38131641336`, artifact `11698879857`, name `nifty-1m-derived-repaired-r2-38126168547`; canonical CSV SHA-256 `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`; 8,999,865 rows, 47 columns, 61 encrypted monthly parts. The recorded gzip SHA is provenance only because recompression can change gzip-header bytes.
3. Exact encrypted monthly part checks are appropriate and stronger than validating only a downloaded merged file. The existing decrypt script validates each encrypted SHA and the post-decrypt gzip SHA before merging. The implementation must additionally validate all part sizes, safe basenames, dataset identity and summed part rows before any plaintext is opened.
4. Running the Phase 8 runner in `--mode preflight` cannot produce empirical P&L. The runner marks all 4,800 configurations INELIGIBLE by construction until the strict fixed-contract panel gate passes. The expected finding—no explicit lot-size/tick-size columns and no demonstrated full historical bid/ask/contract-master coverage—must remain a data-readiness blocker, not be turned into a model/strategy performance conclusion.
5. Temporary handling is acceptable only if the secret is never printed/written, plaintext stays under runner temp, outputs contain no raw records, and unconditional cleanup verifies deletion even when preflight fails.
6. No new exchange/vendor/Hugging Face source requests are needed or authorized by this proposal. Downloading the already pinned Actions artifact and using the existing HF_TOKEN-derived decryption key are within scope.

## Restrictions and required tests

- This approval is proposal-only. The exact implementation workflow still requires synthetic contract tests, secret/permission review, exact tester code/hash review, and a hosted preflight run.
- Check the artifact API ID/name/run/commit before using `actions/download-artifact`; downloading by name/run alone is insufficient.
- Verify the merged decoded CSV hash `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`, rows=8,999,865, columns=47, row counts OPTION=8,490,723 and SPOT=509,142.
- Keep all 4,800 grid cells and four scenario summaries present. Required terminal status fields: `strict_fixed_contract_execution_ready=false`, `empirical_option_execution_authorized=false`, `empirical_pnl_generated=false`, `strategy_promotion_authorized=false`.
- No final-holdout reads, saved forecasts refit, real P&L, winner selection, or strategy promotion.
- Preserve the known data-quality limitations and exact anomaly history in the report.
- The tester role is repository-branch separated but, in this ChatGPT session, is not a separate external human/model instance.

## Authorized next step

Developer may implement the dedicated cached-composite metadata-preflight workflow, its synthetic tests, artifact/status validation and unconditional temporary-file cleanup. Following CI, submit exact code/workflow blob hashes for tester code review. Only after that may one hosted cached-artifact preflight execute.

**Tester → Developer:** implement the R1 preflight exactly as proposed; run only synthetic regressions first; submit the exact workflow/code hashes and prove that no P&L/holdout/source request is reachable.  
**Developer → Tester:** independently inspect the exact implementation and CI run, then return an explicit exact-hash decision before the one cached-composite preflight.
