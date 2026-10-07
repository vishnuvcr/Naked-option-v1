from __future__ import annotations

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, roc_auc_score,
    average_precision_score, brier_score_loss, log_loss, confusion_matrix,
)

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/cache/raw/phase3/nifty50_daily.csv"
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

HORIZONS=[1,2,3,5,10]

def load_daily():
    if not DATA.exists():
        raise SystemExit(f"NO_DATA: {DATA} not found")
    df=pd.read_csv(DATA)
    df["date"]=pd.to_datetime(df["date"])
    for c in ["open","high","low","close","prev_close"]:
        if c in df:
            df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df["log_close"]=np.log(df["close"])
    df["ret_1"]=df["log_close"].diff()
    prev_close=df["close"].shift(1)
    df["gap"]=np.log(df["open"]/prev_close)
    return df

def horizon_sigma(df,h):
    # 20 non-overlapping H-session returns ending no later than t.
    vals=np.full(len(df),np.nan)
    r=df["log_close"].diff(h).to_numpy()
    for i in range(20*h, len(df)):
        window=[]
        for j in range(1,21):
            end=i-j*h
            start=end-h
            if start>=0 and np.isfinite(r[end]):
                window.append(r[end])
        if len(window)==20:
            vals[i]=float(np.std(window,ddof=1))
    return pd.Series(vals,index=df.index)

def make_label(df,h):
    future=np.log(df["close"].shift(-h)/df["close"])
    y=np.where(future>0,1,np.where(future<0,0,np.nan))
    return pd.Series(y,index=df.index),future

def block_bootstrap_accuracy(y, p, block_len=20, reps=200, seed=42):
    y=np.asarray(y,dtype=float); p=np.asarray(p,dtype=float)
    m=np.isfinite(y)&np.isfinite(p); y=y[m].astype(int); p=p[m]
    if len(y)<block_len:
        return {"lower":None,"upper":None,"median":None}
    rng=np.random.default_rng(seed)
    blocks=[np.arange(i,min(i+block_len,len(y))) for i in range(0,len(y),block_len)]
    vals=[]
    for _ in range(reps):
        sel=rng.integers(0,len(blocks),size=len(blocks))
        idx=np.concatenate([blocks[j] for j in sel])[:len(y)]
        vals.append(float(np.mean((p[idx]>=0.5)==y[idx])))
    return {"lower":float(np.quantile(vals,0.025)),"upper":float(np.quantile(vals,0.975)),"median":float(np.median(vals))}

def calibration_metrics(y,p):
    y=np.asarray(y,dtype=float); p=np.asarray(p,dtype=float)
    m=np.isfinite(y)&np.isfinite(p); y=y[m].astype(int); p=np.clip(p[m],1e-6,1-1e-6)
    if len(y)==0:
        return {"calibration_slope":None,"calibration_intercept":None}
    lp=np.log(p/(1-p))
    if np.ptp(lp)<1e-12:
        rate=float(y.mean())
        return {"calibration_slope":None,"calibration_intercept":float(np.log(rate/(1-rate))) if 0<rate<1 else None}
    model=LogisticRegression(C=1e6,solver="lbfgs",max_iter=1000).fit(lp.reshape(-1,1),y)
    return {"calibration_slope":float(model.coef_[0,0]),"calibration_intercept":float(model.intercept_[0])}

def fixed_bin_future_returns(y,p,future):
    if future is None:
        return {}
    z=pd.DataFrame({"p":p,"future":future}).replace([np.inf,-np.inf],np.nan).dropna()
    bins=[-0.001,0.45,0.50,0.55,0.60,1.001]
    names=["<0.45","0.45-0.50","0.50-0.55","0.55-0.60",">=0.60"]
    out={}
    for lo,hi,name in zip(bins[:-1],bins[1:],names):
        m=(z["p"]>=lo)&(z["p"]<hi if hi<1 else z["p"]<=hi)
        out[name]={"n":int(m.sum()),"mean_future_return":float(z.loc[m,"future"].mean()) if m.any() else None}
    return out

