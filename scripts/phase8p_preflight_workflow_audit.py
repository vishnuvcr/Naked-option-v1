#!/usr/bin/env python3
"""Independent static and synthetic-only audit of the Phase 8P preflight executor."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path
import yaml

EXPECTED = {
    "workflow_blob": "15e330467f60df5dc00e502b37bea70b9720b421",
    "proposal_blob": "267cc3fba9d2e5a8313be5efb60879d27586d529",
    "code_commit": "a5a38e3592234aea9052e697416c8154c6f8e8f8",
    "module_blob": "1de7f9e4bce0ee3ddf7dfa0d0b10282a7f0a5c8d",
    "test_blob": "4681c8e34aab1edae44f70ffad455741799d7075",
    "code_decision_blob": "a23774dd9bf476f4e0fa3e1edf2d540bbd548c7b",
    "greek_id": 11723198817,
    "greek_sha256": "e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736",
    "forecast_id": 11638738288,
    "forecast_sha256": "3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9",
}
REVIEW_REQUEST_PATH = "research/gates/PHASE8P_PREFLIGHT_WORKFLOW_REVIEW_REQUEST_R1_2026-10-12.json"
EXECUTION_REQUEST_PATH = "research/gates/PHASE8P_PREFLIGHT_EXECUTION_REQUEST_R2_2026-10-12.json"
WORKFLOW_PATH = ".github/workflows/phase8p-preflight-only.yml"
PROPOSAL_PATH = "research/gates/PHASE8P_PREFLIGHT_EXECUTOR_PROPOSAL_R1_2026-10-12.md"

def run_git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

def blob(root: Path, commit: str, path: str) -> str:
    return run_git(root, "rev-parse", f"{commit}:{path}")

def check(checks, failures, name, ok, detail=None):
    row={"check":name,"pass":bool(ok)}
    if detail is not None: row["detail"]=detail
    checks.append(row)
    if not ok: failures.append(name)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--developer-root",type=Path,required=True)
    ap.add_argument("--request",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    root=args.developer_root.resolve()
    request=json.loads(args.request.read_text(encoding="utf-8"))
    commit=str(request.get("developer_workflow_commit",""))
    checks=[]; failures=[]
    current=run_git(root,"rev-parse","HEAD")
    check(checks,failures,"exact_workflow_commit",current==commit,{"expected":commit,"actual":current})
    workflow_file=root/WORKFLOW_PATH
    proposal_file=root/PROPOSAL_PATH
    wf_text=workflow_file.read_text(encoding="utf-8") if workflow_file.is_file() else ""
    prop_text=proposal_file.read_text(encoding="utf-8") if proposal_file.is_file() else ""
    try:
        actual_workflow_blob=blob(root,commit,WORKFLOW_PATH)
        actual_proposal_blob=blob(root,commit,PROPOSAL_PATH)
    except Exception as exc:
        actual_workflow_blob=actual_proposal_blob=""
        failures.append("WORKFLOW_OR_PROPOSAL_BLOB_LOOKUP_FAILED")
        checks.append({"check":"workflow_proposal_blob_lookup","pass":False,"detail":type(exc).__name__})
    check(checks,failures,"exact_workflow_blob",actual_workflow_blob==EXPECTED["workflow_blob"],actual_workflow_blob)
    check(checks,failures,"exact_proposal_blob",actual_proposal_blob==EXPECTED["proposal_blob"],actual_proposal_blob)
    check(checks,failures,"proposal_scope_and_no_data_before_review",
          "No artifact download yet" in prop_text and "No model fitting occurs in this workflow" in prop_text)
    check(checks,failures,"request_is_pending_review",
          request.get("status")=="PENDING_INDEPENDENT_TESTER_REVIEW"
          and request.get("no_data_download_before_review") is True
          and request.get("no_model_fit_before_report_decision") is True)
    approved=request.get("approved_code_snapshot",{})
    check(checks,failures,"approved_code_snapshot_pins",
          approved.get("commit")==EXPECTED["code_commit"]
          and approved.get("module_blob_sha1")==EXPECTED["module_blob"]
          and approved.get("test_blob_sha1")==EXPECTED["test_blob"]
          and approved.get("code_tester_decision_blob_sha1")==EXPECTED["code_decision_blob"])
    arts=request.get("artifacts",{})
    check(checks,failures,"fixed_artifact_ids_and_digests",
          arts.get("greek")=={"artifact_id":EXPECTED["greek_id"],"sha256":EXPECTED["greek_sha256"]}
          and arts.get("forecast")=={"artifact_id":EXPECTED["forecast_id"],"sha256":EXPECTED["forecast_sha256"]})
    try:
        parsed=yaml.safe_load(wf_text)
        triggers=parsed.get("on",parsed.get(True,{}))
        jobs=parsed.get("jobs",{})
        job=jobs.get("schema-only-preflight",{})
        steps=job.get("steps",[])
        labels=[str(s.get("name","")) for s in steps]
        workflow_yaml_ok=isinstance(parsed,dict) and isinstance(triggers,dict) and isinstance(jobs,dict) and bool(steps)
        check(checks,failures,"workflow_yaml_parse",workflow_yaml_ok,{"trigger_keys":list(triggers) if isinstance(triggers,dict) else None,"step_count":len(steps)})
        push=triggers.get("push",{}) if isinstance(triggers,dict) else {}
        expected_paths=[EXECUTION_REQUEST_PATH]
        check(checks,failures,"push_trigger_limited_to_authorized_request",
              push.get("branches")==["phase-08-prediction-developer"] and push.get("paths")==expected_paths,
              {"branches":push.get("branches"),"paths":push.get("paths")})
        dispatch=triggers.get("workflow_dispatch",{}) if isinstance(triggers,dict) else {}
        dispatch_input=dispatch.get("inputs",{}).get("run_schema_preflight",{})
        check(checks,failures,"manual_dispatch_defaults_disabled",
              dispatch_input.get("type")=="boolean" and dispatch_input.get("default") is False)
        perms=parsed.get("permissions",{})
        check(checks,failures,"least_privilege_workflow_permissions",
              perms.get("contents")=="read" and perms.get("actions")=="read")
        names_to_index={name:i for i,name in enumerate(labels)}
        gate_idx=names_to_index.get("Verify tester-approved workflow, exact code snapshot, and artifact pins before any download",-1)
        download_idx=names_to_index.get("Download or validate exact encrypted Greek artifact",-1)
        forecast_idx=names_to_index.get("Download exact frozen prediction artifact (never persist in cache)",-1)
        check(checks,failures,"authorization_precedes_both_downloads",
              gate_idx>=0 and download_idx>gate_idx and forecast_idx>gate_idx,
              {"gate_index":gate_idx,"greek_download_index":download_idx,"forecast_download_index":forecast_idx})
        preflight_step=next((s for s in steps if s.get("name")=="Run schema/coverage-only preflight, never fit a model"),{})
        preflight_run=str(preflight_step.get("run",""))
        check(checks,failures,"schema_preflight_only_command",
              "--run-preflight" in preflight_run and "--run-study" not in preflight_run
              and "run_prediction_study_from_artifacts" not in preflight_run)
        workflow_gate_run=str(next((s.get("run","") for s in steps if s.get("name","").startswith("Verify tester-approved workflow")), ""))
        check(checks,failures,"gate_checks_decision_and_exact_blob",
              "PASS_PREFLIGHT_WORKFLOW_ONLY" in workflow_gate_run
              and "workflow_blob_sha1" in workflow_gate_run
              and "PASS_FOR_CODE_ONLY" in workflow_gate_run
              and "CODE_DECISION_BLOB_SHA1" in workflow_gate_run)
        constants_ok=all(text in wf_text for text in (
            str(EXPECTED["greek_id"]),EXPECTED["greek_sha256"],
            str(EXPECTED["forecast_id"]),EXPECTED["forecast_sha256"],
            EXPECTED["code_commit"],EXPECTED["code_decision_blob"],
        ))
        check(checks,failures,"workflow_has_fixed_artifact_and_code_constants",constants_ok)
        check(checks,failures,"no_unscoped_market_source_requests",
              not any(s in wf_text.lower() for s in (
                  "huggingface.co","nseindia.com","bseindia.com","dhan.co",
                  "api.dhan.co","yfinance","kaggle.com","huggingface_hub")))
        download_api_count=sum(1 for line in wf_text.splitlines() if "API_URL=" in line and "/actions/artifacts/" in line)
        check(checks,failures,"downloads_only_pinned_github_actions_artifacts",download_api_count==2,download_api_count)
        check(checks,failures,"token_handling_is_environment_only",
              "HF_TOKEN: ${{ secrets.HF_TOKEN }}" in wf_text
              and "echo ${HF_TOKEN}" not in wf_text
              and "Authorization: Bearer ${HF_TOKEN}" not in wf_text)
        cache_restore=next((s for s in steps if s.get("name","").startswith("Restore cached encrypted Greek")),{})
        cache_save=next((s for s in steps if s.get("name","").startswith("Save immutable encrypted Greek")),{})
        check(checks,failures,"only_encrypted_greek_zip_is_cached",
              "nifty-1m-greeks-enriched-r3.zip" in str(cache_restore.get("with",{}).get("path",""))
              and "phase7-ensemble-reference.zip" not in str(cache_restore.get("with",{}).get("path",""))
              and "nifty-1m-greeks-enriched-r3.zip" in str(cache_save.get("with",{}).get("path","")))
        upload=next((s for s in steps if s.get("name")=="Upload aggregate-only preflight receipt"),{})
        upload_paths=str(upload.get("with",{}).get("path",""))
        check(checks,failures,"uploads_aggregate_json_only",
              "phase8p-schema-preflight-report.json" in upload_paths
              and "input-receipt.json" in upload_paths
              and not any(x in upload_paths.lower() for x in (".zip",".csv",".parquet","feature_matrix","raw_rows")))
        cleanup=next((s for s in steps if s.get("name","").startswith("Preserve only encrypted Greek cache")),{})
        cleanup_run=str(cleanup.get("run",""))
        check(checks,failures,"forecast_zip_and_runtime_logs_deleted",
              "phase7-ensemble-reference.zip" in cleanup_run
              and "stdout.log" in cleanup_run and "stderr.log" in cleanup_run)
        check(checks,failures,"workflow_has_no_model_fit_authorization",
              "model_fit_authorized:false" not in wf_text.lower()
              and "model_fit_authorized" in wf_text
              and "model_fit_authorized is not False" in wf_text)
    except Exception as exc:
        failures.append("WORKFLOW_STRUCTURE_PARSE_ERROR:"+type(exc).__name__)
        checks.append({"check":"workflow_structure_parse","pass":False,"detail":type(exc).__name__+":"+str(exc)[:200]})

    # Run the reviewed module's developer synthetic tests in an isolated worktree. No artifact is opened.
    code_commit=EXPECTED["code_commit"]
    core=root.parent/"phase8p-code-snapshot"
    try:
        subprocess.check_call(["git","-C",str(root),"worktree","add","--detach",str(core),code_commit],
                              stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        check(checks,failures,"approved_module_blob_matches",blob(core,code_commit,"scripts/phase8p_greek_prediction.py")==EXPECTED["module_blob"])
        check(checks,failures,"approved_test_blob_matches",blob(core,code_commit,"scripts/test_phase8p_greek_prediction.py")==EXPECTED["test_blob"])
        test=subprocess.run([sys.executable,"scripts/test_phase8p_greek_prediction.py"],cwd=core,
                            capture_output=True,text=True,timeout=300)
        check(checks,failures,"independent_synthetic_regression",test.returncode==0,
              {"returncode":test.returncode,"stdout":test.stdout[-2500:],"stderr":test.stderr[-1500:]})
        selftest=subprocess.run([sys.executable,"scripts/phase8p_greek_prediction.py","--self-test"],cwd=core,
                                capture_output=True,text=True,timeout=300)
        check(checks,failures,"module_synthetic_self_test",selftest.returncode==0,
              {"returncode":selftest.returncode,"stdout":selftest.stdout[-2500:],"stderr":selftest.stderr[-1500:]})
    except Exception as exc:
        failures.append("SYNTHETIC_REVIEW_EXECUTION_ERROR:"+type(exc).__name__)
        checks.append({"check":"independent_synthetic_review","pass":False,"detail":type(exc).__name__+":"+str(exc)[:200]})
    finally:
        subprocess.run(["git","-C",str(root),"worktree","remove","--force",str(core)],
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    decision="PASS_PREFLIGHT_WORKFLOW_ONLY" if not failures else "REQUEST_CHANGES"
    result={
        "schema_version":1,"gate":"PHASE8P_PREFLIGHT_EXECUTOR_WORKFLOW_REVIEW",
        "decision":decision,"developer_workflow_commit":commit,
        "developer_workflow_blob_sha1":actual_workflow_blob,
        "proposal_blob_sha1":actual_proposal_blob,
        "approved_developer_commit":EXPECTED["code_commit"],
        "code_decision_blob_sha1":EXPECTED["code_decision_blob"],
        "checks":checks,"failures":failures,
        "real_artifacts_downloaded":False,"real_artifacts_decrypted":False,
        "model_fitted":False,"holdout_accessed":False,"market_source_requested":False,
        "option_pnl_run":False,"strategy_promotion":False,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"decision":decision,"checks_passed":sum(bool(c.get("pass")) for c in checks),
                      "checks_total":len(checks),"failures":failures,
                      "real_artifacts_downloaded":False,"model_fitted":False},sort_keys=True))
    sys.exit(0 if not failures else 2)

if __name__=="__main__": main()
