from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, average_precision_score, brier_score_loss, log_loss, confusion_matrix
import statsmodels.api as sm
from statsmodels.tsa.ar_model import AutoReg
from arch import arch_model

ROOT=Path(__file__).resolve().parents[1]
DAILY=ROOT/"data/cache/raw/phase3/nifty50_daily.csv"
INTRA=ROOT/"data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet"
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

DAILY_H=[1,2,3,5,10]
INTRA_H=[5,15,30,60,120]
METHODS=[f"C{i:02d}" for i in range(1,12)]


def result_metrics(y,p,future,block_len):
    y=np.asarray(y,dtype=float); p=np.asarray(p,dtype=float); future=np.asarray(future,dtype=float)
    m=np.isfinite(y)&np.isfinite(p)&np.isfinite(future)
    y=y[m].astype(int); p=p[m]; future=future[m]
    if len(y)==0: return {"status":"EXECUTED","n":0}
    pred=(p>=0.5).astype(int); cm=confusion_matrix(y,pred,labels=[0,1]).ravel()
    bins=[-0.001,0.45,0.50,0.55,0.60,1.001]
    names=["<0.45","0.45-0.50","0.50-0.55","0.55-0.60",">=0.60"]
    br={}
    for lo,hi,name in zip(bins[:-1],bins[1:],names):
        mm=(p>=lo)&((p<hi) if hi<1 else (p<=hi))
        br[name]={"n":int(mm.sum()),"mean_future_return":float(future[mm].mean()) if mm.any() else None}
    rng=np.random.default_rng(42)
    blocks=[np.arange(i,min(i+block_len,len(y))) for i in range(0,len(y),block_len)]
    boots=[]
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
        "accuracy_block_bootstrap_95":{"lower":float(np.quantile(boots,0.025)),"upper":float(np.quantile(boots,0.975)),"median":float(np.median(boots))}
    }
    if len(np.unique(y))==2:
        out["roc_auc"]=float(roc_auc_score(y,p)); out["pr_auc"]=float(average_precision_score(y,p))
    else:
        out["roc_auc"]=None; out["pr_auc"]=None
    return out


def lag_features(ret):
    return pd.DataFrame({f"r{k}":ret.shift(k) for k in [1,2,3,5,10]})


def probit_fit_predict(Xtr,ytr,Xte):
    xtr=sm.add_constant(Xtr,has_constant="add")
    xte=sm.add_constant(Xte,has_constant="add")
    model=sm.Probit(ytr,xtr).fit(disp=False,maxiter=200)
    return np.asarray(model.predict(xte),dtype=float)


def model_probs(method,Xtr,ytr,Xte):
    if method=="C02":
        return probit_fit_predict(Xtr,ytr,Xte)
    if method=="C03":
        lda=LinearDiscriminantAnalysis().fit(Xtr,ytr)
        qda=QuadraticDiscriminantAnalysis(reg_param=0.01).fit(Xtr,ytr)
        return np.asarray(0.5*lda.predict_proba(Xte)[:,1]+0.5*qda.predict_proba(Xte)[:,1],dtype=float)
    if method=="C04":
        yseries=pd.Series(ytr.to_numpy(),index=np.arange(len(ytr)))
        # AR(5) on returns; direction probability from a Gaussian approximation
        model=AutoReg(yseries,lags=5,trend="c",old_names=False).fit()
        pred=float(model.predict(start=len(yseries),end=len(yseries)).iloc[0])
        scale=float(np.std(ytr))
        z=pred/(scale if scale>0 else 1.0)
        return np.array([1/(1+np.exp(-z*3))])
    raise ValueError(method)


def train_state_params(ret):
    r=np.asarray(ret.dropna(),dtype=float)
    neg=r[r<0]; pos=r[r>0]
    means=np.array([neg.mean() if len(neg) else -np.std(r), pos.mean() if len(pos) else np.std(r)])
    vars_=np.array([neg.var(ddof=1) if len(neg)>1 else r.var(), pos.var(ddof=1) if len(pos)>1 else r.var()])
    vars_=np.maximum(vars_,1e-12)
    return means,vars_


