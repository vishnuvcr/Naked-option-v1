#!/usr/bin/env python3
"""Fail-closed aggregate-only preflight for the pinned NIFTY minute composite.

The script reads a temporary decrypted gzip CSV, writes only aggregate diagnostics,
and never retains or emits raw observations. It does not fit models or access holdout data.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, math
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CALENDAR=ROOT/"research/data/NSE_CAPITAL_MARKET_SESSION_CALENDAR_R3_2026-10-13.json"
DEFAULT_PREREG=ROOT/"research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
EXPECTED_CANONICAL_CSV_SHA256="cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
EXPECTED_DATA_ROWS=8_999_865
EXPECTED_COLUMNS=47
EXPECTED_ROW_COUNTS={"OPTION":8_490_723,"SPOT":509_142}
EXPECTED_START=date(2021,10,11)
EXPECTED_END=date(2026,10,10)
LOCAL_TZ=ZoneInfo("Asia/Kolkata")
PRICE_PRIORITY=("spot_close","index_close","underlying_close","nifty_close","spot_price","index_price","close","price","last_price","ltp","close_price")
REQUIRED_COLUMNS={"row_type","timestamp_epoch","source_request_id","option_type"}
FEATURE_CHECK_COLUMNS=("option_close","returned_strike","option_type","expiry_date","expiry_mapping_source","time_to_expiry_years","lot_size","tick_size","spot_open","spot_high","spot_low","spot_close")
TIMESTAMP_COLUMNS=("timestamp_epoch",)

class PreflightBlocked(RuntimeError):
    pass

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def decoded_sha256(path:Path)->tuple[str,int]:
    h=hashlib.sha256(); total=0
    with gzip.open(path,"rb") as f:
        for block in iter(lambda:f.read(8*1024*1024),b""):
            h.update(block); total+=len(block)
    return h.hexdigest(),total

def epoch_to_datetime(raw:str)->tuple[int,datetime,str]:
    value=float(raw)
    if not math.isfinite(value): raise ValueError("non-finite timestamp")
    mag=abs(value)
    if mag>=1e17: unit="nanoseconds"; seconds=value/1e9
    elif mag>=1e14: unit="microseconds"; seconds=value/1e6
    elif mag>=1e11: unit="milliseconds"; seconds=value/1e3
    else: unit="seconds"; seconds=value
    dt=datetime.fromtimestamp(seconds,tz=timezone.utc).astimezone(LOCAL_TZ)
    return int(round(seconds)),dt,unit

def exact_close_column(header:list[str])->tuple[str|None,list[str]]:
    normalized={name.strip().lower():name for name in header}
    found=[normalized[name] for name in PRICE_PRIORITY if name in normalized]
    return (found[0] if found else None),found

def fold_for_day(day:str, folds:list[dict[str,Any]])->str|None:
    for fold in folds:
        if fold["start"] <= day <= fold["end_inclusive"]:
            return str(fold["id"])
    return None

def validation_sample_rules(prereg:dict[str,Any])->tuple[dict[str,Any],float]:
    """Return frozen validation minima and a checked target-pair missingness limit."""
    sample_rules=prereg.get("sample_eligibility")
    if not isinstance(sample_rules,dict):
        raise PreflightBlocked("PREREG_SAMPLE_ELIGIBILITY_MISSING_OR_INVALID")
    try:
        missing_fraction=float(sample_rules.get("target_pair_missing_fraction_max",0.01))
    except (TypeError,ValueError) as exc:
        raise PreflightBlocked("PREREG_TARGET_PAIR_MISSINGNESS_LIMIT_INVALID") from exc
    if not math.isfinite(missing_fraction) or not 0.0 <= missing_fraction <= 1.0:
        raise PreflightBlocked("PREREG_TARGET_PAIR_MISSINGNESS_LIMIT_OUT_OF_RANGE")
    return sample_rules, missing_fraction


def empty_metric()->dict[str,int]:
    return {"possible_target_pairs":0,"missing_target_pairs":0,"flat_exclusions":0,"up":0,"down":0,"classifiable_rows":0,"endpoint_ineligible":0}

def finalize_metric(label_id:str, fold_id:str, metric:dict[str,int], missing_max:float,
                    min_rows:int, min_class:int)->dict[str,Any]:
    denom=metric["possible_target_pairs"]
    miss=metric["missing_target_pairs"]
    rate=(miss/denom) if denom else None
    reasons=[]
    n=metric["classifiable_rows"]
    if denom==0: reasons.append("NO_POSSIBLE_TARGET_PAIRS")
    if rate is not None and rate>missing_max: reasons.append("TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT")
    if n<min_rows: reasons.append("VALIDATION_ROWS_BELOW_FROZEN_MINIMUM")
    if metric["up"]<min_class or metric["down"]<min_class: reasons.append("DIRECTION_CLASS_SUPPORT_BELOW_FROZEN_MINIMUM")
    return {"label_id":label_id,"fold_id":fold_id,**metric,
            "target_pair_missing_fraction":rate,"minimum_validation_rows":min_rows,
            "minimum_class_support_each_direction":min_class,
            "passes_frozen_data_minima":not reasons,"block_reasons":reasons}

def run_preflight(merged_gzip:Path, calendar_path:Path, prereg_path:Path)->dict[str,Any]:
    report:dict[str,Any]={
      "schema_version":1,
      "preflight":"phase-08p-r3-nifty-composite-data-preflight",
      "status":"RUNNING",
      "input_name":merged_gzip.name,
      "calendar_path":str(calendar_path.relative_to(ROOT) if calendar_path.is_relative_to(ROOT) else calendar_path.name),
      "preregistration_path":str(prereg_path.relative_to(ROOT) if prereg_path.is_relative_to(ROOT) else prereg_path.name),
      "market_rows_examined":False,"raw_rows_retained":False,"raw_rows_emitted":False,
      "plaintext_uploaded":False,"model_fitting_performed":False,"holdout_accessed":False,
      "blockers":[],"warnings":[]
    }
    if not merged_gzip.is_file(): raise PreflightBlocked(f"missing merged CSV.GZ: {merged_gzip}")
    cal=json.loads(calendar_path.read_text(encoding="utf-8"))
    prereg=json.loads(prereg_path.read_text(encoding="utf-8"))
    if cal.get("status")!="GENERATED_FROM_PINNED_OFFICIAL_SOURCE_PENDING_DATA_PREFLIGHT":
        report["blockers"].append("SESSION_CALENDAR_STATUS_INVALID")
    if cal.get("timezone")!="Asia/Kolkata" or cal.get("date_bounds")!={"start":"2021-10-11","end_inclusive":"2026-10-10"}:
        report["blockers"].append("SESSION_CALENDAR_RANGE_OR_TIMEZONE_INVALID")
    calendar_rows=cal.get("calendar_day_rows",[])
    if len(calendar_rows)!=1826 or cal.get("day_count")!=1826:
        report["blockers"].append("SESSION_CALENDAR_NOT_1826_DAYS")
    day_map={x["date"]:x for x in calendar_rows}
    if len(day_map)!=len(calendar_rows):
        report["blockers"].append("SESSION_CALENDAR_DUPLICATE_DATES")
    if any("prediction_session_index" not in row for row in calendar_rows):
        report["blockers"].append("SESSION_CALENDAR_PREDICTION_INDEX_MISSING")
    else:
        prediction_rows=[row for row in calendar_rows if row.get("prediction_session_index") is not None]
        prediction_indexes=[row["prediction_session_index"] for row in prediction_rows]
        if prediction_indexes!=list(range(1,len(prediction_indexes)+1)):
            report["blockers"].append("SESSION_CALENDAR_PREDICTION_INDEX_NOT_CONTIGUOUS")
        expected_prediction_rows=[row for row in calendar_rows if row.get("is_exchange_trading_session") and row.get("positional_label_eligible")]
        if len(prediction_rows)!=len(expected_prediction_rows) or cal.get("prediction_session_count")!=len(prediction_rows):
            report["blockers"].append("SESSION_CALENDAR_PREDICTION_INDEX_COUNT_MISMATCH")
    fold_defs=prereg.get("chronological_validation",{}).get("fold_calendar_windows",[])
    if len(fold_defs)!=8:
        report["blockers"].append("PREREG_OUTER_FOLD_COUNT_NOT_EIGHT")
    if report["blockers"]:
        report["status"]="BLOCKED_DATA_PREFLIGHT"
        return report

    raw_archive_sha=sha256_file(merged_gzip)
    canonical_sha,canonical_bytes_count=decoded_sha256(merged_gzip)
    report.update({
      "merged_gzip_sha256":raw_archive_sha,
      "canonical_uncompressed_csv_sha256":canonical_sha,
      "canonical_uncompressed_bytes":canonical_bytes_count,
      "expected_canonical_csv_sha256":EXPECTED_CANONICAL_CSV_SHA256,
      "canonical_hash_matches":canonical_sha==EXPECTED_CANONICAL_CSV_SHA256,
      "expected_rows":EXPECTED_DATA_ROWS,
      "expected_columns":EXPECTED_COLUMNS,
      "expected_row_type_counts":EXPECTED_ROW_COUNTS,
      "session_calendar_sha256":sha256_file(calendar_path),
      "session_calendar_source_sha256":cal.get("source_calendar_sha256"),
      "preregistration_git_blob_sha1":None,
      "market_rows_examined":True
    })
    if canonical_sha!=EXPECTED_CANONICAL_CSV_SHA256:
        report["blockers"].append("CANONICAL_DECODED_CSV_SHA256_MISMATCH")
        report["status"]="BLOCKED_DATA_PREFLIGHT"
        return report

    # Count-only schema and chronology scan. Prices/timestamps are used transiently in memory.
    row_counts=Counter(); blank_counts=Counter(); feature_blank_counts=Counter()
    width_errors=0; total_rows=0; malformed_timestamps=0; timestamp_units=Counter()
    local_min=None; local_max=None; out_of_range_rows=0
    spot_points:dict[int,tuple[datetime,float,str]]={}
    spot_by_day:dict[str,list[tuple[int,datetime,float]]]=defaultdict(list)
    duplicate_spot_timestamps=0; identical_value_duplicate_candidates=0
    unknown_spot_dates=Counter(); off_session_spot_rows=0; non_minute_timestamps=0
    spot_symbols:dict[str,Counter]=defaultdict(Counter)
    all_columns=None; price_field=None; price_candidates=[]
    row_hash_duplicate_blocked=False
    actual_close_times=Counter()
    option_rows=0; option_blanks=Counter()
    try:
        with gzip.open(merged_gzip,"rt",encoding="utf-8-sig",newline="") as handle:
            reader=csv.reader(handle,strict=True)
            header=next(reader,None)
            if not header or len(header)!=EXPECTED_COLUMNS or len(set(header))!=len(header):
                report["blockers"].append("CSV_HEADER_MISSING_DUPLICATE_OR_WRONG_COLUMN_COUNT")
                report["observed_header"]=header
                report["status"]="BLOCKED_DATA_PREFLIGHT"
                return report
            all_columns=header
            indexes={name:i for i,name in enumerate(header)}
            missing_required=sorted(REQUIRED_COLUMNS-set(header))
            if missing_required:
                report["blockers"].append("CSV_REQUIRED_COLUMNS_MISSING")
                report["missing_required_columns"]=missing_required
                report["observed_header"]=header
                report["status"]="BLOCKED_DATA_PREFLIGHT"
                return report
            price_field,price_candidates=exact_close_column(header)
            if price_field is None:
                report["blockers"].append("NO_UNAMBIGUOUS_SPOT_PRICE_FIELD")
                report["candidate_price_columns_present"]=[]
                report["observed_header"]=header
                report["status"]="BLOCKED_DATA_PREFLIGHT"
                return report
            for row in reader:
                total_rows+=1
                if len(row)!=len(header):
                    width_errors+=1
                    continue
                kind=row[indexes["row_type"]].strip().upper()
                row_counts[kind or "(blank)"]+=1
                if not kind: blank_counts["row_type"]+=1
                for f in FEATURE_CHECK_COLUMNS:
                    if f in indexes and not row[indexes[f]].strip():
                        feature_blank_counts[f]+=1
                        if kind=="OPTION": option_blanks[f]+=1
                ts_raw=row[indexes["timestamp_epoch"]].strip()
                if not ts_raw:
                    blank_counts["timestamp_epoch"]+=1
                    if kind=="SPOT": report["blockers"].append("SPOT_TIMESTAMP_BLANK")
                    continue
                try:
                    epoch,dt,unit=epoch_to_datetime(ts_raw)
                except Exception:
                    malformed_timestamps+=1
                    continue
                timestamp_units[unit]+=1
                iso=dt.isoformat()
                local_min=iso if local_min is None or iso<local_min else local_min
                local_max=iso if local_max is None or iso>local_max else local_max
                d=dt.date().isoformat()
                if d<EXPECTED_START.isoformat() or d>EXPECTED_END.isoformat():
                    out_of_range_rows+=1
                if kind!="SPOT":
                    if kind=="OPTION": option_rows+=1
                    continue
                dayrow=day_map.get(d)
                if dayrow is None or not dayrow.get("is_exchange_trading_session"):
                    unknown_spot_dates[d]+=1
                    continue
                if dt.second!=0 or dt.microsecond!=0:
                    non_minute_timestamps+=1
                if dayrow.get("regular_hours_compatible"):
                    t=dt.time().replace(tzinfo=None)
                    open_t=time.fromisoformat(cal["regular_session"]["open"])
                    close_t=time.fromisoformat(cal["regular_session"]["close"])
                    if not (open_t<=t<=close_t):
                        off_session_spot_rows+=1
                actual_close_times[dt.strftime("%H:%M")]+=1
                for name in ("symbol","instrument","underlying","ticker","index_symbol"):
                    if name in indexes and row[indexes[name]].strip():
                        spot_symbols[name][row[indexes[name]].strip()]+=1
                raw_price=row[indexes[price_field]].strip()
                try:
                    price=float(raw_price)
                except Exception:
                    price=float("nan")
                if not math.isfinite(price) or price<=0:
                    blank_counts["invalid_spot_price"]+=1
                    continue
                if epoch in spot_points:
                    duplicate_spot_timestamps+=1
                    old_dt,old_price,old_hash=spot_points[epoch]
                    row_signature=hashlib.sha256(json.dumps(row,separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest()
                    if price==old_price and row_signature==old_hash:
                        identical_value_duplicate_candidates+=1
                    row_hash_duplicate_blocked=True
                    continue
                row_signature=hashlib.sha256(json.dumps(row,separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest()
                spot_points[epoch]=(dt,price,row_signature)
                spot_by_day[d].append((epoch,dt,price))
    except csv.Error as exc:
        report["blockers"].append("CSV_PARSE_ERROR")
        report["csv_parse_error_type"]=type(exc).__name__
        report["rows_read_before_csv_error"]=total_rows
        report["rows_by_type_before_error"]=dict(sorted(row_counts.items()))
        report["status"]="BLOCKED_DATA_PREFLIGHT"
        return report

    report.update({
      "rows_read":total_rows,"columns":len(all_columns or []),
      "column_names":all_columns,
      "rows_by_type":dict(sorted(row_counts.items())),
      "row_width_errors":width_errors,
      "timestamp_unit_counts":dict(timestamp_units),
      "timestamp_min_local":local_min,"timestamp_max_local":local_max,
      "timestamp_out_of_range_rows":out_of_range_rows,
      "malformed_timestamps":malformed_timestamps,
      "blank_counts":dict(blank_counts),
      "chosen_spot_price_field":price_field,"recognized_price_candidates":price_candidates,
      "feature_blank_fraction_over_all_rows":{k:(v/total_rows if total_rows else None) for k,v in feature_blank_counts.items()},
      "option_rows":option_rows,
      "option_blank_counts":dict(option_blanks),
      "spot_timestamp_rows_unique":len(spot_points),
      "spot_day_count":len(spot_by_day),
      "duplicate_spot_timestamp_rows":duplicate_spot_timestamps,
      "fieldwise_identical_duplicate_candidates":identical_value_duplicate_candidates,
      "unknown_spot_dates":dict(sorted(unknown_spot_dates.items())),
      "off_session_spot_rows":off_session_spot_rows,
      "non_minute_spot_timestamps":non_minute_timestamps,
      "spot_identity_value_counts":{k:dict(v.most_common(20)) for k,v in spot_symbols.items()},
      "spot_bar_time_frequency":dict(actual_close_times.most_common(20))
    })
    if total_rows!=EXPECTED_DATA_ROWS: report["blockers"].append("ROW_COUNT_MISMATCH")
    if len(all_columns or [])!=EXPECTED_COLUMNS: report["blockers"].append("COLUMN_COUNT_MISMATCH")
    if dict(row_counts)!=EXPECTED_ROW_COUNTS: report["blockers"].append("ROW_TYPE_COUNT_MISMATCH")
    if width_errors: report["blockers"].append("ROW_WIDTH_ERRORS")
    if malformed_timestamps: report["blockers"].append("MALFORMED_TIMESTAMPS")
    if len(timestamp_units)!=1: report["blockers"].append("TIMESTAMP_EPOCH_UNIT_MIXED_OR_EMPTY")
    if out_of_range_rows: report["blockers"].append("TIMESTAMP_OUTSIDE_FROZEN_DATE_RANGE")
    if blank_counts.get("timestamp_epoch",0) or blank_counts.get("row_type",0): report["blockers"].append("BLANK_REQUIRED_KEYS")
    if unknown_spot_dates: report["blockers"].append("SPOT_ROWS_ON_CLOSED_OR_UNMAPPED_DATES")
    if off_session_spot_rows: report["blockers"].append("SPOT_ROWS_OUTSIDE_DECLARED_REGULAR_SESSION")
    if non_minute_timestamps: report["blockers"].append("SPOT_TIMESTAMPS_NOT_MINUTE_ALIGNED")
    if duplicate_spot_timestamps: report["blockers"].append("DUPLICATE_SPOT_TIMESTAMP_KEYS_REQUIRE_SOURCE_RECONCILIATION")
    if blank_counts.get("invalid_spot_price",0): report["blockers"].append("MISSING_OR_INVALID_SPOT_CLOSE_PRICES")

    eligible_expected_days=[r["date"] for r in calendar_rows if r.get("is_exchange_trading_session") and r.get("regular_hours_compatible") and r.get("positional_label_eligible")]
    missing_regular_dates=sorted(set(eligible_expected_days)-set(spot_by_day))
    report["missing_regular_spot_session_dates_count"]=len(missing_regular_dates)
    report["missing_regular_spot_session_dates_sample"]=missing_regular_dates[:30]
    missing_limit=max(1,math.ceil(0.01*len(eligible_expected_days)))
    if len(missing_regular_dates)>missing_limit: report["blockers"].append("MISSING_REGULAR_SPOT_SESSIONS_EXCEED_LIMIT")

    if report["blockers"]:
        report["status"]="BLOCKED_DATA_PREFLIGHT"
        return report

    # Assign calendar session IDs and derive transient daily close prices.
    by_session_index={r["exchange_session_index"]:r for r in calendar_rows if r.get("is_exchange_trading_session")}
    regular_close_time=time.fromisoformat(cal["regular_session"]["close"])
    regular_open_time=time.fromisoformat(cal["regular_session"]["open"])
    daily_close={}
    close_time_counts=Counter()
    nonstandard_closes=[]
    for d,points in spot_by_day.items():
        dayrow=day_map[d]
        if not (dayrow.get("positional_label_eligible") and dayrow.get("regular_hours_compatible")):
            continue
        eligible=[p for p in points if regular_open_time<=p[1].time().replace(tzinfo=None)<=regular_close_time]
        if not eligible: continue
        epoch,dt,price=max(eligible,key=lambda p:p[0])
        bar_time=dt.strftime("%H:%M")
        close_time_counts[bar_time]+=1
        # The pinned CSV labels bars by their exchange timestamp. Last bar must align with
        # either the 15:29 start-of-final-minute bar or explicit 15:30 close timestamp.
        if bar_time not in ("15:29","15:30"):
            nonstandard_closes.append(d)
            continue
        daily_close[dayrow["exchange_session_index"]]=(d,price,dt)
    report["session_close_time_frequency"]=dict(close_time_counts)
    report["nonstandard_session_close_count"]=len(nonstandard_closes)
    report["nonstandard_session_close_sample"]=nonstandard_closes[:30]
    if len(nonstandard_closes)>missing_limit: report["blockers"].append("MISSING_STANDARD_SESSION_CLOSES_EXCEED_LIMIT")

    folds=[str(x["id"]) for x in fold_defs]
    fold_metrics={label:{fold:empty_metric() for fold in folds} for label in (
      [x[0] for x in (( "INTRA_5M_UP_DOWN",5),("INTRA_15M_UP_DOWN",15),("INTRA_30M_UP_DOWN",30),("INTRA_60M_UP_DOWN",60),("INTRA_120M_UP_DOWN",120))]
      +[x[0] for x in (("POS_1D_UP_DOWN",1),("POS_2D_UP_DOWN",2),("POS_3D_UP_DOWN",3),("POS_5D_UP_DOWN",5),("POS_10D_UP_DOWN",10))]
    )}
    label_horizons={f"INTRA_{h}M_UP_DOWN":h for h in (5,15,30,60,120)}
    label_horizons.update({f"POS_{h}D_UP_DOWN":h for h in (1,2,3,5,10)})
    outer_start={str(x["id"]):x["start"] for x in fold_defs}
    outer_end={str(x["id"]):x["end_inclusive"] for x in fold_defs}
    # Intraday close-to-close labels use exact horizon timestamps, never cross a session.
    for epoch,(dt,price,row_sig) in spot_points.items():
        d=dt.date().isoformat(); fold=fold_for_day(d,fold_defs)
        dayrow=day_map[d]
        if fold is None or not dayrow.get("intraday_label_eligible") or not dayrow.get("regular_hours_compatible"):
            continue
        local_t=dt.time().replace(tzinfo=None)
        open_t=time.fromisoformat(cal["regular_session"]["open"]); close_t=time.fromisoformat(cal["regular_session"]["close"])
        if not (open_t<=local_t<close_t): continue
        for h in (5,15,30,60,120):
            lid=f"INTRA_{h}M_UP_DOWN"; target_epoch=epoch+h*60
            target_dt_guess=dt+timedelta(minutes=h)
            if target_dt_guess.date()!=dt.date() or target_dt_guess.time().replace(tzinfo=None)>=close_t:
                continue
            m=fold_metrics[lid][fold]; m["possible_target_pairs"]+=1
            target=spot_points.get(target_epoch)
            if target is None or target[0].date()!=dt.date():
                m["missing_target_pairs"]+=1
                continue
            ret=(target[1]/price)-1.0
            if abs(ret)<=1e-8: m["flat_exclusions"]+=1
            elif ret>0: m["up"]+=1; m["classifiable_rows"]+=1
            else: m["down"]+=1; m["classifiable_rows"]+=1

    # Positional close-to-close labels follow actual exchange-session index, but labels
    # cannot start/end on sessions explicitly excluded by the pinned calendar.
    for session_idx,(decision_date,decision_price,decision_dt) in daily_close.items():
        fold=fold_for_day(decision_date,fold_defs)
        if fold is None: continue
        for h in (1,2,3,5,10):
            lid=f"POS_{h}D_UP_DOWN"; target_idx=session_idx+h
            target_day=by_session_index.get(target_idx)
            if target_day is None: continue
            if fold_for_day(target_day["date"],fold_defs)!=fold: continue
            m=fold_metrics[lid][fold]; m["possible_target_pairs"]+=1
            if not target_day.get("positional_label_eligible") or target_idx not in daily_close:
                m["missing_target_pairs"]+=1; m["endpoint_ineligible"]+=1
                continue
            target_date,target_price,target_dt=daily_close[target_idx]
            ret=(target_price/decision_price)-1.0
            if abs(ret)<=1e-8: m["flat_exclusions"]+=1
            elif ret>0: m["up"]+=1; m["classifiable_rows"]+=1
            else: m["down"]+=1; m["classifiable_rows"]+=1

    validation=[]
    sample_rules, missing_limit_fraction = validation_sample_rules(prereg)
    for label_id in label_horizons:
        for fold in folds:
            row=finalize_metric(label_id,fold,fold_metrics[label_id][fold],missing_limit_fraction,
              int(sample_rules["minimum_validation_rows"][label_id]),
              int(sample_rules["minimum_class_support_each_direction_per_validation_fold"][label_id]))
            validation.append(row)
            if not row["passes_frozen_data_minima"]:
                report["blockers"].append(f"TARGET_SAMPLE_OR_CLASS_SUPPORT_GATE:{label_id}:{fold}")
    report["label_sample_support"]=validation
    report["label_support_summary"]={
      label:{"validation_rows_total":sum(x["classifiable_rows"] for x in validation if x["label_id"]==label),
             "up_total":sum(x["up"] for x in validation if x["label_id"]==label),
             "down_total":sum(x["down"] for x in validation if x["label_id"]==label),
             "folds_passing":sum(x["passes_frozen_data_minima"] for x in validation if x["label_id"]==label)}
      for label in label_horizons
    }
    report["status"]="BLOCKED_DATA_PREFLIGHT" if report["blockers"] else "PASS_DATA_PREFLIGHT"
    report["all_frozen_label_folds_meet_data_support_minima"]=not report["blockers"]
    report["source_artifact_id"]=11698879857
    report["source_artifact_run_id"]=38131641336
    report["feature_availability_note"]="Option expiry/lot/tick/IV/quote feature families must be separately screened; this report only establishes structural data integrity and spot-label support."
    return report

def main()->int:
    p=argparse.ArgumentParser(description="Aggregate-only R3 prediction data preflight; no model fitting or holdout access.")
    p.add_argument("--merged-gzip",type=Path,required=True)
    p.add_argument("--calendar",type=Path,default=DEFAULT_CALENDAR)
    p.add_argument("--preregistration",type=Path,default=DEFAULT_PREREG)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        report=run_preflight(a.merged_gzip.resolve(),a.calendar.resolve(),a.preregistration.resolve())
    except PreflightBlocked as exc:
        report={"schema_version":1,"preflight":"phase-08p-r3-nifty-composite-data-preflight",
                "status":"BLOCKED_DATA_PREFLIGHT","blockers":[str(exc)],
                "input_name":a.merged_gzip.name,"raw_rows_retained":False,"raw_rows_emitted":False,
                "plaintext_uploaded":False,"model_fitting_performed":False,"holdout_accessed":False}
    except Exception as exc:
        report={"schema_version":1,"preflight":"phase-08p-r3-nifty-composite-data-preflight",
                "status":"ERROR_DATA_PREFLIGHT","blockers":[f"UNEXPECTED_{type(exc).__name__}"],
                "error_message":str(exc)[:500],"input_name":a.merged_gzip.name,
                "raw_rows_retained":False,"raw_rows_emitted":False,"plaintext_uploaded":False,
                "model_fitting_performed":False,"holdout_accessed":False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("label_sample_support","column_names","unknown_spot_dates","spot_identity_value_counts")},sort_keys=True,indent=2))
    return 0 if report.get("status")=="PASS_DATA_PREFLIGHT" else 1

if __name__=="__main__":
    raise SystemExit(main())
