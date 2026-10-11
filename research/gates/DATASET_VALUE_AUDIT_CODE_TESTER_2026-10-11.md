# Tester Report — Offline Dataset Value Auditor Code Gate

- Review date: 2026-10-11 UTC
- Branch: `phase-07-tester`
- Exact developer commit reviewed: `346b959f43ad8f97a54a3ecbddab55c54df6f2ac`
- Offline composite test run: [38121967789](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38121967789) — success (includes parsing the new audit workflow and its self-test workflow step)
- Protocol check: [38121967994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38121967994) — success
- Reviewer independence caveat: this tester-role report was created in the same connected assistant session; it is not an independent human identity or independent AI review. The repository's HF AI reviewer was previously unavailable with HTTP 402.

## Exact files reviewed

| File | Blob SHA |
|---|---|
| `scripts/audit_nifty_1m_composite_values.py` | `65a281e56f60e42774b83924d9dbc8c2cd164ba9` |
| `scripts/test_audit_nifty_1m_composite_values.py` | `04dd0ffe347f39e1da56c78b3649c028e98cb10d` |
| `scripts/decrypt_nifty_1m_composite.py` | `6ba27b65548b9197e0db35deeafcedbade6ca445` |
| `requirements-composite.txt` | `8c74241f2035a3e388087078be5e5aaf846addca` |
| `.github/workflows/dataset-value-audit.yml` | `00436a389ee82fd9adde980bfef5515f1e420b49` |
| `.github/workflows/phase-07-nifty-1m-composite-tests.yml` | `db7666905fb97f703784e7f3e7bda8958b106715` |

## Findings and checks

1. **Exact artifact scope — PASS.** The value-audit workflow is pinned to existing Actions run `38116772719` and artifact `11693866249`; it verifies the fixed dataset ID, 57 parts, expected manifest counters, each encrypted file's byte size and SHA-256, and the manifest row sum before decryption. It makes no Dhan/market-data requests.
2. **Authenticated decryption — CODE PATH REVIEWED, NOT YET EXECUTED.** The workflow passes `HF_TOKEN` only to the repository decryptor, which checks each encrypted hash and decrypted gzip hash. Actual secret availability and decryption outcome must be established by the hosted workflow.
3. **Semantic checks — TEST PASS.** The row auditor checks monthly schemas/counts, UTC/IST epoch consistency, session-date/month consistency, composite duplicate keys, duplicate spot timestamps, OHLC consistency, finite numeric representations, row types, spot-join status counts and missingness summaries. It writes aggregates only, with no sampled price values.
4. **Regression suite — PASS.** Eight unit tests (seven data fixtures plus one workflow-scope/cleanup test) cover a valid two-row fixture, invalid OHLC, session-date mismatch, subsecond timestamp mismatch, duplicate composite key, manifest row-count mismatch, schema rejection, and sanitized output. The exact-snapshot hosted offline workflow passed.
5. **Plaintext handling — PASS BY WORKFLOW DESIGN; RUNTIME CLEANUP UNVERIFIED.** Decrypted monthly CSV.GZ files and the duplicate-key SQLite database are written under the ephemeral runner temp directory. The workflow deletes them and uploads only `DATASET_VALUE_AUDIT_RESULT.json`. This requirement still needs confirmation in the actual hosted run logs.
6. **No new authority — PASS.** The report's permission string keeps model fitting/scoring, holdout access, and strategy/P&L tests unauthorized even on a structural pass.

## Verdict

**PASS WITH SCOPED RESTRICTIONS — code/tests and offline-only workflow design.**

This verdict approves the audit implementation to attempt validation of the existing encrypted artifact. It does **not** establish that decryption succeeds, that the row-level data passes, that the dataset is complete, or that it is ready for prediction modeling. The manifest is already marked `PARTIAL_GRID` and `SPOT_GAPFILL_PARTIAL`; six gap-fill windows failed and 899,551 option rows lack matched spot bars. Any resulting audit must retain these restrictions.

## Required next action