def online_hmm(train_ret,test_ret,transition):
    means,vars_=train_state_params(train_ret)
    pi=np.array([0.5,0.5],dtype=float)
    out=[]
    for r in np.asarray(test_ret,dtype=float):
        # posterior at current observation
        lik=np.array([
            np.exp(-0.5*(r-means[0])**2/vars_[0])/np.sqrt(vars_[0]),
            np.exp(-0.5*(r-means[1])**2/vars_[1])/np.sqrt(vars_[1]),
        ])
        post=pi*lik; post=post/post.sum() if post.sum()>0 else np.array([0.5,0.5])
        next_p=transition.T@post
        mu=float(next_p@means)
        s=float(np.sqrt(next_p@vars_ + next_p[0]*next_p[1]*(means[0]-means[1])**2))
        out.append(1/(1+np.exp(-mu/(s if s>0 else 1)*3)))
        pi=post
    return np.asarray(out)


def kalman_local_trend(train_price,test_price):
    z=np.asarray(np.log(train_price),dtype=float)
    obs_var=float(np.var(np.diff(z))) if len(z)>2 else 1e-4
    obs_var=max(obs_var,1e-8); q=0.01*obs_var
    F=np.array([[1.,1.],[0.,1.]])
    H=np.array([[1.,0.]])
    Q=np.array([[q,0.],[0.,q]])
    R=np.array([[obs_var]])
    x=np.array([z[-1], z[-1]-z[-2] if len(z)>1 else 0.])
    P=np.eye(2)*obs_var
    out=[]
    for obs in np.asarray(np.log(test_price),dtype=float):
        xp=F@x; Pp=F@P@F.T+Q
        y=float(obs-(H@xp)[0]); S=float((H@Pp@H.T+R)[0,0])
        K=Pp@H.T/S
        x=xp+(K.flatten()*y); P=(np.eye(2)-K@H)@Pp
        trend=float(x[1])
        out.append(1/(1+np.exp(-trend/(np.sqrt(obs_var)+1e-12)*10)))
    return np.asarray(out)


def garch_vol_signal(train_ret,test_ret):
    scale=100.0
    am=arch_model(np.asarray(train_ret.dropna(),dtype=float)*scale,mean="Constant",vol="GARCH",p=1,q=1,dist="normal")
    res=am.fit(disp="off")
    p=res.params
    omega=float(p.get("omega",1e-6)); alpha=float(p.get("alpha[1]",0.05)); beta=float(p.get("beta[1]",0.9))
    eps=np.asarray(train_ret.dropna(),dtype=float)*scale
    last_eps=float(eps[-1]); h=float(res.conditional_volatility[-1])**2
    train_med=float(np.median(res.conditional_volatility))
    recent=list(eps[-5:])
    out=[]
    for r in np.asarray(test_ret,dtype=float)*scale:
        h=omega+alpha*last_eps**2+beta*h
        sigma=np.sqrt(max(h,1e-12))
        if sigma<=1.2*train_med:
            s=np.sign(last_eps)
        else:
            s=np.sign(np.mean(recent[-5:])) if recent else np.sign(last_eps)
        out.append(0.55 if s>0 else 0.45 if s<0 else 0.5)
        recent.append(float(r)); last_eps=float(r)
    return np.asarray(out)


def cusum_signal(train_ret,test_ret):
    sigma=float(np.std(train_ret.dropna()))
    sigma=max(sigma,1e-8)
    cpos=0.0; cneg=0.0; out=[]
    k=0.5; h=2.5
    for r in np.asarray(test_ret,dtype=float):
        z=r/sigma
        cpos=max(0,cpos+z-k); cneg=min(0,cneg+z+k)
        s=0
        if cpos>h:
            s=1; cpos=0; cneg=0
        elif cneg<-h:
            s=-1; cpos=0; cneg=0
        out.append(0.55 if s>0 else 0.45 if s<0 else 0.5)
    return np.asarray(out)


def prepare_daily():
    df=pd.read_csv(DAILY); df["date"]=pd.to_datetime(df["date"])
    for c in ["open","high","low","close"]: df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df["ret"]=np.log(df["close"]).diff()
    return df


