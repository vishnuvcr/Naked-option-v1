from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("phase3_intraday",ROOT/"scripts/run_phase3_intraday_baselines.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

# Synthetic 1-minute observations across one weekday. At decision t, a label
# is eligible only when its H-minute future endpoint is strictly before t.
ts=pd.date_range("2026-01-05 09:15", periods=20, freq="min", tz="Asia/Kolkata").tz_convert("UTC")
df=pd.DataFrame({
    "timestamp":ts,
    "ist":ts.tz_convert("Asia/Kolkata"),
    "date":ts.tz_convert("Asia/Kolkata").date,
})
df["ist_dow"]=df["ist"].dt.dayofweek
y=np.full(len(df),np.nan)

# Mark t=0..4 as completed positive labels, but t=5's label is not completed
# at decision t=10 for H=5 because its endpoint is exactly decision+?; this
# asserts strict endpoint ordering rather than row-shift semantics.
y[:5]=1.0

got=MOD.pit_weekday_probability(df,y,5)

# At index 10, labels 0..4 all end before the decision, so probability=1.
assert abs(float(got.iloc[10])-1.0)<1e-12

# At index 4, only labels with end < timestamp[4] are eligible. With H=5,
# none of labels 0..4 is complete yet, so the result stays at neutral 0.5.
assert abs(float(got.iloc[4])-0.5)<1e-12

print("PASS: intraday B8 uses only fully completed historical labels.")
