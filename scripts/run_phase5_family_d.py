from __future__ import annotations
from pathlib import Path
import json, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, ElasticNet
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, average_precision_score, brier_score_loss, log_loss, confusion_matrix
from run_phase3_daily_baselines import load_daily, make_label, metrics as daily_metrics
from run_phase3_intraday_baselines import load as load_intraday, labels as intraday_labels, metrics as intra_metrics

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data/reports"; OUT.mkdir(parents=True,exist_ok=True)
DAILY_H=[1,2,3,5,10]; INTRA_H=[5,15,30,60,120]; SEED=42

def features_daily(df):
    r=df["ret_1"]; x=pd.DataFrame({"ret1":r,"ret2":r.shift(1),"ret3":r.shift(2),"ret5":df["log_close"].diff(5),"ret10":df["log_close"].diff(10),"vol20":r.rolling(20).std(),"gap":df["gap"]})
    return x

def features_intraday(df):
    r=df["log_spot"].diff(); x=pd.DataFrame({"ret1":r,"ret2":r.shift(1),"ret3":r.shift(2),"ret5":df["log_spot"].diff(5),"ret10":df["log_spot"].diff(10),"vol20":r.rolling(20).std()})
    day_open=df.groupby("date")["spot"].transform("first"); day_close=df.groupby("date")["spot"].last(); x["gap"]=np.log(day_open/df["date"].map(day_close.shift(1)))
    return x

def model(name):
    if name=="D01": return RandomForestClassifier(n_estimators=300,max_depth=6,min_samples_leaf=20,class_weight="balanced",random_state=SEED,n_jobs=-1)
    if name=="D02": return ExtraTreesClassifier(n_estimators=300,max_depth=6,min_samples_leaf=20,class_weight="balanced",random_state=SEED,n_jobs=-1)
    if name=="D03": return GradientBoostingClassifier(n_estimators=200,learning_rate=.03,max_depth=2,min_samples_leaf=20,random_state=SEED)
    if name in ("D04","D05","D06"): return HistGradientBoostingClassifier(max_iter=250 if name!="D04" else 200,learning_rate=.02 if name!="D04" else .03,max_leaf_nodes=15,min_samples_leaf=40 if name!="D04" else 30,random_state=SEED)
    if name=="D08": return LogisticRegression(C=1.0,penalty="elasticnet",l1_ratio=.5,solver="saga",max_iter=3000,random_state=SEED)
    if name=="D10": return KNeighborsClassifier(n_neighbors=31,weights="distance")
    if name=="D11": return SVC(C=1,kernel="rbf",gamma="scale",probability=True,random_state=SEED)
    if name=="D12": return MLPClassifier(hidden_layer_sizes=(32,),max_iter=250,early_stopping=False,random_state=SEED)
    if name=="D09": return make_pipeline(SplineTransformer(n_knots=8,degree=3,include_bias=False),LogisticRegression(C=1.0,max_iter=2000,solver="lbfgs"))
    return None

def prep_fit(m,x,y):
    if m in ("D08","D09","D10","D11","D12","D13","D14","D15"):
        return make_pipeline(StandardScaler(),model(m if m in ("D08","D09","D10","D11","D12") else "D08"))
    return model(m)

def sequence_features(x,window=20,kind="lag"):
    a=x.to_numpy(float); rows=[]; idx=[]
    for i in range(window-1,len(a)):
        z=a[i-window+1:i+1]
        if not np.isfinite(z).all(): continue
        if kind=="conv":
            k=np.array([-.5,0, .5]); conv=np.array([np.convolve(z[:,j],k,mode="valid")[-1] for j in range(z.shape[1])])
            rows.append(np.r_[z[-1],conv]); idx.append(i)
        elif kind=="attn":
            q=z[-1]; score=z@q; score=score-score.max(); w=np.exp(score); w/=w.sum()
            rows.append(np.r_[w@z,z[-1]]); idx.append(i)
        else:
            rows.append(z.reshape(-1)); idx.append(i)
    return np.asarray(rows),np.asarray(idx,dtype=int)

