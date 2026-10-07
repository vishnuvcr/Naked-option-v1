from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
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

# Free-source chain: Stooq first, FRED series next, Yahoo chart API last.
# FRED is preferred fallback because it is stable and revision timing can be
# explicitly handled. The selected provider is always recorded.
SERIES={
    "S25":{"stooq":"https://stooq.com/q/d/l/?s=%5Espx&i=d","fred_ids":["SP500"],"yahoo":"%5EGSPC"},
    "S26":{"stooq":"https://stooq.com/q/d/l/?s=%5Endq&i=d","fred_ids":["NASDAQCOM"],"yahoo":"%5EIXIC"},
    "S27":{"stooq":"https://stooq.com/q/d/l/?s=%5Enk&i=d","fred_ids":["NIKKEI225"],"yahoo":"%5EN225"},
    "S28":{"stooq":"https://stooq.com/q/d/l/?s=%5Ehsi&i=d","fred_ids":["HSI","HANGSENG"],"yahoo":"%5EHSI","github_raw":"https://raw.githubusercontent.com/rq1234/UROP-tar-efficiency/c44c1f9aaa9288908590ee4fb7bd4f3aac64edc7/data/equity/hangseng.csv"},
    "S20":{"fred_ids":["DGS10"]},
}
HEADERS={"User-Agent":"NIFTY-Naked-Option-Research/1.0","Accept":"text/csv,application/json,*/*"}

def fetch_bytes(url: str) -> bytes:
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=120) as resp:
        data=resp.read()
    if not data:
        raise ValueError("empty_response")
    return data

def parse_csv_rows(raw: bytes) -> tuple[list[str],int]:
    text=raw.decode("utf-8-sig",errors="replace")
    reader=csv.DictReader(text.splitlines())
    dates=[]
    valid_values=0
    for row in reader:
        value=row.get("Date") or row.get("DATE") or row.get("observation_date")
        if not value:
            continue
        try:
            d=dt.date.fromisoformat(str(value).strip()[:10])
        except ValueError:
            continue
        if not (START <= d <= END):
            continue
        dates.append(d.isoformat())
        close=row.get("Close") or row.get("CLOSE") or row.get("close") or row.get("price") or row.get("Price") or row.get("SP500") or row.get("NASDAQCOM") or row.get("NIKKEI225") or row.get("HSI") or row.get("HANGSENG") or row.get("DGS10")
        try:
            if close not in (None,"",".") and float(str(close).replace(",","")) == float(str(close).replace(",","")):
                valid_values += 1
        except Exception:
            pass
    return dates,valid_values

def stooq_window_csv(base_url: str) -> bytes:
    chunks=[]
    cur=START
    while cur<=END:
        stop=min(cur+dt.timedelta(days=179),END)
        url=base_url+f"&d1={cur:%Y%m%d}&d2={stop:%Y%m%d}"
        raw=fetch_bytes(url)
        text=raw.decode("utf-8-sig",errors="replace")
        reader=csv.DictReader(text.splitlines())
        rows=list(reader)
        if not rows:
            raise ValueError(f"stooq_empty_chunk:{cur}:{stop}")
        for row in rows:
            value=row.get("Date") or row.get("DATE")
            if value:
                row["_date"] = str(value).strip()[:10]
                chunks.append(row)
        cur=stop+dt.timedelta(days=1)
    if not chunks:
        raise ValueError("stooq_no_chunk_observations")
    fields=[k for k in chunks[0].keys() if k!="_date"]
    seen=set()
    out=[",".join(fields)]
    for row in chunks:
        d=row.get("_date","")
        if d in seen:
            continue
        seen.add(d)
        out.append(",".join(str(row.get(k,"")) for k in fields))
    return ("\n".join(out)+"\n").encode("utf-8")

def yahoo_csv(symbol: str) -> bytes:
    p1=int(dt.datetime.combine(START,dt.time.min,tzinfo=dt.timezone.utc).timestamp())
    p2=int(dt.datetime.combine(END+dt.timedelta(days=1),dt.time.min,tzinfo=dt.timezone.utc).timestamp())
    url=(
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        +urllib.parse.quote(symbol,safe="")
        +f"?period1={p1}&period2={p2}&interval=1d&events=history"
    )
    data=json.loads(fetch_bytes(url).decode("utf-8"))
    result=(data.get("chart") or {}).get("result") or []
    if not result:
        raise ValueError("yahoo_empty_result")
    r=result[0]
    ts=r.get("timestamp") or []
    q=((r.get("indicators") or {}).get("quote") or [{}])[0]
    opens=q.get("open") or []; highs=q.get("high") or []; lows=q.get("low") or []
    closes=q.get("close") or []; volumes=q.get("volume") or []
    rows=["Date,Open,High,Low,Close,Volume"]
    for i,t in enumerate(ts):
        d=dt.datetime.fromtimestamp(int(t),tz=dt.timezone.utc).date()
        if not (START <= d <= END): continue
        def cell(values):
            v=values[i] if i < len(values) else None
            return "" if v is None else str(v)
        rows.append(f"{d.isoformat()},{cell(opens)},{cell(highs)},{cell(lows)},{cell(closes)},{cell(volumes)}")
    if len(rows)<=1:
        raise ValueError("yahoo_no_observations")
    return ("\n".join(rows)+"\n").encode("utf-8")

