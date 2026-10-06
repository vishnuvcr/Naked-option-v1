from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, average_precision_score, brier_score_loss, log_loss

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/cache/raw/phase3/hf_intraday/nifty_intraday_reference.parquet"
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

HORIZONS=[5,15,30,60,120]
DECISION_MINUTES=[30,60,120,180,240,300,360]  # 09:30 through 15:30 IST

def load():
    if not DATA.exists():
        raise SystemExit("NO_DATA: intraday reference parquet missing")
    df=pd.read_parquet(DATA)
    df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True)
    df["spot"]=pd.to_numeric(df["spot"],errors="coerce")
    df=df.dropna(subset=["timestamp","spot"]).sort_values("timestamp").drop_duplicates("timestamp")
    df["ist"]=df["timestamp"].dt.tz_convert("Asia/Kolkata")
    df["date"]=df["ist"].dt.date
    df["minute_of_day"]=df["ist"].dt.hour*60+df["ist"].dt.minute
    # Only regular NIFTY cash-session observations.
    df=df[(df["minute_of_day"]>=9*60+15)&(df["minute_of_day"]<=15*60+30)].copy()
    return df

def labels(ts, price, h):
    idx=pd.DatetimeIndex(ts)
    series=pd.Series(price,index=idx)
    logp=np.log(series)
    y=[]; future=[]; sigma=[]
    pos=logp.index
    for i,t in enumerate(pos):
        ftime=t+pd.Timedelta(minutes=h)
        if ftime not in logp.index:
            y.append(np.nan); future.append(np.nan); sigma.append(np.nan); continue
        ret=logp.loc[ftime]-logp.loc[t]
        y.append(1 if ret>0 else (0 if ret<0 else np.nan))
        future.append(ret)
        vals=[]
        for j in range(1,21):
            end=t-pd.Timedelta(minutes=j*h)
            start=end-pd.Timedelta(minutes=h)
            if start in logp.index and end in logp.index:
                vals.append(logp.loc[end]-logp.loc[start])
        sigma.append(float(np.std(vals,ddof=1)) if len(vals)==20 else np.nan)
    return pd.Series(y,index=pos),pd.Series(future,index=pos),pd.Series(sigma,index=pos)

def metrics(y,p):
    z=pd.DataFrame({"y":y,"p":p}).dropna()
    if z.empty: return {"n":0}
    yy=z.y.astype(int).to_numpy(); pp=z.p.to_numpy(); pred=(pp>=0.5).astype(int)
    out={
        "n":int(len(z)),
        "positive_rate":float(yy.mean()),
        "accuracy":float(accuracy_score(yy,pred)),
        "balanced_accuracy":float(balanced_accuracy_score(yy,pred)),
        "brier":float(brier_score_loss(yy,pp)),
        "log_loss":float(log_loss(yy,pp,labels=[0,1])),
    }
    if len(np.unique(yy))==2:
        out["roc_auc"]=float(roc_auc_score(yy,pp))
        out["pr_auc"]=float(average_precision_score(yy,pp))
    else:
        out["roc_auc"]=None; out["pr_auc"]=None
    return out

