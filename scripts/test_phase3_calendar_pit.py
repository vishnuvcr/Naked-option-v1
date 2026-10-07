from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

daily=load("daily",ROOT/"scripts/run_phase3_daily_baselines.py")
intra=load("intra",ROOT/"scripts/run_phase3_intraday_baselines.py")

# Daily H=2: at decision index 4, only labels whose 2-session endpoint
# is strictly before index 4 may be used. Labels at indices 2-3 are unfinished.
dates=pd.date_range("2026-01-01",periods=12,freq="B")
ddf=pd.DataFrame({"date":dates})
y=np.full(len(ddf),np.nan)
y[:3]=1.0
got=daily.pit_weekday_probability_daily(ddf,y,2)
assert abs(float(got.iloc[10])-1.0)<1e-12
assert abs(float(got.iloc[4])-0.5)<1e-12

# Intraday H=5: same strict endpoint rule in timestamp space.
ts=pd.date_range("2026-01-05 09:15",periods=20,freq="min",tz="Asia/Kolkata").tz_convert("UTC")
idf=pd.DataFrame({"timestamp":ts,"ist":ts.tz_convert("Asia/Kolkata")})
iy=np.full(len(idf),np.nan); iy[:5]=1.0
ig=intra.pit_weekday_probability(idf,iy,5)
assert abs(float(ig.iloc[10])-1.0)<1e-12
assert abs(float(ig.iloc[4])-0.5)<1e-12

print("PASS: daily and intraday B8 use only fully completed historical labels.")
