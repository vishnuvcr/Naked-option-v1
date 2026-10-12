#!/usr/bin/env python3
"""Independent integrity and coverage audit for the Phase 8 R3 encrypted artifact."""
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

class AuditFailure(ValueError): pass

def require(condition, message):
    if not condition: raise AuditFailure(message)

def int_count(value, field, minimum=0):
    require(not isinstance(value,bool),f"{field} must not be boolean")
    try: x=float(value)
    except (TypeError,ValueError): raise AuditFailure(f"{field} must be numeric")
    require(math.isfinite(x) and x.is_integer() and x>=minimum,f"{field} must be an integer >= {minimum}")
    return int(x)

def read_unique_json(zf,names,basename):
    hits=[n for n in names if PurePosixPath(n).name==basename]
    require(len(hits)==1,f"expected exactly one {basename}, found {len(hits)}")
    try: obj=json.loads(zf.read(hits[0]))
    except Exception as exc: raise AuditFailure(f"cannot parse {basename}: {type(exc).__name__}: {exc}")
    require(isinstance(obj,dict),f"{basename} must be a JSON object")
    return hits[0],obj

def count_map_sum(obj,name,expected):
    values=obj.get(name)
    require(isinstance(values,dict),f"{name} must be an object")
    total=sum(int_count(v,f"{name}.{k}") for k,v in values.items())
    require(total==expected,f"{name} sums to {total}, expected {expected}")
    return total

