from __future__ import annotations
from pathlib import Path
import json, math, warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import run_phase6_novel as p6

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/reports"; OUT.mkdir(parents=True,exist_ok=True)
DAILY_H=[1,2,3,5,10]; INTRA_H=[5,15,30,60,120]
METHODS=[f"E{i:02d}" for i in range(1,11)]+[f"I{i:02d}" for i in range(1,11)]
BLOCKED={"E07","I02","I04","I06","I07","I10"}
CAPTURE_ORDER=[m for m in METHODS if m not in BLOCKED]+["I09"]
SEED=42; EPS=1e-12
ABSTAIN={"P05":(0.45,0.55),"P06":(0.40,0.60)}

def capture_scope(df,intraday,horizons):
    captured={}
    original_metrics=p6.metrics
    counter={"i":0}
    try:
        for H in horizons:
            current_h=H
            counter["i"]=0
            def hook(y,p,future,block_len,extra=None,mask=None):
                i=counter["i"]; m=CAPTURE_ORDER[i%len(CAPTURE_ORDER)]
                key=(str(current_h),m)
                if key not in captured:
                    captured[key]={"y":np.asarray(y,float).copy(),"future":np.asarray(future,float).copy(),"p":np.asarray(p,float).copy()}
                counter["i"]+=1
                return {"status":"EXECUTED","n":int(np.isfinite(y).sum())}
            p6.metrics=hook
            p6.run_scope(df,intraday=intraday,horizons=[current_h])
    finally:
        p6.metrics=original_metrics
    return captured

def blocks_for(df,intraday):
    if not intraday:
        return [np.arange(i,min(i+20,len(df))) for i in range(0,len(df),20)]
    grid=(df["minute_of_day"]>=570)&(df["minute_of_day"]<=930)&(((df["minute_of_day"]-570)%60)==0)
    idx=np.flatnonzero(grid.to_numpy())
    groups=df["date"].iloc[idx].reset_index(drop=True)
    sessions=pd.Index(groups.drop_duplicates())
    out=[]
    for s in range(0,len(sessions),20):
        rows=np.flatnonzero(groups.isin(set(sessions[s:s+20])).to_numpy())
        if len(rows): out.append(rows)
    return out

def regime_inputs(df,intraday):
    if intraday:
        grid=(df["minute_of_day"]>=570)&(df["minute_of_day"]<=930)&(((df["minute_of_day"]-570)%60)==0)
        idx=np.flatnonzero(grid.to_numpy())
        ret=np.log(df["spot"].astype(float)).diff().to_numpy()
    else:
        idx=np.arange(len(df)); ret=df["log_close"].diff().to_numpy()
    vol=pd.Series(ret).rolling(20).std(ddof=1).to_numpy()
    trend=np.abs(pd.Series(ret).rolling(20).mean().to_numpy())/(vol+EPS)
    return vol[idx],trend[idx]

def combine(base):
    arr=np.vstack([base[m] for m in METHODS if m not in BLOCKED])
    p1=np.nanmean(arr,axis=0); p2=np.nanmedian(arr,axis=0)
    p3=np.full(len(p1),np.nan)
    for i in range(len(p3)):
        v=arr[:,i]; v=v[np.isfinite(v)]
        if len(v)==0: continue
        k=int(math.floor(0.10*len(v)))
        p3[i]=float(np.mean(v) if k==0 else np.mean(np.sort(v)[k:-k]))
    e=np.vstack([base[m] for m in METHODS[:10] if m not in BLOCKED])
    ii=np.vstack([base[m] for m in METHODS[10:] if m not in BLOCKED])
    pe=np.nanmean(e,axis=0); pi=np.nanmean(ii,axis=0)
    p4=np.nanmean(np.vstack([pe,pi]),axis=0)
    return p1,p2,p3,p4

def stacking(base,y,blocks):
    names=[m for m in METHODS if m not in BLOCKED]
    X=np.column_stack([base[m] for m in names]); out=np.full(len(y),np.nan)
    for rows in blocks:
        if not len(rows): continue
        tr=np.arange(rows[0]); ok=np.isfinite(y[tr])&np.all(np.isfinite(X[tr]),axis=1)
        tr=tr[ok]
        if len(tr)<200 or np.unique(y[tr]).size<2: continue
        model=LogisticRegression(C=1.0,solver="lbfgs",max_iter=500,random_state=SEED)
        model.fit(X[tr],y[tr].astype(int))
        ok=np.all(np.isfinite(X[rows]),axis=1)
        if ok.any(): out[rows[ok]]=model.predict_proba(X[rows[ok]])[:,1]
    return out

def regimes(p1,p4,y,vol,trend,blocks):
    p8=np.full(len(p1),np.nan); p9=np.full(len(p1),np.nan)
    diag=[]; fallback=0
    for rows in blocks:
        tr=np.arange(rows[0])
        vv=vol[tr][np.isfinite(vol[tr])]; tt=trend[tr][np.isfinite(trend[tr])]
        if len(vv)<200 or len(tt)<200: continue
        vc=float(np.median(vv)); tc=float(np.median(tt))
        valid_y=np.isfinite(y[tr]); pooled=float(np.mean(y[tr][valid_y])) if valid_y.any() else 0.5
        state_rates={}; train_counts={}
        for vs in (0,1):
            for ts in (0,1):
                m=valid_y & ((vol[tr]>vc).astype(int)==vs) & ((trend[tr]>tc).astype(int)==ts)
                n=int(m.sum()); train_counts[f"{vs}{ts}"]=n
                if n>=50: state_rates[(vs,ts)]=float(np.mean(y[tr][m]))
                else: state_rates[(vs,ts)]=pooled; fallback+=1
        test_counts={f"{vs}{ts}":0 for vs in (0,1) for ts in (0,1)}
        for r in rows:
            if np.isfinite(p1[r]) and np.isfinite(p4[r]) and np.isfinite(vol[r]) and np.isfinite(trend[r]):
                state=(int(vol[r]>vc),int(trend[r]>tc)); test_counts[f"{state[0]}{state[1]}"]+=1
                q=state_rates[state]
                p8[r]=0.5*p1[r]+0.5*q
                p9[r]=0.5*p4[r]+0.5*q
        diag.append({"train_counts":train_counts,"test_counts":test_counts,"vol_cut":vc,"trend_cut":tc})
    return p8,p9,diag,fallback

