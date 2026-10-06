from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import datetime
import io
import json
import math
import zipfile

import pyarrow
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "data" / "cache" / "raw" / "nse_fno_samples" / "2024-07-08_udiff.zip"
HF_MANIFEST = ROOT / "data" / "reports" / "hf_reference_acquisition.json"
OUT = ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

MIN_KEY_COVERAGE = 0.95
MIN_CLOSE_TOLERANCE = 0.99
MAX_SPOT_ERROR = 1.0

for p in (OFFICIAL, HF_MANIFEST):
    if not p.exists():
        raise SystemExit(f"ERROR: required input missing: {p}")

hf_meta = json.loads(HF_MANIFEST.read_text(encoding="utf-8"))
hf_path = ROOT / hf_meta["local_path"]
if not hf_path.exists():
    raise SystemExit("ERROR: HF reference file missing")

target_trade_date = datetime.date.fromisoformat(hf_meta["target_date"])
target_expiry = datetime.date.fromisoformat(hf_meta["file_date"])

def pick(cols, candidates):
    lower = {c.lower(): c for c in cols}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    normalized = {x.lower().replace("_", "") for x in candidates}
    for c in cols:
        if c.lower().replace("_", "") in normalized:
            return c
    return None

def parse_date(v):
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    s = str(v).strip().replace("Z", "")
    if "T" in s:
        s = s.split("T", 1)[0]
    if " " in s:
        s = s.split(" ", 1)[0]
    return datetime.date.fromisoformat(s)

