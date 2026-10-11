#!/usr/bin/env python3
"""Row-preserving Greek enrichment for the encrypted NIFTY 1-minute composite."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, math, os, pathlib, re, shutil, sys
from datetime import date, datetime, time, timedelta
import numpy as np
import pandas as pd
from scipy.special import ndtr

MAGIC=b"N1C1"
AAD=b"Naked-option-v1:NIFTY-1m-composite:v1"
KEY_SALT=b"Naked-option-v1-HF-TOKEN-DERIVATION-v1"
YEAR_DAYS=365.0

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def key_from_token(token):
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    if not isinstance(token,str) or len(token.strip())<16: raise ValueError("HF_TOKEN missing/too short")
    return Scrypt(salt=KEY_SALT,length=32,n=2**14,r=8,p=1).derive(token.encode())

def encrypt_part(plain,key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import secrets
    nonce=secrets.token_bytes(12)
    return MAGIC+nonce+AESGCM(key).encrypt(nonce,plain,AAD)

def expiry_from_path(path):
    m=re.search(r"options/NIFTY/(\d{4}-\d{2}-\d{2})\.parquet$",path)
    if not m: return None
    try: return date.fromisoformat(m.group(1))
    except ValueError: return None

def make_expiry_calendar(paths,sessions,last_session):
    source_dates=sorted({d for p in paths if (d:=expiry_from_path(p)) is not None})
    if not source_dates: raise ValueError("No options/NIFTY/YYYY-MM-DD.parquet expiry partitions found")
    last_source=max(source_dates); dates=set(source_dates)
    # Weekly NIFTY expiry is Tuesday under the current rule. A non-trading Tuesday
    # before the latest observed session is mapped to the previous observed session.
    end=last_session+timedelta(days=70); t=last_source+timedelta(days=1)
    while t<=end:
        if t.weekday()==1:
            exp=t
            if t not in sessions and t<=last_session:
                prior=[d for d in sessions if t-timedelta(days=7)<d<t]
                if prior: exp=max(prior)
            if exp>last_source: dates.add(exp)
        t+=timedelta(days=1)
    all_dates=sorted(dates); by_month={}
    for d in all_dates: by_month.setdefault((d.year,d.month),[]).append(d)
    monthly={max(ds) for ds in by_month.values()}
    source={d.isoformat():("HF_EXPIRY_PARTITION_FILELIST_PROXY" if d<=last_source else "NSE_TUESDAY_RULE_PROXY_NOT_CONTRACT_MASTER_VERIFIED") for d in all_dates}
    return all_dates,monthly,source,last_source

def num(df,name):
    if name not in df.columns: return np.full(len(df),np.nan,dtype=float)
    return pd.to_numeric(df[name],errors="coerce").to_numpy(dtype=float,na_value=np.nan)

def epoch_seconds(s):
    x=pd.to_numeric(s,errors="coerce").to_numpy(dtype=float,na_value=np.nan)
    good=np.isfinite(x)
    if np.any(good) and np.nanmedian(x[good])>1e12: x[good]=np.floor(x[good]/1000.0)
    return x

def date_values(s):
    vals=[]
    for x in s.astype(str).tolist():
        try: vals.append(date.fromisoformat(x[:10]))
        except Exception: vals.append(None)
    return vals

def merge_spot(df,spot_source):
    spot=spot_source.copy() if isinstance(spot_source,pd.DataFrame) else pd.read_parquet(spot_source)
    if "timestamp" not in spot.columns: raise ValueError("HF spot parquet lacks timestamp")
    ts=pd.to_datetime(spot["timestamp"],errors="coerce",utc=True)
    spot["_epoch_sec"]=(ts.astype("int64")//1_000_000_000).where(ts.notna(),np.nan)
    rename={}
    for target,candidates in {"nifty_open":["open","Open"],"nifty_high":["high","High"],"nifty_low":["low","Low"],"nifty_close":["close","Close"],"nifty_volume":["volume","Volume"]}.items():
        for c in candidates:
            if c in spot.columns: rename[c]=target; break
    spot=spot.rename(columns=rename)
    cols=["_epoch_sec"]+[c for c in ("nifty_open","nifty_high","nifty_low","nifty_close","nifty_volume") if c in spot.columns]
    spot=spot[cols].dropna(subset=["_epoch_sec"]).drop_duplicates("_epoch_sec",keep="last")
    spot["_epoch_sec"]=spot["_epoch_sec"].astype("int64")
    spot=spot.set_index("_epoch_sec")
    epoch=epoch_seconds(df["timestamp_epoch"]) if "timestamp_epoch" in df.columns else np.full(len(df),np.nan)
    key=pd.Series(epoch).round().astype("Int64")
    lookup=key.to_numpy(dtype="int64",na_value=-1)
    joined=spot.reindex(lookup)
    if "spot_valuation_source" not in df.columns: df["spot_valuation_source"]=""
    fill_rows=np.zeros(len(df),dtype=bool); fills=0
    for c in ("nifty_open","nifty_high","nifty_low","nifty_close","nifty_volume"):
        src=joined[c].to_numpy(dtype=float,na_value=np.nan) if c in joined.columns else np.full(len(df),np.nan)
        if c not in df.columns: df[c]=np.nan
        old=pd.to_numeric(df[c],errors="coerce").to_numpy(dtype=float,na_value=np.nan)
        # Fill absent values only; never overwrite a valid original source value.
        need=(~np.isfinite(old))&np.isfinite(src)
        fills+=int(need.sum()); fill_rows|=need; old[need]=src[need]; df[c]=old
    df.loc[fill_rows,"spot_valuation_source"]="HF_NIFTY_INDEX_EXACT_TIMESTAMP"
    close=num(df,"nifty_close")
    df.loc[np.isfinite(close)&(df["spot_valuation_source"].astype(str)==""),"spot_valuation_source"]="EXISTING_COMPOSITE_SPOT"
    df.loc[~np.isfinite(close),"spot_valuation_source"]="MISSING_NO_EXACT_SPOT"
    hits=int(pd.Index(lookup).isin(spot.index).sum())
    if "spot_join_status" in df.columns:
        df.loc[fill_rows,"spot_join_status"]="HF_EXACT_TIMESTAMP_PATCH"
    return df,{"spot_exact_timestamp_matches":hits,"spot_field_values_filled":fills}

def bs_price(S,K,T,sigma,is_call):
    sqrt_t=np.sqrt(T); d1=(np.log(S/K)+0.5*sigma*sigma*T)/(sigma*sqrt_t); d2=d1-sigma*sqrt_t
    call=S*ndtr(d1)-K*ndtr(d2); put=K*ndtr(-d2)-S*ndtr(-d1)
    return np.where(is_call,call,put)

def solve_iv(S,K,T,P,is_call):
    valid=np.isfinite(S)&np.isfinite(K)&np.isfinite(T)&np.isfinite(P)&(S>0)&(K>0)&(T>0)&(P>0)
    lower=np.where(is_call,np.maximum(S-K,0),np.maximum(K-S,0)); upper=np.where(is_call,S,K)
    valid &= (P>=lower-1e-7)&(P<=upper+1e-7)&(P>lower+1e-10)&(P<upper-1e-10)
    iv=np.full(len(S),np.nan); status=np.full(len(S),"IV_INPUT_INVALID",dtype=object)
    status[valid]="IV_INVERSION_FAILED"
    if not np.any(valid): return iv,status
    idx=np.flatnonzero(valid); s=S[idx]; k=K[idx]; t=T[idx]; p=P[idx]; c=is_call[idx]
    lo=np.full(len(idx),1e-4); hi=np.full(len(idx),5.0)
    min_p=bs_price(s,k,t,lo,c); max_p=bs_price(s,k,t,hi,c)
    possible=(p>=min_p-1e-7)&(p<=max_p+1e-7)
    for _ in range(48):
        mid=(lo+hi)/2; pm=bs_price(s,k,t,mid,c)
        below=pm<p; lo=np.where(below,mid,lo); hi=np.where(below,hi,mid)
    guess=(lo+hi)/2
    iv[idx[possible]]=guess[possible]; status[idx[possible]]="IV_INVERTED_FROM_OPTION_CLOSE"
    status[idx[~possible]]="IV_OUTSIDE_SOLVER_RANGE_OR_PRICE_INCONSISTENT"
    return iv,status

def greeks(S,K,T,sigma,is_call):
    out={n:np.full(len(S),np.nan) for n in ("delta","gamma","theta_per_day","vega_per_1pct_iv","rho_per_1pct_rate")}
    ok=np.isfinite(S)&np.isfinite(K)&np.isfinite(T)&np.isfinite(sigma)&(S>0)&(K>0)&(T>0)&(sigma>0)&(sigma<=5)
    if not ok.any(): return out
    s=S[ok]; k=K[ok]; t=T[ok]; v=sigma[ok]; c=is_call[ok]; root=np.sqrt(t)
    d1=(np.log(s/k)+0.5*v*v*t)/(v*root); d2=d1-v*root
    pdf=np.exp(-.5*d1*d1)/math.sqrt(2*math.pi)
    out["delta"][ok]=np.where(c,ndtr(d1),ndtr(d1)-1)
    out["gamma"][ok]=pdf/(s*v*root)
    out["theta_per_day"][ok]=(-(s*pdf*v)/(2*root))/YEAR_DAYS
    out["vega_per_1pct_iv"][ok]=s*pdf*root*.01
    out["rho_per_1pct_rate"][ok]=np.where(c,k*t*ndtr(d2),-k*t*ndtr(-d2))*.01
    return out

def enrich_frame(df,all_expiries,monthly,expiry_sources,spot_source,sessions):
    df,spot_report=merge_spot(df,spot_source); n=len(df)
    fields=("expiry_date","expiry_mapping_source","time_to_expiry_years","risk_free_rate_decimal","risk_free_rate_source","dividend_yield_decimal","dividend_yield_source","greek_assumption","greek_implied_volatility","greek_iv_source","delta","gamma","theta_per_day","vega_per_1pct_iv","rho_per_1pct_rate","greek_model","greek_status")
    for c in fields:
        if c not in df.columns: df[c]=np.nan if c in {"time_to_expiry_years","risk_free_rate_decimal","dividend_yield_decimal","greek_implied_volatility","delta","gamma","theta_per_day","vega_per_1pct_iv","rho_per_1pct_rate"} else ""
    if "data_quality_flags" not in df.columns: df["data_quality_flags"]=""
    df["data_quality_flags"]=df["data_quality_flags"].fillna("").astype(str)
    is_opt=df.get("row_type",pd.Series(["OPTION"]*n)).astype(str).str.upper().eq("OPTION").to_numpy()
    dates=date_values(df["session_date"]) if "session_date" in df else [None]*n
    flags=df.get("expiry_flag",pd.Series([""]*n)).fillna("").astype(str).str.upper().to_numpy()
    codes=pd.to_numeric(df.get("expiry_code",pd.Series([np.nan]*n)),errors="coerce").to_numpy(dtype=float,na_value=np.nan)
    exp=[None]*n; src=[""]*n
    for i in np.flatnonzero(is_opt):
        sd=dates[i]
        if sd is None: src[i]="SESSION_DATE_MISSING"; continue
        if "MONTH" in flags[i]: cal=sorted(monthly)
        elif "WEEK" in flags[i]: cal=all_expiries
        else: src[i]="EXPIRY_FLAG_UNKNOWN"; continue
        if not np.isfinite(codes[i]) or not float(codes[i]).is_integer() or int(codes[i]) not in (0,1,2):
            src[i]="EXPIRY_CODE_INVALID"; continue
        future=[d for d in cal if d>=sd]; ci=int(codes[i])
        if len(future)<=ci: src[i]="EXPIRY_CALENDAR_EXHAUSTED"; continue
        exp[i]=future[ci]; src[i]=expiry_sources.get(exp[i].isoformat(),"EXPIRY_CALENDAR_PROXY")
    df["expiry_date"]=[x.isoformat() if x else "" for x in exp]; df["expiry_mapping_source"]=src
    tcol="timestamp_ist" if "timestamp_ist" in df.columns else "timestamp_utc"
    tt=pd.to_datetime(df[tcol],errors="coerce")
    if getattr(tt.dt,"tz",None) is None: tt=tt.dt.tz_localize("Asia/Kolkata",ambiguous="NaT",nonexistent="NaT")
    else: tt=tt.dt.tz_convert("Asia/Kolkata")
    tsec=tt.astype("int64").to_numpy(dtype=np.int64)/1e9
    T=np.full(n,np.nan)
    for i,d in enumerate(exp):
        if d is None: continue
        close_time=pd.Timestamp(datetime.combine(d,time(15,30)),tz="Asia/Kolkata").timestamp()
        remaining=(close_time-tsec[i])/(YEAR_DAYS*86400)
        if np.isfinite(remaining) and remaining>0: T[i]=remaining
    df["time_to_expiry_years"]=T; df["risk_free_rate_decimal"]=0.0; df["risk_free_rate_source"]="EXPLICIT_ZERO_RATE_PROXY_NOT_HISTORICAL_RATE"
    df["dividend_yield_decimal"]=0.0; df["dividend_yield_source"]="EXPLICIT_ZERO_DIVIDEND_PROXY_NOT_HISTORICAL_YIELD"
    df["greek_assumption"]="European Black-Scholes; source timestamp/strike/spot and expiry proxy; r=0,q=0; estimated, not historical vendor Greeks"
    S=num(df,"nifty_close"); roll=num(df,"rolling_spot"); use_roll=(~np.isfinite(S)|(S<=0))&np.isfinite(roll)&(roll>0); S=np.where(np.isfinite(S)&(S>0),S,roll)
    df.loc[use_roll,"spot_valuation_source"]="EXISTING_COMPOSITE_ROLLING_SPOT_FALLBACK"
    K=num(df,"returned_strike"); P=num(df,"option_close")
    opt=df.get("option_type",pd.Series([""]*n)).fillna("").astype(str).str.upper().to_numpy()
    call=np.isin(opt,["CE","CALL","C"]); put=np.isin(opt,["PE","PUT","P"]); known=call|put
    iv,ivstat=solve_iv(S,K,T,P,call); raw=num(df,"implied_volatility")
    rawnorm=np.where(raw>3,raw/100.0,raw)
    fallback=(~np.isfinite(iv))&np.isfinite(rawnorm)&(rawnorm>0)&(rawnorm<=5)&known&np.isfinite(S)&(S>0)&np.isfinite(K)&(K>0)&np.isfinite(T)&(T>0)
    iv[fallback]=rawnorm[fallback]; ivstat[fallback]="SOURCE_IV_HEURISTIC_FALLBACK_GT3_AS_PERCENT_POINTS"
    iv[~known]=np.nan; ivstat[~known]="OPTION_TYPE_UNKNOWN"
    gs=greeks(S,K,T,iv,call)
    df["greek_implied_volatility"]=iv; df["greek_iv_source"]=ivstat
    for k,v in gs.items(): df[k]=v
    df["greek_model"]="BLACK_SCHOLES_EUROPEAN_ZERO_RATE_ZERO_DIVIDEND_PROXY"
    status=np.full(n,"NOT_OPTION_ROW",dtype=object)
    weekend=np.array([d is None or d not in sessions for d in dates])&is_opt
    # Leave the Greek fields null for rows whose timestamp date is not in observed NIFTY sessions.
    for col in ("greek_implied_volatility","delta","gamma","theta_per_day","vega_per_1pct_iv","rho_per_1pct_rate"):
        a=pd.to_numeric(df[col],errors="coerce").to_numpy(dtype=float,na_value=np.nan); a[weekend]=np.nan; df[col]=a
    for i in np.flatnonzero(is_opt):
        if weekend[i]: status[i]="SESSION_NOT_IN_OBSERVED_TRADING_CALENDAR"
        elif not known[i]: status[i]="OPTION_TYPE_UNKNOWN"
        elif exp[i] is None: status[i]="EXPIRY_UNMAPPED:"+str(src[i])
        elif not np.isfinite(S[i]) or S[i]<=0: status[i]="SPOT_MISSING_OR_INVALID"
        elif not np.isfinite(K[i]) or K[i]<=0: status[i]="STRIKE_MISSING_OR_INVALID"
        elif not np.isfinite(T[i]) or T[i]<=0: status[i]="EXPIRED_OR_ZERO_TIME_TO_EXPIRY"
        elif not np.isfinite(iv[i]): status[i]=str(ivstat[i])
        else: status[i]="GREEKS_ESTIMATED_FROM_INVERTED_IV" if ivstat[i]=="IV_INVERTED_FROM_OPTION_CLOSE" else "GREEKS_ESTIMATED_FROM_SOURCE_IV_FALLBACK"
    df["greek_status"]=status
    missspot=is_opt&(~np.isfinite(S)|(S<=0)); missexp=is_opt&np.array([x is None for x in exp])
    df.loc[weekend,"data_quality_flags"]=df.loc[weekend,"data_quality_flags"].astype(str).str.rstrip("|")+"|SESSION_NOT_IN_OBSERVED_TRADING_CALENDAR"
    df.loc[missspot,"data_quality_flags"]=df.loc[missspot,"data_quality_flags"].astype(str).str.rstrip("|")+"|GREEK_SPOT_MISSING"
    df.loc[missexp,"data_quality_flags"]=df.loc[missexp,"data_quality_flags"].astype(str).str.rstrip("|")+"|GREEK_EXPIRY_UNMAPPED"
    ost=df.loc[is_opt,"greek_status"].value_counts(dropna=False).to_dict()
    ec=df.loc[is_opt,"expiry_mapping_source"].value_counts(dropna=False).to_dict()
    ivc=df.loc[is_opt,"greek_iv_source"].value_counts(dropna=False).to_dict()
    report={"input_rows":int(n),"option_rows":int(is_opt.sum()),"spot_rows":int((~is_opt).sum()),"greek_status_counts":{str(k):int(v) for k,v in ost.items()},"expiry_mapping_source_counts":{str(k):int(v) for k,v in ec.items()},"iv_source_counts":{str(k):int(v) for k,v in ivc.items()},"greek_rows_with_delta":int(np.isfinite(df.loc[is_opt,"delta"].to_numpy(dtype=float,na_value=np.nan)).sum()),"option_rows_missing_spot":int(missspot.sum()),"option_rows_unmapped_expiry":int(missexp.sum()),"spot_merge":spot_report}
    return df,report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=pathlib.Path,required=True)
    p.add_argument("--output-dir",type=pathlib.Path,required=True)
    p.add_argument("--coverage-report",type=pathlib.Path,required=True)
    p.add_argument("--expiry-file-list",type=pathlib.Path,required=True)
    p.add_argument("--hf-spot-parquet",type=pathlib.Path,required=True)
    a=p.parse_args(); token=os.environ.get("HF_TOKEN","")
    if not token: raise ValueError("HF_TOKEN environment variable required; do not pass it in command line")
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key=key_from_token(token)
    mp=a.input_dir/"dataset_manifest.json"
    if not mp.is_file(): raise FileNotFoundError("encrypted source dataset manifest missing")
    manifest=json.loads(mp.read_text(encoding="utf-8"))
    if manifest.get("download_bundle_contains_encrypted_data_only") is not True: raise ValueError("source bundle encryption marker missing")
    if len(manifest.get("parts",[]))!=61: raise ValueError("expected 61 encrypted source parts; source manifest differs")
    for part in manifest["parts"]:
        path=a.input_dir/part["file"]
        if not path.is_file() or sha256(path)!=part["encrypted_sha256"]: raise ValueError("source encrypted part hash mismatch: "+part["file"])
    spot=pd.read_parquet(a.hf_spot_parquet)
    if "timestamp" not in spot.columns: raise ValueError("HF NIFTY spot parquet lacks timestamp")
    st=pd.to_datetime(spot["timestamp"],errors="coerce",utc=True)
    sessions=set(st.dropna().dt.tz_convert("Asia/Kolkata").dt.date.tolist())
    paths=[x.strip() for x in a.expiry_file_list.read_text().splitlines() if x.strip()]
    dates,monthly,sources,last_source=make_expiry_calendar(paths,sessions,max(sessions))
    a.output_dir.mkdir(parents=True,exist_ok=True); total=0
    coverage={"schema_version":1,"status":"COMPLETE_WITH_COVERAGE_RESTRICTIONS","source_dataset_id":manifest.get("dataset_id"),"source_status":manifest.get("status"),"source_option_rows":int(manifest.get("source_row_count_options",0)),"source_spot_rows":int(manifest.get("source_row_count_spot",0)),"source_total_rows":int(manifest.get("rows_preserved",0)),"source_artifact_id":11698879857,"source_run_id":38131641336,"source_artifact_sha256":"40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b","calculated_at_utc":datetime.utcnow().isoformat()+"Z","source_attribution":"https://huggingface.co/datasets/thetrademarkk/india-index-options-1m","source_license":"CC-BY-NC-4.0: non-commercial research only","expiry_partition_count":sum(1 for x in paths if expiry_from_path(x)),"latest_hf_expiry_date":last_source.isoformat(),"expiry_mapping_method":"HF expiry-partition file-list proxy through latest listed date; weekly Tuesday-rule proxy after that; not an official point-in-time contract master","greek_method":"European Black-Scholes Greeks; solve IV from minute option close when arbitrage-bounded and numerically solvable; fallback to source IV with documented heuristic; zero-rate/zero-dividend proxy; not historical vendor Greeks","data_limitations":["The underlying Dhan request grid is PARTIAL_GRID and does not cover every exchange-listed strike/contract.","The HF dataset itself documents partial option coverage for sparse/illiquid/far strikes.","Expiry mapping for relative expiry codes is inferred from a public expiry partition list, not reconciled against point-in-time official Dhan contract-master snapshots.","Historical risk-free rates and dividend yields are unavailable; r=q=0 proxies are explicit.","Rows with missing/invalid spot, expiry, IV, option type or session keep Greek values missing and are reported."],"parts":[],"row_count_by_month":{},"rows_preserved":0,"greek_rows_with_delta":0,"option_rows_missing_spot":0,"option_rows_unmapped_expiry":0,"spot_field_values_filled":0,"greek_status_counts":{},"expiry_mapping_source_counts":{},"iv_source_counts":{}}
    (a.output_dir/".plain").mkdir(exist_ok=True)
    try:
        by_name={p["file"]:p for p in manifest["parts"]}
        for enc in sorted(a.input_dir.glob("nifty_1m_composite_*.csv.gz.enc")):
            part=by_name.get(enc.name)
            if not part: raise ValueError("unexpected encrypted source part "+enc.name)
            raw=enc.read_bytes()
            if not raw.startswith(MAGIC): raise ValueError("invalid source encryption header "+enc.name)
            plain=AESGCM(key).decrypt(raw[4:16],raw[16:],AAD)
            if hashlib.sha256(plain).hexdigest()!=part["plain_gzip_sha256"]: raise ValueError("authenticated source plaintext checksum mismatch "+enc.name)
            name=enc.name.removesuffix(".enc"); plain_path=a.output_dir/".plain"/name
            plain_path.write_bytes(plain)
        source_plain=sorted((a.output_dir/".plain").glob("nifty_1m_composite_*.csv.gz"))
        if len(source_plain)!=61: raise ValueError("expected 61 monthly CSV.GZ parts after decrypt")
        for pth in source_plain:
            df=pd.read_csv(pth,compression="gzip",low_memory=False)
            out,rep=enrich_frame(df,dates,monthly,sources,spot,sessions)
            gz=a.output_dir/pth.name
            out.to_csv(gz,index=False,compression={"method":"gzip","compresslevel":6,"mtime":0})
            plain=gz.read_bytes(); enc=encrypt_part(plain,key); encname=pth.name+".enc"
            ep=a.output_dir/encname; ep.write_bytes(enc); gz.unlink()
            coverage["parts"].append({"file":encname,"encrypted_bytes":len(enc),"encrypted_sha256":hashlib.sha256(enc).hexdigest(),"plain_gzip_sha256":hashlib.sha256(plain).hexdigest(),"row_count":int(len(out)),"encryption":"AES-256-GCM per-file nonce; key derived via scrypt from HF_TOKEN"})
            total+=len(out); coverage["rows_preserved"]+=len(out); coverage["row_count_by_month"][pth.name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz")]=len(out)
            for k in ("greek_rows_with_delta","option_rows_missing_spot","option_rows_unmapped_expiry","spot_field_values_filled"):
                coverage[k]+=int(rep.get(k,0) if k=="spot_field_values_filled" else rep.get(k,0) if k in ("option_rows_missing_spot","option_rows_unmapped_expiry") else rep.get(k,0))
            for grp in ("greek_status_counts","expiry_mapping_source_counts","iv_source_counts"):
                for k,v in rep.get(grp,{}).items(): coverage[grp][k]=coverage[grp].get(k,0)+int(v)
        shutil.rmtree(a.output_dir/".plain",ignore_errors=True)
        if total!=int(manifest.get("rows_preserved",0)): raise ValueError(f"row count changed: source={manifest.get('rows_preserved')} output={total}")
        outman={"schema_version":1,"dataset_id":"NIFTY_1M_DHAN_HF_SPOT_GREEKS_ENRICHED_R1","created_at_utc":coverage["calculated_at_utc"],"download_bundle_contains_encrypted_data_only":True,"do_not_upload_plaintext_or_publish_in_public_repository":True,"encryption":"AES-256-GCM; key derivation requires same HF_TOKEN used for original cache","columns":list(out.columns),"parts":coverage["parts"],"rows_preserved":coverage["rows_preserved"],"row_count_by_month":coverage["row_count_by_month"],"greek_status_counts":coverage["greek_status_counts"],"expiry_mapping_source_counts":coverage["expiry_mapping_source_counts"],"iv_source_counts":coverage["iv_source_counts"],"greek_model":"BLACK_SCHOLES_EUROPEAN_ZERO_RATE_ZERO_DIVIDEND_PROXY","expiry_mapping_method":coverage["expiry_mapping_method"],"greek_method":coverage["greek_method"],"source_attribution":coverage["source_attribution"],"source_license":coverage["source_license"],"limitations":coverage["data_limitations"],"source_artifact_id":11698879857,"source_run_id":38131641336}
        (a.output_dir/"dataset_manifest.json").write_text(json.dumps(outman,indent=2,sort_keys=True))
        a.coverage_report.parent.mkdir(parents=True,exist_ok=True); a.coverage_report.write_text(json.dumps(coverage,indent=2,sort_keys=True))
        print(json.dumps({"status":coverage["status"],"rows_preserved":coverage["rows_preserved"],"greek_rows_with_delta":coverage["greek_rows_with_delta"],"option_rows_missing_spot":coverage["option_rows_missing_spot"],"option_rows_unmapped_expiry":coverage["option_rows_unmapped_expiry"],"parts":len(coverage["parts"])},sort_keys=True))
    except Exception:
        shutil.rmtree(a.output_dir/".plain",ignore_errors=True)
        raise

if __name__=="__main__":
    try: main()
    except Exception as e:
        print("GREEK_ENRICHMENT_ERROR "+type(e).__name__+": "+str(e),file=sys.stderr); sys.exit(1)
