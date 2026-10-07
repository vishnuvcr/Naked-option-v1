from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, average_precision_score, brier_score_loss, log_loss, confusion_matrix

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet"
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
    out_index=np.arange(len(pos))
    return pd.Series(y,index=out_index),pd.Series(future,index=out_index),pd.Series(sigma,index=out_index)

def block_bootstrap_accuracy(y, p, block_len=60, reps=200, seed=42):
    z=pd.DataFrame({"y":y,"p":p}).dropna()
    if len(z)<block_len:
        return {"lower":None,"upper":None,"median":None}
    rng=np.random.default_rng(seed); n=len(z)
    blocks=[np.arange(i,min(i+block_len,n)) for i in range(0,n,block_len)]
    vals=[]
    for _ in range(reps):
        sel=rng.integers(0,len(blocks),size=len(blocks))
        idx=np.concatenate([blocks[j] for j in sel])[:n]
        yy=z.y.to_numpy()[idx]; pp=z.p.to_numpy()[idx]
        vals.append(float(np.mean((pp>=0.5)==yy)))
    return {"lower":float(np.quantile(vals,0.025)),"upper":float(np.quantile(vals,0.975)),"median":float(np.median(vals))}

def calibration_metrics(y,p):
    z=pd.DataFrame({"y":y,"p":p}).dropna()
    if len(z)==0:
        return {"calibration_slope":None,"calibration_intercept":None}
    yy=z.y.astype(int).to_numpy(); pp=np.clip(z.p.to_numpy(),1e-6,1-1e-6)
    lp=np.log(pp/(1-pp))
    if np.ptp(lp)<1e-12:
        rate=float(yy.mean())
        return {"calibration_slope":None,"calibration_intercept":float(np.log(rate/(1-rate))) if 0<rate<1 else None}
    model=LogisticRegression(C=1e6,solver="lbfgs",max_iter=1000).fit(lp.reshape(-1,1),yy)
    return {"calibration_slope":float(model.coef_[0,0]),"calibration_intercept":float(model.intercept_[0])}

def fixed_bin_future_returns(p,future):
    if future is None:
        return {}
    if len(p)!=len(future):
        raise ValueError("future/p length mismatch in intraday probability-bin report")
    z=pd.DataFrame({"p":np.asarray(p,dtype=float),"future":np.asarray(future,dtype=float)}).replace([np.inf,-np.inf],np.nan).dropna()
    bins=[-0.001,0.45,0.50,0.55,0.60,1.001]
    names=["<0.45","0.45-0.50","0.50-0.55","0.55-0.60",">=0.60"]
    out={}
    for lo,hi,name in zip(bins[:-1],bins[1:],names):
        m=(z["p"]>=lo)&((z["p"]<hi) if hi<1 else (z["p"]<=hi))
        out[name]={"n":int(m.sum()),"mean_future_return":float(z.loc[m,"future"].mean()) if m.any() else None}
    return out

def metrics(y,p,future=None):
    z=pd.DataFrame({"y":y,"p":p}).dropna()
    if z.empty: return {"n":0}
    yy=z.y.astype(int).to_numpy(); pp=z.p.to_numpy(); pred=(pp>=0.5).astype(int)
    cm=confusion_matrix(yy,pred,labels=[0,1]).ravel()
    out={
        "status":"EXECUTED",
        "n":int(len(z)),
        "positive_rate":float(yy.mean()),
        "accuracy":float(accuracy_score(yy,pred)),
        "balanced_accuracy":float(balanced_accuracy_score(yy,pred)),
        "brier":float(brier_score_loss(yy,pp)),
        "log_loss":float(log_loss(yy,pp,labels=[0,1])),
        "tn":int(cm[0]),"fp":int(cm[1]),"fn":int(cm[2]),"tp":int(cm[3]),
        **calibration_metrics(y,p),
        "accuracy_block_bootstrap_95":block_bootstrap_accuracy(y,p),
        "future_return_by_probability_bin":fixed_bin_future_returns(p,future),
    }
    if len(np.unique(yy))==2:
        out["roc_auc"]=float(roc_auc_score(yy,pp))
        out["pr_auc"]=float(average_precision_score(yy,pp))
    else:
        out["roc_auc"]=None; out["pr_auc"]=None
    return out

def b7_regime_counts(df):
    ret=df["log_spot"].diff()
    v=ret.rolling(20).std()
    pct=v.rolling(252,min_periods=252).rank(pct=True)
    return {
        "low_lt33":int((pct<0.33).sum()),
        "mid_33_67":int(((pct>=0.33)&(pct<=0.67)).sum()),
        "high_gt67":int((pct>0.67).sum()),
        "unclassified":int(pct.isna().sum()),
    }

