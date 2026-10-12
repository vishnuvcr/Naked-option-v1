#!/usr/bin/env python3
"""Synthetic-only regression tests for the independent Greek artifact audit."""
from __future__ import annotations
import hashlib,json,tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED,ZipFile
from phase8_greek_artifact_audit import AuditFailure,audit_bundle

def digest(data): return hashlib.sha256(data).hexdigest()
def fixture(path,fault=None):
    payloads={"nifty_1m_composite_2026-01.csv.gz.enc":b"N1C1"+bytes(range(12))+b"mock-ciphertext-01",
              "nifty_1m_composite_2026-02.csv.gz.enc":b"N1C1"+bytes(range(12))+b"mock-ciphertext-02"}
    months={"2026-01":2,"2026-02":3}; parts=[]; cparts=[]
    for idx,(name,data) in enumerate(payloads.items()):
        h=digest(data)
        if fault=="part_hash" and idx==0: h="0"*64
        n=months[name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz.enc")]
        parts.append({"file":name,"row_count":n,"encrypted_sha256":h,"plain_gzip_sha256":"1"*64,
          "encrypted_bytes":len(data),"encryption":"AES-256-GCM per-file nonce"})
        cparts.append({"file":name,"row_count":n,"encrypted_sha256":h,"plain_gzip_sha256":"1"*64,
          "encrypted_bytes":len(data),"encryption":"AES-256-GCM per-file nonce"})
    m={"dataset_id":"NIFTY_1M_DHAN_HF_SPOT_GREEKS_ENRICHED_R3","download_bundle_contains_encrypted_data_only":True,
       "do_not_upload_plaintext_or_publish_in_public_repository":True,"encryption":"AES-256-GCM; same HF_TOKEN-derived key",
       "source_license":"CC-BY-NC-4.0; non-commercial research only","source_artifact_id":11698879857,
       "source_run_id":38131641336,"rows_preserved":5,"parts":parts,"row_count_by_month":months,
       "columns":["expiry_date","expiry_mapping_source","time_to_expiry_years","greek_implied_volatility","greek_iv_source",
        "delta","gamma","theta_per_day","vega_per_1pct_iv","rho_per_1pct_rate","greek_model","greek_status",
        "risk_free_rate_source","dividend_yield_source"]}
    if fault=="row_total": m["rows_preserved"]=4
    c={"status":"COMPLETE_WITH_COVERAGE_RESTRICTIONS","rows_preserved":5,"source_total_rows":5,
       "source_total_rows_method":"SUM_OF_PART_MANIFEST_ROW_COUNTS","source_option_rows":3,"source_spot_rows":2,
       "source_artifact_id":11698879857,"source_run_id":38131641336,
       "source_artifact_sha256":"40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b",
       "source_attribution":"https://huggingface.co/datasets/thetrademarkk/india-index-options-1m",
       "source_license":"CC-BY-NC-4.0: non-commercial research only","data_limitations":["PARTIAL_GRID"],
       "parts":cparts,"row_count_by_month":months,"greek_rows_with_delta":1,"option_rows_missing_spot":1,
       "option_rows_unmapped_expiry":0,"spot_field_values_filled":1,
       "greek_status_counts":{"GREEKS_ESTIMATED_FROM_INVERTED_IV":2,"SPOT_MISSING_OR_INVALID":1},
       "expiry_mapping_source_counts":{"HF_EXPIRY_PARTITION_FILELIST_PROXY":3},
       "iv_source_counts":{"IV_INVERTED_FROM_OPTION_CLOSE":2,"IV_INPUT_INVALID":1},"latest_hf_expiry_date":"2026-02-24"}
    if fault=="coverage_option_total": c["source_option_rows"]=2
    meta={"repo_id":"thetrademarkk/india-index-options-1m","revision":"0123456789abcdef0123456789abcdef01234567",
          "license":"CC-BY-NC-4.0","non_commercial_research_only":True}
    with ZipFile(path,"w",ZIP_DEFLATED) as z:
        for n,b in payloads.items(): z.writestr("nifty-1m-greeks-enriched-r3/"+n,b)
        z.writestr("nifty-1m-greeks-enriched-r3/dataset_manifest.json",json.dumps(m))
        z.writestr("greek-enrichment-coverage-r3.json",json.dumps(c))
        z.writestr("hf-nifty/source_metadata.json",json.dumps(meta))
        if fault=="plaintext": z.writestr("nifty-1m-greeks-enriched-r3/plain.csv.gz",b"plaintext")
    return path
def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); valid=fixture(root/"valid.zip")
        result=audit_bundle(valid,5,2,3,2,11698879857,38131641336)
        assert result["status"]=="PASS" and result["rows_preserved"]==5 and result["parts"]==2
        bads=0
        for fault in ("part_hash","row_total","plaintext","coverage_option_total"):
            try: audit_bundle(fixture(root/(fault+".zip"),fault),5,2,3,2,11698879857,38131641336)
            except (AuditFailure,ValueError,AssertionError): bads+=1
            else: raise AssertionError("invalid artifact accepted: "+fault)
        assert bads==4
        print(json.dumps({"status":"PASS","valid_artifact_fixtures":1,"invalid_artifact_fixtures_rejected":bads},sort_keys=True))
if __name__=="__main__": main()
