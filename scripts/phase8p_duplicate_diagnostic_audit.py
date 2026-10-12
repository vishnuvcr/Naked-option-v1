#!/usr/bin/env python3
"""Independent static/synthetic code gate for Phase 8P duplicate-key diagnostic."""
from __future__ import annotations
import argparse, ast, hashlib, json, subprocess
from pathlib import Path
import yaml

FORBIDDEN_IMPORTS={"requests","urllib","httpx","socket","ftplib","yfinance","akshare","huggingface_hub","boto3"}
KEY_FIELDS={"timestamp_epoch","expiry_date","expiry_flag","expiry_code","returned_strike","option_type"}

def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],text=True).strip()

def blob(root,commit,path):
    return git(root,"rev-parse",commit+":"+path)

def check(rows,failures,name,passed,detail=None):
    row={"check":name,"pass":bool(passed)}
    if detail is not None: row["detail"]=detail
    rows.append(row)
    if not passed: failures.append(name)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--developer-root",type=Path,required=True)
    ap.add_argument("--request",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    root=args.developer_root.resolve()
    req=json.loads(args.request.read_text(encoding="utf-8"))
    commit=str(req.get("developer_commit",""))
    checks=[]; failures=[]
    current=git(root,"rev-parse","HEAD")
    check(checks,failures,"exact_developer_commit",current==commit,{"expected":commit,"actual":current})
    paths={
      "diagnostic":req.get("diagnostic_path",""),
      "test":req.get("test_path",""),
      "workflow":req.get("synthetic_workflow_path",""),
      "module":"scripts/phase8p_greek_prediction.py",
    }
    expected={
      "diagnostic":req.get("diagnostic_blob_sha1"),
      "test":req.get("test_blob_sha1"),
      "workflow":req.get("synthetic_workflow_blob_sha1"),
      "module":req.get("existing_approved_module_blob_sha1"),
    }
    contents={}
    for key,path in paths.items():
      try:
        actual=blob(root,commit,path)
        content=(root/path).read_text(encoding="utf-8")
      except Exception as exc:
        actual=""; content=""
        failures.append("FILE_READ_FAILED_"+key.upper())
        checks.append({"check":"file_read_"+key,"pass":False,"detail":type(exc).__name__})
      check(checks,failures,"exact_blob_"+key,actual==expected[key],{"path":path,"actual":actual,"expected":expected[key]})
      contents[key]=content

    check(checks,failures,"request_pending_and_no_authorization",
      req.get("status")=="PENDING_INDEPENDENT_TESTER_REVIEW"
      and req.get("real_artifact_access_authorized") is False
      and req.get("real_artifact_decryption_authorized") is False
      and req.get("model_fit_authorized") is False
      and req.get("holdout_access_authorized") is False
      and req.get("deduplication_authorized") is False)

    try:
      wf=yaml.safe_load(contents["workflow"])
      check(checks,failures,"synthetic_workflow_yaml_valid",isinstance(wf,dict) and isinstance(wf.get("jobs"),dict))
      workflow_text=contents["workflow"]
      check(checks,failures,"synthetic_workflow_has_no_secrets_or_real_data_access",
        "HF_TOKEN" not in workflow_text and "artifact download" not in workflow_text.lower()
        and "--greek-zip" not in workflow_text and "actions/artifacts/" not in workflow_text)
    except Exception as exc:
      check(checks,failures,"synthetic_workflow_yaml_valid",False,type(exc).__name__)

    source=contents["diagnostic"]
    try:
      tree=ast.parse(source)
      imported=set()
      for node in ast.walk(tree):
        if isinstance(node,ast.Import):
          imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module:
          imported.add(node.module.split(".")[0])
      check(checks,failures,"no_network_data_source_imports",not bool(imported & FORBIDDEN_IMPORTS),sorted(imported & FORBIDDEN_IMPORTS))
      check(checks,failures,"key_fields_explicit",all(field in source for field in KEY_FIELDS))
      check(checks,failures,"full_row_sha256_present","def _row_hash" in source and "hashlib.sha256" in source)
      check(checks,failures,"no_deduplication_in_diagnostic","deduplication_performed" in source and "False" in source and "drop_duplicates" not in source)
      check(checks,failures,"no_raw_row_output","print(json.dumps({" in source and "raw_keys_or_rows_emitted" in source)
      check(checks,failures,"pinned_artifact_identity_before_decryption",
        source.index("verify_pinned_artifact_identity(greek_zip,") < source.index("iter_encrypted_composite_parts(greek_zip)"))
      check(checks,failures,"only_aggregate_report_written",
        '"input_artifact_sha256"' in source and '"option_rows_scanned"' in source
        and '"raw_key"' not in source and '"option_close"' not in source)
    except Exception as exc:
      check(checks,failures,"diagnostic_ast_checks",False,type(exc).__name__)

    test_source=contents["test"]
    check(checks,failures,"synthetic_edge_fixtures_present",
      all(term in test_source for term in ("exact_full_row_duplicate_groups","conflicting_full_row_duplicate_groups","timestamp_normalization_case","DUPLICATE_DIAGNOSTIC_PART_SCHEMA_INVALID")))

    # Execute only the pure synthetic tests from the exact reviewed snapshot.
    try:
      r=subprocess.run(["python","scripts/phase8p_duplicate_key_diagnostic.py","--self-test"],
        cwd=root,text=True,capture_output=True,timeout=60)
      check(checks,failures,"module_synthetic_self_test",r.returncode==0,
        {"exit_code":r.returncode,"stdout_sha256":hashlib.sha256(r.stdout.encode()).hexdigest(),"stderr_sha256":hashlib.sha256(r.stderr.encode()).hexdigest()})
      r2=subprocess.run(["python","scripts/test_phase8p_duplicate_key_diagnostic.py"],
        cwd=root,text=True,capture_output=True,timeout=120)
      check(checks,failures,"regression_test_suite",r2.returncode==0,
        {"exit_code":r2.returncode,"stdout_sha256":hashlib.sha256(r2.stdout.encode()).hexdigest(),"stderr_sha256":hashlib.sha256(r2.stderr.encode()).hexdigest()})
    except Exception as exc:
      check(checks,failures,"synthetic_tests_executed",False,type(exc).__name__)

    art=req.get("source_artifact",{})
    check(checks,failures,"pinned_source_artifact",
      art.get("artifact_id")==11723198817 and art.get("sha256")=="e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736")
    decision="PASS_FOR_DUPLICATE_DIAGNOSTIC_CODE_ONLY" if not failures else "REQUEST_CHANGES"
    result={
      "schema_version":1,"gate":"PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW",
      "decision":decision,"developer_commit":commit,"checks_passed":sum(x["pass"] for x in checks),
      "checks_total":len(checks),"failures":failures,"checks":checks,
      "real_artifact_accessed":False,"real_artifact_decrypted":False,"model_fitted":False,
      "holdout_accessed":False,"deduplication_performed":False,
      "real_diagnostic_authorized":False,"model_fit_authorized":False
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("decision","checks_passed","checks_total","failures","real_artifact_accessed","model_fitted")},sort_keys=True))
    if failures: raise SystemExit(1)

if __name__=="__main__": main()
