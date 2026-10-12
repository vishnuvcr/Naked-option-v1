# Independent tester review — Phase 8 Greek-enrichment artifact R1

Decision: **PASS_WITH_SCOPED_RESTRICTIONS**
Developer run: 38195812828
Developer snapshot: f556c7b44088f18551453c36f78e8d5de7fe141e
Artifact: nifty-1m-greeks-enriched-r3 (ID 11723198817)
Artifact ZIP SHA-256: e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736
Source identity: PASS; synthetic tests: PASS; download/hash/CRC: PASS; actual artifact audit: PASS

## Findings
- No integrity or coverage inconsistency was detected in the downloaded artifact.

## Independent audit result
{
  "bundle_sha256": "e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736",
  "coverage_report_path": "greek-enrichment-coverage-r3.json",
  "dataset_id": "NIFTY_1M_DHAN_HF_SPOT_GREEKS_ENRICHED_R3",
  "expiry_mapping_source_counts": {
    "HF_EXPIRY_PARTITION_FILELIST_PROXY": 7715704,
    "NSE_TUESDAY_RULE_PROXY_NOT_CONTRACT_MASTER_VERIFIED": 775019
  },
  "greek_rows_with_delta": 8418616,
  "greek_status_counts": {
    "GREEKS_ESTIMATED_FROM_INVERTED_IV": 8382036,
    "GREEKS_ESTIMATED_FROM_SOURCE_IV_FALLBACK": 36580,
    "IV_INPUT_INVALID": 49873,
    "SOURCE_FLAGGED_NON_TRADING_SESSION": 22234
  },
  "hf_revision": "0f4800e43e6f96cec0794369d78eb4d3c4211ef5",
  "iv_source_counts": {
    "IV_INPUT_INVALID": 49873,
    "IV_INVERTED_FROM_OPTION_CLOSE": 8404270,
    "SOURCE_IV_HEURISTIC_FALLBACK_GT3_AS_PERCENT_POINTS": 36580
  },
  "latest_hf_expiry_date": "2026-08-04",
  "manifest_path": "nifty-1m-greeks-enriched-r3/dataset_manifest.json",
  "option_rows": 8490723,
  "option_rows_missing_spot": 0,
  "option_rows_unmapped_expiry": 0,
  "parts": 61,
  "plaintext_files_present": false,
  "rows_preserved": 8999865,
  "source_license": "CC-BY-NC-4.0",
  "source_metadata_path": "hf-nifty/source_metadata.json",
  "spot_field_values_filled": 19746,
  "spot_rows": 509142,
  "status": "PASS"
}

## Limits and restrictions
- This is an artifact integrity and coverage gate, not evidence of a profitable trading strategy.
- The input grid remains PARTIAL_GRID; expiry map is a file-list/rule proxy, not an official point-in-time master.
- Greeks are model estimates using r=0, q=0, IV inversion/labelled fallback, not historical vendor Greek observations.
- CC-BY-NC-4.0 means non-commercial research only. No Dhan API, option P&L, holdout, strategy promotion, commercial use or plaintext upload is authorized.

**Developer → Tester:** correct any artifact mismatch before resubmission.
**Tester → Developer:** accept delivery only if this decision is PASS_WITH_SCOPED_RESTRICTIONS; trading gates remain blocked.