def metrics(y, p, future=None):
    y=np.asarray(y,dtype=float)
    p=np.asarray(p,dtype=float)
    m=np.isfinite(y)&np.isfinite(p)
    future_arr=None
    if future is not None:
        future_arr=np.asarray(future,dtype=float)
        if len(future_arr)!=len(m):
            raise ValueError("future/y/p length mismatch before metric masking")
        future_arr=future_arr[m]
    y=y[m].astype(int); p=p[m]
    if len(y)==0:
        return {"n":0}
    pred=(p>=0.5).astype(int)
    cm=confusion_matrix(y,pred,labels=[0,1]).ravel()
    out={
        "status":"EXECUTED",
        "n":int(len(y)),
        "positive_rate":float(y.mean()),
        "accuracy":float(accuracy_score(y,pred)),
        "balanced_accuracy":float(balanced_accuracy_score(y,pred)),
        "brier":float(brier_score_loss(y,p)),
        "log_loss":float(log_loss(y,p,labels=[0,1])),
        "tn":int(cm[0]),"fp":int(cm[1]),"fn":int(cm[2]),"tp":int(cm[3]),
        **calibration_metrics(y,p),
        "accuracy_block_bootstrap_95":block_bootstrap_accuracy(y,p),
        "future_return_by_probability_bin":fixed_bin_future_returns(y,p,future_arr),
    }
    if len(np.unique(y))==2:
        out["roc_auc"]=float(roc_auc_score(y,p))
        out["pr_auc"]=float(average_precision_score(y,p))
    else:
        out["roc_auc"]=None
        out["pr_auc"]=None
    return out

def deterministic_features(df,h):
    x=pd.DataFrame(index=df.index)
    x["ret_1"]=df["ret_1"]
    x["vol20"]=df["ret_1"].rolling(20).std()
    x["gap"]=df["gap"]
    return x

def b7_regime_counts(df):
    sigma=df["ret_1"].rolling(20).std()
    pct=sigma.rolling(252,min_periods=252).rank(pct=True)
    return {
        "low_lt33":int((pct<0.33).sum()),
        "mid_33_67":int(((pct>=0.33)&(pct<=0.67)).sum()),
        "high_gt67":int((pct>0.67).sum()),
        "unclassified":int(pct.isna().sum()),
    }

def pit_weekday_probability_daily(df, y_full, h):
    """Weekday probability using only labels whose h-session endpoint is before decision."""
    y_arr=np.asarray(y_full,dtype=float)
    out=np.full(len(df),0.5,dtype=float)
    dow=df["date"].dt.dayofweek.to_numpy()
    for d in np.unique(dow):
        pos=np.flatnonzero(dow==d)
        for i in pos:
            cutoff=i-h
            if cutoff<=0:
                continue
            eligible=pos[pos<cutoff]
            vals=y_arr[eligible]
            vals=vals[np.isfinite(vals)]
            if len(vals):
                out[i]=float(vals.mean())
    return pd.Series(out,index=df.index)

