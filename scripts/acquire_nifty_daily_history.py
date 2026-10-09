from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/cache/raw/phase3"
REPORT = ROOT / "data/reports"
CSV_PATH = RAW / "nifty50_daily.csv"
MANIFEST_PATH = REPORT / "nifty50_daily_manifest.json"

START_DATE = dt.date(2020, 1, 1)
SYMBOL = "^NSEI"
SOURCE_NAME = "Yahoo Finance public chart with official NSE overlap validation"
CACHE_MAX_AGE_DAYS = 7
IST = ZoneInfo("Asia/Kolkata")
UTC = dt.timezone.utc
HEADERS = {
    "User-Agent": "Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept": "application/json,text/plain,*/*",
}
CSV_FIELDS = [
    "date", "open", "high", "low", "close", "volume", "source", "available_at"
]
OVERLAP_DATES = (dt.date(2024, 7, 5), dt.date(2024, 7, 8))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def now_ist(value: dt.datetime | None = None) -> dt.datetime:
    """Return an aware Asia/Kolkata timestamp for cache and cutoff decisions."""
    if value is None:
        return dt.datetime.now(IST)
    if value.tzinfo is None:
        raise ValueError("now_ist must be timezone-aware")
    return value.astimezone(IST)


def exclusive_end_date(now: dt.datetime | None = None) -> dt.date:
    """Exclude today's potentially incomplete daily bar until after the close."""
    local_now = now_ist(now)
    cutoff = dt.time(18, 30)
    if local_now.timetz().replace(tzinfo=None) >= cutoff:
        return local_now.date() + dt.timedelta(days=1)
    return local_now.date()


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _write_csv_atomic(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError("refusing to write an empty NIFTY history")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def _validate_rows(rows: list[dict], manifest: dict, today: dt.date) -> tuple[bool, str]:
    if len(rows) < 1000:
        return False, f"row count below minimum: {len(rows)}"
    if set(CSV_FIELDS) - set(rows[0].keys()):
        return False, "required CSV columns are missing"
    try:
        dates = [dt.date.fromisoformat(str(row["date"])) for row in rows]
    except (TypeError, ValueError):
        return False, "one or more dates are not ISO calendar dates"
    if any(a >= b for a, b in zip(dates, dates[1:])):
        return False, "dates are not strictly increasing and unique"
    if dates[0] > START_DATE + dt.timedelta(days=7):
        return False, f"coverage starts more than 7 days after requested start {START_DATE.isoformat()}"
    if manifest.get("rows") != len(rows):
        return False, "manifest row count does not match CSV"
    if manifest.get("observed_start") != dates[0].isoformat():
        return False, "manifest observed_start does not match CSV"
    if manifest.get("observed_end") != dates[-1].isoformat():
        return False, "manifest observed_end does not match CSV"
    age_days = (today - dates[-1]).days
    if age_days < 0 or age_days > CACHE_MAX_AGE_DAYS:
        return False, (
            f"latest row age {age_days} days is outside the "
            f"0..{CACHE_MAX_AGE_DAYS} day freshness window"
        )
    for row, day in zip(rows, dates):
        try:
            close = float(row["close"])
        except (TypeError, ValueError):
            return False, f"non-numeric close on {day.isoformat()}"
        if not math.isfinite(close) or close <= 0:
            return False, f"invalid close on {day.isoformat()}"
        if row["source"] != "Yahoo Finance public chart; validated against official NSE archive":
            return False, f"unexpected source value on {day.isoformat()}"
        if row["available_at"] != day.isoformat() + "T18:30:00+05:30":
            return False, f"availability timestamp mismatch on {day.isoformat()}"
    checks = manifest.get("official_nse_overlap_checks")
    if not isinstance(checks, list):
        return False, "manifest is missing official NSE overlap checks"
    check_by_date = {str(item.get("date")): item for item in checks if isinstance(item, dict)}
    for day in OVERLAP_DATES:
        item = check_by_date.get(day.isoformat())
        if not item or item.get("within_1_point") is not True:
            return False, f"missing or failed NSE overlap validation for {day.isoformat()}"
    if manifest.get("source") != SOURCE_NAME or manifest.get("index") != "Nifty 50":
        return False, "manifest source or index identity mismatch"
    if not manifest.get("fetched_at_utc"):
        return False, "manifest lacks fetched_at_utc"
    return True, "cached CSV, manifest, coverage, freshness and NSE-overlap checks passed"


def validate_cache(
    path: Path = CSV_PATH,
    manifest_path: Path = MANIFEST_PATH,
    now: dt.datetime | None = None,
) -> tuple[dict | None, str]:
    """Validate cache bytes and manifest; never trust file presence alone."""
    if not path.is_file():
        return None, "cached NIFTY CSV is missing"
    if not manifest_path.is_file():
        return None, "NIFTY manifest is missing"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"cannot read NIFTY manifest: {type(exc).__name__}"
    actual_hash = sha256_file(path)
    if manifest.get("sha256") != actual_hash:
        return None, "cached CSV SHA-256 does not match manifest"
    if manifest.get("bytes") != path.stat().st_size:
        return None, "cached CSV byte count does not match manifest"
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None or set(CSV_FIELDS) - set(reader.fieldnames):
                return None, "cached CSV is missing required columns"
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return None, f"cannot parse cached CSV: {type(exc).__name__}"
    ok, reason = _validate_rows(rows, manifest, now_ist(now).date())
    if not ok:
        return None, reason
    return manifest, reason


def yahoo_daily(now: dt.datetime | None = None) -> tuple[str, list[dict]]:
    local_now = now_ist(now)
    end_date = exclusive_end_date(local_now)
    end = dt.datetime.combine(end_date, dt.time.min, tzinfo=UTC)
    start = dt.datetime.combine(START_DATE, dt.time.min, tzinfo=UTC)
    qs = urllib.parse.urlencode({
        "period1": int(start.timestamp()),
        "period2": int(end.timestamp()),
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    })
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(SYMBOL, safe='')}?{qs}"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    result = ((payload.get("chart") or {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError("Yahoo chart returned no result")
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    rows = []
    for i, timestamp in enumerate(timestamps):
        vals = {
            key: (quote.get(key, [None] * len(timestamps))[i]
                  if i < len(quote.get(key, [None] * len(timestamps))) else None)
            for key in ["open", "high", "low", "close", "volume"]
        }
        if vals["close"] is None:
            continue
        day = dt.datetime.fromtimestamp(timestamp, UTC).date().isoformat()
        rows.append({
            "date": day,
            "open": vals["open"],
            "high": vals["high"],
            "low": vals["low"],
            "close": vals["close"],
            "volume": vals["volume"],
            "source": "Yahoo Finance public chart; validated against official NSE archive",
            "available_at": day + "T18:30:00+05:30",
        })
    rows = sorted({row["date"]: row for row in rows}.values(), key=lambda row: row["date"])
    if len(rows) < 1000:
        raise RuntimeError(f"too few Yahoo NIFTY rows: {len(rows)}")
    return url, rows


