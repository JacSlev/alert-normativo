# tests/test_date_utils.py
from datetime import datetime, timedelta, timezone
from scraper.date_utils import iso_week_cutoff, previous_iso_week_window


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


def test_iso_week_cutoff_within_last_14_days():
    # Previous Monday is always between 7 and 13 days ago
    cutoff = iso_week_cutoff()
    assert cutoff > datetime.now(timezone.utc) - timedelta(days=14)


def test_iso_week_cutoff_returns_correct_monday():
    # Wednesday 2026-05-13 → previous Monday = 2026-05-04
    cutoff = iso_week_cutoff(_now=datetime(2026, 5, 13, 14, 30, 0, tzinfo=timezone.utc))
    assert cutoff == datetime(2026, 5, 4, 0, 0, 0, tzinfo=timezone.utc)


def test_iso_week_cutoff_on_monday_returns_prev_monday():
    # Monday 2026-05-11 → previous Monday = 2026-05-04
    cutoff = iso_week_cutoff(_now=datetime(2026, 5, 11, 9, 0, 0, tzinfo=timezone.utc))
    assert cutoff == datetime(2026, 5, 4, 0, 0, 0, tzinfo=timezone.utc)


def test_iso_week_cutoff_on_sunday_returns_prev_monday():
    # Sunday 2026-05-17 → this Monday = 2026-05-11, previous Monday = 2026-05-04
    cutoff = iso_week_cutoff(_now=datetime(2026, 5, 17, 23, 59, 0, tzinfo=timezone.utc))
    assert cutoff == datetime(2026, 5, 4, 0, 0, 0, tzinfo=timezone.utc)


# ── previous_iso_week_window ──────────────────────────────────────────────────

def test_previous_iso_week_window_returns_utc_midnight_tuple():
    start, end = previous_iso_week_window()
    for dt in (start, end):
        assert dt.weekday() == 0        # both are Mondays
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0
        assert dt.microsecond == 0
        assert dt.tzinfo == timezone.utc


def test_previous_iso_week_window_end_is_7_days_after_start():
    start, end = previous_iso_week_window()
    assert end - start == timedelta(days=7)


def test_previous_iso_week_window_on_wednesday():
    # Wednesday 2026-05-13 → prev_monday = 2026-05-04, this_monday = 2026-05-11
    start, end = previous_iso_week_window(
        _now=datetime(2026, 5, 13, 14, 30, 0, tzinfo=timezone.utc)
    )
    assert start == datetime(2026, 5, 4, 0, 0, 0, tzinfo=timezone.utc)
    assert end   == datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)


def test_previous_iso_week_window_on_monday():
    # Monday 2026-05-11 → prev_monday = 2026-05-04, this_monday = 2026-05-11
    start, end = previous_iso_week_window(
        _now=datetime(2026, 5, 11, 9, 0, 0, tzinfo=timezone.utc)
    )
    assert start == datetime(2026, 5, 4, 0, 0, 0, tzinfo=timezone.utc)
    assert end   == datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)


def test_previous_iso_week_window_includes_sunday_2359():
    # Publication on Sunday 2026-05-10 23:59 → inside window [May 4, May 11)
    start, end = previous_iso_week_window(
        _now=datetime(2026, 5, 13, 0, 0, 0, tzinfo=timezone.utc)  # any day of week May 11-17
    )
    pub_inside = datetime(2026, 5, 10, 23, 59, 0, tzinfo=timezone.utc)
    assert start <= pub_inside < end


def test_previous_iso_week_window_excludes_this_monday_0000():
    # Publication on Monday 2026-05-11 00:00 → outside window (>= end)
    start, end = previous_iso_week_window(
        _now=datetime(2026, 5, 13, 0, 0, 0, tzinfo=timezone.utc)
    )
    pub_outside = datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)
    assert not (start <= pub_outside < end)
