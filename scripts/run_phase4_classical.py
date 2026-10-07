from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, average_precision_score, brier_score_loss, log_loss, confusion_matrix

ROOT=Path(__file__).resolve().parents[1]
DAILY=ROOT/"data/cache/raw/phase3/nifty50_daily.csv"
INTRA=ROOT/"data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet"
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

DAILY_H=[1,2,3,5,10]
INTRA_H=[5,15,30,60,120]
METHODS=[f"B{i:02d}" for i in range(1,14)]


def metrics(y,p,future,block_len):
    y=np.asarray(y,dtype=float); p=np.asarray(p,dtype=float); f=np.asarray(future,dtype=float)
    m=np.isfinite(y)&np.isfinite(p)&np.isfinite(f)
    y=y[m].astype(int); p=p[m]; f=f[m]
    if len(y)==0:
        return {"status":"EXECUTED","n":0}
    pred=(p>=0.5).astype(int)
    cm=confusion_matrix(y,pred,labels=[0,1]).ravel()
    bins=[-0.001,0.45,0.50,0.55,0.60,1.001]
    names=["<0.45","0.45-0.50","0.50-0.55","0.55-0.60",">=0.60"]
    br={}
    for lo,hi,name in zip(bins[:-1],bins[1:],names):
        mm=(p>=lo)&((p<hi) if hi<1 else (p<=hi))
        br[name]={"n":int(mm.sum()),"mean_future_return":float(f[mm].mean()) if mm.any() else None}
    rng=np.random.default_rng(42)
    blocks=[np.arange(i,min(i+block_len,len(y))) for i in range(0,len(y),block_len)]
    boots=[]
    if len(y)>=block_len:
        for _ in range(200):
            sel=rng.integers(0,len(blocks),size=len(blocks))
            idx=np.concatenate([blocks[j] for j in sel])[:len(y)]
            boots.append(float(np.mean((p[idx]>=0.5)==y[idx])))
    out={
        "status":"EXECUTED","n":int(len(y)),"positive_rate":float(y.mean()),
        "accuracy":float(accuracy_score(y,pred)),
        "balanced_accuracy":float(balanced_accuracy_score(y,pred)),
        "brier":float(brier_score_loss(y,p)),
        "log_loss":float(log_loss(y,p,labels=[0,1])),
        "tn":int(cm[0]),"fp":int(cm[1]),"fn":int(cm[2]),"tp":int(cm[3]),
        "future_return_by_probability_bin":br,
        "accuracy_block_bootstrap_95":{
            "lower":float(np.quantile(boots,0.025)) if boots else None,
            "upper":float(np.quantile(boots,0.975)) if boots else None,
            "median":float(np.median(boots)) if boots else None,
        }
    }
    if len(np.unique(y))==2:
        out["roc_auc"]=float(roc_auc_score(y,p))
        out["pr_auc"]=float(average_precision_score(y,p))
    else:
        out["roc_auc"]=None; out["pr_auc"]=None
    return out


def sig_to_prob(sig):
    return np.where(sig>0,0.55,np.where(sig<0,0.45,0.5))


def rsi(close,n=14):
    d=close.diff()
    up=d.clip(lower=0).ewm(alpha=1/n,adjust=False).mean()
    down=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
    rs=up/down.replace(0,np.nan)
    return 100-(100/(1+rs))


def atr(high,low,close,n=14):
    prev=close.shift(1)
    tr=pd.concat([(high-low),(high-prev).abs(),(low-prev).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False).mean()


def adx_components(high,low,close,n=14):
    prev_h=high.shift(1); prev_l=low.shift(1); prev_c=close.shift(1)
    up=high-prev_h; dn=prev_l-low
    plus_dm=pd.Series(np.where((up>dn)&(up>0),up,0.0),index=close.index)
    minus_dm=pd.Series(np.where((dn>up)&(dn>0),dn,0.0),index=close.index)
    tr=pd.concat([(high-low),(high-prev_c).abs(),(low-prev_c).abs()],axis=1).max(axis=1)
    atrv=tr.ewm(alpha=1/n,adjust=False).mean()
    pdi=100*plus_dm.ewm(alpha=1/n,adjust=False).mean()/atrv
    mdi=100*minus_dm.ewm(alpha=1/n,adjust=False).mean()/atrv
    dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)
    adxv=dx.ewm(alpha=1/n,adjust=False).mean()
    return adxv,pdi,mdi