def official_nse_spot_check(day: dt.date) -> dict:
    filename = f"ind_close_all_{day.strftime('%d%m%Y')}.csv"
    urls = [
        f"https://nsearchives.nseindia.com/content/indices/{filename}",
        f"https://archives.nseindia.com/content/indices/{filename}",
    ]
    last_error = None
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
                    "Accept": "text/csv,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                text = response.read().decode("utf-8-sig", errors="replace")
            rows = list(csv.DictReader(io.StringIO(text)))
            for row in rows:
                if str(row.get("Index Name", "")).strip() != "Nifty 50":
                    continue
                for key in ("Closing Index Value", "CLOSING_INDEX_VALUE"):
                    if row.get(key) not in (None, "", "-"):
                        return {"date": day.isoformat(), "url": url, "close": float(row[key])}
            last_error = "Nifty 50 row absent"
        except Exception as exc:  # noqa: BLE001 - try the alternative official archive URL
            last_error = f"{type(exc).__name__}: {exc}"
    return {"date": day.isoformat(), "status": "unavailable", "error": last_error}


def compare_spots(yahoo_rows: list[dict]) -> list[dict]:
    by_date = {row["date"]: row for row in yahoo_rows}
    checks = []
    for day in OVERLAP_DATES:
        official = official_nse_spot_check(day)
        yahoo_row = by_date.get(day.isoformat())
        if official.get("close") is None or yahoo_row is None:
            raise RuntimeError(
                f"official/Yahoo overlap missing for {day.isoformat()}: {official}"
            )
        diff = abs(float(yahoo_row["close"]) - float(official["close"]))
        check = {
            **official,
            "yahoo_close": float(yahoo_row["close"]),
            "abs_diff": diff,
            "within_1_point": diff <= 1.0,
        }
        checks.append(check)
        if diff > 1.0:
            raise RuntimeError(f"Yahoo-vs-NSE close mismatch on {day.isoformat()}: {diff}")
    return checks