def write_and_check(path: Path, raw: bytes) -> tuple[list[str],int]:
    path.write_bytes(raw)
    dates,valid=parse_csv_rows(raw)
    if not dates:
        raise ValueError("no_observations_in_frozen_window")
    if valid==0:
        raise ValueError("no_numeric_close_values_in_frozen_window")
    if len(dates)!=len(set(dates)):
        raise ValueError("duplicate_dates")
    return dates,valid

records=[]
for sid,config in SERIES.items():
    selected_provider=None
    selected_url=None
    selected_path=None
    selected_dates=[]
    selected_valid=0
    cache_hit=False
    errors=[]

    candidates=[]
    if "stooq" in config:
        candidates.append(("stooq",config["stooq"],None))
    for fid in config.get("fred_ids",[]):
        candidates.append(("fred",f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fid}&cosd={START.isoformat()}&coed={END.isoformat()}",fid))
    if "yahoo" in config:
        candidates.append(("yahoo_chart_api",None,config["yahoo"]))
    if "github_raw" in config:
        candidates.append(("github_raw",config["github_raw"],None))

    for provider,url,extra in candidates:
        try:
            if provider=="stooq":
                path=RAW/f"{sid}_stooq_windowed_{START}_{END}.csv"
                if path.exists() and path.stat().st_size>0:
                    raw=path.read_bytes(); hit=True
                    dates,valid=parse_csv_rows(raw)
                    if not dates or valid==0: raise ValueError("cached_stooq_unusable")
                else:
                    raw=stooq_window_csv(url); hit=False
                    dates,valid=write_and_check(path,raw)
            elif provider=="fred":
                fid=extra
                path=RAW/f"{sid}_fred_{fid}_{START}_{END}.csv"
                if path.exists() and path.stat().st_size>0:
                    raw=path.read_bytes(); hit=True
                    dates,valid=parse_csv_rows(raw)
                    if not dates or valid==0: raise ValueError("cached_fred_unusable")
                else:
                    raw=fetch_bytes(url); hit=False
                    dates,valid=write_and_check(path,raw)
            elif provider=="github_raw":
                path=RAW/f"{sid}_github_raw_{START}_{END}.csv"
                if path.exists() and path.stat().st_size>0:
                    raw=path.read_bytes(); hit=True
                    dates,valid=parse_csv_rows(raw)
                    if not dates or valid==0: raise ValueError("cached_github_raw_unusable")
                else:
                    raw=fetch_bytes(url); hit=False
                    dates,valid=write_and_check(path,raw)
            else:
                symbol=extra
                path=RAW/f"{sid}_yahoo_{START}_{END}.csv"
                if path.exists() and path.stat().st_size>0:
                    raw=path.read_bytes(); hit=True
                    dates,valid=parse_csv_rows(raw)
                    if not dates or valid==0: raise ValueError("cached_yahoo_unusable")
                else:
                    raw=yahoo_csv(symbol); hit=False
                    dates,valid=write_and_check(path,raw)
            selected_provider=provider
            selected_url=url or ("https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(extra,safe=""))
            selected_path=path
            selected_dates=dates
            selected_valid=valid
            cache_hit=hit
            break
        except Exception as exc:
            errors.append(f"{provider}:{type(exc).__name__}:{exc}")

    if selected_provider is None:
        raise SystemExit(f"ERROR: no usable free global source for {sid}; attempts={errors}")

    if len(selected_dates)!=len(set(selected_dates)):
        raise SystemExit(f"ERROR: duplicate dates in {sid} from provider {selected_provider}")

    records.append({
        "source_id":sid,
        "provider":selected_provider,
        "url":selected_url,
        "source_attempt_errors":errors,
        "cache_hit":cache_hit,
        "path":str(selected_path.relative_to(ROOT)),
        "bytes":selected_path.stat().st_size,
        "sha256":hashlib.sha256(selected_path.read_bytes()).hexdigest(),
        "rows":len(selected_dates),
        "numeric_value_rows":selected_valid,
        "min_date":min(selected_dates),
        "max_date":max(selected_dates),
        "availability_rule":"Daily close used only when the source market had already closed before the NIFTY decision; otherwise default to next NIFTY session.",
    })

(OUT/"global_reference_window.json").write_text(json.dumps({
    "window_start":START.isoformat(),
    "window_end":END.isoformat(),
    "records":records,
    "free_source_policy":"Stooq primary; FRED free public series as first fallback; Yahoo Finance chart API as last free fallback; no paid source.",
},indent=2),encoding="utf-8")
print(OUT/"global_reference_window.json")
