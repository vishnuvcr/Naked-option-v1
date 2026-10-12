#!/usr/bin/env python3
"""Independent, synthetic-only Phase 8P code audit. Never opens market artifacts."""
from __future__ import annotations
import argparse, ast, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED_FILES = [
    "scripts/phase8p_greek_prediction.py",
    "scripts/test_phase8p_greek_prediction.py",
    ".github/workflows/phase8p-greek-prediction.yml",
    "research/gates/PHASE8P_GREEK_PREDICTION_SCOPE_R3_2026-10-12.md",
]
REQUIRED_PIPELINE_FUNCTIONS = [
    "verify_pinned_artifact_identity",
    "build_option_feature_frame",
    "build_daily_spot_features",
    "align_features_to_prediction_panel",
    "run_prediction_study",
    "write_aggregate_only_report",
]
PROHIBITED_MARKET_OPERATIONS = ["requests.get(", "huggingface_hub", "dhan", "download_workflow_artifact("]

def blob_sha(root: Path, commit: str, path: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", f"{commit}:{path}"], text=True).strip()

def load_module(path: Path):
    spec=importlib.util.spec_from_file_location("phase8p_independent_subject", path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--developer-root", type=Path, required=True)
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args=ap.parse_args()
    root=args.developer_root.resolve()
    request=json.loads(args.request.read_text())
    commit=request["developer_commit"]
    failures=[]; checks=[]
    current=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    checks.append({"check":"exact_commit","expected":commit,"actual":current,"pass":current==commit})
    if current!=commit: failures.append("REQUEST_COMMIT_MISMATCH")
    blob_results={}
    for path,expected in request["reviewed_blobs"].items():
        try: actual=blob_sha(root,commit,path)
        except Exception as e: actual="ERROR:"+str(e)
        ok=actual==expected; blob_results[path]={"expected":expected,"actual":actual,"pass":ok}
        checks.append({"check":"blob:"+path,"pass":ok})
        if not ok: failures.append("REVIEWED_BLOB_MISMATCH:"+path)
    for path in REQUIRED_FILES:
        if not (root/path).is_file():
            failures.append("REQUIRED_FILE_MISSING:"+path)
    module_path=root/"scripts/phase8p_greek_prediction.py"
    source=module_path.read_text(encoding="utf-8")
    tree=ast.parse(source)
    functions={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    missing_funcs=sorted(set(REQUIRED_PIPELINE_FUNCTIONS)-functions)
    checks.append({"check":"end_to_end_pipeline_completeness","required_functions":REQUIRED_PIPELINE_FUNCTIONS,"missing_functions":missing_funcs,"pass":not missing_funcs})
    if missing_funcs: failures.append("END_TO_END_PIPELINE_INCOMPLETE:"+",".join(missing_funcs))
    if "def enforce_fit_gate" in source and "scope_approved: bool" in source and "code_approved: bool" in source:
        failures.append("FIT_AUTHORIZATION_USES_CALLER_CONTROLLED_BOOLEAN_FLAGS")
        checks.append({"check":"authorization_binding","pass":False,"reason":"Caller can supply True flags; gate does not verify signed/pinned decision fields itself"})
    else: checks.append({"check":"authorization_binding","pass":True})
    wf=(root/".github/workflows/phase8p-greek-prediction.yml").read_text(encoding="utf-8")
    if "requests.get(" in source or "huggingface_hub" in source:
        failures.append("UNSCOPED_EXTERNAL_DATA_ACCESS_IN_REVIEWED_MODULE")
    if "run_prediction_study" not in source:
        failures.append("NO_REPRODUCIBLE_20_CELL_RUN_OR_HOLM_AGGREGATION")
    if "block_index" in source and "np.diff(blocks) < 0" not in source and "BLOCK_INDEX_NOT_MONOTONE" not in source:
        failures.append("WALK_FORWARD_DOES_NOT_VERIFY_CHRONOLOGICAL_BLOCK_ORDER")
    checks.append({"check":"chronological_block_order_validation","pass":"BLOCK_INDEX_NOT_MONOTONE" in source or "np.diff(blocks) < 0" in source})
    test_path=root/"scripts/test_phase8p_greek_prediction.py"
    test=subprocess.run([sys.executable,str(test_path)],cwd=str(root),capture_output=True,text=True)
    checks.append({"check":"developer_synthetic_suite","pass":test.returncode==0,"returncode":test.returncode,"stdout":test.stdout[-5000:],"stderr":test.stderr[-3000:]})
    if test.returncode: failures.append("DEVELOPER_SYNTHETIC_SUITE_FAILED")
    # Independent arithmetic tests: do not rely on the developer's internal self-test.
    mod=load_module(module_path)
    sample=[]
    for delta in (.60,.61,.62,.63,.64):
        sample.append({"row_type":"OPTION","option_type":"CE","greek_status":"GREEKS_ESTIMATED_FROM_INVERTED_IV","delta":delta,
                       "gamma":.01,"theta_per_day":-1,"vega_per_1pct_iv":.2,"greek_implied_volatility":.2,
                       "open_interest":100,"volume":10})
    for delta in (-.40,-.41,-.42,-.43,-.44):
        sample.append({"row_type":"OPTION","option_type":"PE","greek_status":"GREEKS_ESTIMATED_FROM_INVERTED_IV","delta":delta,
                       "gamma":.01,"theta_per_day":-1,"vega_per_1pct_iv":.2,"greek_implied_volatility":.25,
                       "open_interest":200,"volume":20})
    a=mod.aggregate_option_snapshot(sample)
    math_ok=bool(abs(a["call_delta_median"]-.62)<1e-12 and abs(a["put_delta_median"]+.42)<1e-12
             and abs(a["delta_imbalance"]-.20)<1e-12
             and abs(a["oi_put_call_ratio"]-2)<1e-12
             and abs(a["iv_skew_put_minus_call"]-.05)<1e-12)
    checks.append({"check":"independent_signed_delta_and_ratio_math","pass":math_ok,"values":{
        "call_delta_median":a["call_delta_median"],"put_delta_median":a["put_delta_median"],
        "delta_imbalance":a["delta_imbalance"],"oi_put_call_ratio":a["oi_put_call_ratio"],
        "iv_skew_put_minus_call":a["iv_skew_put_minus_call"]}})
    if not math_ok: failures.append("FEATURE_SIGN_OR_RATIO_ARITHMETIC_FAILURE")
    # A composite contains SPOT rows with NaN Greek offsets. Snapshot selection must
    # ignore those rows and apply the exact timestamp rule to OPTION rows only.
    base_epoch=pd.Timestamp("2025-01-02T04:00:00Z").timestamp()
    mixed_rows=[
        {"row_type":"OPTION","timestamp_epoch":base_epoch,"greek_valuation_offset_seconds":60,"id":"option"},
        {"row_type":"SPOT","timestamp_epoch":base_epoch,"greek_valuation_offset_seconds":float("nan"),"id":"spot"},
    ]
    try:
        selected=mod.exact_snapshot_rows(mixed_rows,pd.Timestamp(base_epoch+60,unit="s",tz="UTC"))
        mixed_snapshot_ok=([row.get("id") for row in selected]==["option"])
        mixed_snapshot_error=None
    except Exception as exc:
        mixed_snapshot_ok=False
        mixed_snapshot_error=f"{type(exc).__name__}:{exc}"
    checks.append({"check":"mixed_OPTION_SPOT_exact_snapshot","pass":bool(mixed_snapshot_ok),"error":mixed_snapshot_error})
    if not mixed_snapshot_ok: failures.append("EXACT_SNAPSHOT_REJECTS_SPOT_ROWS_WITH_NAN_GREEK_OFFSET")
    y=np.array([0.,1.]*40); p0=np.where(y==1,.55,.45); p1=np.where(y==1,.70,.30)
    stats=mod.paired_brier_bootstrap(y,p0,p1,20,reps=99,seed=42)
    signed_ok=bool(stats["mean_brier_improvement"]>0 and abs(stats["mean_brier_improvement"]-(np.mean((p0-y)**2)-np.mean((p1-y)**2)))<1e-12)
    checks.append({"check":"independent_paired_brier_sign","pass":signed_ok,"mean_improvement":stats["mean_brier_improvement"],"raw_p":stats["raw_p_value"]})
    if not signed_ok: failures.append("PAIRED_BRIER_SIGN_OR_NUMERICAL_FAILURE")
    holm=mod.holm_adjust([.01,.04,.03,.002])
    holm_ok=np.allclose(holm,[.03,.06,.06,.008],atol=1e-12)
    checks.append({"check":"independent_holm_adjustment","pass":bool(holm_ok),"values":holm})
    if not holm_ok: failures.append("HOLM_MULTIPLICITY_ARITHMETIC_FAILURE")
    outcome="PASS_FOR_CODE_ONLY" if not failures else "REQUEST_CHANGES"
    result={"schema_version":1,"gate":"PHASE8P_INDEPENDENT_CODE_REVIEW","decision":outcome,
            "reviewed_commit":commit,"checks":checks,"reviewed_blobs":blob_results,
            "failures":failures,"real_artifacts_opened":False,"model_fitted":False,
            "market_source_requested":False,"holdout_accessed":False,"option_pnl_run":False,
            "strategy_promotion":False}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":outcome,"failures":failures,"checks_passed":sum(bool(c.get("pass")) for c in checks),
                      "checks_total":len(checks),"real_artifacts_opened":False,"model_fitted":False},sort_keys=True))
    sys.exit(0 if outcome=="PASS_FOR_CODE_ONLY" else 2)

if __name__=="__main__": main()