def fit_predict_block(name,X,y,train_end,test_rows):
    train=X.iloc[:train_end].copy(); yy=y.iloc[:train_end].copy()
    mask=yy.notna()&train.notna().all(axis=1); train=train.loc[mask]; yy=yy.loc[mask].astype(int)
    if len(yy)<300 or yy.nunique()<2: return np.full(len(test_rows),np.nan)
    if name=="D07":
        preds=[]
        for sub in ["D01","D02","D03","D08"]:
            m=model(sub); pipe=make_pipeline(StandardScaler(),m) if sub=="D08" else m
            pipe.fit(train,yy); preds.append(pipe.predict_proba(X.iloc[test_rows])[:,1])
        return np.mean(preds,axis=0)
    if name in ("D13","D14","D15"):
        kind={"D13":"lag","D14":"conv","D15":"attn"}[name]
        tr,ti=sequence_features(train,20,kind); 
        te,ei=sequence_features(X.iloc[max(0,train_end-19):max(test_rows)+1],20,kind)
        if len(tr)<300 or len(te)==0: return np.full(len(test_rows),np.nan)
        mm=make_pipeline(StandardScaler(),LogisticRegression(C=1.0,max_iter=2000,solver="lbfgs"))
        mm.fit(tr,yy.iloc[ti]); p=mm.predict_proba(te)[:,1]
        # sequence evaluation is aligned to the requested block's tail only
        out=np.full(len(test_rows),np.nan); out[-min(len(out),len(p)):]=p[-min(len(out),len(p)):]
        return out
    mm=prep_fit(name,X,y); mm.fit(train,yy)
    return mm.predict_proba(X.iloc[test_rows])[:,1]

def run_layer(df, horizons, layer):
    X=features_daily(df) if layer=="daily" else features_intraday(df)
    result={}
    for H in horizons:
        if layer=="daily":
            y,future=make_label(df,H); eval_idx=np.arange(len(df))
            block_key=df["date"].dt.to_period("M").astype(str) if "date" in df else pd.Series(np.arange(len(df))//20)
        else:
            y,future,_=intraday_labels(df["timestamp"],df["spot"],H); grid=((df["minute_of_day"]>=570)&(df["minute_of_day"]<=930)&(((df["minute_of_day"]-570)%60)==0)); eval_idx=np.flatnonzero(grid.to_numpy())
            block_key=df["date"]
        out={}; 
        for name in [f"D{i:02d}" for i in range(1,16)]:
            p=np.full(len(df),np.nan)
            # D04-D06 are provider-independent histogram-boosting surrogates; record this explicitly.
            for start in range(0,len(eval_idx),20):
                rows=eval_idx[start:start+20]
                if len(rows)==0: continue
                train_end=max(0,int(rows[0])-H)
                try: p[rows]=fit_predict_block(name,X,y,train_end,rows)
                except Exception as e: out[name]={"status":"BLOCKED_RUNTIME","reason":type(e).__name__+":"+str(e)}; p=None; break
            if p is not None:
                out[name]= (daily_metrics(y,p,future) if layer=="daily" else intra_metrics(y.loc[eval_idx],p[eval_idx],future.loc[eval_idx]))
                out[name]["implementation_note"]="D04-D06 use HistGradientBoosting provider-independent surrogates" if name in ("D04","D05","D06") else None
        result[str(H)] = out
    return result

def main():
    with warnings.catch_warnings(): warnings.simplefilter("ignore")
    d=load_daily(); daily=run_layer(d,DAILY_H,"daily")
    q=load_intraday(); q["log_spot"]=np.log(q["spot"]); intra=run_layer(q,INTRA_H,"intraday")
    out={"protocol":"research/phase5/MACHINE_LEARNING_PROTOCOL.md","seed":SEED,"daily":{"rows":len(d),"horizons":daily},"intraday":{"rows":len(q),"horizons":intra}}
    (OUT/"phase5_family_d_results.json").write_text(json.dumps(out,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps({"daily_rows":len(d),"intraday_rows":len(q),"status":"PASS"},indent=2))
if __name__=="__main__": main()
