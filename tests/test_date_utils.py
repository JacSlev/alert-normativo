# tests/test_date_utils.py
from datetime import datetime, timedelta, timezone
from scraper.date_utils import iso_week_cutoff


def test_iso_week_cutoff_is_monday():
    cutoff = iso_week_cutoff()
    assert cutoff.weekday() == 0          # 0 = Monday
    assert cutoff.hour == 0
    assert cutoff.minute == 0
    assert cutoff.second == 0
    assert cutoff.microsecond == 0
    assert cutoff.tzinfo == timezone.utc


def test_iso_week_cutoff_not_in_future():
    cutoff = iso_week_cutoff()
    assert cutoff <= datetime.now(timezone.utc)


def test_iso_week_cutoff_within_last_7_days():
    cutoff = iso_week_cutoff()
    assert cutoff > datetime.now(timezone.utc) - timedelta(days=7)


def test_iso_week_cutoff_returns_correct_monday():
    # Wednesday 2026-05-13 → Monday 2026-05-11
    cutoff = iso_week_cutoff(_now=datetime(2026, 5, 13, 14, 30, 0, tzinfo=timezone.utc))
    assert cutoff == datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)


def test_iso_week_cutoff_on_monday_returns_same_day():
    # Monday 2026-05-11 → Monday 2026-05-11
    cutoff = iso_week_cutoff(_now=datetime(2026, 5, 11, 9, 0, 0, tzinfo=timezone.utc))
    assert cutoff == datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)


def test_iso_week_cutoff_on_sunday_returns_prev_monday():
    # Sunday 2026-05-17 → Monday 2026-05-11
    cutoff = iso_week_cutoff(_now=datetime(2026, 5, 17, 23, 59, 0, tzinfo=timezone.utc))
    assert cutoff == datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)
