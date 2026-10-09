from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import acquire_nifty_daily_history as mod


def fixture_rows(end_date: dt.date) -> list[dict]:
    rows = []
    day = mod.START_DATE
    i = 0
    while day <= end_date:
        if day.weekday() < 5:
            close = 10000.0 + i / 10.0
            rows.append({
                "date": day.isoformat(),
                "open": close - 1.0,
                "high": close + 1.0,
                "low": close - 2.0,
                "close": close,
                "volume": 100 + i,
                "source": "Yahoo Finance public chart; validated against official NSE archive",
                "available_at": day.isoformat() + "T18:30:00+05:30",
            })
            i += 1
        day += dt.timedelta(days=1)
    return rows


def write_cache(path: Path, manifest_path: Path, rows: list[dict]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=mod.CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    by_date = {row["date"]: row for row in rows}
    checks = []
    for day in mod.OVERLAP_DATES:
        row = by_date[day.isoformat()]
        checks.append({
            "date": day.isoformat(),
            "url": "https://example.invalid/official-nse-fixture.csv",
            "close": float(row["close"]),
            "yahoo_close": float(row["close"]),
            "abs_diff": 0.0,
            "within_1_point": True,
        })
    manifest = {
        "source": mod.SOURCE_NAME,
        "index": "Nifty 50",
        "exchange_timezone": mod.NIFTY_TIMEZONE,
        "requested_start": mod.START_DATE.isoformat(),
        "requested_end": rows[-1]["date"],
        "observed_start": rows[0]["date"],
        "observed_end": rows[-1]["date"],
        "rows": len(rows),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "source_url": "https://example.invalid/yahoo-fixture.json",
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "official_nse_overlap_checks": checks,
        "canonical_policy": "fixture only; not exchange-exact",
        "pit_rule": "strict historical timestamps",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def overlap_checks(rows: list[dict]) -> list[dict]:
    by_date = {row["date"]: row for row in rows}
    return [
        {
            "date": day.isoformat(),
            "url": "https://example.invalid/official-nse-fixture.csv",
            "close": float(by_date[day.isoformat()]["close"]),
            "yahoo_close": float(by_date[day.isoformat()]["close"]),
            "abs_diff": 0.0,
            "within_1_point": True,
        }
        for day in mod.OVERLAP_DATES
    ]


def test_valid_cache_reuses_file_without_network() -> None:
    now = dt.datetime(2026, 10, 10, 12, 0, tzinfo=mod.IST)
    rows = fixture_rows(now.date())
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "nifty.csv"
        manifest_path = root / "manifest.json"
        original_manifest = write_cache(path, manifest_path, rows)
        original_csv = path.read_bytes()
        with (
            patch.object(mod, "yahoo_daily", side_effect=AssertionError("unexpected download")),
            patch.object(mod, "compare_spots", side_effect=AssertionError("unexpected spot-check download")),
        ):
            result = mod.acquire(path, manifest_path, now=now)
        assert result["cache_hit"] is True, result
        assert result["cache_decision"] == "REUSED", result
        assert path.read_bytes() == original_csv, "valid cached CSV was unexpectedly rewritten"
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert stored["sha256"] == original_manifest["sha256"]
        assert stored["last_cache_decision"]["decision"] == "REUSED"


def test_stale_cache_is_reacquired_and_hashes_reconcile() -> None:
    now = dt.datetime(2026, 10, 10, 12, 0, tzinfo=mod.IST)
    stale_end = now.date() - dt.timedelta(days=20)
    old_rows = fixture_rows(stale_end)
    new_rows = fixture_rows(now.date() - dt.timedelta(days=1))
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "nifty.csv"
        manifest_path = root / "manifest.json"
        write_cache(path, manifest_path, old_rows)
        checks = [
            {"date": day.isoformat(), "close": float({r["date"]: r for r in new_rows}[day.isoformat()]["close"]),
             "yahoo_close": float({r["date"]: r for r in new_rows}[day.isoformat()]["close"]),
             "abs_diff": 0.0, "within_1_point": True}
            for day in mod.OVERLAP_DATES
        ]
        with (
            patch.object(mod, "yahoo_daily", return_value=("https://example.invalid/new.json", new_rows)),
            patch.object(mod, "compare_spots", return_value=checks),
        ):
            result = mod.acquire(path, manifest_path, now=now)
        assert result["cache_hit"] is False, result
        assert result["cache_decision"] == "REACQUIRED", result
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert stored["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert stored["bytes"] == path.stat().st_size
        assert stored["observed_end"] == new_rows[-1]["date"]


def test_hash_mismatch_invalidates_cache() -> None:
    now = dt.datetime(2026, 10, 10, 12, 0, tzinfo=mod.IST)
    rows = fixture_rows(now.date())
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "nifty.csv"
        manifest_path = root / "manifest.json"
        write_cache(path, manifest_path, rows)
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n")
        with (
            patch.object(mod, "yahoo_daily", return_value=("https://example.invalid/new.json", rows)),
            patch.object(mod, "compare_spots", return_value=overlap_checks(rows)),
        ):
            result = mod.acquire(path, manifest_path, now=now)
        assert result["cache_hit"] is False, result
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert stored["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_missing_manifest_cannot_bless_existing_csv() -> None:
    now = dt.datetime(2026, 10, 10, 12, 0, tzinfo=mod.IST)
    rows = fixture_rows(now.date())
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "nifty.csv"
        manifest_path = root / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=mod.CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        with (
            patch.object(mod, "yahoo_daily", return_value=("https://example.invalid/new.json", rows)),
            patch.object(mod, "compare_spots", return_value=[
                {"date": day.isoformat(), "close": 1.0, "yahoo_close": 1.0, "abs_diff": 0.0, "within_1_point": True}
                for day in mod.OVERLAP_DATES
            ]),
        ):
            result = mod.acquire(path, manifest_path, now=now)
        assert result["cache_hit"] is False, result
        assert manifest_path.is_file(), "successful reacquisition must write a manifest"


def test_session_date_uses_exchange_timezone() -> None:
    local_midnight = dt.datetime(2026, 10, 9, 0, 0, tzinfo=mod.IST)
    timestamp = int(local_midnight.timestamp())
    assert dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).date() == dt.date(2026, 10, 8)
    assert mod.session_date_from_timestamp(timestamp, "Asia/Kolkata") == dt.date(2026, 10, 9)


def test_query_boundaries_are_exchange_local_midnights() -> None:
    before_close = dt.datetime(2026, 10, 9, 12, 0, tzinfo=mod.IST)
    period1, period2 = mod.chart_period_timestamps(before_close)
    assert dt.datetime.fromtimestamp(period1, dt.timezone.utc).astimezone(mod.IST) == dt.datetime(2020, 1, 1, 0, 0, tzinfo=mod.IST)
    assert dt.datetime.fromtimestamp(period2, dt.timezone.utc).astimezone(mod.IST) == dt.datetime(2026, 10, 9, 0, 0, tzinfo=mod.IST)
    after_close = dt.datetime(2026, 10, 9, 19, 0, tzinfo=mod.IST)
    _, period2_after = mod.chart_period_timestamps(after_close)
    assert dt.datetime.fromtimestamp(period2_after, dt.timezone.utc).astimezone(mod.IST) == dt.datetime(2026, 10, 10, 0, 0, tzinfo=mod.IST)


def test_same_day_cache_is_rejected_before_bar_cutoff() -> None:
    now = dt.datetime(2026, 10, 9, 12, 0, tzinfo=mod.IST)
    rows = fixture_rows(now.date())
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "nifty.csv"
        manifest_path = root / "manifest.json"
        write_cache(path, manifest_path, rows)
        manifest, reason = mod.validate_cache(path, manifest_path, now=now)
        assert manifest is None
        assert "allowed complete session date 2026-10-08" in reason, reason


def test_overlap_manifest_close_mismatch_invalidates_cache() -> None:
    now = dt.datetime(2026, 10, 10, 12, 0, tzinfo=mod.IST)
    rows = fixture_rows(now.date())
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "nifty.csv"
        manifest_path = root / "manifest.json"
        write_cache(path, manifest_path, rows)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["official_nse_overlap_checks"][0]["yahoo_close"] = 12345.0
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        cached, reason = mod.validate_cache(path, manifest_path, now=now)
        assert cached is None
        assert "differs from cached CSV" in reason, reason


def main() -> None:
    checks = [
        test_valid_cache_reuses_file_without_network,
        test_stale_cache_is_reacquired_and_hashes_reconcile,
        test_hash_mismatch_invalidates_cache,
        test_missing_manifest_cannot_bless_existing_csv,
        test_session_date_uses_exchange_timezone,
        test_query_boundaries_are_exchange_local_midnights,
        test_same_day_cache_is_rejected_before_bar_cutoff,
        test_overlap_manifest_close_mismatch_invalidates_cache,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    print(f"PASS {len(checks)} NIFTY acquisition/cache regression checks")


if __name__ == "__main__":
    main()