def prediction_series(name,df,h,features=None):
    p=pd.Series(np.nan,index=df.index)
    if name=="B0":
        p.iloc[:]=0.5
        return p
    if name=="B1":
        prev=df["ret_1"]
        p=np.where(prev>0,0.55,np.where(prev<0,0.45,0.5))
        return pd.Series(p,index=df.index)
    if name=="B2":
        prev=df["ret_1"]
        p=np.where(prev>0,0.55,np.where(prev<0,0.45,0.5))
        return pd.Series(p,index=df.index)
    if name=="B5":
        state=np.where(df["close"].rolling(5).mean()>df["close"].rolling(20).mean(),1,0)
        p=np.where(state==1,0.55,0.45)
        return pd.Series(p,index=df.index)
    if name=="B6":
        prior_lo=df["low"].rolling(20).min().shift(1)
        prior_hi=df["high"].rolling(20).max().shift(1)
        pos=(df["close"]-prior_lo)/(prior_hi-prior_lo)
        p=np.where(pos>0.5,0.55,np.where(pos<0.5,0.45,0.5))
        return pd.Series(p,index=df.index)
    if name=="B7":
        sigma=df["ret_1"].rolling(20).std()
        pct=sigma.rolling(252,min_periods=252).rank(pct=True)
        persistence=np.where(df["ret_1"]>0,0.55,np.where(df["ret_1"]<0,0.45,0.5))
        p=np.where(pct<0.33,persistence,np.where(pct>0.67,1-persistence,0.5))
        return pd.Series(p,index=df.index)
    if name=="B8":
        y_hist,_=make_label(df,h)
        return pit_weekday_probability_daily(df,y_hist,h)
    return pd.Series(np.nan,index=df.index)

def logistic_walkforward(df,h):
    y,_=make_label(df,h)
    X=deterministic_features(df,h)
    cols=["ret_1","vol20","gap"]
    out=np.full(len(df),np.nan)
    train_start=max(252,20*h+20)
    for i in range(train_start,len(df)):
        # Purge observations whose H-step label would overlap the current
        # decision timestamp. Training labels must end strictly before i.
        train_end=max(0,i-h)
        y_train=y.iloc[:train_end]
        mask=y_train.notna()
        x_train=X.iloc[:train_end][cols].copy()
        mask &= x_train.notna().all(axis=1)
        yv=y_train[mask].astype(int)
        if len(yv)<200 or yv.nunique()<2:
            continue
        x_train=x_train[mask]
        mu=x_train.mean(); sd=x_train.std(ddof=0).replace(0,1)
        x_train=(x_train-mu)/sd
        x_test=X.iloc[[i]][cols]
        if x_test.isna().any(axis=1).iloc[0]:
            continue
        x_test=(x_test-mu)/sd
        model=LogisticRegression(C=1.0,solver="liblinear",max_iter=1000,class_weight=None)
        model.fit(x_train,yv)
        out[i]=model.predict_proba(x_test)[0,1]
    return pd.Series(out,index=df.index)

def run():
    df=load_daily()
    result={}
    for h in HORIZONS:
        y,future=make_label(df,h)
        sig=horizon_sigma(df,h)
        result[str(h)]={"label":{
            "n":int(y.notna().sum()),
            "positive_rate":float(y.dropna().mean()),
            "future_return_mean":float(future.mean()),
            "future_return_std":float(future.std()),
            "sigma_h_available":int(sig.notna().sum()),
        }}
        for name in ["B0","B1","B2","B5","B6","B7","B8"]:
            p=prediction_series(name,df,h)
            result[str(h)][name]=metrics(y,p,future)

        result[str(h)]["B3"]={"status":"NOT_APPLICABLE","reason":"B3 is defined as intraday gap sign only"}
        result[str(h)]["B4"]={"status":"NOT_APPLICABLE","reason":"B4 is defined as intraday momentum only"}
        result[str(h)]["B9"]={"status":"BLOCKED_DATA","reason":"PIT-safe global daily histories are not yet materialized in the Phase 3 feature factory"}
        result[str(h)]["B10"]={"status":"BLOCKED_DATA","reason":"PIT-safe historical NSE breadth observations are not yet materialized in Phase 3"}
        result[str(h)]["B11"]=metrics(y,logistic_walkforward(df,h),future)
        result[str(h)]["B7_regime_counts"]=b7_regime_counts(df)
    out={"data_rows":len(df),"date_start":df["date"].min().date().isoformat(),"date_end":df["date"].max().date().isoformat(),"horizons":result}
    (OUT/"phase3_daily_baseline_results.json").write_text(json.dumps(out,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    run()