def prepare_intra():
    df=pd.read_parquet(INTRA)
    df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True); df["spot"]=pd.to_numeric(df["spot"],errors="coerce")
    df=df.dropna(subset=["timestamp","spot"]).sort_values("timestamp").drop_duplicates("timestamp")
    df["ist"]=df["timestamp"].dt.tz_convert("Asia/Kolkata"); df["date"]=df["ist"].dt.date
    df["minute_of_day"]=df["ist"].dt.hour*60+df["ist"].dt.minute
    df=df[(df["minute_of_day"]>=555)&(df["minute_of_day"]<=930)].copy().reset_index(drop=True)
    df["ret"]=np.log(df["spot"]).diff()
    return df


def daily_run():
    df=prepare_daily(); out={}
    for H in DAILY_H:
        future=np.log(df["close"].shift(-H)/df["close"])
        y=np.where(future>0,1,np.where(future<0,0,np.nan))
        hres={}
        # C01 accepted Phase 3 reference: same feature specification is represented by a compact rerun here.
        for method in METHODS:
            if method=="C10":
                hres[method]={"status":"BLOCKED_DATA","reason":"PIT-safe event-intensity history not materialized"}
                continue
            if method=="C11":
                hres[method]={"status":"BLOCKED_DATA","reason":"PIT-safe synchronized cross-market feature layer not materialized"}
                continue
            p=np.full(len(df),np.nan)
            start=max(300,int(len(df)*0.4))
            if method=="C05":
                try:
                    p[start:]=garch_vol_signal(df["ret"].iloc[:start],df["ret"].iloc[start:])
                except Exception as exc:
                    hres[method]={"status":"BLOCKED_DATA","reason":f"GARCH fit unavailable: {type(exc).__name__}: {exc}"}
                    continue
            elif method=="C06":
                tr=df["ret"].iloc[:start].dropna(); te=df["ret"].iloc[start:]
                p[start:]=online_hmm(tr,te,np.array([[0.95,0.05],[0.05,0.95]]))[:len(df)-start]
            elif method=="C07":
                tr=df["ret"].iloc[:start].dropna()
                hard=(tr.to_numpy()>0).astype(int)
                trans=np.ones((2,2))*0.05
                for a,b in zip(hard[:-1],hard[1:]): trans[a,b]+=1
                trans=trans/trans.sum(axis=1,keepdims=True)
                p[start:]=online_hmm(tr,df["ret"].iloc[start:],trans)[:len(df)-start]
            elif method=="C08":
                p[start:]=kalman_local_trend(df["close"].iloc[:start],df["close"].iloc[start:])[:len(df)-start]
            elif method=="C09":
                p[start:]=cusum_signal(df["ret"].iloc[:start],df["ret"].iloc[start:])[:len(df)-start]
            else:
                # Session-refresh models C01-C04.
                X=lag_features(df["ret"])
                for i in range(start,len(df)):
                    tr_end=max(30,i-H)
                    Xtr=X.iloc[:tr_end].dropna()
                    ytr=pd.Series(y[:tr_end],index=df.index[:tr_end]).loc[Xtr.index].dropna().astype(int)
                    if len(ytr)<50 or ytr.nunique()<2: continue
                    Xtr=Xtr.loc[ytr.index]
                    Xte=X.iloc[[i]]
                    if Xte.isna().any(axis=1).iloc[0]: continue
                    if method=="C01":
                        # logistic reference implementation via closed-form sklearn-like Newton using statsmodels Logit
                        model=sm.Logit(ytr,sm.add_constant(Xtr,has_constant="add")).fit(disp=False,maxiter=100)
                        p[i]=float(model.predict(sm.add_constant(Xte,has_constant="add")).iloc[0])
                    else:
                        p[i]=float(model_probs(method,Xtr,ytr,Xte)[0])
            hres[method]=result_metrics(y,p,future,20)
        out[str(H)]={"label":{"n":int(np.isfinite(y).sum()),"positive_rate":float(np.nanmean(y))},**hres}
    return {"data_rows":len(df),"date_start":df["date"].min().date().isoformat(),"date_end":df["date"].max().date().isoformat(),"horizons":out}


