from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
START=dt.date.fromisoformat("2019-02-11")
END=dt.date.fromisoformat("2026-09-30")
RAW=ROOT/"data/cache/raw/global_window"
OUT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)

# Free-source chain: Stooq first, then Yahoo chart API for US/Asian equity
# indices if Stooq returns no usable observations in the frozen window.
SERIES={
    "S25":{"stooq":"https://stooq.com/q/d/l/?s=%5Espx&i=d","yahoo":"%5EGSPC"},
    "S26":{"stooq":"https://stooq.com/q/d/l/?s=%5Endq&i=d","yahoo":"%5EIXIC"},
    "S27":{"stooq":"https://stooq.com/q/d/l/?s=%5Enk&i=d","yahoo":"%5EN225"},
    "S28":{"stooq":"https://stooq.com/q/d/l/?s=%5Ehsi&i=d","yahoo":"%5EHSI"},
    "S20":{"fred":"https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"},
}
HEADERS={"User-Agent":"NIFTY-Naked-Option-Research/1.0","Accept":"text/csv,application/json,*/*"}

def fetch_bytes(url: str) -> bytes:
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=120) as resp:
        data=resp.read()
    if not data:
        raise ValueError("empty_response")
    return data

def parse_csv_dates(raw: bytes) -> list[str]:
    text=raw.decode("utf-8-sig",errors="replace")
    reader=csv.DictReader(text.splitlines())
    dates=[]
    for row in reader:
        value=row.get("Date") or row.get("DATE") or row.get("observation_date")
        if not value:
            continue
        try:
            d=dt.date.fromisoformat(str(value).strip()[:10])
        except ValueError:
            continue
        if START <= d <= END:
            dates.append(d.isoformat())
    return dates

def yahoo_csv(symbol: str) -> bytes:
    p1=int(dt.datetime.combine(START,dt.time.min,tzinfo=dt.timezone.utc).timestamp())
    p2=int(dt.datetime.combine(END+dt.timedelta(days=1),dt.time.min,tzinfo=dt.timezone.utc).timestamp())
    url=(
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        +urllib.parse.quote(symbol,safe="")
        +f"?period1={p1}&period2={p2}&interval=1d&events=history"
    )
    raw=fetch_bytes(url)
    data=json.loads(raw.decode("utf-8"))
    result=(data.get("chart") or {}).get("result") or []
    if not result:
        raise ValueError("yahoo_empty_result")
    r=result[0]
    timestamps=r.get("timestamp") or []
    quote=((r.get("indicators") or {}).get("quote") or [{}])[0]
    opens=quote.get("open") or []
    highs=quote.get("high") or []
    lows=quote.get("low") or []
    closes=quote.get("close") or []
    volumes=quote.get("volume") or []
    rows=["Date,Open,High,Low,Close,Volume"]
    for i,ts in enumerate(timestamps):
        d=dt.datetime.fromtimestamp(int(ts),tz=dt.timezone.utc).date()
        if not (START <= d <= END):
            continue
        def cell(values):
            v=values[i] if i < len(values) else None
            return "" if v is None else str(v)
        rows.append(f"{d.isoformat()},{cell(opens)},{cell(highs)},{cell(lows)},{cell(closes)},{cell(volumes)}")
    if len(rows)<=1:
        raise ValueError("yahoo_no_observations")
    return ("\n".join(rows)+"\n").encode("utf-8")

records=[]
for sid,config in SERIES.items():
    selected_raw=None
    selected_provider=None
    selected_url=None
    selected_path=None
    errors=[]

    # Try Stooq first for equity indices.
    if "stooq" in config:
        raw_path=RAW/f"{sid}_stooq_{START}_{END}.csv"
        try:
            if raw_path.exists() and raw_path.stat().st_size>0:
                raw=raw_path.read_bytes()
                dates=parse_csv_dates(raw)
                if not dates:
                    raise ValueError("cached_stooq_no_observations")
            else:
                raw=fetch_bytes(config["stooq"])
                dates=parse_csv_dates(raw)
                if not dates:
                    raise ValueError("stooq_no_observations")
                raw_path.write_bytes(raw)
            selected_raw=raw
            selected_provider="stooq"
            selected_url=config["stooq"]
            selected_path=raw_path
        except Exception as exc:
            errors.append(f"stooq:{type(exc).__name__}:{exc}")

    # Free fallback: Yahoo Finance chart API.
    if selected_raw is None and "yahoo" in config:
        raw_path=RAW/f"{sid}_yahoo_{START}_{END}.csv"
        try:
            if raw_path.exists() and raw_path.stat().st_size>0:
                raw=raw_path.read_bytes()
            else:
                raw=yahoo_csv(config["yahoo"])
                raw_path.write_bytes(raw)
            dates=parse_csv_dates(raw)
            if not dates:
                raise ValueError("cached_yahoo_no_observations")
            selected_raw=raw
            selected_provider="yahoo_chart_api"
            selected_url=(
                "https://query1.finance.yahoo.com/v8/finance/chart/"
                +urllib.parse.quote(config["yahoo"],safe="")
            )
            selected_path=raw_path
        except Exception as exc:
            errors.append(f"yahoo:{type(exc).__name__}:{exc}")

    # FRED remains the validated official US 10Y fallback and is not part of
    # the Stooq/Yahoo chain.
    if selected_raw is None and sid=="S20":
        raw_path=RAW/f"{sid}_{START}_{END}.csv"
        if raw_path.exists() and raw_path.stat().st_size>0:
            raw=raw_path.read_bytes()
        else:
            url=config["fred"]+"&cosd="+START.isoformat()+"&coed="+END.isoformat()
            raw=fetch_bytes(url)
            raw_path.write_bytes(raw)
        dates=parse_csv_dates(raw)
        if not dates:
            raise SystemExit("ERROR: FRED DGS10 returned no observations in the frozen window")
        selected_raw=raw
        selected_provider="fred"
        selected_url=config["fred"]+"&cosd="+START.isoformat()+"&coed="+END.isoformat()
        selected_path=raw_path

    if selected_raw is None or selected_path is None:
        raise SystemExit(f"ERROR: no usable free global source for {sid}; attempts={errors}")

    if len(dates)!=len(set(dates)):
        raise SystemExit(f"ERROR: duplicate dates in {sid} from provider {selected_provider}")

    records.append({
        "source_id":sid,
        "provider":selected_provider,
        "url":selected_url,
        "source_attempt_errors":errors,
        "cache_hit":selected_path.exists() and selected_path.stat().st_mtime < time.time(),
        "path":str(selected_path.relative_to(ROOT)),
        "bytes":selected_path.stat().st_size,
        "sha256":hashlib.sha256(selected_path.read_bytes()).hexdigest(),
        "rows":len(dates),
        "min_date":min(dates),
        "max_date":max(dates),
        "availability_rule":"Daily close used only when the source market had already closed before the NIFTY decision; otherwise default to next NIFTY session.",
    })

(OUT/"global_reference_window.json").write_text(json.dumps({
    "window_start":START.isoformat(),
    "window_end":END.isoformat(),
    "records":records,
    "free_source_policy":"Stooq primary for global equity indices; Yahoo Finance chart API is a free fallback if Stooq is unavailable; no paid source is used.",
},indent=2),encoding="utf-8")
print(OUT/"global_reference_window.json")
