# Developer → Tester Review Request — Extension 2 Gate A Sampler v2 (Current Corrected Snapshot)

**Status: REQUESTED — approval manifest absent; no live source samples have been fetched by this snapshot.**  
**Review scope: exact code/workflow review for one bounded Gate A run only.**

## Exact source snapshot

Reviewed developer commit candidate: `e6a7a66c55f6c25baac972c9eb59980dfe52d447`.

| Protected file | Git blob ID |
|---|---|
| `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md` | `a5e65b56f9aa23c8292b718403c3db4448dad2e3` |
| `scripts/phase7_extension2_source_feasibility.py` | `532c1212fad29dbd771d609b1e0ddb85d46d9e50` |
| `scripts/test_phase7_extension2_source_feasibility.py` | `4b470468a4aef23ba59d5efef8755be33ce23fe0` |
| `scripts/phase7_extension2_source_feasibility_v2.py` | `aa714264481034c52b9e2b75d020a270212c8204` |
| `scripts/test_phase7_extension2_source_feasibility_v2.py` | `43bd50df257ecc6d094ca64c6770f26a50340ecf` |
| `.github/workflows/phase-07-extension2-source-feasibility-v2.yml` | `20470b88d29b1d97e8060936e5ed7a40fe28a80d` |

The developer branch and pinned commit were re-fetched; the six protected Git blob IDs match. The workflow's Git blob is `20470b88d29b1d97e8060936e5ed7a40fe28a80d`; reviewed commit ID and file blob IDs are listed separately.

## Changes after previous tester REQUEST CHANGES

The prior report identified a multi-year URL `fromDate=01-01-2020&toDate=31-12-2025`, which breached the Gate A small-sample restriction, and an incorrect workflow Git-blob value in the handoff. The current snapshot corrects these issues:

1. The only configured date-range API probe is now fixed to 2024-07-01 through 2024-07-10.
2. `validate_nse_fii_api_url` rejects unregistered hosts/paths, unknown request keys, malformed date parameters and any date window longer than ten days before calling the fetcher.
3. NSE FII/DII API calls use a **512,000-byte** per-request response cap. Oversized responses are rejected by the shared `fetch_bytes` helper.
4. API payloads exceeding **50 rows** are rejected and not copied into the report.
5. Unrecognized JSON response shapes are explicitly marked `UNRECOGNIZED_JSON_SHAPE`; they are no longer reported as successfully parsed with zero rows.
6. New tests check rejection of the old multi-year URL before fetch, verify the fixed ten-day configuration, verify the byte cap is actually passed to the fetcher, test >50-row rejection, and test unrecognized JSON shapes. A v1 regression tests that per-request byte caps stop oversized reads.
7. Corrected the handoff: workflow blob is `20470...`; commit ID is shown separately.

## Bounded sample scope

The workflow runs both sampler scripts and uploads both JSON reports:

- `scripts/phase7_extension2_source_feasibility.py`: legacy F&O archive 2024-07-05, UDiFF F&O archive 2024-07-08, and bounded public-page/API probes.
- `scripts/phase7_extension2_source_feasibility_v2.py`: official sector-index CSVs for 2024-07-05 and 2024-07-08, equity cash bhavcopies for the same two sessions, limited FII/DII mirror/page probes, and NSE FII/DII API requests with date/byte/row bounds.

No full historical datasets, normalized feature tables, labels, predictions, metrics, p-values or final-holdout reads are produced. The bounded API source response might be too short or have an unexpected shape; that must be recorded as a source-feasibility result, not worked around with a broader request.

## Workflow safety

- First job runs both offline test suites.
- The approval job is downstream of those tests.
- The approval job verifies the tester report digest, exact decision line, explicit restrictions on full-history acquisition and model fitting, protected path set, file SHA-256 values, Git blob IDs quoted in the report, and reviewed-commit ancestry.
- The source job depends on successful tests and the authorization output. Manual sampling defaults to false. A changed protected blob invalidates the decision.
- The earlier run `38019728293` failed before source acquisition; its network and artifact-upload steps were skipped. Generic Research Protocol Check runs do not count as these sampler tests.

## Requested independent checks

1. Verify current protected blob IDs and the exact reviewed commit.
2. Independently inspect the bounded FII/DII API validator, response-byte cap and row cap; confirm the 2020–2025 URL cannot reach `fetch_bytes`.
3. Review the new regression cases and source parsers, including both F&O schema versions and both uploaded-report paths.
4. Verify both manual and automatic routes remain closed until the exact-snapshot report/manifest is valid and tests pass.
5. Return PASS or REQUEST CHANGES. If passing, authorize **one** Gate A sample run only.

**Developer → Tester:** Review this exact six-blob snapshot. Do not authorize full-history acquisition, feature/label construction, model fitting, metrics or final-holdout access.

**Tester → Developer:** Approval must quote every reviewed Git blob and state exact Gate A-only scope. The artifact generated after the sample still requires a separate independent source-feasibility audit before proceeding.
