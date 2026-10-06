from __future__ import annotations

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
)

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/cache/raw/phase3/nse_index_archives/nifty50_daily.csv"
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
    df["gap"]=np.log(df["open"]/df["prev_close"]) if {"open","prev_close"}<=set(df) else np.nan
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

def metrics(y, p):
    y=np.asarray(y,dtype=float)
    p=np.asarray(p,dtype=float)
    m=np.isfinite(y)&np.isfinite(p)
    y=y[m].astype(int); p=p[m]
    if len(y)==0:
        return {"n":0}
    pred=(p>=0.5).astype(int)
    out={
        "n":int(len(y)),
        "positive_rate":float(y.mean()),
        "accuracy":float(accuracy_score(y,pred)),
        "balanced_accuracy":float(balanced_accuracy_score(y,pred)),
        "brier":float(brier_score_loss(y,p)),
        "log_loss":float(log_loss(y,p,labels=[0,1])),
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
    x["ret_h"]=df["log_close"].diff(h)
    x["vol20"]=df["ret_1"].rolling(20).std()
    x["ma5_gap"]=np.log(df["close"]/df["close"].rolling(5).mean())
    x["ma20_gap"]=np.log(df["close"]/df["close"].rolling(20).mean())
    x["range20_pos"]=(df["close"]-df["low"].rolling(20).min())/(df["high"].rolling(20).max()-df["low"].rolling(20).min())
    x["gap"]=df["gap"]
    x["dow"]=df["date"].dt.dayofweek
    x["month_end"]=(df["date"].dt.day>=25).astype(float)
    x["is_expiry_placeholder"]=(df["date"].dt.weekday==3).astype(float)
    return x

def prediction_series(name,df,h,features=None):
    p=pd.Series(np.nan,index=df.index)
    if name=="B0":
        p.iloc[:]=0.5
        return p
    if name=="B1":
        prev=df["log_close"].diff(h).shift(0)
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
        pos=(df["close"]-df["low"].rolling(20).min())/(df["high"].rolling(20).max()-df["low"].rolling(20).min())
        p=np.where(pos>0.5,0.55,np.where(pos<0.5,0.45,0.5))
        return pd.Series(p,index=df.index)
    if name=="B7":
        sigma=df["ret_1"].rolling(20).std()
        pct=sigma.rolling(252,min_periods=252).rank(pct=True)
        persistence=np.where(df["ret_1"]>0,0.55,np.where(df["ret_1"]<0,0.45,0.5))
        p=np.where(pct<0.33,persistence,np.where(pct>0.67,1-persistence,0.5))
        return pd.Series(p,index=df.index)
    if name=="B8":
        dow=df["date"].dt.dayofweek
        # Phase 3 freezes a calendar-only weekday effect; expiry-day labels are
        # deferred until an official historical expiry calendar is joined.
        return pd.Series(np.where(dow==3,0.51,0.5),index=df.index)
    return pd.Series(np.nan,index=df.index)

def logistic_walkforward(df,h):
    y,_=make_label(df,h)
    X=deterministic_features(df,h)
    cols=["ret_1","ret_h","vol20","ma5_gap","ma20_gap","range20_pos","gap","dow","month_end"]
    out=np.full(len(df),np.nan)
    train_start=max(252,20*h+20)
    for i in range(train_start,len(df)):
        # Purge observations whose H-step label would overlap the current
        # decision timestamp. Training labels must end strictly before i.
        train_end=max(0,i-h)
        y_train=y.iloc[:train_end]
        mask=y_train.notna()
        x_train=X.iloc[:i][cols].copy()
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
            result[str(h)][name]=metrics(y,p)
        result[str(h)]["B11"]=metrics(y,logistic_walkforward(df,h))
    out={"data_rows":len(df),"date_start":df["date"].min().date().isoformat(),"date_end":df["date"].max().date().isoformat(),"horizons":result}
    (OUT/"phase3_daily_baseline_results.json").write_text(json.dumps(out,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    run()
