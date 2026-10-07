from __future__ import annotations
import json
from pathlib import Path
import math

METHODS=[f"D{i:02d}" for i in range(1,16)]
DAILY=["1","2","3","5","10"]
INTRA=["5","15","30","60","120"]

def finite_or_none(x):
    return x is None or (isinstance(x,(int,float)) and math.isfinite(x))

def main(path: str):
    d=json.loads(Path(path).read_text())
    assert d["daily"]["horizons"].keys() >= set(DAILY)
    assert d["intraday"]["horizons"].keys() >= set(INTRA)
    for layer,hs in (("daily",DAILY),("intraday",INTRA)):
        for h in hs:
            v=d[layer]["horizons"][h]
            assert set(v)==set(METHODS)
            for m in METHODS:
                r=v[m]
                assert r.get("status") in {"EXECUTED","BLOCKED_DATA","BLOCKED_RUNTIME"} and r.get("status") is not None
                if r.get("status")=="EXECUTED":
                    n=int(r["n"])
                    assert n>=0
                    for key in ["accuracy","balanced_accuracy","brier","log_loss","roc_auc","pr_auc"]:
                        if key in r: assert finite_or_none(r[key]), (layer,h,m,key,r[key])
                    if all(k in r for k in ["tn","fp","fn","tp"]):
                        assert r["tn"]+r["fp"]+r["fn"]+r["tp"]==n, (layer,h,m,"cm")
                    bins=r.get("future_return_by_probability_bin")
                    if isinstance(bins,dict):
                        counts=[int(x.get("n",0)) for x in bins.values() if isinstance(x,dict) and "n" in x]
                        if counts: assert sum(counts)<=n, (layer,h,m,"bins")
                elif r.get("status")=="BLOCKED_RUNTIME":
                    assert r.get("reason")
            for m in ["D04","D05","D06"]:
                note=v[m].get("implementation_note","")
                assert "surrogate" in note.lower(), (layer,h,m,note)
    print("PHASE5_TESTER_SCHEMA_PASS")

if __name__=="__main__":
    import sys
    main(sys.argv[1])