Run the exact workflow on `main` using only artifact 11693866249 and the existing decryption secret. Inspect the generated sanitized report and cleanup log. If audit status is `FAIL` or `AUDIT_ERROR`, keep fitting/holdout/strategy gates closed and fix only findings supported by the report. If it returns `PASS_WITH_COVERAGE_RESTRICTIONS`, a separate exact-snapshot model-gate decision is still required.

**Tester → Developer:** Promote only these exact reviewed code/workflow blobs; verify the report after the fixed-artifact run and do not widen empirical permissions.

**Developer → Tester:** Independently inspect the hosted result status, summary metrics and cleanup evidence; report any runtime flaw on `phase-07-tester`.


## Workflow-definition defect found and corrected

The first published workflow on `main` failed before any job started; its job list was empty, so no artifact download, decryption, or row-level audit was executed. Root cause: the self-test insertion had omitted the named step header for the artifact-download action, causing the action's `uses:` to coexist with the previous `run:` in the same step definition. The corrected developer snapshot restores the step boundary. A regression test now asserts the expected download step block and that offline tests occur before artifact access.

- The first regression assertion itself initially encoded literal backslash-n characters instead of Python newline escapes, so [run 38121943728](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38121943728) failed only that test. The test source was corrected, and the full offline suite passed at [run 38121967789](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38121967789).
- Protocol check: [run 38121967994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38121967994) — PASS.
- Exact reviewed workflow blob SHA: `00436a389ee82fd9adde980bfef5515f1e420b49`.

These corrections are code/test-only. The deployment on `main` still needs to be updated from the reviewed blob, and a successful hosted run must prove artifact download, authenticated decryption, semantic audit, and temporary plaintext cleanup before the research can claim value-level validation.


## Runtime result — fixed artifact scan (2026-10-11)

- Hosted run: [38122043916](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38122043916)
- Artifact retrieval, encrypted hash/size preflight, authenticated decryption, and the row-level audit step completed successfully.
- Sanitized report: [DATASET_VALUE_AUDIT_RESULT.json](https://github.com/vishnuvcr/Naked-option-v1/blob/main/research/data/DATASET_VALUE_AUDIT_RESULT.json), status **FAIL**.
- Row totals reconcile: 8,490,723 option + 403,664 spot = 8,894,387. Monthly manifest counts reconcile. Observed join counts reconcile: 7,591,172 exact timestamp matches and 899,551 unmatched.
- Findings: 224 invalid OHLC rows among option-joined NIFTY candles, 9 invalid standalone spot OHLC rows, and 11 negative option-volume values. Composite duplicate keys and duplicate spot timestamps were both zero. These are aggregate counts; the audit report contains no price values.
- Coverage remains limited: partial historical option grid; six failed gap-fill requests; 899,551 unmatched option rows; 42 option-session dates with no spot rows in the assembled spot set. Greek fields/time-to-expiry are unpopulated across the option rows, so those features are not currently usable.
- Workflow runtime cleanup step failed due to a shell heredoc delimiter syntax error, despite the code attempting to remove temporary plaintext. The step did run `rm -rf` on its designated temp directories before failing. The run does not provide a successful cleanup verification; fix and rerun cleanup before declaring the operational gate passed.
- The semantic scan step itself completed with exit code 0, but its report correctly returned FAIL. The final workflow gate failed closed. No model fitting/scoring, holdout access or strategy test was performed.

### Tester verdict update

**FAIL — data quality and workflow cleanup gate not passed.** The current report supports a precise next task: diagnose the 233 OHLC violations and 11 negative-volume rows without publishing market prices, fix the cleanup shell block, add regression tests, and rerun against the same already-collected artifact. Do not fit prediction models until the issues are resolved and a separate exact-snapshot gate is approved.

**Tester → Developer:** Fix the cleanup step and investigate the 244 price/volume findings with sanitized row IDs, dates, and violation categories; do not silently drop or rewrite source rows.

**Developer → Tester:** Review the next exact code SHA, confirm cleanup in hosted logs, and validate any proposed exclusions/corrections before they enter the modelling dataset.
