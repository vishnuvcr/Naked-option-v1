from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import time
import urllib.parse
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cache" / "raw" / "global_history"
REPORT = ROOT / "data" / "reports"
RAW.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)

START = datetime(2018, 1, 1, tzinfo=timezone.utc)
END = datetime.now(timezone.utc) + pd.Timedelta(days=2)
MIN_ROWS = 500
MIN_COVERAGE_START = pd.Timestamp("2021-01-01")
HEADERS = {"User-Agent": "Mozilla/5.0 NIFTY-Naked-Option-Research/1.0"}

# Candidate sources are declared before the prediction run. Failures are recorded
# per-source so one unavailable symbol cannot block independent available sources.
SERIES = {
    "SENSEX": ("^BSESN", "India", "G01"),
    "BANKNIFTY": ("^NSEBANK", "India", "G02"),
    "SP500": ("^GSPC", "America/New_York", "G04"),
    "NASDAQ": ("^IXIC", "America/New_York", "G05"),
    "NIKKEI": ("^N225", "Asia/Tokyo", "G06"),
    "HANGSENG": ("^HSI", "Asia/Hong_Kong", "G06"),
    "VIX": ("^VIX", "America/New_York", "G08"),
    "USDINR": ("INR=X", "America/New_York", "G09"),
    "GOLD": ("GC=F", "America/New_York", "G11"),
    "CRUDE": ("CL=F", "America/New_York", "G12"),
    "INDIAVIX": ("^INDIAVIX", "Asia/Kolkata", "G16"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_series(key: str, symbol: str, expected_timezone: str) -> dict:
    dst = RAW / f"{key.lower()}.csv"
    if dst.exists() and dst.stat().st_size > 0:
        try:
            cached = pd.read_csv(dst, parse_dates=["date"])
            cached["close"] = pd.to_numeric(cached.get("close"), errors="coerce")
            cache_valid = (
                {"date", "close", "source_symbol", "source_timezone"}.issubset(cached.columns)
                and len(cached) >= MIN_ROWS
                and cached["date"].notna().all()
                and cached["date"].is_unique
                and cached["date"].min() <= MIN_COVERAGE_START
                and cached["close"].notna().all()
                and (cached["close"] > 0).all()
                and cached["source_symbol"].astype(str).eq(symbol).all()
                and cached["source_timezone"].notna().all()
                and cached["source_timezone"].astype(str).nunique() == 1
                and cached["date"].max() >= (pd.Timestamp.now().normalize() - pd.Timedelta(days=10))
            )
            if cache_valid:
                cached["date"] = pd.to_datetime(cached["date"]).dt.date.astype(str)
                return {
                    "id": key, "symbol": symbol, "status": "ACTIVE", "cache_hit": True,
                    "path": str(dst.relative_to(ROOT)), "rows": int(len(cached)),
                    "min_date": str(cached["date"].min()), "max_date": str(cached["date"].max()),
                    "timezone": str(cached["source_timezone"].iloc[0]), "sha256": sha256(dst),
                }
        except Exception:
            pass  # Invalid/stale cache is reacquired and its failure is captured below.

    query = urllib.parse.urlencode({
        "period1": int(START.timestamp()),
        "period2": int(END.timestamp()),
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    })
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol, safe='')}?{query}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    result = ((payload.get("chart") or {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError("provider returned no chart result")
    meta = result.get("meta") or {}
    timezone_name = meta.get("exchangeTimezoneName") or expected_timezone
    try:
        zone = ZoneInfo(timezone_name)
    except Exception:
        timezone_name = expected_timezone
        zone = ZoneInfo(timezone_name)

    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    if len(timestamps) != len(closes):
        raise RuntimeError(f"timestamp/close length mismatch: {len(timestamps)} vs {len(closes)}")

    rows = []
    for ts, close in zip(timestamps, closes):
        if ts is None or close is None:
            continue
        local_dt = datetime.fromtimestamp(int(ts), timezone.utc).astimezone(zone)
        value = float(close)
        if not pd.notna(value) or value <= 0:
            continue
        rows.append({
            "date": local_dt.date().isoformat(),
            "close": value,
            "source_symbol": symbol,
            "source_timezone": timezone_name,
        })
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("provider returned no valid positive closes")
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if len(frame) < MIN_ROWS:
        raise RuntimeError(f"coverage below minimum: {len(frame)} rows < {MIN_ROWS}")
    if frame["date"].min() > MIN_COVERAGE_START:
        raise RuntimeError(f"history begins too late for the registered walk-forward window: {frame['date'].min().date()}")
    frame.to_csv(dst, index=False, date_format="%Y-%m-%d")
    return {
        "id": key, "symbol": symbol, "status": "ACTIVE", "cache_hit": False,
        "path": str(dst.relative_to(ROOT)), "rows": int(len(frame)),
        "min_date": str(frame["date"].min().date()), "max_date": str(frame["date"].max().date()),
        "timezone": timezone_name, "sha256": sha256(dst), "provider_url": url,
    }


def main() -> None:
    records = []
    for key, (symbol, tz, family) in SERIES.items():
        try:
            record = fetch_series(key, symbol, tz)
            record["family_id"] = family
            records.append(record)
            print(f"{key}: ACTIVE rows={record['rows']} cache_hit={record['cache_hit']}")
        except Exception as exc:
            records.append({
                "id": key, "symbol": symbol, "family_id": family, "status": "BLOCKED_DATA",
                "reason": f"{type(exc).__name__}: {str(exc)[:300]}",
            })
            print(f"{key}: BLOCKED_DATA ({type(exc).__name__})")
        time.sleep(0.2)

    active = [r for r in records if r["status"] == "ACTIVE"]
    equities = {r["id"] for r in active}
    global_equities = len(equities.intersection({"SP500", "NASDAQ", "NIKKEI", "HANGSENG"}))
    if not active:
        print("WARNING: no global/peer source passed coverage validation; the pre-registered calendar control remains independently testable.")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "Yahoo Finance public chart endpoint (free research reference, not execution data)",
        "requested_start": START.date().isoformat(),
        "requested_end_exclusive": END.date().isoformat(),
        "minimum_rows": MIN_ROWS,
        "point_in_time_rule": "Source observations are joined only when their instrument-local session date is strictly earlier than the NIFTY decision session date.",
        "active_count": len(active),
        "global_equity_constituent_count": global_equities,
        "global_composite_eligible": global_equities >= 2,
        "series": records,
    }
    out = REPORT / "available_global_source_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}; active={len(active)} global_equities={global_equities}")


if __name__ == "__main__":
    main()
