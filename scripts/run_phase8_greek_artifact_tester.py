#!/usr/bin/env python3
"""Independent tester gate for the exact R3 Greek-enrichment artifact."""
from __future__ import annotations
import base64,hashlib,json,os,subprocess,sys,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(".")
REQ=ROOT/"research/gates/PHASE8_GREEK_ENRICHMENT_ARTIFACT_REQUEST_R1_2026-10-12.json"
DEC=ROOT/"research/gates/PHASE8_GREEK_ENRICHMENT_ARTIFACT_DECISION_R1_2026-10-12.json"
REPORT=ROOT/"research/gates/PHASE8_GREEK_ENRICHMENT_ARTIFACT_REVIEW_R1_2026-10-12.md"

def api_json(url,token):
    r=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
    with urllib.request.urlopen(r,timeout=60) as x: return json.loads(x.read())

def sha_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def download(url,token,path):
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","User-Agent":"Naked-option-v1-artifact-tester"})
    opener=urllib.request.build_opener(NoRedirect)
    try:
        response=opener.open(req,timeout=60)
        location=response.geturl()
        response.close()
    except urllib.error.HTTPError as exc:
        if exc.code not in (301,302,303,307,308): raise
        location=exc.headers.get("Location")
        if not location: raise RuntimeError("artifact API redirect has no Location header")
    obj=urllib.request.Request(location,headers={"User-Agent":"Naked-option-v1-artifact-tester"})
    with urllib.request.urlopen(obj,timeout=240) as response,path.open("wb") as out:
        while True:
            block=response.read(1024*1024)
            if not block: break
            out.write(block)

def append_once(path,marker,body):
    old=path.read_text(encoding="utf-8")
    if marker not in old: path.write_text(old+"\n\n"+marker+"\n"+body+"\n",encoding="utf-8")