def finite_float(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

table = pq.read_table(hf_path)
cols = list(table.column_names)
mapping = {
    "timestamp": pick(cols, ["datetime", "timestamp", "date_time", "time"]),
    "trade_date": pick(cols, ["date"]),
    "expiry": pick(cols, ["expiry", "expiry_date", "expiryDate"]),
    "strike": pick(cols, ["strike", "strike_price", "strikePrice"]),
    "option_type": pick(cols, ["option_type", "optionType", "type", "opt_type"]),
    "close": pick(cols, ["close", "cls_price", "close_price"]),
    "open": pick(cols, ["open", "opn_price", "open_price"]),
    "high": pick(cols, ["high", "high_price"]),
    "low": pick(cols, ["low", "low_price"]),
    "volume": pick(cols, ["volume", "traded_volume"]),
    "oi": pick(cols, ["oi", "open_interest"]),
    "spot": pick(cols, ["spot", "underlying", "underlying_value", "underlying_price"]),
}
required = ["timestamp", "expiry", "strike", "option_type", "close"]
missing = [k for k in required if mapping[k] is None]
if missing:
    raise SystemExit(f"ERROR: HF schema cannot be mapped for critical fields: {missing}")

ts_col = table[mapping["timestamp"]]
if not pyarrow.types.is_timestamp(ts_col.type):
    raise SystemExit("ERROR: HF reference does not expose a timestamp-resolution field")

# Filter to the target trading date.
trade_date_col = table[mapping["trade_date"]] if mapping["trade_date"] else ts_col
if pyarrow.types.is_timestamp(trade_date_col.type):
    trade_dates = pc.cast(trade_date_col, pyarrow.date32())
else:
    trade_dates = pc.cast(trade_date_col, pyarrow.date32())
trade_mask = pc.equal(trade_dates, pyarrow.scalar(target_trade_date, type=pyarrow.date32()))
hf_day = table.filter(trade_mask)

# Keep only the weekly expiry represented by the selected HF file, then take the
# final observed bar for every contract to make an EOD-compatible comparison.
latest = {}
latest_ties = Counter()
for i in range(hf_day.num_rows):
    def get(k):
        return hf_day[mapping[k]][i].as_py() if mapping[k] else None

    try:
        exp = parse_date(get("expiry"))
        if exp != target_expiry:
            continue
        strike = finite_float(get("strike"))
        opt = str(get("option_type")).strip().upper()
        ts = get("timestamp")
        close = finite_float(get("close"))
        if strike is None or opt not in {"CE", "PE"}:
            continue
        if isinstance(ts, datetime.datetime):
            ts_key = ts
        else:
            ts_key = datetime.datetime.fromisoformat(str(ts))
        key = (exp, strike, opt)
        if key not in latest or ts_key > latest[key]["timestamp"]:
            latest[key] = {
                "timestamp": ts_key,
                "close": close,
                "spot": finite_float(get("spot")),
                "volume": finite_float(get("volume")),
                "oi": finite_float(get("oi")),
            }
        elif ts_key == latest[key]["timestamp"]:
            latest_ties[key] += 1
    except Exception:
        continue

if latest_ties:
    raise SystemExit(f"ERROR: HF reference has tied latest timestamps for {len(latest_ties)} contracts")

hf_missing_final_close = sum(1 for v in latest.values() if v["close"] is None)
if hf_missing_final_close:
    raise SystemExit(f"ERROR: HF reference has {hf_missing_final_close} contracts with missing final close")

if not latest:
    raise SystemExit("ERROR: zero HF NIFTY contracts for the target trade date/expiry")

# Parse the official UDiFF archive.
with zipfile.ZipFile(OFFICIAL) as z:
    csv_names = [n for n in z.namelist() if n.lower().endswith(".csv")]
    if not csv_names:
        raise SystemExit("ERROR: official archive has no CSV")
    with z.open(csv_names[0]) as fh:
        text = fh.read().decode("utf-8-sig", errors="replace")
official_rows = list(csv.DictReader(io.StringIO(text)))

official_map = {}
official_duplicate_keys = Counter()
official_missing_close = 0
official_spots = []

for row in official_rows:
    if row.get("TckrSymb", "").strip() != "NIFTY":
        continue
    opt = row.get("OptnTp", "").strip().upper()
    if opt not in {"CE", "PE"}:
        continue
    try:
        exp = parse_date(row["XpryDt"])
    except Exception:
        continue
    if exp != target_expiry:
        continue
    strike = finite_float(row.get("StrkPric"))
    close = finite_float(row.get("ClsPric"))
    if strike is None:
        continue
    spot = None
    for name in ["UndrlygPric", "UndrlygVal", "UnderlyingValue", "Underlying"]:
        if row.get(name) not in (None, ""):
            spot = finite_float(row.get(name))
            if spot is not None:
                break
    if spot is not None:
        official_spots.append(spot)
    if close is None:
        official_missing_close += 1
        continue
    key = (exp, strike, opt)
    if key in official_map:
        official_duplicate_keys[key] += 1
    else:
        official_map[key] = {
            "close": close,
            "spot": spot,
        }

if official_duplicate_keys:
    raise SystemExit(f"ERROR: official UDiFF duplicate NIFTY keys: {len(official_duplicate_keys)}")
if official_missing_close:
    raise SystemExit(f"ERROR: official NIFTY target-expiry core close missing: {official_missing_close}")
if not official_map:
    raise SystemExit("ERROR: zero official NIFTY contracts for selected expiry")

matched = set(official_map) & set(latest)
official_coverage = len(matched) / max(1, len(official_map))
hf_coverage = len(matched) / max(1, len(latest))
if official_coverage < MIN_KEY_COVERAGE or hf_coverage < MIN_KEY_COVERAGE:
    raise SystemExit(
        f"ERROR: key coverage below threshold: official={official_coverage:.4%}, hf={hf_coverage:.4%}"
    )

abs_errors = []
within_tolerance = 0
for key in matched:
    a = official_map[key]["close"]
    b = latest[key]["close"]
    err = abs(a - b)
    abs_errors.append(err)
    if err <= max(0.05, 0.0025 * abs(a)):
        within_tolerance += 1

close_tolerance_fraction = within_tolerance / max(1, len(matched))
if close_tolerance_fraction < MIN_CLOSE_TOLERANCE:
    raise SystemExit(
        f"ERROR: close-price reconciliation below threshold: {close_tolerance_fraction:.4%}"
    )

# Compare underlying/index value using latest HF spot and the official EOD spot.
hf_spot = None
if mapping["spot"]:
    spot_candidates = [
        latest[k]["spot"] for k in latest
        if latest[k]["spot"] is not None
    ]
    if spot_candidates:
        # Use the spot observed at the last timestamp represented by the HF file.
        last_ts = max(latest[k]["timestamp"] for k in latest)
        last_spots = [
            latest[k]["spot"] for k in latest
            if latest[k]["timestamp"] == last_ts and latest[k]["spot"] is not None
        ]
        if last_spots:
            hf_spot = sum(last_spots) / len(last_spots)

official_spot = (sum(official_spots) / len(official_spots)) if official_spots else None
spot_error = abs(hf_spot - official_spot) if (hf_spot is not None and official_spot is not None) else None
if spot_error is None:
    raise SystemExit("ERROR: underlying spot could not be compared from both sources")
if spot_error > MAX_SPOT_ERROR:
    raise SystemExit(f"ERROR: underlying spot mismatch {spot_error:.4f} > {MAX_SPOT_ERROR}")

report = {
    "official_snapshot": "2024-07-08_UDiFF",
    "hf_dataset": hf_meta["dataset"],
    "hf_file": hf_meta["selected_file"],
    "target_trade_date": target_trade_date.isoformat(),
    "matched_expiry": target_expiry.isoformat(),
    "official_target_expiry_keys": len(official_map),
    "hf_target_expiry_latest_keys": len(latest),
    "matched_contract_keys": len(matched),
    "official_key_coverage_of_hf": hf_coverage,
    "hf_key_coverage_of_official": official_coverage,
    "close_tolerance_fraction": close_tolerance_fraction,
    "median_abs_close_error": sorted(abs_errors)[len(abs_errors)//2],
    "p95_abs_close_error": sorted(abs_errors)[min(len(abs_errors)-1, int(0.95*len(abs_errors)))],
    "hf_latest_spot": hf_spot,
    "official_eod_spot": official_spot,
    "spot_error": spot_error,
    "status": "PASS",
    "thresholds": {
        "min_key_coverage": MIN_KEY_COVERAGE,
        "min_close_tolerance_fraction": MIN_CLOSE_TOLERANCE,
        "max_spot_error": MAX_SPOT_ERROR,
    },
}
(OUT / "official_vs_hf_reconciliation.json").write_text(
    json.dumps(report, indent=2, default=str), encoding="utf-8"
)
print(json.dumps(report, indent=2, default=str))