def audit_bundle(bundle_path,expected_rows=8999865,expected_parts=61,expected_option_rows=8490723,
                 expected_spot_rows=509142,expected_source_artifact_id=11698879857,expected_source_run_id=38131641336):
    digest=hashlib.sha256()
    with bundle_path.open('rb') as source_file:
        for block in iter(lambda: source_file.read(1024*1024), b''):
            digest.update(block)
    zipsha=digest.hexdigest()
    with ZipFile(bundle_path,"r") as zf:
        infos=[i for i in zf.infolist() if not i.is_dir()]
        names=[i.filename for i in infos]
        require(len(names)==len(set(names)),"ZIP contains duplicate member paths")
        for name in names:
            path=PurePosixPath(name)
            require(".." not in path.parts,f"unsafe ZIP path: {name}")
            require(".plain" not in path.parts,f"temporary plaintext path present: {name}")
            require(not name.lower().endswith(".csv.gz"),f"unencrypted CSV.GZ present: {name}")
            require(not name.lower().endswith(".csv"),f"plaintext CSV present: {name}")
        manifest_path,m=read_unique_json(zf,names,"dataset_manifest.json")
        coverage_path,c=read_unique_json(zf,names,"greek-enrichment-coverage-r3.json")
        metadata_path,meta=read_unique_json(zf,names,"source_metadata.json")
        require(m.get("dataset_id")=="NIFTY_1M_DHAN_HF_SPOT_GREEKS_ENRICHED_R3","unexpected R3 dataset ID")
        require(m.get("download_bundle_contains_encrypted_data_only") is True,"encrypted-only flag missing")
        require(m.get("do_not_upload_plaintext_or_publish_in_public_repository") is True,"plaintext-publishing prohibition flag missing")
        require(m.get("rows_preserved")==expected_rows,f"manifest rows_preserved={m.get('rows_preserved')!r}, expected {expected_rows}")
        require("AES-256-GCM" in str(m.get("encryption","")),"AES-256-GCM encryption not declared")
        require("CC-BY-NC-4.0" in str(m.get("source_license","")),"source license missing CC-BY-NC-4.0")
        require(m.get("source_artifact_id")==expected_source_artifact_id,"source cache artifact ID mismatch")
        require(m.get("source_run_id")==expected_source_run_id,"source cache run ID mismatch")
        parts=m.get("parts")
        require(isinstance(parts,list) and len(parts)==expected_parts,f"manifest part count not {expected_parts}")
        encrypted_names=[n for n in names if n.lower().endswith(".csv.gz.enc")]
        require(len(encrypted_names)==expected_parts,f"ZIP has {len(encrypted_names)} encrypted parts, expected {expected_parts}")
        bybase={}
        for name in names: bybase.setdefault(PurePosixPath(name).name,[]).append(name)
        listed=[]; monthly={}; row_sum=0
        for idx,p in enumerate(parts):
            require(isinstance(p,dict),f"manifest part {idx} malformed")
            name=p.get("file")
            require(isinstance(name,str) and re.fullmatch(r"nifty_1m_composite_[0-9]{4}-[0-9]{2}\.csv\.gz\.enc",name) is not None,
                    f"invalid encrypted part file name at index {idx}")
            require(name not in listed,f"duplicate manifest part {name}")
            listed.append(name)
            matches=bybase.get(name,[])
            require(len(matches)==1,f"encrypted part {name} appears {len(matches)} times in ZIP")
            data=zf.read(matches[0])
            require(data.startswith(b"N1C1") and len(data)>32,f"invalid encrypted envelope in {name}")
            require(hashlib.sha256(data).hexdigest()==p.get("encrypted_sha256"),f"encrypted SHA-256 mismatch for {name}")
            count=int_count(p.get("row_count"),f"parts[{idx}].row_count")
            row_sum+=count
            monthly[name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz.enc")]=count
        require(set(PurePosixPath(n).name for n in encrypted_names)==set(listed),"encrypted ZIP files and manifest entries differ")
        require(row_sum==expected_rows,f"sum of encrypted part rows={row_sum}, expected {expected_rows}")
        require(m.get("row_count_by_month")==monthly,"manifest monthly counts disagree with part rows")
        cols=m.get("columns")
        require(isinstance(cols,list),"manifest columns absent")
        mandatory={"expiry_date","expiry_mapping_source","time_to_expiry_years","greek_implied_volatility","greek_iv_source",
          "delta","gamma","theta_per_day","vega_per_1pct_iv","rho_per_1pct_rate","greek_model","greek_status",
          "risk_free_rate_source","dividend_yield_source"}
        require(not (mandatory-set(cols)),f"required Greek columns missing: {sorted(mandatory-set(cols))}")
        require(c.get("status")=="COMPLETE_WITH_COVERAGE_RESTRICTIONS",f"unexpected coverage status {c.get('status')!r}")
        require(c.get("rows_preserved")==expected_rows,"coverage row count mismatch")
        require(c.get("source_total_rows")==expected_rows,"coverage source total mismatch")
        require(c.get("source_total_rows_method")=="SUM_OF_PART_MANIFEST_ROW_COUNTS","coverage method not disclosed")
        require(isinstance(c.get("parts"),list) and len(c["parts"])==expected_parts,"coverage part list mismatch")
        require(c.get("row_count_by_month")==monthly,"coverage monthly counts disagree with manifest")
        require("CC-BY-NC-4.0" in str(c.get("source_license","")),"coverage license mismatch")
        require(isinstance(c.get("data_limitations"),list) and any("PARTIAL_GRID" in str(x) for x in c["data_limitations"]),
                "coverage report omits PARTIAL_GRID limitation")
        for idx,cp in enumerate(c["parts"]):
            fn=cp.get("file") if isinstance(cp,dict) else None
            mp=next((p for p in parts if p.get("file")==fn),None)
            require(mp is not None,f"coverage lists unmanifested part {fn!r}")
            require(cp.get("encrypted_sha256")==mp.get("encrypted_sha256"),f"coverage hash mismatch for {fn}")
            require(int_count(cp.get("row_count"),f"coverage.parts[{idx}].row_count")==int_count(mp.get("row_count"),f"manifest.parts[{idx}].row_count"),
                    f"coverage row count mismatch for {fn}")
        require(c.get("source_option_rows")==expected_option_rows,
                f"source_option_rows={c.get('source_option_rows')!r}, expected {expected_option_rows}")
        require(c.get("source_spot_rows")==expected_spot_rows,
                f"source_spot_rows={c.get('source_spot_rows')!r}, expected {expected_spot_rows}")
        for field in ("greek_status_counts","expiry_mapping_source_counts","iv_source_counts"):
            count_map_sum(c,field,expected_option_rows)
        delta=int_count(c.get("greek_rows_with_delta"),"greek_rows_with_delta")
        missing=int_count(c.get("option_rows_missing_spot"),"option_rows_missing_spot")
        unmapped=int_count(c.get("option_rows_unmapped_expiry"),"option_rows_unmapped_expiry")
        fills=int_count(c.get("spot_field_values_filled"),"spot_field_values_filled")
        require(delta<=expected_option_rows and missing<=expected_option_rows and unmapped<=expected_option_rows,"coverage counter exceeds option row count")
        require(meta.get("repo_id")=="thetrademarkk/india-index-options-1m","HF dataset repo ID mismatch")
        revision=meta.get("revision")
        require(isinstance(revision,str) and re.fullmatch(r"[0-9a-f]{40}",revision) is not None,"HF revision not a full commit SHA")
        require("CC-BY-NC-4.0" in str(meta.get("license","")),"HF source metadata license mismatch")
        require(meta.get("non_commercial_research_only") is True,"HF non-commercial restriction missing")
        require(str(c.get("source_attribution","")).startswith("https://huggingface.co/datasets/"),"source attribution missing")
        require(c.get("source_artifact_id")==expected_source_artifact_id,"coverage source artifact ID mismatch")
        require(c.get("source_run_id")==expected_source_run_id,"coverage source run ID mismatch")
        require("40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b"==c.get("source_artifact_sha256"),
                "coverage cached-source archive SHA mismatch")
        return {"status":"PASS","bundle_sha256":zipsha,"manifest_path":manifest_path,"coverage_report_path":coverage_path,
          "source_metadata_path":metadata_path,"dataset_id":m["dataset_id"],"rows_preserved":row_sum,"parts":len(parts),
          "option_rows":expected_option_rows,"spot_rows":expected_spot_rows,"greek_rows_with_delta":delta,
          "option_rows_missing_spot":missing,"option_rows_unmapped_expiry":unmapped,"spot_field_values_filled":fills,
          "greek_status_counts":c["greek_status_counts"],"expiry_mapping_source_counts":c["expiry_mapping_source_counts"],
          "iv_source_counts":c["iv_source_counts"],"latest_hf_expiry_date":c.get("latest_hf_expiry_date"),
          "hf_revision":revision,"source_license":meta.get("license"),"plaintext_files_present":False}

def main():
    p=argparse.ArgumentParser(); p.add_argument("bundle",type=Path)
    p.add_argument("--expected-rows",type=int,default=8999865); p.add_argument("--expected-parts",type=int,default=61)
    p.add_argument("--expected-option-rows",type=int,default=8490723); p.add_argument("--expected-spot-rows",type=int,default=509142)
    p.add_argument("--expected-source-artifact-id",type=int,default=11698879857)
    p.add_argument("--expected-source-run-id",type=int,default=38131641336); a=p.parse_args()
    try:
        result=audit_bundle(a.bundle,a.expected_rows,a.expected_parts,a.expected_option_rows,a.expected_spot_rows,
                            a.expected_source_artifact_id,a.expected_source_run_id)
        print(json.dumps(result,sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error_type":type(exc).__name__,"findings":[str(exc)]},sort_keys=True)); return 1
if __name__=="__main__": raise SystemExit(main())