def acquire(
    path: Path = CSV_PATH,
    manifest_path: Path = MANIFEST_PATH,
    now: dt.datetime | None = None,
    force_refresh: bool = False,
) -> dict:
    """Reuse a verified recent cache; download only if it is missing or invalid."""
    local_now = now_ist(now)
    cache_manifest, cache_reason = validate_cache(path, manifest_path, local_now)
    checked_at = dt.datetime.now(UTC).isoformat()
    if cache_manifest is not None and not force_refresh:
        cache_manifest["last_cache_decision"] = {
            "decision": "REUSED",
            "checked_at_utc": checked_at,
            "reason": cache_reason,
        }
        _write_json_atomic(manifest_path, cache_manifest)
        return {
            "status": "CACHED",
            "cache_hit": True,
            "cache_decision": "REUSED",
            "rows": int(cache_manifest["rows"]),
            "observed_start": cache_manifest["observed_start"],
            "observed_end": cache_manifest["observed_end"],
            "sha256": sha256_file(path),
            "reason": cache_reason,
        }

    source_url, rows = yahoo_daily(local_now)
    checks = compare_spots(rows)
    _write_csv_atomic(path, rows)
    manifest = {
        "source": SOURCE_NAME,
        "index": "Nifty 50",
        "requested_start": START_DATE.isoformat(),
        "requested_end": (exclusive_end_date(local_now) - dt.timedelta(days=1)).isoformat(),
        "observed_start": rows[0]["date"],
        "observed_end": rows[-1]["date"],
        "rows": len(rows),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "source_url": source_url,
        "fetched_at_utc": checked_at,
        "official_nse_overlap_checks": checks,
        "canonical_policy": (
            "Use official NSE data where directly available; use Yahoo only as a free bulk "
            "backfill reference after explicit NSE overlap validation. Derived rows retain "
            "provider provenance and are not treated as exchange-exact."
        ),
        "pit_rule": (
            "Daily global/index observations may enter features only at or after their "
            "information-availability time. No future rows enter rolling transformations."
        ),
        "last_cache_decision": {
            "decision": "REACQUIRED",
            "checked_at_utc": checked_at,
            "reason": (
                "force_refresh requested" if force_refresh else
                f"cache was not reusable: {cache_reason}"
            ),
        },
    }
    _write_json_atomic(manifest_path, manifest)
    return {
        "status": "ACQUIRED",
        "cache_hit": False,
        "cache_decision": "REACQUIRED",
        "rows": len(rows),
        "observed_start": rows[0]["date"],
        "observed_end": rows[-1]["date"],
        "sha256": manifest["sha256"],
        "nse_overlap_checks": checks,
        "reason": manifest["last_cache_decision"]["reason"],
    }


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    result = acquire()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
