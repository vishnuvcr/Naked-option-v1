"""Developer-side regression tests for the pinned NSE exchange session calendar."""
from __future__ import annotations
import hashlib, json, sys, unittest
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_nse_session_calendar_r3 as build

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

class NSESessionCalendarR3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build.main()
        cls.source_raw=build.SOURCE.read_bytes()
        cls.source=read_json(build.SOURCE)
        cls.calendar=read_json(build.OUTPUT)
        cls.days={row["date"]:row for row in cls.calendar["calendar_day_rows"]}

    def test_day_range_is_full_and_unique(self):
        self.assertEqual(self.calendar["date_bounds"],{"start":"2021-10-11","end_inclusive":"2026-10-10"})
        self.assertEqual(self.calendar["day_count"],1826)
        dates=[row["date"] for row in self.calendar["calendar_day_rows"]]
        self.assertEqual(len(dates),len(set(dates)))
        self.assertEqual(dates[0],"2021-10-11")
        self.assertEqual(dates[-1],"2026-10-10")

    def test_source_metadata_and_exact_file_hash_are_pinned(self):
        self.assertEqual(self.calendar["source_calendar_path"],build.SOURCE.relative_to(ROOT).as_posix())
        self.assertEqual(self.calendar["source_calendar_sha256"],hashlib.sha256(self.source_raw).hexdigest())
        git_blob=hashlib.sha1(b"blob "+str(len(self.source_raw)).encode("ascii")+b"\0"+self.source_raw).hexdigest()
        self.assertEqual(self.calendar["source_calendar_git_blob_sha1"],git_blob)
        self.assertEqual({int(x["year"]) for x in self.calendar["source_circulars"]},{2021,2022,2023,2024,2025,2026})

    def test_regular_sessions_only_on_weekdays_not_closed_holidays(self):
        holidays={item["date"] for year,rows in self.source["regular_session_holidays_by_year"].items() for item in rows}
        holidays.update(item["date"] for item in self.source.get("supplements",[]))
        specials={item["date"]:item for item in self.source.get("special_sessions",[])}
        for row in self.calendar["calendar_day_rows"]:
            if row["session_type"]=="regular":
                d=date.fromisoformat(row["date"])
                self.assertLess(d.weekday(),5,row["date"])
                self.assertNotIn(row["date"],holidays,row["date"])
                self.assertEqual(row["regular_open"],"09:15:00")
                self.assertEqual(row["regular_close"],"15:30:00")
                self.assertTrue(row["intraday_label_eligible"])
                self.assertTrue(row["positional_label_eligible"])
            if row["is_exchange_trading_session"] and row["weekday"] in ("Saturday","Sunday"):
                special=specials[row["date"]]
                self.assertEqual(row["regular_hours_compatible"], special["regular_hours_compatible"])
                if special["regular_hours_compatible"]:
                    self.assertTrue(row["intraday_label_eligible"])
                    self.assertTrue(row["positional_label_eligible"])
                else:
                    self.assertFalse(row["intraday_label_eligible"])
                    self.assertFalse(row["positional_label_eligible"])

    def test_reconciled_2026_closures_are_closed(self):
        for d in ("2026-01-15","2026-08-26"):
            self.assertFalse(self.days[d]["is_exchange_trading_session"])
            self.assertEqual(self.days[d]["session_type"],"declared_full_day_holiday")

    def test_special_sessions_are_explicit_and_fail_closed(self):
        expected={
            "2021-11-04","2022-10-24","2023-11-12","2024-01-20",
            "2024-03-02","2024-05-18","2024-11-01","2025-02-01","2025-10-21"
        }
        actual={x["date"] for x in self.calendar["special_sessions_in_bounds"]}
        self.assertEqual(actual,expected)
        for d in expected-{"2025-02-01"}:
            self.assertTrue(self.days[d]["is_exchange_trading_session"],d)
            self.assertFalse(self.days[d]["intraday_label_eligible"],d)
            self.assertFalse(self.days[d]["positional_label_eligible"],d)
            self.assertFalse(self.days[d]["regular_hours_compatible"],d)
        budget=self.days["2025-02-01"]
        self.assertTrue(budget["is_exchange_trading_session"])
        self.assertEqual(budget["session_type"],"normal_weekend_open")
        self.assertTrue(budget["intraday_label_eligible"])
        self.assertTrue(budget["positional_label_eligible"])
        self.assertEqual(budget["regular_open"],"09:15:00")
        self.assertEqual(budget["regular_close"],"15:30:00")

    def test_session_indices_and_counts_are_consistent(self):
        open_rows=[x for x in self.calendar["calendar_day_rows"] if x["is_exchange_trading_session"]]
        indexes=[x["exchange_session_index"] for x in open_rows]
        self.assertEqual(indexes,list(range(1,len(open_rows)+1)))
        self.assertEqual(self.calendar["exchange_session_count"],len(open_rows))
        self.assertEqual(self.calendar["intraday_label_eligible_session_count"],sum(x["intraday_label_eligible"] for x in open_rows))
        self.assertEqual(self.calendar["positional_label_eligible_session_count"],sum(x["positional_label_eligible"] for x in open_rows))

    def test_unannounced_special_session_fails_if_calendar_is_patched_in_memory(self):
        altered=dict(self.source)
        altered["special_sessions"]=list(self.source["special_sessions"])+[
            {"date":"2024-06-01","session_id":"UNSOURCED","session_mode":"normal_weekend_open",
             "positional_eligible":True,"intraday_eligible":True,"regular_hours_compatible":True,
             "open":"09:15:00","close":"15:30:00"}
        ]
        with self.assertRaisesRegex(ValueError,"lacks a source pin"):
            build.build_calendar(altered,self.source_raw)

if __name__=="__main__":
    unittest.main()