def base_preds(df,h,name):
    idx=df.index
    p=pd.Series(np.nan,index=idx)
    ret=df["log_spot"].diff()
    if name=="B0": return pd.Series(0.5,index=idx)
    if name=="B4":
        r=np.log(df["spot"]/df["spot"].shift(h))
        return pd.Series(np.where(r>0,0.55,np.where(r<0,0.45,0.5)),index=idx)
    if name=="B5":
        ma5=df["spot"].rolling(5).mean(); ma20=df["spot"].rolling(20).mean()
        return pd.Series(np.where(ma5>ma20,0.55,np.where(ma5<ma20,0.45,0.5)),index=idx)
    if name=="B6":
        lo=df["spot"].rolling(20).min(); hi=df["spot"].rolling(20).max()
        pos=(df["spot"]-lo)/(hi-lo)
        return pd.Series(np.where(pos>0.5,0.55,np.where(pos<0.5,0.45,0.5)),index=idx)
    if name=="B7":
        v=ret.rolling(20).std()
        pct=v.rolling(252).rank(pct=True)
        raw=np.where(ret>0,0.55,np.where(ret<0,0.45,0.5))
        return pd.Series(raw,index=idx)
    if name=="B8":
        dow=df["ist"].dt.dayofweek
        return pd.Series(np.where(dow==3,0.51,0.5),index=idx)
    if name=="B3":
        day_open=df.groupby("date")["spot"].transform("first")
        prior_close=df["spot"].shift(1)
        pday=np.where(day_open>prior_close,0.55,np.where(day_open<prior_close,0.45,0.5))
        return pd.Series(pday,index=idx)
    return p

def logistic(df,h,y):
    X=pd.DataFrame(index=df.index)
    ret=df["log_spot"].diff()
    X["ret1"]=ret
    X["reth"]=df["log_spot"].diff(h)
    X["vol20"]=ret.rolling(20).std()
    X["ma5gap"]=np.log(df["spot"]/df["spot"].rolling(5).mean())
    X["ma20gap"]=np.log(df["spot"]/df["spot"].rolling(20).mean())
    X["range20"]=(df["spot"]-df["spot"].rolling(20).min())/(df["spot"].rolling(20).max()-df["spot"].rolling(20).min())
    X["dow"]=df["ist"].dt.dayofweek
    X["session_min"]=df["minute_of_day"]
    out=np.full(len(df),np.nan)
    for i in range(300,len(df)):
        train_end=max(0,i-h)
        if train_end<300: continue
        yy=y.iloc[:train_end]
        mask=yy.notna()
        xx=X.iloc[:train_end]
        mask &= xx.notna().all(axis=1)
        yy=yy[mask].astype(int)
        xx=xx[mask]
        if len(yy)<300 or yy.nunique()<2: continue
        mu=xx.mean(); sd=xx.std(ddof=0).replace(0,1)
        xx=(xx-mu)/sd
        xt=X.iloc[[i]]
        if xt.isna().any(axis=1).iloc[0]: continue
        xt=(xt-mu)/sd
        model=LogisticRegression(C=1.0,solver="liblinear",max_iter=1000,class_weight=None)
        model.fit(xx,yy)
        out[i]=model.predict_proba(xt)[0,1]
    return pd.Series(out,index=df.index)

def run():
    df=load()
    df["log_spot"]=np.log(df["spot"])
    # Keep only fixed decision grid times.
    grid_mask=(df["minute_of_day"]>=9*60+30)&(df["minute_of_day"]<=15*60+30)&(((df["minute_of_day"]-9*60-30)%60)==0)
    d=df[grid_mask].copy()
    out={}
    for h in HORIZONS:
        y,fut,sig=labels(d["timestamp"],d["spot"],h)
        out[str(h)]={"label":{"n":int(y.notna().sum()),"positive_rate":float(y.dropna().mean()) if y.notna().any() else None,"future_return_mean":float(fut.mean()),"future_return_std":float(fut.std()),"sigma_h_available":int(sig.notna().sum())}}
        for name in ["B0","B3","B4","B5","B6","B7","B8"]:
            out[str(h)][name]=metrics(y,base_preds(d,h,name))
        out[str(h)]["B11"]=metrics(y,logistic(d,h,y))
    report={"rows":len(d),"timestamp_start":d["timestamp"].min().isoformat(),"timestamp_end":d["timestamp"].max().isoformat(),"horizons":out,"status":"PASS" if len(d)>=50000 else "LOW_POWER"}
    (OUT/"phase3_intraday_baseline_results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"rows":report["rows"],"timestamp_start":report["timestamp_start"],"timestamp_end":report["timestamp_end"],"status":report["status"]},indent=2))

if __name__=="__main__":
    run()
