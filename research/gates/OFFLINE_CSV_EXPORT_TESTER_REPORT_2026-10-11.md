# Tester Report — One-time Encrypted Offline CSV Export

- Review date: 2026-10-11 UTC
- Exact developer snapshot: `24da8b1a7ff13b1caed6d9ac4b1e49efbe4ba464`
- Export workflow blob SHA: `4dd600188bf82370746c3a7bd869a375802bd8f9`
- One-time public key blob SHA: `1c975e2af52e97a1612f231fcf6fe6e67669277e`
- Repository protocol check: [38132975473](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38132975473) — success on exact developer snapshot.
- Scope: export the fixed, tester-reviewed derived dataset as one merged CSV.GZ for the requesting user; no acquisition, modelling, holdout, or strategy scope.

## Reviewed behavior

1. Source identity is pinned to successful repair run 38131641336, exact source commit `5e769cd4b19887311213baf16eb81b97416322d7`, output artifact 11698879857 and expected artifact name. Preflight requires completed/successful run status and exact head SHA before download.
2. The downloaded artifact is treated as encrypted-only. The export step finds exactly one dataset manifest, requires the repaired dataset ID, encrypted-only marker, pinned parent source run/artifact/hash and exactly 61 monthly parts.
3. Before decryption, each encrypted part's filename, size and SHA-256 are checked, and the total manifest count must equal 8,999,865.
4. The repository's existing AES-GCM decryption utility is used. It checks each encrypted-part SHA-256 and the authenticated plaintext gzip digest against the manifest. The monthly gzip CSVs are merged into a single gzip-compressed CSV with one header; schema equality and the full 8,999,865 data rows are then checked.
5. The export is encrypted with a fresh random AES-256-GCM key. That key is wrapped to the supplied RSA public key using RSA-OAEP-SHA256. The one-time private key is not stored in the repository or sent to Actions.
6. Only ciphertext, the wrapped AES key, and a metadata manifest are uploaded. The Actions artifact retention is one day. Plaintext merge and monthly parts are removed from runner temp in an `if: always()` cleanup step, and the step fails if CSV/CSV.GZ plaintext remains.
7. No source data, derived dataset, or decrypted CSV is committed into Git. No new market-data requests, model fitting, holdout access or strategy/P&L tests are included.

## Review notes and constraints

- The source repair gate passed with scoped restrictions; the output still contains 19,021 unmatched option rows and 24,847 weekend-session review flags. The export must preserve these rows/flags, not treat them as fixed.
- The one-time public key is public by design. Only its matching private key can decrypt the uploaded export package. The reviewer cannot infer access to the private key from the repository.
- The hosted run includes a runtime Ruby YAML parse step; the GitHub Actions protocol check passed for the exact developer snapshot. This is a static workflow review/authorization, not evidence that the export has executed yet.
- The original encrypted dataset/artifact and repository source are unchanged.

## Decision

**PASS WITH SCOPED RESTRICTIONS — one-time encrypted offline export only.**

Promote the exact reviewed workflow and public key to `main`. Allow the workflow's push trigger to produce the encrypted-only handoff artifact. On completion, download the artifact into the connected workspace, decrypt with the matching private key locally, and verify the CSV.GZ SHA-256 plus the 8,999,865 data-row count before offering it to the user. If any exact source identity, hash, manifest, row count, decryption, upload, or cleanup check fails, do not offer the output and record the failure.

This decision does not change any research/model/holdout/strategy gate.

**Tester → Developer:** Promote only workflow blob `4dd600188bf82370746c3a7bd869a375802bd8f9` and public-key blob `1c975e2af52e97a1612f231fcf6fe6e67669277e`. Keep the matching private key outside GitHub and never upload the CSV plaintext.

**Developer → Tester:** After export completes, review the encrypted artifact metadata and safe manifest, record final hash/row-count verification, and keep plaintext out of repository commits and Action artifacts.