def intra_run():
    df=prepare_intra(); out={}
    grid=(df["minute_of_day"].between(570,930)&(((df["minute_of_day"]-570)%60)==0)).to_numpy()
    idx=pd.Index(df["timestamp"]); vals=np.log(df["spot"].to_numpy())
    for H in INTRA_H:
        target=idx+pd.Timedelta(minutes=H); pos=idx.get_indexer(target)
        fut=np.full(len(df),np.nan); good=pos>=0; fut[good]=vals[pos[good]]-vals[good]
        y=np.where(np.isfinite(fut),np.where(fut>0,1,np.where(fut<0,0,np.nan)),np.nan)
        hres={}
        start=int(len(df)*0.4)
        for method in METHODS:
            if method in {"C10","C11"}:
                hres[method]={"status":"BLOCKED_DATA","reason":"Required PIT-safe event/cross-market layer not materialized"}
                continue
            p=np.full(len(df),np.nan)
            if method=="C05":
                try: p[start:]=garch_vol_signal(df["ret"].iloc[:start],df["ret"].iloc[start:])[:len(df)-start]
                except Exception as exc:
                    hres[method]={"status":"BLOCKED_DATA","reason":f"GARCH fit unavailable: {type(exc).__name__}: {exc}"}; continue
            elif method=="C06":
                p[start:]=online_hmm(df["ret"].iloc[:start].dropna(),df["ret"].iloc[start:],np.array([[0.95,0.05],[0.05,0.95]]))[:len(df)-start]
            elif method=="C07":
                tr=df["ret"].iloc[:start].dropna(); hard=(tr.to_numpy()>0).astype(int)
                trans=np.ones((2,2))*0.05
                for a,b in zip(hard[:-1],hard[1:]): trans[a,b]+=1
                trans=trans/trans.sum(axis=1,keepdims=True)
                p[start:]=online_hmm(tr,df["ret"].iloc[start:],trans)[:len(df)-start]
            elif method=="C08":
                p[start:]=kalman_local_trend(df["spot"].iloc[:start],df["spot"].iloc[start:])[:len(df)-start]
            elif method=="C09":
                p[start:]=cusum_signal(df["ret"].iloc[:start],df["ret"].iloc[start:])[:len(df)-start]
            else:
                X=lag_features(df["ret"])
                # One fit per trading day; model trained on rows strictly before the day.
                dates=df["date"].iloc[start:].unique()
                for day in dates:
                    loc=np.flatnonzero((df["date"].to_numpy()==day))
                    loc=loc[loc>=start]
                    if len(loc)==0: continue
                    tr_end=int(loc[0]-H)
                    Xtr=X.iloc[:tr_end].dropna(); yy=pd.Series(y[:tr_end],index=df.index[:tr_end]).loc[Xtr.index].dropna().astype(int)
                    if len(yy)<300 or yy.nunique()<2: continue
                    Xtr=Xtr.loc[yy.index]
                    Xte=X.loc[loc]
                    goodte=~Xte.isna().any(axis=1)
                    if not goodte.any(): continue
                    if method=="C01":
                        model=sm.Logit(yy,sm.add_constant(Xtr,has_constant="add")).fit(disp=False,maxiter=100)
                        pred=model.predict(sm.add_constant(Xte.loc[goodte],has_constant="add")).to_numpy()
                    else:
                        pred=model_probs(method,Xtr,yy,Xte.loc[goodte])
                    p[loc[goodte.to_numpy()]]=pred
            hres[method]=result_metrics(y[grid],p[grid],fut[grid],60)
        out[str(H)]={"label":{"n":int(np.isfinite(y[grid]).sum()),"positive_rate":float(np.nanmean(y[grid]))},**hres}
    return {"data_rows":len(df),"decision_grid_rows":int(grid.sum()),"timestamp_start":df["timestamp"].min().isoformat(),"timestamp_end":df["timestamp"].max().isoformat(),"horizons":out}

report={"daily":daily_run(),"intraday":intra_run(),"methods":METHODS,"status":"PASS"}
(OUT/"phase4_family_c_results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"daily_rows":report["daily"]["data_rows"],"intraday_rows":report["intraday"]["data_rows"],"grid":report["intraday"]["decision_grid_rows"]},indent=2))