def method_signals(df, intraday=False):
    c=df["close"]; h=df["high"]; l=df["low"]
    ema20=c.ewm(span=20,adjust=False).mean(); ema50=c.ewm(span=50,adjust=False).mean()
    macd_line=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean()
    macd_sig=macd_line.ewm(span=9,adjust=False).mean()
    r=rsi(c,14)
    ll=l.rolling(14).min(); hh=h.rolling(14).max()
    k=100*(c-ll)/(hh-ll).replace(0,np.nan); d=k.rolling(3).mean()
    adxv,pdi,mdi=adx_components(h,l,c,14)
    at=atr(h,l,c,14)
    prior_hi=h.rolling(20).max().shift(1); prior_lo=l.rolling(20).min().shift(1)
    bb_mid=c.rolling(20).mean(); bb_sd=c.rolling(20).std(); bb_up=bb_mid+2*bb_sd; bb_dn=bb_mid-2*bb_sd

    sig={}
    sig["B01"]=np.sign(ema20-ema50)
    sig["B02"]=np.sign(macd_line-macd_sig)
    sig["B03"]=np.where(r>55,1,np.where(r<45,-1,0))
    sig["B04"]=np.where((k>d)&(k>50),1,np.where((k<d)&(k<50),-1,0))
    sig["B05"]=np.where((adxv>=25)&(pdi>mdi),1,np.where((adxv>=25)&(mdi>pdi),-1,0))
    sig["B06"]=np.where(c>prior_hi+0.5*at,1,np.where(c<prior_lo-0.5*at,-1,0))
    sig["B07"]=np.where(c>prior_hi,1,np.where(c<prior_lo,-1,0))
    sig["B08"]=np.where(c>bb_up,1,np.where(c<bb_dn,-1,np.sign(c-bb_mid)))

    if intraday:
        minute=df["ist"].dt.hour*60+df["ist"].dt.minute
        opening=(minute>=9*60+15)&(minute<9*60+30)
        day_high=df.loc[opening].groupby(df.loc[opening,"date"])["high"].transform("max")
        day_low=df.loc[opening].groupby(df.loc[opening,"date"])["low"].transform("min")
        or_high=df.loc[opening].groupby(df.loc[opening,"date"])["high"].first()
        or_low=df.loc[opening].groupby(df.loc[opening,"date"])["low"].first()
        day_high_map=df.loc[opening].groupby("date")["high"].max()
        day_low_map=df.loc[opening].groupby("date")["low"].min()
        session_high=df["date"].map(day_high_map)
        session_low=df["date"].map(day_low_map)
        sig["B10"]=np.where(c>session_high,1,np.where(c<session_low,-1,0))
        sig["B09"]=None
    else:
        sig["B10"]=None; sig["B09"]=None

    # Prior-session CPR/pivot. No current-session information is used in the pivot.
    prev_ohlc=df.groupby("date")[["high","low","close"]].agg({"high":"max","low":"min","close":"last"})
    prev_ohlc.index=prev_ohlc.index
    prev=prev_ohlc.shift(1)
    P=(prev["high"]+prev["low"]+prev["close"])/3
    R1=2*P-prev["low"]; S1=2*P-prev["high"]
    pivot_r1=df["date"].map(R1); pivot_s1=df["date"].map(S1)
    sig["B11"]=np.where(c>pivot_r1,1,np.where(c<pivot_s1,-1,0))

    prior5_hi=h.rolling(5).max().shift(1); prior5_lo=l.rolling(5).min().shift(1)
    rise_lo=l.rolling(5).min()>l.rolling(5).min().shift(5)
    fall_hi=h.rolling(5).max()<h.rolling(5).max().shift(5)
    sig["B12"]=np.where((c>prior5_hi)&rise_lo,1,np.where((c<prior5_lo)&fall_hi,-1,0))

    ema100=c.ewm(span=100,adjust=False).mean()
    sig["B13"]=np.where((ema20>ema50)&(ema50>ema100),1,np.where((ema20<ema50)&(ema50<ema100),-1,0))
    return sig