def main():
    req=json.loads(REQ.read_text(encoding="utf-8"))
    token=os.environ.get("GH_TOKEN","")
    repo=os.environ.get("GITHUB_REPOSITORY","vishnuvcr/Naked-option-v1")
    runid=os.environ.get("GITHUB_RUN_ID","")
    findings=[]; audit={}; bundle_sha=""; source_gate="FAIL"; synthetic="FAIL"; download_gate="SKIPPED"; audit_gate="SKIPPED"
    temp=Path(os.environ.get("RUNNER_TEMP","/tmp")); temp.mkdir(parents=True,exist_ok=True)
    bundle=temp/"phase8-greek-enrichment-r3.zip"
    try:
        if not token: raise ValueError("GH_TOKEN missing")
        if req.get("gate")!="PHASE8_GREEK_ENRICHMENT_ARTIFACT_R1": raise ValueError("wrong artifact gate")
        rid=int(req["developer_run_id"]); aid=int(req["artifact_id"])
        dr=api_json(f"https://api.github.com/repos/{repo}/actions/runs/{rid}",token)
        if dr.get("status")!="completed" or dr.get("conclusion")!="success": raise ValueError("developer run not successful")
        if dr.get("head_branch")!="phase-08-developer" or dr.get("head_sha")!=req.get("developer_snapshot_sha"): raise ValueError("developer branch/SHA mismatch")
        if dr.get("path")!=".github/workflows/phase8-greek-enrichment.yml": raise ValueError("unexpected developer workflow")
        dc=api_json(f"https://api.github.com/repos/{repo}/contents/research/gates/PHASE8_GREEK_ENRICHMENT_TESTER_DECISION_R3_2026-10-12.json?ref=phase-08-tester",token)
        code_dec=json.loads(base64.b64decode(dc["content"]).decode("utf-8"))
        if code_dec.get("decision")!="PASS_WITH_SCOPED_RESTRICTIONS" or code_dec.get("developer_snapshot_sha")!=req.get("developer_snapshot_sha"): raise ValueError("exact R3 code tester decision mismatch")
        listings=api_json(f"https://api.github.com/repos/{repo}/actions/runs/{rid}/artifacts?per_page=100",token)
        found=[a for a in listings.get("artifacts",[]) if int(a.get("id",-1))==aid]
        if len(found)!=1: raise ValueError("artifact ID not uniquely attached to developer run")
        art=found[0]
        if art.get("name")!=req.get("artifact_name"): raise ValueError("artifact name mismatch")
        if art.get("expired") is not False: raise ValueError("artifact expired or expiry state unknown")
        if int(art.get("size_in_bytes",0))!=int(req["artifact_size_bytes"]): raise ValueError("artifact size mismatch")
        if art.get("digest")!="sha256:"+req["artifact_zip_sha256"]: raise ValueError("GitHub artifact digest differs from requested SHA-256")
        source_gate="PASS"
    except Exception as exc:
        findings.append("Source identity gate: "+type(exc).__name__+": "+str(exc))
    try:
        proc=subprocess.run([sys.executable,"scripts/test_phase8_greek_artifact_audit.py"],capture_output=True,text=True,timeout=300)
        if proc.returncode:
            findings.append("Independent synthetic audit tests failed: "+(proc.stdout+" "+proc.stderr)[-1800:])
        else: synthetic="PASS"
    except Exception as exc:
        findings.append("Independent synthetic audit tests could not run: "+type(exc).__name__+": "+str(exc))
    if source_gate=="PASS" and synthetic=="PASS":
        try:
            download(f"https://api.github.com/repos/{repo}/actions/artifacts/{req['artifact_id']}/zip",token,bundle)
            bundle_sha=sha_file(bundle)
            if bundle_sha!=req.get("artifact_zip_sha256"): raise ValueError("downloaded ZIP SHA-256 mismatch")
            with zipfile.ZipFile(bundle,"r") as z:
                bad=z.testzip()
                if bad: raise ValueError("ZIP CRC error: "+bad)
            download_gate="PASS"
        except Exception as exc:
            download_gate="FAIL"; findings.append("Artifact download/hash/CRC: "+type(exc).__name__+": "+str(exc))
    if download_gate=="PASS":
        try:
            from phase8_greek_artifact_audit import audit_bundle
            audit=audit_bundle(bundle,int(req["expected_rows"]),int(req["expected_parts"]),
                int(req["expected_option_rows"]),int(req["expected_spot_rows"]),
                int(req["source_cached_artifact_id"]),int(req["source_cached_run_id"]))
            audit_gate="PASS"
        except Exception as exc:
            audit_gate="FAIL"; findings.append("Actual artifact audit: "+type(exc).__name__+": "+str(exc))
    decision="PASS_WITH_SCOPED_RESTRICTIONS" if source_gate=="PASS" and synthetic=="PASS" and download_gate=="PASS" and audit_gate=="PASS" and audit.get("status")=="PASS" else "REQUEST_CHANGES"
    payload={"schema_version":1,"gate":"PHASE8_GREEK_ENRICHMENT_ARTIFACT_R1","decision":decision,
      "reviewed_at_utc":datetime.now(timezone.utc).isoformat(),"tester_workflow_run_id":runid,
      "developer_run_id":req.get("developer_run_id"),"developer_snapshot_sha":req.get("developer_snapshot_sha"),
      "artifact_id":req.get("artifact_id"),"artifact_name":req.get("artifact_name"),"artifact_size_bytes":req.get("artifact_size_bytes"),
      "artifact_sha256":bundle_sha,"source_gate_status":source_gate,"synthetic_test_status":synthetic,
      "download_gate_status":download_gate,"audit_gate_status":audit_gate,"audit_result":audit,"findings":findings,
      "restrictions":{"dhan_api_requests_authorized":False,"empirical_option_pnl_authorized":False,
       "holdout_access_authorized":False,"strategy_promotion_authorized":False,"plaintext_upload_authorized":False,
       "commercial_use_authorized":False,"source_license":"CC-BY-NC-4.0; non-commercial research only","source_grid_status":"PARTIAL_GRID"}}
    DEC.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    report=f"""# Independent tester review — Phase 8 Greek-enrichment artifact R1

Decision: **{decision}**
Developer run: {req.get("developer_run_id")}
Developer snapshot: {req.get("developer_snapshot_sha")}
Artifact: {req.get("artifact_name")} (ID {req.get("artifact_id")})
Artifact ZIP SHA-256: {bundle_sha}
Source identity: {source_gate}; synthetic tests: {synthetic}; download/hash/CRC: {download_gate}; actual artifact audit: {audit_gate}

## Findings
{chr(10).join("- "+f for f in findings) if findings else "- No integrity or coverage inconsistency was detected in the downloaded artifact."}

## Independent audit result
{json.dumps(audit,indent=2,sort_keys=True)}

## Limits and restrictions
- This is an artifact integrity and coverage gate, not evidence of a profitable trading strategy.
- The input grid remains PARTIAL_GRID; expiry map is a file-list/rule proxy, not an official point-in-time master.
- Greeks are model estimates using r=0, q=0, IV inversion/labelled fallback, not historical vendor Greek observations.
- CC-BY-NC-4.0 means non-commercial research only. No Dhan API, option P&L, holdout, strategy promotion, commercial use or plaintext upload is authorized.

**Developer → Tester:** correct any artifact mismatch before resubmission.
**Tester → Developer:** accept delivery only if this decision is PASS_WITH_SCOPED_RESTRICTIONS; trading gates remain blocked.
"""
    REPORT.write_text(report,encoding="utf-8")
    marker=f"## 2026-10-12 — Phase 8 Greek-enrichment artifact audit R1 (workflow {runid})"
    sp=ROOT/"research/STATUS.md"; status=sp.read_text(encoding="utf-8")
    label="**ARTIFACT AUDIT PASSED — TRADING GATES BLOCKED**" if decision=="PASS_WITH_SCOPED_RESTRICTIONS" else "**ARTIFACT AUDIT REQUEST CHANGES — DELIVERY NOT ACCEPTED**"
    row=f"| Phase 8 Long-option execution | {label} | Tester-owned decision {decision}; see PHASE8_GREEK_ENRICHMENT_ARTIFACT_REVIEW_R1_2026-10-12.md |"
    lines=status.splitlines()
    for idx,line in enumerate(lines):
        if line.startswith("| Phase 8 Long-option execution |"): lines[idx]=row; break
    if marker not in status:
        sp.write_text("\n".join(lines)+"\n\n"+marker+"\n- Decision: "+decision+".\n- Developer run "+str(req.get("developer_run_id"))+"; artifact ID "+str(req.get("artifact_id"))+".\n- "+("Encrypted part hashes, row counts, coverage and no-plaintext conditions passed." if decision=="PASS_WITH_SCOPED_RESTRICTIONS" else "Artifact not accepted; see tester report findings.")+"\n- Trading/economic gates remain blocked.\n",encoding="utf-8")
    if decision!="PASS_WITH_SCOPED_RESTRICTIONS":
        append_once(ROOT/"research/ERROR_LOG.md",marker,"- Category: independent artifact audit.\n- Decision: REQUEST_CHANGES.\n- Findings: "+("; ".join(findings) if findings else "see review report")+"\n- No dataset accepted and no downstream gate opened.")
    details={k:audit.get(k) for k in ("status","rows_preserved","parts","option_rows","spot_rows","greek_rows_with_delta","option_rows_missing_spot","option_rows_unmapped_expiry","spot_field_values_filled","hf_revision","source_license","greek_status_counts","expiry_mapping_source_counts","iv_source_counts")}
    append_once(ROOT/"research/logs/CHAT_LOG.md",marker,"- Developer run "+str(req.get("developer_run_id"))+"; artifact "+str(req.get("artifact_id"))+"; decision "+decision+".\n- Artifact ZIP SHA-256: "+bundle_sha+"\n- Coverage summary: "+json.dumps(details,sort_keys=True)+"\n- Findings: "+("; ".join(findings) if findings else "none")+"\n\n**Developer → Tester:** "+("correct discrepancies before resubmitting." if decision!="PASS_WITH_SCOPED_RESTRICTIONS" else "keep economic/strategy gates blocked until separately authorized.")+"\n**Tester → Developer:** "+("reject artifact delivery." if decision!="PASS_WITH_SCOPED_RESTRICTIONS" else "accept only artifact integrity/coverage; no P&L or strategy promotion.") )
    print(json.dumps({"decision":decision,"source_gate":source_gate,"synthetic_tests":synthetic,"download_gate":download_gate,
      "audit_gate":audit_gate,"artifact_sha256":bundle_sha,"findings":findings,
      "summary":{k:audit.get(k) for k in ("rows_preserved","parts","option_rows","spot_rows","greek_rows_with_delta","option_rows_missing_spot","option_rows_unmapped_expiry","spot_field_values_filled")}},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