def causal_baseline(y,blocks):
    b=np.full(len(y),np.nan)
    for rows in blocks:
        if not len(rows): continue
        tr=np.arange(rows[0]); yy=y[tr][np.isfinite(y[tr])]
        if len(yy)>=200: b[rows]=float(np.mean(yy))
    return b

def block_diagnostics(y,p,blocks):
    out=[]
    for rows in blocks:
        mask=np.isfinite(y[rows])&np.isfinite(p[rows])
        if not mask.any(): continue
        yy=y[rows][mask].astype(int); pp=np.clip(p[rows][mask],1e-6,1-1e-6)
        pred=(pp>=0.5).astype(int)
        out.append({"n":int(len(yy)),"accuracy":float(np.mean(pred==yy)),
                    "balanced_accuracy":float(p6.balanced_accuracy_score(yy,pred)),
                    "brier":float(np.mean((pp-yy)**2))})
    return out

def family_bootstrap(y,candidates,baseline,block_len):
    names=list(candidates); n=len(y); diffs=np.full((n,len(names)),np.nan)
    for j,name in enumerate(names):
        p=candidates[name].copy()
        finite=np.isfinite(y)&np.isfinite(p)&np.isfinite(baseline)
        if name in ABSTAIN:
            lo,hi=ABSTAIN[name]; trade=finite&~((p>=lo)&(p<=hi))
            d=np.zeros(n); d[trade]=(baseline[trade]-y[trade])**2-(p[trade]-y[trade])**2
            diffs[:,j]=d
        else:
            diffs[finite,j]=(baseline[finite]-y[finite])**2-(p[finite]-y[finite])**2
    means=np.nanmean(diffs,axis=0); observed=float(np.nanmax(means))
    centered=diffs-means
    rng=np.random.default_rng(SEED); starts=np.arange(0,n,block_len)
    idx_blocks=[np.arange(s,min(s+block_len,n)) for s in starts]
    boot=np.empty(500)
    for b in range(500):
        sel=rng.integers(0,len(idx_blocks),size=len(idx_blocks))
        idx=np.concatenate([idx_blocks[k] for k in sel])[:n]
        boot[b]=float(np.nanmax(np.nanmean(centered[idx],axis=0)))
    return {"observed_max_brier_improvement":observed,
            "family_p_value":float(np.mean(boot>=observed)),
            "candidate_mean_brier_improvement":{name:float(v) for name,v in zip(names,means)}}

def run_layer(df,intraday,horizons):
    captured=capture_scope(df,intraday,horizons); blocks=blocks_for(df,intraday)
    vol,trend=regime_inputs(df,intraday); block_len=60 if intraday else 20
    out={}
    for H in horizons:
        base={m:captured[(str(H),m)]["p"] for m in METHODS if (str(H),m) in captured}
        y=captured[(str(H),"E01")]["y"]; future=captured[(str(H),"E01")]["future"]
        for m in BLOCKED: base[m]=np.full(len(y),np.nan)
        p1,p2,p3,p4=combine(base); p7=stacking(base,y,blocks); p8,p9,regime_diag,regime_fallbacks=regimes(p1,p4,y,vol,trend,blocks)
        cand={"P01":p1,"P02":p2,"P03":p3,"P04":p4,"P05":p1.copy(),"P06":p1.copy(),"P07":p7,"P08":p8,"P09":p9,"P10":p9.copy()}
        ho={}
        baseline=causal_baseline(y,blocks)
        family=family_bootstrap(y,cand,baseline,block_len)
        for name,p in cand.items():
            mask=None; extra={}
            if name in ABSTAIN:
                lo,hi=ABSTAIN[name]; finite=np.isfinite(p); mask=finite&~((p>=lo)&(p<=hi))
                extra={"coverage":float(mask.sum()/finite.sum()) if finite.sum() else 0.0,"trade_n":int(mask.sum()),"evaluable_n":int(finite.sum())}
            res=p6.metrics(y,p,future,block_len,extra=extra,mask=mask)
            res["chronological_blocks"]=block_diagnostics(y,p,blocks)
            if name in ("P08","P09","P10"):
                res["regime_diagnostics"]=regime_diag
                res["regime_fallback_count"]=int(regime_fallbacks)
            ho[name]=res
        ho["_FAMILY_TEST"]=family
        out[str(H)]=ho
    return out

def main():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        d=p6.load_daily(); q=p6.load_intraday()
        out={"protocol":"research/phase7/PHASE7_METHOD_SPEC.md","seed":SEED,
             "daily":{"rows":int(len(d)),"horizons":run_layer(d,False,DAILY_H)},
             "intraday":{"rows":int(len(q)),"horizons":run_layer(q,True,INTRA_H)}}
    (OUT/"phase7_ensemble_results.json").write_text(json.dumps(out,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps({"status":"PASS","daily_rows":len(d),"intraday_rows":len(q)}))

if __name__=="__main__": main()