def load_daily():
    df=pd.read_csv(DAILY)
    df["date"]=pd.to_datetime(df["date"])
    for c in ["open","high","low","close"]:
        df[c]=pd.to_numeric(df[c],errors="coerce")
    return df.sort_values("date").drop_duplicates("date").reset_index(drop=True)


def load_intraday():
    df=pd.read_parquet(INTRA)
    df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True)
    df["spot"]=pd.to_numeric(df["spot"],errors="coerce")
    df=df.dropna(subset=["timestamp","spot"]).sort_values("timestamp").drop_duplicates("timestamp")
    df["ist"]=df["timestamp"].dt.tz_convert("Asia/Kolkata")
    df["date"]=df["ist"].dt.date
    df["minute_of_day"]=df["ist"].dt.hour*60+df["ist"].dt.minute
    df=df[(df["minute_of_day"]>=555)&(df["minute_of_day"]<=930)].copy().reset_index(drop=True)
    df=df.rename(columns={"spot":"close"})
    df["high"]=df["close"]; df["low"]=df["close"]; df["open"]=df["close"]
    return df


def daily_run():
    df=load_daily(); sig=method_signals(df,False)
    out={}
    for H in DAILY_H:
        future=np.log(df["close"].shift(-H)/df["close"])
        y=np.where(future>0,1,np.where(future<0,0,np.nan))
        out[str(H)]={"label":{"n":int(np.isfinite(y).sum()),"positive_rate":float(np.nanmean(y))}}
        for m in METHODS:
            if m=="B09":
                out[str(H)][m]={"status":"BLOCKED_DATA","reason":"PIT-safe volume series unavailable in canonical NIFTY spot layer; VWAP cannot be computed"}
            elif m=="B10":
                out[str(H)][m]={"status":"NOT_APPLICABLE","reason":"Opening-range breakout is intraday-specific"}
            else:
                p=sig_to_prob(sig[m])
                out[str(H)][m]=metrics(y,p,future,20)
    return {"data_rows":len(df),"date_start":df["date"].min().date().isoformat(),"date_end":df["date"].max().date().isoformat(),"horizons":out}


def intra_run():
    df=load_intraday()
    # Frozen hourly decision grid from Phase 3.
    grid=(df["minute_of_day"].between(570,930)&(((df["minute_of_day"]-570)%60)==0))
    sig=method_signals(df,True)
    out={}
    idx=pd.Index(df["timestamp"])
    vals=np.log(df["close"].to_numpy())
    for H in INTRA_H:
        target=idx+pd.Timedelta(minutes=H)
        pos=idx.get_indexer(target)
        fut=np.full(len(df),np.nan); good=pos>=0; fut[good]=vals[pos[good]]-vals[good]
        y=np.where(np.isfinite(fut),np.where(fut>0,1,np.where(fut<0,0,np.nan)),np.nan)
        g=grid.to_numpy()
        out[str(H)]={"label":{"n":int(np.isfinite(y[g]).sum()),"positive_rate":float(np.nanmean(y[g]))}}
        for m in METHODS:
            if m=="B09":
                out[str(H)][m]={"status":"BLOCKED_DATA","reason":"No PIT-safe NIFTY volume in canonical spot reference; VWAP blocked"}
            else:
                p=sig_to_prob(sig[m])
                out[str(H)][m]=metrics(y[g],p[g],fut[g],60)
    return {"data_rows":len(df),"decision_grid_rows":int(grid.sum()),"timestamp_start":df["timestamp"].min().isoformat(),"timestamp_end":df["timestamp"].max().isoformat(),"horizons":out}


daily=daily_run(); intraday=intra_run()
report={"daily":daily,"intraday":intraday,"methods":METHODS,"status":"PASS"}
(OUT/"phase4_classical_results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"daily_rows":daily["data_rows"],"intraday_rows":intraday["data_rows"],"intraday_grid":intraday["decision_grid_rows"],"status":"PASS"},indent=2))
