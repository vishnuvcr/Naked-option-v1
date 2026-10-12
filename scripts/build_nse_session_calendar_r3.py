#!/usr/bin/env python3
"""Generate a daily NSE Capital Market session calendar from pinned official holiday sources."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "data" / "NSE_EQUITY_TRADING_CALENDAR_2021_2026_R3.json"
OUTPUT = ROOT / "research" / "data" / "NSE_CAPITAL_MARKET_SESSION_CALENDAR_R3_2026-10-13.json"
START = date(2021, 10, 11)
END = date(2026, 10, 10)
EXPECTED_YEARS = set(range(2021, 2027))

def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def build_calendar(source: dict[str, Any], source_raw: bytes) -> dict[str, Any]:
    if source.get("calendar_id") != "NSE_CAPITAL_MARKET_EQUITIES_2021_2026_R3":
        raise ValueError("CALENDAR_BLOCKED: source calendar id mismatch")
    if source.get("timezone") != "Asia/Kolkata":
        raise ValueError("CALENDAR_BLOCKED: timezone must be Asia/Kolkata")
    if source.get("date_bounds") != {"start": START.isoformat(), "end_inclusive": END.isoformat()}:
        raise ValueError("CALENDAR_BLOCKED: date bounds differ from frozen data range")
    annual_sources = {int(row.get("year",0)) for row in source.get("sources",[]) if row.get("url") and row.get("circular")}
    if annual_sources != EXPECTED_YEARS:
        raise ValueError(f"CALENDAR_BLOCKED: missing official annual source metadata: {sorted(annual_sources)}")
    holidays: dict[str, str] = {}
    by_year = source.get("regular_session_holidays_by_year",{})
    for year in range(2021,2027):
        entries=by_year.get(str(year))
        if not isinstance(entries,list) or not entries:
            raise ValueError(f"CALENDAR_BLOCKED: missing annual holiday list for {year}")
        for item in entries:
            d=item.get("date")
            try: parsed=date.fromisoformat(d)
            except Exception: raise ValueError(f"CALENDAR_BLOCKED: invalid holiday date {d!r}") from None
            if parsed.year != year:
                raise ValueError(f"CALENDAR_BLOCKED: holiday {d} filed under wrong year")
            if d in holidays:
                raise ValueError(f"CALENDAR_BLOCKED: duplicate holiday date {d}")
            holidays[d]=item.get("description","Official holiday")
    supplement_dates=set()
    for item in source.get("supplements",[]):
        d=item.get("date","")
        if item.get("date_reconciled_from_live_page") is not True or not item.get("source_url"):
            raise ValueError(f"CALENDAR_BLOCKED: supplemental closure not source-pinned: {item!r}")
        if d not in holidays:
            supplement_dates.add(d)
    # Source additions override old/sparse annual PDFs only as an explicit, provenance-bearing supplement.
    for item in source.get("supplements",[]):
        holidays.setdefault(item["date"], item.get("description","Official source supplement"))
    specials={}
    for item in source.get("special_sessions",[]):
        d=item.get("date")
        try: parsed=date.fromisoformat(d)
        except Exception: raise ValueError(f"CALENDAR_BLOCKED: invalid special-session date {d!r}") from None
        if d in specials:
            raise ValueError(f"CALENDAR_BLOCKED: duplicate special-session date {d}")
        if not item.get("source_url") or not item.get("circular") or not item.get("session_id"):
            raise ValueError(f"CALENDAR_BLOCKED: special session lacks a source pin: {d}")
        for flag in ("intraday_eligible","positional_eligible","regular_hours_compatible"):
            if not isinstance(item.get(flag),bool):
                raise ValueError(f"CALENDAR_BLOCKED: special session {d} missing boolean {flag}")
        if parsed < START or parsed > END:
            continue
        specials[d]=item

    days=[]
    current=START
    session_index=0
    while current<=END:
        ds=current.isoformat()
        is_weekday=current.weekday()<5
        special=specials.get(ds)
        if special:
            is_open=True
            session_type=special["session_mode"]
            intraday=bool(special["intraday_eligible"])
            positional=bool(special["positional_eligible"])
            compatible=bool(special["regular_hours_compatible"])
            opened_reason=special["reason"]
            regular_open=special.get("open") if compatible else None
            regular_close=special.get("close") if compatible else None
            source_circular=special["circular"]
            session_id=special["session_id"]
        elif is_weekday and ds not in holidays:
            is_open=True
            session_type="regular"
            intraday=True
            positional=True
            compatible=True
            opened_reason="Regular weekday session under official NSE Capital Market calendar."
            regular_open=source["regular_session"]["open"]
            regular_close=source["regular_session"]["close"]
            source_circular=None
            session_id=f"NSE_CM_{ds}"
        else:
            is_open=False
            intraday=False
            positional=False
            compatible=False
            regular_open=None
            regular_close=None
            source_circular=None
            session_id=None
            if ds in holidays:
                session_type="declared_full_day_holiday"
                opened_reason=holidays[ds]
            elif not is_weekday:
                session_type="weekend_closed"
                opened_reason="Saturday/Sunday closed unless an explicit, source-pinned special session overrides this rule."
            else:
                session_type="closed"
                opened_reason="Exchange not scheduled open."
        if is_open:
            session_index+=1
        days.append({
            "date":ds,
            "weekday":current.strftime("%A"),
            "is_exchange_trading_session":is_open,
            "exchange_session_index":session_index if is_open else None,
            "session_type":session_type,
            "session_id":session_id,
            "regular_hours_compatible":compatible,
            "regular_open":regular_open,
            "regular_close":regular_close,
            "intraday_label_eligible":intraday,
            "positional_label_eligible":positional,
            "source_circular":source_circular,
            "description":opened_reason
        })
        current+=timedelta(days=1)
    session_dates=[x["date"] for x in days if x["is_exchange_trading_session"]]
    if len(session_dates)!=len(set(session_dates)):
        raise ValueError("CALENDAR_BLOCKED: duplicate exchange-session dates")
    # Every weekend opening must be explicitly declared and regular-hours compatible.
    special_by_date={x["date"]:x for x in source.get("special_sessions",[])}
    for row in days:
        if row["is_exchange_trading_session"] and row["weekday"] in ("Saturday","Sunday"):
            special=special_by_date.get(row["date"])
            if not special or not special.get("source_url"):
                raise ValueError(f"CALENDAR_BLOCKED: unsupported weekend session {row['date']}")
        if row["intraday_label_eligible"] and not row["regular_hours_compatible"]:
            raise ValueError(f"CALENDAR_BLOCKED: intraday-eligible date lacks regular hours: {row['date']}")
    special_list=sorted(specials.values(),key=lambda x:x["date"])
    return {
      "schema_version":"nse-capital-market-session-calendar-v1",
      "calendar_id":"NSE_CAPITAL_MARKET_EQUITIES_2021_2026_R3",
      "status":"GENERATED_FROM_PINNED_OFFICIAL_SOURCE_PENDING_DATA_PREFLIGHT",
      "timezone":"Asia/Kolkata",
      "date_bounds":{"start":START.isoformat(),"end_inclusive":END.isoformat()},
      "regular_session":source["regular_session"],
      "source_calendar_path":SOURCE.relative_to(ROOT).as_posix(),
      "source_calendar_sha256":sha256(source_raw),
      "source_calendar_git_blob_sha1":git_blob_sha1(source_raw),
      "source_circulars":source["sources"],
      "source_supplements":source["supplements"],
      "special_sessions_in_bounds":special_list,
      "regular_session_holidays_by_year":source["regular_session_holidays_by_year"],
      "day_count":len(days),
      "calendar_day_rows":days,
      "exchange_session_count":sum(x["is_exchange_trading_session"] for x in days),
      "intraday_label_eligible_session_count":sum(x["intraday_label_eligible"] for x in days),
      "positional_label_eligible_session_count":sum(x["positional_label_eligible"] for x in days),
      "notes":[
        "This calendar is a frozen, sourced session assumption to be reconciled to observed SPOT timestamps before labels are generated.",
        "Special Muhurat and multi-segment BCP/DR dates are explicitly excluded from both label grids; a later change requires a dated protocol amendment before inspecting prediction results.",
        "No raw market rows are represented in this file."
      ]
    }

def main()->int:
    raw=SOURCE.read_bytes()
    source=json.loads(raw.decode("utf-8"))
    obj=build_calendar(source, raw)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    out_raw=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    OUTPUT.write_bytes(out_raw)
    summary={
      "status":obj["status"],
      "calendar_day_rows":obj["day_count"],
      "exchange_session_count":obj["exchange_session_count"],
      "intraday_label_eligible_session_count":obj["intraday_label_eligible_session_count"],
      "positional_label_eligible_session_count":obj["positional_label_eligible_session_count"],
      "special_session_dates":[x["date"] for x in obj["special_sessions_in_bounds"]],
      "source_calendar_sha256":obj["source_calendar_sha256"],
      "generated_calendar_sha256":sha256(out_raw),
      "output_git_blob_sha1":git_blob_sha1(out_raw)
    }
    print(json.dumps(summary,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