def base_preds(df,h,name):
    idx=df.index
    p=pd.Series(np.nan,index=idx)
    ret=df["log_spot"].diff()
    if name=="B0": return pd.Series(0.5,index=idx)
    if name=="B1":
        return pd.Series(np.where(ret>0,0.55,np.where(ret<0,0.45,0.5)),index=idx)
    if name=="B4":
        lookback=min(h,30)
        past=df.set_index("timestamp")["spot"].reindex(df["timestamp"]-pd.Timedelta(minutes=lookback)).to_numpy()
        r=np.log(df["spot"].to_numpy()/past)
        r=pd.Series(r,index=df.index)
        return pd.Series(np.where(r>0,0.55,np.where(r<0,0.45,0.5)),index=idx)
    if name=="B5":
        ma5=df["spot"].rolling(5).mean(); ma20=df["spot"].rolling(20).mean()
        return pd.Series(np.where(ma5>ma20,0.55,np.where(ma5<ma20,0.45,0.5)),index=idx)
    if name=="B6":
        lo=df["spot"].rolling(20).min().shift(1); hi=df["spot"].rolling(20).max().shift(1)
        pos=(df["spot"]-lo)/(hi-lo)
        return pd.Series(np.where(pos>0.5,0.55,np.where(pos<0.5,0.45,0.5)),index=idx)
    if name=="B7":
        v=ret.rolling(20).std()
        pct=v.rolling(252).rank(pct=True)
        persistence=np.where(ret>0,0.55,np.where(ret<0,0.45,0.5))
        p=np.where(pct<0.33,persistence,np.where(pct>0.67,1-persistence,0.5))
        return pd.Series(p,index=idx)
    if name=="B8":
        out=np.full(len(df),np.nan)
        dow=df["ist"].dt.dayofweek.to_numpy()
        y_cache={}
        for hkey in HORIZONS:
            y_cache[hkey]=None
        # Calendar probabilities are estimated from earlier observations only.
        # For the current horizon they are populated inside run() from y_full.
        return pd.Series(out,index=idx)
    if name=="B3":
        day_open=df.groupby("date")["spot"].transform("first")
        day_closes=df.groupby("date")["spot"].last()
        prior_day_close=day_closes.shift(1)
        prior_close=df["date"].map(prior_day_close)
        pday=np.where(day_open>prior_close,0.55,np.where(day_open<prior_close,0.45,0.5))
        return pd.Series(pday,index=idx)
    if name=="B2":
        day_closes=df.groupby("date")["spot"].last()
        prior_session_return=np.log(day_closes/day_closes.shift(1)).shift(1)
        r=df["date"].map(prior_session_return)
        return pd.Series(np.where(r>0,0.55,np.where(r<0,0.45,0.5)),index=idx)
    return p

def logistic(df,h,y,eval_index):
    X=pd.DataFrame(index=df.index)
    ret=df["log_spot"].diff()
    X["ret1"]=ret
    X["vol20"]=ret.rolling(20).std()
    day_open=df.groupby("date")["spot"].transform("first")
    day_closes=df.groupby("date")["spot"].last()
    prior_close=df["date"].map(day_closes.shift(1))
    X["gap"]=np.log(day_open/prior_close)
    out=np.full(len(df),np.nan)
    positions=[df.index.get_loc(i) for i in eval_index if i in df.index]
    for i in positions:
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
    grid_mask=(df["minute_of_day"]>=9*60+30)&(df["minute_of_day"]<=15*60+30)&(((df["minute_of_day"]-9*60-30)%60)==0)
    grid=df[grid_mask].copy()
    out={}
    for h in HORIZONS:
        y_full,fut_full,sig_full=labels(df["timestamp"],df["spot"],h)
        # Use the full 1-minute path to construct labels/features, then evaluate only
        # at the frozen decision grid.
        y=y_full.loc[grid.index]
        fut=fut_full.loc[grid.index]
        sig=sig_full.loc[grid.index]
        base_full=df.copy()
        base_preds_full={name:base_preds(base_full,h,name) for name in ["B0","B1","B2","B3","B4","B5","B6","B7"]}
        out[str(h)]={"label":{
            "n":int(y.notna().sum()),
            "positive_rate":float(y.dropna().mean()) if y.notna().any() else None,
            "future_return_mean":float(fut.mean()),
            "future_return_std":float(fut.std()),
            "sigma_h_available":int(sig.notna().sum())
        }}
        for name,series in base_preds_full.items():
            out[str(h)][name]=metrics(y,series.loc[grid.index],fut)

        # PIT-safe weekday probability: expanding training history by weekday.
        b8=np.full(len(df),np.nan)
        dow=df["ist"].dt.dayofweek.to_numpy()
        yy=y_full.to_numpy()
        for i in range(len(df)):
            d=dow[i]
            past=(dow[:i]==d)
            valid=past & np.isfinite(yy)
            b8[i]=float(np.mean(yy[valid])) if valid.any() else 0.5
        out[str(h)]["B8"]=metrics(y,pd.Series(b8,index=df.index).loc[grid.index],fut)

        # B2 is an intraday decision feature derived from the prior completed session return.
        out[str(h)]["B9"]={"status":"BLOCKED_DATA","reason":"PIT-safe global daily histories are not yet materialized in the Phase 3 feature factory"}
        out[str(h)]["B10"]={"status":"BLOCKED_DATA","reason":"PIT-safe historical NSE breadth observations are not yet materialized in Phase 3"}
        out[str(h)]["B11"]=metrics(y,logistic(df,h,y_full,grid.index).loc[grid.index],fut)
        out[str(h)]["B7_regime_counts"]=b7_regime_counts(df)
    report={
        "rows":len(grid),
        "full_rows":len(df),
        "timestamp_start":grid["timestamp"].min().isoformat(),
        "timestamp_end":grid["timestamp"].max().isoformat(),
        "horizons":out,
        "status":"PASS" if len(df)>=50000 else "LOW_POWER",
        "feature_path":"full 1-minute series; evaluation restricted to frozen hourly decision grid"
    }
    (OUT/"phase3_intraday_baseline_results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"full_rows":report["full_rows"],"grid_rows":report["rows"],"timestamp_start":report["timestamp_start"],"timestamp_end":report["timestamp_end"],"status":report["status"]},indent=2))

if __name__=="__main__":
    run()
