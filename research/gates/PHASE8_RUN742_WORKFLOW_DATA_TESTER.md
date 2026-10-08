# Phase 8 Workflow/Data Gate — Independent Tester REQUEST CHANGES

**Tester branch:** `phase-08-tester`  
**Developer head reviewed:** `132c234fc70355ba8c0034b9e2e8a0c4b776affb`  
**Hosted run:** Research Protocol Check #742 (`37815078803`)  
**Status: REQUEST CHANGES**  
**Empirical option P&L:** BLOCKED

## Finding

The Phase 8 hosted regression job failed in the reconstruction regression before the reconstruction engine or empirical option grid could run.

Failure:
```
NameError: name '__file__' is not defined
```

Location:
`scripts/test_phase8_reconstruction.py::test_recursive_compare_tolerance`

The regression test parses `scripts/reconstruct_phase7_predictions.py` into an AST and executes it with:
`exec(compile(tree, str(SRC), "exec"), ns)`.

The executed production source reads `Path(__file__).resolve().parents[1]`, but the test namespace does not define `__file__`.

## Scientific assessment

- This is a regression-harness defect, not evidence of a production reconstruction defect.
- The failing test prevents the required gate from passing, so the workflow/data gate cannot be accepted.
- The source-audit job independently reached the NSE/BSE/Hugging Face reconciliation stage and had not failed at the time the regression job failed.
- No Run #654 reconstruction, option-selection P&L, or 4,800-cell execution was authorized.
- Run #742 is non-evidence for Phase 8 empirical results.

## Required correction

Correct the regression harness so AST-executed production source receives an explicit `__file__` value corresponding to `SRC`. The correction must remain test-only, preserve the production reconstruction implementation, and include a deterministic regression assertion proving the harness executes the source with the expected path context.

After correction, rerun the full hosted workflow/data gate. Tester must independently review:
1. workflow contract;
2. Run #654 artifact digest verification;
3. source audit/reconciliation;
4. reconstruction regression;
5. execution-engine regression;
6. forecast-panel validation;
7. empirical authorization remains false.

**Tester → Developer:** correct only the regression-harness path-context defect, archive the error, and resubmit the complete hosted workflow/data gate. Do not run the 4,800-cell option grid.
