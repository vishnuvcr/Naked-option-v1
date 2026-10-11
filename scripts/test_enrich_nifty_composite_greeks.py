#!/usr/bin/env python3
"""Synthetic-only tests: no token, live source calls, or real market data."""
import importlib.util, math, tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd

spec=importlib.util.spec_from_file_location("greek_module",Path(__file__).with_name("enrich_nifty_composite_greeks.py"))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def bs(s,k,t,v,call):
    d1=(math.log(s/k)+.5*v*v*t)/(v*math.sqrt(t)); d2=d1-v*math.sqrt(t)
    N=lambda z:.5*(1+math.erf(z/math.sqrt(2)))
    return s*N(d1)-k*N(d2) if call else k*N(-d2)-s*N(-d1)

def main():
    s=np.array([25000.,25000.]); k=s.copy(); t=np.array([20/365,20/365]); expected=np.array([.22,.22]); call=np.array([True,False])
    p=np.array([bs(s[i],k[i],t[i],expected[i],call[i]) for i in range(2)])
    iv,st=m.solve_iv(s,k,t,p,call)
    assert np.allclose(iv,expected,atol=1e-7),(iv,st)
    g=m.greeks(s,k,t,iv,call)
    assert g["delta"][0]>0 and g["delta"][1]<0
    assert np.all(g["gamma"]>0) and np.all(g["vega_per_1pct_iv"]>0)
    assert g["rho_per_1pct_rate"][0]>0 and g["rho_per_1pct_rate"][1]<0
    eps=.1
    dfd=(bs(s[0]+eps,k[0],t[0],iv[0],True)-bs(s[0]-eps,k[0],t[0],iv[0],True))/(2*eps)
    assert abs(dfd-g["delta"][0])<1e-5
    gfd=(bs(s[0]+eps,k[0],t[0],iv[0],True)-2*bs(s[0],k[0],t[0],iv[0],True)+bs(s[0]-eps,k[0],t[0],iv[0],True))/(eps**2)
    assert abs(gfd-g["gamma"][0])<1e-5
    bad,badst=m.solve_iv(np.array([100.]),np.array([100.]),np.array([.1]),np.array([101.]),np.array([True]))
    assert np.isnan(bad[0]) and badst[0]=="IV_INPUT_INVALID"
    sessions={date(2026,7,28),date(2026,8,4),date(2026,8,11),date(2026,8,18),date(2026,8,25),date(2026,9,1)}
    allx,monthly,sources,last=m.make_expiry_calendar(["options/NIFTY/2026-07-28.parquet","options/NIFTY/2026-08-04.parquet"],sessions,date(2026,8,4))
    assert date(2026,7,28) in monthly and date(2026,8,25) in monthly
    assert sources["2026-07-28"]=="HF_EXPIRY_PARTITION_FILELIST_PROXY"
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); spotpath=td/"spot.parquet"; spotpath.write_text("synthetic placeholder")
        ts=pd.Timestamp("2026-07-28 09:15:00",tz="Asia/Kolkata")
        spot=pd.DataFrame({"timestamp":[ts],"open":[25000.],"high":[25001.],"low":[24999.],"close":[25000.],"volume":[1]})
        bar_close=ts+pd.Timedelta(seconds=60)
        tte=(pd.Timestamp("2026-07-28 15:30:00",tz="Asia/Kolkata")-bar_close).total_seconds()/(365*86400)
        cp=bs(25000,25000,tte,.22,True); pp=bs(25000,25000,tte,.22,False)
        rows=[]
        for typ,price in (("CE",cp),("PE",pp)):
            rows.append({"timestamp_epoch":int(ts.timestamp()),"timestamp_ist":ts.isoformat(),"session_date":"2026-07-28","row_type":"OPTION","expiry_flag":"WEEK","expiry_code":0,"option_type":typ,"returned_strike":25000,"option_close":price,"implied_volatility":np.nan,"nifty_close":25000,"spot_join_status":"MATCHED","data_quality_flags":""})
        rows.append({"timestamp_epoch":int(ts.timestamp()),"timestamp_ist":ts.isoformat(),"session_date":"2026-07-28","row_type":"SPOT","expiry_flag":"","expiry_code":np.nan,"option_type":"","returned_strike":np.nan,"option_close":np.nan,"implied_volatility":np.nan,"nifty_close":25000,"spot_join_status":"SPOT","data_quality_flags":""})
        with patch.object(m.pd,"read_parquet",return_value=spot):
            out,report=m.enrich_frame(pd.DataFrame(rows),allx,monthly,sources,spotpath,sessions)
        assert len(out)==3 and report["greek_rows_with_delta"]==2,report
        assert out.loc[0,"greek_status"]=="GREEKS_ESTIMATED_FROM_INVERTED_IV",out.loc[0,"greek_status"]
        assert out.loc[0,"delta"]>0 and out.loc[1,"delta"]<0
        assert abs(float(out.loc[0,"time_to_expiry_years"])-tte)<1e-12
        assert out.loc[0,"greek_valuation_offset_seconds"]==60
        assert out.loc[2,"greek_status"]=="NOT_OPTION_ROW"
    print("PASS: IV inversion, Greek signs, finite-difference delta/gamma, invalid premium, expiry calendar, row-preserving synthetic enrichment")
if __name__=="__main__": main()
