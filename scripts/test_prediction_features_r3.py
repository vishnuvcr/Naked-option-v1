"""Synthetic-only tests for R3 lag-stack construction; no market data and no model fits."""
from __future__ import annotations

import unittest
from datetime import date, datetime, time, timedelta

from prediction_features_r3 import (
    EXPECTED_CALENDAR_ID,
    EXPECTED_CALENDAR_SHA256,
    EXPECTED_DATA_SHA256,
    FeatureBuildError,
    build_feature_batch,
    ordered_lagged_returns_and_levels,
)


IST = timedelta(hours=5, minutes=30)


def iso(day: str, hour: int, minute: int) -> str:
    return datetime.fromisoformat(f"{day}T{hour:02d}:{minute:02d}:00+05:30").isoformat()


def calendar_for(days: list[str]) -> dict:
    return {
        "calendar_id": EXPECTED_CALENDAR_ID,
        "calendar_day_rows": [
            {
                "date": day,
                "is_exchange_trading_session": True,
                "regular_hours_compatible": True,
                "intraday_label_eligible": True,
                "positional_label_eligible": True,
            }
            for day in days
        ],
    }


def intraday_rows(day: str, start: int, count: int, base: float = 100.0, step: float = 0.1):
    out = []
    for i in range(count):
        minute_of_day = start + i
        out.append({
            "row_type": "SPOT",
            "session_date": day,
            "timestamp_ist": iso(day, minute_of_day // 60, minute_of_day % 60),
            "nifty_close": str(base + i * step),
        })
    return out


def positional_rows(days: list[str], missing_close_days: set[str] | None = None):
    missing_close_days = missing_close_days or set()
    out = []
    for i, day in enumerate(days):
        if day in missing_close_days:
            continue
        out.append({
            "row_type": "SPOT",
            "session_date": day,
            "timestamp_ist": iso(day, 15, 30),
            "nifty_close": str(100.0 + i),
        })
    return out


def sequential_dates(start: str, count: int) -> list[str]:
    # Synthetic exchange calendar: weekdays only, so a +1-session label crosses weekends.
    current = date.fromisoformat(start)
    out = []
    while len(out) < count:
        if current.weekday() < 5:
            out.append(current.isoformat())
        current += timedelta(days=1)
    return out


class FeatureConstructionR3Tests(unittest.TestCase):
    def test_ordered_lag_stack_has_returns_then_levels_newest_to_oldest(self):
        closes = list(map(float, range(80, 101)))  # 21 exact closes for L=20
        feature = ordered_lagged_returns_and_levels(closes, 20)
        self.assertEqual(len(feature), 40)
        self.assertAlmostEqual(feature[0], 100.0 / 99.0 - 1.0)
        self.assertAlmostEqual(feature[1], 99.0 / 98.0 - 1.0)
        self.assertEqual(feature[20], 100.0)
        self.assertEqual(feature[21], 99.0)
        self.assertEqual(feature[-1], 81.0)

    def test_intraday_uses_exact_same_session_endpoints_and_counts_warmup(self):
        day = "2025-01-06"
        rows = intraday_rows(day, 9 * 60 + 16, 60)
        # A non-SPOT option row must never become a target or predictor.
        rows.append({"row_type": "OPTION", "session_date": day, "timestamp_ist": iso(day, 9, 20), "nifty_close": "999999"})
        batch = build_feature_batch(
            rows, calendar_for([day]), "INTRA_5M_UP_DOWN", 20,
            source_csv_sha256=EXPECTED_DATA_SHA256,
            calendar_sha256=EXPECTED_CALENDAR_SHA256,
        )
        self.assertEqual(batch.diagnostics["feature_dimension"], 40)
        self.assertEqual(batch.diagnostics["samples_considered"], 60)
        self.assertEqual(batch.diagnostics["target_pairs_possible"], 60)
        self.assertEqual(batch.diagnostics["target_pairs_missing"], 5)  # final five endpoints absent, not filled
        self.assertEqual(batch.diagnostics["feature_history_excluded"], 20)
        self.assertEqual(batch.diagnostics["samples_emitted"], 35)
        self.assertTrue(all(row.y == 1 for row in batch.samples))
        self.assertTrue(all(row.decision_session_index == row.target_endpoint_session_index for row in batch.samples))
        self.assertFalse(batch.diagnostics["model_fitting_performed"])
        self.assertFalse(batch.diagnostics["samples_persisted"])

    def test_intraday_targets_after_session_close_are_endpoint_ineligible_not_missing(self):
        day = "2025-01-07"
        rows = intraday_rows(day, 15 * 60 + 20, 11, base=100.0, step=0.1)
        batch = build_feature_batch(
            rows, calendar_for([day]), "INTRA_5M_UP_DOWN", 20,
            source_csv_sha256=EXPECTED_DATA_SHA256,
            calendar_sha256=EXPECTED_CALENDAR_SHA256,
        )
        self.assertEqual(batch.diagnostics["target_pairs_possible"], 6)
        self.assertEqual(batch.diagnostics["target_pairs_missing"], 0)
        self.assertEqual(batch.diagnostics["endpoint_ineligible"], 5)
        self.assertEqual(batch.diagnostics["samples_emitted"], 0)

    def test_exact_timestamp_is_required_no_nearest_row_substitution(self):
        day = "2025-01-08"
        rows = intraday_rows(day, 9 * 60 + 16, 60)
        missing_timestamp = iso(day, 9, 41)
        rows = [r for r in rows if r["timestamp_ist"] != missing_timestamp]
        batch = build_feature_batch(
            rows, calendar_for([day]), "INTRA_5M_UP_DOWN", 20,
            source_csv_sha256=EXPECTED_DATA_SHA256,
            calendar_sha256=EXPECTED_CALENDAR_SHA256,
        )
        self.assertGreaterEqual(batch.diagnostics["target_pairs_missing"], 6)
        # It is acceptable to use observed bars before the gap as lag history, but the missing label endpoint is never replaced.
        self.assertFalse(any(r.target_endpoint_timestamp == iso(day, 9, 41) for r in batch.samples))

    def test_flat_targets_are_excluded_and_counted(self):
        day = "2025-01-09"
        rows = intraday_rows(day, 9 * 60 + 16, 60, base=200.0, step=0.0)
        batch = build_feature_batch(
            rows, calendar_for([day]), "INTRA_5M_UP_DOWN", 20,
            source_csv_sha256=EXPECTED_DATA_SHA256,
            calendar_sha256=EXPECTED_CALENDAR_SHA256,
        )
        self.assertEqual(batch.diagnostics["flat_targets_excluded"], 55)
        self.assertEqual(batch.diagnostics["samples_emitted"], 0)

    def test_positional_horizon_counts_exchange_session_indices_not_calendar_days(self):
        days = sequential_dates("2025-01-02", 25)
        rows = positional_rows(days)
        batch = build_feature_batch(
            rows, calendar_for(days), "POS_1D_UP_DOWN", 20,
            source_csv_sha256=EXPECTED_DATA_SHA256,
            calendar_sha256=EXPECTED_CALENDAR_SHA256,
        )
        self.assertEqual(batch.diagnostics["samples_considered"], 25)
        self.assertEqual(batch.diagnostics["target_pairs_possible"], 24)
        self.assertEqual(batch.diagnostics["endpoint_ineligible"], 1)
        self.assertEqual(batch.diagnostics["target_pairs_missing"], 0)
        self.assertEqual(batch.diagnostics["feature_history_excluded"], 20)
        self.assertEqual(batch.diagnostics["samples_emitted"], 4)
        self.assertTrue(all(row.target_endpoint_session_index == row.decision_session_index + 1 for row in batch.samples))
        friday_prediction = next(row for row in batch.samples if datetime.fromisoformat(row.decision_timestamp).weekday() == 4)
        calendar_gap = datetime.fromisoformat(friday_prediction.target_endpoint_timestamp).date() - datetime.fromisoformat(friday_prediction.decision_timestamp).date()
        self.assertEqual(calendar_gap, timedelta(days=3))  # Friday to Monday is one exchange session, not one calendar day.
        self.assertEqual(len(batch.samples[0].features), 40)

    def test_missing_official_session_close_is_never_forward_filled(self):
        days = sequential_dates("2025-01-02", 27)
        missing_day = days[22]
        rows = positional_rows(days, {missing_day})
        batch = build_feature_batch(
            rows, calendar_for(days), "POS_1D_UP_DOWN", 20,
            source_csv_sha256=EXPECTED_DATA_SHA256,
            calendar_sha256=EXPECTED_CALENDAR_SHA256,
        )
        self.assertEqual(batch.diagnostics["missing_decision_close_sessions"], 1)
        self.assertGreaterEqual(batch.diagnostics["target_pairs_missing"], 1)
        # Histories that span the missing session are excluded rather than filled.
        self.assertGreater(batch.diagnostics["feature_history_excluded"], 0)

    def test_duplicate_eligible_timestamp_fails_closed(self):
        day = "2025-01-10"
        rows = intraday_rows(day, 9 * 60 + 16, 30)
        rows.append(dict(rows[0]))
        with self.assertRaisesRegex(FeatureBuildError, "DUPLICATE_ELIGIBLE_SPOT_TIMESTAMP"):
            build_feature_batch(
                rows, calendar_for([day]), "INTRA_5M_UP_DOWN", 20,
                source_csv_sha256=EXPECTED_DATA_SHA256,
                calendar_sha256=EXPECTED_CALENDAR_SHA256,
            )

    def test_unknown_lookback_and_changed_source_hash_fail_closed(self):
        with self.assertRaisesRegex(FeatureBuildError, "LOOKBACK_NOT_IN_FROZEN_REGISTRY"):
            ordered_lagged_returns_and_levels(list(range(21, 42)), 21)
        with self.assertRaisesRegex(FeatureBuildError, "CANONICAL_DATA_HASH_PIN_MISMATCH"):
            build_feature_batch([], calendar_for(["2025-01-06"]), "INTRA_5M_UP_DOWN", 20,
                                source_csv_sha256="0" * 64)

    def test_session_date_mismatch_is_quarantined_not_used(self):
        day = "2025-01-11"
        rows = intraday_rows(day, 9 * 60 + 16, 30)
        rows[0]["session_date"] = "2025-01-12"
        batch = build_feature_batch(
            rows, calendar_for([day]), "INTRA_5M_UP_DOWN", 20,
            source_csv_sha256=EXPECTED_DATA_SHA256,
            calendar_sha256=EXPECTED_CALENDAR_SHA256,
        )
        self.assertEqual(batch.diagnostics["quarantined_SESSION_DATE_MISMATCH"], 1)
        self.assertEqual(batch.diagnostics["eligible_SPOT_rows"], 29)

    def test_feature_workflow_checkout_ref_has_no_literal_backslash(self):
        from pathlib import Path
        workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "phase-08p-r3-feature-construction.yml"
        text = workflow.read_text(encoding="utf-8")
        malformed = "ref: " + "\\" + "$" + "{{ github.sha }}"
        self.assertNotIn(malformed, text)
        self.assertIn("ref: " + "$" + "{{ github.sha }}", text)


if __name__ == "__main__":
    unittest.main()
